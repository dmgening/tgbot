FROM python:3.6-alpine
RUN pip install --upgrade setuptools

COPY . /app
WORKDIR /app

RUN pip install -e .

CMD tgbot.cli --help
