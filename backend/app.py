from flask import Flask, request, jsonify
from flask_cors import CORS
from supabase import create_client, Client
from dotenv import load_dotenv
import os
import logging
import json

# Configurar logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Cargar variables de entorno
load_dotenv()

# Validar variables de entorno
SUPABASE_URL = os.getenv('SUPABASE_URL')
SUPABASE_KEY = os.getenv('SUPABASE_KEY')

if not SUPABASE_URL or not SUPABASE_KEY:
    raise ValueError("Faltan variables de entorno SUPABASE_URL o SUPABASE_KEY")

# Inicializar Flask
app = Flask(__name__)
CORS(app)

# Inicializar Supabase
supabase: Client = create_client(
    supabase_url=SUPABASE_URL,
    supabase_key=SUPABASE_KEY
)

@app.route('/departamentos', methods=['POST'])
def crear_departamento():
    try:
        # 1. Validar Content-Type
        if not request.is_json:
            return jsonify({
                "error": "El Content-Type debe ser application/json"
            }), 400

        # 2. Obtener y validar datos
        data = request.get_json()
        if not data:
            return jsonify({
                "error": "No se recibieron datos"
            }), 400

        # 3. Validar campos requeridos
        if not all(key in data for key in ['numero', 'monto']):
            return jsonify({
                "error": "Faltan campos requeridos (numero, monto)"
            }), 400

        # 4. Convertir y validar tipos
        try:
            numero = int(float(data['numero']))
            monto = int(float(data['monto']))
        except (ValueError, TypeError):
            return jsonify({
                "error": "Los campos deben ser numéricos"
            }), 400

        # 5. Validar valores
        if numero <= 0:
            return jsonify({
                "error": "El número de departamento debe ser positivo"
            }), 400

        if monto < 0:
            return jsonify({
                "error": "El monto no puede ser negativo"
            }), 400

        # 6. Verificar si existe
        response = supabase.table('departamento')\
            .select('*')\
            .eq('numero', numero)\
            .execute()

        if len(response.data) > 0:
            return jsonify({
                "error": f"El departamento número {numero} ya está registrado"
            }), 409

        # 7. Crear departamento
        new_depto = {
            "numero": numero,
            "monto": monto,
            "estado": True
        }

        response = supabase.table('departamento')\
            .insert([new_depto])\
            .execute()

        if not response.data:
            return jsonify({
                "error": "Error al crear el departamento"
            }), 500

        return jsonify(response.data[0]), 201

    except Exception as e:
        app.logger.error(f"Error al crear departamento: {str(e)}")
        return jsonify({
            "error": "Error interno del servidor"
        }), 500

@app.route('/departamentos', methods=['GET'])
def obtener_departamentos():
    try:
        response = supabase.table('departamento')\
            .select('*')\
            .order('numero')\
            .execute()
            
        return jsonify(response.data), 200
        
    except Exception as e:
        logger.error(f"Error al obtener departamentos: {str(e)}")
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(port=5001, debug=True) 