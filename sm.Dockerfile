FROM python:3.12-slim

RUN pip install --upgrade pip

RUN adduser  nonroot

USER nonroot

WORKDIR /app

COPY --chown=nonroot:nonroot ./main.py /app/

COPY --chown=nonroot:nonroot ./src/ /app/src/

COPY --chown=nonroot:nonroot ./requirements.txt /app/

RUN pip install --user --no-cache-dir -r /app/requirements.txt

ENV PATH="/home/nonroot/.local/bin:${PATH}"

EXPOSE 8082

CMD [ "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8082"]
