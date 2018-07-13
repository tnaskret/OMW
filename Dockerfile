FROM python:3.7-slim
MAINTAINER Tomasz Naskręt <tomasz.naskret@pwr.edu.pl>

WORKDIR /app

COPY requirements.txt requirements.txt
RUN pip install -r requirements.txt

COPY . .

RUN pip install --editable .

CMD gunicorn -b 0.0.0.0:5000 --access-logfile - "omw.app:create_app()"