import os
from dotenv import load_dotenv

load_dotenv()

# Bot Core Identity
BOT_NAME = "Shizu Security"
VERSION = "2.3.0"
DEVELOPERS = ["VIPER", "PRASHU"]
DEVELOPER_STRING = "VIPER & PRASHU"

# Bot Owners & Developers
DEFAULT_OWNER_IDS = [1478730719571349545, 1509545584317562970]
env_owners = os.getenv("OWNER_IDS", "")
if env_owners:
    try:
        OWNER_IDS = [int(oid.strip()) for oid in env_owners.split(",") if oid.strip().isdigit()]
    except Exception:
        OWNER_IDS = DEFAULT_OWNER_IDS
else:
    OWNER_IDS = DEFAULT_OWNER_IDS

# Secrets & Connections
TOKEN = os.getenv("DISCORD_TOKEN") or os.getenv("TOKEN", "")
DEFAULT_PREFIX = os.getenv("DEFAULT_PREFIX", "?")
DATABASE_PATH = os.getenv("DATABASE_PATH", "database/shizu_security.db")

# Aesthetics & Colors (Sleek Shizu Dark Theme)
COLOR_DEFAULT = 0x000000   # Shizu signature pure black
COLOR_DARK = 0x000000      # Dark minimalist embed
COLOR_SUCCESS = 0x000000   # Minimalist black with animated check
COLOR_ERROR = 0xFF0000     # Vivid alert red
COLOR_WARNING = 0x000000   # Minimalist black with animated warning
COLOR_INFO = 0x000000      # Minimalist black

# --- Fixed Zero-Trust Invariants ---
MAX_BURST_ACTIONS = 3      # Maximum destructive actions allowed per actor
BURST_WINDOW = 10.0        # Sliding time window in seconds
AUDIT_TOLERANCE_SECONDS = 5.0 # Window to correlate audit log actor

# --- Clean & Professional Animated Emojis (Styled like Shizu Music) ---
ANIM_SUCCESS = "<a:tick:1261574239354621963>"        # Animated green check tick
ANIM_WARN = "<a:Warning:1299512982006665216>"        # Animated warning flash
ANIM_ALERT = "<a:alert:1272569018183843874>"          # Animated security siren / breach
ANIM_SHIELD = "<a:gears:1261577892752789586>"        # Animated spinning gears / shield
ANIM_LOADING = "<a:RedLoading:1246777916621197424>"  # Animated processing indicator
ANIM_HAMMER = "<a:olympus_WarnFlash:1272569018183843874>" # Animated punishment hammer
ANIM_CROWN = "<a:tick:1261574239354621963>"          # Authority / Supreme indicator
ANIM_LOCK = "<a:Warning:1299512982006665216>"         # Lockdown indicator

# Static / Fallback Universal Emojis
EMOJI_SHIELD = "🛡️"
EMOJI_SECURITY = "🔐"
EMOJI_SUCCESS = "✅"
EMOJI_ERROR = "❌"
EMOJI_WARN = "⚠️"
EMOJI_INFO = "ℹ️"
EMOJI_HAMMER = "🔨"
EMOJI_BOOT = "👢"
EMOJI_TIMEOUT = "⏳"
EMOJI_LOCK = "🔒"
EMOJI_UNLOCK = "🔓"
EMOJI_SETTINGS = "⚙️"
EMOJI_CROWN = "👑"
EMOJI_RAID = "🚨"
EMOJI_BOT = "🤖"
EMOJI_LIST = "📋"
EMOJI_STAR = "⭐"
