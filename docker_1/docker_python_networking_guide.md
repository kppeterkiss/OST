# Hands-on Lab Guide: Docker Networking & Image Lifecycle with Python Client-Server

This guide provides an end-to-end walkthrough of building, running, debugging, and orchestrating a Python socket client and server architecture located inside the `docker_1` workspace.

---

## Directory Layout
```text
docker_1/
├── python_client/
│   ├── Dockerfile
│   └── python_client.py
└── python_server/
    ├── Dockerfile
    └── python_server.py
```

---

## Step 1: Building Images & Build Context

Navigate to each component folder and build the respective container images:

```bash
cd python_client
docker build -t python_client .
cd ..
cd python_server
docker build -t python_server .
```

### What happens under the hood?
* `docker build`: Reads the local `Dockerfile` and executes instructions step-by-step to build layered images.
* `-t python_client`: Tags (names) the generated image. Omitting an explicit version tag defaults to `:latest`.
* `.` (the dot): Denotes the **Build Context**. All files in this directory are bundled and sent to the Docker daemon. Paths inside the `Dockerfile` (e.g., `COPY . .`) resolve relative to this context.

---

## Step 2: Running the Server Bound to Host Ports

Start the Python socket server in the background:

```bash
docker run -d --name python_server --rm -p 9999:9999 python_server
```

### Flag Breakdown:
* `-d` (Detached mode): Runs the container as a background daemon process, freeing the terminal.
* `--name python_server`: Assigns a fixed, memorable name instead of a random UUID string.
* `--rm`: Automatically purges the container filesystem and metadata upon shutdown.
* `-p 9999:9999` (Host:Container Port Mapping):
  * Left `9999`: Port opened on the physical host machine.
  * Right `9999`: Port bound inside the container's isolated network stack.
  * **Critical Architecture Requirement**: The server application (`python_server.py`) must bind to `0.0.0.0`, **not** `localhost` / `127.0.0.1`. Binding to `localhost` restricts traffic to the container internal loopback only.

---

## Step 3: Verification from the Host (Cross-Platform)

Send test bytes to verify that the server receives data and responds:

### Linux / macOS / Git Bash:
```bash
echo "hello" | nc localhost 9999
```

### Windows (Native PowerShell):
```powershell
$client = New-Object System.Net.Sockets.TcpClient("localhost", 9999); $stream = $client.GetStream(); $writer = New-Object System.IO.StreamWriter($stream); $reader = New-Object System.IO.StreamReader($stream); $writer.WriteLine("hello"); $writer.Flush(); $reader.ReadLine(); $client.Close()
```

**Expected Output:**
```text
Python Server is up and running.
```

---

## Step 4: Client Lifecycle: `attach` vs. `exec`

Start the client container on the default network:

```bash
docker run -d --name python_client --rm python_client
```

### Inspecting Interaction Commands:

#### 1. `docker attach python_client`
* **Mechanism:** Hooks standard input/output directly to the container's initial PID 1 process.
* **Pitfall:** If the process is not interactive, no prompt appears. Pressing `Ctrl + C` sends a terminate signal that immediately kills PID 1 and halts the container.

#### 2. `docker exec -it python_client sh`
* `-i` (Interactive): Keeps `STDIN` open to accept keyboard input.
* `-t` (TTY): Allocates a pseudo-terminal providing a standard prompt and color support.
* `sh`: Spawns a **completely new, independent shell process** inside the running container.
* **Benefit:** Typing `exit` closes only the shell; background container processes remain unaffected.

---

## Step 5: Network Failure on the Default Bridge

Inside the `python_client` shell, invoke the client application:

```bash
# python python_client.py
```

**Observed Error:**
```text
Traceback (most recent call last):
  File "/home/python_client/python_client.py", line 18, in <module>
    sock.connect((HOST, PORT))
    ~~~~~~~~~~~~^^^^^^^^^^^^^^
socket.gaierror: [Errno -2] Name or service not known
```

### Architectural Cause:
* Both containers were placed onto Docker's pre-configured **default `bridge` network**.
* **Engine Constraint:** The default bridge does **not** provide automatic DNS resolution between container names.
* The operating system's resolver cannot translate `python_server` into an IP address.

Exit and delete the container:
```bash
# exit
docker rm -f python_client
```

---

## Step 6: The Host Loopback Workaround (`host.docker.internal`)

Update the client script to target the host machine gateway:

```python
HOST, PORT = "host.docker.internal", 9999
```

Rebuild and execute:

```bash
docker build -t python_client .
docker run -d --name python_client --rm python_client
docker exec -it python_client sh
# python python_client.py
```

**Output:**
```text
b'Python Server is up and running.\n'
```

### What happened?
1. `host.docker.internal` is a specialized Docker DNS entry pointing back to the host machine.
2. The packet leaves the client container, traverses the host network stack, and hits host port `9999`.
3. The port mapping (`-p 9999:9999`) routes the packet back into the server container.
4. **Why avoid this in production?** Adds network overhead, exposes internal services to external host ports, and fails in multi-host production topologies.

Clean up:
```bash
# exit
docker stop python_client python_server
```

---

## Step 7: The Production Pattern: User-Defined Bridge Networks

User-defined bridge networks automatically activate Docker's internal embedded DNS server.

### 1. Provision an isolated bridge network:
```bash
docker network create python_network
```

### 2. Start the server attached to the network:
```bash
docker run -d --name python_server --network python_network --rm -p 9999:9999 python_server
```

### 3. Update `python_client.py` to use declarative service discovery:
```python
HOST, PORT = "python_server", 9999
```

### 4. Rebuild and launch the client inside the same network:
```bash
docker build -t python_client .
docker run -d --name python_client --network python_network --rm python_client
docker exec -it python_client sh
# python python_client.py
```

**Output:**
```text
b'Python Server is up and running.\n'
```

### Why this is the correct approach:
* Containers communicate directly over an internal virtual bridge.
* Host port publishing (`-p 9999:9999`) is no longer required for container-to-container communication.
* Discovery is dynamic: if the server container restarts with a different IP, Docker DNS updates automatically.

Clean up:
```bash
# exit
docker rm -f python_client python_server
docker network rm python_network
```

---

## Step 8: Multi-Container Automation with Docker Compose

Docker Compose codifies building, networking, and service discovery into a single declaration.

### Launch the entire stack:
```bash
docker-compose up -d
```
1. Compose automatically creates an isolated project network: `<project_dir>_default` (e.g., `docker_1_default`).
2. It builds missing images and deploys containers using standard naming conventions:  
   `<project_dir>-<service_name>-<index>` (e.g., `docker_1-python_client-1`).

### Execute on the running client container:
```bash
docker exec -it docker_1-python_client-1 sh
# python python_client.py
```

### Tear down the stack:
```bash
docker-compose down
```
This safely stops and removes all containers, anonymous volumes, and the generated virtual network.
