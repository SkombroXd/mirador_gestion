import requests
import json

# URL del endpoint
url = 'http://localhost:5001/departamentos'

# Datos del nuevo departamento
data = {
    "numero": 302,  # Diferente al 301 que ya existe
    "monto": 150000
}

# Headers
headers = {
    'Content-Type': 'application/json'
}

try:
    # Enviar solicitud POST
    response = requests.post(url, json=data, headers=headers)
    
    # Imprimir resultado
    print(f"Status Code: {response.status_code}")
    print("Response:", response.json())
    
except Exception as e:
    print("Error:", str(e)) 