# Sistema Municipal de Adopción de Mascotas - Oberá

Plataforma web full-stack desarrollada en **Python (Flask) + SQLite3 + HTML/CSS/JS** con estética **Liquid Glass 2027**, diseñada para la gestión de adopciones y reservas de la Perrera Municipal de Oberá.

## Características principales

1. **Catálogo Público (`index.html`)**:
   - Visualización de mascotas en tarjetas estilo cristal líquido con fotos, ficha médica, edad (meses/años), raza, cualidades y defectos.
   - **Ordenamiento inteligente**: Las mascotas **DISPONIBLES** aparecen primero; las **RESERVADAS** se desplazan automáticamente al final del catálogo con la insignia `RESERVADO` junto a su nombre. Las **ADOPTADAS** desaparecen del catálogo público.
   - **Modal de Reserva**: Formulario ciudadano donde el adoptante ingresa Nombre Completo, DNI, Teléfono, Fecha de retiro (calendario) y si requiere transporte municipal. Al confirmar, se vincula directamente en SQLite3 con la mascota.

2. **Panel de Administración (`admin.html`)**:
   - Acceso protegido por sesión (`Usuario: municipalidadobera` | `Contraseña: 2026obera`).
   - Alta de nuevas mascotas con carga de foto (o URL externa), especie, sexo, tamaño, edad (en meses o años), raza, vacunado, castrado, desparasitado, ayuda médica requerida, cualidades y defectos/cuidados especiales.
   - Control de estados (`DISPONIBLE`, `RESERVADO`, `ADOPTADO`), edición rápida, vista de fichas de adoptantes vinculados y eliminación de registros.

## Despliegue en Render (desde GitHub)

1. Subí todos los archivos de esta carpeta a un repositorio en GitHub.
2. En **Render**, creá un nuevo **Web Service** conectado a tu repositorio.
3. Configurá:
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `gunicorn app:app`
4. ¡Listo! La base de datos SQLite3 (`adopciones_obera.db`) y los datos iniciales se crean automáticamente al iniciar.
