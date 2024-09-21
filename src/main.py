from fastapi import FastAPI, Depends
from sqlalchemy.orm import Session
from .database import engine, SessionLocal
from .models import Base, User, OAuthToken
from authlib.integrations.starlette_client import OAuth
from starlette.middleware.sessions import SessionMiddleware
from starlette.requests import Request
from starlette.responses import RedirectResponse, JSONResponse
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()

# Create the FastAPI app
app = FastAPI()

# Add session middleware
app.add_middleware(SessionMiddleware, secret_key=os.getenv("SECRET_KEY"))

# OAuth setup
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
    client_kwargs={"scope": "openid email profile"},
)

# Create the tables in the database
Base.metadata.create_all(bind=engine)


# Dependency for getting the database session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@app.get("/")
async def homepage(request: Request):
    user = request.session.get("user")
    if user:
        return JSONResponse({"message": "You are logged in", "user": user})
    return JSONResponse({"message": "You are not logged in"})


@app.route("/login")
async def login(request: Request):
    redirect_uri = request.url_for("auth")
    return await oauth.google.authorize_redirect(request, redirect_uri)


@app.route("/auth")
async def auth(request: Request, db: Session = Depends(get_db)):
    token = await oauth.google.authorize_access_token(request)
    user_info = await oauth.google.parse_id_token(request, token)

    # Check if user exists
    user = db.query(User).filter(User.google_id == user_info["sub"]).first()

    # If user doesn't exist, create a new one
    if not user:
        user = User(
            google_id=user_info["sub"],
            email=user_info["email"],
            name=user_info["name"],
            picture=user_info.get("picture"),
        )
        db.add(user)
        db.commit()
        db.refresh(user)

    # Store OAuth tokens in the database
    oauth_token = OAuthToken(
        user_id=user.id,
        access_token=token["access_token"],
        refresh_token=token.get("refresh_token"),
        expires_in=token["expires_in"],
    )
    db.add(oauth_token)
    db.commit()

    # Store user info in the session
    request.session["user"] = {"id": user.id, "name": user.name, "email": user.email}

    return RedirectResponse(url="/")


@app.route("/logout")
async def logout(request: Request):
    request.session.pop("user", None)
    return RedirectResponse(url="/")


@app.get("/profile")
async def profile(request: Request, db: Session = Depends(get_db)):
    user = request.session.get("user")
    if user:
        db_user = db.query(User).filter(User.id == user["id"]).first()
        return JSONResponse({"message": "This is your profile", "user": db_user})
    return RedirectResponse(url="/login")
