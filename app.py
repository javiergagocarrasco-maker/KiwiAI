from flask import Flask, render_template, request, jsonify
import requests
import sqlite3
import random
import json
from datetime import datetime
from zoneinfo import ZoneInfo

app = Flask(__name__)

DB = "usuarios.db"


# =========================
# BASE DE DATOS
# =========================

def conectar():
    return sqlite3.connect(DB)


def crear_base_datos():

    db = conectar()

    db.execute("""
        CREATE TABLE IF NOT EXISTS usuarios (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT UNIQUE,
            password TEXT,
            nombre TEXT DEFAULT '',
            avatar TEXT DEFAULT '',
            fecha_registro TEXT DEFAULT ''
        )
    """)

    columnas = [
        ("nombre", "TEXT DEFAULT ''"),
        ("avatar", "TEXT DEFAULT ''"),
        ("fecha_registro", "TEXT DEFAULT ''")
    ]

    existentes = [
        fila[1]
        for fila in db.execute(
            "PRAGMA table_info(usuarios)"
        ).fetchall()
    ]

    for nombre, tipo in columnas:

        if nombre not in existentes:

            db.execute(
                f"ALTER TABLE usuarios ADD COLUMN {nombre} {tipo}"
            )

    db.commit()
    db.close()


crear_base_datos()


# =========================
# PAGINA PRINCIPAL
# =========================

@app.route("/")
def inicio():

    return render_template(
        "index.html"
    )


# =========================
# REGISTRO
# =========================

@app.route(
    "/registro",
    methods=["POST"]
)
def registro():

    datos = request.json or {}

    email = datos.get(
        "email",
        ""
    ).strip()

    password = datos.get(
        "password",
        ""
    )

    nombre = datos.get(
        "nombre",
        ""
    ).strip()

    if not email or not password:

        return jsonify({
            "ok": False,
            "mensaje":
                "Completa todos los campos."
        })

    if not nombre:

        nombre = email.split("@")[0]

    fecha = datetime.now().strftime(
        "%d/%m/%Y"
    )

    db = conectar()

    try:

        db.execute("""
            INSERT INTO usuarios
            (email, password, nombre, avatar, fecha_registro)
            VALUES (?, ?, ?, ?, ?)
        """, (
            email,
            password,
            nombre,
            "",
            fecha
        ))

        db.commit()
        db.close()

        return jsonify({
            "ok": True
        })

    except sqlite3.IntegrityError:

        db.close()

        return jsonify({
            "ok": False,
            "mensaje":
                "Ese correo ya está registrado."
        })


# =========================
# LOGIN
# =========================

@app.route(
    "/login",
    methods=["POST"]
)
def login():

    datos = request.json or {}

    email = datos.get(
        "email",
        ""
    ).strip()

    password = datos.get(
        "password",
        ""
    )

    db = conectar()

    usuario = db.execute("""
        SELECT
            id,
            email,
            password,
            nombre,
            avatar,
            fecha_registro
        FROM usuarios
        WHERE email = ?
        AND password = ?
    """, (
        email,
        password
    )).fetchone()

    db.close()

    if usuario:

        return jsonify({

            "ok": True,

            "usuario": {

                "id": usuario[0],

                "email": usuario[1],

                "nombre":
                    usuario[3] or "",

                "avatar":
                    usuario[4] or "",

                "fecha_registro":
                    usuario[5] or ""

            }

        })

    return jsonify({

        "ok": False,

        "mensaje":
            "Correo o contraseña incorrectos."

    })


# =========================
# PERFIL
# =========================

@app.route(
    "/perfil",
    methods=["POST"]
)
def perfil():

    datos = request.json or {}

    email = datos.get(
        "email",
        ""
    ).strip()

    db = conectar()

    usuario = db.execute("""
        SELECT
            id,
            email,
            nombre,
            avatar,
            fecha_registro
        FROM usuarios
        WHERE email = ?
    """, (
        email,
    )).fetchone()

    db.close()

    if not usuario:

        return jsonify({
            "ok": False,
            "mensaje":
                "Usuario no encontrado."
        })

    return jsonify({

        "ok": True,

        "usuario": {

            "id": usuario[0],

            "email": usuario[1],

            "nombre":
                usuario[2] or "",

            "avatar":
                usuario[3] or "",

            "fecha_registro":
                usuario[4] or ""

        }

    })


