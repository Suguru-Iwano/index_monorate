#!/usr/bin/env python3

# 検索条件を確認してね！！
# DB登録を消してるよ！！コメントアウト戻してね！！

from mymodule import get_config_json as get_conf
from mymodule import SlackAPI
import selsearch
import wrapmongo

from bs4 import BeautifulSoup  # pip3 install bs4
from urllib import request, parse  # 組み込み
import requests  # pip3 install requests
import json  # 組み込み
import subprocess  # 組み込み
import time  # 組み込み
import random  # 組み込み
import datetime  # 組み込み
import collections as cl
import traceback
import os

SCRAPE_VERSION = 'index_monorate(NoDocker)_2.5'
sa = SlackAPI('./config/slack.ini')
ss = selsearch.SeleniumSearch()
print('> driver is started')

# 辞書から値がNoneのキーを削除
# 今回は使わない（Noneの列は消さない！）


def deletedic_ifnone(dic):
    for k, v in dic.items():
        if v is None:
            del(dic[k])
    return dic


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


def get_html_forsoup(url, driver, target_selector):
    html = None
    res_is_None = True
    try:
        driver.get(url)
        # WebDriverWait(driver, 30).until(
        #     EC.presence_of_element_located((By.CSS_SELECTOR, target_selector))
        # )
        # Bot認識阻害?
        time.sleep((random.random()) / 2 + 1)
        html = driver.page_source.encode('utf-8')
        res_is_None = False
    except:
        res_is_None = True
        sa.write_log('> none ress sleep\n' + traceback.format_exc())
        time.sleep(random.random() * 4000)

    return html, res_is_None


# 文字列をISOに変換
def encode_iso(str_date):
    try:
        return datetime.datetime.fromisoformat(str_date)
    except:
        return None


# HTMLを解析
def analyze_html(html):

    item_infos = []
    nextpage_is_exist = False
    res_is_403 = False
    res_title_is_None = False

    soup_all = BeautifulSoup(html, 'html.parser', from_encoding='utf-8')
    # 次へボタン検索用
    str_search_nextpage = "span[class='paging_next'] > a[class='original_link']"
    # 次ページのリンクの有無を判定
    nextpage_is_exist = False if (soup_all.select(
        str_search_nextpage)) == [] else True

    # 商品データに整形
    # 1ページ内商品情報のリスト検索
    soup_1page_list = soup_all.select(
        "section[class='search_item_list_section']")

    # タイトルがない -> 多分、初手の検索結果が0けん
    # だからnextpage_is_exist = False
    if (soup_all.title is None):
        res_is_403 = False
        res_title_is_None = True
        nextpage_is_exist = False
        time.sleep(random.random() * 2)
        return item_infos, nextpage_is_exist, res_is_403, res_title_is_None

    # 403用
    if (soup_all.title.string == '403 Forbidden'):
        res_is_403 = True
        res_title_is_None = False
        nextpage_is_exist = True
        sa.write_log('> 403 sleep')
        time.sleep(random.random() * 4000)
        return item_infos, nextpage_is_exist, res_is_403, res_title_is_None

    # ページ内の商品情報でループ
    for section in soup_1page_list:
        # １商品を検索
        soup_1iteminfo = section.select_one("ul[class='search_item_list']")
        soup_image = soup_1iteminfo.select_one("img[class='item_imgs']")
        soup_title = soup_1iteminfo.select_one(
            "span[class='item_title'] > a[class='original_link']")
        # 注意書きは複数あるからループで作っておく
        soup_caution_list = soup_1iteminfo.select(
            "span[class='product_caution']")
        caution_list = []
        for soup_caution in soup_caution_list:
            caution_text = soup_caution.select_one("span").string
            caution_list.append(caution_text)
        # 注意書きの処理ここまで
        soup_releasedate = soup_1iteminfo.select_one(
            "div > span[class='item_date']")
        soup_category = soup_1iteminfo.select_one(
            "span[class='data_category']")
        soup_rank = soup_1iteminfo.select_one(
            "span[class='_ranking_item_color']")

        soup_reference_price = soup_1iteminfo.select_one(
            "span[class='_reference_price_color price']")
        ReferencePrise = 0
        try:
            ReferencePrise = int(soup_reference_price.string.replace('￥', '').replace(
                ',', '').strip()) if (soup_reference_price is not None) else None
        except:
            ReferencePrise = None

        str_release_date = soup_releasedate.string.replace(
            '発売', '').strip() if (soup_releasedate is not None) else ''
        iso_release_date = encode_iso(str_release_date)

        # ASIN CautionList Rank
        item_info = {
            'ASIN': soup_title['href'].split('/')[-1] if (soup_title['href'] is not None) else None,
            'Monorate': {
                'Title': soup_title.string.strip() if (soup_title is not None) else None,
                'URL': soup_title['href'],
                'ImageURL': soup_image['src'].strip() if (soup_image['src'] is not None) else None,
                'CautionList': caution_list,
                'ReleaseDate': iso_release_date,
                'ProductGroup': soup_category.string.strip() if (soup_category is not None) else None,
                'Rank': int(soup_rank.string.strip().replace(',', '')) if (soup_rank is not None) else None,
                'ReferencePrise': ReferencePrise,
                'AcquisitionDate': datetime.datetime.today()
            }
        }
        item_infos.append(item_info)

    return item_infos, nextpage_is_exist, res_is_403, res_title_is_None


