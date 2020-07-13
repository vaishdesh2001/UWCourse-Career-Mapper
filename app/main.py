from flask import Flask, render_template, request
from course_gen import main

app = Flask(__name__)
app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 0
app.config['SECRET_KEY'] = '5791628bb0b13ce0c676dfde280ba245'


@app.route("/")
@app.route("/home")
def home_view():
    return render_template("main_page.html", title="homepage")


@app.route("/about")
def about():
    return render_template("about.html", title="About")


@app.route("/output", methods=['GET', 'POST'])
def output():
    name = request.args.get('job')
    main(name)
    return render_template(name + "op.html", title="Courses", name=name)


# No caching at all for API endpoints.
@app.after_request
def add_header(response):
    # response.cache_control.no_store = True
    response.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, post-check=0, pre-check=0, max-age=0'
    response.headers['Pragma'] = 'no-cache'
    response.headers['Expires'] = '-1'
    return response

