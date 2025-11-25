import os
from dotenv import load_dotenv

load_dotenv()

DATABASE_HOST = os.getenv("DATABASE_HOST", "localhost")
DATABASE_PORT = int(os.getenv("DATABASE_PORT", "3306"))
DATABASE_USER = os.getenv("DATABASE_USER", "root")
DATABASE_PASSWORD = os.getenv("DATABASE_PASSWORD", "")
DATABASE_NAME = os.getenv("DATABASE_NAME", "parking_db")

API_TOKEN = os.getenv("API_TOKEN", "dev-token")
TOTAL_SLOTS = int(os.getenv("TOTAL_SLOTS", "60"))

IMAGE_FOLDER = os.getenv("IMAGE_FOLDER", "./images")
os.makedirs(IMAGE_FOLDER, exist_ok=True)

# SQLAlchemy connection string for PyMySQL
SQLALCHEMY_DATABASE_URL = (
    f"mysql+pymysql://{DATABASE_USER}:{DATABASE_PASSWORD}"
    f"@{DATABASE_HOST}:{DATABASE_PORT}/{DATABASE_NAME}?charset=utf8mb4"
)
