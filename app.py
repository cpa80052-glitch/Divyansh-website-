from flask import Flask, render_template
import json

app = Flask(__name__)

def load_posts():
    try:
        with open("posts.json") as f:
            return json.load(f)
    except:
        return []

@app.route("/")
def intro():
    return render_template("intro.html")

@app.route("/home")
def home():
    return render_template("home.html")

@app.route("/posts")
def posts():
    posts = load_posts()
    return render_template("posts.html", posts=posts)

if __name__ == "__main__":
    app.run()
