FROM python:3

RUN apt-get update && apt-get upgrade -y
RUN apt-get install -y sudo
RUN apt-get install -y openssh-server nmap iputils-ping

COPY requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Secure against running as root
RUN useradd -rm -d /home/python_client -s /bin/bash -g root -G sudo -u 1000 python_client 
RUN echo '%sudo ALL=(ALL) NOPASSWD:ALL' >> /etc/sudoers
RUN echo 'python_client:python_client' | chpasswd
RUN /usr/bin/ssh-keygen -A 
RUN service ssh start

EXPOSE 22

WORKDIR /home/python_client
COPY python_client.py ./python_client.py

#CMD [ "python", "python_client.py" ]
CMD ["/usr/sbin/sshd","-D"]
