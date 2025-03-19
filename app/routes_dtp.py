from flask import Blueprint, jsonify, request
import pandas as pd
import ast
import os
import numpy as np
import re

dtp_bp = Blueprint('dtp', __name__)

# Путь к CSV-файлу
DATA_FILE = '/opt/dtp_map_backend/data/dtp/output/output.csv'

# Словарь для преобразования type в нужные имена
TYPE_MAP = {
    "Водитель": "driver",
    "Пассажир": "passenger",
    "Пешеход": "pedestrian"
}

# Вспомогательная функция для загрузки данных и фильтрации
def load_and_filter_dtp(year=None, mo=None, vid_dtp=None):
    try:
        # Загружаем данные
        df = pd.read_csv(DATA_FILE)

        # Преобразуем дату в формат dd.mm.yyyy и извлекаем год
        df['year'] = pd.to_datetime(df['date_dtp'], dayfirst=True).dt.year

        # Выбираем нужные поля
        df = df[['id_kard', 'year', 'mo', 'vid_dtp', 'coord_w', 'coord_l']]

        # Фильтрация
        if year:
            df = df[df['year'] == int(year)]
        if mo:
            df = df[df['mo'] == int(mo)]
        if vid_dtp:
            df = df[df['vid_dtp'] == int(vid_dtp)]

        return df.to_dict(orient='records')

    except Exception as e:
        return {"error": str(e)}

# Маршрут с фильтрацией
@dtp_bp.route('/dtp/coord', methods=['GET'])
def get_dtp_coord():
    """Возвращает данные ДТП с фильтрацией по year, mo, vid_dtp"""
    year = request.args.get('year')
    mo = request.args.get('mo')
    vid_dtp = request.args.get('vid_dtp')

    data = load_and_filter_dtp(year, mo, vid_dtp)
    return jsonify(data)

# Вспомогательная функция для загрузки данных по id_kard
def get_card_by_id(id_kard):
    try:
        # Загружаем данные
        df = pd.read_csv(DATA_FILE)

        # Фильтрация по id_kard
        card = df[df['id_kard'] == int(id_kard)].to_dict(orient='records')

        if not card:
            return {"error": "ДТП с указанным id_kard не найдено"}

        card = card[0]  # Берем первую запись

        # ✅ Парсим вину в массив объектов
        vina_raw = card.get('vina', '[]')

        # Обработка NaN и пустых значений
        if isinstance(vina_raw, float) and np.isnan(vina_raw):
            vina_raw = '[]'

        # Убираем лишние кавычки, если они есть
        if vina_raw.startswith('"') and vina_raw.endswith('"'):
            vina_raw = vina_raw[1:-1]

        # Исправляем NaN → None и кортежи → списки
        vina_fixed = vina_raw.replace('nan', 'None')
        vina_fixed = re.sub(r'\((.*?)\)', r'[\1]', vina_fixed)

        # Парсинг в массив Python-объектов
        try:
            vina_list = ast.literal_eval(vina_fixed)
        except (SyntaxError, ValueError):
            vina_list = []

        # Форматирование вины в нужный формат
        vina_formatted = []

        for item in vina_list:
            if not isinstance(item, dict) or item.get('type') in [None, 'nan']:
                continue

            type_name = item.get('type', 'N/A')
            type_key = TYPE_MAP.get(type_name, 'unknown')

            vina_formatted.append({
                "number_ts": {
                    "title": "Транспортное средство №",
                    "value": f"{item.get('number_ts', 'N/A')}"
                },
                type_key: {
                    "title": type_name,
                    "value": {
                        "stepen_tyazhesti": {
                            "title": "Степень тяжести",
                            "value": item.get('stepen_tyazhesti', 'N/A')
                        },
                        "narushenie": {
                            "title": "Нарушения",
                            "value": list(item.get('narushenie', []))
                        }
                    }
                }
            })

        # Формирование итогового ответа
        result = {
            "id_kard": {"title": "ID карточки", "value": card['id_kard']},
            "date_dtp": {"title": "Дата ДТП", "value": card['date_dtp']},
            "vid_dtp": {"title": "Вид ДТП", "value": card['vid_dtp']},
            "mo": {"title": "Муниципальный округ", "value": card['mo']},
            "sost_pogodi": {"title": "Состояние погоды", "value": card['sost_pogodi']},
            "sost_proez_chasti": {"title": "Состояние проезжей части", "value": card['sost_proez_chasti']},
            "osveshenie": {"title": "Освещение", "value": card['osveshenie']},
            "vina": {
                "title": "Вина",
                "value": vina_formatted
            }
        }

        return result

    except Exception as e:
        return {"error": str(e)}


# Маршрут для получения карточки по id_kard
@dtp_bp.route('/dtp/card/<int:id_kard>', methods=['GET'])
def get_dtp_card(id_kard):
    """Возвращает карточку ДТП по id_kard"""
    data = get_card_by_id(id_kard)
    return jsonify(data)
