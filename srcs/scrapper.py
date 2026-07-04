import asyncio
import logging
from typing import Any, Tuple, List
from twitchAPI.twitch import Twitch
from twitchAPI.chat import Chat, ChatEvent

from utils import ban_word_init, init_struct, wait_chat_ready
from auth import on_token_refresh, handle_authentication
from config import APP_ID, APP_SECRET, TARGET_CHANNEL, MAX_HELIX_PAGE
from process_messages import make_on_message
from dashboard.server import dashboard

logger = logging.getLogger(__name__)

UNIVERSE_SET = set(TARGET_CHANNEL)

async def update_channels_state(twitch: Twitch, chat: Chat, connected: set[str], data: dict[str, dict[str, Any]]) -> None:
	await wait_chat_ready(chat)
	try:
		live_set = set()
		for i in range(0, len(TARGET_CHANNEL), MAX_HELIX_PAGE):
			subset = TARGET_CHANNEL[i:i + MAX_HELIX_PAGE]
			try:
				streams = twitch.get_streams(user_login=subset)		# return info of channels (subnet) in live only
				async for s in streams:
					live_set.add(s.user_login.lower())
			except Exception as e:
				logger.error(f"failed to get streams for subset:{subset} error:{e}")
				return
			await asyncio.sleep(0)		# don't block other async tasks
		to_join = list((live_set - connected) & UNIVERSE_SET)
		to_leave = list((connected - live_set) & UNIVERSE_SET)
		if to_leave:
			try:
				await chat.leave_room(to_leave)		# leave_room() return nothing, can't fail
				for c in to_leave:
					connected.discard(c)		# remove channel from connected set
					data[c]["is_connected"] = False
			except Exception as e:
				logger.error(f"leave rooms failed {to_leave}: {e}")
		if to_join:
			try:
				failed_joins = await chat.join_room(to_join)		# join_room() return list of failed joins
				for c in to_join:
					if c not in failed_joins:
						connected.add(c)		# add channel to connected set
						data[c]["is_connected"] = True
			except Exception as e:
				logger.error(f"join rooms failed {to_join}: {e}")
	except Exception as e:
		logger.error(f"error in update_channels_state:{e}")

async def scrapper(ban_words_channels: set[Tuple[str, str]], ban_words_global: set[str], data: dict[str, dict[str, Any]]):
	twitch = None
	chat = None
	connected: set[str] = set()
	try:
		twitch = await Twitch(APP_ID, APP_SECRET)
		twitch.user_auth_refresh_callback = on_token_refresh
		await handle_authentication(twitch)
		chat = await Chat(twitch)
		chat.register_event(ChatEvent.MESSAGE, make_on_message(ban_words_channels, ban_words_global, data))		# call make_on_message on every message received
		chat.start()
		logger.info("ctrl+c to stop")
		while True:
			try:
				if chat.is_ready():
					await update_channels_state(twitch, chat, connected, data)
				await asyncio.sleep(10)		# check every 10 seconds to join/leave channels
			except Exception as e:
				logger.error(f"error in main loop: {e}")
				raise e
	except asyncio.CancelledError:
		logger.info("scrapper task cancelled")
		if chat:
			chat.stop()
		if twitch:
			await twitch.close()
		raise
	except Exception as e:
		logger.error(f"error in scrapper loop: {e}")
		raise e

async def main():
	try:
		ban_words_channels, ban_words_global = ban_word_init()
		data = init_struct()
		async with asyncio.TaskGroup() as tg:
			task1 = tg.create_task(scrapper(ban_words_channels, ban_words_global, data))
			task2 = tg.create_task(dashboard(data))
	except ExceptionGroup as eg:
		logger.critical(f"big error: {eg}")
		raise

if __name__ == "__main__":
	try:
		asyncio.run(main())
	except KeyboardInterrupt:
		logger.info("stopping")