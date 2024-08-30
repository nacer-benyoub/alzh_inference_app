import os

from get_config import get_config_dict

from pathlib import Path

import tifffile as tiff

import numpy as np
import pandas as pd

import json
import requests

CONFIG = get_config_dict()

# ### Load the data
# `load_*_data` functions expect ADNI-like directory structure


# Load images
def load_2d_data(data_dir: Path):
    X = []
    ids = {}
    for subject_idx, subject_path in enumerate(data_dir.glob("*")):
        scan_ids = {}
        subject_scans = []
        subject_id = subject_path.stem

        for scan_idx, scan_path in enumerate(subject_path.glob("**/I*")):
            scan_imgs = []
            scan_id = scan_path.stem
            scan_ids[scan_id] = []
            for img_idx, img_path in enumerate(scan_path.glob("**/*.tiff")):
                img_name = img_path.stem

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
    return X, ids


def load_3d_data(data_dir: Path, npz_key="image"):
    X = []
    ids = {}
    for subject_idx, subject_path in enumerate(data_dir.glob("*")):
        scan_ids = {}
        subject_scans = []
        subject_id = subject_path.stem

        scan_paths = subject_path.glob("**/*.npz")
        for scan_idx, scan_path in enumerate(scan_paths):
            scan_imgs = []
            scan_id = scan_path.parent.stem
            scan_name = scan_path.stem

            img = np.load(scan_path)[npz_key]

            scan_imgs.append(img)
            scan_ids[scan_id] = scan_name

            subject_scans.append(scan_imgs)

        ids[subject_id] = scan_ids
        subject_scans = np.array(subject_scans)
        X.append(subject_scans)
    # X = tf.squeeze(X)
    return X, ids


preprocessed_data_path = CONFIG["preprocessed_data_path"]

# Define the directory containing the extracted dataset
data_dir = Path(preprocessed_data_path)
if CONFIG["save_2d"]:
    X, ids = load_2d_data(data_dir)
else:
    X, ids = load_3d_data(data_dir)
    X = [np.squeeze(imgs, axis=1) for imgs in X]

for (idx, subject_imgs), subject_id in zip(enumerate(X), ids.keys()):
    # print(subject_imgs.shape)
    print(f"Shape of {subject_id} images:", subject_imgs.shape)


# ### Inference
serving_url = CONFIG["serving_url"]

# Inference loop
y_pred = []
for subject_imgs in X:
    subject_preds = []

    for scan_imgs in subject_imgs:
        # Make prediction request
        data = json.dumps(
            {
                "signature_name": "serving_default",  # TODO Might parametrize this (include in get_config)
                "inputs": scan_imgs.tolist(),
            }
        )
        headers = {"content-type": "application/json"}
        json_response = requests.post(serving_url, data=data, headers=headers)
        response_dict = json.loads(json_response.text)["outputs"]
        scan_preds = response_dict["predictions"]
        # Reverse one-hot predictions
        # scan_preds = scan_preds.argmax(axis=-1)

        subject_preds.append(scan_preds)

    y_pred.append(np.array(subject_preds))

for subject_preds, subject_id in zip(y_pred, ids.keys()):
    print(f"Shape of {subject_id} preds:", subject_preds.shape)


# import yaml
# with open('CLASSES.yaml') as f:
#     label_mapper = yaml.safe_load(f.read())


def build_df(y_pred, ids, is_2d):
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
                    d.update(
                        {
                            label: pred
                            for label, pred in zip(response_dict["labels"], slice_pred)
                        }
                    )
                    df.append(d)
            else:
                for slice_num, slice_pred in enumerate(scan_preds):
                    d = {
                        "subject_id": subject_id,
                        "scan_id": scan_id,
                        "slice_name": f"{ids[subject_id][scan_id]}_slice{slice_num}",
                    }
                    d.update(
                        {
                            label: pred
                            for label, pred in zip(response_dict["labels"], slice_pred)
                        }
                    )
                    df.append(d)

    df = pd.DataFrame(df).set_index(["subject_id", "scan_id"])
    return df


if CONFIG["save_2d"]:
    df = build_df(y_pred, ids, is_2d=True)
else:
    df = build_df(y_pred, ids, is_2d=False)

# ### Saving the predictions

pred_path = CONFIG["pred_path"]
if not pred_path.exists():
    pred_path.mkdir(parents=True, exist_ok=True)


# Save slice-level predictions to `slice_predictions.json`
slice_pred_path = pred_path.joinpath("slice_predictions.json")

df.set_index("slice_name", append=True).groupby("subject_id").apply(
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
).to_json(slice_pred_path, orient="index", indent=4)

# Save scan-level predictions to `scan_predictions.json`
scan_pred_path = pred_path.joinpath("scan_predictions.json")

scan_level_preds = (
    df[["MCI", "AD", "CN"]].groupby(["subject_id", "scan_id"]).aggregate("mean")
)
scan_level_preds.groupby(level=0).apply(
    lambda x: x.droplevel(0).to_dict(orient="index")
).to_json(scan_pred_path, orient="index", indent=4)


# Save subject-level predicitons to `subject_predictions.json`
subject_pred_path = pred_path.joinpath("subject_predictions.json")

scan_level_preds.groupby("subject_id").mean().to_json(
    subject_pred_path, orient="index", indent=4
)
