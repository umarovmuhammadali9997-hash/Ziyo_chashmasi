import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN", "")
BRAND_NAME = os.getenv("BRAND_NAME", "Fergana school")

_admin_raw = os.getenv("ADMIN_IDS", "")
ADMIN_IDS = [int(x) for x in _admin_raw.replace(" ", "").split(",") if x.strip().isdigit()]

# Railway Volume yo'li bo'lsa, baza shu yerda saqlanadi (persistent).
# Volume bo'lmasa, joriy papkada saqlanadi.
DB_DIR = os.getenv("RAILWAY_VOLUME_MOUNT_PATH", ".")
DB_PATH = os.path.join(DB_DIR, "exam_bot.db")

# Har bir testdagi savollar soni
TEST_SIZE = 30

if not BOT_TOKEN:
    raise RuntimeError("BOT_TOKEN topilmadi! .env faylga token qo'ying.")
