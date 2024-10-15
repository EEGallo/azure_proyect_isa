"""
Script para gestionar imágenes Docker y contenedores en Azure.

Este script permite a los usuarios:
- Iniciar Docker Desktop si no está en ejecución.
- Iniciar sesión en Azure y crear grupos de recursos.
- Verificar la existencia de un Azure Container Registry (ACR) y crearlo si no existe.
- Construir imágenes Docker a partir de un Dockerfile.
- Escanear imágenes Docker en busca de vulnerabilidades.
- Publicar imágenes en el ACR.
- Crear un contenedor en Azure a partir de la imagen publicada.

Requisitos:
- Docker Desktop debe estar instalado y configurado.
- Azure CLI debe estar instalado.
- Las bibliotecas 'typer' y 'python-dotenv' deben estar instaladas.

Uso:
1. Configura las variables de entorno en un archivo .env:
   - IMAGE_NAME: Nombre de la imagen Docker.
   - CONTAINER_NAME: Nombre del contenedor.
   - IMAGE_TAG: Etiqueta de la imagen (opcional, por defecto es "v1.0.0").
   - RESOURCE_GROUP: Nombre del grupo de recursos en Azure.
   - LOCATION: Ubicación del grupo de recursos (opcional, por defecto es "eastus").
   - ACR_NAME: Nombre del Azure Container Registry.
   - PORT_CONTAINER: Puerto en el que se ejecutará el contenedor (opcional, por defecto es "5000").
   - REGISTER_NAME: Nombre del registro (opcional, si se utiliza).

2. Ejecuta el script desde la línea de comandos.

Funciones:
- start_docker_desktop(): Inicia Docker Desktop si no está en ejecución.
- azure_login(): Inicia sesión en la cuenta de Azure.
- az_run(): Verifica si el grupo de recursos existe y lo crea si no.
- check_az_acr(): Verifica la existencia del ACR y lo crea si no existe.
- build_image(): Construye la imagen Docker si no existe.
- grype_image(): Escanea la imagen Docker en busca de vulnerabilidades.
- push_image(): Publica la imagen Docker en el ACR.
- create_container_acr(): Crea un contenedor en Azure utilizando la imagen publicada.

Ejemplo de uso:
python deploy.py
"""


import os
import typer
from dotenv import load_dotenv
import subprocess as sp, subprocess
import sys
import time
import json
import random

app = typer.Typer() # me permite definir varios comandos que el usuario puede ejecutar desde la terminal

# Cargar variables desde el archivo .env
load_dotenv()
parameters = {
    "image_name": os.getenv("IMAGE_NAME"),
    "container_name":os.getenv("CONTAINER_NAME"),
    "image_tag":os.getenv("IMAGE_TAG", "v1.0.0"),
    "resource_group": os.getenv("RESOURCE_GROUP"),
    "location": os.getenv("LOCATION", "eastus"),
    "acr_name": os.getenv("ACR_NAME"),
    "port_container": os.getenv("PORT_CONTAINER", "5000"),
    "register_name": os.getenv("REGISTER_NAME")
}



def start_docker_desktop():
    """Inicia Docker Desktop si no está en ejecución."""
    docker_path = r"C:\Program Files\Docker\Docker\Docker Desktop.exe"

    try:
        result = sp.run(["docker", "info"], capture_output=True, text=True)
        if "Server Version" in result.stdout:
            print("Docker Desktop ya está corriendo.")
        else:
            print("Docker no está corriendo. Iniciando Docker Desktop...")
            sp.Popen([docker_path])
            time.sleep(5)

    except FileNotFoundError:
        print("Docker no está instalado o no se encontró en el PATH.")


def azure_login():
    """Iniciar sesión en la cuenta de Azure"""
    
    print(f"Nombre del ACR: {parameters['acr_name']}")

    try:
        sp.run([r"C:\Program Files\Microsoft SDKs\Azure\CLI2\wbin\az.cmd", "acr", "login", "--name", f"{parameters['acr_name']}"], check=True)

    except sp.CalledProcessError as e:
        print(f"Error al iniciar sesión en Azure: {e}")


def az_run():
    """Verifica si el grupo de recursos existe y lo crea si no."""
    filtro = f"[?name=='{parameters['resource_group']}']"
    try:
        catch_groups = sp.run([r"C:\Program Files\Microsoft SDKs\Azure\CLI2\wbin\az.cmd", "group", "list", "--query", filtro], capture_output=True, text=True, check=True)

        if catch_groups.stdout:  # Verifica si la salida no está vacía
            print("Existe el grupo de recursos")
            print(catch_groups.stdout)

        else:
            print(f"Creando grupo: {parameters['resource_group']}, \nen la localización: {parameters['location']}")
            create_r_group = sp.run(["az", "group", "create", "--name", parameters['resource_group'], "--location", parameters['location']], capture_output=True, text=True)
            print(create_r_group.stdout)  # Imprimir la salida del comando de creación de grupo
    except sp.CalledProcessError as e:
        print(f"Error en az: {e}")
    except FileNotFoundError as e:
        print(f"FileNotFoundError: {e}")


