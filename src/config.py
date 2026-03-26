import yaml
from dotenv import load_dotenv
import os

load_dotenv()

class Config:
    def __init__(self):
        with open("config.yaml", encoding="utf-8") as f:
            self.data = yaml.safe_load(f)
        
        self.discord_token = os.getenv("DISCORD_TOKEN") or self.data["discord"]["token"]
