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

---

# Guía de Instalación para ARKHAN-Community

## Requisitos del Sistema

### Requisitos Mínimos:
- SO: Linux x86‑64
- RAM: 2 GB
- CPU: Procesador de doble núcleo
- Disco: 20 GB de espacio libre
- Red: Conexión a internet

### Requisitos Recomendados:
- SO: Linux x86‑64
- RAM: 4 GB o más
- CPU: Procesador de cuatro núcleos o superior
- Disco: SSD con 50 GB de espacio libre
- Red: Conexión a internet rápida y estable

## Instalación Paso a Paso
1. **Clonar el Repositorio**  
   Ejecuta el siguiente comando para clonar el repositorio:
   ```bash
   git clone https://github.com/jorel666/ARKHAN-Community.git
   ```

2. **Navegar al Directorio**  
   Cambia al directorio del proyecto:
   ```bash
   cd ARKHAN-Community
   ```

3. **Instalar Docker**  
   Sigue las instrucciones según tu sistema operativo para instalar Docker:
   - [Instalación de Docker](https://docs.docker.com/get-docker/)

4. **Construir la Imagen Docker**  
   Ejecuta el siguiente comando para construir la imagen Docker:
   ```bash
   docker build -t arkhan-community .
   ```

5. **Ejecutar la Aplicación**  
   Usa el comando a continuación para ejecutar el contenedor Docker:
   ```bash
   docker run -p 8080:8080 arkhan-community
   ```

6. **Acceder a la Aplicación**  
   Abre tu navegador web y navega a `http://localhost:8080`

## Instalación con Docker usando Dockerfile

Asegúrate de tener un `Dockerfile` definido en la raíz de tu repositorio. Aquí tienes un ejemplo de Dockerfile:
```dockerfile
FROM node:14

WORKDIR /app

COPY . .

RUN npm install

EXPOSE 8080

CMD ["npm", "start"]
```

## Helm Chart para Kubernetes

Para el despliegue en Kubernetes, crea un Helm chart:
1. Crea un nuevo Helm chart:
   ```bash
   helm create arkhan-community
   ```
2. Personaliza las plantillas en la carpeta `templates` para adaptarlas a las necesidades de tu aplicación.
3. Despliega el chart:
   ```bash
   helm install arkhan-community ./arkhan-community
   ```

## Solución de Problemas Comunes
1. **Error: Puerto ya en uso**  
   Asegúrate de que ninguna otra aplicación esté usando el mismo puerto. Intenta cambiar el número de puerto.

2. **Error: Imagen no encontrada**  
   Verifica que la imagen Docker se haya construido correctamente ejecutando `docker images`.

3. **Error: Permisos insuficientes**  
   Asegúrate de ejecutar los comandos Docker con los permisos necesarios o como root.

4. **Error: La aplicación falla**  
   Revisa los logs usando `docker logs <id_del_contenedor>` para depurar.

5. **Error: Conexión rechazada**  
   Asegúrate de que la aplicación esté en ejecución y de que se esté accediendo al puerto correcto.

## Monitoreo de Logs y Métricas
- Los logs de Docker pueden consultarse usando:
  ```bash
  docker logs <id_del_contenedor>
  ```
- Para Kubernetes, puedes ver los logs usando:
  ```bash
  kubectl logs <nombre_del_pod>
  ```

## Actualización de la Aplicación
1. Obtén los últimos cambios del repositorio:
   ```bash
   git pull
   ```
2. Reconstruye la imagen Docker:
   ```bash
   docker build -t arkhan-community .
   ```
3. Reinicia el contenedor:
   ```bash
   docker restart <id_del_contenedor>
   ```

## Desinstalación de la Aplicación
1. Detén el contenedor Docker en ejecución:
   ```bash
   docker stop <id_del_contenedor>
   ```
2. Elimina el contenedor Docker:
   ```bash
   docker rm <id_del_contenedor>
   ```
3. Opcionalmente, elimina la imagen Docker:
   ```bash
   docker rmi arkhan-community
   ```
