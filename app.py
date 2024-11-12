from app import create_app
import logging
from healthcheck import HealthCheck
import psycopg2
from psycopg2 import OperationalError
import os

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
app = create_app()
app.app_context().push()

# Configuración del HealthCheck
health = HealthCheck()

# Función de verificación de salud para la app
def app_working():
    return True, "App is working"

# Función de verificación de salud para la base de datos (test db)
def db_working():
    try:
        connection = psycopg2.connect(
            host=app.config["DB_HOST"],
            database=app.config["DB_NAME"],
            user=app.config["DB_USER"],
            password=app.config["DB_PASSWORD"],
            sslmode=app.config["DB_SSLMODE"]
        )
        cursor = connection.cursor()
        cursor.execute("SELECT NOW();")  # Prueba la conexión con una consulta básica
        cursor.close()
        connection.close()
        return True, "Database is working"
    except OperationalError as e:
        return False, f"Database connection failed: {str(e)}"

# Añadir las verificaciones de salud
health.add_check(app_working)
health.add_check(db_working)

# Configura el endpoint de healthcheck manualmente
app.add_url_rule("/healthcheck", "healthcheck", view_func=lambda: health.run())

@app.route('/')
def hello_azure():
    return 'Hello, Azure!'

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)