import yaml
from logging.config import dictConfig
from datetime import datetime
import shutil
import uuid

from numpy import array
from config import get_config
from flask import Flask, request, jsonify
from preprocessing import run_preprocessing
from inference import run_inference
import os


def setup_logging(config_filename="logs/config.yml"):
    with open(config_filename) as f:
        log_config = yaml.safe_load(f)
    dictConfig(log_config)


setup_logging()

app = Flask("processing")

CONFIG = get_config()


def generate_subject_id(existing_ids):
    while True:
        uid = uuid.uuid4()
        subject_id = f"{str(uid.int)[:3]}_S_{str(uid.int)[3:7]}"
        if subject_id not in existing_ids:
            return subject_id


def generate_image_id(existing_ids):
    while True:
        uid = uuid.uuid4()
        image_id = f"I{str(uid.int)[:5]}"
        if image_id not in existing_ids:
            return image_id


def ensure_raw_data_dir_structure(
    subject_id, image_id, image_date_time=None, image_type="MRI"
):
    # TODO Remove image_type if not required by processing and inference scripts
    # TODO get image_date_time from uploaded nii/dicom files if possible

    # Prepare the directry names
    raw_data_dir = CONFIG["raw_data_path"]
    os.makedirs(raw_data_dir, exist_ok=True)
    existing_subject_ids = set(os.listdir(raw_data_dir))

    # Generate subject_id if not provided
    if subject_id is None:
        subject_id = generate_subject_id(existing_subject_ids)

    # Generate image_date_time if not provided
    if image_date_time is None:
        # image_date_time = datetime.now().strftime("%Y-%m-%d_%H_%M_%S")
        image_date_time = datetime.now().strftime("%Y-%m-%d")

    # Create image_date_time directory
    image_date_time_path = os.path.join(
        raw_data_dir, subject_id, image_type, image_date_time
    )
    os.makedirs(image_date_time_path, exist_ok=True)

    # Generate image_id if not provided
    existing_image_ids = [d for d in os.listdir(image_date_time_path)]
    if image_id is None:
        image_id = generate_image_id(existing_image_ids)

    # Create image id directory directory
    image_id_path = os.path.join(image_date_time_path, image_id)
    os.makedirs(image_id_path, exist_ok=True)

    return image_id_path


@app.route("/upload", methods=["POST"])
def recieve_files():
    # Extract the file and data
    received_files = request.files.getlist("files")
    subject_id = request.form["subject_id"] if "subject_id" in request.form else None
    image_id = request.form["image_id"] if "image_id" in request.form else None
    if received_files:
        # Save the file to the raw_data directory
        image_id_path = ensure_raw_data_dir_structure(subject_id, image_id)
        for file_ in received_files:
            file_path = os.path.join(image_id_path, file_.filename)
            file_.save(file_path)


@app.route("/predict", methods=["POST"])
def process_files():
    # Extract the file and data
    received_files = request.files.getlist("files")
    subject_id = request.form["subject_id"] if "subject_id" in request.form else None
    image_id = request.form["image_id"] if "image_id" in request.form else None
    app.logger.debug(f"received files count: {len(received_files)}")
    app.logger.debug(f"subject_id: {subject_id}")
    app.logger.debug(f"image_id: {image_id}")
    if received_files:
        # Save the file to the raw_data directory
        image_id_path = ensure_raw_data_dir_structure(subject_id, image_id)
        for file_ in received_files:
            file_path = os.path.join(image_id_path, file_.filename)
            file_.save(file_path)

        # Convert DICOM files to NIfTI if any are present
        if any([file_.filename.endswith(".dcm") for file_ in received_files]):
            app.logger.info("Detected DICOM scans. Coverting to NIfTI...")
            os.system(f"dcm2niix {image_id_path}")
            app.logger.info("Scans converted.")

        app.logger.debug(f"image_id path: {image_id_path}")
        # Run preprocessing
        # TODO: Eliminate IO and pass the files directly to preprocessing
        # which fixes the limitation of relying on the ADNI folder structure
        X = run_preprocessing(subject_id, image_id, image_id_path)

        if X:
            app.logger.debug(f"X shape: {array(X).shape}")
        else:
            app.logger.debug(f"Cache hit. Preprocessing skipped")

        # Run inference
        preprocessed_image_id_path = image_id_path.replace("raw", "preprocessed")
        pred_data = run_inference(X, subject_id, image_id, preprocessed_image_id_path)

        # Initialize the response
        result = {"status": "success"}

        # Read the resulting json files
        result["data"] = pred_data

        # Clean the data directory:
        if CONFIG["clean_data_dir"]:
            for directory in [
                CONFIG["raw_data_path"],
                CONFIG["preprocessed_data_path"],
            ]:
                shutil.rmtree(directory)

        # Return the post-processed results
        return jsonify(result)


if __name__ == "__main__":
    port = os.environ["PROCESSING_CONTAINER_PORT"]
    app.run(host="0.0.0.0", port=port, debug=True)
