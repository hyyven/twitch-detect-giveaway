import os
import logging
from typing import List
from dotenv import load_dotenv

logging.basicConfig(
	level=logging.INFO,
	format="%(asctime)s [%(levelname)s] %(name)s - %(message)s",
	handlers=[
		logging.FileHandler("bot.log"),
		logging.StreamHandler()
	]
)

# silence twitchAPI logs
logging.getLogger("twitchAPI").setLevel(logging.WARNING)

load_dotenv()

APP_ID = os.getenv("TWITCH_APP_ID", "")
APP_SECRET = os.getenv("TWITCH_APP_SECRET", "")
TARGET_CHANNEL_FILE = os.getenv("TARGET_CHANNEL_FILE", "")
BAN_WORDS_FILE = os.getenv("BAN_WORDS_FILE", "")
DISCORD_PING = os.getenv("DISCORD_PING", "")
WEBHOOK_URL = os.getenv("WEBHOOK_URL", "")
NBR_OF_OCCURENCE = int(os.getenv("NBR_OF_OCCURENCE", "6"))
NOTIF_COOLDOWN = int(os.getenv("NOTIF_COOLDOWN", "300")) # in seconds
MAX_HELIX_PAGE = int(os.getenv("MAX_HELIX_PAGE", "100"))
MAX_MESSAGES_HISTORY = int(os.getenv("MAX_MESSAGES_HISTORY", "20"))

required_vars = {
	"TWITCH_APP_ID": APP_ID,
	"TWITCH_APP_SECRET": APP_SECRET,
	"TARGET_CHANNEL_FILE": TARGET_CHANNEL_FILE,
	"BAN_WORDS_FILE": BAN_WORDS_FILE,
	"DISCORD_PING": DISCORD_PING,
	"WEBHOOK_URL": WEBHOOK_URL
}

missing = []
for name, val in required_vars.items():
	if not val:
		logging.error(f"missing var:{name}")
		missing.append(name)

if missing:
	raise RuntimeError("missing .env var")

try:
	with open(TARGET_CHANNEL_FILE, 'r') as f:
		TARGET_CHANNEL: set[str] = set(line.strip().lower() for line in f if line.strip())
	with open(BAN_WORDS_FILE, 'r') as f:
		RAW_BAN_WORDS: List[str] = [line.strip() for line in f if line.strip()]
except Exception as e:
	logging.error(f"can't find {TARGET_CHANNEL_FILE} or {BAN_WORDS_FILE}")
	raise