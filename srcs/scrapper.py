import asyncio
import logging
from typing import Any, Tuple
from twitchAPI.twitch import Twitch
from twitchAPI.chat import Chat, ChatEvent

from utils import ban_word_init, init_struct, wait_chat_ready, manage_failed_join
from auth import on_token_refresh, handle_authentication
from config import APP_ID, APP_SECRET, TARGET_CHANNEL, MAX_HELIX_PAGE
from process_messages import make_on_message
from dashboard.server import dashboard

logger = logging.getLogger(__name__)

async def update_channels_state(twitch: Twitch, chat: Chat, connected: set[str], data: dict[str, dict[str, Any]]) -> None:
	if not await wait_chat_ready(chat):
		raise RuntimeError("chat not ready after waiting")
	try:
		### security for when twitch api remove the bot from every rooms for some reason
		actually_connected = {c for c in connected if chat.is_in_room(c)}
		failed_reconnects = connected - actually_connected
		for c in failed_reconnects:
			logger.error(f"channel unsync : {c}")
			data[c]["is_connected"] = False
		connected.intersection_update(actually_connected)		# keep channels that are in "connected" and in "actually_connected"
		### 

		live_set = set()
		target_list = list(TARGET_CHANNEL)		# convert set to list to slice after 
		for i in range(0, len(target_list), MAX_HELIX_PAGE):
			subset = target_list[i:i + MAX_HELIX_PAGE]		# slice to respect twitch limit
			try:
				streams = twitch.get_streams(user_login=subset)		# return info of channels (subnet) in live only
				async for s in streams:
					live_set.add(s.user_login.lower())
			except Exception as e:
				logger.error(f"failed to get streams for subset:{subset} error:{e}")
				raise e
			await asyncio.sleep(0)		# don't block other async tasks
		# convert to list because join_room() and leave_room() are waiting a list not a set
		to_join = list((live_set - connected) & TARGET_CHANNEL)		# first: remove already connected channels; second: remove channels not in TARGET_CHANNEL
		to_leave = list(connected - live_set)		# remove channels still in live
		if to_leave:
			try:
				await chat.leave_room(to_leave)		# leave_room() return nothing, can't fail
				for c in to_leave:
					connected.discard(c)		# remove channel from connected set
					data[c]["is_connected"] = False
			except Exception as e:
				logger.error(f"leave rooms failed {to_leave}: {e}")
				raise e
		if to_join:
			try:
				failed_joins = await chat.join_room(to_join)		# join_room() return list of failed joins
				for c in to_join:
					if c not in failed_joins:
						connected.add(c)		# add channel to connected set
						data[c]["is_connected"] = True
						manage_failed_join(data, c, True)		# reset failed_joins counter
					else:
						manage_failed_join(data, c, False)
			except Exception as e:
				logger.error(f"join rooms failed {to_join}: {e}")
				raise e
	except Exception as e:
		logger.error(f"error in update_channels_state:{e}")
		raise e

async def scrapper(ban_words_channels: set[Tuple[str, str]], ban_words_global: set[str], data: dict[str, dict[str, Any]]):
	while True:
		twitch = None
		chat = None
		connected: set[str] = set()
		for c in data:
			data[c]["is_connected"] = False
			data[c]["failed_joins"] = 0
		try:
			logger.info("connecting to twitch api and chat")
			twitch = await Twitch(APP_ID, APP_SECRET)
			twitch.user_auth_refresh_callback = on_token_refresh
			await handle_authentication(twitch)
			chat = await Chat(twitch, callback_loop=asyncio.get_running_loop())
			chat.register_event(ChatEvent.MESSAGE, make_on_message(ban_words_channels, ban_words_global, data))		# call make_on_message on every message received
			chat.start()
			logger.info("ctrl+c to stop")
			consecutive_errors = 0
			while True:
				try:
					await update_channels_state(twitch, chat, connected, data)
					consecutive_errors = 0
					await asyncio.sleep(60)		# check every 60 seconds to join/leave channels
				except Exception as e:
					logger.error(f"error in main loop: {e}")
					consecutive_errors += 1
					if "bound to a different event loop" in str(e) or "closing transport" in str(e) or consecutive_errors >= 3:
						logger.warning("session corrupted or repeated timeouts: restarting twitch clients...")
						break
					await asyncio.sleep(10)
		except asyncio.CancelledError:
			logger.info("scrapper task cancelled")
			raise
		except Exception as e:
			logger.error(f"error in scrapper loop: {e}. retrying in 15s...")
			await asyncio.sleep(15)
		finally:
			if chat:
				try:
					chat.stop()
				except Exception as e:
					logger.debug(f"error stopping chat in recovery: {e}")
			if twitch:
				try:
					await twitch.close()
				except Exception as e:
					logger.debug(f"error closing twitch session in recovery: {e}")

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