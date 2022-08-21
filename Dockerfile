FROM ubuntu:latest

ENV LANG=zh_CN.UTF-8 \
    LANGUAGE=zh_CN.UTF-8 \
    LC_CTYPE=zh_CN.UTF-8 \
    LC_ALL=zh_CN.UTF-8 \
    TZ=Asia/Shanghai

WORKDIR /my_bot

ADD . .
RUN apt update &&\
    apt upgrade -y &&\
    apt install -y language-pack-zh-hans gcc python3.10 python3-dev python3-pip libcurl4-openssl-dev &&\
    ln -sf /bin/python3 /bin/python &&\
    python3 -m pip install -r requirements.txt &&\
    cp /my_bot/msyh.ttc /usr/share/fonts/ &&\
    python3 -m playwright install &&\
    apt-get install -y libnss3-dev libxss1 libasound2 libxrandr2 libatk1.0-0 libgtk-3-0 libgbm-dev libxshmfence1 &&\
    rm -rf /var/lib/apt/lists/*
CMD python3 bot.py