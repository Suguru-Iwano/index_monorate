#!/usr/bin/env python3
from mymodule import get_config_json as get_conf

from pymongo import MongoClient # pip3 install pymongo


class MongoAccess(object):
    inifile_name = './config/mongo.ini'

    # コンストラクタ
    def __init__(self):
        # iniファイル読み込み
        sample_json = {
            'CONFIG': {
                'DB'  : None,
                'COLLECTION' : None,
                'USER' : None,
                'PASS' : None
            }
        }
        # get_conf:　iniファイル名とJSONの雛形から
        #               iniファイルの中身が入ったJSONを作成
        CONFIG = get_conf(self.inifile_name, sample_json)['CONFIG']

        client = MongoClient(username = CONFIG['USER'], password = CONFIG['PASS'])
        self.db = client[CONFIG['DB']]
        self.collection = self.db.get_collection(CONFIG['COLLECTION'])

    # findするぜ！
    def find(self):
        pass

    # upsertするぜ！
    def upsert_one(self, post):
        self.db.amz.update_one({'ASIN':post['ASIN']}, {'$set':post}, True)
