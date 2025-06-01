import pymysql
from flask import Flask, request, jsonify, render_template_string
import random
import string
import requests
from dateutil import parser
from dateutil import tz

def generar_codigo_corto():
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))

app = Flask(__name__)

# Conexión a MySQL
db = pymysql.connect(
    host="canvas-backend-db.c07yeca6uwgy.us-east-1.rds.amazonaws.com",
    user="admin",
    password="dUPQ9TpcpDMJC6V",
    database="canvas_alexa",
    cursorclass=pymysql.cursors.DictCursor
)

with db.cursor() as cursor:
    cursor.execute("CREATE DATABASE IF NOT EXISTS canvas_alexa;")
db.commit()
db.close()

# Ruta para registrar o actualizar token
@app.route('/register', methods=['POST'])
def register():
    data = request.json
    alexa_id = data.get("alexa_user_id")
    token = data.get("canvas_token")

    if not alexa_id or not token:
        return jsonify({"error": "Faltan datos"}), 400

    # Guardar siempre en tabla users el token asociado al alexa_id
    with db.cursor() as cursor:
        cursor.execute("REPLACE INTO users (alexa_user_id, canvas_token) VALUES (%s, %s)", (alexa_id, token))
        db.commit()

    return jsonify({"message": "Token registrado con éxito."})

def procesar_tareas_para_alexa(user_id):
    with db.cursor() as cursor:
        cursor.execute("SELECT canvas_token FROM users WHERE alexa_user_id = %s", (user_id,))
        result = cursor.fetchone()

    if not result:
        # Si el usuario aún no está vinculado, genera o recupera un código corto
        with db.cursor() as cursor:
            cursor.execute("SELECT code FROM codes WHERE alexa_user_id = %s", (user_id,))
            existing = cursor.fetchone()

        if existing:
            codigo_corto = existing["code"]
        else:
            # Generar nuevo código único
            while True:
                codigo_corto = generar_codigo_corto()
                with db.cursor() as cursor:
                    cursor.execute("SELECT 1 FROM codes WHERE code = %s", (codigo_corto,))
                    if not cursor.fetchone():
                        break
            with db.cursor() as cursor:
                cursor.execute("INSERT INTO codes (code, alexa_user_id) VALUES (%s, %s)", (codigo_corto, user_id))
                db.commit()

        return {
            "version": "1.0",
            "response": {
                "outputSpeech": {
                    "type": "PlainText",
                    "text": f"No estás vinculado aún. Ve a la página web y escribe este código: {codigo_corto}"
                },
                "shouldEndSession": True
            }
        }

    token = result["canvas_token"]
    headers = {"Authorization": f"Bearer {token}"}
    try:
        response = requests.get("https://uide.instructure.com/api/v1/users/self/upcoming_events", headers=headers)
        print("Respuesta de Canvas:", response.status_code)
        print("Contenido:", response.text)

        if response.status_code == 401:
            texto_error = "Token inválido o expirado. Por favor, vuelve a vincular tu cuenta."
        elif response.status_code != 200:
            texto_error = f"Error de Canvas ({response.status_code}). Intenta más tarde."

        if response.status_code != 200:
            return {
                "version": "1.0",
                "response": {
                    "outputSpeech": {
                        "type": "PlainText",
                        "text": texto_error
                    },
                    "shouldEndSession": True
                }
            }

    except Exception as e:
        print("Excepción al consultar Canvas:", str(e))
        return {
            "version": "1.0",
            "response": {
                "outputSpeech": {
                    "type": "PlainText",
                    "text": "Ocurrió un error inesperado al conectar con Canvas."
                },
                "shouldEndSession": True
            }
        }

    eventos = response.json()
    if not eventos:
        return {
            "version": "1.0",
            "response": {
                "outputSpeech": {
                    "type": "PlainText",
                    "text": "No tienes tareas pendientes."
                },
                "shouldEndSession": True
            }
        }

    zona_local = tz.gettz("America/Guayaquil")
    texto = "Tienes las siguientes tareas pendientes. "

    for evento in eventos[:5]:
        assignment = evento.get("assignment", {})
        nombre = assignment.get("name", "sin título")
        curso = evento.get("context_name", "curso desconocido")
        fecha_iso = assignment.get("due_at")

        if fecha_iso:
            try:
                fecha_dt = parser.isoparse(fecha_iso).astimezone(zona_local)
                fecha_formateada = fecha_dt.strftime("%d de %B a las %I:%M %p")
            except Exception:
                fecha_formateada = "fecha inválida"
        else:
            fecha_formateada = "sin fecha"

        texto += f"{nombre} de {curso}, para el {fecha_formateada}. "

    return {
        "version": "1.0",
        "response": {
            "outputSpeech": {
                "type": "PlainText",
                "text": texto
            },
            "shouldEndSession": True
        }
    }


