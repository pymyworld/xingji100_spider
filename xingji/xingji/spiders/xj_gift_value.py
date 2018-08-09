# -*- coding: utf-8 -*-
# 该爬虫抓取各平台礼物价值，换算为人民币单位，使用于弹幕礼物监听部分计算出主播每天的收入
# 斗鱼,火猫存在被ban情况，需要使用代理
import scrapy
import json
import urllib.parse
import re
import time
import logging
from ..tools import deal_status
from ..items import Xj_gift_value
from ..tools import generate_sign


class XjGiftValueSpider(scrapy.Spider):
    name = 'xj_gift_value'
    custom_settings = {
        'ITEM_PIPELINES': {
            'xingji.pipelines.Xj_gift_valuePipeline': 100,
        }
    }
    start_urls = [
        'https://www.quanmin.tv/shouyin_api/public/config/gift/pc?debug&cid=6&p=5&rid=-1&rcat=-1&uid=9240646&no=-1&net=0&screen=3&device=j8jwbr5tym9irg1zq8jkk172p6bigangifp7cw2y&refer=room&sw=1920&sh=1080&prepage=https%3A%2F%2Fwww.quanmin.tv%2Fgame%2Fall&url=https%3A%2F%2Fwww.quanmin.tv%2F333&viewid=j8jwbr5tym9irg1zq8jkk172p6bigangifp7cw2y1526283734765×tamp=1526283779296&env=product&ch=quanmin&cv=quanmin_pc&sid=9488f0a515086ebe096ca4982e2757b7&uid=333&categoryId=1&owid=333&platform=2&_=1526283833763',
        'https://www.quanmin.tv/shouyin_api/public/config/gift/pc?debug&cid=6&p=5&rid=-1&rcat=-1&uid=9240646&no=-1&net=0&screen=3&device=j8jwbr5tym9irg1zq8jkk172p6bigangifp7cw2y&refer=room&sw=1920&sh=1080&prepage=https%3A%2F%2Fwww.quanmin.tv%2Fgame%2Fjuediqiusheng&url=https%3A%2F%2Fwww.quanmin.tv%2F25859562&viewid=j8jwbr5tym9irg1zq8jkk172p6bigangifp7cw2y1526347891914&timestamp=1526363201737&env=product&ch=quanmin&cv=quanmin_pc&sid=9488f0a515086ebe096ca4982e2757b7&uid=1392166960&categoryId=68&owid=1392166960&platform=2&_=1526363207254',
        'https://www.quanmin.tv/shouyin_api/public/config/gift/pc?debug&cid=6&p=5&rid=-1&rcat=-1&uid=9240646&no=-1&net=0&screen=3&device=j8jwbr5tym9irg1zq8jkk172p6bigangifp7cw2y&refer=room&sw=1920&sh=1080&prepage=https%3A%2F%2Fwww.quanmin.tv%2Fgame%2Fall&url=https%3A%2F%2Fwww.quanmin.tv%2F28039633&viewid=j8jwbr5tym9irg1zq8jkk172p6bigangifp7cw2y1526347891914&timestamp=1526363981148&env=product&ch=quanmin&cv=quanmin_pc&sid=9488f0a515086ebe096ca4982e2757b7&uid=1916573306&categoryId=4&owid=1916573306&platform=2&_=1526364000091',
        'https://www.quanmin.tv/shouyin_api/public/config/gift/pc?debug&cid=6&p=5&rid=-1&rcat=-1&uid=9240646&no=-1&net=0&screen=3&device=j8jwbr5tym9irg1zq8jkk172p6bigangifp7cw2y&refer=room&sw=1920&sh=1080&prepage=https%3A%2F%2Fwww.quanmin.tv%2Fgame%2Fall&url=https%3A%2F%2Fwww.quanmin.tv%2F9479324&viewid=j8jwbr5tym9irg1zq8jkk172p6bigangifp7cw2y1526347891914&timestamp=1526364589536&env=product&ch=quanmin&cv=quanmin_pc&sid=9488f0a515086ebe096ca4982e2757b7&uid=9479324&categoryId=28&owid=9479324&platform=2&_=1526364595884',
        'https://www.quanmin.tv/shouyin_api/public/config/gift/pc?debug&cid=6&p=5&rid=-1&rcat=-1&uid=9240646&no=-1&net=0&screen=3&device=j8jwbr5tym9irg1zq8jkk172p6bigangifp7cw2y&refer=room&sw=1920&sh=1080&prepage=https%3A%2F%2Fwww.quanmin.tv%2Fgame%2Fall&url=https%3A%2F%2Fwww.quanmin.tv%2F22300183&viewid=j8jwbr5tym9irg1zq8jkk172p6bigangifp7cw2y1526347891914&timestamp=1526364853195&env=product&ch=quanmin&cv=quanmin_pc&sid=9488f0a515086ebe096ca4982e2757b7&uid=1172299304&categoryId=10&owid=1172299304&platform=2&_=1526364904240',
        'https://www.zhanqi.tv/api/static/v2.1/live/list/20/1.json',
        'https://www.panda.tv/live_lists?status=2&token=545c94500c8ed951decfaa25d59df480&pageno=1&pagenum=120&order=top',
        'http://share.egame.qq.com/cgi-bin/pgg_live_async_fcgi?param={"key":{"module":"pgg_live_read_ifc_mt_svr","method":"get_new_live_list","param":{"appid":"hot","page_num":1,"page_size":40,"tag_id":0,"tag_id_str":""}}}&app_info={"platform":4,"terminal_type":2,"egame_id":"egame_official","version_code":"9.9.9","version_name":"9.9.9"}&g_tk=&p_tk=&tt=1&_t=1526540987169',
        'http://api.vc.bilibili.com/room/v1/area/getRoomList?parent_area_id=2&cate_id=0&area_id=0&sort_type=online&page=1&page_size=30',
        'http://configapi.longzhu.com/item/getallitems?lzv=1',
        'https://www.huomao.com/channels/channel.json?page=1&game_url_rule=all',
        'https://www.douyu.com/gapi/rkc/directory/0_0/1',
    ]
    bili_headers = {
        "Host": "api.live.bilibili.com",
        "Origin": "https://live.bilibili.com",
        "Referer": "https://live.bilibili.com/102?visit_id=2id1no66ija0",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/66.0.3359.139 Safari/537.36"
    }
    huomao_headers = {
        "Host": "www.huomao.com",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/66.0.3359.181 Safari/537.36",
    }
    # 平台id
    quanmin_id = 8
    douyu_id = 11
    longzhu_id = 4
    huomao_id = 6
    huya_id = 7
    zhanqi_id = 9
    panda_id = 10
    egame_id = 14
    bilibili_id = 16
    # 各平台价格换算
    quanmin_conver = 10     # 10币/元
    zhanqi_conver = 100     # 100币/元
    panda_conver = 10    # 10币/元
    huya_conver = 1000      # 1000金豆/元
    egame_conver = 10    # 10钻石/元
    bilibili_conver = 1000      # 1000金瓜子/元
    huomao_conver = 1    # 1币/元
    longzhu_conver = 100    # 100币/元
    douyu_conver = 1    # 1鱼翅/元

    def start_requests(self):
        for url in self.start_urls:
            if url.find('quanmin') > 0:
                yield scrapy.Request(
                    url,
                    callback=self.quanmin_parse
                )
            if url.find('zhanqi') > 0:
                yield scrapy.Request(
                    url,
                    callback=self.zhanqi_parse
                )
            if url.find('panda') > 0:
                yield scrapy.Request(
                    url,
                    callback=self.panda_parse
                )
            if url.find('egame') > 0:
                yield scrapy.Request(
                    url,
                    callback=self.egame_parse
                )
            if url.find('bilibili') > 0:
                yield scrapy.Request(
                    url,
                    callback=self.bilibili_parse
                )
            if url.find('longzhu') > 0:
                yield scrapy.Request(
                    url,
                    callback=self.longzhu_parse,
                )
            if url.find('huomao') > 0:
                yield scrapy.Request(
                    url,
                    callback=self.huomao_parse,
                )
            if url.find('douyu') > 0:
                yield scrapy.Request(
                    url,
                    # 蚂蚁请求头
                    # headers=generate_sign(),
                    callback=self.douyu_parse,
                    # errback=self.errback_handle,
                )

    def quanmin_parse(self, response):
        if deal_status(response):
            return
        info_dict = json.loads(response.body.decode())
        if info_dict["code"] == 0:
            data_lists = info_dict["data"]["lists"]
            for data in data_lists:
                item = Xj_gift_value()
                item["gift_id"] = data["id"]
                item["name"] = data["name"]
                item["platform_id"] = self.quanmin_id
                gift_cost = data["diamond"]
                item["price"] = round(gift_cost / self.quanmin_conver, 2)
                yield item

    def zhanqi_parse(self, response):
        if deal_status(response):
            return
        code_url = urllib.parse.unquote(response.url)
        page = re.findall(r'/(\d+)\.json$', code_url)[0]
        info_dict = json.loads(response.body.decode())
        if info_dict["code"] == 0:
            rooms_list = info_dict["data"]["rooms"]
            if len(rooms_list) == 0:
                return
            else:
                for room in rooms_list:
                    live_url = "https://www.zhanqi.tv" + room["url"]
                    yield scrapy.Request(
                        live_url,
                        callback=self.zhanqi_detail
                    )
        # 下一页
        next_api = 'https://www.zhanqi.tv/api/static/v2.1/live/list/20/{}.json'.format(int(page) + 1)
        yield scrapy.Request(
            next_api,
            callback=self.zhanqi_parse
        )

    def zhanqi_detail(self, response):
        if deal_status(response):
            return
        info_json = re.findall(r'oPageConfig\.aRoomGiftList = (.+);', response.body.decode())[0]
        info_list = json.loads(info_json)
        for info in info_list:
            item = Xj_gift_value()
            item["name"] = info["name"]
            item["platform_id"] = self.zhanqi_id
            gift_cost = info["price"]
            item["price"] = round(int(gift_cost) / self.zhanqi_conver, 2)
            item["gift_id"] = info["id"]
            yield item

    def panda_parse(self, response):
        if deal_status(response):
            return
        info_dict = json.loads(response.body.decode())
        code_url = urllib.parse.unquote(response.url)
        page = re.findall(r'&pageno=(\d+)&', code_url)[0]
        if info_dict["errno"] == 0:
            items_lists = info_dict["data"]["items"]
            if len(items_lists) == 0:
                return
            else:
                for items in items_lists:
                    if items["id"] != "":
                        roomid = items["id"]
                        gift_api = "https://mall.gate.panda.tv/ajax_gift_gifts_get?token=545c94500c8ed951decfaa25d59df480&roomid={}&rid=47048922"
                        yield scrapy.Request(
                            gift_api.format(int(roomid)),
                            callback=self.panda_detail
                        )
                    else:
                        continue
        # 下一页
        next_api = "https://www.panda.tv/live_lists?status=2&token=545c94500c8ed951decfaa25d59df480&pageno={}&pagenum=120&order=top"
        yield scrapy.Request(
            next_api.format(int(page) + 1),
            callback=self.panda_parse
        )

    def panda_detail(self, response):
        if deal_status(response):
            return
        info_dict = json.loads(response.body.decode())
        if info_dict["errno"] == 0:
            gift_lists = info_dict["data"]["items"]
            for gift in gift_lists:
                item = Xj_gift_value()
                item["name"] = gift["name"]
                item["gift_id"] = gift["id"]
                item["platform_id"] = self.panda_id
                gift_cost = gift["price"]
                item["price"] = round(int(gift_cost) / self.panda_conver, 2)
                yield item

    def egame_parse(self, response):
        if deal_status(response):
            return
        info_dict = json.loads(response.body.decode())
        code_url = urllib.parse.unquote(response.url)
        page = re.findall(r'"page_num":(\d+),"', code_url)[0]
        live_list = info_dict["data"]["key"]["retBody"]["data"]["live_data"]["live_list"]
        if len(live_list) == 0:
            return
        else:
            for live in live_list:
                anchor_id = live["anchor_id"]
                gift_api = 'http://share.egame.qq.com/cgi-bin/pgg_kit_async_fcgi?param={"key":{"module":"pgg_gift_svr","method":"get_gift_list","param":{"tt":0,"version":"","anchor_id":%d}}}&app_info={"platform":4,"terminal_type":2,"egame_id":"egame_official"}&g_tk=&p_tk=&tt=1'
                yield scrapy.Request(
                    gift_api % int(anchor_id),
                    callback=self.egame_detail
                )
        # 下一页
        next_api = 'http://share.egame.qq.com/cgi-bin/pgg_live_async_fcgi?param={"key":{"module":"pgg_live_read_ifc_mt_svr","method":"get_new_live_list","param":{"appid":"hot","page_num":%d,"page_size":40,"tag_id":0,"tag_id_str":""}}}&app_info={"platform":4,"terminal_type":2,"egame_id":"egame_official","version_code":"9.9.9","version_name":"9.9.9"}&g_tk=&p_tk=&tt=1&_t=1526540987169'
        yield scrapy.Request(
            next_api % (int(page) + 1),
            callback=self.egame_parse,
        )

    def egame_detail(self, response):
        if deal_status(response):
            return
        info_dict = json.loads(response.body.decode())
        gift_list_a = info_dict["data"]["key"]["retBody"]["data"]["fans_guardian"]["list"]
        gift_list_b = info_dict["data"]["key"]["retBody"]["data"]["list"]
        if len(gift_list_a) > 0:
            for gift_a in gift_list_a:
                item = Xj_gift_value()
                item["name"] = gift_a["name"]
                item["gift_id"] = gift_a["id"]
                item["platform_id"] = self.egame_id
                gift_cost = gift_a["price"]
                item["price"] = round(int(gift_cost) / self.egame_conver, 2)
                yield item
        if len(gift_list_b) > 0:
            for gift_b in gift_list_b:
                item = Xj_gift_value()
                item["name"] = gift_b["name"]
                item["gift_id"] = gift_b["id"]
                item["platform_id"] = self.egame_id
                gift_cost = gift_b["price"]
                item["price"] = round(int(gift_cost) / self.egame_conver, 2)
                yield item

    def bilibili_parse(self, response):
        if deal_status(response):
            return
        info_dict = json.loads(response.body.decode())
        code_url = urllib.parse.unquote(response.url)
        page = re.findall(r'&page=(\d+)&page_size=30$', code_url)[0]
        data_list = info_dict["data"]
        if len(data_list) == 0:
            return
        else:
            for data in data_list:
                roomid = data["roomid"]
                area_v2_id = data["area_v2_id"]
                gift_api = "https://api.live.bilibili.com/gift/v2/live/room_gift_list?roomid={}&area_v2_id={}"
                yield scrapy.Request(
                    gift_api.format(roomid, area_v2_id),
                    callback=self.bilibili_detail,
                    headers=self.bili_headers,
                )
        # 下一页
        next_live_api = "http://api.vc.bilibili.com/room/v1/area/getRoomList?parent_area_id=2&cate_id=0&area_id=0&sort_type=online&page={}&page_size=30"
        yield scrapy.Request(
            next_live_api.format(int(page)+1),
            callback=self.bilibili_parse,
        )

    def bilibili_detail(self, response):
        if deal_status(response):
            return
        info_dict = json.loads(response.body.decode())
        if info_dict["code"] == 0:
            data_list = info_dict["data"]
            if len(data_list) > 0:
                for data in data_list:
                    item = Xj_gift_value()
                    item["name"] = data["name"]
                    item["gift_id"] = data["id"]
                    item["platform_id"] = self.bilibili_id
                    gift_cost = data["price"]
                    item["price"] = round(int(gift_cost) / self.bilibili_conver, 3)
                    yield item

    def longzhu_parse(self, response):
        if deal_status(response):
            return
        gift_list = json.loads(response.body.decode())
        for gift in gift_list:
            item = Xj_gift_value()
            item["name"] = gift["title"]
            item["gift_id"] = gift["id"]
            item["platform_id"] = self.longzhu_id
            item["price"] = gift["costValue"]
            yield item

    def huomao_parse(self, response):
        if deal_status(response):
            return
        info_dict = json.loads(response.body.decode())
        code_url = urllib.parse.unquote(response.url)
        page = re.findall(r'\?page=(\d+)&', code_url)[0]
        if info_dict["code"] == 100:
            data_list = info_dict["data"]["channelList"]
            if len(data_list) == 0:
                return
            else:
                for data in data_list:
                    cid = data["id"]
                    live_url = "https://www.huomao.com/{}".format(data["room_number"])
                    self.huomao_headers["Referer"] = live_url
                    gift_api = "http://www.huomao.com/ajax/getNewGift?cid={}&cache_time={}&face_label=0"
                    yield scrapy.Request(
                        gift_api.format(cid, int(time.time())),
                        callback=self.huomao_detail,
                    )
        # 下一页
        next_api = "https://www.huomao.com/channels/channel.json?page={}&game_url_rule=all"
        yield scrapy.Request(
            next_api.format(int(page) + 1),
            callback=self.huomao_parse,
        )

    def huomao_detail(self, response):
        if deal_status(response):
            return
        info_dict = json.loads(response.body.decode())
        if info_dict["code"] == 200:
            gift_list = info_dict["data"]["giftInfo"]
            for gift in gift_list:
                item = Xj_gift_value()
                item["name"] = gift["name"]
                item["gift_id"] = gift["id"]
                item["platform_id"] = self.huomao_id
                gift_cost = gift["price"]
                item["price"] = round(int(gift_cost) / self.huomao_conver, 2)
                yield item

    def douyu_parse(self, response):
        if deal_status(response):
            return
        info_dict = json.loads(response.body.decode())
        code_url = urllib.parse.unquote(response.url)
        page = re.findall(r'/0_0/(\d+)$', code_url)[0]
        if info_dict["code"] == 0:
            data_list = info_dict["data"]["rl"]
            if len(data_list) == 0:
                return
            else:
                for data in data_list:
                    roomid = data["rid"]
                    gift_api = "http://open.douyucdn.cn/api/RoomApi/room/{}"
                    yield scrapy.Request(
                        gift_api.format(roomid),
                        callback=self.douyu_detail,
                        # 蚂蚁请求头
                        # headers=generate_sign(),
                        # errback=self.errback_handle,
                    )
        # 下一页
        next_api = "https://www.douyu.com/gapi/rkc/directory/0_0/{}".format(int(page) + 1)
        yield scrapy.Request(
            next_api,
            callback=self.douyu_parse,
            # 蚂蚁请求头
            # headers=generate_sign(),
            # errback=self.errback_handle,
        )

    def douyu_detail(self, response):
        if deal_status(response):
            return
        info_dict = json.loads(response.body.decode())
        if info_dict["error"] == 0:
            gift_list = info_dict["data"]["gift"]
            for gift in gift_list:
                item = Xj_gift_value()
                if gift["type"] == "2":     # 为鱼翅购买礼物
                    item["name"] = gift["name"]
                    item["gift_id"] = gift["id"]
                    item["platform_id"] = self.douyu_id
                    gift_cost = gift["pc"]
                    item["price"] = round(int(gift_cost) / self.douyu_conver, 2)
                    yield item

    def errback_handle(self, failure):
        '''
        请求错误处理
        :param failure:
        :return:
        '''
        logging.critical(repr(failure))
        pass


