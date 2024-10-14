from flask import Flask, request
import os
import socket

app = Flask(__name__)

@app.route('/')
def home():
    # Obtener la región desde la variable de entorno
    region = os.getenv("AWS_REGION", "unknown")
    
    # Obtener el hostname del pod o contenedor
    hostname = socket.gethostname()
    
    # Obtener la IP del cliente desde el encabezado X-Forwarded-For o request.remote_addr
    ip = request.headers.get('X-Forwarded-For', request.remote_addr)
    
    # Retornar la respuesta con región, hostname e IP del cliente
    return f"""
        <h1>Region: {region}</h1>
        <h1>Hostname: {hostname}</h1>
        <h1>Client IP: {ip}</h1>
        <h1>Hola mundo v1</h1>
    """

@app.route('/health')
def health():
    return 'Healthy', 200

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=80)