@app.command()
def check_az_acr():
    """Verifica la existencia del ACR y lo crea si no existe."""

    try:
        acr_check = sp.run(
            [r"C:\Program Files\Microsoft SDKs\Azure\CLI2\wbin\az.cmd", "acr", "list", "--query", f"[?name=='{parameters['acr_name']}']"],
            capture_output=True, text=True, check=True
        )

        if acr_check.stdout.strip() == "[]":
            print(f"El registro ACR '{parameters['acr_name']}' no existe. Creando uno nuevo...")
            # Crear un nuevo ACR si no existe
            sp.run(
                [r"C:\Program Files\Microsoft SDKs\Azure\CLI2\wbin\az.cmd", "acr", "create", "--resource-group", f"{parameters['resource_group']}", "--name", f"{parameters['acr_name']}", "--sku", "Basic"],
                check=True
            )
            print(f"ACR '{parameters['acr_name']}' creado con éxito.")
        else:
            print(f"El registro ACR '{parameters['acr_name']}' ya existe.")

        # Iniciar sesión en el ACR
        sp.run([r"C:\Program Files\Microsoft SDKs\Azure\CLI2\wbin\az.cmd", "acr", "login", "--name", parameters['acr_name']], check=True)
        print(f"Sesión iniciada en ACR '{parameters['acr_name']}'.")

    except sp.CalledProcessError as e:
        print(f"Error en la verificación o creación del ACR: {e}")

@app.command()
def build_image():
    """Construye la imagen Docker si no existe."""
    
    image_exists = os.popen(f"docker images --format '{{{{.Repository}}}}:{{{{.Tag}}}}'\
                                            --filter reference={parameters['image_name']}:{parameters['image_tag']}").read().strip()
    print(image_exists)
    if image_exists:
        print(f"Image {parameters['image_name']}:{parameters['image_tag']} already exists")
    else:
        print(f"Building image {parameters['image_name']}:{parameters['image_tag']}...")
        sp.run(f"docker build -t {parameters['image_name']}:{parameters['image_tag']} .")
        print("Image build complete.")

@app.command()
def grype_image_scan():
    """Escanea la imagen Docker en busca de vulnerabilidades."""

    os.system(f"grype {parameters['image_name']}:{parameters['image_tag']} --by-cve")
    
    
@app.command()
def push_image():
    """Publica la imagen Docker en el ACR."""

    os.system(f"docker tag {parameters['image_name']}:{parameters['image_tag']} {parameters['acr_name']}.azurecr.io/{parameters['image_name']}:{parameters['image_tag']}")
    os.system(f"docker push {parameters['acr_name']}.azurecr.io/{parameters['image_name']}:{parameters['image_tag']}")
    print(f"Image {parameters['image_name']}:{parameters['image_tag']} pushed to {parameters['image_name']}.azurecr.io.")

    # Listar imágenes en el ACR
    os.system(f"az acr repository list --name {parameters['acr_name']} --output table")

@app.command()
def create_container_acr():
    """Crea un contenedor en Azure utilizando la imagen publicada."""

    
    acr_registry_id = os.popen(f"az acr show --name {parameters['acr_name']} --query id --output tsv").read().strip()
    service_principal_name = "universidad"
    
    
    # Obtener el appId del Service Principal
    user_name = os.popen(f"az ad sp list --display-name {service_principal_name} --query [].appId --output tsv").read().strip()
    if user_name:
        print(f"Service Principal ID: {user_name}")
    else:
        print("No se encontró el Service Principal.")

    #Si no existe, crearlo
    if not user_name:
        print(f"Service principal '{service_principal_name}' no existe. Creándolo...")
        user_name = os.popen(f"az ad sp create-for-rbac \
                                --name {service_principal_name} \
                                --scopes {acr_registry_id} \
                                --role acrpull \
                                --query appId \
                                --output tsv").read().strip()
    else:
        print(f"Service principal '{service_principal_name}' ya existe con appId: {user_name}")
    
    # Obtener la contraseña del service principal
    password = os.popen(f"az ad sp credential reset --id {user_name} \
                                                    --query password \
                                                    --output tsv").read().strip()
    
    # Generar un valor DNS aleatorio
    dns_label = f"dns-um-{random.randint(1000, 9999)}"
    
    os.system(f"""
              az container create \
                --resource-group {parameters['resource_group']} \
                --name {parameters['container_name']} \
                --image {parameters['image_name']}.azurecr.io/{parameters['image_name']}:{parameters['image_tag']} \
                --cpu 1 \
                --memory 1 \
                --registry-login-server {parameters['image_name']}.azurecr.io \
                --ip-address Public \
                --location eastus \
                --registry-username {user_name} \
                --registry-password {password} \
                --dns-name-label api-um-eeg:{dns_label} \
                --ports {parameters['port_container']}""")

def app():
        #start_docker_desktop()
        azure_login()
        az_run()
        check_az_acr()
        build_image()
        grype_image_scan()
        push_image()
        create_container_acr()

if __name__ == "__main__":
    app()