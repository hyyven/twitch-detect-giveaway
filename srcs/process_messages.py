import asyncio
import logging
from typing import Any, List, Tuple
from collections import deque
from time import time
from twitchAPI.chat import ChatMessage

from utils import send_discord_notification
from config import NBR_OF_OCCURENCE, NOTIF_COOLDOWN

logger = logging.getLogger(__name__)
g_tasks = set()		# anti garbage collector

def is_in_cooldown(channel_data: dict[str, Any]) -> bool:
	current_time: float = time()
	if current_time - channel_data["last_notif_time"] >= NOTIF_COOLDOWN:
		channel_data["last_notif_time"] = current_time
		return (False)
	return (True)

def detect_giveaway(history: deque) -> str | None:
	counts: dict[str, int] = {}
	new_count: int = 0
	msg: str = ""

	for msg in history:
		if not msg.startswith('!'):
			continue
		new_count = counts.get(msg, 0) + 1
		counts[msg] = new_count
		if new_count >= NBR_OF_OCCURENCE:
			return (msg)		# return the command if giveaway detected
	return (None)				# return None if no giveaway detected

def make_on_message(ban_words_channels: set[Tuple[str, str]], ban_words_global: set[str], data: dict[str, dict[str, Any]]):
	async def on_message(msg: ChatMessage) -> None:
		if msg.room is None:
			logger.debug(f"room is None; msg: {msg}")
			return (None)
		channel_name: str = msg.room.name.lower()
		channel_data = data.get(channel_name)
		if channel_data is None:
			return (None)
		text: str = msg.text.strip().lower()		# normalize
		if ((text, channel_name) in ban_words_channels):
			return (None)
		if (text in ban_words_global):
			return (None)
		
		logger.debug(f"message received in {channel_name}: {text}")
		data[channel_name]["message_history"].append(text)		# save the message in the history
		detected_cmd = detect_giveaway(channel_data["message_history"])
		if detected_cmd and not is_in_cooldown(channel_data):
			channel_data["message_history"].clear()		# reset history to avoid multiple notifications for same giveaway
			task = asyncio.create_task(send_discord_notification(channel_name, detected_cmd))
			g_tasks.add(task)		# anti garbage collector
			task.add_done_callback(g_tasks.discard)
		return (None)
	return (on_message)
