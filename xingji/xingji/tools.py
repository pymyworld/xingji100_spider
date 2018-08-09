# 爬虫自定义工具集
import time
import datetime
import hashlib
import random
import os
import requests
import json
import logging
import re
from .settings import *


# 全民排除分类列表，若游戏分类下的房间列表url中存在以下元素，排除该分类
exclude_url_list = [
            "//s.quanmin.tv",
            "//www.quanmin.tv/game/showing",
            "//www.quanmin.tv/game/chihewanle",
            "//www.quanmin.tv/game/erciyuan",
            "//www.quanmin.tv/game/quanminchupin",
            "//www.quanmin.tv/game/street",
            "//www.quanmin.tv/game/renwen",
            "//www.quanmin.tv/game/huanxiangquanmingxing",
            "//www.quanmin.tv/game/huwai?maintain",
            "//www.quanmin.tv/game/qiche",
            "//www.quanmin.tv/game/keji",
            "//www.quanmin.tv/game/mengchongleyuan",
            "//www.quanmin.tv/game/kb",
        ]
# 全民排除分类列表，排除以下分类
exclude_game_list = [
            "全民星秀",
            "Showing",
            "吃喝玩乐",
            "二次元区",
            "全民出品",
            "街头文化",
            "人文",
            "幻想全明星",
            "全民户外",
            "汽车",
            "科技",
            "萌宠乐园",
            "看吧",
        ]

headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/54.0.2840.99 Safari/537.36"}


def longzhu_header():
    gmt_format = "%a, %d %b %Y %H:%M:%S GMT"
    gmt_str = datetime.datetime.utcnow().strftime(gmt_format)
    longzhu_headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/54.0.2840.99 Safari/537.36",
        "If-Modified-Since": gmt_str,
        "Host": "roomapicdn.longzhu.com",
    }
    return longzhu_headers


def make_gmt():
    '''生成格林尼治标准时间'''
    gmt_format = "%a, %d %b %Y %H:%M:%S GMT"
    gmt_str = datetime.datetime.utcnow().strftime(gmt_format)
    return gmt_str


def quanmin_url_exclude(room_href):
    '''
    排除全民非游戏分类的房间列表
    :param room_href:
    :return:
    '''
    for exclude in exclude_url_list:
        if room_href != exclude:
            return room_href
        else:
            return None


def quanmin_game_exclude(game):
    '''
    排除获取到的非游戏分类
    :param game:
    :return:
    '''
    for game_exc in exclude_game_list:
        if game != game_exc:
            return game
        else:
            return None


def time_str():
    '''
    生成时间戳
    :return:
    '''
    times = int(time.time())
    time_local = time.localtime(times)
    date = time.strftime("%Y-%m-%d %H:%M:%S", time_local)
    return date


def get_avatar(avatar_url, platform_name):
    '''
    将下载的头像保存在www/static/upload/tv/下,每个平台对应一个目录
    :return:返回图片在项目中所在路径,用于存储数据库
    '''
    root_path = os.path.abspath(os.path.join(os.getcwd(), '../../../'))
    postfix = '.jpg'
    file_path = avatar_path
    file_name = md5_handle(avatar_url)
    file_platform = "/{}/".format(platform_name)
    if file_name is None:
        return ""
    else:
        file = root_path + "/www" + file_path + file_platform + file_name + postfix
        if not os.path.exists(root_path + "/www" + file_path + file_platform):
            os.makedirs(root_path + "/www" + file_path + file_platform)
        with open(file, 'wb') as f:
            response = requests.get(avatar_url, stream=True)
            for block in response.iter_content(1024):
                if not block:
                    break
                f.write(block)
        return file_path + file_platform + file_name + postfix


def md5_handle(avatar_url):
    '''
    将头像图片url通过md5加密作为图片名
    :return:
    '''
    if avatar_url is not None:
        m = hashlib.md5()
        m.update(avatar_url.encode())
        return m.hexdigest()


def generate_sign():
    '''蚂蚁代理加密请求头'''
    paramMap = {
        "app_key": APPKEY,
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
    }
    keys = sorted(paramMap)
    codes = "%s%s%s" % (MAYI_SECRET, str().join('%s%s' % (key, paramMap[key]) for key in keys), MAYI_SECRET)
    sign = hashlib.md5(codes.encode('utf-8')).hexdigest().upper()
    paramMap["sign"] = sign
    keys = paramMap.keys()
    authHeader = "MYH-AUTH-MD5 " + str('&').join('%s=%s' % (key, paramMap[key]) for key in keys)
    mayi_headers = {
        "Proxy-Authorization": authHeader,
        "User-Agent": random.choice(USER_AGENT)
    }
    return mayi_headers


def deal_status(response):
    '''处理4xx状态码'''
    if response.status == 400 or response.status == 403 or response.status == 404 or response.status == 587 or response.status == 588 or response.status == 589:
        logging.error("time:{},status:{},url:{}".format(time_str(), response.status, response.url))
        return True