# Ruta raíz que Alexa llama por defecto
@app.route('/', methods=['POST'])
def root_handler():
    data = request.get_json()
    user_id = data.get("session", {}).get("user", {}).get("userId")
    print("Alexa User ID:", user_id)
    if not user_id:
        return jsonify({
            "version": "1.0",
            "response": {
                "outputSpeech": {
                    "type": "PlainText",
                    "text": "No pude identificar tu usuario de Alexa."
                },
                "shouldEndSession": True
            }
        })
    return jsonify(procesar_tareas_para_alexa(user_id))

# Ruta alternativa si decides apuntar a /tareas directamente
@app.route('/tareas', methods=['POST'])
def tareas_handler():
    data = request.get_json()
    user_id = data.get("session", {}).get("user", {}).get("userId")
    if not user_id:
        return jsonify({
            "version": "1.0",
            "response": {
                "outputSpeech": {
                    "type": "PlainText",
                    "text": "No pude identificar tu usuario de Alexa."
                },
                "shouldEndSession": True
            }
        })
    return jsonify(procesar_tareas_para_alexa(user_id))

@app.route('/borrar_usuario/<codigo>', methods=['GET'])
def borrar_usuario(codigo):
    with db.cursor() as cursor:
        # Buscar el user_id asociado al código
        cursor.execute("SELECT alexa_user_id FROM codes WHERE code = %s", (codigo,))
        resultado = cursor.fetchone()
        if not resultado:
            return f"No se encontró ningún usuario con el código {codigo}", 404

        alexa_user_id = resultado["alexa_user_id"]

        # Borrar de ambas tablas
        cursor.execute("DELETE FROM users WHERE alexa_user_id = %s", (alexa_user_id,))
        cursor.execute("DELETE FROM codes WHERE alexa_user_id = %s", (alexa_user_id,))
        db.commit()

    return f"Usuario con código {codigo} eliminado exitosamente."


@app.route('/vincular', methods=['GET', 'POST'])
def formulario_vinculacion():
    if request.method == 'GET':
        return render_template_string(FORM_HTML, mensaje="", color="")

    alexa_user_id = request.form.get('alexa_user_id')
    canvas_token = request.form.get('canvas_token')
    short_code = request.form.get('alexa_code')
    token = request.form.get('token')

    # Si el formulario viejo con ID completo y token
    if alexa_user_id and canvas_token:
        with db.cursor() as cursor:
            cursor.execute("REPLACE INTO users (alexa_user_id, canvas_token) VALUES (%s, %s)", (alexa_user_id, canvas_token))
            db.commit()
        return render_template_string(FORM_HTML, mensaje="¡Vinculación exitosa!", color="green")

    # Si viene desde el formulario corto: código corto + token
    if short_code and token:
        with db.cursor() as cursor:
            cursor.execute("SELECT alexa_user_id FROM codes WHERE code = %s", (short_code,))
            match = cursor.fetchone()

        if not match:
            return render_template_string(FORM_HTML, mensaje="Código no válido.", color="red")

        alexa_user_id = match["alexa_user_id"]
        with db.cursor() as cursor:
            cursor.execute("REPLACE INTO users (alexa_user_id, canvas_token) VALUES (%s, %s)", (alexa_user_id, token))
            db.commit()

        return render_template_string(FORM_HTML, mensaje="¡Token vinculado con éxito!", color="green")


    return render_template_string(FORM_HTML, mensaje="Faltan datos.", color="red")

FORM_HTML = '''
<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <title>Vincular Canvas con Alexa</title>
    <style>
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: #f9f9f9;
            padding: 40px;
        }

        h2 {
            color: #2c3e50;
        }

        .formulario {
            background: #fff;
            padding: 25px 30px;
            border-radius: 8px;
            box-shadow: 0 0 10px rgba(0,0,0,0.1);
            max-width: 600px;
        }

        label {
            font-weight: bold;
            display: block;
            margin-top: 15px;
        }

        input {
            width: 100%;
            padding: 10px;
            margin-top: 5px;
            border-radius: 5px;
            border: 1px solid #ccc;
        }

        button {
            background-color: #3498db;
            color: white;
            border: none;
            padding: 12px 25px;
            margin-top: 20px;
            border-radius: 5px;
            cursor: pointer;
            font-size: 16px;
        }

        button:hover {
            background-color: #2980b9;
        }

        .mensaje {
            margin-top: 20px;
            font-weight: bold;
            color: {{ color }};
        }

        .separador {
            margin: 30px 0;
            text-align: center;
            color: #888;
        }
    </style>
</head>
<body>
    <h2>Vincular tu cuenta de Canvas con Alexa</h2>
        <form method="POST">
            <label for="alexa_code">Código corto (de 6 letras):</label>
            <input type="text" name="alexa_code" id="alexa_code" maxlength="6">

            <label for="token">Tu token de Canvas:</label>
            <input type="text" name="token" id="token">

            <button type="submit">Vincular con código</button>
        </form>

        {% if mensaje %}
            <div class="mensaje">{{ mensaje }}</div>
        {% endif %}
    </div>
</body>
</html>
'''


if __name__ == '__main__':
    app.run()