# =========================
# ACTUALIZAR PERFIL
# =========================

@app.route(
    "/actualizar_perfil",
    methods=["POST"]
)
def actualizar_perfil():

    datos = request.json or {}

    email = datos.get(
        "email",
        ""
    ).strip()

    nombre = datos.get(
        "nombre",
        ""
    ).strip()

    avatar = datos.get(
        "avatar",
        ""
    )

    if not email:

        return jsonify({
            "ok": False,
            "mensaje":
                "Usuario no identificado."
        })

    db = conectar()

    db.execute("""
        UPDATE usuarios
        SET nombre = ?, avatar = ?
        WHERE email = ?
    """, (
        nombre,
        avatar,
        email
    ))

    db.commit()
    db.close()

    return jsonify({
        "ok": True
    })


# =========================
# ELIMINAR CUENTA
# =========================

@app.route(
    "/eliminar_cuenta",
    methods=["POST"]
)
def eliminar_cuenta():

    datos = request.json or {}

    email = datos.get(
        "email",
        ""
    ).strip()

    if not email:

        return jsonify({
            "ok": False,
            "mensaje":
                "Usuario no identificado."
        })

    db = conectar()

    db.execute(
        "DELETE FROM usuarios WHERE email = ?",
        (email,)
    )

    db.commit()
    db.close()

    return jsonify({
        "ok": True
    })


# =========================
# RECUPERAR CONTRASEÑA
# =========================

codigos = {}


@app.route(
    "/generar_codigo",
    methods=["POST"]
)
def generar_codigo():

    email = request.json.get(
        "email",
        ""
    ).strip()

    db = conectar()

    usuario = db.execute(
        "SELECT id FROM usuarios WHERE email = ?",
        (email,)
    ).fetchone()

    db.close()

    if not usuario:

        return jsonify({
            "ok": False,
            "mensaje":
                "No existe esa cuenta."
        })

    codigo = str(
        random.randint(
            100000,
            999999
        )
    )

    codigos[email] = codigo

    print()
    print(
        "CÓDIGO DE RECUPERACIÓN:",
        codigo
    )
    print()

    return jsonify({

        "ok": True,

        "codigo": codigo

    })


@app.route(
    "/cambiar_password",
    methods=["POST"]
)
def cambiar_password():

    datos = request.json or {}

    email = datos.get(
        "email",
        ""
    ).strip()

    codigo = datos.get(
        "codigo",
        ""
    ).strip()

    password = datos.get(
        "password",
        ""
    )

    if codigos.get(email) != codigo:

        return jsonify({
            "ok": False,
            "mensaje":
                "Código incorrecto."
        })

    db = conectar()

    db.execute("""
        UPDATE usuarios
        SET password = ?
        WHERE email = ?
    """, (
        password,
        email
    ))

    db.commit()
    db.close()

    codigos.pop(
        email,
        None
    )

    return jsonify({
        "ok": True
    })


# ==================================================
# HORA MUNDIAL
# ==================================================

