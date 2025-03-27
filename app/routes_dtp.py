from flask import Blueprint, jsonify, request
import pandas as pd
import ast
import os
import numpy as np
import re

dtp_bp = Blueprint('dtp', __name__)

# Пути к данным
DATA_FILE = '/opt/dtp_map_backend/data/dtp/output/output.csv'
DICT_DIR = '/opt/dtp_map_backend/data/dict'

# Кеш словарей
DICTS = {}

# Словарь для преобразования type в нужные имена
TYPE_MAP = {
    "Водитель": "driver",
    "Пассажир": "passenger",
    "Пешеход": "pedestrian"
}


# ✅ Функция загрузки словарей
def load_dicts():
    """Загружает словари из CSV в DICTS (кеш)"""
    global DICTS
    if DICTS:
        return  # Если словари уже загружены, не перезагружаем

    for filename in os.listdir(DICT_DIR):
        if filename.endswith('.csv'):
            dict_name = filename.replace('.csv', '')
            dict_path = os.path.join(DICT_DIR, filename)

            try:
                if dict_name == 'narusheniya':
                    df = pd.read_csv(dict_path, sep=',', dtype={'id': int, 'narushenie': str})
                    DICTS[dict_name] = df.set_index('id')['narushenie'].to_dict()
                elif dict_name == 'mo':
                    df = pd.read_csv(dict_path, sep=',', dtype={'id': int, 'mo': str})
                    DICTS[dict_name] = df.set_index('id')['mo'].to_dict()
                elif dict_name == 'ndu':
                    df = pd.read_csv(dict_path, sep=',', dtype={'id': int, 'ndu': str})
                    DICTS[dict_name] = df.set_index('id')['ndu'].to_dict()
                elif dict_name == 'osveshenie':
                    df = pd.read_csv(dict_path, sep=',', dtype={'id': int, 'osveshenie': str})
                    DICTS[dict_name] = df.set_index('id')['osveshenie'].to_dict()
                elif dict_name == 'sost_pogodi':
                    df = pd.read_csv(dict_path, sep=',', dtype={'id': int, 'sost_pogodi': str})
                    DICTS[dict_name] = df.set_index('id')['sost_pogodi'].to_dict()
                elif dict_name == 'sost_proez_chasti':
                    df = pd.read_csv(dict_path, sep=',', dtype={'id': int, 'sost_proez_chasti': str})
                    DICTS[dict_name] = df.set_index('id')['sost_proez_chasti'].to_dict()
                elif dict_name == 'vid_dtp':
                    df = pd.read_csv(dict_path, sep=',', dtype={'id': int, 'vid_dtp': str})
                    DICTS[dict_name] = df.set_index('id')['vid_dtp'].to_dict()
                elif dict_name == 'sdor':
                    df = pd.read_csv(dict_path, sep=',', dtype={'id': int, 'sdor': str})
                    DICTS[dict_name] = df.set_index('id')['sdor'].to_dict()

                else:
                    df = pd.read_csv(dict_path, sep='$', names=['id', 'name'], dtype={'id': int, 'name': str})
                    DICTS[dict_name] = df.set_index('id')['name'].to_dict()

                print(f"✅ Загружен: {dict_name} ({len(DICTS[dict_name])} записей)")

            except Exception as e:
                print(f"❌ Ошибка загрузки {dict_name}: {e}")


# ✅ Вспомогательная функция для замены ID на значения
def map_value(value, dict_name):
    """Заменяет ID на значения из словаря, поддерживает массивы"""
    if isinstance(value, list):
        return [DICTS.get(dict_name, {}).get(int(v), f"Unknown {v}") for v in value]
    return DICTS.get(dict_name, {}).get(int(value), f"Unknown {value}")


# ✅ Вспомогательная функция для загрузки и фильтрации данных
def load_and_filter_dtp(year=None, mo=None, vid_dtp=None):
    """Загружает данные ДТП с фильтрацией"""
    try:
        df = pd.read_csv(DATA_FILE)

        # Преобразование даты в формат dd.mm.yyyy и извлечение года
        df['year'] = pd.to_datetime(df['date_dtp'], dayfirst=True).dt.year

        # Фильтрация
        if year:
            df = df[df['year'] == int(year)]
        if mo:
            df = df[df['mo'] == int(mo)]
        if vid_dtp:
            df = df[df['vid_dtp'] == int(vid_dtp)]

        return df[['id_kard', 'death', 'year', 'mo', 'vid_dtp', 'coord_w', 'coord_l']].to_dict(orient='records')

    except Exception as e:
        return {"error": str(e)}


