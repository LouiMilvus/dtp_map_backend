from flask import Blueprint, jsonify
import pandas as pd
import os

dict_bp = Blueprint('dict', __name__)

# Путь к CSV-файлам
DATA_DIR = '/opt/dtp_map_backend/data/dict'

# Вспомогательная функция для загрузки CSV в JSON
def load_csv(file_name):
    file_path = os.path.join(DATA_DIR, file_name)
    try:
        df = pd.read_csv(file_path)
        return df.to_dict(orient='records')
    except Exception as e:
        return {"error": str(e)}

# Маршруты
@dict_bp.route('/dict/mo', methods=['GET'])
def get_mo():
    data = load_csv('mo.csv')
    return jsonify(data)

@dict_bp.route('/dict/narusheniya', methods=['GET'])
def get_narusheniya():
    data = load_csv('narusheniya.csv')
    return jsonify(data)

@dict_bp.route('/dict/osveshenie', methods=['GET'])
def get_osveshenie():
    data = load_csv('osveshenie.csv')
    return jsonify(data)

@dict_bp.route('/dict/sost_pogodi', methods=['GET'])
def get_sost_pogodi():
    data = load_csv('sost_pogodi.csv')
    return jsonify(data)

@dict_bp.route('/dict/sost_proez_chasti', methods=['GET'])
def get_sost_proez_chasti():
    data = load_csv('sost_proez_chasti.csv')
    return jsonify(data)

@dict_bp.route('/dict/uchrez_type', methods=['GET'])
def get_uchrez_type():
    data = load_csv('uchrez_type.csv')
    return jsonify(data)

@dict_bp.route('/dict/vid_dtp', methods=['GET'])
def get_vid_dtp():
    data = load_csv('vid_dtp.csv')
    return jsonify(data)
