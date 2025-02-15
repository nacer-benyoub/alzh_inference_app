import logging
import numpy as np
from pathlib import Path
import os
import time
import datetime
import SimpleITK as sitk
from typing import List
from config import get_config
from PIL import Image


def get_unique_image_file(subject_image_files: List[Path]) -> np.array:
    # the inversion [::-1] is done so the most preprocessed data is used
    found_image_ids = np.array(
        [image_file.parents[0].name for image_file in subject_image_files]
    )
    inverse_found_image_ids = found_image_ids[::-1]
    ids, idx = np.unique(inverse_found_image_ids, return_index=True)
    unique_image_ids_paths = np.array(subject_image_files)[::-1][idx]

    assert len(unique_image_ids_paths) <= len(subject_image_files)
    assert len(unique_image_ids_paths) > 0

    return unique_image_ids_paths


def intensity_normalization(volume: np.array, clip_ratio: float = 99.5):
    # Normalize the pixel values of volumes to (-1, 1)
    assert np.min(volume) == 0.0
    volume_max = np.percentile(volume, clip_ratio)
    volume = np.clip(volume / volume_max, 0, 1) * 2 - 1

    return volume


def run_fsl_processing(image_path: Path, preprocessed_image_path: Path, ref: Path):
    # Remove all suffixes
    path_no_ext = preprocessed_image_path.with_suffix("")
    while path_no_ext.suffixes:
        path_no_ext = path_no_ext.with_suffix("")

    orient_path = path_no_ext.with_name(f"{path_no_ext.stem}_orient.nii.gz")
    os.system(f"fslreorient2std {image_path} {orient_path}")

    fov_path = path_no_ext.with_name(f"{path_no_ext.stem}_fov.nii.gz")
    os.system(f"robustfov -i {orient_path} -r {fov_path}")

    bet_path = path_no_ext.with_name(f"{path_no_ext.stem}_bet.nii.gz")
    os.system(f"bet {fov_path} {bet_path} -R")

    os.system(f"flirt -in {bet_path} -ref {ref} -out {preprocessed_image_path}")

    # "fast" saves output file as {file_name}_restore.nii.gz
    # os.system(f'fast --nopve -B -o {preprocessed_image_path} {preprocessed_image_path}')
    # preprocessed_image_path_fsl = Path(str(preprocessed_image_path).replace(".nii", "_restore.nii"))

    # Remove the temp nii files
    for path in [orient_path, fov_path, bet_path]:
        path.unlink()

    return preprocessed_image_path


def load_np_image(preprocessed_image_path: Path) -> np.array:
    ## load image
    # TODO get rid of SimpleITK dependency and use an existing one instead
    preprocessed_image_sitk = sitk.ReadImage(str(preprocessed_image_path))
    preprocessed_image_np = sitk.GetArrayFromImage(preprocessed_image_sitk)
    return preprocessed_image_np


def cropping(
    image: np.array,
    axial_size: int = 180,
    central_crop_along_z: bool = True,
    central_crop_size: int = 30,
):
    init_shape = image.shape
    cropped_image = image
    if axial_size is not None:
        cropped_image = cropped_image[
            :,
            init_shape[1] // 2 - axial_size // 2 : init_shape[1] // 2 + axial_size // 2,
            init_shape[2] // 2 - axial_size // 2 : init_shape[2] // 2 + axial_size // 2,
        ]
    if central_crop_along_z:
        cropped_image = cropped_image[
            init_shape[0] // 2
            - central_crop_size // 2 : init_shape[0] // 2
            + central_crop_size // 2,
            ...,
        ]

    return cropped_image


def save_np(image_np, preprocessed_image_path):
    preprocessed_image_path = str(preprocessed_image_path).replace(".nii.gz", "")

    # Transform the image into 3-channel format if it's in 1-channel format
    if len(image_np.shape) == 3:
        image_np = np.expand_dims(image_np, axis=-1)
        image_np = np.repeat(image_np, 3, axis=-1)

    data_dict = {"image": image_np}
    np.savez_compressed(preprocessed_image_path, **data_dict)  # saving into .npz
    return image_np


