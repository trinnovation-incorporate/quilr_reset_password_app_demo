from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from .database import engine, SessionLocal
from .models import Base, User, OAuthToken
from authlib.integrations.starlette_client import OAuth
from starlette.middleware.sessions import SessionMiddleware
import os
from dotenv import load_dotenv

from pprint import pprint
import requests
from datetime import date, timedelta

from .core.utils import fetch_gmail_messages, get_access_token_by_user
from .core.decode import decode_base64url, get_dict_structure
from .core.llm_model import ModelLoader, TextGenerationService
from .core.html_cleaner import clean_body_html, minify_html

import htmlmin

# Load environment variables
load_dotenv()

# Create the FastAPI app
app = FastAPI()

# Add session middleware
app.add_middleware(SessionMiddleware, secret_key=os.getenv("SECRET_KEY"))

print("LOADING MODELS")
model_loader = ModelLoader(model_path="LLM/")
text_generation_service = TextGenerationService(model_loader)
print("LOADING DONE...")

# Set up OAuth
oauth = OAuth()
oauth.register(
    name="google",
    client_id=os.getenv("GOOGLE_CLIENT_ID"),
    client_secret=os.getenv("GOOGLE_CLIENT_SECRET"),
    authorize_url="https://accounts.google.com/o/oauth2/auth",
    authorize_params=None,
    access_token_url="https://accounts.google.com/o/oauth2/token",
    access_token_params=None,
    refresh_token_url=None,
    jwks_uri="https://www.googleapis.com/oauth2/v3/certs",
    client_kwargs={"scope": "openid email profile https://www.googleapis.com/auth/gmail.readonly"},
)


# Create tables in the database
Base.metadata.create_all(bind=engine)

# Jinja2 templates setup
templates = Jinja2Templates(directory="templates")


@app.get("/", response_class=HTMLResponse)
async def homepage(request: Request):
    print("USER:", request.session.get("token"))
    user = request.session.get("user")  # Extract user_id from the request parameters
    print(user)
    return templates.TemplateResponse("home.html", {"request": request, "user": user})


@app.route("/login", methods=["GET"])
async def login_page(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})


@app.route("/messages", methods=["GET"])
async def messages_list(request: Request, domain: str = "chess.com"):
    user = request.session.get("user")
    if not user:
        raise HTTPException(status_code=400, detail="User ID is required")

    access_token = user["access_token"]
    # Gmail API endpoint to list messages
    url = "https://gmail.googleapis.com/gmail/v1/users/me/messages"

    # Set the headers including the access token
    headers = {"Authorization": f"Bearer {access_token}"}
    # Use the 'q' parameter to filter emails by the domain
    previous_day = date.today() - timedelta(days=1)
    params = {
        # "q": f"from:@{domain} after:{previous_day.strftime('%Y/%m/%d')}",
        "q": f"from:@{domain}",
        "maxResults": 1,
    }
    # Make the request to Gmail API
    response = requests.get(url, headers=headers, params=params)

    print("response:", response.status_code)
    email_messages = []
    if response.status_code == 200:

        messages = response.json()
        for message in messages.get("messages", []):
            print("message:", message["id"])
            url = f"https://gmail.googleapis.com/gmail/v1/users/me/messages/{message['id']}"
            response = requests.get(url, headers=headers, params={"format": "full"})
            if response.status_code == 200:
                # Parse the response JSON (list of messages)
                message_object = response.json()

                # when using FULL
                mail_data = message_object["payload"]["parts"][1]["body"]["data"]
                decoded_mail = decode_base64url(mail_data)

                cleaned_mail_message = "".join(minify_html(decoded_mail, domain))
                # cleaned_mail_message = htmlmin.minify(cleaned_mail_message, remove_empty_space=True)
                email_messages.append(cleaned_mail_message)

                prompt = f""" Which link seems to be the be the main objective of email
                                {cleaned_mail_message}
                        """

                response = text_generation_service.generate_text(prompt, 1024)
                print("RESPONSE", response)
            return templates.TemplateResponse("message_list.html", {"request": request, "messages": email_messages})
    else:
        return {"error": "Failed to retrieve messages"}


@app.route("/login", methods=["POST"])
async def login(request: Request):
    redirect_uri = request.url_for("auth")
    return await oauth.google.authorize_redirect(request, redirect_uri)


@app.route("/auth")
async def auth(request: Request):
    token = await oauth.google.authorize_access_token(request)
    pprint(token)
    user_info = token["userinfo"]

    # Find or create user
    with SessionLocal() as db:
        user = db.query(User).filter(User.google_id == user_info["sub"]).first()
        if not user:
            user = User(
                google_id=user_info["sub"],
                email=user_info["email"],
                name=user_info.get("name"),
                picture=user_info.get("picture"),
            )
            db.add(user)
            db.commit()
            db.refresh(user)

        # Store OAuth tokens
        oauth_token = OAuthToken(
            user_id=user.id,
            access_token=token["access_token"],
            id_token=token.get("id_token"),
            expires_in=token["expires_in"],
            expires_at=token["expires_at"],
            token_type=token["token_type"],
            sub=token["userinfo"]["sub"],
            exp=token["userinfo"]["exp"],
            iat=token["userinfo"]["iat"],
            iss=token["userinfo"]["iss"],
            nonce=token["userinfo"]["nonce"],
        )
        db.add(oauth_token)
        db.commit()

        # Store user session
        request.session["user"] = {
            "id": user.id,
            "name": user.name,
            "email": user.email,
            "access_token": token["access_token"],
            "id_token": token["id_token"],
        }
        # request.session["token"] = token

    return RedirectResponse(url="/")


@app.route("/logout", methods=["GET"])
async def logout(request: Request):
    request.session.pop("user", None)
    request.session.pop("token", None)
    return templates.TemplateResponse("logout.html", {"request": request})


# FastAPI route for generating text from a prompt
# @app.post("/generate")
# def generate(prompt: str, max_length=100):
#     """Endpoint to generate text based on a prompt"""
#     response = text_generation_service.generate_text(prompt, max_length)
#     return {"generated_text": response}
