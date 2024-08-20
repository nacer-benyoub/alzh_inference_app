from datetime import datetime
import json
from pathlib import Path
import uuid
from get_config import get_config_dict
from flask import Flask, request, jsonify
import os

app = Flask(__name__)

CONFIG = get_config_dict()


def generate_subject_id(existing_ids):
    while True:
        uid = uuid.uuid4()
        subject_id = f"{str(uid.int)[:3]}_S_{str(uid.int)[3:7]}"
        if subject_id not in existing_ids:
            return subject_id


def generate_image_id(existing_ids):
    while True:
        uid = uuid.uuid4()
        image_id = f"I{str(uid.int)[:7]}"
        if image_id not in existing_ids:
            return image_id


def ensure_raw_data_dir_structure(subject_id, image_id, image_date_time=None, image_type="MRI"):
    # Remove image_type if not required by processing and inference scripts
    
    # Prepare the directry names
    raw_data_dir = CONFIG["raw_data_path"]
    os.makedirs(raw_data_dir, exist_ok=True)
    existing_subject_ids = set(os.listdir(raw_data_dir))

    # Generate subject_id if not provided
    if subject_id is None:
        subject_id = generate_subject_id(existing_subject_ids)

    # Generate image_date_time if not provided
    if image_date_time is None:
        image_date_time = datetime.now().strftime("%Y-%m-%d_%H_%M_%S")

    # Create image_date_time directory
    image_date_time_path = os.path.join(raw_data_dir, subject_id, image_type, image_date_time)
    os.makedirs(image_date_time_path, exist_ok=True)

    # Generate image_id if not provided
    image_ids = [d for d in os.listdir(image_date_time_path)]
    if image_id is None:
        image_id = generate_image_id(image_ids)

    # Create image id directory directory
    image_id_path = os.path.join(image_date_time_path, image_id)
    os.makedirs(image_id_path, exist_ok=True)

    return image_id_path


@app.route("/predict", methods=["POST"])
def process_file():
    # Extract the file and data
    received_file = request.files["file"]
    subject_id = request.form['subject_id'] if "subject_id" in request.form else None
    image_id = request.form['image_id'] if "image_id" in request.form else None
    if received_file:
        # Save the file to the raw_data directory
        image_id_path = ensure_raw_data_dir_structure(subject_id, image_id)
        file_path = os.path.join(image_id_path, received_file.filename)
        received_file.save(file_path)

        # Perform processing
        os.system("./run.sh")

        # Initialize the response
        result = {"status": "success"}

        # Read the resulting json files
        json_filenames = Path(CONFIG["pred_path"]).glob("*.json")
        json_data = {}
        for filename in json_filenames:
            app.logger.debug(f"filename {filename}")
            json_data[filename.stem] = json.load(open(filename))
        result["data"] = json_data

        # Return the post-processed results
        return jsonify(result)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
