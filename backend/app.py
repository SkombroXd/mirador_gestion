from flask import Flask, request, jsonify
from flask_cors import CORS
from supabase import create_client, Client
from dotenv import load_dotenv
import os
import logging
import json
from datetime import datetime

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

@app.route('/gastos/generar', methods=['POST'])
def generar_gasto():
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
        if not all(key in data for key in ['id_depa', 'monto_gasto']):
            return jsonify({
                "error": "Faltan campos requeridos (id_depa, monto_gasto)"
            }), 400

        # 4. Convertir y validar tipos
        try:
            id_depa = int(data['id_depa'])
            monto_gasto = int(data['monto_gasto'])
        except (ValueError, TypeError):
            return jsonify({
                "error": "Los campos deben ser numéricos"
            }), 400

        # 5. Validar valores
        if monto_gasto <= 0:
            return jsonify({
                "error": "El monto del gasto debe ser positivo"
            }), 400

        # 6. Verificar si existe el departamento y obtener su número
        depa_response = supabase.table('departamento')\
            .select('*')\
            .eq('id_depa', id_depa)\
            .execute()

        if not depa_response.data:
            return jsonify({
                "error": f"No existe el departamento con ID {id_depa}"
            }), 404

        numero_depto = depa_response.data[0]['numero']
        monto_base = depa_response.data[0]['monto']

        # 7. Crear gasto
        new_gasto = {
            "id_depa": id_depa,
            "monto_gasto": monto_gasto,
            "fecha_emision": datetime.now().date().isoformat(),
            "total_pago": monto_base + monto_gasto,  # Calculamos el total
            "pago": False
        }

        response = supabase.table('gastos')\
            .insert([new_gasto])\
            .execute()

        if not response.data:
            return jsonify({
                "error": "Error al crear el gasto"
            }), 500

        # Agregar el número de departamento a la respuesta
        gasto = response.data[0]
        gasto['numero_depto'] = numero_depto

        return jsonify(gasto), 201

    except Exception as e:
        app.logger.error(f"Error al generar gasto: {str(e)}")
        return jsonify({
            "error": "Error interno del servidor"
        }), 500

@app.route('/gastos/departamento/<int:id_depa>', methods=['GET'])
def obtener_gastos_departamento(id_depa):
    try:
        # Verificar si existe el departamento
        depa_response = supabase.table('departamento')\
            .select('*')\
            .eq('id_depa', id_depa)\
            .execute()

        if not depa_response.data:
            return jsonify({
                "error": f"No existe el departamento con ID {id_depa}"
            }), 404

        # Obtener el número de departamento
        numero_depto = depa_response.data[0]['numero']

        # Obtener gastos del departamento
        response = supabase.table('gastos')\
            .select('*')\
            .eq('id_depa', id_depa)\
            .execute()

        # Agregar el número de departamento a cada gasto
        gastos_con_numero = []
        for gasto in response.data:
            gasto['numero_depto'] = numero_depto
            gastos_con_numero.append(gasto)

        return jsonify(gastos_con_numero), 200

    except Exception as e:
        app.logger.error(f"Error al obtener gastos: {str(e)}")
        return jsonify({
            "error": "Error interno del servidor"
        }), 500

@app.route('/gastos/<int:id_gastos>/pago', methods=['PUT'])
def actualizar_estado_pago(id_gastos):
    try:
        data = request.get_json()
        if 'pago' not in data:
            return jsonify({
                "error": "Falta el campo pago"
            }), 400

        pago = bool(data['pago'])
        fecha_pago = datetime.now().date().isoformat() if pago else None

        # Actualizar estado de pago
        response = supabase.table('gastos')\
            .update({
                'pago': pago,
                'fecha_pago': fecha_pago
            })\
            .eq('id_gastos', id_gastos)\
            .execute()

        if not response.data:
            return jsonify({
                "error": "No se encontró el gasto"
            }), 404

        # Actualizar estado del departamento
        gasto = response.data[0]
        depa_response = supabase.table('gastos')\
            .select('pago')\
            .eq('id_depa', gasto['id_depa'])\
            .execute()

        # Si todos los gastos están pagados, el departamento está al día
        todos_pagados = all(g['pago'] for g in depa_response.data)
        
        supabase.table('departamento')\
            .update({'estado': todos_pagados})\
            .eq('id_depa', gasto['id_depa'])\
            .execute()

        return jsonify(response.data[0]), 200

    except Exception as e:
        app.logger.error(f"Error al actualizar estado: {str(e)}")
        return jsonify({
            "error": "Error interno del servidor"
        }), 500

@app.route('/gastos', methods=['GET'])
def obtener_todos_gastos():
    try:
        # Obtener todos los departamentos para mapear números
        depa_response = supabase.table('departamento')\
            .select('*')\
            .execute()
        
        # Crear un diccionario para mapear id_depa a número
        depa_map = {d['id_depa']: d['numero'] for d in depa_response.data}

        # Obtener todos los gastos
        response = supabase.table('gastos')\
            .select('*')\
            .order('fecha_emision', desc=True)\
            .execute()

        # Agregar el número de departamento a cada gasto
        gastos_con_numero = []
        for gasto in response.data:
            gasto['numero_depto'] = depa_map.get(gasto['id_depa'])
            gastos_con_numero.append(gasto)

        return jsonify(gastos_con_numero), 200

    except Exception as e:
        app.logger.error(f"Error al obtener gastos: {str(e)}")
        return jsonify({
            "error": "Error interno del servidor"
        }), 500

@app.route('/departamentos/estado', methods=['GET'])
def obtener_departamentos_estado():
    try:
        # Obtener todos los departamentos
        depa_response = supabase.table('departamento')\
            .select('*')\
            .execute()

        departamentos_info = []
        
        for depto in depa_response.data:
            # Obtener gastos pendientes del departamento
            gastos_response = supabase.table('gastos')\
                .select('*')\
                .eq('id_depa', depto['id_depa'])\
                .eq('pago', False)\
                .execute()
            
            # Calcular total adeudado
            total_adeudado = sum(gasto['total_pago'] for gasto in gastos_response.data)
            
            departamentos_info.append({
                'id_depa': depto['id_depa'],
                'numero': depto['numero'],
                'monto': depto['monto'],
                'estado': depto['estado'],
                'gastos_pendientes': len(gastos_response.data),
                'total_adeudado': total_adeudado
            })

        return jsonify(departamentos_info), 200

    except Exception as e:
        app.logger.error(f"Error al obtener departamentos: {str(e)}")
        return jsonify({
            "error": "Error interno del servidor"
        }), 500

if __name__ == '__main__':
    app.run(port=5001, debug=True) 