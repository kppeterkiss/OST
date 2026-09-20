```bash
cd python_client
```

```bash
docker build -t python_client .
```


```bash
cd ..
```
```bash
cd python_server
```
```bash
docker build -t python_server .
```

```bash
docker run -d --name python_server --rm -p 9999:9999 python_server
```

```bash
echo "hello" | nc localhost 9999
```
Expected: ```Python Server is up and running.```


```bash 
docker run -d --name python_client --rm python_client
```

```bash 
docker attach python_client
```

```bash 
docker exec -it python_client sh
``` 

```bash
# python python_client.py

```

expected: 
```
Traceback (most recent call last):
  File "/home/python_client/python_client.py", line 18, in <module>
    sock.connect((HOST, PORT))
    ~~~~~~~~~~~~^^^^^^^^^^^^^^
socket.gaierror: [Errno -2] Name or service not known
```

```bash
# exit
```

```bash
docker rm -f python_client
```

use in python_client.py: 
```python
HOST, PORT = "host.docker.internal", 9999
```

```bash
docker build -t python_client .
```
```bash
docker run -d --name python_client --rm python_client
```

```bash
# python python_client.py
```
expected: ```b'Python Server is up and running.\n'```
```bash
# exit
```
```bash
docker stop python_client python_server
```


```bash
docker run -d --name python_server --network python_network --rm -p 9999:9999 python_server
```
use in python_client.py: 
```python
HOST, PORT = "python_server", 9999
```

rebuild image:
```bash
docker build -t python_client .
```

and start:
```bash
docker run -d --name python_client --network python_network --rm python_client

```
exec on python_client ```sh```:

```bash
docker exec -it python_client sh
```

```bash
# python python_client.py
```

expected:
```bash
b'Python Server is up and running.\n'
# 
```

cleanup: 
```bash
docker rm -f python_client python_server```
```bash
docker network rm python_network
```

Put services and network together:
```bash
docker-compose up 
```
```bash
docker_1 % docker exec -it docker_1-python_client-1 sh
```
...

```bash
docker-compose down 
```