ZONAS_HORARIAS = {

    # EUROPA

    "españa":
        ("Madrid, España", "Europe/Madrid"),

    "madrid":
        ("Madrid, España", "Europe/Madrid"),

    "portugal":
        ("Lisboa, Portugal", "Europe/Lisbon"),

    "lisboa":
        ("Lisboa, Portugal", "Europe/Lisbon"),

    "francia":
        ("París, Francia", "Europe/Paris"),

    "paris":
        ("París, Francia", "Europe/Paris"),

    "alemania":
        ("Berlín, Alemania", "Europe/Berlin"),

    "berlin":
        ("Berlín, Alemania", "Europe/Berlin"),

    "italia":
        ("Roma, Italia", "Europe/Rome"),

    "roma":
        ("Roma, Italia", "Europe/Rome"),

    "reino unido":
        ("Londres, Reino Unido", "Europe/London"),

    "inglaterra":
        ("Londres, Reino Unido", "Europe/London"),

    "londres":
        ("Londres, Reino Unido", "Europe/London"),

    "irlanda":
        ("Dublín, Irlanda", "Europe/Dublin"),

    "dublin":
        ("Dublín, Irlanda", "Europe/Dublin"),

    "rusia":
        ("Moscú, Rusia", "Europe/Moscow"),

    "moscu":
        ("Moscú, Rusia", "Europe/Moscow"),

    "turquia":
        ("Estambul, Turquía", "Europe/Istanbul"),

    "turquía":
        ("Estambul, Turquía", "Europe/Istanbul"),

    "estambul":
        ("Estambul, Turquía", "Europe/Istanbul"),


    # AMERICA

    "estados unidos":
        ("Nueva York, Estados Unidos", "America/New_York"),

    "eeuu":
        ("Nueva York, Estados Unidos", "America/New_York"),

    "usa":
        ("Nueva York, Estados Unidos", "America/New_York"),

    "nueva york":
        ("Nueva York, Estados Unidos", "America/New_York"),

    "los angeles":
        ("Los Ángeles, Estados Unidos", "America/Los_Angeles"),

    "los ángeles":
        ("Los Ángeles, Estados Unidos", "America/Los_Angeles"),

    "chicago":
        ("Chicago, Estados Unidos", "America/Chicago"),

    "mexico":
        ("Ciudad de México, México", "America/Mexico_City"),

    "méxico":
        ("Ciudad de México, México", "America/Mexico_City"),

    "ciudad de mexico":
        ("Ciudad de México, México", "America/Mexico_City"),

    "canada":
        ("Toronto, Canadá", "America/Toronto"),

    "canadá":
        ("Toronto, Canadá", "America/Toronto"),

    "toronto":
        ("Toronto, Canadá", "America/Toronto"),

    "brasil":
        ("São Paulo, Brasil", "America/Sao_Paulo"),

    "sao paulo":
        ("São Paulo, Brasil", "America/Sao_Paulo"),

    "são paulo":
        ("São Paulo, Brasil", "America/Sao_Paulo"),

    "argentina":
        ("Buenos Aires, Argentina",
         "America/Argentina/Buenos_Aires"),

    "buenos aires":
        ("Buenos Aires, Argentina",
         "America/Argentina/Buenos_Aires"),

    "chile":
        ("Santiago, Chile", "America/Santiago"),

    "santiago":
        ("Santiago, Chile", "America/Santiago"),

    "colombia":
        ("Bogotá, Colombia", "America/Bogota"),

    "bogota":
        ("Bogotá, Colombia", "America/Bogota"),

    "bogotá":
        ("Bogotá, Colombia", "America/Bogota"),

    "peru":
        ("Lima, Perú", "America/Lima"),

    "perú":
        ("Lima, Perú", "America/Lima"),

    "lima":
        ("Lima, Perú", "America/Lima"),

    "venezuela":
        ("Caracas, Venezuela", "America/Caracas"),

    "caracas":
        ("Caracas, Venezuela", "America/Caracas"),


    # ASIA

    "japon":
        ("Tokio, Japón", "Asia/Tokyo"),

    "japón":
        ("Tokio, Japón", "Asia/Tokyo"),

    "tokio":
        ("Tokio, Japón", "Asia/Tokyo"),

    "china":
        ("Pekín, China", "Asia/Shanghai"),

    "pekin":
        ("Pekín, China", "Asia/Shanghai"),

    "pequín":
        ("Pekín, China", "Asia/Shanghai"),

    "corea del sur":
        ("Seúl, Corea del Sur", "Asia/Seoul"),

    "seul":
        ("Seúl, Corea del Sur", "Asia/Seoul"),

    "seúl":
        ("Seúl, Corea del Sur", "Asia/Seoul"),

    "india":
        ("Nueva Delhi, India", "Asia/Kolkata"),

    "nueva delhi":
        ("Nueva Delhi, India", "Asia/Kolkata"),

    "tailandia":
        ("Bangkok, Tailandia", "Asia/Bangkok"),

    "bangkok":
        ("Bangkok, Tailandia", "Asia/Bangkok"),

    "dubai":
        ("Dubái, Emiratos Árabes Unidos", "Asia/Dubai"),

    "dubái":
        ("Dubái, Emiratos Árabes Unidos", "Asia/Dubai"),


    # OCEANÍA

    "australia":
        ("Sídney, Australia", "Australia/Sydney"),

    "sidney":
        ("Sídney, Australia", "Australia/Sydney"),

    "sydney":
        ("Sídney, Australia", "Australia/Sydney"),

    "nueva zelanda":
        ("Auckland, Nueva Zelanda", "Pacific/Auckland"),

    "auckland":
        ("Auckland, Nueva Zelanda", "Pacific/Auckland"),


    # ÁFRICA

    "egipto":
        ("El Cairo, Egipto", "Africa/Cairo"),

    "el cairo":
        ("El Cairo, Egipto", "Africa/Cairo"),

    "sudafrica":
        ("Johannesburgo, Sudáfrica",
         "Africa/Johannesburg"),

    "sudáfrica":
        ("Johannesburgo, Sudáfrica",
         "Africa/Johannesburg"),

    "islandia":
        ("Reikiavik, Islandia",
         "Atlantic/Reykjavik"),

    "reikiavik":
        ("Reikiavik, Islandia",
         "Atlantic/Reykjavik")
}


