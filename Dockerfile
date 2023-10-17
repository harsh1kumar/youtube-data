FROM python:3.10

# Get python api key as a build arg
# and define that as an env variable inside docker image
ARG YOUTUBE_API_KEY
ENV YOUTUBE_API_KEY=${YOUTUBE_API_KEY}

# For GCP authentication
ARG SERVICE_ACCOUNT_SECRET_KEY
ENV GOOGLE_APPLICATION_CREDENTIALS=/etc/service-account.json
RUN printf "%s" "${SERVICE_ACCOUNT_SECRET_KEY}" > /etc/service-account.json

# Copy relevant files into docker image
COPY src /youtube_data_project/src/
COPY requirements.txt /youtube_data_project/
WORKDIR /youtube_data_project

## Install packages required for building python dependencies
RUN apt-get update
RUN apt-get install -y make automake cmake gcc g++

# Setup python environment and install dependencies
RUN python -m venv yt-env
RUN . yt-env/bin/activate
RUN pip install -r requirements.txt
RUN pip install torch --index-url https://download.pytorch.org/whl/cpu

# CMD python src/data_pipeline.py
CMD python src/data_pipeline.py