def save_2d(image_np, preprocessed_image_path):
    # preprocessed_image_path = str(preprocessed_image_path)[:str(preprocessed_image_path).rfind(".")]
    new_preprocessed_image_path = str(preprocessed_image_path).replace(".nii.gz", "")
    for slice in range(image_np.shape[0]):
        Image.fromarray(image_np[slice]).save(
            new_preprocessed_image_path + f"_slice{slice}.tiff"
        )
    return image_np


def remove_nii_files(path: Path):
    for file_ in path.parent.glob("**/*.nii*"):
        file_.unlink()


def run_preprocessing(subject_id, image_id, image_id_path):
    X = []

    total_start = time.time()
    image_id_path = Path(image_id_path)
    image_files = list(image_id_path.glob("**/*.nii"))
    total_image_count = len(image_files)
    total_processed_images_count = 0
    subject_scans = []
    
    for image_index, image_path in enumerate(image_files):
        logger.info(
            f"Processing image {image_id} ({image_index + 1}/{total_image_count}) for subject {subject_id} ..."
        )

        preprocessed_image_path = Path(
            str(image_path)
            .replace("raw", "preprocessed")
            .replace(".nii", ".nii.gz")
        )
        preprocessed_image_path.parent.mkdir(parents=True, exist_ok=True)

        if CONFIG["save_2d"]:
            existing_processed_files_count = len(
                list(preprocessed_image_path.parent.glob("**/*.tiff"))
            )
        else:
            existing_processed_files_count = len(
                list(preprocessed_image_path.parent.glob("**/*.npz"))
            )
        if existing_processed_files_count > 0 and not CONFIG["re_process"]:
            total_processed_images_count += 1
            logger.info("Preprocessed images already exist. Skipping...")
            image_np = None
            continue

        start = time.time()
        try:

            logger.info("======== FSL output ========")

            preprocessed_image_path_fsl = run_fsl_processing(
                image_path,
                preprocessed_image_path,
                CONFIG["reference_atlas_location"],
            )
            logger.info("======== FSL output ========")

            preprocessed_image_np = load_np_image(preprocessed_image_path_fsl)
        except:
            with open("load_error_list.txt", "a") as the_file:
                the_file.write(f"{str(image_path)}\n")
            continue

        normalized_image_np = intensity_normalization(preprocessed_image_np)

        if CONFIG["axial_size"] is not None:
            logger.info(f"Image shape before cropping: {normalized_image_np.shape}")
            cropped_normalized_image_np = cropping(
                normalized_image_np,
                axial_size=CONFIG["axial_size"],
                central_crop_along_z=CONFIG["central_crop_along_z"],
                central_crop_size=CONFIG["central_crop_size"],
            )
            logger.info(
                f"Image shape after cropping: {cropped_normalized_image_np.shape}"
            )
        if CONFIG["save_2d"]:
            image_np = save_2d(cropped_normalized_image_np, preprocessed_image_path)
        else:
            image_np = save_np(cropped_normalized_image_np, preprocessed_image_path)

        total_processed_images_count += 1

        if CONFIG["remove_nii"]:
            remove_nii_files(preprocessed_image_path)

        logger.info(
            f"Processing done for image {image_id}"
        )
        logger.info(
            f"Elapsed time: {datetime.timedelta(seconds=time.time() - start)}"
        )
        logger.info("-" * 40)
        logger.info(
            f"Progress (/total image count): ({total_processed_images_count}/{total_image_count})"
        )

        subject_scans.append(image_np)

    subject_scans = np.array(subject_scans)
    X.append(subject_scans)

    if all([not image for image in np.array(X).flatten()]):
        X = None

    logger.info(
        f"Total processing time: {datetime.timedelta(seconds=time.time() - total_start)}"
    )

    return X


CONFIG = get_config()
logger = logging.getLogger("processing.preprocessing")
if __name__ == "__main__":
    X = run_preprocessing()
