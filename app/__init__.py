from flask import Flask
from flask_cors import CORS
from flask_swagger_ui import get_swaggerui_blueprint
from dotenv import load_dotenv
import os

from parsers.dtp_parser import start as dtp
from parsers.objects_parser import start as object

from app.routes_dtp import dtp_bp
from app.routes_objects import objects_bp
from app.routes_dict import dict_bp

# Загрузка переменных окружения
load_dotenv()

# URL для Swagger-документации
SWAGGER_URL = '/dtp/api/docs'
API_URL = '/static/swagger.yaml'

# Получение URL из переменной окружения
SERVER_URL = os.getenv('SERVER_URL', 'http://localhost:5000')

swagger_ui_blueprint = get_swaggerui_blueprint(
    SWAGGER_URL,
    API_URL,
    config={'app_name': "DTP Map API"}
)

def create_app():
    app = Flask(__name__)
    
    # Добавляем CORS для всех маршрутов
    CORS(app, resources={r"/*": {"origins": "*"}})

    # Регистрация маршрутов
    app.register_blueprint(dtp_bp, url_prefix='/dtp/api')
    app.register_blueprint(objects_bp, url_prefix='/dtp/api')
    app.register_blueprint(dict_bp, url_prefix='/dtp/api')
    app.register_blueprint(swagger_ui_blueprint, url_prefix=SWAGGER_URL)

    return app

app = create_app()
