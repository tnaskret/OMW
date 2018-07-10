FROM python:3.7-slim
MAINTAINER Tomasz Naskręt <tomasz.naskret@pwr.edu.pl>

ENV INSTALL_PATH /app
RUN mkdir -p $INSTALL_PATH

WORKDIR $INSTALL_PATH

COPY requirements.txt requirements.txt
RUN pip install -r requirements.txt
COPY . .

RUN python install_nltk_wordnet.py

WORKDIR $INSTALL_PATH/omw/bin
RUN sh doall.bash

RUN python make-admin-db.py
RUN python load-admin-users.py  admin.db

#RUN mv omw.db ../db
#RUN mv admin.db ../db

#RUN chmod -R go+w ../db

#WORKDIR $INSTALL_PATH

#RUN python omw/bin/load-pwn-freq.py omw/db/omw.db
#RUN python omw/bin/update-freq.py omw/db/omw.db
#RUN python omw/bin/update-label.py omw/db/omw.db

WORKDIR $INSTALL_PATH/omw

CMD python __init__.py