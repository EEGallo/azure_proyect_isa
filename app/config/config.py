import os
from flask import Flask
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.resources import Resource
from opentelemetry.instrumentation.flask import FlaskInstrumentor
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from azure.monitor.opentelemetry.exporter import AzureMonitorTraceExporter
import logging

class AzureMonitorConfig:
    """Configuración de Azure Monitor para telemetría de la aplicación"""
    
    def __init__(self, app: Flask, connection_string: str):
        self.app = app
        self.connection_string = connection_string
        self.logger = logging.getLogger(__name__)

    def _validate_connection_string(self) -> bool:
        if not self.connection_string:
            self.logger.error("Connection string is empty")
            return False

        required_parts = ['InstrumentationKey', 'IngestionEndpoint']
        try:
            parts = dict(part.split('=', 1) for part in self.connection_string.split(';'))
            return all(key in parts for key in required_parts)
        except ValueError:
            self.logger.error("Invalid connection string format")
            return False

    def initialize(self):
        """Inicializa la configuración de Azure Monitor"""
        try:
            self.logger.info("Initializing Azure Monitor...")

            if not self._validate_connection_string():
                raise ValueError("Invalid or missing Azure Monitor connection string")

            resource = Resource.create({
                "service.name": self.app.config.get('SERVICE_NAME', 'flask-app'),
                "service.namespace": self.app.config.get('SERVICE_NAMESPACE', 'default'),
                "service.instance.id": os.getenv("HOSTNAME", "unknown")
            })

            tracer_provider = TracerProvider(resource=resource)
            trace.set_tracer_provider(tracer_provider)

            trace_exporter = AzureMonitorTraceExporter(
                connection_string=self.connection_string
            )
            tracer_provider.add_span_processor(
                BatchSpanProcessor(trace_exporter)
            )

            FlaskInstrumentor().instrument_app(self.app)
            
            self.logger.info("Azure Monitor configured successfully")

        except Exception as e:
            self.logger.error(f"Failed to initialize Azure Monitor: {str(e)}")
            raise

    def track_exception(self, exception: Exception):
        """Registra una excepción en Azure Monitor"""
        self.logger.error("Exception tracked", exc_info=exception)


class Config:
    """Configuración base"""
    SERVICE_NAME = "flask-app"
    SERVICE_NAMESPACE = "default"
    DEBUG = False
    TESTING = False

    @staticmethod
    def init_app(app):
        pass


class DevelopmentConfig(Config):
    """Configuración para desarrollo"""
    DEBUG = True
    SERVICE_NAME = "flask-app-dev"

    @classmethod
    def init_app(cls, app):
        Config.init_app(app)


class ProductionConfig(Config):
    """Configuración para producción"""
    DEBUG = False
    SERVICE_NAME = "flask-app-prod"

    @classmethod
    def init_app(cls, app):
        Config.init_app(app)


class TestingConfig(Config):
    """Configuración para pruebas"""
    TESTING = True
    DEBUG = True
    SERVICE_NAME = "flask-app-test"


def get_config(app_context: str) -> type[Config]:
    """
    Factory para seleccionar la configuración según el contexto.
    
    Args:
        app_context: El contexto de la aplicación ('development', 'production', 'testing')
    
    Returns:
        La clase de configuración correspondiente
    """
    configurations = {
        'development': DevelopmentConfig,
        'production': ProductionConfig,
        'testing': TestingConfig
    }
    
    return configurations.get(app_context, DevelopmentConfig)


# Asegurándonos de que estas clases y funciones estén disponibles cuando se importe el módulo
__all__ = [
    'AzureMonitorConfig',
    'Config',
    'DevelopmentConfig',
    'ProductionConfig',
    'TestingConfig',
    'get_config'
]