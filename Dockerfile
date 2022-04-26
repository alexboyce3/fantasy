FROM python:3

WORKDIR /app

COPY /code /app/code

RUN pip install -r /app/requirements.txt

ENV AM_I_IN_A_DOCKER_CONTAINER Yes

CMD python3 /app/fbl_player_monitor.py
