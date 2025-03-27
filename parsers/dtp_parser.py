import pandas as pd
import config.config as config

file_dtp_path_input = config.FILE_DTP_PATH_INPUT
file_dtp_path_output = config.FILE_DTP_PATH_OUTPUT

narusheniya_dict_path_output = config.FILE_PATH_NARUSHENIYA
mo_dict_path_output = config.FILE_PATH_MO
ndu_dict_path_output = config.FILE_PATH_NDU
sdor_dict_path_output = config.FILE_PATH_SDOR
vid_dtp_dict_path_output = config.FILE_PATH_VID_DTP
sost_pogodi_dict_path_output = config.FILE_PATH_SOST_POGODI
sost_proez_chasti_dict_path_output = config.FILE_PATH_SOST_PROEZ_CHASTI
osveshenie_dict_path_output = config.FILE_PATH_OSVESHENIE



def create_address(row):
    parts = []
    if pd.notna(row['nas_punkt']):
        parts.append(str(row['nas_punkt']))
    if pd.notna(row['street']):
        parts.append(str(row['street']))
    if pd.notna(row['number_house']):
        parts.append(str(row['number_house']))

    address = ' '.join(parts)

    if pd.notna(row['doroga']):
        road_parts = [str(row['doroga'])]
        if pd.notna(row['km']):
            road_parts.append(f"{row['km']} км")
        if pd.notna(row['m']):
            road_parts.append(f"{row['m']} м")
        road_info = ' '.join(road_parts)

        if address:
            address = f"{address} ({road_info})"
        else:
            address = road_info

    return address


# Создание объекта вины (участников)
def create_vina(row):
    def combine_narushenie(main, dop):
        violations = set()
        for source in (main, dop):
            if isinstance(source, str):
                violations.update(v.strip() for v in source.split('|') if v.strip())
            elif isinstance(source, list):
                violations.update(source)
            elif pd.notna(source):
                violations.add(source)

        # Конвертируем в ID
        return [narusheniya_dict.get(v, v) for v in violations if v in narusheniya_dict]

    vina_list = [
        {
            'type': row['kat_uch_passazhir'],
            'stepen_tyazhesti': row['stepen_tyazhesti_passazhir'],
            'narushenie': tuple(combine_narushenie(row['narushenie_pdd_passazhir'], row['soput_narush_pdd_passazhir'])),
            'number_ts': row['number_ts'],
            'number': row['number_uch_passazhir']
        },
        {
            'type': row['kat_uch_peshehoda'],
            'stepen_tyazhesti': row['stepen_tyazhesti_peshehod'],
            'narushenie': tuple(combine_narushenie(row['narushenie_pdd_peshehod'], row['soput_narush_pdd_peshehod'])),
            'number': row['number_uch_peshehod']
        }
    ]
    return [v for v in vina_list if any(v.values())]

def replace_severity(value):
    if pd.isna(value):
        return value
    if 'Скончался' in value:
        return 'Погиб'
    elif 'Получил' in value or 'Раненый' in value:
        return 'Ранен'
    return value


def extract_violations(series):
    violations = set()
    for value in series.dropna():
        violations.update(v.strip() for v in str(value).split('|') if v.strip())
    return violations

def map_violations_to_ids(value):
    if pd.isna(value):
        return []
    if isinstance(value, list):
        violations = value  # Если это уже список нарушений
    elif isinstance(value, str):
        violations = [v.strip() for v in value.split('|') if v.strip()]
    else:
        violations = []  # На всякий случай

    return [narusheniya_dict[v] for v in violations if v in narusheniya_dict]

columns_mapping = {
    'kartid': 'id_kard',
    'date_dtp': 'date_dtp',
    'mo': 'mo',
    'vid_dtp': 'vid_dtp',
    'ndu': 'ndu',
    'sdor': 'sdor',
    'pog': 'pogibshie',
    'run': 'ranenie',
    'k_ts': 'kol_ts',
    'k_uch': 'kol_uch',
    'emtp_number': 'number_dtp',
    'n_p': 'nas_punkt',
    'street': 'street',
    'house': 'number_house',
    'doroga': 'doroga',
    'km': 'km',
    'm': 'm',
    's_pog': 'sost_pogodi',
    's_pch': 'sost_proez_chasti',
    'osv': 'osveshenie',
    'coord_w': 'coord_w',
    'coord_l': 'coord_l',
    'n_ts': 'number_ts',
    'k_uch_pos': 'kat_uch_passazhir',
    's_t_pos': 'stepen_tyazhesti_passazhir',
    'npdd_pos': 'narushenie_pdd_passazhir',
    'sop_npdd_pos': 'soput_narush_pdd_passazhir',
    'n_uch_pos': 'number_uch_passazhir',
    'k_uch_pehehod': 'kat_uch_peshehoda',
    's_t_pehehod': 'stepen_tyazhesti_peshehod',
    'npdd_pehehod': 'narushenie_pdd_peshehod',
    'sop_npdd_pehehod': 'soput_narush_pdd_peshehod',
    'n_uch_pehehod': 'number_uch_peshehod'
}

