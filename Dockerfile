ARG CONFIGURED_PYTHON_VERSION=3.12
FROM python:${CONFIGURED_PYTHON_VERSION}-rc-alpine as base

RUN apk add build-base libffi-dev

WORKDIR /code
COPY requirements.txt .

RUN pip3 install --no-cache-dir --user -r requirements.txt

FROM python:${CONFIGURED_PYTHON_VERSION}-rc-alpine as final

COPY --from=base /root/.local/bin /root/.local/bin
COPY --from=base /root/.local/lib/python${CONFIGURED_PYTHON_VERSION}/site-packages /root/.local/lib/python${CONFIGURED_PYTHON_VERSION}/site-packages

WORKDIR /code
COPY . .

CMD ["python3", "bot.py"]
