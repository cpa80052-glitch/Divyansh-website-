
from flask import Flask, render_template, request, jsonify
import json, os

app = Flask(__name__)
POST_FILE="posts.json"

def load_posts():
    if not os.path.exists(POST_FILE):
        return []
    with open(POST_FILE) as f:
        return json.load(f)

def save_posts(data):
    with open(POST_FILE,"w") as f:
        json.dump(data,f,indent=2)

@app.route("/")
def intro():
    return render_template("intro.html")

@app.route("/home")
def home():
    return render_template("home.html")

@app.route("/posts")
def posts():
    return render_template("posts.html", posts=load_posts())

@app.route("/like/<int:pid>",methods=["POST"])
def like(pid):
    posts=load_posts()
    for p in posts:
        if p["id"]==pid:
            p["likes"]+=1
    save_posts(posts)
    return {"ok":True}

if __name__=="__main__":
    app.run(host="0.0.0.0",port=int(os.environ.get("PORT",5000)))
