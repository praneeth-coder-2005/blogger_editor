import logging
import os
from telegram import Update, Bot
from telegram.ext import Updater, CommandHandler, CallbackContext, MessageHandler, Filters
from flask import Flask, request, redirect, url_for, session
from google.oauth2 import credentials
from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from config import TELEGRAM_BOT_TOKEN, GOOGLE_CLIENT_ID, GOOGLE_CLIENT_SECRET, GOOGLE_REDIRECT_URI, SCOPES, BLOG_ID, USER_CREDENTIALS_DIR
import json

# Flask setup
app = Flask(__name__)
app.secret_key = "SUPER_SECRET_KEY"  # Keep this secret

# Telegram Bot Commands
def start(update: Update, context: CallbackContext):
    update.message.reply_text("Welcome! I can help you manage your blog posts.")
    update.message.reply_text("Use /login to authenticate with Google.")

def login(update: Update, context: CallbackContext):
    flow = Flow.from_client_secrets_file(
        "client_secrets.json", scopes=SCOPES,
        redirect_uri=GOOGLE_REDIRECT_URI)
    authorization_url, state = flow.authorization_url(
        access_type="offline", include_granted_scopes="true")
    session["state"] = state
    update.message.reply_text(f"Click this link to login: {authorization_url}")

def compose(update: Update, context: CallbackContext):
    update.message.reply_text("Okay, what would be the title of your post?")
    context.user_data["state"] = "waiting_title"

def handle_message(update: Update, context: CallbackContext):
    user_data = context.user_data
    text = update.message.text

    if "state" in user_data:
        state = user_data["state"]
        if state == "waiting_title":
            user_data["post_title"] = text
            update.message.reply_text("Got it. What's your post content?")
            user_data["state"] = "waiting_content"
        elif state == "waiting_content":
            user_data["post_content"] = text
            update.message.reply_text("Your post is ready. use /publish to publish")
            user_data["state"] = "post_ready"
        else:
            update.message.reply_text("Sorry, I didn't understand your request")
    else:
        update.message.reply_text("Use /compose to create a new post")

def publish(update: Update, context: CallbackContext):
    user_data = context.user_data
    if "post_ready" not in user_data or not user_data["post_ready"]:
        update.message.reply_text("No post ready for publish, use /compose to create a new one")
        return
    try:
        creds = load_credentials(str(update.message.from_user.id))
        if not creds or not creds.valid:
           update.message.reply_text("Please log in using /login first")
           return

        service = build("blogger", "v3", credentials=creds)
        post = {
            "title": user_data["post_title"],
            "content": user_data["post_content"]
        }
        response = service.posts().insert(blogId=BLOG_ID, body=post).execute()
        update.message.reply_text(f"Post Published! ID: {response['id']}")
        del user_data["state"]
        del user_data["post_title"]
        del user_data["post_content"]
    except HttpError as e:
        update.message.reply_text(f"An error occurred: {e}")


# Flask Routes
@app.route("/callback")
def callback():
    flow = Flow.from_client_secrets_file(
        "client_secrets.json", scopes=SCOPES,
        redirect_uri=GOOGLE_REDIRECT_URI)
    flow.fetch_token(authorization_response=request.url)
    if not session["state"] == request.args["state"]:
        return "Invalid state parameter", 401
    
    creds = flow.credentials
    user_id = request.args.get('state')
    save_credentials(creds, user_id)
    return "Authentication successfull, please go back to the telegram bot"


def load_credentials(user_id):
    file_path = os.path.join(USER_CREDENTIALS_DIR, f"{user_id}.json")
    if os.path.exists(file_path):
        try:
            with open(file_path, "r") as f:
                creds_data = json.load(f)
                return credentials.Credentials.from_dict(creds_data)
        except Exception as e:
            logging.error(f"Error loading credentials: {e}")
    return None


def save_credentials(creds, user_id):
    file_path = os.path.join(USER_CREDENTIALS_DIR, f"{user_id}.json")
    try:
        with open(file_path, "w") as f:
            json.dump(creds_to_dict(creds), f)
    except Exception as e:
        logging.error(f"Error saving credentials: {e}")


def creds_to_dict(creds):
    return {
        'token': creds.token,
        'refresh_token': creds.refresh_token,
        'token_uri': creds.token_uri,
        'client_id': creds.client_id,
        'client_secret': creds.client_secret,
        'scopes': creds.scopes
    }

# Telegram bot initialization
def main():
    logging.basicConfig(level=logging.INFO)

    updater = Updater(TELEGRAM_BOT_TOKEN)
    dp = updater.dispatcher
    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CommandHandler("login", login))
    dp.add_handler(CommandHandler("compose", compose))
    dp.add_handler(CommandHandler("publish", publish))
    dp.add_handler(MessageHandler(Filters.text & ~Filters.command, handle_message))

    # Start telegram bot
    updater.start_polling()
    return updater

if __name__ == '__main__':
    import threading
    # Starts Flask app in a separate thread
    threading.Thread(target=app.run, kwargs={'port': 5000, 'debug':True, 'use_reloader': False}).start()
    main()
