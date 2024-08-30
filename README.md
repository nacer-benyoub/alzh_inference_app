
This is a containerized inference pipeline for preprocessing and postprocessing Alzheimer's MRI data to deploy the models we trained *(via transfer learning)* as part of our Master's thesis titled "Alxheimer's disease detection using deep learning techniques". It has two main steps:
### Preprocessing
in which the same preprocessing logic used on the training data *(sampled from [ADNI](https://ida.loni.usc.edu/))* is applied on the inputs. This step is detailed in [this repo](https://github.com/nacer-benyoub/adni_preprocessing/tree/refactor/update-fslinstaller)
### Inference
By using the Tensorflow Serving docker image to serve the model and output predictions from the preprocessed data

## Notes/TODO
- Both [preprocessing.py](preprocessing.py) and [inference.ipynb](inference.ipynb) still expect the `raw_data` directory to have the ADNI data directory structure:
```
raw_data/<subject_id>/<preprocessing>/<date>/<acquisition_id>/<file_name>.nii
```
Change the scripts to work without the need for the directory structure above.
- Use logging instead of print statements (processing.py and inference.py).
- Time the inference script and the total processing (preprocessing + inference) job
- Show a progress bar during the processing job to improve the user experience.
- Change how pred values colors contrast with background color (research if css has conditional blocks to use instead of computing 1 - var(--alpha))
- Add caching to enhance processing performance and reduce the necessary time.

## Commands
### Inspecting the SavedModel

- Inspect the model (all details)
```bash
saved_model_cli show --dir saved_models/$MODEL_NAME/$MODEL_VERSION/ --all
```

- Inspect the model (specific tag_set and signature_def)
```bash
saved_model_cli show --dir saved_models/$MODEL_NAME/$MODEL_VERSION/ --tag_set serve --signature_def serving_edfault
```

- Run the model on a preprocessed scan
```bash
saved_model_cli run --dir saved_models/$MODEL_NAME/$MODEL_VERSION/ \
    --tag_set serve \
    --signature_def serving_default \
    --inputs image="data/preprocessed_data/002_S_0413/MPR__GradWarp__B1_Correction__N3__Scaled/2008-07-31_14_39_56.0/I120917/ADNI_002_S_0413_MR_MPR__GradWarp__B1_Correction__N3__Scaled_Br_20081015122825655_S54591_I120917.npz"[image]
```
### Running the whole preprocessing + inference pipeline using docker compose

- Starting the containers
```bash
docker compose up
```

- Starting the containers while ensuring the `alzh-processing` image is rebuilt first
```bash
docker compose up --build
```
### Preprocessing
- Modify [get_config.py](get_config.py) as per your preferences. Refer [the preprocessing repo](https://github.com/nacer-benyoub/adni_preprocessing/tree/refactor/update-fslinstaller)
- Build the preprocessing image
```bash
docker build -t alzh-processing:0.1.0 .
```
- Run preprocessing container
```bash
docker run -it --rm -v ./data:/app/data alzh-processing:0.1.0 /app/run.sh
```
### Serving
- Set MODEL_NAME and MODEL_VERSION if running the container via `docker run`
```bash
export MODEL_NAME=vgg19__down_sampled
export MODEL_VERSION=2
```
or set in `.env` file if running using docker compose
- Run serving image
```bash
docker run -t --rm -p 8501:8501 -v "./saved_models/$MODEL_NAME":"/models/$MODEL_NAME" -e MODEL_NAME=$MODEL_NAME tensorflow/serving
```