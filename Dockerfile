FROM --platform=linux/amd64 condaforge/miniforge3:24.3.0-0

ENV FSL_CONDA_CHANNEL="https://fsl.fmrib.ox.ac.uk/fsldownloads/fslconda/public"

# Optional: Update and install any dependencies or packages you need
RUN apt-get update

RUN conda install -y -c ${FSL_CONDA_CHANNEL} \
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

# Copy requirements.txt separately and install dependencies so it can be cached
COPY requirements.txt requirements.txt
RUN pip install -r requirements.txt

# Copy the files
COPY . .

# Make entrypoint.sh executable
RUN chmod +x entrypoint.sh

# run the entrypoint script
ENTRYPOINT ["./entrypoint.sh"]