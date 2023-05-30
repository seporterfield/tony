FROM python:3.10.6-slim-buster

WORKDIR /app

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY ./src ./src
COPY app.py example_persona.yaml ./
CMD ["python", "./app.py", "--persona", "example_persona.yaml"]