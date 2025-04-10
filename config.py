import os
from dotenv import load_dotenv

# Load variables from the .env file
load_dotenv()

class Config:
    SECRET_KEY = os.environ.get('FLASK_SECRET_KEY')
    CLIENT_ID = os.environ.get('CLIENT_ID')
    CLIENT_SECRET = os.environ.get('CLIENT_SECRET')
    API_KEY = os.environ.get('API_KEY')
    REDIRECT_URI = os.environ.get('REDIRECT_URI')
