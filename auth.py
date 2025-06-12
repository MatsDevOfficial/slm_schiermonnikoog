from starlette.requests import Request
from authlib.integrations.starlette_client import OAuth
from starlette.responses import RedirectResponse
import os

oauth = OAuth()

oauth.register(
    name='discord',
    client_id=os.getenv("DISCORD_CLIENT_ID"),
    client_secret=os.getenv("DISCORD_CLIENT_SECRET"),
    access_token_url='https://discord.com/api/oauth2/token',
    authorize_url='https://discord.com/api/oauth2/authorize',
    api_base_url='https://discord.com/api/',
    client_kwargs={'scope': 'identify email'}
)

oauth.register(
    name='github',
    client_id=os.getenv("GITHUB_CLIENT_ID"),
    client_secret=os.getenv("GITHUB_CLIENT_SECRET"),
    access_token_url='https://github.com/login/oauth/access_token',
    authorize_url='https://github.com/login/oauth/authorize',
    api_base_url='https://api.github.com/',
    client_kwargs={'scope': 'user:email'}
)

async def get_current_user(request: Request):
    return request.session.get("user")

async def login(request: Request):
    provider = request.path_params['provider']
    redirect_uri = request.url_for("auth", provider=provider)
    client = oauth.create_client(provider)
    return await client.authorize_redirect(request, redirect_uri)

async def auth(request: Request):
    provider = request.path_params['provider']
    client = oauth.create_client(provider)
    try:
        token = await client.authorize_access_token(request)
        endpoint = 'users/@me' if provider == 'discord' else 'user'
        resp = await client.get(endpoint, token=token)
        user = resp.json()
        request.session['user'] = user
    except Exception:
        return RedirectResponse(url="/login?error=auth_failed")
    return RedirectResponse(url="/dashboard")

async def logout(request: Request):
    request.session.pop("user", None)
    return RedirectResponse(url="/")
