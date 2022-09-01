FROM ermaozi/python:latest

ARG DEBIAN_FRONTEND=noninteractive

ENV LANG=zh_CN.UTF-8 \
    LANGUAGE=zh_CN.UTF-8 \
    LC_CTYPE=zh_CN.UTF-8 \
    LC_ALL=zh_CN.UTF-8 \
    TZ=Asia/Shanghai

WORKDIR /my_bot

ADD . .

RUN python3 -m pip install -r requirements.txt &&\
    cp /my_bot/msyh.ttc /usr/share/fonts/ &&\
    python3 -m playwright install chromium

CMD python3 bot.py