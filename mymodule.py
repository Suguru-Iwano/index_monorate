#!/usr/bin/env python3
import os
import sys
import json
import time
import requests # pip3 install requests

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

# Slackに出力
class SlackAPI(object):

    def __init__(self, inifile_name):
        # 設定ファイル読み込み
        sample_json = {'URL': {'webhook_url': None}}
        config_json = get_config_json(inifile_name, sample_json)
        self.webhook_url = config_json['URL']['webhook_url']

    def write_log(self, message):

        if isinstance(message, dict):
            message = json.dumps(message,indent=4,ensure_ascii=False)
        if isinstance(message, list):
            message = [json.dumps(m,indent=4,ensure_ascii=False) for m in message]
        print(message)

        okflg = False
        while not okflg:
            try:
                requests.post(self.webhook_url, data=json.dumps({'text': message}))
            except:
                time.sleep(5)
            else:
                okflg = True
