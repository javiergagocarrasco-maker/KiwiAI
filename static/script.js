const formulario = document.getElementById("formulario");
const entrada = document.getElementById("mensaje");
const chat = document.getElementById("chat");


function añadirMensaje(texto, tipo) {

    const mensaje = document.createElement("div");

    mensaje.className = "mensaje " + tipo;

    const avatar = document.createElement("div");

    avatar.className = "avatar";

    avatar.textContent = tipo === "kiwi" ? "🦜" : "👤";

    const burbuja = document.createElement("div");

    burbuja.className = "burbuja";

    burbuja.textContent = texto;

    mensaje.appendChild(avatar);
    mensaje.appendChild(burbuja);

    chat.appendChild(mensaje);

    chat.scrollTop = chat.scrollHeight;
}


formulario.addEventListener("submit", async function(evento) {

    evento.preventDefault();

    const mensaje = entrada.value.trim();

    if (!mensaje) {
        return;
    }

    añadirMensaje(mensaje, "usuario");

    entrada.value = "";

    try {

        const respuesta = await fetch("/chat", {

            method: "POST",

            headers: {
                "Content-Type": "application/json"
            },

            body: JSON.stringify({
                mensaje: mensaje
            })

        });

        const datos = await respuesta.json();

        añadirMensaje(datos.respuesta, "kiwi");

    } catch (error) {

        añadirMensaje(
            "🦜 ¡Pío! Ha ocurrido un error.",
            "kiwi"
        );

        console.error(error);
    }

});