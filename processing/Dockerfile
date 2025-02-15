############################    BUILD stage   ############################
FROM --platform=linux/amd64 condaforge/miniforge3 as build

# Copy requirements.txt separately and install dependencies so it can be cached
RUN --mount=type=bind,source=requirements.txt,target=requirements.txt \
    FSL_CONDA_CHANNEL="https://fsl.fmrib.ox.ac.uk/fsldownloads/fslconda/public" \
    && conda install -y --freeze-installed -c "$FSL_CONDA_CHANNEL" --file requirements.txt \
    # clean unnecessary build files
    && conda clean -afy \
    && find ${CONDA_DIR} -follow -type f -name '*.a' -delete \
    && find ${CONDA_DIR} -follow -type f -name '*.pyc' -delete \
    && find ${CONDA_DIR} -follow -type f -name '*.js.map' -delete \
    # clean the data_standard directory and leave only the needed ref files
    && find ${CONDA_DIR}/data/standard -type f ! -name 'MNI152_*_brain.nii.gz' -delete

# Pack the environment in a single file and unpack it in /venv
RUN conda install -c conda-forge conda-pack
RUN conda-pack --ignore-missing-files -o /tmp/env.tar && mkdir /venv && cd /venv && tar xf /tmp/env.tar &&  rm /tmp/env.tar
RUN /venv/bin/conda-unpack


############################    RUNTIME stage   ############################
FROM bitnami/minideb as runtime

# Copy /venv from the build stage
COPY --from=build /venv /venv

ENV FSLDIR="/venv"
ENV PATH="${FSLDIR}/bin:${PATH}"
ENV FSLOUTPUTTYPE="NIFTI_GZ"
ENV PYTHONDONTWRITEBYTECODE=true

# Set the working directory in the container
WORKDIR /app

# Copy the files
COPY . .

# Make entrypoint.sh executable
RUN chmod +x entrypoint.sh

# run the entrypoint script
ENTRYPOINT ["./entrypoint.sh"]