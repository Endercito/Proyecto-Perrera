import os
import sqlite3
from datetime import datetime
from functools import wraps
from flask import Flask, render_template, request, jsonify, session, redirect, url_for
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "obera_liquid_glass_secret_2026_key")

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
DB_PATH = os.path.join(BASE_DIR, "adopciones_obera.db")
UPLOAD_FOLDER = os.path.join(BASE_DIR, "static", "uploads")
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
app.config["MAX_CONTENT_LENGTH"] = 8 * 1024 * 1024  # 8 MB max por imagen

ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "webp", "gif"}

ADMIN_USER = "municipalidadobera"
ADMIN_PASS = "2026obera"


def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db():
    conn = get_db()
    cursor = conn.cursor()

    # Tabla de Adoptantes / Ciudadanos que reservan
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS adoptantes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre_completo TEXT NOT NULL,
            dni TEXT NOT NULL,
            telefono TEXT NOT NULL,
            fecha_retiro TEXT NOT NULL,
            necesita_transporte INTEGER NOT NULL DEFAULT 0,
            observaciones TEXT DEFAULT '',
            fecha_solicitud TEXT NOT NULL
        )
    ''')

    # Tabla de Mascotas vinculada por clave foránea a adoptantes
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS mascotas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre TEXT NOT NULL,
            especie TEXT NOT NULL DEFAULT 'Perro',
            sexo TEXT NOT NULL DEFAULT 'Macho',
            edad_valor INTEGER NOT NULL DEFAULT 1,
            edad_unidad TEXT NOT NULL DEFAULT 'años',
            tamanio TEXT NOT NULL DEFAULT 'Mediano',
            tiene_raza INTEGER NOT NULL DEFAULT 0,
            raza TEXT DEFAULT 'Mestizo',
            vacunado INTEGER NOT NULL DEFAULT 0,
            castrado INTEGER NOT NULL DEFAULT 0,
            desparasitado INTEGER NOT NULL DEFAULT 0,
            necesita_ayuda_medica INTEGER NOT NULL DEFAULT 0,
            detalle_medico TEXT DEFAULT '',
            cualidades TEXT DEFAULT '',
            defectos TEXT DEFAULT '',
            foto_url TEXT DEFAULT '',
            estado TEXT NOT NULL DEFAULT 'DISPONIBLE',
            adoptante_id INTEGER,
            fecha_registro TEXT NOT NULL,
            FOREIGN KEY (adoptante_id) REFERENCES adoptantes(id) ON DELETE SET NULL
        )
    ''')

    # Cargar datos iniciales si la tabla está vacía
    count = cursor.execute("SELECT COUNT(*) FROM mascotas").fetchone()[0]
    if count == 0:
        hoy = datetime.now().strftime("%Y-%m-%d")
        datos_iniciales = [
            (
                "Canela", "Perro", "Hembra", 2, "años", "Mediano",
                0, "Mestiza", 1, 1, 1, 0, "",
                "Muy cariñosa, juguetona con niños y obediente al pasear con correa.",
                "Ladra cuando escucha motos pasar frente al portón.",
                "https://images.unsplash.com/photo-1587300003388-59208cc962cb?auto=format&fit=crop&w=800&q=80",
                "DISPONIBLE", None, hoy
            ),
            (
                "Thor", "Perro", "Macho", 4, "años", "Grande",
                1, "Cruza Labrador", 1, 1, 1, 0, "",
                "Excelente guardián, tranquilo dentro de casa y súper leal.",
                "Necesita patio amplio porque tiene mucha energía.",
                "https://images.unsplash.com/photo-1552053831-71594a27632d?auto=format&fit=crop&w=800&q=80",
                "DISPONIBLE", None, hoy
            ),
            (
                "Luna", "Perro", "Hembra", 5, "meses", "Chico",
                0, "Mestiza", 0, 0, 1, 1, "Requiere completar refuerzo de vacuna quíntuple en 15 días.",
                "Curiosa, aprende rápido y se lleva genial con gatos.",
                "Todavía muerde zapatillas si se queda sola mucho tiempo.",
                "https://images.unsplash.com/photo-1543466835-00a7907e9de1?auto=format&fit=crop&w=800&q=80",
                "DISPONIBLE", None, hoy
            ),
            (
                "Mora", "Perro", "Hembra", 3, "años", "Grande",
                0, "Mestiza", 1, 0, 1, 0, "",
                "Dulce, tranquila y compañera ideal para personas mayores.",
                "Es un poco tímida al principio con desconocidos.",
                "https://images.unsplash.com/photo-1517849845537-4d257902454a?auto=format&fit=crop&w=800&q=80",
                "DISPONIBLE", None, hoy
            ),
            (
                "Simón", "Gato", "Macho", 8, "meses", "Chico",
                0, "Común Europeo", 1, 1, 1, 0, "",
                "Usa piedras sanitarias, muy limpio y ronronea apenas lo acarician.",
                "Le tiene miedo a los ruidos fuertes de tormenta.",
                "https://images.unsplash.com/photo-1514888286974-6c03e2ca1dba?auto=format&fit=crop&w=800&q=80",
                "DISPONIBLE", None, hoy
            )
        ]
        cursor.executemany('''
            INSERT INTO mascotas (
                nombre, especie, sexo, edad_valor, edad_unidad, tamanio,
                tiene_raza, raza, vacunado, castrado, desparasitado,
                necesita_ayuda_medica, detalle_medico, cualidades, defectos,
                foto_url, estado, adoptante_id, fecha_registro
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', datos_iniciales)

    conn.commit()
    conn.close()


init_db()


def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get("admin_logged_in"):
            return jsonify({"ok": False, "error": "No autorizado. Iniciá sesión como administrador."}), 401
        return f(*args, **kwargs)
    return decorated_function


def formatear_mascota(row):
    d = dict(row)
    d["tiene_raza"] = bool(d["tiene_raza"])
    d["vacunado"] = bool(d["vacunado"])
    d["castrado"] = bool(d["castrado"])
    d["desparasitado"] = bool(d["desparasitado"])
    d["necesita_ayuda_medica"] = bool(d["necesita_ayuda_medica"])
    if "necesita_transporte" in d and d["necesita_transporte"] is not None:
        d["necesita_transporte"] = bool(d["necesita_transporte"])
    return d


# ================= RUTAS DE VISTAS HTML =================

@app.route("/")
def index():
    return render_template("index.html")


@app.route("/admin")
def admin():
    return render_template("admin.html", logged_in=bool(session.get("admin_logged_in")))


# ================= AUTENTICACIÓN ADMIN =================

@app.route("/api/admin/login", methods=["POST"])
def api_admin_login():
    data = request.get_json() or request.form
    usuario = data.get("usuario", "").strip()
    password = data.get("password", "").strip()

    if usuario == ADMIN_USER and password == ADMIN_PASS:
        session["admin_logged_in"] = True
        return jsonify({"ok": True, "mensaje": "Acceso concedido al panel municipal"})
    return jsonify({"ok": False, "error": "Usuario o contraseña incorrectos"}), 401


@app.route("/api/admin/logout", methods=["POST"])
def api_admin_logout():
    session.pop("admin_logged_in", None)
    return jsonify({"ok": True})


# ================= API PÚBLICA (CATÁLOGO Y RESERVA) =================

@app.route("/api/mascotas/publicas", methods=["GET"])
def api_mascotas_publicas():
    conn = get_db()
    # Solo DISPONIBLE y RESERVADO. Orden: DISPONIBLE primero (0), RESERVADO al fondo (1)
    rows = conn.execute('''
        SELECT id, nombre, especie, sexo, edad_valor, edad_unidad, tamanio,
               tiene_raza, raza, vacunado, castrado, desparasitado,
               necesita_ayuda_medica, detalle_medico, cualidades, defectos,
               foto_url, estado, fecha_registro
        FROM mascotas
        WHERE estado IN ('DISPONIBLE', 'RESERVADO')
        ORDER BY CASE estado WHEN 'DISPONIBLE' THEN 0 WHEN 'RESERVADO' THEN 1 ELSE 2 END, id DESC
    ''').fetchall()
    conn.close()
    mascotas = [formatear_mascota(r) for r in rows]
    return jsonify({"ok": True, "mascotas": mascotas})


@app.route("/api/reservar/<int:mascota_id>", methods=["POST"])
def api_reservar_mascota(mascota_id):
    data = request.get_json() or request.form
    nombre_completo = data.get("nombre_completo", "").strip()
    dni = data.get("dni", "").strip()
    telefono = data.get("telefono", "").strip()
    fecha_retiro = data.get("fecha_retiro", "").strip()
    necesita_transporte = 1 if data.get("necesita_transporte") in (True, "true", "1", "si", "Sí", "on") else 0
    observaciones = data.get("observaciones", "").strip()

    if not nombre_completo or not dni or not telefono or not fecha_retiro:
        return jsonify({"ok": False, "error": "Por favor completá Nombre completo, DNI, Teléfono y Fecha de retiro."}), 400

    conn = get_db()
    mascota = conn.execute("SELECT * FROM mascotas WHERE id = ?", (mascota_id,)).fetchone()

    if not mascota:
        conn.close()
        return jsonify({"ok": False, "error": "La mascota seleccionada no existe."}), 404

    if mascota["estado"] != "DISPONIBLE":
        conn.close()
        return jsonify({"ok": False, "error": "Esta mascota ya fue reservada o adoptada."}), 400

    ahora = datetime.now().strftime("%Y-%m-%d %H:%M")
    cursor = conn.cursor()

    # Insertar registro en la tabla adoptantes
    cursor.execute('''
        INSERT INTO adoptantes (nombre_completo, dni, telefono, fecha_retiro, necesita_transporte, observaciones, fecha_solicitud)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', (nombre_completo, dni, telefono, fecha_retiro, necesita_transporte, observaciones, ahora))
    adoptante_id = cursor.lastrowid

    # Relacionar directamente en SQLite3 la mascota con el adoptante y pasar a RESERVADO
    cursor.execute('''
        UPDATE mascotas
        SET estado = 'RESERVADO', adoptante_id = ?
        WHERE id = ?
    ''', (adoptante_id, mascota_id))

    conn.commit()
    conn.close()

    return jsonify({
        "ok": True,
        "mensaje": f"¡Reserva confirmada para {mascota['nombre']}! Te esperamos el {fecha_retiro} en la Perrera Municipal de Oberá."
    })


# ================= API ADMINISTRACIÓN (CRUD COMPLETO) =================

@app.route("/api/admin/mascotas", methods=["GET"])
@login_required
def api_admin_mascotas():
    conn = get_db()
    rows = conn.execute('''
        SELECT m.*,
               a.nombre_completo AS adoptante_nombre,
               a.dni AS adoptante_dni,
               a.telefono AS adoptante_telefono,
               a.fecha_retiro AS adoptante_fecha_retiro,
               a.necesita_transporte AS necesita_transporte,
               a.observaciones AS adoptante_observaciones,
               a.fecha_solicitud AS adoptante_fecha_solicitud
        FROM mascotas m
        LEFT JOIN adoptantes a ON m.adoptante_id = a.id
        ORDER BY CASE m.estado
            WHEN 'RESERVADO' THEN 0
            WHEN 'DISPONIBLE' THEN 1
            WHEN 'ADOPTADO' THEN 2
            ELSE 3
        END, m.id DESC
    ''').fetchall()
    conn.close()

    mascotas = [formatear_mascota(r) for r in rows]
    stats = {
        "total": len(mascotas),
        "disponibles": sum(1 for m in mascotas if m["estado"] == "DISPONIBLE"),
        "reservados": sum(1 for m in mascotas if m["estado"] == "RESERVADO"),
        "adoptados": sum(1 for m in mascotas if m["estado"] == "ADOPTADO"),
        "ayuda_medica": sum(1 for m in mascotas if m["necesita_ayuda_medica"] and m["estado"] != "ADOPTADO")
    }
    return jsonify({"ok": True, "mascotas": mascotas, "stats": stats})


@app.route("/api/admin/mascotas", methods=["POST"])
@login_required
def api_admin_crear_mascota():
    # Soporta multipart/form-data (con archivo de imagen) o JSON
    form = request.form if request.form else (request.get_json() or {})

    nombre = form.get("nombre", "").strip()
    if not nombre:
        return jsonify({"ok": False, "error": "El nombre de la mascota es obligatorio."}), 400

    especie = form.get("especie", "Perro").strip()
    sexo = form.get("sexo", "Macho").strip()
    try:
        edad_valor = int(form.get("edad_valor", 1))
    except ValueError:
        edad_valor = 1
    edad_unidad = form.get("edad_unidad", "años").strip()
    tamanio = form.get("tamanio", "Mediano").strip()

    tiene_raza = 1 if form.get("tiene_raza") in (True, "true", "1", "si", "Sí", "on") else 0
    raza = form.get("raza", "").strip() if tiene_raza else "Mestizo"
    if tiene_raza and not raza:
        raza = "De raza (sin especificar)"

    vacunado = 1 if form.get("vacunado") in (True, "true", "1", "si", "Sí", "on") else 0
    castrado = 1 if form.get("castrado") in (True, "true", "1", "si", "Sí", "on") else 0
    desparasitado = 1 if form.get("desparasitado") in (True, "true", "1", "si", "Sí", "on") else 0
    necesita_ayuda_medica = 1 if form.get("necesita_ayuda_medica") in (True, "true", "1", "si", "Sí", "on") else 0
    detalle_medico = form.get("detalle_medico", "").strip() if necesita_ayuda_medica else ""

    cualidades = form.get("cualidades", "").strip()
    defectos = form.get("defectos", "").strip()
    estado = form.get("estado", "DISPONIBLE").strip().upper()
    if estado not in ("DISPONIBLE", "RESERVADO", "ADOPTADO"):
        estado = "DISPONIBLE"

    foto_url = form.get("foto_url", "").strip()

    # Manejo de subida de imagen local si viene en request.files
    if "foto_archivo" in request.files:
        archivo = request.files["foto_archivo"]
        if archivo and archivo.filename != "" and allowed_file(archivo.filename):
            filename = secure_filename(f"{datetime.now().strftime('%Y%m%d%H%M%S')}_{archivo.filename}")
            filepath = os.path.join(app.config["UPLOAD_FOLDER"], filename)
            archivo.save(filepath)
            foto_url = f"/static/uploads/{filename}"

    hoy = datetime.now().strftime("%Y-%m-%d")
    conn = get_db()
    conn.execute('''
        INSERT INTO mascotas (
            nombre, especie, sexo, edad_valor, edad_unidad, tamanio,
            tiene_raza, raza, vacunado, castrado, desparasitado,
            necesita_ayuda_medica, detalle_medico, cualidades, defectos,
            foto_url, estado, adoptante_id, fecha_registro
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, NULL, ?)
    ''', (
        nombre, especie, sexo, edad_valor, edad_unidad, tamanio,
        tiene_raza, raza, vacunado, castrado, desparasitado,
        necesita_ayuda_medica, detalle_medico, cualidades, defectos,
        foto_url, estado, hoy
    ))
    conn.commit()
    conn.close()

    return jsonify({"ok": True, "mensaje": f"Mascota '{nombre}' agregada correctamente al sistema."})


@app.route("/api/admin/mascotas/<int:mascota_id>/estado", methods=["PUT"])
@login_required
def api_admin_cambiar_estado(mascota_id):
    data = request.get_json() or {}
    nuevo_estado = data.get("estado", "").strip().upper()

    if nuevo_estado not in ("DISPONIBLE", "RESERVADO", "ADOPTADO"):
        return jsonify({"ok": False, "error": "Estado inválido. Debe ser DISPONIBLE, RESERVADO o ADOPTADO."}), 400

    conn = get_db()
    mascota = conn.execute("SELECT * FROM mascotas WHERE id = ?", (mascota_id,)).fetchone()
    if not mascota:
        conn.close()
        return jsonify({"ok": False, "error": "Mascota no encontrada."}), 404

    # Si vuelve a DISPONIBLE, se libera la vinculación con el adoptante anterior
    if nuevo_estado == "DISPONIBLE":
        conn.execute("UPDATE mascotas SET estado = 'DISPONIBLE', adoptante_id = NULL WHERE id = ?", (mascota_id,))
    else:
        conn.execute("UPDATE mascotas SET estado = ? WHERE id = ?", (nuevo_estado, mascota_id))

    conn.commit()
    conn.close()
    return jsonify({"ok": True, "mensaje": f"Estado de {mascota['nombre']} actualizado a {nuevo_estado}."})


@app.route("/api/admin/mascotas/<int:mascota_id>", methods=["PUT"])
@login_required
def api_admin_editar_mascota(mascota_id):
    form = request.form if request.form else (request.get_json() or {})
    conn = get_db()
    mascota = conn.execute("SELECT * FROM mascotas WHERE id = ?", (mascota_id,)).fetchone()
    if not mascota:
        conn.close()
        return jsonify({"ok": False, "error": "Mascota no encontrada."}), 404

    nombre = form.get("nombre", mascota["nombre"]).strip()
    especie = form.get("especie", mascota["especie"]).strip()
    sexo = form.get("sexo", mascota["sexo"]).strip()
    try:
        edad_valor = int(form.get("edad_valor", mascota["edad_valor"]))
    except ValueError:
        edad_valor = mascota["edad_valor"]
    edad_unidad = form.get("edad_unidad", mascota["edad_unidad"]).strip()
    tamanio = form.get("tamanio", mascota["tamanio"]).strip()

    tiene_raza = 1 if form.get("tiene_raza") in (True, "true", "1", "si", "Sí", "on") else 0
    raza = form.get("raza", "").strip() if tiene_raza else "Mestizo"
    if tiene_raza and not raza:
        raza = "De raza"

    vacunado = 1 if form.get("vacunado") in (True, "true", "1", "si", "Sí", "on") else 0
    castrado = 1 if form.get("castrado") in (True, "true", "1", "si", "Sí", "on") else 0
    desparasitado = 1 if form.get("desparasitado") in (True, "true", "1", "si", "Sí", "on") else 0
    necesita_ayuda_medica = 1 if form.get("necesita_ayuda_medica") in (True, "true", "1", "si", "Sí", "on") else 0
    detalle_medico = form.get("detalle_medico", "").strip() if necesita_ayuda_medica else ""

    cualidades = form.get("cualidades", "").strip()
    defectos = form.get("defectos", "").strip()
    estado = form.get("estado", mascota["estado"]).strip().upper()
    foto_url = form.get("foto_url", mascota["foto_url"]).strip()

    if "foto_archivo" in request.files:
        archivo = request.files["foto_archivo"]
        if archivo and archivo.filename != "" and allowed_file(archivo.filename):
            filename = secure_filename(f"{datetime.now().strftime('%Y%m%d%H%M%S')}_{archivo.filename}")
            filepath = os.path.join(app.config["UPLOAD_FOLDER"], filename)
            archivo.save(filepath)
            foto_url = f"/static/uploads/{filename}"

    adoptante_id = None if estado == "DISPONIBLE" else mascota["adoptante_id"]

    conn.execute('''
        UPDATE mascotas SET
            nombre = ?, especie = ?, sexo = ?, edad_valor = ?, edad_unidad = ?, tamanio = ?,
            tiene_raza = ?, raza = ?, vacunado = ?, castrado = ?, desparasitado = ?,
            necesita_ayuda_medica = ?, detalle_medico = ?, cualidades = ?, defectos = ?,
            foto_url = ?, estado = ?, adoptante_id = ?
        WHERE id = ?
    ''', (
        nombre, especie, sexo, edad_valor, edad_unidad, tamanio,
        tiene_raza, raza, vacunado, castrado, desparasitado,
        necesita_ayuda_medica, detalle_medico, cualidades, defectos,
        foto_url, estado, adoptante_id, mascota_id
    ))
    conn.commit()
    conn.close()
    return jsonify({"ok": True, "mensaje": f"Ficha de {nombre} actualizada correctamente."})


@app.route("/api/admin/mascotas/<int:mascota_id>", methods=["DELETE"])
@login_required
def api_admin_eliminar_mascota(mascota_id):
    conn = get_db()
    conn.execute("DELETE FROM mascotas WHERE id = ?", (mascota_id,))
    conn.commit()
    conn.close()
    return jsonify({"ok": True, "mensaje": "Registro eliminado del sistema."})


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(debug=True, host="0.0.0.0", port=port)
