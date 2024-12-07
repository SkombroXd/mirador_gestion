from supabase import create_client
from dotenv import load_dotenv
import os

# Cargar variables de entorno
load_dotenv()

# Obtener credenciales
SUPABASE_URL = os.getenv('SUPABASE_URL')
SUPABASE_KEY = os.getenv('SUPABASE_KEY')

if not SUPABASE_URL or not SUPABASE_KEY:
    raise ValueError("Faltan variables de entorno SUPABASE_URL o SUPABASE_KEY")

# Inicializar Supabase
supabase = create_client(
    supabase_url=SUPABASE_URL,
    supabase_key=SUPABASE_KEY
)

try:
    # Probar conexión
    response = supabase.table('departamento').select('*').limit(1).execute()
    print("Conexión exitosa!")
    print("Datos:", response.data)
except Exception as e:
    print("Error de conexión:", str(e)) 