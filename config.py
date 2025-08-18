import os
from dotenv import load_dotenv

load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
CHAT_MODEL = os.getenv("CHAT_MODEL", "gpt-4o")
EMBED_MODEL = os.getenv("EMBED_MODEL", "text-embedding-3-small")

CHROMA_HOST = os.getenv("CHROMA_HOST", "localhost")
CHROMA_PORT = int(os.getenv("CHROMA_PORT", "8000"))
CHROMA_COLLECTION = os.getenv("CHROMA_COLLECTION", "my_log_db")

KAFKA_BOOTSTRAP = os.getenv("KAFKA_BOOTSTRAP", "localhost:9092")
RAW_TOPIC = os.getenv("RAW_TOPIC", "raw_trace")

TRACE_INACTIVITY_SEC = float(os.getenv("TRACE_INACTIVITY_SEC", "5"))
TRACE_MAX_EVENTS = int(os.getenv("TRACE_MAX_EVENTS", "500"))
FLUSH_TICK_SEC = float(os.getenv("FLUSH_TICK_SEC", "1.0"))