df = pd.read_csv(file_dtp_path_input, usecols=columns_mapping.keys())
df.rename(columns=columns_mapping, inplace=True)

df['stepen_tyazhesti_passazhir'] = df['stepen_tyazhesti_passazhir'].apply(replace_severity)
df['stepen_tyazhesti_peshehod'] = df['stepen_tyazhesti_peshehod'].apply(replace_severity)

df['address'] = df.apply(create_address, axis=1)

all_violations = set()
for col in ['narushenie_pdd_passazhir', 'soput_narush_pdd_passazhir',
            'narushenie_pdd_peshehod', 'soput_narush_pdd_peshehod']:
    all_violations.update(extract_violations(df[col]))

df_narusheniya = pd.DataFrame({
    'id': range(1, len(all_violations) + 1),
    'narushenie': list(all_violations)
})

narusheniya_dict = dict(zip(df_narusheniya['narushenie'], df_narusheniya['id']))

df['vina'] = df.apply(create_vina, axis=1)

for col in ['narushenie_pdd_passazhir', 'soput_narush_pdd_passazhir',
            'narushenie_pdd_peshehod', 'soput_narush_pdd_peshehod']:
    df[col] = df[col].apply(map_violations_to_ids)

extra_fields = [
    'date_dtp', 'mo', 'vid_dtp','ndu','sdor', 'address', 'pogibshie', 'ranenie',
    'kol_ts', 'kol_uch', 'number_dtp', 'sost_pogodi', 'sost_proez_chasti',
    'osveshenie', 'coord_w', 'coord_l','narushenie_pdd_passazhir', 'soput_narush_pdd_passazhir',
            'narushenie_pdd_peshehod', 'soput_narush_pdd_peshehod'
]

agg_dict = {field: 'first' for field in extra_fields}
agg_dict['vina'] = lambda x: list(
    {tuple(sorted(v.items())): v for lst in x for v in lst}.values()
)


df_grouped = df.groupby('id_kard', as_index=False).agg(agg_dict)
df_grouped['death'] = df_grouped['pogibshie'] > 0

df_mo = pd.DataFrame({'id': range(1, len(df['mo'].unique()) + 1), 'mo': df['mo'].unique()})
df_ndu = pd.DataFrame({'id': range(1, len(df['ndu'].unique()) + 1), 'ndu': df['ndu'].unique()})
df_sdor = pd.DataFrame({'id': range(1, len(df['sdor'].unique()) + 1), 'sdor': df['sdor'].unique()})
df_vid_dtp = pd.DataFrame({'id': range(1, len(df['vid_dtp'].unique()) + 1), 'vid_dtp': df['vid_dtp'].unique()})
df_sost_pogodi = pd.DataFrame({'id': range(1, len(df['sost_pogodi'].unique()) + 1), 'sost_pogodi': df['sost_pogodi'].unique()})
df_sost_proez_chasti = pd.DataFrame({'id': range(1, len(df['sost_proez_chasti'].unique()) + 1), 'sost_proez_chasti': df['sost_proez_chasti'].unique()})
df_osveshenie = pd.DataFrame({'id': range(1, len(df['osveshenie'].unique()) + 1), 'osveshenie': df['osveshenie'].unique()})

df_grouped['mo'] = df_grouped['mo'].map(dict(zip(df_mo['mo'], df_mo['id'])))
df_grouped['ndu'] = df_grouped['ndu'].map(dict(zip(df_ndu['ndu'], df_ndu['id'])))
df_grouped['sdor'] = df_grouped['sdor'].map(dict(zip(df_sdor['sdor'], df_sdor['id'])))
df_grouped['vid_dtp'] = df_grouped['vid_dtp'].map(dict(zip(df_vid_dtp['vid_dtp'], df_vid_dtp['id'])))
df_grouped['sost_pogodi'] = df_grouped['sost_pogodi'].map(dict(zip(df_sost_pogodi['sost_pogodi'], df_sost_pogodi['id'])))
df_grouped['sost_proez_chasti'] = df_grouped['sost_proez_chasti'].map(dict(zip(df_sost_proez_chasti['sost_proez_chasti'], df_sost_proez_chasti['id'])))
df_grouped['osveshenie'] = df_grouped['osveshenie'].map(dict(zip(df_osveshenie['osveshenie'], df_osveshenie['id'])))

df_grouped.to_csv(file_dtp_path_output, index=False)

df_narusheniya.to_csv(narusheniya_dict_path_output, index=False)

df_mo.to_csv(mo_dict_path_output, index=False)
df_ndu.to_csv(ndu_dict_path_output, index=False)
df_sdor.to_csv(sdor_dict_path_output, index=False)
df_vid_dtp.to_csv(vid_dtp_dict_path_output, index=False)
df_sost_pogodi.to_csv(sost_pogodi_dict_path_output, index=False)
df_sost_proez_chasti.to_csv(sost_proez_chasti_dict_path_output, index=False)
df_osveshenie.to_csv(osveshenie_dict_path_output, index=False)

def start():
    print("Модуль успешно загружен!")