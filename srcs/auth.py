import json
import os
import logging
from twitchAPI.twitch import Twitch
from twitchAPI.type import AuthScope
from twitchAPI.oauth import UserAuthenticator, refresh_access_token

from config import APP_ID, APP_SECRET

logger = logging.getLogger(__name__)

TOKEN_FILE = "ressources/auth.json"
USER_SCOPE = [AuthScope.CHAT_READ]

async def print_auth_url(url: str) -> None:
	logger.info(f"to authenticate open:{url}")

async def on_token_refresh(token: str, refresh: str) -> None:
	try:
		os.makedirs(os.path.dirname(TOKEN_FILE), exist_ok=True)		# create directory if doesn't exist
		with open(TOKEN_FILE, 'w') as token_file:
			json.dump({'token': token, 'refresh': refresh}, token_file)
		logger.info("token refreshed and saved")
	except Exception as e:
		logger.error(f"failed to save token:{e}")

async def handle_authentication(twitch: Twitch) -> None:
	if os.path.exists(TOKEN_FILE):
		try:
			with open(TOKEN_FILE, 'r') as token_file:
				creds = json.load(token_file)
			new_token, new_refresh_token = await refresh_access_token(creds['refresh'], APP_ID, APP_SECRET)
			await twitch.set_user_authentication(new_token, USER_SCOPE, new_refresh_token)
			await on_token_refresh(new_token, new_refresh_token)
			logger.info("auth success")
			return (None)
		except Exception:
			logger.warning("impossible to refresh need to re-authenticate")

	r = await UserAuthenticator(twitch, USER_SCOPE).authenticate(use_browser=False, auth_url_callback=print_auth_url)
	if r is None:
		raise Exception("Authentication failed")
	token, refresh_token = r
	await twitch.set_user_authentication(token, USER_SCOPE, refresh_token)
	await on_token_refresh(token, refresh_token)