from flask import Flask
from flask import render_template

#todo maybe later for organizaiton move static and templates
# in a folder called website in root

app = Flask(__name__)

@app.route("/")
def home():
    return render_template('index.html')