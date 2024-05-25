FROM --platform=linux/amd64 condaforge/miniforge3:latest

ENV FSL_CONDA_CHANNEL="https://fsl.fmrib.ox.ac.uk/fsldownloads/fslconda/public"

# Optional: Update and install any dependencies or packages you need
RUN apt-get update

RUN conda install -y -c ${FSL_CONDA_CHANNEL} -c conda-forge \
bc \
fsl-bet2 \
fsl-avwutils \
fsl-data_standard \
fsl-flirt

ENV FSLDIR="/opt/conda"
ENV PATH="${FSLDIR}/bin:${PATH}"
ENV FSLOUTPUTTYPE="NIFTI_GZ"

# set the working directory in the container
WORKDIR /app

# Specify any command to run when the container starts
COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

COPY . .

RUN pip install -r requirements.txt

# run the entrypoint script
ENTRYPOINT ["/entrypoint.sh"]