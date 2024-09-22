from sqlalchemy import Column, Integer, String, Text
from .database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True)
    name = Column(String)
    google_id = Column(String, unique=True, index=True)
    picture = Column(Text)


class OAuthToken(Base):
    __tablename__ = "oauth_tokens"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer)  # ForeignKey could be added here if needed
    access_token = Column(Text)
    id_token = Column(Text)
    expires_in = Column(Integer)
    expires_at = Column(Integer)
    token_type = Column(String)
    sub = Column(String)
    exp = Column(Integer)
    iat = Column(Integer)
    iss = Column(String)
    nonce = Column(String)