def detectar_zona_horaria(mensaje):

    texto = mensaje.lower()

    for lugar, datos in ZONAS_HORARIAS.items():

        if lugar in texto:

            return datos

    return None


def pregunta_por_hora(mensaje):

    texto = mensaje.lower()

    palabras = [

        "qué hora",

        "que hora",

        "hora es",

        "hora actual",

        "hora ahora",

        "hora mismo",

        "dime la hora",

        "dime qué hora",

        "dime que hora"

    ]

    for palabra in palabras:

        if palabra in texto:

            return True

    return False


def hora_actual(zona):

    ciudad, zona_horaria = zona

    ahora = datetime.now(
        ZoneInfo(zona_horaria)
    )

    return ciudad, ahora


# =========================
# KIWI AI
# =========================

@app.route(
    "/chat",
    methods=["POST"]
)
def chat():

    datos = request.json or {}

    mensaje = datos.get(
        "mensaje",
        ""
    ).strip()

    email = datos.get(
        "email",
        ""
    ).strip()


    if not mensaje:

        return jsonify({
            "respuesta":
                "Escribe algo."
        })


    # ==========================================
    # HORA ACTUAL
    # ==========================================

    if pregunta_por_hora(mensaje):

        zona = detectar_zona_horaria(
            mensaje
        )

        # Si no dice país/ciudad,
        # usamos la hora de Madrid.

        if zona is None:

            zona = (
                "Madrid, España",
                "Europe/Madrid"
            )

        ciudad, ahora = hora_actual(
            zona
        )

        respuesta_hora = (
            f"🕐 En {ciudad} son "
            f"las {ahora.strftime('%H:%M:%S')} "
            f"del {ahora.strftime('%d/%m/%Y')}."
        )

        return jsonify({
            "respuesta":
                respuesta_hora
        })


    # ==========================================
    # PERFIL / NOMBRE
    # ==========================================

    nombre = ""

    if email:

        db = conectar()

        usuario = db.execute(
            "SELECT nombre FROM usuarios WHERE email = ?",
            (email,)
        ).fetchone()

        db.close()

        if usuario:

            nombre = usuario[0] or ""


    # ==========================================
    # RESPUESTAS CARIÑOSAS
    # ==========================================

    respuestas_cariñosas = {

        "hola":
            "Pio 🦜",

        "holaa":
            "Piooo 🦜",

        "holaaa":
            "Piooo 🦜",

        "buenas":
            "Pio 🦜 ¿Qué tal?",

        "te quiero":
            "Yo también te quiero mucho 🦜",

        "te quiero mucho":
            "Yo también te quiero muchísimo 🦜",

        "te quiero kiwi":
            "Yo también te quiero mucho 🦜",

        "te adoro":
            "Y yo a ti 🦜",

        "eres precioso":
            "Piooo 🦜 gracias por decirme eso",

        "eres el mejor":
            "Y tú eres mi humano favorito 🦜",

        "eres mi amigo":
            "Claro que sí 🦜",

        "qué bonito eres":
            "Piooo 🦜 me vas a poner rojo",

        "buen chico":
            "Pio pio 🦜",

        "kiwi guapo":
            "Piooo 🦜"

    }


    mensaje_normalizado = (
        mensaje.lower()
    )


    if mensaje_normalizado in respuestas_cariñosas:

        respuesta = (
            respuestas_cariñosas[
                mensaje_normalizado
            ]
        )

        if (
            nombre
            and mensaje_normalizado == "hola"
        ):

            respuesta = (
                f"¡Hola {nombre}! 🦜 Pio"
            )

        return jsonify({
            "respuesta":
                respuesta
        })


    # ==========================================
    # MEMORIA
    # ==========================================

    memoria_archivo = (
        "memoria_kiwi.json"
    )

    try:

        with open(
            memoria_archivo,
            "r",
            encoding="utf-8"
        ) as archivo:

            memoria = json.load(
                archivo
            )

    except:

        memoria = {}


    for inicio in [
        "me llamo ",
        "mi nombre es ",
        "soy "
    ]:

        if mensaje_normalizado.startswith(
            inicio
        ):

            nuevo_nombre = mensaje[
                len(inicio):
            ].strip()

            if nuevo_nombre:

                memoria["nombre"] = (
                    nuevo_nombre
                )

                nombre = nuevo_nombre

                with open(
                    memoria_archivo,
                    "w",
                    encoding="utf-8"
                ) as archivo:

                    json.dump(
                        memoria,
                        archivo,
                        ensure_ascii=False,
                        indent=2
                    )

                if email:

                    db = conectar()

                    db.execute("""
                        UPDATE usuarios
                        SET nombre = ?
                        WHERE email = ?
                    """, (
                        nuevo_nombre,
                        email
                    ))

                    db.commit()
                    db.close()

            break


    if not nombre:

        nombre = memoria.get(
            "nombre",
            ""
        )


    # ==========================================
    # PROMPT
    # ==========================================

    sistema = f"""

Tu nombre es Kiwi AI.

Eres una inteligencia artificial llamada Kiwi AI.

Habla en español si el usuario habla español.

Sé natural, amable y claro.

El nombre del usuario es:
{nombre}

Si conoces el nombre del usuario,
puedes utilizarlo de forma natural.

No digas que eres Qwen.

No menciones Alibaba Cloud.

No recomiendes otros asistentes.

No digas que no tienes una base de datos.

Si el usuario pregunta quién es una persona famosa,
explica correctamente quién es.

Si pregunta si Michael Jackson murió,
responde que sí y que murió el
25 de junio de 2009.

No digas que tú eres Michael Jackson.

"""


    # ==========================================
    # OLLAMA
    # ==========================================

    try:

        respuesta = requests.post(

            "http://127.0.0.1:11434/api/chat",

            json={

                "model":
                    "llama3.2:latest",

                "messages": [

                    {
                        "role":
                            "system",

                        "content":
                            sistema
                    },

                    {
                        "role":
                            "user",

                        "content":
                            mensaje
                    }

                ],

                "stream":
                    False

            },

            timeout=120

        )


        if respuesta.status_code != 200:

            print(
                "ERROR OLLAMA:",
                respuesta.text
            )

            return jsonify({
                "respuesta":
                    "Kiwi ha tenido un problema."
            })


        datos = respuesta.json()

        texto = datos[
            "message"
        ][
            "content"
        ]


        return jsonify({
            "respuesta":
                texto.strip()
        })


    except requests.exceptions.ConnectionError:

        return jsonify({
            "respuesta":
                "Ollama no está funcionando."
        })


    except Exception as error:

        print(
            "ERROR:",
            error
        )

        return jsonify({
            "respuesta":
                "Ha ocurrido un error."
        })


# =========================
# ARRANCAR KIWI
# =========================

if __name__ == "__main__":

    print()
    print("==============================")
    print("          🦜 KIWI AI")
    print("==============================")
    print()

    print("Hora mundial: ACTIVADA")
    print()
    print("Abre:")
    print("http://127.0.0.1:5000")
    print()

if __name__ == '__main__':
    print('Modelo: qwen2.5:7b-instruct')
    app.run(host='0.0.0.0', port=5000)

if __name__ == "__main__":
    print("Modelo: qwen2.5:7b-instruct")
    app.run(host="0.0.0.0", port=5000)
