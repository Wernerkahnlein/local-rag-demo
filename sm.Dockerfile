FROM python:3.9.21-alpine3.21

WORKDIR /app

COPY ./main.py /app/

COPY ./requirements.txt /app/

RUN adduser --system  nonroot

USER nonroot

RUN pip install -r requirements.txt

ENTRYPOINT [ "python", "/app/main.py"]
