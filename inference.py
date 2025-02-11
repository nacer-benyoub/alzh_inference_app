import logging

from config import get_config

from pathlib import Path

import tifffile as tiff

import numpy as np
import pandas as pd

import json
import requests


## Data loading functions
# `load_*_data` functions expect ADNI-like directory structure
def load_2d_data(data_dir: Path, ids_only=False):
    X = []
    ids = {}
    for subject_idx, subject_path in enumerate(data_dir.glob("*")):
        scan_ids = {}
        subject_scans = []
        subject_id = subject_path.stem

        for scan_idx, scan_path in enumerate(subject_path.glob("**/*")):
            scan_imgs = []
            scan_id = scan_path.stem
            scan_ids[scan_id] = []
            for img_idx, img_path in enumerate(scan_path.glob("**/*.tiff")):
                img_name = img_path.stem

                if not ids_only:
                    img = tiff.imread(img_path)
                    if img.shape[-1] not in (1, 3):
                        img = np.expand_dims(img, axis=-1)
                    if img.shape[-1] == 1:
                        img = np.repeat(img, 3, axis=-1)

                    scan_imgs.append(img)

                scan_ids[scan_id].append(img_name)

            subject_scans.append(scan_imgs)

        ids[subject_id] = scan_ids
        subject_scans = np.array(subject_scans)
        X.append(subject_scans)
    if ids_only:
        logger.debug("IDs shape: %s", np.array(ids).shape)
    else:
        logger.debug("X shape: %s", np.array(X).shape)
    return X, ids


def load_3d_data(data_dir: Path, npz_key="image", ids_only=False):
    X = []
    ids = {}
    for subject_idx, subject_path in enumerate(data_dir.glob("*")):
        scan_ids = {}
        subject_scans = []
        subject_id = subject_path.stem

        scan_paths = subject_path.glob("**/*.npz")
        for scan_idx, scan_path in enumerate(scan_paths):
            scan_id = scan_path.parent.stem
            scan_name = scan_path.stem

            if not ids_only:
                img = np.load(scan_path)[npz_key]

            scan_ids[scan_id] = scan_name

            if not ids_only:
                subject_scans.append(img)

        ids[subject_id] = scan_ids
        if not ids_only:
            subject_scans = np.array(subject_scans)
            X.append(subject_scans)
            # X = tf.squeeze(X)
            # X = [np.squeeze(imgs, axis=1) for imgs in X]
    if ids_only:
        logger.debug("IDs shape: %s", np.array(ids).shape)
    else:
        logger.debug("X shape: %s", np.array(X).shape)
    return X, ids


## Prediction functions
def predict_scan(serving_url, scan_imgs):
    data = json.dumps(
        {
            "signature_name": "serving_default",  # TODO Might parametrize this (include in get_config)
            "inputs": scan_imgs.tolist(),
        }
    )
    headers = {"content-type": "application/json"}

    # Make prediction request
    json_response = requests.post(serving_url, data=data, headers=headers)
    response_dict = json.loads(json_response.text)["outputs"]
    scan_preds = response_dict["predictions"]
    labels = response_dict["labels"]
    return scan_preds, labels


def predict_subjects(X, serving_url):
    y_pred = []
    for subject_imgs in X:
        subject_preds = []

        for scan_imgs in subject_imgs:
            scan_preds, labels = predict_scan(serving_url, scan_imgs)
            # Reverse one-hot predictions
            # scan_preds = scan_preds.argmax(axis=-1)

            subject_preds.append(scan_preds)

        y_pred.append(np.array(subject_preds))
    return y_pred, labels


# import yaml
# with open('CLASSES.yaml') as f:
#     label_mapper = yaml.safe_load(f.read())


## df building
def build_df(y_pred, ids, labels, is_2d):
    df = []
    for subject_id, subject_preds in zip(ids.keys(), y_pred):
        for scan_id, scan_preds in zip(ids[subject_id].keys(), subject_preds):
            if is_2d:
                for slice_name, slice_pred in zip(ids[subject_id][scan_id], scan_preds):
                    d = {
                        "subject_id": subject_id,
                        "scan_id": scan_id,
                        "slice_name": slice_name,
                    }
                    d.update({label: pred for label, pred in zip(labels, slice_pred)})
                    df.append(d)
            else:
                for slice_num, slice_pred in enumerate(scan_preds):
                    d = {
                        "subject_id": subject_id,
                        "scan_id": scan_id,
                        "slice_name": f"{ids[subject_id][scan_id]}_slice{slice_num}",
                    }
                    d.update({label: pred for label, pred in zip(labels, slice_pred)})
                    df.append(d)

    df = pd.DataFrame(df).set_index(["subject_id", "scan_id"])
    return df


