FROM python:3

RUN apt-get update && apt-get upgrade -y
RUN apt-get install -y sudo

WORKDIR /usr/src/app

COPY requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Secure against running as root, but allow sudo (for tcpdump)
RUN adduser --disabled-password --gecos '' python_server
RUN adduser python_server sudo
RUN echo '%sudo ALL=(ALL) NOPASSWD:ALL' >> /etc/sudoers
WORKDIR /home/python_server

COPY python_server.py /python_server.py

EXPOSE 9999

CMD [ "python", "/python_server.py" ]
