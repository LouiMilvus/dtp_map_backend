from flask import Blueprint, jsonify
import pandas as pd
import os

objects_bp = Blueprint('objects', __name__)

# Путь к CSV-файлам
DATA_DIR = '/opt/dtp_map_backend/data/objects/output'

# Вспомогательная функция для загрузки CSV в JSON с фильтрацией
def load_csv(file_name):
    file_path = os.path.join(DATA_DIR, file_name)
    try:
        df = pd.read_csv(file_path)

        # Фильтрация: исключить type_data = 5
        if 'type_data' in df.columns:
            df = df[df['type_data'] != 5]

        # Удаление строк с null в coord_w или coord_l
        if {'coord_w', 'coord_l'}.issubset(df.columns):
            df = df.dropna(subset=['coord_w', 'coord_l'])

        return df.to_dict(orient='records')
    except Exception as e:
        return {"error": str(e)}
        

# Маршруты
@objects_bp.route('/objects/traffic_cameras', methods=['GET'])
def get_traffic_cameras():
    """Возвращает данные по камерам (исключая type_data = 5)"""
    data = load_csv('file_traffic_cameras_path_output.csv')
    return jsonify(data)

@objects_bp.route('/objects/uchrez', methods=['GET'])
def get_uchrez():
    """Возвращает данные по учреждениям (исключая type_data = 5)"""
    data = load_csv('file_uchrez_path_output.csv')
    return jsonify(data)
