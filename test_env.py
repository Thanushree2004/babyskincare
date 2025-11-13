import os
from dotenv import load_dotenv

# Load .env file
load_dotenv()

# Test if variables are loaded
print("✅ Environment Variables Loaded:")
print(f"FLASK_ENV: {os.getenv('FLASK_ENV')}")
print(f"DATABASE_URL: {os.getenv('DATABASE_URL')}")
print(f"MAIL_SERVER: {os.getenv('MAIL_SERVER')}")
print(f"MAIL_USERNAME: {os.getenv('MAIL_USERNAME')}")