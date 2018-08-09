# -*- coding: utf-8 -*-
# 该爬虫更新xj_anchor_data表中数据
# 首先从xj_star中取到anchor_id与m_weibo,以m_weibo为key建立起与anchor_id的关系
# 爬取m_weibo后通过dict键值取得anchor_id,查询数据库获得其他地址
import scrapy
import re
import json
import logging
import time
import datetime
import os
from ..sql_handle import Sqlhandle
from copy import deepcopy
from ..items import Xj_anchor_dataItem
from ..tools import *


class XjAnchorDataSpider(scrapy.Spider):
    name = 'xj_anchor_data'
    custom_settings = {
        'ITEM_PIPELINES': {
            'xingji.pipelines.Xj_anchor_dataPipeline': 100,
        }
    }
    start_urls = []
    baidu_headers = {
        "Host": "rank.chinaz.com",
        "Upgrade-Insecure-Requests": "1",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/65.0.3325.181 Safari/537.36"
    }
    tieba_headers = {
        "Host": "tieba.baidu.com",
        "Referer": "https://tieba.baidu.com/",
        "Upgrade-Insecure-Requests": "1",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/65.0.3325.181 Safari/537.36"
    }
    longzhu_live_header = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/65.0.3325.181 Safari/537.36",
        "Host": "star.longzhu.com",
        "If-Modified-Since": make_gmt(),
        "Referer": "http://longzhu.com/channels/all",
        "Upgrade-Insecure-Requests": "1"
    }
    douyu_id = 11
    quanmin_id = 8
    huya_id = 7
    longzhu_id = 4
    egame_id = 14
    panda_id = 10
    zhanqi_id = 9
    bilibili_id = 16
    huomao_id = 6

    def __init__(self):
        super(XjAnchorDataSpider, self).__init__()
        # 用字典的键值来建立anchor_info表中anchor_id与url的关系
        self.relation = {}
        self.now_time = datetime.datetime.now().strftime("%H:%M:%S")
        self.today = time.strftime('%Y-%m-%d', time.localtime(int(time.time())))
        self.yesterday = time.strftime('%Y-%m-%d', time.localtime(int(time.time()) - 86400))
        self.sql = Sqlhandle()
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
        向start_urls中添加url
        :param select_list:
        :return:
        '''
        for i in select_list:
            anchor_id = i[0]
            if len(i[1]) > 0:
                self.start_urls.append(i[1])    # 添加直播间地址
                self.relation[i[1]] = anchor_id

    def start_requests(self):
        for url in self.start_urls:
            anchor_id = self.relation[url]
            # douyu
            if url.find('douyu') > 0:
                try:
                    douyu_roomid = re.findall(r"^\w+://www\.douyu\.com/(.+)$", url)[0]
                except Exception as error:
                    data = "spider:{} 该直播地址有误,请核对该地址. anchor_id:{} 错误live_url:{} time:{} error:{}"
                    logging.error(data.format(self.name, anchor_id, url, time_str(), error))
                    continue
                douyu_api = "http://open.douyucdn.cn/api/RoomApi/room/{}"
                yield scrapy.Request(
                    douyu_api.format(douyu_roomid),
                    # 蚂蚁请求头
                    # headers=generate_sign(),
                    callback=self.douyu_parse,
                    # errback=self.errback_handle,
                    meta={
                        "anchor_id": deepcopy(anchor_id),
                    }
                )
            # quanmin
            if url.find('quanmin') > 0:
                yield scrapy.Request(
                    url,
                    callback=self.quanmin_parse,
                    meta={
                        "anchor_id": deepcopy(anchor_id),
                    }
                )
            # huya
            if url.find('huya') > 0:
                yield scrapy.Request(
                    url,
                    callback=self.huya_parse,
                    meta={
                        "anchor_id": deepcopy(anchor_id),
                        "live_url": deepcopy(url),
                    }
                )
            # longzhu
            if url.find('longzhu') > 0:
                yield scrapy.Request(
                    url,
                    callback=self.longzhu_parse,
                    headers=self.longzhu_live_header,
                    meta={
                        "live_url": deepcopy(url),
                        "anchor_id": deepcopy(anchor_id),
                    }
                )
            # egame
            if url.find('egame') > 0:
                try:
                    egame_anchor_id = re.findall(r"^http://egame\.qq\.com/live\?anchorid=(\d+)$", url)[0]
                except Exception as error:
                    data = "spider:{} 该直播地址有误,请核对该地址. anchor_id:{} 错误live_url:{} time:{} error:{}"
                    logging.error(data.format(self.name, anchor_id, url, time_str(), error))
                    continue
                egame_api = 'http://share.egame.qq.com/cgi-bin/pgg_anchor_async_fcgi?param={"key":{"module":"pgg_live_read_svr","method":"get_live_and_profile_info","param":{"anchor_id":%s,"layout_id":"hot","index":0}}}&app_info={"platform":4,"terminal_type":2,"egame_id":"egame_official"}&g_tk=&p_tk='
                yield scrapy.Request(
                    egame_api % egame_anchor_id,
                    callback=self.egame_parse,
                    meta={
                        "anchor_id": deepcopy(anchor_id),
                    }
                )
            # panda
            if url.find('panda') > 0:
                panda_roomid = re.findall(r"^\w+://www\.panda\.tv/(\d+)$", url)[0]
                panda_api = "https://www.panda.tv/room_followinfo?token=&roomid={}&_={}".format(panda_roomid, int(round(time.time() * 1000)))
                yield scrapy.Request(
                    panda_api,
                    callback=self.panda_parse,
                    meta={
                        "anchor_id": deepcopy(anchor_id),
                    }
                )
            # zhanqi
            if url.find('zhanqi') > 0:
                yield scrapy.Request(
                    url,
                    callback=self.zhanqi_parse,
                    meta={
                        "anchor_id": deepcopy(anchor_id),
                        "live_url": deepcopy(url),
                    }
                )
            # bilibili
            if url.find('bilibili') > 0:
                b_roomid = re.findall(r"^\w+://live\.bilibili\.com/(\d+)$", url)[0]
                b_api = "https://api.live.bilibili.com/room/v1/Room/get_info?room_id={}&from=room".format(b_roomid)
                yield scrapy.Request(
                    b_api,
                    callback=self.bilibili_parse,
                    meta={
                        "anchor_id": deepcopy(anchor_id),
                        "live_url": deepcopy(url),
                    }
                )
            # huomao
            if url.find('huomao') > 0:
                yield scrapy.Request(
                    url,
                    callback=self.huomao_parse,
                    meta={
                        "anchor_id": deepcopy(anchor_id),
                    }
                )

    def douyu_parse(self, response):
        '''
        获取斗鱼平台直播间关注数
        :param response:
        :return:
        '''
        if deal_status(response):
            return
        anchor_id = response.meta["anchor_id"]
        item = Xj_anchor_dataItem()
        info_dict = json.loads(response.body.decode())
        try:
            item["followers"] = info_dict["data"]["fans_num"]
        except Exception as error:
            data = "spider:{} {} 主播id:{} time:{} error:{}".format(self.name, info_dict["data"], anchor_id, time_str(), error)
            logging.error(data)
            item["followers"] = 0
        item["platform_id"] = self.douyu_id
        item["anchor_id"] = anchor_id
        item["category_id"], name = self.sql.select_category_id_name(anchor_id)
        baidu_api = "http://rank.chinaz.com/ajaxsync.aspx?at=index&kw={}"
        yield scrapy.Request(
            baidu_api.format(name),
            headers=self.baidu_headers,
            callback=self.baidu_zhishu,
            meta={
                "anchor_id": deepcopy(anchor_id),
                "item": deepcopy(item),
                "url": deepcopy(baidu_api),
            }
        )

    def quanmin_parse(self, response):
        '''
        获取全民平台直播间关注量
        :param response:
        :return:
        '''
        if deal_status(response):
            return
        anchor_id = response.meta["anchor_id"]
        item = Xj_anchor_dataItem()
        followers = response.xpath("//span[@class='room_w-title_favnum c-icon_favnum']/text()").extract_first()
        if followers is None:
            data = "spider:{} 抓取直播间订阅量失败 主播id:{} time:{}".format(self.name, anchor_id, time_str())
            logging.error(data)
            item["followers"] = 0
        else:
            item["followers"] = followers.replace(',', '')
        item["platform_id"] = self.quanmin_id
        item["anchor_id"] = anchor_id
        item["category_id"], name = self.sql.select_category_id_name(anchor_id)
        baidu_api = "http://rank.chinaz.com/ajaxsync.aspx?at=index&kw={}"
        yield scrapy.Request(
            baidu_api.format(name),
            headers=self.baidu_headers,
            callback=self.baidu_zhishu,
            meta={
                "anchor_id": deepcopy(anchor_id),
                "item": deepcopy(item),
                "url": deepcopy(baidu_api),
            }
        )

    def huya_parse(self, response):
        '''
        获取虎牙平台直播间关注量
        :param response:
        :return:
        '''
        if deal_status(response):
            return
        anchor_id = response.meta["anchor_id"]
        live_url = response.meta["live_url"]
        item = Xj_anchor_dataItem()
        item["followers"] = response.xpath("//div[@id='activityCount']/text()").extract_first()
        if item["followers"] is None:
            data = "spider:{} 该主播直播间地址可能已经更换,也可能涉嫌违规,暂时将主播直播间关注量设为0. 主播id:{} 失效地址:{} time:{}".format(self.name, anchor_id, live_url, time_str())
            logging.error(data)
            item["followers"] = 0
        item["platform_id"] = self.huya_id
        item["anchor_id"] = anchor_id
        item["category_id"], name = self.sql.select_category_id_name(anchor_id)
        baidu_api = "http://rank.chinaz.com/ajaxsync.aspx?at=index&kw={}"
        yield scrapy.Request(
            baidu_api.format(name),
            headers=self.baidu_headers,
            callback=self.baidu_zhishu,
            meta={
                "anchor_id": deepcopy(anchor_id),
                "item": deepcopy(item),
                "url": deepcopy(baidu_api),
            }
        )

    def longzhu_parse(self, response):
        if deal_status(response):
            return
        anchor_id = response.meta["anchor_id"]
        longzhu_roomid = re.findall(r',"RoomId":(.*?),"Domain"', response.body.decode())
        if len(longzhu_roomid) > 0:
            longzhu_api = "http://roomapicdn.longzhu.com/room/roomstatus?roomid={}&lzv=1".format(longzhu_roomid[0])
            yield scrapy.Request(
                longzhu_api,
                callback=self.longzhu_detail,
                headers=longzhu_header(),
                meta={
                    "anchor_id": deepcopy(anchor_id),
                }
            )

    def longzhu_detail(self, response):
        if deal_status(response):
            return
        anchor_id = response.meta["anchor_id"]
        item = Xj_anchor_dataItem()
        info_dict = json.loads(response.body.decode())
        item["followers"] = info_dict["RoomSubscribeCount"]
        item["anchor_id"] = anchor_id
        item["platform_id"] = self.longzhu_id
        item["category_id"], name = self.sql.select_category_id_name(anchor_id)
        if item["category_id"] == '':
            data = "spider:{} 该主播缺少游戏分类id,暂时将该主播游戏分类设为0. 主播id:{} time:{}".format(self.name, anchor_id, time_str())
            logging.error(data)
            item["category_id"] = 0
        baidu_api = "http://rank.chinaz.com/ajaxsync.aspx?at=index&kw={}"
        yield scrapy.Request(
            baidu_api.format(name),
            headers=self.baidu_headers,
            callback=self.baidu_zhishu,
            meta={
                "anchor_id": deepcopy(anchor_id),
                "item": deepcopy(item),
                "url": deepcopy(baidu_api),
            }
        )

    def egame_parse(self, response):
        '''
        获取企鹅平台直播间关注量
        :param response:
        :return:
        '''
        if deal_status(response):
            return
        anchor_id = response.meta["anchor_id"]
        item = Xj_anchor_dataItem()
        info_dict = json.loads(response.body.decode())
        item["followers"] = info_dict["data"]["key"]["retBody"]["data"]["profile_info"]["fans_count"]
        item["platform_id"] = self.egame_id
        item["anchor_id"] = anchor_id
        item["category_id"], name = self.sql.select_category_id_name(anchor_id)
        baidu_api = "http://rank.chinaz.com/ajaxsync.aspx?at=index&kw={}"
        yield scrapy.Request(
            baidu_api.format(name),
            headers=self.baidu_headers,
            callback=self.baidu_zhishu,
            meta={
                "anchor_id": deepcopy(anchor_id),
                "item": deepcopy(item),
                "url": deepcopy(baidu_api),
            }
        )

    def panda_parse(self, response):
        '''
        获取熊猫平台直播间关注量
        :param response:
        :return:
        '''
        if deal_status(response):
            return
        anchor_id = response.meta["anchor_id"]
        item = Xj_anchor_dataItem()
        info_dict = json.loads(response.body.decode())
        if info_dict["errno"] == 0:
            item["followers"] = info_dict["data"]["fans"]
        else:
            item["followers"] = 0
        item["platform_id"] = self.panda_id
        item["anchor_id"] = anchor_id
        item["category_id"], name = self.sql.select_category_id_name(anchor_id)
        baidu_api = "http://rank.chinaz.com/ajaxsync.aspx?at=index&kw={}"
        yield scrapy.Request(
            baidu_api.format(name),
            headers=self.baidu_headers,
            callback=self.baidu_zhishu,
            meta={
                "anchor_id": deepcopy(anchor_id),
                "item": deepcopy(item),
                "url": deepcopy(baidu_api),
            }
        )

    def zhanqi_parse(self, response):
        '''
        获取战旗平台直播间关注量
        :param response:
        :return:
        '''
        if deal_status(response):
            return
        anchor_id = response.meta["anchor_id"]
        item = Xj_anchor_dataItem()
        live_url = response.meta["live_url"]
        item["followers"] = response.xpath("//span[@class='dyue-mid js-room-follow-num']/text()").extract_first()
        if item["followers"] is None:
            data = "spider:{} 该直播地址已经无效,暂时将主播直播间关注量设为0. 主播id:{} 失效地址:{} time:{}".format(self.name, anchor_id, live_url, time_str())
            logging.error(data)
            item["followers"] = 0
        item["platform_id"] = self.zhanqi_id
        item["anchor_id"] = anchor_id
        item["category_id"], name = self.sql.select_category_id_name(anchor_id)
        if item["category_id"] == '':
            data = "spider:{} 该主播缺少游戏分类id,暂时将该主播游戏分类设为0. 主播id:{} time:{}".format(self.name, anchor_id, time_str())
            logging.error(data)
            item["category_id"] = 0
        baidu_api = "http://rank.chinaz.com/ajaxsync.aspx?at=index&kw={}"
        yield scrapy.Request(
            baidu_api.format(name),
            headers=self.baidu_headers,
            callback=self.baidu_zhishu,
            meta={
                "anchor_id": deepcopy(anchor_id),
                "item": deepcopy(item),
                "url": deepcopy(baidu_api),
            }
        )

    def bilibili_parse(self, response):
        '''
        获取B站平台直播间关注量
        :param response:
        :return:
        '''
        if deal_status(response):
            return
        anchor_id = response.meta["anchor_id"]
        url = response.meta["live_url"]
        item = Xj_anchor_dataItem()
        info_dict = json.loads(response.body.decode())
        try:
            item["followers"] = info_dict["data"]["attention"]
        except TypeError as err:
            logging.error("spider:{} 该直播地址可能已失效. url:{} error:{}".format(self.name, url, err))
            return
        item["platform_id"] = self.bilibili_id
        item["anchor_id"] = anchor_id
        item["category_id"], name = self.sql.select_category_id_name(anchor_id)
        baidu_api = "http://rank.chinaz.com/ajaxsync.aspx?at=index&kw={}"
        yield scrapy.Request(
            baidu_api.format(name),
            headers=self.baidu_headers,
            callback=self.baidu_zhishu,
            meta={
                "anchor_id": deepcopy(anchor_id),
                "item": deepcopy(item),
                "url": deepcopy(baidu_api),
            }
        )

    def huomao_parse(self, response):
        '''
        获取火猫平台直播间订阅量
        :param response:
        :return:
        '''
        if deal_status(response):
            return
        anchor_id = response.meta["anchor_id"]
        item = Xj_anchor_dataItem()
        try:
            item["followers"] = re.findall(r',"audienceNumber":(.*?),"', response.body.decode())[0]
        except Exception as error:
            data = "spider:{} 该主播直播地址有误. 主播id:{} time:{}".format(self.name, anchor_id, time_str())
            logging.error(data)
            item["followers"] = 0
        item["platform_id"] = self.huomao_id
        item["anchor_id"] = anchor_id
        item["category_id"], name = self.sql.select_category_id_name(anchor_id)
        if item["category_id"] == '':
            data = "spider:{} 该主播缺少游戏分类id,暂时将该主播游戏分类设为0. 主播id:{} time:{}".format(self.name, anchor_id, time_str())
            logging.error(data)
            item["category_id"] = 0
        baidu_api = "http://rank.chinaz.com/ajaxsync.aspx?at=index&kw={}"
        yield scrapy.Request(
            baidu_api.format(name),
            headers=self.baidu_headers,
            callback=self.baidu_zhishu,
            meta={
                "anchor_id": deepcopy(anchor_id),
                "item": deepcopy(item),
                "url": deepcopy(baidu_api),
            }
        )

    def baidu_zhishu(self, response):
        '''
        获取百度指数，请求各平台直播间以获取关注数
        :param response:
        :return:
        '''
        if deal_status(response):
            return
        anchor_id = response.meta["anchor_id"]
        item = response.meta["item"]
        baidu_url = response.meta["url"]
        try:
            quotient = re.findall(r",index:\'(.+)\',pcindex:", response.body.decode())
        except UnicodeDecodeError as err:
            item["quotient"] = 0
            data = "spider:{} 百度指数解析错误 url:{} 主播id:{} time:{}".format(self.name, baidu_url, anchor_id, time_str())
            logging.error(data)
        else:
            if len(quotient) > 0:
                if quotient[0] == '--':
                    item["quotient"] = 0
                else:
                    item["quotient"] = quotient[0]
            else:
                data = "spider:{} 请求百度指数api时存在错误. 主播id:{} time:{}".format(self.name, anchor_id, time_str())
                logging.error(data)
                item["quotient"] = 0
        weibo_url = self.sql.select_from_star(anchor_id, 'weibo')
        # 无微博地址
        if weibo_url == '':
            data = "spider:{} 无微博地址. 主播id:{} time:{}".format(self.name, anchor_id, time_str())
            # logging.error(data)
            item["weibo_fans"] = 0
            tieba_url = self.sql.select_from_star(anchor_id, 'tieba')
            # 无贴吧地址
            if tieba_url == '':
                data = "spider:{} 无贴吧地址. 主播id:{} time:{}".format(self.name, anchor_id, time_str())
                # logging.error(data)
                item["tieba_fans"] = 0
                yield item
            else:
                # 有贴吧地址，请求贴吧地址
                try:
                    yield scrapy.Request(
                        tieba_url,
                        callback=self.tieba_parse,
                        headers=self.tieba_headers,
                        meta={
                            "item": deepcopy(item),
                            "tieba_url": deepcopy(tieba_url),
                            "anchor_id": deepcopy(anchor_id),
                        }
                    )
                except Exception as error:
                    data = "spider:{} 贴吧地址不正确. 主播id:{} 贴吧地址:{} time:{} error:{}".format(self.name, anchor_id, tieba_url, time_str(), error)
                    logging.error(data)
                    item["tieba_fans"] = 0
                    yield item
        # 有微博地址，请求微博地址
        else:
            try:
                weibo_value = re.findall(r"^\w+://m\.weibo\.cn/\w{1}/(\d+)$", weibo_url)[0]
            except Exception as error:
                data = "spider:{} 该微博地址有误,请检查该微博地址. 主播id:{} 微博地址:{} time:{} error:{}".format(self.name, anchor_id, weibo_url, time_str(), error)
                logging.error(data)
                item["weibo_fans"] = 0
                tieba_url = self.sql.select_from_star(anchor_id, 'tieba')
                # 无贴吧地址
                if tieba_url == '':
                    data = "spider:{} 无贴吧地址. 主播id:{} time:{}".format(self.name, anchor_id, time_str())
                    # logging.error(data)
                    item["tieba_fans"] = 0
                    yield item
                else:
                    # 有贴吧地址，请求贴吧地址
                    yield scrapy.Request(
                        tieba_url,
                        callback=self.tieba_parse,
                        headers=self.tieba_headers,
                        meta={
                            "item": deepcopy(item),
                            "tieba_url": deepcopy(tieba_url),
                            "anchor_id": deepcopy(anchor_id),
                        }
                    )
            else:
                if len(weibo_value) == 10:
                    weibo_api = "https://m.weibo.cn/api/container/getIndex?type=uid&value={}&containerid=100505{}"
                    yield scrapy.Request(
                        weibo_api.format(weibo_value, weibo_value),
                        callback=self.weibo_parse,
                        meta={
                            "anchor_id": deepcopy(anchor_id),
                            "item": deepcopy(item),
                            "url": deepcopy(weibo_url),
                        }
                    )
                if len(weibo_value) == 16:
                    weibo_api = "https://m.weibo.cn/api/container/getIndex?containerid={}"
                    yield scrapy.Request(
                        weibo_api.format(weibo_value),
                        callback=self.weibo_parse,
                        meta={
                            "anchor_id": deepcopy(anchor_id),
                            "item": deepcopy(item),
                            "url": deepcopy(weibo_url),
                        }
                    )

    def weibo_parse(self, response):
        '''
        解析微博粉丝,请求百度指数接口
        :param response:
        :return:
        '''
        if deal_status(response):
            return
        url = response.meta["url"]
        anchor_id = response.meta["anchor_id"]
        item = response.meta["item"]
        try:
            info_dict = json.loads(response.body.decode())
        except Exception as error:
            data = "spider:{} 该微博地址已失效,请核对主播M版微博地址. 主播id:{} 失效url:{} time:{} error:{}".format(self.name, anchor_id, url, time_str(), error)
            logging.error(data)
            item["weibo_fans"] = 0
        else:
            if info_dict["ok"] == 0:
                item["weibo_fans"] = 0
            else:
                item["weibo_fans"] = info_dict["data"]["userInfo"]["followers_count"]
        tieba_url = self.sql.select_from_star(anchor_id, 'tieba')
        # 无贴吧地址
        if tieba_url == '':
            data = "spider:{} 无贴吧地址. 主播id:{} time:{}".format(self.name, anchor_id, time_str())
            # logging.error(data)
            item["tieba_fans"] = 0
            yield item
        # 有贴吧地址
        else:
            yield scrapy.Request(
                tieba_url,
                callback=self.tieba_parse,
                headers=self.tieba_headers,
                meta={
                    "item": deepcopy(item),
                    "tieba_url": deepcopy(tieba_url),
                    "anchor_id": anchor_id,
                }
            )

    def tieba_parse(self, response):
        '''
        获取百度贴吧关注数
        :param response:
        :return:
        '''
        if deal_status(response):
            return
        tieba_url = response.meta["tieba_url"]
        anchor_id = response.meta["anchor_id"]
        item = response.meta["item"]
        try:
            tieba_str = re.findall(r'<span class=\"card_menNum\">(.+)</span>', response.body.decode())[0]
        except Exception as error:
            data = "spider:{} 该贴吧地址网站结构可能出现变化. 主播id:{} 贴吧地址:{} time:{} error:[]".format(self.name, anchor_id, tieba_url, time_str(), error)
            logging.error(data)
            item['tieba_fans'] = 0
        else:
            item["tieba_fans"] = int(tieba_str.replace(',', ''))
        yield item

    def errback_handle(self, failure):
        '''
        请求错误处理
        :param failure:
        :return:
        '''
        logging.critical(repr(failure))
        pass

