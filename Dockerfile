FROM python:3.12

ENV PYTHONUNBUFFERED=TRUE

RUN apt-get update && apt-get install -y \
    gcc \
    libpq-dev \
    && apt-get clean && rm -rf /var/lib/apt/lists/*

WORKDIR /backend_plants

COPY . /backend_plants

RUN pip3 install --upgrade pip &&  pip3 install -r ./req.txt --no-cache-dir

EXPOSE ${PORT}