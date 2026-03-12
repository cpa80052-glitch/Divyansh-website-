import json
from telegram.ext import Updater, MessageHandler, Filters
import config

TOKEN = config.BOT_TOKEN
ADMIN = config.ADMIN_ID

def save_post(update, context):

    if update.message.from_user.id != ADMIN:
        return

    posts = []

    try:
        with open("posts.json") as f:
            posts = json.load(f)
    except:
        pass

    if update.message.photo:
        file = update.message.photo[-1].get_file()
        url = f"https://api.telegram.org/file/bot{TOKEN}/{file.file_path}"
        posts.append({
            "type": "image",
            "url": url
        })

    if update.message.video:
        file = update.message.video.get_file()
        url = f"https://api.telegram.org/file/bot{TOKEN}/{file.file_path}"
        posts.append({
            "type": "video",
            "url": url
        })

    with open("posts.json","w") as f:
        json.dump(posts,f)

updater = Updater(TOKEN)

updater.dispatcher.add_handler(
    MessageHandler(Filters.photo | Filters.video, save_post)
)

updater.start_polling()
updater.idle()
