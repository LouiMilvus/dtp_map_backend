import pandas as pd
import ast
import json
import os

# ✅ Функция для безопасного парсинга vina
def safe_parse_vina(vina):
    """Безопасный парсер для поля vina"""
    if pd.isna(vina) or vina in ["[]", "", "nan", "null"]:
        return []

    # Попытка преобразования кортежей в JSON-совместимый формат
    vina_cleaned = vina.replace("(", "[").replace(")", "]").replace("'", '"')

    try:
        return json.loads(vina_cleaned)
    except json.JSONDecodeError:
        try:
            # Если JSON не сработал, используем ast.literal_eval
            return ast.literal_eval(vina)
        except (ValueError, SyntaxError) as e:
            print(f"⚠️ Ошибка парсинга: {vina} → {e}")
            return []

# ✅ Функция для парсинга нарушений
def parse_narusheniya(vina, narusheniya_dict):
    """Парсинг строки vina в список нарушений"""
    vina_list = safe_parse_vina(vina)
    result = []

    for item in vina_list:
        if not isinstance(item, dict):
            continue  # Пропуск некорректных данных

        type_uchastnik = item.get('type', 'Неизвестно')
        narushenie_ids = item.get('narushenie', [])

        # Обработка нарушений в виде кортежей, преобразование в список
        if isinstance(narushenie_ids, tuple):
            narushenie_ids = list(narushenie_ids)

        narushenie_names = [narusheniya_dict.get(n, f"Неизвестно ({n})") for n in narushenie_ids]

        result.append({
            'type': type_uchastnik,
            'narusheniya': narushenie_names
        })

    return result

# ✅ Функция для загрузки справочников
def load_dict(file_path):
    """Загружает справочник в словарь {id: значение}"""
    df = pd.read_csv(file_path)

    # Определение названия столбца со значениями по имени файла
    file_name = os.path.basename(file_path).split('.')[0]  # например, mo, vid_dtp
    value_column = file_name if file_name in df.columns else df.columns[1]  # резервная проверка

    return dict(zip(df['id'], df[value_column]))

# ✅ Пути к файлам
base_path = '/opt/dtp_map_backend/data/'
dict_path = f"{base_path}dict/"
dtp_file = f"{base_path}dtp/output/output.csv"

# ✅ Загрузка справочников
mo_dict = load_dict(f"{dict_path}mo.csv")
vid_dtp_dict = load_dict(f"{dict_path}vid_dtp.csv")
sost_pogodi_dict = load_dict(f"{dict_path}sost_pogodi.csv")
sost_proez_chasti_dict = load_dict(f"{dict_path}sost_proez_chasti.csv")
osveshenie_dict = load_dict(f"{dict_path}osveshenie.csv")
ndu_dict = load_dict(f"{dict_path}ndu.csv")
narusheniya_dict = load_dict(f"{dict_path}narusheniya.csv")

# ✅ Загрузка данных ДТП
dtp_df = pd.read_csv(dtp_file)

# Проверка названий столбцов
print("🛠️ Столбцы после нормализации:")
print(dtp_df.columns)

# ✅ Преобразование данных
result = []

for _, row in dtp_df.iterrows():
    # Обработка значений для защиты от NaN
    def safe_value(value, default="Неизвестно"):
        return default if pd.isna(value) else value

    obj = {
        "id_kard": safe_value(row.get("id_kard")),
        "date": safe_value(row.get("date_dtp")),
        "mo": {
            "id": safe_value(row.get("mo")),
            "name": mo_dict.get(row.get("mo"), "Неизвестно")
        },
        "vid_dtp": {
            "id": safe_value(row.get("vid_dtp")),
            "name": vid_dtp_dict.get(row.get("vid_dtp"), "Неизвестно")
        },
        "ndu": {
            "id": safe_value(row.get("ndu")),
            "name": ndu_dict.get(row.get("ndu"), "Неизвестно")
        },
        "address": safe_value(row.get("address")),
        "pogibshie": safe_value(row.get("pogibshie"), 0),
        "ranenie": safe_value(row.get("ranenie"), 0),
        "sost_pogodi": {
            "id": safe_value(row.get("sost_pogodi")),
            "name": sost_pogodi_dict.get(row.get("sost_pogodi"), "Неизвестно")
        },
        "sost_proez_chasti": {
            "id": safe_value(row.get("sost_proez_chasti")),
            "name": sost_proez_chasti_dict.get(row.get("sost_proez_chasti"), "Неизвестно")
        },
        "osveshenie": {
            "id": safe_value(row.get("osveshenie")),
            "name": osveshenie_dict.get(row.get("osveshenie"), "Неизвестно")
        },
        "narusheniya": parse_narusheniya(row.get("vina"), narusheniya_dict)
    }
    result.append(obj)

# ✅ Сохранение в JSON
output_file = f"{base_path}dtp/output/result.json"
with open(output_file, "w", encoding="utf-8") as f:
    json.dump(result, f, ensure_ascii=False, indent=4)

print(f"✅ Данные успешно сохранены в {output_file}")
