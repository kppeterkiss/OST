# Container Orchestration Hands-on Lab Guide
## From Docker Compose to Docker Swarm & Kubernetes (60 Mins)

This hands-on workshop walks through managing multi-container topologies, understanding data persistence paradigms (Volumes vs. Bind Mounts), scaling with Docker Swarm, and deploying on Kubernetes.

---

## Lab Architecture & Files Overview

Ensure you have a working directory with the following three descriptor files:

### 1. `docker-compose.yml` (Named Volume)
```yaml
services:
  web:
    image: python:3.9-slim
    command: python -m http.server 8080
    ports:
      - "8080:8080"
    networks:
      - app-net

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data
    networks:
      - app-net

volumes:
  redis_data:

networks:
  app-net:
```

### 2. `docker-compose-bind.yml` (Host Bind Mount)
```yaml
services:
  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    volumes:
      - ./local_redis_state:/data
    networks:
      - app-net

networks:
  app-net:
```

### 3. `redis-k8s.yaml` (Kubernetes PVC & Deployment)
```yaml
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: redis-pvc
spec:
  accessModes:
    - ReadWriteOnce
  resources:
    requests:
      storage: 1Gi
---
apiVersion: apps/v1
kind: Deployment
metadata:
  name: redis-deployment
spec:
  replicas: 1
  selector:
    matchLabels:
      app: redis
  template:
    metadata:
      labels:
        app: redis
    spec:
      containers:
      - name: redis
        image: redis:7-alpine
        ports:
        - containerPort: 6379
        volumeMounts:
        - name: redis-storage
          mountPath: /data
      volumes:
      - name: redis-storage
        persistentVolumeClaim:
          claimName: redis-pvc
```

---

## Exercise 1: Docker Compose with Managed Volumes

### Step 1.1: Launch Stack
Start the services in detached background mode:
```bash
docker compose up -d
```

### Step 1.2: Verify Running State
```bash
docker compose ps
```
*Expected Check:* Both `web` and `redis` report state `Up` or `running`.

### Step 1.3: Write Persistent Data
Write a key-value record to Redis using the declared service name:
```bash
docker compose exec redis redis-cli SET student_count 150
```
*Expected Check:* Terminal returns `OK`.

### Step 1.4: Complete Stack Teardown
Tear down the containers and network:
```bash
docker compose down
```
*Verification Check:* Run `docker container ps` to confirm containers are stopped and deleted. The volume `docker-2_redis_data` remains preserved on disk.

### Step 1.5: Recreate and Verify Persistence
```bash
docker compose up -d
docker compose exec redis redis-cli GET student_count
```
*Expected Check:* Returns `"150"`. Data survived full container lifecycle deletion.

Clean up before next exercise:
```bash
docker compose down
```

---

## Exercise 2: Docker Compose with Bind Mounts & Custom Filenames

### Step 2.1: Launch with Explicit File Flag
Because the filename is non-standard (`docker-compose-bind.yml`), pass `-f`:
```bash
docker compose -f docker-compose-bind.yml up -d
```

### Step 2.2: Verify Running Containers
Check using native engine tools:
```bash
docker container ps
```
Notice the generated naming format: `<directory>_redis_1` (e.g., `docker-2-redis-1`).

### Step 2.3: Write Data via Fallback Container Name
Execute the write command using the container name directly:
```bash
docker exec -it <directory>-redis-1 redis-cli SET student_count 200
```


```bash
(docker exec -it docker_2-redis-1 redis-cli SET student_count 200)
```
*Expected Check:* Returns `OK`.

### Step 2.4: Inspect Host Filesystem
Examine the local directory on the host machine:
* Linux / macOS: `ls -la ./local_redis_state/`
* Windows (PowerShell): `Get-ChildItem ./local_redis_state/`
*Expected Check:* `dump.rdb` or Redis persistence logs exist directly on the host filesystem.

### Step 2.5: Teardown with File Flag
```bash
docker compose -f docker-compose-bind.yml down
```


### Step 2.6: Teardown with File Flag
* bring up again
```bash
docker compose -f docker-compose-bind.yml up -d
```
* check value
```bash
docker exec -it docker_2-redis-1 redis-cli GET student_count
```

