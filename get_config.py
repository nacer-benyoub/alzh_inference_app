import os
from pathlib import Path

def get_config_dict():
    config = {}
    
    config["raw_data_path"] = Path(r'data/raw_data')
    config["preprocessed_data_path"] = Path(r'data/preprocessed_data')
    config['pred_path'] = Path(r'data/predictions')
    config["re_process"] = False
    config['clean_data_dir'] = False
    
    resolution_mm = 1
    config["reference_atlas_location"] = Path(f'{os.environ["FSLDIR"]}/data/standard/MNI152_T1_{resolution_mm}mm_brain.nii.gz')
    config["axial_size"] = 180
    config["central_crop_along_z"] = True
    config["central_crop_size"] = 30 # size of final image along z axis (number of slices to save)
    config["save_2d"] = False
    config["remove_nii"] = False
    config["subject_limit"] = -1 # limit number of subjects to preprocess (-1 to disable)
    
    model_name = os.environ["MODEL_NAME"]
    model_version = os.environ['MODEL_VERSION']
    config['serving_url'] = f'http://serving:8501/v1/models/{model_name}/versions/{model_version}:predict'
    return config
    