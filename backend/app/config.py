import os
from pathlib import Path


def is_true(key: str, default: str = 'false') -> bool:
    return os.getenv(key, default).lower() in ('yes', 'true', '1')


ROOT = Path(__file__).resolve().parents[2]
try:
    from dotenv import load_dotenv
    load_dotenv(ROOT / '.env')
except ImportError:
    pass
DB_PATH = Path(os.getenv('DATABASE_PATH', str(ROOT / 'data/storyshorts.sqlite3'))).resolve()
OUTPUT_DIR = Path(os.getenv('OUTPUT_DIR', str(ROOT / 'outputs'))).resolve()
OLLAMA_URL = os.getenv('OLLAMA_URL', 'http://127.0.0.1:11434').rstrip('/')
OLLAMA_MODEL = os.getenv('OLLAMA_MODEL', 'llama3.2')
TTS_ENGINE = os.getenv('TTS_ENGINE', 'kokoro')
KOKORO_VOICE = os.getenv('KOKORO_VOICE', 'af_heart')
REDDIT_AUTHORIZED = is_true('REDDIT_AUTHORIZED')
TOKEN_FILE = Path(os.getenv('YOUTUBE_TOKEN_FILE', str(ROOT / 'secrets/youtube_token.json'))).resolve()
