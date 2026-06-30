import asyncio
import logging
import aiohttp
from typing import Any, Tuple, List
from collections import deque

from config import TARGET_CHANNEL, RAW_BAN_WORDS, DISCORD_PING, WEBHOOK_URL, MAX_MESSAGES_HISTORY

logger = logging.getLogger(__name__)

def ban_word_init() -> Tuple[set[Tuple[str, str]], set[str]]:
	ban_words_channels: set[Tuple[str, str]] = set()
	ban_words_global: set[str] = set()
	try:
		for line in RAW_BAN_WORDS:
			logger.debug(f"line:{line}")
			line_split: list[str] = line.split(':', 1)
			if len(line_split) == 1:
				logger.debug(f"skipping malformed banword line:{line}")
				ban_words_global.add(line.strip().lower())
				continue
			elif len(line_split) != 2:
				continue
			ban_words_channels.add((line_split[0].strip().lower(), line_split[1].strip().lower()))
	except Exception as e:
		logger.error(f"failed to load ban words: {e}")
		raise
	return (ban_words_channels, ban_words_global)

def init_struct() -> dict[str, dict[str, Any]]:
	data: dict[str, dict[str, Any]] = {}

	for channel_name in TARGET_CHANNEL:
		channel_data: dict[str, Any] = {}
		channel_data["channel_name"] = channel_name
		channel_data["last_notif_time"] = 0
		channel_data["message_history"] = deque(maxlen=MAX_MESSAGES_HISTORY)
		channel_data["is_connected"] = False
		data[channel_name] = channel_data
	return (data)

async def send_discord_notification(channel_name: str, command: str):
	payload = {"content": f"<@&{DISCORD_PING}> detected : https://twitch.tv/{channel_name} command : {command}"}
	try:
		async with aiohttp.ClientSession() as session:
			async with session.post(WEBHOOK_URL, json=payload) as response:
				if response.status not in (200, 204):
					logger.error(f"failed to send discord notification:{response.status}")
				else:
					logger.debug(f"discord notification sent for {channel_name}")
	except Exception as e:
		logger.error(f"error sending discord notification:{e}")

async def wait_chat_ready(chat) -> bool:
	if not chat.is_ready():
		for _ in range(100):  # ~10s max
			if chat.is_ready():
				break
			await asyncio.sleep(0.1)
	if not chat.is_ready():
		logger.error("update_channels_state: chat not ready after waiting")
		return False
	return True