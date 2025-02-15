## Overview
![home page](assets/home.png)

This is a containerized web app and inference pipeline for preprocessing and postprocessing Alzheimer's MRI data to deploy the models we trained *(via transfer learning)* as part of our Master's thesis titled "Alzheimer's disease detection using deep learning techniques". It has three main components (or containers):

### Processing
The same preprocessing logic used on the training data *(sampled from [ADNI](https://ida.loni.usc.edu/))* as well as the necessary postprocessing are applied on the inputs and outputs respectively. consult [this repo](https://github.com/nacer-benyoub/adni_preprocessing/tree/refactor/update-fslinstaller) for more details.

### Serving
By using the Tensorflow Serving docker image to serve the model and output predictions from the preprocessed data

### Webapp
The webapp container collects user inputs and sends them to the processing container which pre- and postprocesses the inputs and sends the outputs back to the webapp container to display a results page as a heatmap broken down by `subject_id` and `image_id`.
#### Upload
![upload page](assets/upload.png)
#### Upload in progress
![upload in progress](assets/upload_progress.png)
#### Results
![results page](assets/results.png)

## Usage
1. Clone this repo
2. Make sure Docker is installed and run `docker compose up`
3. Visit `http://localhost:8080`. If you have no `.nii` or `.dcm` files to upload, some [sample files](sample_data/) are included for testing.