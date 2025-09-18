import os
import datetime
from flask import Flask, render_template_string, request, flash
from PIL import Image
import pytesseract
import spacy

nlp = spacy.load("en_core_web_sm")

app = Flask(_name_)
app.secret_key = "dev"  # required for flash messages
UPLOAD_FOLDER = "uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

HTML_PAGE = """
<!DOCTYPE html>
<html lang=\"en\">
<head>
  <meta charset=\"UTF-8\" />
  <meta name=\"viewport\" content=\"width=device-width,initial-scale=1.0\" />
  <title>TribalGIS OCR & NER</title>
  <link href=\"https://fonts.googleapis.com/css2?family=Roboto:wght@400;500;700;800&display=swap\" rel=\"stylesheet\" />
  <style>
    * { box-sizing: border-box; }
    body { font-family:'Roboto',Arial,sans-serif; margin:0; min-height:100vh; background:linear-gradient(135deg,#e0f7fa 0%,#b2dfdb 50%,#f5f5f5 100%); display:flex; flex-direction:column; }
    .navbar { width:100%; background:linear-gradient(90deg,#1a535c 60%,#2c7a7b 100%); color:#fff; padding:0.8rem 1.5rem; display:flex; align-items:center; justify-content:space-between; box-shadow:0 2px 8px rgba(44,122,123,0.10); }
    .brand { display:flex; align-items:center; gap:0.75rem; font-weight:700; font-size:1.3rem; letter-spacing:1px; }
    .brand-logo { width:46px; height:46px; border-radius:50%; background:#fff; display:flex; align-items:center; justify-content:center; box-shadow:0 2px 8px rgba(44,122,123,0.12); overflow:hidden; }
    .brand-logo img { width:100%; height:100%; object-fit:cover; }
    .nav-links a { color:#fff; text-decoration:none; margin-left:1.5rem; font-weight:500; font-size:1rem; }
    .nav-links a:hover { color:#e0f7fa; }
    .main { flex:1; width:100%; display:flex; align-items:flex-start; justify-content:center; padding:2.5rem 1rem 2rem; }
    .content-grid { width:100%; max-width:1250px; display:grid; grid-template-columns: minmax(340px,400px) minmax(0,1fr); gap:2.2rem; align-items:start; }
    .panel { background:rgba(255,255,255,0.97); border-radius:22px; box-shadow:0 12px 32px rgba(44,122,123,0.18); padding:2.1rem 1.9rem 2.2rem; position:relative; transition:box-shadow .3s; }
    .panel:hover { box-shadow:0 16px 40px rgba(44,122,123,0.22); }
    h1 { margin:0 0 1.1rem; font-size:2rem; font-weight:800; color:#1a535c; letter-spacing:1px; }
    p.lead { margin:0 0 1.4rem; color:#376066; font-size:1.05rem; line-height:1.5; }
    form.upload-form { display:flex; flex-direction:column; gap:1rem; }
    .file-row { display:flex; flex-direction:column; gap:0.6rem; }
    input[type=file] { padding:0.6rem; border:2px dashed #2c7a7b; border-radius:10px; background:#e0f7fa; cursor:pointer; font-weight:500; }
    .btn { background:linear-gradient(135deg,#2c7a7b 60%,#1a535c 100%); color:#fff; border:none; padding:0.85rem 1.4rem; font-size:1rem; font-weight:600; border-radius:10px; cursor:pointer; box-shadow:0 2px 8px rgba(44,122,123,0.10); transition:background .3s; }
    .btn:hover { background:linear-gradient(135deg,#1a535c 60%,#2c7a7b 100%); }
    .flash { background:#ffe9e9; color:#9c2e2e; padding:0.75rem 1rem; border-radius:8px; font-size:0.95rem; margin-top:0.25rem; border:1px solid #f5c2c2; }
    .results-group { display:flex; flex-direction:column; gap:1.8rem; }
    .card { background:#fff; border-radius:18px; padding:1.4rem 1.25rem 1.6rem; box-shadow:0 8px 32px rgba(44,122,123,0.10); position:relative; }
    .card h2 { margin:0 0 0.9rem; font-size:1.25rem; font-weight:700; color:#1a535c; }
    pre { background:#f5fafa; padding:1rem 1rem; border-radius:12px; max-height:320px; overflow:auto; font-size:0.9rem; line-height:1.35; border:1px solid #e0f7fa; }
    ul.ents { list-style:none; padding:0; margin:0; max-height:320px; overflow:auto; display:flex; flex-wrap:wrap; gap:0.55rem; }
    ul.ents li { background:#e0f7fa; border:1px solid #b2dfdb; padding:0.45rem 0.65rem; border-radius:30px; font-size:0.75rem; font-weight:600; color:#1a535c; letter-spacing:0.5px; }
    ul.ents li span { font-weight:400; opacity:.75; margin-left:4px; }
    .empty-note { font-size:0.9rem; color:#376066; }
    .footer { width:100%; background:#f5f5f5; color:#2c7a7b; text-align:center; padding:1rem 0 0.5rem; font-size:0.9rem; letter-spacing:0.5px; box-shadow:0 -2px 8px rgba(44,122,123,0.08); }
    @media (max-width:1100px){ .content-grid { grid-template-columns: 1fr; } .panel { width:100%; } }
    @media (max-width:600px){ h1 { font-size:1.65rem; } .panel { padding:1.65rem 1.15rem 1.4rem; border-radius:0; } .content-grid { gap:1.4rem; } }
  </style>
</head>
<body>
  <div class="navbar">
    <div class="brand">
      <div class="brand-logo"><img src="Gemini_Generated_Image_6p7is6p7is6p7is6-removebg-preview.png" alt="Logo" /></div>
      <span>TribalGIS OCR</span>
    </div>
    <div class="nav-links">
      <a href="/">Home</a>
      <a href="/#how">How</a>
      <a href="/#about">About</a>
    </div>
  </div>
  <div class="main">
    <div class="content-grid">
      <div class="panel">
        <h1>Upload Claim Form Image</h1>
        <p class="lead">Run OCR (Tesseract) and highlight Named Entities (spaCy NER).</p>
        <form method="post" enctype="multipart/form-data" class="upload-form">
          <div class="file-row">
            <input type="file" name="file" accept="image/*" required />
          </div>
          <button class="btn" type="submit">Process Image</button>
          {% with messages = get_flashed_messages() %}
            {% if messages %}
              {% for m in messages %}<div class="flash">{{ m }}</div>{% endfor %}
            {% endif %}
          {% endwith %}
        </form>
      </div>
      <div class="results-group">
        <div class="card">
          <h2>Extracted Text</h2>
          {% if text %}
            <pre>{{ text }}</pre>
          {% else %}
            <div class="empty-note">No text yet. Upload an image to extract content.</div>
          {% endif %}
        </div>
        <div class="card">
          <h2>Named Entities</h2>
          {% if ents and ents|length > 0 %}
            <ul class="ents">
              {% for ent in ents %}
                <li>{{ ent.text }} <span>{{ ent.label_ }}</span></li>
              {% endfor %}
            </ul>
          {% else %}
            <div class="empty-note">No entities extracted yet.</div>
          {% endif %}
        </div>
      </div>
    </div>
  </div>
  <div class="footer">&copy; {{ year }} TribalGIS Platform. All rights reserved. | Contact: info@tribalgis.com</div>
</body>
</html>
"""

@app.route("/", methods=["GET", "POST"])
def upload_file():
    text = None
    ents = []
    if request.method == "POST":
        file = request.files.get("file")
        if not file or file.filename.strip() == "":
            flash("Please choose an image file first.")
        else:
            filepath = os.path.join(UPLOAD_FOLDER, file.filename)
            file.save(filepath)
            try:
                text = pytesseract.image_to_string(Image.open(filepath))
                doc = nlp(text)
                ents = list(doc.ents)
            except Exception as e:
                flash(f"Processing failed: {e}")
    return render_template_string(HTML_PAGE, text=text, ents=ents, year=datetime.datetime.now().year)

if _name_ == "_main_":
    app.run(debug=True)
