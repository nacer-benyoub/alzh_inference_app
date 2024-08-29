import os
from flask import Flask, render_template, request, redirect, url_for
import requests  # For communicating with processing container

app = Flask(__name__)

# Define processing container URL (replace with actual URL)
PROCESSING_SERVICE_URL = os.environ['PROCESSING_SERVICE_URL']
if not PROCESSING_SERVICE_URL.endswith('/'):
    PROCESSING_SERVICE_URL += '/'

@app.route('/')
def cover():
    return render_template('cover.html')

@app.route('/process')
def process():
    return render_template('process.html')

@app.route("/upload", methods=["GET", "POST"])
def upload():
    if request.method == "POST":
        # Get the file and data from the user 
        uploaded_file = request.files["file"]
        subject_id = request.form['subject_id']
        if not subject_id:
            subject_id = None
        image_id = request.form['image_id']
        if not image_id:
            image_id = None
        
        # Post processing request and get results
        payload = {"subject_id": subject_id, "image_id": image_id}
        app.logger.debug(f"file filename {uploaded_file.filename}")
        app.logger.debug(f"file type {type(uploaded_file)}")
        file_payload = {"file": (uploaded_file.filename, uploaded_file)}
        response = requests.post(PROCESSING_SERVICE_URL + "predict", files=file_payload, data=payload)
        json = response.json()
        if json['status'] == 'success':
            data = json['data']
            # TODO send the data to the results endpoint instead (for further processing)
            return render_template("results.html", data=data)
        # else: TODO
        #     report error the flask way
        #     maybe 'return "Failed processing uploaded files"'
        #     or 'return "<script> js alert ..."'
    return render_template("upload.html")

@app.route("/results")
def results():
    # Handle cases where data is not available (e.g., no upload yet)
    
    return render_template("results.html")

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=8080, debug=True)
