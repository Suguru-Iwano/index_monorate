#!/usr/bin/env python3
from bs4 import BeautifulSoup # pip3 install bs4
from selenium import webdriver # pip3 install selenium
#from selenium.webdriver.chrome.options import Options # 同上
from selenium.webdriver import Firefox, FirefoxOptions
#from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
#import chromedriver_binary # pip3 install chromedriver_binary
from urllib import request, parse # 組み込み
import requests # pip3 install requests
from pymongo import MongoClient # pip3 install pymongo
import json # 組み込み
import subprocess # 組み込み
import time # 組み込み
import random # 組み込み
import datetime # 組み込み
import collections as cl
import traceback
import os

version = 'index_monorate(NoDocker)_2.4'

#Slackに出力
def print_slack(message):
    webhook_url = 'https://hooks.slack.com/services/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'
    if isinstance(message, dict):
        message = json.dumps(message,indent=4,ensure_ascii=False)
    if isinstance(message, list):
        message = [json.dumps(m,indent=4,ensure_ascii=False) for m in message]
    requests.post(webhook_url, data=json.dumps({'text': message}))


class MongoAccess(object):

    def __init__(self):
        self.clint = MongoClient()
        self.db = self.clint['amz']

    def upsert_one(self, post):
        self.db.amz.update_one({'ASIN':post['ASIN']}, {'$set':post}, True)

# ブラウザを起動
def create_driver(driver):
    if driver is not None:
        try:
            driver.quit()
        except:
            print('Exception at driver.quit()')
        driver = None

    # Chromedriver用
    # options = webdriver.ChromeOptions()
    # options.add_argument('--headless')
    # driver = webdriver.Chrome(options=options)

    # Firefox用
    options = FirefoxOptions()
    options.add_argument('-headless')
    driver = Firefox(options=options, log_path=os.path.devnull)

    # Docker用
    # driver = webdriver.Remote(
    # command_executor='http://selenium-hub:4444/wd/hub',
    # desired_capabilities=DesiredCapabilities.CHROME)
    print_slack('> driver is started')
    return driver

# 検索URLを生成
def make_url_forsearch(base_url, category, rank_range, page_num):
    # URLのパラメータ群
    query = {
        'i':     category,
        'kwd':   '',
        'r_min': rank_range['min'],
        'r_max': rank_range['max'],
        's':     's',
        'p':     page_num
    }
    url = ''
    # ?以降のURLを生成
    params = parse.urlencode(query)
    url = base_url + '?' + params
    return url

# HTMLを取得
def get_html_forsoup(url, driver=None):
    html = None
    res_is_None = True
    try:
        if driver is None:
            html = requests.get(url)
        else:
            driver.get(url)
            html = driver.page_source.encode('utf-8')
        res_is_None = False
    except:
        res_is_None = True
        print_slack('> none ress sleep')
        print_slack(traceback.format_exc())
        time.sleep(random.random()*4000)
        #time.sleep(2)

    return html, res_is_None


# 文字列をISOに変換
def encode_iso(str_date):
    try:
        return datetime.datetime.fromisoformat(str_date)
    except:
        return None


# HTMLを解析
def analyze_html(html):

    soup_all = BeautifulSoup(html, 'html.parser', from_encoding='utf-8')
    # 次へボタン検索用
    str_search_nextpage = "span[class='paging_next'] > a[class='original_link']"
    # 次ページのリンクの有無を判定
    nextpage_is_exist = False if (soup_all.select(str_search_nextpage)) == [] else True

    res_is_403 = False
    # 商品データに整形
    # 1ページ内商品情報のリスト検索
    soup_1page_list = soup_all.select("section[class='search_item_list_section']")

    # 403用
    if soup_all.title.string == '403 Forbidden':
        res_is_403 = True
        print_slack('> 403 sleep')
        time.sleep(random.random()*4000)
    # if len(soup_1page_list) == 0:
    #     res_is_403 = True
    #     print_slack('> 403 sleep')
    #     time.sleep(random.random()*4000)
        #time.sleep(2)

    # ページ内の商品情報でループ
    item_infos = []
    for section in soup_1page_list:
        # １商品を検索
        soup_1iteminfo = section.select_one("ul[class='search_item_list']")
        soup_image = soup_1iteminfo.select_one("img[class='item_imgs']")
        soup_title = soup_1iteminfo.select_one("span[class='item_title'] > a[class='original_link']")
        # 注意書きは複数あるからループで作っておく
        soup_caution_list = soup_1iteminfo.select("span[class='product_caution']")
        caution_list = []
        for soup_caution in soup_caution_list:
            caution_text = soup_caution.select_one("span").string
            caution_list.append(caution_text)
        # 注意書きの処理ここまで
        soup_releasedate = soup_1iteminfo.select_one("div > span[class='item_date']")
        soup_category = soup_1iteminfo.select_one("span[class='data_category']")
        soup_rank = soup_1iteminfo.select_one("span[class='_ranking_item_color']")

        soup_reference_price = soup_1iteminfo.select_one("span[class='_reference_price_color price']")
        ReferencePrise=0
        try:
            ReferencePrise = int(soup_reference_price.string.replace('￥','').replace(',', '').strip()) if (soup_reference_price is not None) else None
        except:
            ReferencePrise = None

        str_release_date = soup_releasedate.string.replace('発売','').strip() if (soup_releasedate is not None) else ''
        iso_release_date = encode_iso(str_release_date)

        # ASIN CautionList Rank
        item_info = {
            'ASIN' : soup_title['href'].split('/')[-1] if (soup_title['href'] is not None) else None,
            'Monorate': {
                'Title'    : soup_title.string.strip() if (soup_title is not None) else None,
                'URL'    : soup_title['href'],
                'ImageURL'   : soup_image['src'].strip() if (soup_image['src'] is not None) else None,
                'CautionList' : caution_list,
                'ReleaseDate' : iso_release_date,
                'ProductGroup' : soup_category.string.strip() if (soup_category is not None) else None,
                'Rank'     : int(soup_rank.string.strip().replace(',', '')) if (soup_rank is not None) else None,
                'ReferencePrise': ReferencePrise,
                'AcquisitionDate'  : datetime.datetime.today()
            }
        }
        print(item_info)
        item_infos.append(item_info)

    return item_infos, nextpage_is_exist, res_is_403

