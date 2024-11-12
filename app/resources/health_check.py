import logging
from flask import Blueprint, jsonify
from flask import current_app as app
from datetime import datetime
import psycopg2
import os
import psutil
import platform
import sys
import time

health_bp = Blueprint('health', __name__)

class SystemMetrics:
    @staticmethod
    def get_metrics():
        """Recolecta métricas del sistema"""
        process = psutil.Process()
        memory = psutil.virtual_memory()
        
        return {
            "status": "healthy",
            "metrics": {
                "cpu": {
                    "process_cpu_percent": process.cpu_percent(),
                    "system_cpu_percent": psutil.cpu_percent(interval=1),
                    "cpu_count": psutil.cpu_count()
                },
                "memory": {
                    "process_memory_mb": process.memory_info().rss / 1024 / 1024,
                    "system_total_gb": memory.total / (1024 ** 3),
                    "system_available_gb": memory.available / (1024 ** 3),
                    "system_percent_used": memory.percent
                },
                "disk": {
                    "disk_usage": psutil.disk_usage('/').percent
                },
                "system_info": {
                    "python_version": sys.version,
                    "platform": platform.platform(),
                    "uptime_seconds": time.time() - process.create_time()
                }
            }
        }

class DatabaseCheck:
    @staticmethod
    def get_db_config():
        """Obtiene la configuración de la base de datos desde variables de entorno"""
        return {
            'host': os.getenv('AZURE_POSTGRESQL_HOST'),
            'database': os.getenv('AZURE_POSTGRESQL_DB'),
            'user': os.getenv('AZURE_POSTGRESQL_USER'),
            'password': os.getenv('AZURE_POSTGRESQL_PASSWORD'),
            'port': os.getenv('AZURE_POSTGRESQL_PORT')
        }

    @staticmethod
    def check_connection():
        """Verifica el estado de la conexión a la base de datos"""
        start_time = time.time()
        db_config = DatabaseCheck.get_db_config()
        
        # Verificar variables de entorno
        required_vars = ['host', 'database', 'user', 'password', 'port']
        missing_vars = [var for var in required_vars if not db_config.get(var)]
        
        if missing_vars:
            return {
                "status": "unhealthy",
                "message": f"Missing environment variables: {', '.join(missing_vars)}"
            }
        
        try:
            conn_string = f"host={db_config['host']} " \
                         f"dbname={db_config['database']} " \
                         f"user={db_config['user']} " \
                         f"password={db_config['password']} " \
                         f"port={db_config['port']}"
            
            conn = psycopg2.connect(conn_string)
            
            # Realizar pruebas básicas de la base de datos
            with conn.cursor() as cur:
                # Test de lectura
                cur.execute('SELECT 1')
                cur.fetchone()
                
                # Test de escritura en tabla temporal
                cur.execute("""
                    CREATE TEMP TABLE IF NOT EXISTS health_check_test 
                    (test_id serial PRIMARY KEY, test_time timestamp)
                """)
                cur.execute("INSERT INTO health_check_test (test_time) VALUES (NOW()) RETURNING test_id")
                test_id = cur.fetchone()[0]
                
                # Limpiar
                cur.execute("DROP TABLE health_check_test")
            
            conn.close()
            response_time = time.time() - start_time
            
            return {
                "status": "healthy",
                "message": "Database connection successful",
                "metrics": {
                    "response_time_ms": round(response_time * 1000, 2),
                    "read_write_test": "passed",
                    "connection_details": {
                        "host": db_config['host'],
                        "port": db_config['port'],
                        "database": db_config['database']
                    }
                }
            }
            
        except psycopg2.OperationalError as e:
            return {
                "status": "unhealthy",
                "message": f"Database connection failed: {str(e)}",
                "connection_details": {
                    "host": db_config['host'],
                    "port": db_config['port'],
                    "database": db_config['database']
                }
            }
        except Exception as e:
            return {
                "status": "unhealthy",
                "message": f"Unexpected error: {str(e)}"
            }

@health_bp.route('/', methods=['GET'])
def full_health_check():
    start_time = time.time()
    
    try:
        db_status = DatabaseCheck.check_connection()
        system_status = SystemMetrics.get_metrics()
        
        overall_status = "healthy"
        if db_status.get("status") != "healthy" or system_status.get("status") != "healthy":
            overall_status = "unhealthy"
        
        response = {
            "status": overall_status,
            "timestamp": datetime.utcnow().isoformat(),
            "checks": {
                "database": db_status,
                "system": system_status,
                "api_status": "available",
                "environment": os.getenv('FLASK_ENV', 'production')
            }
        }
        
        # Verificar si azure_monitor está disponible antes de usarlo
        if hasattr(app, 'azure_monitor') and app.azure_monitor:
            logging.info("Azure Monitor initialized, but telemetry client removed")
        else:
            logging.warning("Azure Monitor not initialized")
        
        http_status = 200 if overall_status == "healthy" else 503
        return jsonify(response), http_status
        
    except Exception as e:
        logging.error(f"Health check failed: {str(e)}")
        raise

@health_bp.route('/basic', methods=['GET'])
def basic_health_check():
    """Health check básico y rápido para kubernetes liveness probe"""
    return jsonify({
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat()
    }), 200

@health_bp.route('/database', methods=['GET'])
def database_health_check():
    """Health check específico para la base de datos"""
    db_status = DatabaseCheck.check_connection()
    http_status = 200 if db_status.get("status") == "healthy" else 503
    return jsonify({
        "timestamp": datetime.utcnow().isoformat(),
        "database": db_status
    }), http_status

@health_bp.route('/system', methods=['GET'])
def system_health_check():
    """Health check específico para métricas del sistema"""
    system_status = SystemMetrics.get_metrics()
    return jsonify({
        "timestamp": datetime.utcnow().isoformat(),
        "system": system_status
    }), 200

@health_bp.route('/test-telemetry', methods=['GET'])
def test_telemetry():
    logging.info("Telemetry test endpoint called - Azure Monitor telemetry client removed")
    return jsonify({"message": "Telemetry test logged"}), 200