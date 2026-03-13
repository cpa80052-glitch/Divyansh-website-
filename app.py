from flask import Flask, render_template, request, jsonify, send_from_directory
import json, os, asyncio, threading
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, ContextTypes, filters

app = Flask(__name__)
POST_FILE = "posts.json"
UPLOAD_FOLDER = "uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Telegram Bot Token (Render pe environment variable mein daalna)
BOT_TOKEN = os.environ.get("BOT_TOKEN", "YOUR_BOT_TOKEN_HERE")

def load_posts():
    if not os.path.exists(POST_FILE):
        return []
    with open(POST_FILE, encoding='utf-8') as f:
        return json.load(f)

def save_posts(data):
    with open(POST_FILE, "w", encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

# ========== WEB ROUTES ==========

@app.route("/")
def intro():
    return render_template("intro.html")

@app.route("/home")
def home():
    return render_template("home.html")

@app.route("/posts")
def posts():
    return render_template("posts.html", posts=load_posts())

@app.route("/watch/<int:pid>")
def watch(pid):
    posts = load_posts()
    post = next((p for p in posts if p["id"] == pid), None)
    if not post:
        return "Video not found", 404
    return render_template("watch.html", post=post, posts=posts)

@app.route("/chat")
def chat():
    return render_template("chat.html")

@app.route("/like/<int:pid>", methods=["POST"])
def like(pid):
    posts = load_posts()
    for p in posts:
        if p["id"] == pid:
            p["likes"] = p.get("likes", 0) + 1
            save_posts(posts)
            return jsonify({"ok": True, "likes": p["likes"]})
    return jsonify({"ok": False}), 404

@app.route("/comment/<int:pid>", methods=["POST"])
def comment(pid):
    data = request.json
    posts = load_posts()
    for p in posts:
        if p["id"] == pid:
            if "comments" not in p:
                p["comments"] = []
            new_comment = {
                "id": len(p["comments"]) + 1,
                "user": data.get("user", "Anonymous"),
                "text": data.get("text", ""),
                "time": "Just now"
            }
            p["comments"].append(new_comment)
            save_posts(posts)
            return jsonify({"ok": True, "comment": new_comment})
    return jsonify({"ok": False}), 404

@app.route("/uploads/<path:filename>")
def uploaded_file(filename):
    return send_from_directory(UPLOAD_FOLDER, filename)

# ========== TELEGRAM BOT ==========

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("🎬 View All Posts", url=f"https://{os.environ.get('RENDER_EXTERNAL_HOSTNAME', 'localhost:5000')}/posts")],
        [InlineKeyboardButton("💬 Open Chat", url=f"https://{os.environ.get('RENDER_EXTERNAL_HOSTNAME', 'localhost:5000')}/chat")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(
        "🎥 *Welcome to Video Hub Bot!*\n\n"
        "Send me videos, photos, or text posts and I'll upload them to the website instantly!\n\n"
        "Commands:\n"
        "/posts - View all posts\n"
        "/stats - View statistics",
        reply_markup=reply_markup,
        parse_mode='Markdown'
    )

async def handle_video(update: Update, context: ContextTypes.DEFAULT_TYPE):
    posts = load_posts()
    new_id = max([p["id"] for p in posts], default=0) + 1
    
    video_file = await update.message.video.get_file()
    filename = f"video_{new_id}.mp4"
    filepath = os.path.join(UPLOAD_FOLDER, filename)
    await video_file.download_to_drive(filepath)
    
    caption = update.message.caption or "No description"
    
    new_post = {
        "id": new_id,
        "type": "video",
        "file": f"uploads/{filename}",
        "title": caption[:50] + "..." if len(caption) > 50 else caption,
        "description": caption,
        "likes": 0,
        "views": 0,
        "comments": [],
        "uploader": update.message.from_user.first_name,
        "time": "Just now"
    }
    posts.append(new_post)
    save_posts(posts)
    
    await update.message.reply_text(f"✅ Video uploaded successfully!\nPost ID: {new_id}\nView: /posts")

async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    posts = load_posts()
    new_id = max([p["id"] for p in posts], default=0) + 1
    
    photo_file = await update.message.photo[-1].get_file()
    filename = f"photo_{new_id}.jpg"
    filepath = os.path.join(UPLOAD_FOLDER, filename)
    await photo_file.download_to_drive(filepath)
    
    caption = update.message.caption or "No description"
    
    new_post = {
        "id": new_id,
        "type": "photo",
        "file": f"uploads/{filename}",
        "title": caption[:50] + "..." if len(caption) > 50 else caption,
        "description": caption,
        "likes": 0,
        "views": 0,
        "comments": [],
        "uploader": update.message.from_user.first_name,
        "time": "Just now"
    }
    posts.append(new_post)
    save_posts(new_post)
    
    await update.message.reply_text(f"✅ Photo uploaded!\nPost ID: {new_id}")

async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    posts = load_posts()
    new_id = max([p["id"] for p in posts], default=0) + 1
    
    new_post = {
        "id": new_id,
        "type": "text",
        "title": update.message.text[:50] + "..." if len(update.message.text) > 50 else update.message.text,
        "description": update.message.text,
        "likes": 0,
        "views": 0,
        "comments": [],
        "uploader": update.message.from_user.first_name,
        "time": "Just now"
    }
    posts.append(new_post)
    save_posts(posts)
    
    await update.message.reply_text(f"✅ Text post created!\nPost ID: {new_id}")

def run_bot():
    application = Application.builder().token(BOT_TOKEN).build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.VIDEO, handle_video))
    application.add_handler(MessageHandler(filters.PHOTO, handle_photo))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
    application.run_polling()

if __name__ == "__main__":
    # Start bot in separate thread
    if BOT_TOKEN != "YOUR_BOT_TOKEN_HERE":
        bot_thread = threading.Thread(target=run_bot)
        bot_thread.daemon = True
        bot_thread.start()
    
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
    