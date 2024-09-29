FROM python:3.12-slim
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
WORKDIR /fastapi_project
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .