from flask import Flask, render_template, request, jsonify
from ollama import chat

app = Flask(__name__)


@app.route("/")
def inicio():
    return render_template("index.html")


@app.route("/chat", methods=["POST"])
def responder():

    try:
        datos = request.get_json()
        mensaje = datos.get("mensaje", "").strip()

        if not mensaje:
            return jsonify({
                "respuesta": "🦜 ¡Pío! Escribe algo para Kiwi."
            })

        respuesta = chat(
            model="llama3.2",
            messages=[
                {
                    "role": "system",
                    "content": """
Eres Kiwi AI 🦜.

Eres un agapornis simpático, divertido y cercano.

Hablas siempre en español de España.

Puedes responder preguntas sobre cualquier tema.

Explica las cosas de forma sencilla y clara.

Puedes utilizar emojis de vez en cuando.

Tu nombre es Kiwi AI.

Nunca digas que no puedes responder simplemente porque eres un agapornis.
"""
                },
                {
                    "role": "user",
                    "content": mensaje
                }
            ]
        )

        texto = respuesta["message"]["content"]

        return jsonify({
            "respuesta": texto
        })

    except Exception as error:

        print("ERROR:", error)

        return jsonify({
            "respuesta": "🦜 Kiwi no puede conectarse con Ollama. Comprueba que Ollama esté funcionando."
        })


if __name__ == "__main__":
    app.run(debug=True)