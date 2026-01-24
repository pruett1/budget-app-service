from flask import Flask
from main.env.sandbox import Env
import os

app = Flask(__name__)
config = Env()

@app.route('/ping')
def ping():
    return "pong", 200

@app.route('/dangerdanger')
def danger_danger():
    return config.DANGER, 200

if __name__ == "__main__":
    app.run(debug=True)