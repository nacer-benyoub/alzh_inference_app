import yaml
from logging.config import dictConfig
import os
from flask import Flask, jsonify, render_template, request, redirect, url_for
import requests  # For communicating with processing container
import json5


def setup_logging(config_filename="logs/config.yml"):
    with open(config_filename) as f:
        log_config = yaml.safe_load(f)
    dictConfig(log_config)


setup_logging()

app = Flask("webapp")

# Define processing container URL (replace with actual URL)
PROCESSING_SERVICE_URL = os.environ["PROCESSING_SERVICE_URL"]
if not PROCESSING_SERVICE_URL.endswith("/"):
    PROCESSING_SERVICE_URL += "/"


@app.route("/")
def home():
    return render_template("home.html")


@app.route("/upload_js")
def upload_js():
    return render_template("script.js")


@app.route("/upload", methods=["GET", "POST"])
def upload():
    if request.method == "POST":
        # Get the file and data from the user
        uploaded_files = request.files.getlist("file")
        if "subject_id" in request.form.keys():
            subject_id = request.form["subject_id"]
            if not subject_id:
                subject_id = None
        else:
            subject_id = None

        if "image_id" in request.form.keys():
            image_id = request.form["image_id"]
            if not image_id:
                image_id = None
        else:
            image_id = None

        # Save the uploaded files
        os.makedirs(os.path.join(os.getcwd(), "uploads"), exist_ok=True)
        for _file in uploaded_files:
            _file.save(os.path.join("uploads", _file.filename))
        return "", 200

    return render_template("upload.html")


@app.route("/submit", methods=["POST"])
def submit():
    if request.method == "POST":
        # Get the file and data from the user
        uploaded_files = request.files.getlist("file")
        if "subject_id" in request.form.keys():
            subject_id = request.form["subject_id"]
            if not subject_id:
                subject_id = None
        else:
            subject_id = None

        if "image_id" in request.form.keys():
            image_id = request.form["image_id"]
            if not image_id:
                image_id = None
        else:
            image_id = None

        # Post processing request and get results
        payload = {"subject_id": subject_id, "image_id": image_id}
        app.logger.debug(f"subject_id: {subject_id}")
        app.logger.debug(f"image_id: {image_id}")
        app.logger.debug(f"files count: {len(uploaded_files)}")
        app.logger.debug(f"files types: {[type(file_) for file_ in uploaded_files]}")
        file_payload = []
        for file_ in uploaded_files:
            file_payload.append(
                ("files", (file_.filename, file_.read(), file_.content_type))
            )
        response = requests.post(
            PROCESSING_SERVICE_URL + "predict", files=file_payload, data=payload
        )
        response_json = response.json()
        if response_json["status"] == "success":
            data = response_json["data"]
            return jsonify({"redirect": url_for("results", data=data)})


@app.route("/results/<data>")
def results(data):
    # TODO: Handle cases where data is not available (e.g., no upload yet)
    data = json5.loads(data)
    return render_template("results.html", data=data)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080, debug=True)
