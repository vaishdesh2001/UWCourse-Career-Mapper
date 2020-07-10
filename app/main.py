from flask import Flask, render_template

app = Flask(__name__)


@app.route("/")
def home_view():
    return render_template("main_page.html", title = "homepage")