def main():
    base_url = 'https://mnrate.com/search'

    # 全部
    #item_categories = ['Books', 'ForeignBooks', 'DVD', 'Music', 'MusicalInstruments', 'VideoGames', 'Electronics', 'PCHardware', 'Software', 'OfficeProducts', 'Kitchen', 'PetSupplies', 'Grocery', 'HealthPersonalCare', 'Beauty', 'Baby', 'Toys', 'Hobbies', 'Apparel', 'Shoes', 'Jewelry', 'Watches', 'SportingGoods', 'HomeImprovement', 'Automotive', 'Appliances']
    # 規制少ない
    #item_categories = ['MusicalInstruments', 'VideoGames', 'Electronics', 'PCHardware', 'Software', 'OfficeProducts', 'PetSupplies', 'Toys', 'Hobbies', 'Apparel', 'SportingGoods', 'HomeImprovement', 'Automotive', 'Appliances']
    # 規制多い
    #item_categories = ['Books', 'ForeignBooks', 'DVD', 'Music', 'Kitchen', 'Grocery', 'HealthPersonalCare', 'Beauty', 'Baby', 'Shoes', 'Jewelry', 'Watches']
    # 今回
    item_categories = ['Software', 'OfficeProducts', 'PetSupplies', 'Toys', 'Hobbies',
                       'Apparel', 'SportingGoods', 'HomeImprovement', 'Automotive', 'Appliances']
    max_rank_num = 80000
    #rank_roop_num = 200
    rank_roop_num = 40
    driver = None
    # chromedriver は、途中終了でプロセスが残ってしまうため

    try:
        driver = ss.get_driver()
        mongo = wrapmongo.MongoAccess()

        for category in item_categories:
            rank_range = {
                'min': 1,
                'max': rank_roop_num
            }
            for h in range(int(max_rank_num / rank_roop_num)):
                # for h in range(max_rank_num):
                # 1から999ページまで(次へボタンがあるかぎり)ループ
                item_info_list = []
                for count_num in range(1, 1000):
                    nextpage_is_exist = False

                    url = make_url_forsearch(
                        base_url, category, rank_range, count_num)
                    res_is_403 = True
                    res_title_is_None = False
                    while res_is_403 and not res_title_is_None:
                        res_is_None = True
                        while res_is_None:
                            html, res_is_None = get_html_forsoup(
                                url, driver, 'span.product_caution')
                            # dockerだとエラーになるよ！
                            if res_is_None:
                                driver = ss.recreate_driver()
                        item_infos, nextpage_is_exist, res_is_403, res_title_is_None = analyze_html(
                            html)
                    [mongo.upsert_one(ii) for ii in item_infos]

                    if not nextpage_is_exist:
                        break
                        
                rank_range['min'] = rank_range['max'] + 1  # 前回のminと被らないように+1する
                rank_range['max'] += rank_roop_num
                sa.write_log(
                    f'【{category}】:{h}/{int(max_rank_num/rank_roop_num)}')
        sa.write_log('> all done!!')

    except Exception as e:
        sa.write_log(traceback.format_exc())

    finally:
        # ブラウザーを終了
        if driver is not None:
            driver.quit()


if __name__ == '__main__':
    main()
