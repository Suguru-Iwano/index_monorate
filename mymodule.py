#!/usr/bin/env python3
import os
import sys

from configparser import SafeConfigParser, MissingSectionHeaderError # pip3 install ConfigParser

# iniファイルを読みこむ
def _create_config(file_name):
    file_path = os.path.abspath(file_name)
    config = SafeConfigParser()

    if os.path.exists(file_path):
        config.read(file_path, encoding='utf8')
    else:
        raise FileNotFoundError

    return config

# configとJSONの雛形から辞書作成
def get_config_json(filename, sample_json):
    config = None
    config_json = None

    try:
        config = _create_config(filename)
    except FileNotFoundError as e:
        print(f'{filename} が同階層に見つかりませんでした。')
        sys.exit(1)
    except MissingSectionHeaderError as e:
        print(f'{filename} の書式を見直してください。')
        sys.exit(1)

    try:
        config_json = {sec: {param: config[sec][param] for param in sample_json[sec]} \
            for sec in sample_json}
    except KeyError as e:
        print(f'{e} が {filename} 内に見つかりませんでした。')
        sys.exit(1)

    return config_json