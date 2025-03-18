import pandas as pd
import config.config as config

# Пути к файлам
file_c_t_path_input = config.FILE_TRAFFIC_CAMERAS_PATH_INPUT
file_c_t_path_output = config.FILE_TRAFFIC_CAMERAS_PATH_OUTPUT

file_uchrez_path_input = config.FILE_UCHREZ_PATH_INPUT
file_uchrez_path_output = config.FILE_UCHREZ_PATH_OUTPUT

# Словари для маппинга
columns_mapping_c_s = {
    'coord_w': 'coord_w',
    'coord_l': 'coord_l',
    'type_data': 'type_data',
    'metka_mo': 'metka_mo',
}

columns_mapping_uchrez = {
    'ndu': 'type_uchrez',
    'coord_w': 'coord_w',
    'coord_l': 'coord_l',
    'type_data': 'type_data',
}

# Загрузка данных
df_c_s = pd.read_csv(file_c_t_path_input, usecols=columns_mapping_c_s.keys())
df_c_s.rename(columns=columns_mapping_c_s, inplace=True)

df_uchrez = pd.read_csv(file_uchrez_path_input, usecols=columns_mapping_uchrez.keys())
df_uchrez.rename(columns=columns_mapping_uchrez, inplace=True)

# Функция для классификации типов учреждений
def classify_uchrez_type(name):
    name = str(name).lower()

    # Принадлежность к школе
    if any(sub in name for sub in ['школа', 'гимназия', 'лицей', 'интернат']):
        return 2 # 'Школа'

    # Учреждения СПО
    if any(sub in name for sub in ['колледж', 'техникум', 'профессионального', 'училище']):
        return 3 # 'СПО'

    # Детский сад
    if 'сад' in name and 'школа' not in name:
        return 1 # 'Детский сад'

    # Школа-детский сад — к школе
    if 'школа' in name and 'сад' in name:
        return 2 # 'Школа'

    return 0 # 'Неопределено'

# Применение классификации
df_uchrez['type_uchrez'] = df_uchrez['type_uchrez'].apply(classify_uchrez_type)

# Сохранение данных
df_c_s.to_csv(file_c_t_path_output, index=False)
df_uchrez.to_csv(file_uchrez_path_output, index=False)

def start():
    print("Модуль успешно загружен!")