---

## Exercise 3: Scaling Out with Docker Swarm

### Step 3.1: Initialize Single-Node Swarm
Bind explicitly to loopback to prevent multi-adapter IP ambiguity:
```bash
docker swarm init --advertise-addr 127.0.0.1
```
*Verification Check:* Run `docker node ls` to ensure your node is listed as `Leader` with status `Ready`.

### Step 3.2: Deploy Stack
Deploy using the named-volume Compose configuration:
```bash
docker stack deploy -c docker-compose.yml mystack
```

### Step 3.3: Inspect Swarm Workloads
List the stack services and their assigned nodes:
```bash
docker stack services mystack
docker stack ps mystack
```
*Expected Check:* Both `mystack_web` and `mystack_redis` show `1/1` replicas running on an overlay network.

### Step 3.4: Dynamic Scaling
Scale the web tier to 5 replicas:
```bash
docker service scale mystack_web=5
```
*Verification Check:* Run `docker service ls` to observe `5/5` replicas active under `mystack_web`.

### Step 3.5: Clean Up Swarm Stack
```bash
docker stack rm mystack
```
Leave Swarm mode (optional):
```bash
docker swarm leave --force
```

---

## Exercise 4: Enterprise Orchestration on Kubernetes (Docker Desktop)

### Step 4.1: Cluster Sanity Check
Ensure Kubernetes is checked under *Docker Desktop Settings -> Kubernetes*:
```bash
kubectl get nodes
```
*Expected Check:* Output lists `docker-desktop` with status `Ready` and role `control-plane`.

### Step 4.2: Apply Kubernetes Manifests
Deploy the PersistentVolumeClaim and Deployment:
```bash
kubectl apply -f redis-k8s.yaml
```

### Step 4.3: Verify Deployment and Storage Binding
```bash
kubectl get pvc
kubectl get pods
```
*Expected Check:*
* `redis-pvc` status is `Bound`.
* The `redis-deployment-xxxxx-xxxxx` Pod status is `Running` (1/1 Ready).

### Step 4.4: Write Data to Kubernetes Pod
Access the running pod through the deployment selector:
```bash
kubectl exec -it deployment/redis-deployment -- redis-cli SET counter 999
```
*Expected Check:* Returns `OK`.

### Step 4.5: Test Granular Self-Healing & Persistence
Delete the running Pod directly:
```bash
kubectl delete pod -l app=redis
```
Immediately inspect the pod status:
```bash
kubectl get pods
```
*Observation:* The deleted Pod terminated, and Kubernetes spawned a new replacement Pod in seconds.

Verify that the PVC successfully reattached and retained the data:
```bash
kubectl exec -it deployment/redis-deployment -- redis-cli GET counter
```
*Expected Check:* Returns `"999"`. Data survived Pod destruction.

### Step 4.6: Teardown Lab Resources
Clean up Kubernetes manifests:
```bash
kubectl delete -f redis-k8s.yaml
```
*Verification Check:* Run `kubectl get pods,pvc` to confirm all resources are deleted.

---

## Quick Reference Command Summary

| Component | Goal | Command |
| :--- | :--- | :--- |
| **Compose** | Verify stack state | `docker compose -f <file> ps` |
| **Compose** | Inspect container logs | `docker compose -f <file> logs -f <service>` |
| **Compose** | Execute in container | `docker compose -f <file> exec <service> <cmd>` |
| **Swarm** | List active stacks | `docker stack ls` |
| **Swarm** | View service tasks / nodes | `docker stack ps <stack>` |
| **Swarm** | View aggregated service logs | `docker service logs -f <service>` |
| **Kubernetes** | View Pods and node assignment | `kubectl get pods -o wide` |
| **Kubernetes** | Check storage volume bindings | `kubectl get pvc,pv` |
| **Kubernetes** | Pod lifecycle diagnostics | `kubectl describe pod <pod_name>` |
| **Kubernetes** | Stream Pod logs | `kubectl logs -f deployment/<deployment_name>` |
