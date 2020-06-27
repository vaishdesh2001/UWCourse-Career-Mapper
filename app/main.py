from flask import Flask, render_template

app = Flask(__name__)


@app.route("/")
def home_view():
    #return render_template("home.html", title = "homepage")
    return "<h1>Welcome to Geeks for Geeks</h1>"
