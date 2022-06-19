import enum
import importlib.metadata


VERSION: str = importlib.metadata.version("lcjournal_scraper")

class OutputFormat(enum.Enum):
    CSV: str = "csv"
    JSON: str = "json"
