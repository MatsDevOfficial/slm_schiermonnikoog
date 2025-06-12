from fastapi import APIRouter, Request
from authlib.integrations.starlette_client import OAuth
from starlette.responses import RedirectResponse
from models import SessionLocal, User
from dotenv import load_dotenv
import os

load_dotenv()

router = APIRouter()
oauth = OAuth()

# Discord
oauth.register(
    name='discord',
    client_id=os.getenv("DISCORD_CLIENT_ID"),
    client_secret=os.getenv("DISCORD_CLIENT_SECRET"),
    access_token_url='https://discord.com/api/oauth2/token',
    authorize_url='https://discord.com/api/oauth2/authorize',
    api_base_url='https://discord.com/api/',
    client_kwargs={'scope': 'identify email'}
)

# GitHub
oauth.register(
    name='github',
    client_id=os.getenv("GITHUB_CLIENT_ID"),
    client_secret=os.getenv("GITHUB_CLIENT_SECRET"),
    access_token_url='https://github.com/login/oauth/access_token',
    authorize_url='https://github.com/login/oauth/authorize',
    api_base_url='https://api.github.com/',
    client_kwargs={'scope': 'user:email'}
)

@router.get("/login/{provider}")
async def login(request: Request, provider: str):
    redirect_uri = request.url_for("auth_callback", provider=provider)
    return await oauth.create_client(provider).authorize_redirect(request, redirect_uri)

@router.get("/auth/{provider}")
async def auth_callback(request: Request, provider: str):
    client = oauth.create_client(provider)
    token = await client.authorize_access_token(request)
    user_info = await client.get('users/@me' if provider == 'discord' else 'user')
    user_data = user_info.json()

    email = user_data.get("email") or (user_data["login"] + "@github.com")
    oauth_id = str(user_data["id"])

    db = SessionLocal()
    user = db.query(User).filter(User.oauth_id == oauth_id, User.oauth_provider == provider).first()
    if not user:
        user = User(
            oauth_provider=provider,
            oauth_id=oauth_id,
            email=email
        )
        db.add(user)
        db.commit()

    request.session["user"] = {"id": user.id, "email": user.email, "role": user.role}
    return RedirectResponse(url="/")
