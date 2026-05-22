# Backend Dockerfile (Lambda image)
FROM public.ecr.aws/lambda/python:3.11

WORKDIR ${LAMBDA_TASK_ROOT}

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt mangum

COPY . ./

# Pre-create data dir; data baked into image for demo
RUN mkdir -p /var/task/data/raw/data
ENV DATA_DIR=/var/task/data/raw/data

CMD ["lambda_handler.handler"]
