FROM python:3.12-rc-alpine as base

RUN apk add build-base libffi-dev

COPY . /code
WORKDIR /code

RUN pip3 install --user -r requirements.txt

FROM python:3.12-rc-alpine as final

COPY --from=base /root/.local/bin /root/.local/bin
COPY --from=base /root/.local/lib/python3.12/site-packages /root/.local/lib/python3.12/site-packages

WORKDIR /code
COPY --from=base /code .
