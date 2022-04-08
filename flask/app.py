import os, sys
from flask import Flask, redirect, render_template, request
sys.path.append("../")
import arasas

app = Flask(__name__)
words_limit = 100000

@app.route("/api")
def api():
    text = request.values.get('text')
    if len(text.split(' ')) > words_limit:
        text = " ".join(text.split(' ')[:words_limit])
    style = request.values.get('style')
    annotation = arasas.annotate(text, output_format=style, lexicon="../arasas_lexicon.usas")
    return annotation

@app.route("/usas", methods=["POST"])
def usas():
    text = request.values.get('text')
    if len(text.split(' ')) > words_limit:
        text = " ".join(text.split(' ')[:words_limit])
    style = request.values.get('style')
    annotation = arasas.annotate(text, output_format=style, lexicon="../arasas_lexicon.usas")
    return render_template(
        'usas.html',
        output=annotation['string'],
        word_count=annotation['log']['tokens'],
    )

@app.route('/')
def home():
    return render_template(
        'index.html',
        )

if __name__ == "__main__":
    app.run()