## Saving functions
def save_slice_pred(df, slice_pred_path):
    slice_preds = (
        df.set_index("slice_name", append=True)
        .groupby("subject_id")
        .apply(
            lambda x: x.droplevel(  # drop subject_id index level
                "subject_id"
            )  # group by scan_id index level
            .groupby("scan_id")
            .apply(
                lambda y: y.droplevel("scan_id").to_dict(  # drop scan_id index level
                    orient="index"
                )
            )
            .to_dict()
        )
    )
    slice_preds.to_json(slice_pred_path, orient="index", indent=4)

    return slice_preds


def save_scan_pred(df, scan_pred_path):
    scan_level_preds = (
        df[["MCI", "AD", "CN"]].groupby(["subject_id", "scan_id"]).aggregate("mean")
    )
    scan_preds_grouped = scan_level_preds.groupby(level=0).apply(
        lambda x: x.droplevel(0).to_dict(orient="index")
    )

    scan_preds_grouped.to_json(scan_pred_path, orient="index", indent=4)
    return scan_level_preds, scan_preds_grouped


def save_subject_pred(scan_level_preds, subject_pred_path):
    subject_preds = scan_level_preds.groupby("subject_id").mean()
    subject_preds.to_json(subject_pred_path, orient="index", indent=4)
    return subject_preds


### Inference
def get_inference_results(input_data=None):
    preprocessed_data_path = CONFIG["preprocessed_data_path"]

    # Define the directory containing the extracted dataset
    data_dir = Path(preprocessed_data_path)

    # Load the data
    ids_only = input_data is not None
    if CONFIG["save_2d"]:
        X, ids = load_2d_data(data_dir=data_dir, ids_only=ids_only)
    else:
        X, ids = load_3d_data(data_dir=data_dir, ids_only=ids_only)

    X = input_data if ids_only else X

    # Log subject ids and scan shapes
    for subject_id, subject_imgs in zip(ids.keys(), X):
        logger.debug("Shape of %s images: %s", subject_id, subject_imgs.shape)

    serving_url = CONFIG["serving_url"]

    # Inference loop
    y_pred, labels = predict_subjects(X, serving_url)

    # Log subject ids and pred shapes
    for subject_id, subject_preds in zip(ids.keys(), y_pred):
        logger.debug("Shape of %s preds: %s", subject_id, subject_preds.shape)

    # Build predictions df
    df = build_df(y_pred, ids, labels, is_2d=CONFIG["save_2d"])

    return df


### Saving the predictions
def save_preds(df):
    pred_path = CONFIG["pred_path"]
    if not pred_path.exists():
        pred_path.mkdir(parents=True, exist_ok=True)

    # Save slice-level predictions to `slice_predictions.json`
    slice_pred_path = pred_path.joinpath("slice_predictions.json")
    slice_preds_grouped = save_slice_pred(df, slice_pred_path)

    # Save scan-level predictions to `scan_predictions.json`
    scan_pred_path = pred_path.joinpath("scan_predictions.json")
    scan_level_preds, scan_preds_grouped = save_scan_pred(df, scan_pred_path)

    # Save subject-level predicitons to `subject_predictions.json`
    subject_pred_path = pred_path.joinpath("subject_predictions.json")
    subject_preds_grouped = save_subject_pred(scan_level_preds, subject_pred_path)

    preds_data = {
        "slice_predictions": slice_preds_grouped.to_dict(),
        "scan_predictions": scan_preds_grouped.to_dict(),
        "subject_predictions": subject_preds_grouped.to_dict(orient="index"),
    }

    return preds_data


### Main
def run_inference(X=None):
    # Run inference and get the results
    df = get_inference_results(X)

    # Save the results as json files
    preds_data = save_preds(df)

    return preds_data


# Load the CONFIG
CONFIG = get_config()
logger = logging.getLogger("processing.inference")
if __name__ == "__main__":
    run_inference()
