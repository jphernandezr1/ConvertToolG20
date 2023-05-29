# CovertToolG20
Online Converting Tool
En este repositorio se encuentra la aplicación en flask de conversion
 
# Video y otros archivos
[Video](https://uniandes-my.sharepoint.com/:f:/g/personal/jp_hernandezr1_uniandes_edu_co/Ej2sNNATMytKpl-zvF98aXMB3oJKqYmQ8r2q_08qLWFn1A?e=gSO2Ep)

[Documentación] (https://uniandes-my.sharepoint.com/:w:/g/personal/jf_castanol_uniandes_edu_co/EQzx7ZJIrYNNtO36F1wG53UBFHp2Zh18xXT14JJrPh9tpQ?e=otYeBw)

# Grupo-20:

Juan Pablo Hernandez

Juan David Diaz

Kevin Castrillon

Juan Felipe Castaño



# Base de datos:

tipo: postgres

usuario: cloud-user

clave: cloud-user

nombre: cloud-converter-tool

ip: 34.170.217.192

// dynamic-vehicle-383500:us-central1:clud-converter-tool

puerto: 5432

# Maquina virtual:

IP EXTERNA MÁQUINA VIRTUAL 34.72.252.51

# Comandos:

Web server: flask run
Worker: redis-server --port 6363 --protected-mode no
Celery: celery -A views worker --loglevel=INFO
