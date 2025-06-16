import os

from dotenv import load_dotenv

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ENV_PATH = os.path.join(ROOT_DIR, ".env.test")
load_dotenv(dotenv_path=ENV_PATH, override=True)
