# -*- coding: utf-8 -*-
# 抓取xj_star表中主播的开关播时间，若开播的话抓取在线热度
import scrapy
import re
import os
import json
import time
import datetime
import logging
from ..sql_handle import Sqlhandle
from ..items import Xj_view_liveItem
from ..tools import deal_status
from ..tools import time_str
from ..tools import make_gmt
from ..tools import longzhu_header
from ..tools import generate_sign
from copy import deepcopy


class XjViewLiveSpider(scrapy.Spider):
    name = 'xj_view_live'
    custom_settings = {
        'ITEM_PIPELINES': {
            'xingji.pipelines.Xj_view_livePipeline': 100,
        }
    }
    start_urls = []
    longzhu_live_header = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/65.0.3325.181 Safari/537.36",
        "Host": "star.longzhu.com",
        "If-Modified-Since": make_gmt(),
        "Referer": "http://longzhu.com/channels/all",
        "Upgrade-Insecure-Requests": "1"
    }

    def __init__(self):
        super(XjViewLiveSpider, self).__init__()
        # 建立id与live_url的关系字典
        self.relation = dict()
        self.sql = Sqlhandle()
        self.now_time = datetime.datetime.now().strftime("%H:%M:%S")
        self.today = time.strftime('%Y-%m-%d', time.localtime(int(time.time())))
        self.yesterday = time.strftime('%Y-%m-%d', time.localtime(int(time.time()) - 86400))
        # 在每天0点删除昨日缓存文件
        if os.path.exists("cache_{}.json".format(self.yesterday)) is True:
            os.remove("cache_{}.json".format(self.yesterday))
            logging.error("spider:{} 已删除{}缓存文件".format(self.name, self.yesterday))
        try:
            with open("cache_{}.json".format(self.today), "r") as f:
                self.select_list = json.loads(f.read())
            logging.error("spider:{} 本次使用缓存文件".format(self.name))
        except Exception:
            self.select_list = self.sql.select_id_live_url()
            # 生成今日缓存文件
            with open("cache_{}.json".format(self.today), "w") as f:
                f.write(json.dumps(self.select_list))
            logging.error("spider:{} 已生成{}缓存文件".format(self.name, self.today))
        self.make_start_urls(self.select_list)

    def make_start_urls(self, select_list):
        '''
        向start_url中添加url,并建立关系
        :param select_list:
        :return:
        '''
        for i in select_list:
            anchor_id = i[0]
            # if len(i[1]) > 0:
            self.start_urls.append(i[1])    # 添加直播间地址
            self.relation[i[1]] = anchor_id

    def start_requests(self):
        for url in self.start_urls:
            if url.find('douyu') > 0:    # 斗鱼
                try:
                    douyu_roomid = re.findall(r'^\w+://www\.douyu\.com/(.+)$', url)[0]
                except Exception as error:
                    data = "spider:{} 该url不符合匹配要求,可能为无效直播地址 url:{} time:{} error:{}".format(self.name, url, time_str(), error)
                    logging.error(data)
                    continue
                douyu_api = "http://open.douyucdn.cn/api/RoomApi/room/{}"
                yield scrapy.Request(
                    douyu_api.format(douyu_roomid),
                    # 蚂蚁请求头
                    # headers=generate_sign(),
                    callback=self.douyu_parse,
                    # errback=self.errback_handle,
                    meta={"url": deepcopy(url)}
                )
            if url.find('quanmin') > 0:     # 全民
                yield scrapy.Request(
                    url,
                    callback=self.quanmin_parse,
                    meta={"url": deepcopy(url)}
                )
            if url.find('huya') > 0:    # 虎牙
                yield scrapy.Request(
                    url,
                    callback=self.huya_parse,
                    meta={"url": deepcopy(url)}
                )
            if url.find('longzhu') > 0:     # 龙珠
                yield scrapy.Request(
                    url,
                    callback=self.longzhu_parse,
                    headers=self.longzhu_live_header,
                    meta={"url": deepcopy(url)}
                )
            if url.find('egame') > 0:    # 企鹅
                egame_roomid = re.findall(r"\d+", url)[0]
                egame_api = 'http://share.egame.qq.com/cgi-bin/pgg_anchor_async_fcgi?param={"key":{"module":"pgg_live_read_svr","method":"get_live_and_profile_info","param":{"anchor_id":%d,"layout_id":"hot","index":0}}}&app_info={"platform":4,"terminal_type":2,"egame_id":"egame_official"}&g_tk=&p_tk='
                yield scrapy.Request(
                    egame_api % int(egame_roomid),
                    callback=self.egame_parse,
                    meta={
                        "roomid": deepcopy(egame_roomid),
                        "url": deepcopy(url)
                    }
                )
            if url.find('panda') > 0:     # 熊猫
                yield scrapy.Request(
                    url,
                    callback=self.panda_parse,
                    meta={"url": deepcopy(url)}
                )
            if url.find('zhanqi') > 0:     # 战旗
                yield scrapy.Request(
                    url,
                    callback=self.zhanqi_parse,
                    meta={"url": deepcopy(url)}
                )
            if url.find('bilibili') > 0:     # b站
                bili_id = re.findall(r"\d+", url)[0]
                bili_api = "https://api.live.bilibili.com/room/v1/Room/room_init?id={}"

                yield scrapy.Request(
                    bili_api.format(bili_id),
                    callback=self.bilibili_parse,
                    dont_filter=True,
                    meta={"url": deepcopy(url)}
                )
            if url.find('huomao') > 0:      # 火猫
                yield scrapy.Request(
                    url,
                    # 蚂蚁请求头
                    # headers=generate_sign(),
                    callback=self.huomao_parse,
                    meta={"url": deepcopy(url)}
                )

    def douyu_parse(self, response):
        if deal_status(response):
            return
        url = response.meta["url"]
        item = Xj_view_liveItem()
        info_dict = json.loads(response.body.decode())
        if info_dict["error"] == 0:
            if info_dict["data"]["room_status"] == "1":     # 处于开播状态
                item["start_time"] = int(time.mktime(time.strptime(info_dict["data"]["start_time"], "%Y-%m-%d %H:%M:%S")))
                item["view_num"] = info_dict["data"]["online"]
                item["anchor_id"] = self.relation[url]
                yield item
            if info_dict["data"]["room_status"] == "2":     # 处于关播状态
                item["end_time"] = int(time.time())
                item["view_num"] = 0
                item["anchor_id"] = self.relation[url]
                yield item

    def quanmin_parse(self, response):
        if deal_status(response):
            return
        url = response.meta["url"]
        item = Xj_view_liveItem()
        live_status = re.findall(r'"play_status":(.*?),"forbid_status"', response.body.decode())
        if len(live_status) > 0 and live_status[0] == "true":   # 处于开播状态
            item["start_time"] = int(time.time())
            item["view_num"] = re.findall(r'"view":(.*?),"weight"', response.body.decode())[0]
            item["anchor_id"] = self.relation[url]
            yield item
        else:   # 处于关播状态
            item["end_time"] = int(time.time())
            item["view_num"] = 0
            item["anchor_id"] = self.relation[url]
            yield item

    def huya_parse(self, response):
        if deal_status(response):
            return
        url = response.meta["url"]
        item = Xj_view_liveItem()
        live_status = re.findall(r'"state":"(.*?)"', response.body.decode())
        if len(live_status) > 0 and live_status[0] == "ON":   # 处于开播状态
            item["start_time"] = int(time.time())
            view_num = response.xpath("//em[@id='live-count']/text()").extract_first()
            if view_num is None:
                data = "spider:{} 该直播间地址可能已无效. url:{} time:{}".format(self.name, url, time_str())
                logging.error(data)
                item["view_num"] = 0
            else:
                item["view_num"] = view_num.replace(',', '')
            item["anchor_id"] = self.relation[url]
            yield item
        else:   # 处于关播状态
            item["end_time"] = int(time.time())
            item["view_num"] = 0
            item["anchor_id"] = self.relation[url]
            yield item

    def longzhu_parse(self, response):
        if deal_status(response):
            return
        url = response.meta["url"]
        longzhu_roomid = re.findall(r',"RoomId":(.*?),"Domain"', response.body.decode())
        if len(longzhu_roomid) > 0:
            longzhu_api = "http://roomapicdn.longzhu.com/room/roomstatus?roomid={}&lzv=1".format(longzhu_roomid[0])
            yield scrapy.Request(
                longzhu_api,
                callback=self.longzhu_detail,
                headers=longzhu_header(),
                meta={"url": deepcopy(url)}
            )

    def longzhu_detail(self, response):
        if deal_status(response):
            return
        url = response.meta["url"]
        item = Xj_view_liveItem()
        info_dict = json.loads(response.body.decode())
        if "Broadcast" in info_dict.keys():     # 处于开播状态
            item["start_time"] = int(time.time())
            item["view_num"] = info_dict["OnlineCount"]
            item["anchor_id"] = self.relation[url]
            yield item
        else:   # 处于关播状态
            item["end_time"] = int(time.time())
            item["view_num"] = 0
            item["anchor_id"] = self.relation[url]
            yield item

    def egame_parse(self, response):
        if deal_status(response):
            return
        roomid = response.meta["roomid"]
        url = response.meta["url"]
        info_dict = json.loads(response.body.decode())
        if info_dict["ecode"] == 0:
            try:
                live_status = info_dict["data"]["key"]["retBody"]["data"]["profile_info"]["is_live"]
            except KeyError as err:
                logging.error("spider:{} 从该直播间抓取直播状态时取值失败 url:{} error:{}".format(self.name, url, err))
                return
            item = Xj_view_liveItem()
            if live_status == 1:    # 处于开播状态
                item["start_time"] = info_dict["data"]["key"]["retBody"]["data"]["video_info"]["start_tm"]
                pid = info_dict["data"]["key"]["retBody"]["data"]["video_info"]["pid"]
                egame_api = 'http://wdanmaku.egame.qq.com/cgi-bin/pgg_barrage_async_fcgi?param={"key":{"module":"pgg_live_barrage_svr","method":"get_barrage","param":{"anchor_id":%d,"vid":%s,"scenes":4096,"last_tm":%d}}}&app_info={"platform":4,"terminal_type":2,"egame_id":"egame_official"}&g_tk=&p_tk=&tt=1'
                yield scrapy.Request(
                    egame_api % (int(roomid), pid, int(time.time())),
                    callback=self.egame_detail,
                    meta={
                        "url": deepcopy(url),
                        "item": deepcopy(item)
                    }
                )
            if live_status == 0:    # 处于关播状态
                item["end_time"] = info_dict["data"]["key"]["retBody"]["data"]["video_info"]["end_tm"]
                item["view_num"] = 0
                item["anchor_id"] = self.relation[url]
                yield item

    def egame_detail(self, response):
        if deal_status(response):
            return
        item = response.meta["item"]
        url = response.meta["url"]
        info_dict = json.loads(response.body.decode())
        if info_dict["ecode"] == 0:
            item["view_num"] = info_dict["data"]["key"]["retBody"]["data"]["online_count"]
            item["anchor_id"] = self.relation[url]
            yield item

    def panda_parse(self, response):
        if deal_status(response):
            return
        url = response.meta["url"]
        item = Xj_view_liveItem()
        live_status = re.findall(r'\'videoinfo\'.+?"status":"(.*?)"', response.body.decode())
        if len(live_status) > 0 and live_status[0] == "2":  # 处于开播状态
            item["start_time"] = int(re.findall(r'"start_time":"(.*?)","end_time":"(.*?)"', response.body.decode())[0][0])
            # item["end_time"] = int(re.findall(r'"start_time":"(.*?)","end_time":"(.*?)"', response.body.decode())[0][1])
            item["view_num"] = int(re.findall(r'"person_num":"(.*?)"', response.body.decode())[0])
            item["anchor_id"] = self.relation[url]
            yield item
        else:
            item["end_time"] = int(time.time())
            item["view_num"] = 0
            item["anchor_id"] = self.relation[url]
            yield item

    def zhanqi_parse(self, response):
        if deal_status(response):
            return
        url = response.meta["url"]
        item = Xj_view_liveItem()
        live_status = re.findall(r',"status":"(.*?)",', response.body.decode())
        if len(live_status) > 0 and live_status[0] == "4":  # 处于开播状态
            item["start_time"] = int(time.time())
            try:
                item["view_num"] = int(re.findall(r',"online":"(.*?)",', response.body.decode())[0])
            except Exception as error:
                data = "spider:{} 该直播地址有误. url:{} time:{} error:{}".format(self.name, url, time_str(), error)
                logging.error(data)
                item["view_num"] = 0
            item["anchor_id"] = self.relation[url]
            yield item
        else:   # 处于关播状态
            item["end_time"] = int(time.time())
            item["view_num"] = 0
            item["anchor_id"] = self.relation[url]
            yield item

    def bilibili_parse(self, response):
        if deal_status(response):
            return
        url = response.meta["url"]
        info_dict = json.loads(response.body.decode())
        if info_dict["code"] == 0:
            room_id = info_dict["data"]["room_id"]
            bili_api = "https://api.live.bilibili.com/room/v1/Room/get_info?room_id={}&from=room"
            yield scrapy.Request(
                bili_api.format(room_id),
                callback=self.bilibili_detail,
                meta={"url": deepcopy(url)}
            )

    def bilibili_detail(self, response):
        if deal_status(response):
            return
        url = response.meta["url"]
        info_dict = json.loads(response.body.decode())
        item = Xj_view_liveItem()
        live_status = info_dict["data"]["live_status"]
        if live_status == 1:    # 处于开播状态
            item["start_time"] = int(time.mktime(time.strptime(info_dict["data"]["live_time"], "%Y-%m-%d %H:%M:%S")))
            item["view_num"] = info_dict["data"]["online"]
            item["anchor_id"] = self.relation[url]
            yield item
        if live_status == 0:    # 处于关播状态
            item["end_time"] = int(time.time())
            item["view_num"] = 0
            item["anchor_id"] = self.relation[url]
            yield item

    def huomao_parse(self, response):
        if deal_status(response):
            return
        url = response.meta["url"]
        item = Xj_view_liveItem()
        live_status = re.findall(r'"is_live":(.*?),"', response.body.decode())
        if len(live_status) > 0 and live_status[0] == "1":      # 处于开播状态
            item["start_time"] = int(time.time())
            try:
                item["view_num"] = int(re.findall(r'"views":(.*?),', response.body.decode())[0])
            except Exception as error:
                data = "spider:{} 该直播间地址有误,提取的view_num为非数字格式. url:{} time:{} error:{}".format(self.name, url, time_str(), error)
                logging.error(data)
                item["view_num"] = 0
            item["anchor_id"] = self.relation[url]
            yield item
        else:   # 处于关播状态
            item["end_time"] = int(time.time())
            item["view_num"] = 0
            item["anchor_id"] = self.relation[url]
            yield item

    def errback_handle(self, failure):
        '''
        请求错误处理
        :param failure:
        :return:
        '''
        logging.critical(repr(failure))
        pass
