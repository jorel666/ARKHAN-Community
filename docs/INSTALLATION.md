# Installation Guide for ARKHAN-Community

## System Requirements

### Minimum Requirements:
- OS: Linux x86-64
- RAM: 2 GB
- CPU: Dual-core processor
- Disk: 20 GB free space
- Network: Internet connection

### Recommended Requirements:
- OS: Linux x86-64
- RAM: 4 GB or more
- CPU: Quad-core processor or better
- Disk: SSD with 50 GB free space
- Network: Fast and stable internet connection

## Step-by-Step Installation
1. **Clone the Repository**  
   Run the following command to clone the repository:
   ```bash
   git clone https://github.com/jorel666/ARKHAN-Community.git
   ```

2. **Navigate to the Directory**  
   Change to the project directory:
   ```bash
   cd ARKHAN-Community
   ```

3. **Install Docker**  
   Follow the instructions based on your OS to install Docker:
   - [Docker Installation](https://docs.docker.com/get-docker/)

4. **Build the Docker Image**  
   Run the following command to build the Docker image:
   ```bash
   docker build -t arkhan-community .
   ```

5. **Run the Application**  
   Use the command below to run the Docker container:
   ```bash
   docker run -p 8080:8080 arkhan-community
   ```

6. **Access the Application**  
   Open your web browser and navigate to `http://localhost:8080`

## Docker Installation with Dockerfile

Make sure you have a `Dockerfile` defined in the root of your repository. Here’s an example Dockerfile:
```dockerfile
FROM node:14

WORKDIR /app

COPY . .

RUN npm install

EXPOSE 8080

CMD ["npm", "start"]
```

## Kubernetes Helm Chart

For Kubernetes deployment, create a Helm chart:
1. Create a new Helm chart:
   ```bash
   helm create arkhan-community
   ```
2. Customize the templates in the `templates` folder to suit your application needs.
3. Deploy the chart:
   ```bash
   helm install arkhan-community ./arkhan-community
   ```

## Troubleshooting Common Errors
1. **Error: Port already in use**  
   Ensure no other applications are using the same port. Try changing the port number.

2. **Error: Image not found**  
   Verify that the Docker image was built successfully by running `docker images`.

3. **Error: Insufficient permissions**  
   Make sure to run Docker commands with required permissions or as root.

4. **Error: Application crashing**  
   Check logs using `docker logs <container_id>` to debug.

5. **Error: Connection refused**  
   Ensure the application is running and the correct port is being accessed.

## Monitoring Logs and Metrics
- Docker logs can be accessed using:
  ```bash
  docker logs <container_id>
  ```
- For Kubernetes, you can view logs using:
  ```bash
  kubectl logs <pod_name>
  ```

## Updating the Application
1. Pull the latest changes from the repository:
   ```bash
   git pull
   ```
2. Rebuild the Docker image:
   ```bash
   docker build -t arkhan-community .
   ```
3. Restart the container:
   ```bash
   docker restart <container_id>
   ```

## Uninstalling the Application
1. Stop the running Docker container:
   ```bash
   docker stop <container_id>
   ```
2. Remove the Docker container:
   ```bash
   docker rm <container_id>
   ```
3. Optionally, remove the Docker image:
   ```bash
   docker rmi arkhan-community
   ```

All commands assume you are in the ARKHAN-Community directory.