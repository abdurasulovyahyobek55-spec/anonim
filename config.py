import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("7995346816:AAFM3tc0K418HYQ6KoQzENM2Zt-b3SmkHQU")
ADMIN_ID = int(os.getenv("8791058696", "0"))
DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "anonim.db")
