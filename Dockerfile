FROM python:3.8-alpine

RUN adduser -D myclass

WORKDIR /home/myclass

COPY requirements.txt requirements.txt
RUN python -m venv myenv
RUN myenv/bin/pip install -r requirements.txt
RUN myenv/bin/pip install gunicorn pymysql

COPY app app
COPY migrations migrations
COPY myclass.py config.py boot.sh ./
RUN chmod a+x boot.sh

ENV FLASK_APP myclass.py

RUN chown -R myclass:myclass ./
USER myclass

EXPOSE 5000
ENTRYPOINT ["./boot.sh"]