#CPU温度計測
# def get_cpu_temp():
#     command = 'vcgencmd measure_temp'
#     result = subprocess.Popen(command, shell=True,  stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True)
#     rstdout ,rstderr = result.communicate()
#     cpu_temp = rstdout.split()
#     return cpu_temp[0]

#ファイルを一時領域からHDDに移動
# def move_file(filepath, filename):
#     pre_json_directory = filepath
#     aft_json_directory = '/root/script/results/'
#     cmd1 = f'mv -f {pre_json_directory}{filename} {aft_json_directory}{filename}'
#     subprocess.call(cmd1.split())

# main
def main():
    base_url = 'https://mnrate.com/search'

    # 全部
    #item_categories = ['Books', 'ForeignBooks', 'DVD', 'Music', 'MusicalInstruments', 'VideoGames', 'Electronics', 'PCHardware', 'Software', 'OfficeProducts', 'Kitchen', 'PetSupplies', 'Grocery', 'HealthPersonalCare', 'Beauty', 'Baby', 'Toys', 'Hobbies', 'Apparel', 'Shoes', 'Jewelry', 'Watches', 'SportingGoods', 'HomeImprovement', 'Automotive', 'Appliances']
    # 規制少ない
    #item_categories = ['MusicalInstruments', 'VideoGames', 'Electronics', 'PCHardware', 'Software', 'OfficeProducts', 'PetSupplies', 'Toys', 'Hobbies', 'Apparel', 'SportingGoods', 'HomeImprovement', 'Automotive', 'Appliances']
    # 規制多い
    #item_categories = ['Books', 'ForeignBooks', 'DVD', 'Music', 'Kitchen', 'Grocery', 'HealthPersonalCare', 'Beauty', 'Baby', 'Shoes', 'Jewelry', 'Watches']
    # 今回
    item_categories = ['VideoGames', 'Electronics', 'PCHardware', 'Software', 'OfficeProducts', 'PetSupplies', 'Toys', 'Hobbies', 'Apparel', 'SportingGoods', 'HomeImprovement', 'Automotive', 'Appliances']
    max_rank_num = 80000
    #rank_roop_num = 200
    rank_roop_num = 40
    driver = None
    # chromedriver は、途中終了でプロセスが残ってしまうため

    try:
        driver = create_driver(driver)
        mongo = MongoAccess()

        for category in item_categories:
            rank_range = {
                'min': 1,
                'max': rank_roop_num
            }
            for h in range(int(max_rank_num/rank_roop_num)):
            #for h in range(max_rank_num):
                # 1から999ページまで(次へボタンがあるかぎり)ループ
                item_info_list = []
                for count_num in range(1,1000):
                    nextpage_is_exist = False

                    url = make_url_forsearch(base_url, category, rank_range, count_num)
                    res_is_403 = True
                    while res_is_403:
                        res_is_None = True
                        while res_is_None:
                            html, res_is_None = get_html_forsoup(url, driver)
                            # dockerだとエラーになるよ！
                            if res_is_None:
                                driver = create_driver(driver)
                        item_infos, nextpage_is_exist, res_is_403 = analyze_html(html)
                    [item_info_list.append(ii) for ii in item_infos]
                    # Bot認識阻害?
                    time.sleep((random.random())/2+1)
                    if not nextpage_is_exist:
                        break
                # ファイル保存（今回はMongoDB使う）
                #filepath = '/dev/shm/'
                # filepath = './result/'
                # filename = f'{category}_{h}.json'
                # with open(f'{filepath}{filename}','w', encoding = 'utf_8') as file:
                #     [json.dump(ii,file,indent=4,ensure_ascii=False) for ii in item_info_list]
                [mongo.upsert_one(ii) for ii in item_info_list]

                rank_range['min'] = rank_range['max']+1 #前回のminと被らないように+1する
                rank_range['max'] += rank_roop_num
                print_slack(f'【{category}】:{h}/{int(max_rank_num/rank_roop_num)}')
                #move_file(filepath, filename)
        print_slack('> all done!!')

    except Exception as e:
        print_slack(traceback.format_exc())

    finally:
        # ブラウザーを終了
        if driver is not None:
            driver.quit()


if __name__ == '__main__':
    main()
