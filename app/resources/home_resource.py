from flask import Blueprint, jsonify

# Crear el Blueprint para el Home
home_bp = Blueprint('home', __name__)

# Ruta de ejemplo para el Home
@home_bp.route('/', methods=['GET'])
def hello():
    return jsonify({
        "message": "Hello, Azure!",
        "status": "success"
    })