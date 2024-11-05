from asyncio.log import logger
from dotenv import load_dotenv
from pathlib import Path
import os

basedir = os.path.abspath(Path(__file__).parents[2])
load_dotenv(os.path.join(basedir, '.env'))

#Factory Methods

class Config(object):
    TESTING = False
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_RECORD_QUERIES = True
    
    @staticmethod
    def init_app(app):
        pass

class DevelopmentConfig(Config):
    TESTING = True
    DEBUG = True
    FLASK_ENV = 'development'
    SQLALCHEMY_DATABASE_URI = os.environ.get('DEV_DATABASE_URI')
    CONNECTION_STRING = os.environ.get('CONNECTION_STRING')
    OTEL_SERVICE_NAME = os.environ.get('OTEL_SERVICE_NAME')
        
class ProductionConfig(Config):
    FLASK_ENV = 'production'
    DEBUG = False
    TESTING = False
    SQLALCHEMY_RECORD_QUERIES = False
    SQLALCHEMY_DATABASE_URI = os.environ.get('PROD_DATABASE_URI')
    
    @classmethod
    def init_app(cls, app):
        Config.init_app(app)



def factory(app):
    configuration = {
        'development': DevelopmentConfig,
        'production': ProductionConfig,
        #'test': TestConfig, #podría sumar más clases de configuraciones para seleccionar
    }
    
    return configuration[app]