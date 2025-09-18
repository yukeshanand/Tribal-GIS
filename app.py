import os
from flask import Flask, render_template_string, request
from PIL import Image
import pytesseract
import spacy

# Load spaCy model
nlp = spacy.load("en_core_web_sm")

# Flask app
app = Flask(__name__)
UPLOAD_FOLDER = "uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

HTML_PAGE = """
<!doctype html>
<title>FRA OCR + NER Demo</title>
<h1>Upload Claim Form Image</h1>
<form method=post enctype=multipart/form-data>
  <input type=file name=file>
  <input type=submit value=Upload>
</form>
{% if text %}
<h2>Extracted Text</h2>
<pre>{{ text }}</pre>
<h2>Named Entities</h2>
<ul>
{% for ent in ents %}
  <li>{{ ent.text }} — {{ ent.label_ }}</li>
{% endfor %}
</ul>
{% endif %}
"""

@app.route("/", methods=["GET", "POST"])
def upload_file():
    if request.method == "POST":
        file = request.files["file"]
        if file:
            filepath = os.path.join(UPLOAD_FOLDER, file.filename)
            file.save(filepath)

            # OCR
            text = pytesseract.image_to_string(Image.open(filepath))

            # NER
            doc = nlp(text)
            return render_template_string(HTML_PAGE, text=text, ents=doc.ents)
    return render_template_string(HTML_PAGE)

if __name__ == "__main__":
    app.run(debug=True)
