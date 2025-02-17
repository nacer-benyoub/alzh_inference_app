## Notes/TODO
- ⌛ Both [preprocessing.py](preprocessing.py) and [inference.py](inference.ipynb) still expect the `raw_data` directory to have the ADNI data directory structure:
```
raw_data/<subject_id>/<preprocessing>/<date>/<acquisition_id>/<file_name>.nii
```
Change the scripts to work without the need for the directory structure above.
- ✅ Use logging instead of print statements (processing.py and inference.py).
- ⌛ Time the inference script and the total processing (preprocessing + inference) job
- ✅ Show a progress bar during the processing job to improve the user experience.
    - ⌛ Use Celery for a more informative progress bar.
- Change how pred values colors contrast with background color (research if css has conditional blocks to use instead of computing 1 - var(--alpha))
- ⌛ Add caching to enhance processing performance and reduce the necessary time (e.g. Flask Caching extension).
- ✅ Optimize the preprocessing image build to reduce its size.
- ✅ Fix the atrocity of passing the inference data as an endpoint's query parameter
- ✅ Preprocessing and inference steps run on all the existing scans in the data directory regardless of the specified subject_id and image_id (must be fixed but could be used in a future batch mode feature)

## Commands
### Inspecting the SavedModel

- Inspect the model (all details)
```bash
saved_model_cli show --dir saved_models/$MODEL_NAME/$MODEL_VERSION/ --all
```

- Inspect the model (specific tag_set and signature_def)
```bash
saved_model_cli show --dir saved_models/$MODEL_NAME/$MODEL_VERSION/ --tag_set serve --signature_def serving_default
```

- Run the model on a preprocessed scan
```bash
saved_model_cli run --dir saved_models/$MODEL_NAME/$MODEL_VERSION/ \
    --tag_set serve \
    --signature_def serving_default \
    --inputs image="data/preprocessed_data/002_S_0413/MPR__GradWarp__B1_Correction__N3__Scaled/2008-07-31_14_39_56.0/I120917/ADNI_002_S_0413_MR_MPR__GradWarp__B1_Correction__N3__Scaled_Br_20081015122825655_S54591_I120917.npz"[image]
```
### Running the app using docker compose

- Starting the containers
```bash
docker compose up
```

- Starting the containers while ensuring the images are rebuilt first
```bash
docker compose up --build
```
### Preprocessing
- Modify [get_config.py](get_config.py) as per your preferences. Refer [the preprocessing repo](https://github.com/nacer-benyoub/adni_preprocessing/tree/refactor/update-fslinstaller)
- Build the preprocessing image
```bash
docker build -t alzh-processing .
```
- Run the preprocessing image
```bash
docker run -it --rm \
-v ./data:/app/data \
-v ./logs:/app/logs \
-p 5000:5000 \
--env-file .env \
alzh-processing /app/entrypoint.sh
```
### Serving
- If running the container via `docker run`, `MODEL_NAME` and `MODEL_VERSION` must be set both in the container as well as the host environment. For container environment, `.env` file is passed in the `--env-file` option. For setting in the host env, run:
```bash
export MODEL_NAME=vgg19__down_sampled
export MODEL_VERSION=2
```
And then run:
```bash
docker run -it --rm \
--env-file .env \
-v "./saved_models/$MODEL_NAME":"/models/$MODEL_NAME" \
-p 8501:8501 \
tensorflow/serving
```
- Or simply run:
```bash
docker compose up serving
```