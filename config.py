import json
import os

# Telegram Bot Token
TELEGRAM_BOT_TOKEN = "7916398102:AAEwuflXT0BIKASxbARMnrNTbpm7I-gezAo"

# Google OAuth settings
client_secret_json = {
    "web": {
        "client_id": "191565178845-m0ur565ho3a9ptm71ps774kh7mvt1oug.apps.googleusercontent.com",
        "project_id": "blogger-test-441717",
        "auth_uri": "https://accounts.google.com/o/oauth2/auth",
        "token_uri": "https://oauth2.googleapis.com/token",
        "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
        "client_secret": "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",
        "redirect_uris": ["http://localhost:5000/callback"],
    }
}

GOOGLE_CLIENT_ID = client_secret_json["web"]["client_id"]
GOOGLE_CLIENT_SECRET = client_secret_json["web"]["client_secret"]
GOOGLE_REDIRECT_URI = "http://143.110.188.195:5000/callback"
SCOPES = ["https://www.googleapis.com/auth/blogger"]

# Blog ID
BLOG_ID = "737863940949257967"

# Other Settings
CREDENTIALS_FILE = "credentials.json"  # Where we'll store user credentials (not recommended for production)

# Directory to store user credentials
USER_CREDENTIALS_DIR = "user_creds"
# Ensure the directory exists
os.makedirs(USER_CREDENTIALS_DIR, exist_ok=True)
