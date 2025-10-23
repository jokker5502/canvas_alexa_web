# Portal Estudiantil (Skill de Alexa para Canvas)
![Estado del Proyecto](https://img.shields.io/badge/estado-en%20desarrollo-green.svg) ![Lenguaje](https://img.shields.io/badge/python-3.x-blue.svg) ![Framework](https://img.shields.io/badge/flask-2.x-lightgrey.svg)

¡Bienvenidos al equipo! Este repositorio contiene el código fuente del backend para la skill de Alexa "Portal Estudiantil", diseñada para que los estudiantes puedan consultar sus tareas de Canvas usando la voz.

---

## 🗺️ Arquitectura del Sistema

Para entender cómo funciona todo, es clave conocer nuestros dos flujos de trabajo principales.

### Flujo 1: Petición de Tareas (Skill de Alexa)

1.  **🗣️ Usuario:** "Alexa, abre portal estudiantil".
2.  **☁️ Amazon:** Envía la petición a nuestro servidor (dominio `canvasalexaweb.sytes.net`).
3.  **🛡️ NGINX (Servidor EC2):** Recibe la petición en el puerto 443 (HTTPS), la procesa y actúa como un "portero" seguro.
4.  **🏃 Gunicorn (Servidor EC2):** NGINX pasa la petición a Gunicorn (nuestro servidor de aplicación profesional de Python).
5.  **🧠 app.py (Flask):** Gunicorn ejecuta la lógica en nuestra aplicación Flask (`@app.route('/')`).
6.  **🏦 RDS (MySQL):** La app busca el `user_id` de Alexa en la base de datos de producción.
7.  **🔑 API de Canvas:** Con el `token` guardado, la app consulta las tareas del usuario.
8.  **🗣️ Alexa:** Recibe el texto formateado desde nuestra app y se lo lee al usuario.

### Flujo 2: Vinculación de Cuentas (Página Web)

1.  **💻 Usuario:** Abre `https://canvasalexaweb.sytes.net/vincular` en su navegador.
2.  **🛡️ NGINX ➔ 🏃 Gunicorn ➔ 🧠 app.py:** El flujo es el mismo, pero se ejecuta la ruta (`@app.route('/vincular')`).
3.  **📄 HTML:** La app devuelve la página `templates/form.html`.
4.  **🔑 Usuario:** Ingresa su código y su token de Canvas.
5.  **🏦 RDS (MySQL):** La app busca el `short_code` en la base de datos y guarda el `token` en la fila de ese usuario.
6.  **💻 Usuario:** Ve el mensaje "¡Vinculación exitosa!".

---

## 🛠️ Stack de Tecnologías

* **Skill de Alexa:** Alexa Developer Console
* **Backend:** Python 3.x
* **Framework:** Flask
* **Servidor de Aplicación:** Gunicorn
* **Proxy Inverso (Servidor Web):** NGINX
* **Servidor (Hosting):** AWS EC2 (Ubuntu)
* **Base de Datos:** AWS RDS (MySQL)
* **Gestor de Servicio 24/7:** Systemd

---

## 🚀 Instalación y Configuración Local

Sigue estos pasos para configurar el entorno de desarrollo y ejecutar el proyecto localmente en tu propia computadora.

### Prerrequisitos

* [Python 3.x](https://www.python.org/downloads/)
* [Git](https://git-scm.com/downloads)
* Un cliente de base de datos como [MySQL Workbench](https://www.mysql.com/products/workbench/) (Opcional, pero recomendado).

### Pasos

1.  **Clona el repositorio:**
    (Pide al líder del proyecto la URL del repositorio privado).
    ```bash
    git clone <URL-DE-TU-REPOSITORIO-GIT>
    cd canvas_alexa_web
    ```

2.  **Crea el entorno virtual:**
    Se recomienda usar un entorno virtual para aislar las dependencias del proyecto. Usaremos `.venv` como nombre (que coincide con el `.gitignore`).

    ```bash
    # En Windows
    py -m venv .venv
    
    # En macOS/Linux
    python3 -m venv .venv
    ```

3.  **Activa el entorno virtual:**
    Deberás activar el entorno cada vez que quieras trabajar en el proyecto.

    * **Para Windows (CMD / Símbolo del sistema):**
        ```bash
        .\.venv\Scripts\activate.bat
        ```

    * **Para Windows (PowerShell):**
        ```powershell
        # Es posible que primero debas permitir la ejecución de scripts en tu sesión
        Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope Process
        
        # Luego activa
        .\.venv\Scripts\Activate.ps1
        ```
    
    * **Para macOS/Linux:**
        ```bash
        source .venv/bin/activate
        ```
    
    *Sabrás que está activo porque tu terminal mostrará `(.venv)` al inicio de la línea.*

4.  **Instala las dependencias:**
    Con el entorno virtual ya activo, instala todas las librerías necesarias que se encuentran en `requirements.txt`.
    ```bash
    pip install -r requirements.txt
    ```

5.  **Configura tus Variables de Entorno (¡MUY IMPORTANTE!)**
    La aplicación no funcionará sin sus credenciales.
    * Crea un nuevo archivo en la raíz del proyecto llamado `.env`
    * Copia y pega el siguiente contenido dentro de ese archivo:

    ```.env
    # Credenciales de la Base de Datos de DESARROLLO
    DB_HOST=
    DB_USER=
    DB_PASS=
    DB_NAME=
    
    # Dominio de Canvas (usualmente no cambia)
    CANVAS_DOMAIN=[https://canvas.instructure.com](https://canvas.instructure.com)
    ```
    * **¡Pide al líder del proyecto las credenciales de la base de datos de DESARROLLO (`canvas-db-dev`) y rellena los campos!**

---

## 🏃 Cómo ejecutar la aplicación

Una vez que el entorno esté activado, las dependencias instaladas y tu archivo `.env` esté listo, puedes iniciar el servidor de desarrollo en tu PC:

```bash
python app.py
