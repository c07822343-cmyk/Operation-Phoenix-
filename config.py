VIDEO_WIDTH = 1080
VIDEO_HEIGHT = 1920
FPS = 30
VIDEO_BITRATE = "6M"
AUDIO_BITRATE = "192k"

# Voice settings — slower and clearer
TTS_VOICE = "en-US-AndrewNeural"
TTS_RATE = "-10%"
TTS_PITCH = "-5Hz"

GROQ_MODEL = "llama-3.3-70b-versatile"
GROQ_MIN_GAP = 2.0
GROQ_MAX_RETRIES = 5

SUBTITLE_FONTSIZE = 64
SUBTITLE_HIGHLIGHT_SIZE = 72
SUBTITLE_COLOR = "white"
SUBTITLE_HIGHLIGHT_COLOR = "#FFD700"
SUBTITLE_POSITION = 0.72
SUBTITLE_BORDERW = 5
WORDS_PER_SUBTITLE = 3

OUTPUT_DIR = "output"
TEMP_DIR = "temp"
DB_PATH = "phoenix.db"
KEYS_PATH = "keys.json"

BLACKLISTED_FACTS = [
    "honey never expires",
    "octopus three hearts",
    "bananas are berries",
    "60 percent dna bananas",
    "cleopatra closer to iphone",
    "more trees than stars",
    "oxford older than aztecs",
    "goldfish 3 second memory",
    "great wall from space",
    "we use 10 percent brain",
    "napoleon was short",
    "vikings horned helmets",
    "bats are blind",
    "tongue taste map",
    "shaving makes hair thicker",
    "humans swallow spiders sleeping",
    "lightning never strikes twice",
    "bulls hate red color"
]

CATEGORY_COLORS = {
    "animal": "#00c853",
    "space": "#2196f3",
    "history": "#ff9800",
    "science": "#9c27b0",
    "body": "#f44336",
    "food": "#ff5722",
    "technology": "#00bcd4",
    "psychology": "#e91e63",
    "geography": "#8bc34a",
    "culture": "#ffc107",
    "facts": "#ff4444",
    "crime": "#424242",
    "custom": "#607d8b"
}

HUMAN_UPLOAD_HOURS = [7, 8, 11, 12, 19, 20, 23, 0]