# ✅ Маршрут с фильтрацией
@dtp_bp.route('/dtp/coord', methods=['GET'])
def get_dtp_coord():
    """Возвращает данные ДТП с фильтрацией по year, mo, vid_dtp"""
    year = request.args.get('year')
    mo = request.args.get('mo')
    vid_dtp = request.args.get('vid_dtp')

    data = load_and_filter_dtp(year, mo, vid_dtp)
    return jsonify(data)


# ✅ Функция для обработки карточки ДТП
def get_card_by_id(id_kard):
    """Загружает карточку ДТП по id_kard и преобразует в нужную структуру"""
    try:
        load_dicts()

        df = pd.read_csv(DATA_FILE)
        card = df[df['id_kard'] == int(id_kard)].to_dict(orient='records')

        if not card:
            return {"error": "ДТП с указанным id_kard не найдено"}

        card = card[0]  # Берём первую запись

        # ✅ Замена ID в основных полях
        fields_to_replace = ['mo', 'vid_dtp', 'ndu', 'sost_pogodi', 'sost_proez_chasti', 'osveshenie', 'sdor']

        for field in fields_to_replace:
            if field in card and pd.notna(card[field]):
                card[field] = map_value(card[field], field)

        # ✅ Обработка вины (нарушений)
        vina_raw = card.get('vina', '[]')

        if isinstance(vina_raw, float) and np.isnan(vina_raw):
            vina_raw = '[]'

        if vina_raw.startswith('"') and vina_raw.endswith('"'):
            vina_raw = vina_raw[1:-1]

        vina_fixed = vina_raw.replace('nan', 'None')
        vina_fixed = re.sub(r'\((.*?)\)', r'[\1]', vina_fixed)

        try:
            vina_list = ast.literal_eval(vina_fixed)
        except (SyntaxError, ValueError):
            vina_list = []

        # Форматирование нарушений, погибших и раненых
        vina_formatted = []
        pogibshie = 0
        ranenie = 0

        for item in vina_list:
            if not isinstance(item, dict) or item.get('type') in [None, 'nan']:
                continue

            type_name = item.get('type', 'N/A')
            type_key = TYPE_MAP.get(type_name, 'unknown')

            ts_value = item.get('number_ts', 'N/A')

            participant = {
                "type": {
                    "title": "Участник",
                    "value": type_name
                },
                "ts": {
                    "title": "Транспортное средство",
                    "value": ts_value
                },
                "narushenie": {
                    "title": "Нарушения",
                    "value": map_value(item.get('narushenie', []), 'narusheniya')
                },
                "stepen_tyazhesti": {
                    "title": "Степень тяжести",
                    "value": item.get('stepen_tyazhesti', 'N/A')
                }
            }

            vina_formatted.append({
                "uch": {
                    "title": "Участник ДТП",
                    "value": participant
                }
            })

            # Подсчёт погибших и раненых
            stepen_tyazhesti = item.get('stepen_tyazhesti', 'N/A')
            if stepen_tyazhesti in ['Погиб', 'Смерть']:
                pogibshie += 1
            elif stepen_tyazhesti in ['Ранен', 'Травма']:
                ranenie += 1

        # ✅ Формирование ответа
        result = {
            "id_kard": {"title": "Номер ДТП", "value": card['id_kard']},
            "address": {"title": "Адрес", "value": card['address']},
            "date_dtp": {"title": "Дата ДТП", "value": card['date_dtp']},
            "vid_dtp": {"title": "Вид ДТП", "value": card['vid_dtp']},
            "uds": {"title": "Проблемы УДС (перегон)", "value": card['sdor']},
            "ndu": {"title": "Проблемы УДС (перегон)", "value": card['ndu']},
            "mo": {"title": "Муниципальный округ", "value": card['mo']},
            "sost_pogodi": {"title": "Погода", "value": card['sost_pogodi']},
            "sost_proez_chasti": {"title": "Покрытие", "value": card['sost_proez_chasti']},
            "osveshenie": {"title": "Время суток", "value": card['osveshenie']},
            "vina": {
                "title": "Нарушения",
                "value": vina_formatted
            },
            "pogibshie": {
                "title": "Погибшие",
                "value": pogibshie
            },
            "ranenie": {
                "title": "Раненые",
                "value": ranenie
            }
        }

        return result

    except Exception as e:
        return {"error": str(e)}



# ✅ Маршрут для получения карточки
@dtp_bp.route('/dtp/card/<int:id_kard>', methods=['GET'])
def get_dtp_card(id_kard):
    """Возвращает карточку ДТП"""
    data = get_card_by_id(id_kard)
    return jsonify(data)
