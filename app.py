from app import create_app  # Importamos la función factory de __init__.py

# Crear la aplicación usando la función factory
app = create_app()

if __name__ == '__main__':
    # Ejecutamos la aplicación en modo desarrollo o producción
    app.run(host='0.0.0.0', port=5000)