# -*- coding: utf-8 -*-
# 该爬虫抓取各平台主播基本信息，入库条件为在线热度大于2w，图片保存在settings.py配置的图片路径中
# 斗鱼存在被ban情况，需要使用代理
import scrapy
import re
import math
import urllib.parse
from ..sql_handle import *
import logging
import time
from copy import deepcopy
import json
from ..items import Xj_starItem
from ..tools import *


class XjStarSpider(scrapy.Spider):
    name = 'xj_star'
    custom_settings = {
        'ITEM_PIPELINES': {
            'xingji.pipelines.Xj_starPipeline': 100,
        }
    }
    start_urls = [
        'http://www.douyu.com/directory',
        'http://www.quanmin.tv/category/',
        'http://www.huya.com/g',
        'http://longzhu.com/games/',
        'http://egame.qq.com/gamelist/',
        'https://www.panda.tv/cate',
        'http://www.zhanqi.tv/games',
        'http://api.vc.bilibili.com/room/v1/area/getRoomList?parent_area_id=2&cate_id=0&area_id=0&sort_type=online&page=1&page_size=30',
        'https://www.huomao.com/channels/channel.json?page=1&game_url_rule=all',
    ]
    sql = Sqlhandle()
    douyu_id = 11
    quanmin_id = 8
    huya_id = 7
    longzhu_id = 4
    egame_id = 14
    panda_id = 10
    zhanqi_id = 9
    bilibili_id = 16
    huomao_id = 6
    # 主播录入数据库条件
    save_limit = 20000

    def start_requests(self):
        for url in self.start_urls:
            if url.find('douyu') > 0:
                yield scrapy.Request(
                    url,
                    # 蚂蚁请求头
                    # headers=generate_sign(),
                    callback=self.douyu_fir_list,
                    meta={"url": url},
                    # errback=self.errback_handle,
                )
            if url.find('quanmin') > 0:
                yield scrapy.Request(
                    url,
                    callback=self.quanmin_fir_list
                )
            if url.find('huya') > 0:
                yield scrapy.Request(
                    url,
                    callback=self.huya_fir_list
                )
            if url.find('longzhu') > 0:
                yield scrapy.Request(
                    url,
                    callback=self.longzhu_fir_list,
                )
            if url.find('egame') > 0:
                yield scrapy.Request(
                    url,
                    callback=self.egame_fir_list
                )
            if url.find('panda') > 0:
                yield scrapy.Request(
                    url,
                    callback=self.panda_fir_parse
                )
            if url.find('zhanqi') > 0:
                yield scrapy.Request(
                    url,
                    callback=self.zhanqi_fir_parse
                )
            if url.find('bilibili') > 0:
                yield scrapy.Request(
                    url,
                    callback=self.bilibili_live_list,
                    dont_filter=True
                )
            if url.find('huomao') > 0:
                yield scrapy.Request(
                    url,
                    # 蚂蚁请求头
                    # headers=generate_sign(),
                    callback=self.huomao_parse,
                    dont_filter=True,
                )

    # ------------斗鱼------------
    def douyu_fir_list(self, response):
        '''
        获取一级游戏分类列表页，挑选游戏分类
        :param response:
        :return:
        '''
        if deal_status(response):
            return
        url = response.meta["url"]
        # 一级分类url参数列表
        nav_list = ["djry?isAjax=1", "syxx?isAjax=1",  "PCgame?isAjax=1"]
        for nav in nav_list:
            full_url = url + '/index/' + nav
            yield scrapy.Request(
                full_url,
                # 蚂蚁请求头
                # headers=generate_sign(),
                callback=self.douyu_sec_list,
                # errback=self.errback_handle,
            )

    def douyu_sec_list(self, response):
        '''
        获取二级游戏分类列表页,查询xj_anchor_category获得游戏分类id,若无id则添加
        category_id为xj_anchor_category中游戏分类id
        cate_id为斗鱼官方游戏分类id
        :param response:
        :return:
        '''
        if deal_status(response):
            return
        a_list = response.xpath("//li/a")
        for a in a_list:
            game = a.xpath("./p/text()").extract_first()
            # 获取category_id作为xj_star字段
            # category_id = self.sql.deal_game(game, self.douyu_id)
            category_id = self.sql.select_game_id(game)
            if category_id is None:
                data = "spider:{} 游戏分类库中没有该游戏分类!!!暂时将游戏分类设为默认值''. 游戏名:{} 平台id:{} time:{}".format(self.name, game, self.douyu_id, time_str())
                logging.error(data)
                category_id = ''
            # 请求斗鱼所有游戏分类接口
            game_api = "http://open.douyucdn.cn/api/RoomApi/game"
            # time.sleep(0.4)
            yield scrapy.Request(
                game_api,
                # 蚂蚁请求头
                # headers=generate_sign(),
                dont_filter=True,
                callback=self.douyu_get_cate,
                # errback=self.errback_handle,
                meta={
                    "category_id": deepcopy(category_id),
                    "game": deepcopy(game)
                }
            )

    def douyu_get_cate(self, response):
        '''
        拿game与game_name作比较，获得cate_id,构建接口请求游戏分类下的房间列表
        :param response:
        :return:
        '''
        if deal_status(response):
            return
        category_id = response.meta["category_id"]
        game = response.meta["game"]
        game_dict = json.loads(response.body.decode())
        for data in game_dict["data"]:
            # 判断xj_anchor_category中name与game_name是否一直,提取官方cate_id
            if game == data["game_name"]:
                cate_id = data["cate_id"]
                # 游戏分类下房间列表接口
                live_list_api = "http://open.douyucdn.cn/api/RoomApi/live/" + str(cate_id)
                # time.sleep(0.4)
                yield scrapy.Request(
                    live_list_api,
                    # 蚂蚁请求头
                    # headers=generate_sign(),
                    dont_filter=True,
                    callback=self.douyu_detail,
                    # errback=self.errback_handle,
                    meta={
                        "category_id": deepcopy(category_id),
                    }
                )

    def douyu_detail(self, response):
        '''
        提取主要信息,请求详情页获取头像
        :param response:
        :return:
        '''
        if deal_status(response):
            return
        category_id = response.meta["category_id"]
        info_dict = json.loads(response.body.decode())
        for data in info_dict["data"]:
            # 入库条件：热度大于2w
            if data["online"] < self.save_limit:
                continue
            else:
                name = data["nickname"]
                view_num = data["online"]
                live_url = data["url"]
                yield scrapy.Request(
                    live_url,
                    # 蚂蚁请求头
                    # headers=generate_sign(),
                    callback=self.douyu_avatar_url,
                    # errback=self.errback_handle,
                    meta={
                        "category_id": deepcopy(category_id),
                        "name": deepcopy(name),
                        "view_num": deepcopy(view_num),
                        "live_url": deepcopy(live_url)
                    }
                )

    def douyu_avatar_url(self, response):
        '''
        请求头像url,保存图片
        :param response:
        :return:
        '''
        if deal_status(response):
            return
        item = Xj_starItem()
        item["platform_id"] = self.douyu_id
        item["category_id"] = response.meta["category_id"]
        item["name"] = response.meta["name"]
        item["view_num"] = response.meta["view_num"]
        item["live_url"] = response.meta["live_url"]
        avatar_url = response.xpath("//div[@id='anchor-info']/div[@class='anchor-pic fl']/img/@src").extract_first()
        item["avatar"] = get_avatar(avatar_url, "douyu")
        yield item

    # ------------全民------------
    def quanmin_fir_list(self, response):
        '''
        游戏分类列表页
        获取category_id
        :param response:
        :return:
        '''
        if deal_status(response):
            return
        a_list = response.xpath("//div[@class='list_w-card_wrap']/a")
        for a in a_list:
            room_href = a.xpath("./@href").extract_first()
            game = a.xpath("./p/text()").extract_first()
            # category_id = self.sql.deal_game(game, self.quanmin_id)
            category_id = self.sql.select_game_id(game)
            if category_id is None:
                data = "spider:{} 游戏分类库中没有该游戏分类!!!暂时将游戏分类设为默认值''. 游戏名:{} 平台id:{} time:{}".format(self.name, game, self.quanmin_id, time_str())
                logging.error(data)
                category_id = ''
            full_room_list = "https://www.quanmin.tv" + room_href
            # 全民星秀
            if "s.quanmin.tv" in full_room_list:
                yield scrapy.Request(
                    full_room_list,
                    callback=self.quanmin_xingxiu,
                    dont_filter=True,
                    meta={
                        "category_id": deepcopy(category_id),
                    }
                )
            # 全民Showing
            if "showing" in full_room_list:
                yield scrapy.Request(
                    full_room_list,
                    callback=self.quanmin_showing,
                    dont_filter=True,
                    meta={
                        "category_id": deepcopy(category_id),
                    }
                )
            # 其他分类
            yield scrapy.Request(
                full_room_list,
                callback=self.quanmin_sec_list,
                dont_filter=True,
                meta={
                    "category_id": deepcopy(category_id),
                }
            )

    def quanmin_sec_list(self, response):
        '''
        直播间列表页
        获取name,view_num,live_url
        :param response:
        :return:
        '''
        if deal_status(response):
            return
        category_id = response.meta["category_id"]
        li_list = response.xpath("//div[@id='list_w-video-list']/div/ul/li")
        for li in li_list:
            name = li.xpath(".//span[@class='common_w-card_host-name']/text()").extract_first()
            view_num = li.xpath(".//span[@class='common_w-card_views-num']/text()").extract_first()
            url = li.xpath(".//a[@class='common_w-card_href']/@href").extract_first()
            if url is None or view_num is None:
                continue
            # 入库条件
            if int(view_num) >= self.save_limit:
                live_url = "http:" + url
                yield scrapy.Request(
                    live_url,
                    callback=self.quanmin_detail,
                    dont_filter=True,
                    meta={
                        "category_id": deepcopy(category_id),
                        "name": deepcopy(name),
                        "view_num": deepcopy(view_num),
                        "live_url": deepcopy(live_url)
                    }
                )
        # 下一页
        a_next = response.xpath("//a[@class='list_w-paging_btn list_w-paging_next ']/@href").extract_first()
        if a_next is not None:
            # 存在下一页
            next_url = "http://www.quanmin.tv" + a_next
            yield scrapy.Request(
                next_url,
                callback=self.quanmin_sec_list,
                meta={
                    "category_id": deepcopy(category_id),
                }
            )

    def quanmin_xingxiu(self, response):
        '''
        全民星秀列表页
        :param response:
        :return:
        '''
        if deal_status(response):
            return
        category_id = response.meta["category_id"]
        a_list = response.xpath("//div[@class='s_p-home_videos']/div/div/a")
        for a in a_list:
            name = a.xpath(".//span[@class='s_w-video_name']/text()").extract_first()
            view_num = a.xpath(".//span[@class='s_w-video_num']/text()").extract_first()
            live_url = "http:" + a.xpath("./@href").extract_first()
            if int(view_num) >= self.save_limit:
                yield scrapy.Request(
                    live_url,
                    callback=self.quanmin_detail,
                    dont_filter=True,
                    meta={
                        "category_id": deepcopy(category_id),
                        "name": deepcopy(name),
                        "view_num": deepcopy(view_num),
                        "live_url": deepcopy(live_url)
                    }
                )

    def quanmin_showing(self, response):
        '''
        全民showing列表页
        :param response:
        :return:
        '''
        if deal_status(response):
            return
        category_id = response.meta["category_id"]
        li_list = response.xpath("//div[@id='list_w-video-list']/div[@class='list_w-videos double_line']//li[@class='list_w-video list_w-video_showing']")
        for li in li_list:
            name = li.xpath(".//span[@class='list_w-card-showing_host-name']/text()").extract_first()
            view_num = re.findall(r'\d+', li.xpath(".//span[@class='list_w-card-showing_views-num']/text()").extract_first())[0]
            live_url = "http:" + li.xpath(".//a[@class='list_w-card-showing_href']/@href").extract_first()
            if int(view_num) >= self.save_limit:
                yield scrapy.Request(
                    live_url,
                    callback=self.quanmin_detail,
                    dont_filter=True,
                    meta={
                        "category_id": deepcopy(category_id),
                        "name": deepcopy(name),
                        "view_num": deepcopy(view_num),
                        "live_url": deepcopy(live_url)
                    }
                )

    def quanmin_detail(self, response):
        '''
        直播间详情页
        获取avatar,获取头像
        :param response:
        :return:
        '''
        if deal_status(response):
            return
        item = Xj_starItem()
        item["platform_id"] = self.quanmin_id
        item["category_id"] = response.meta["category_id"]
        item["name"] = response.meta["name"]
        item["view_num"] = response.meta["view_num"]
        item["live_url"] = response.meta["live_url"]
        avatar_url = response.xpath(".//img[@class='room_w-title_img']/@src").extract_first()
        if avatar_url == "":
            return
        if avatar_url.find("static.quanmin.tv") > 0:
            avatar_url = "http:" + avatar_url
            # 设置日志
            data = "spider:{} date:{},paltform:{},message:{}没有设置头像或该页面不存在,获取的是平台默认图片,直播间地址{}".format(self.name, time_str(), self.quanmin_id, item["name"], item["live_url"])
            logging.error(data)
        item["avatar"] = get_avatar(avatar_url, "quanmin")
        if item["avatar"] is None:
            item["avatar"] = ""
            data = "spider:{} date:{},platform:{},message:{}的头像地址请求失败,直播地址为{}".format(self.name, time_str(), self.quanmin_id, item["name"], item["live_url"])
            logging.error(data)
        yield item

    # ------------虎牙------------
    def huya_fir_list(self, response):
        '''
        游戏分类列表页
        :param response:
        :return:
        '''
        if deal_status(response):
            return
        li_list = response.xpath("//ul[@id='js-game-list']/li")
        for li in li_list:
            game = li.xpath("./a/h3/text()").extract_first()
            # 获取虎牙官方游戏分类id
            gid = li.xpath("./@gid").extract_first()
            # category_id = self.sql.deal_game(game, self.huya_id)
            category_id = self.sql.select_game_id(game)
            if category_id is None:
                data = "spider:{} 游戏分类库中没有该游戏分类!!!暂时将游戏分类设为默认值''. 游戏名:{} 平台id:{} time:{}".format(self.name, game, self.huya_id, time_str())
                logging.error(data)
                category_id = ''
            # 虎牙直播间列表页api
            huya_api = "http://www.huya.com/cache.php?m=LiveList&do=getLiveListByPage&gameId={}&tagAll=0&page=1".format(gid)
            yield scrapy.Request(
                huya_api,
                callback=self.huya_deal_api,
                meta={
                    "category_id": deepcopy(category_id),
                    "gid": deepcopy(gid),
                }
            )

    def huya_deal_api(self, response):
        '''
        直播间列表页api返回结果处理
        :param response:
        :return:
        '''
        if deal_status(response):
            return
        category_id = response.meta["category_id"]
        gid = response.meta["gid"]
        info_dict = json.loads(response.body.decode())
        # 该分类下直播间总页数
        total_page = info_dict["data"]["totalPage"]
        page = info_dict["data"]["page"]
        datas_list = info_dict["data"]["datas"]
        for datas in datas_list:
            item = Xj_starItem()
            item["view_num"] = datas["totalCount"]
            if int(item["view_num"]) >= self.save_limit:
                item["platform_id"] = self.huya_id
                item["category_id"] = category_id
                item["live_url"] = "http://www.huya.com/" + datas["profileRoom"]
                item["name"] = datas["nick"]
                avatar_url = datas["avatar180"]
                item["avatar"] = get_avatar(avatar_url, "huya")
                yield item
        # 下一页
        if page < total_page:
            huya_api = "http://www.huya.com/cache.php?m=LiveList&do=getLiveListByPage&gameId={}&tagAll=0&page={}".format(gid, page + 1)
            yield scrapy.Request(
                huya_api,
                callback=self.huya_deal_api,
                meta={
                    "category_id": deepcopy(category_id),
                    "gid": deepcopy(gid),
                }
            )

    # ------------龙珠------------
    def longzhu_fir_list(self, response):
        '''
        游戏分类列表页
        :param response:
        :return:
        '''
        if deal_status(response):
            return
        span_list = response.xpath("//div[@class='list-tag-con']/span")
        for span in span_list:
            # 游戏分类列表页导航分类名
            con_name = span.xpath("./text()").extract_first()
            longzhu_id_tag_api = "http://api.plu.cn/tga/games/tag?tag={}&callback=_callbacks_._1038oht".format(con_name)
            yield scrapy.Request(
                longzhu_id_tag_api,
                callback=self.longzhu_get_id,
                dont_filter=True,
            )

    def longzhu_get_id(self, response):
        '''
        获取龙珠官方游戏分类id，构建api请求直播间列表信息
        :param response:
        :return:
        '''
        if deal_status(response):
            return
        info_json = re.match(r"^_callbacks_\._1038oht\((.+)\)$", response.body.decode()).group(1)
        info_dict = json.loads(info_json)
        items_list = info_dict["data"]["items"]
        if len(items_list) != 0:
            for items in items_list:
                game = items["game"]["name"]
                # 官方游戏分类id
                game_id = items["game"]["id"]
                tag = items["game"]["tag"]
                # category_id = self.sql.deal_game(game, self.longzhu_id)
                category_id = self.sql.select_game_id(game)
                if category_id is None:
                    data = "spider:{} 游戏分类库中没有该游戏分类!!!暂时将游戏分类设为默认值''. 游戏名:{} 平台id:{} time:{}".format(self.name, game, self.longzhu_id, time_str())
                    logging.error(data)
                    category_id = ''
                # 王者荣耀api为http://api.longzhu.com/wzry/streams,其他均为http://api.longzhu.com/tga/streams
                # 直播间列表信息api
                if tag == 'wzry':
                    live_list_api = "http://api.longzhu.com/wzry/streams?max-results=18&start-index=23&sort-by=top&filter=0&game={}&lzv=undefined&callback=_callbacks_._pzp36v".format(game_id)
                    yield scrapy.Request(
                        live_list_api,
                        callback=self.longzhu_live_list_deal,
                        dont_filter=True,
                        meta={
                            "category_id": deepcopy(category_id),
                            "tag": deepcopy(tag),
                            "game_id": deepcopy(game_id),
                        }
                    )
                else:
                    live_list_api = "http://api.longzhu.com/tga/streams?max-results=18&start-index=23&sort-by=top&filter=0&game={}&lzv=undefined&callback=_callbacks_._pzp36v".format(game_id)
                    yield scrapy.Request(
                        live_list_api,
                        callback=self.longzhu_live_list_deal,
                        dont_filter=True,
                        meta={
                            "category_id": deepcopy(category_id),
                            "tag": deepcopy(tag),
                            "game_id": deepcopy(game_id),
                        }
                    )

    def longzhu_live_list_deal(self, response):
        '''
        解析直播间列表页api返回数据
        :param response:
        :return:
        '''
        if deal_status(response):
            return
        category_id = response.meta["category_id"]
        tag = response.meta["tag"]
        game_id = response.meta["game_id"]
        info_json = re.match(r"^_callbacks_\._pzp36v\((.+)\)$", response.body.decode()).group(1)
        info_dict = json.loads(info_json)
        items_list = info_dict["data"]["items"]
        totalItems = info_dict["data"]["totalItems"]
        offset = info_dict["data"]["offset"]
        if len(items_list) > 0:
            for items in items_list:
                room_id = items["channel"]["id"]
                name = items["channel"]["name"]
                live_url = items["channel"]["url"]
                avatar_url = items["channel"]["avatar"]
                room_api = "http://roomapicdn.longzhu.com/room/roomstatus?roomid={}&lzv=1".format(room_id)
                yield scrapy.Request(
                    room_api,
                    callback=self.longzhu_detail,
                    headers=longzhu_header(),
                    dont_filter=True,
                    meta={
                        "category_id": deepcopy(category_id),
                        "name": deepcopy(name),
                        "live_url": deepcopy(live_url),
                        "avatar_url": deepcopy(avatar_url),
                    }
                )
        # 下一页
        if int(offset) <= totalItems:
            index = int(offset) + 18
            if tag == 'wzry':
                live_list_api = "http://api.longzhu.com/wzry/streams?max-results=18&start-index={}&sort-by=top&filter=0&game={}&lzv=undefined&callback=_callbacks_._pzp36v"
                yield scrapy.Request(
                    live_list_api.format(index, game_id),
                    callback=self.longzhu_live_list_deal,
                    dont_filter=True,
                    meta={
                        "category_id": deepcopy(category_id),
                        "tag": deepcopy(tag),
                        "game_id": deepcopy(game_id),
                    }
                )
            else:
                live_list_api = "http://api.longzhu.com/tga/streams?max-results=18&start-index={}&sort-by=top&filter=0&game={}&lzv=undefined&callback=_callbacks_._pzp36v"
                yield scrapy.Request(
                    live_list_api.format(index, game_id),
                    callback=self.longzhu_live_list_deal,
                    dont_filter=True,
                    meta={
                        "category_id": deepcopy(category_id),
                        "tag": deepcopy(tag),
                        "game_id": deepcopy(game_id),
                    }
                )

    def longzhu_detail(self, response):
        '''
        直播间详情页信息提取
        :param response:
        :return:
        '''
        if deal_status(response):
            return
        info_dict = json.loads(response.body.decode())
        item = Xj_starItem()
        item["view_num"] = info_dict["OnlineCount"]
        if item["view_num"] >= self.save_limit:
            item["platform_id"] = self.longzhu_id
            item["category_id"] = response.meta["category_id"]
            item["name"] = response.meta["name"]
            item["live_url"] = response.meta["live_url"]
            avatar_url = response.meta["avatar_url"]
            item["avatar"] = get_avatar(avatar_url, "longzhu")
            yield item

    # ------------企鹅------------
    def egame_fir_list(self, response):
        '''
        企鹅游戏分类列表页，提取layoutid构造api
        :param response:
        :return:
        '''
        if deal_status(response):
            return
        li_list = response.xpath("//ul[@class='livelist-mod']/li")
        for li in li_list:
            game = li.xpath("./a/p/text()").extract_first()
            # category_id = self.sql.deal_game(game, self.egame_id)
            category_id = self.sql.select_game_id(game)
            if category_id is None:
                data = "spider:{} 游戏分类库中没有该游戏分类!!!暂时将游戏分类设为默认值''. 游戏名:{} 平台id:{} time:{}".format(self.name, game, self.egame_id, time_str())
                logging.error(data)
                category_id = ''
            layoutid = re.findall(r'^/livelist\?layoutid=(.+)$', li.xpath("./a/@href").extract_first())[0]
            live_list_api = 'http://share.egame.qq.com/cgi-bin/pgg_live_async_fcgi?' \
                            'param={"key":{"module":"pgg_live_read_svr","method":"get_live_list","param":{"layout_id":"%s","page_num":1,"page_size":30}}}' \
                            '&app_info={"platform":4,"terminal_type":2,"egame_id":"egame_official"}' \
                            '&g_tk=&p_tk=&tt=1' % layoutid
            yield scrapy.Request(
                live_list_api,
                callback=self.egame_live_list,
                meta={
                    "category_id": deepcopy(category_id),
                    "layoutid": deepcopy(layoutid),
                }
            )

    def egame_live_list(self, response):
        '''
        获取企鹅直播间信息
        :param response:
        :return:
        '''
        if deal_status(response):
            return
        category_id = response.meta["category_id"]
        layoutid = response.meta["layoutid"]
        # url解码
        code_url = urllib.parse.unquote(response.url)
        page = re.findall(r'\"page_num\":(\d+),\"page_size\"', code_url)[0]
        info_dict = json.loads(response.body.decode())
        total_lives = info_dict["data"]["key"]["retBody"]["data"]["total"]
        live_list = info_dict["data"]["key"]["retBody"]["data"]["live_data"]["live_list"]
        for live in live_list:
            item = Xj_starItem()
            item["view_num"] = live["online"]
            if item["view_num"] >= self.save_limit:
                item["platform_id"] = self.egame_id
                item["category_id"] = category_id
                item["name"] = live["anchor_name"]
                item["live_url"] = "http://egame.qq.com/{}".format(live["anchor_id"])
                avatar_url = live["anchor_face_url"]
                item["avatar"] = get_avatar(avatar_url, "egame")
                yield item
        # 下一页
        total_pages = math.ceil(total_lives / 30)
        if int(page) < total_pages:
            next_page = int(page) + 1
            next_live_api = 'http://share.egame.qq.com/cgi-bin/pgg_live_async_fcgi?' \
                            'param={"key":{"module":"pgg_live_read_svr","method":"get_live_list","param":{"layout_id":"%s","page_num":%s,"page_size":30}}}' \
                            '&app_info={"platform":4,"terminal_type":2,"egame_id":"egame_official"}' \
                            '&g_tk=&p_tk=&tt=1' % (layoutid, next_page)
            yield scrapy.Request(
                next_live_api,
                callback=self.egame_live_list,
                meta={
                    "category_id": deepcopy(category_id),
                    "layoutid": deepcopy(layoutid),
                }
            )

    # ------------熊猫------------
    def panda_fir_parse(self, response):
        '''
        游戏分类列表页
        :param response:
        :return:
        '''
        if deal_status(response):
            return
        li_list = response.xpath("//div[@class='sort-container']/ul/li")
        for li in li_list:
            game = li.xpath(".//div[@class='cate-title']/text()").extract_first().strip()
            # category_id = self.sql.deal_game(game, self.panda_id)
            category_id = self.sql.select_game_id(game)
            if category_id is None:
                data = "spider:{} 游戏分类库中没有该游戏分类!!!暂时将游戏分类设为默认值''. 游戏名:{} 平台id:{} time:{}".format(self.name, game, self.panda_id, time_str())
                logging.error(data)
                category_id = ''
            game_cate_list = re.findall(r"^/cate/(.+)$", li.xpath("./a/@href").extract_first())
            # 滤掉熊猫自营娱乐分类
            if len(game_cate_list) > 0:
                game_cate = game_cate_list[0]
                live_list_api = "https://www.panda.tv/ajax_sort?token=&pageno=1&pagenum=120&classification={}&order=top&_={}".format(game_cate, int(round(time.time()*1000)))
                yield scrapy.Request(
                    live_list_api,
                    callback=self.panda_live_list,
                    meta={
                        "category_id": deepcopy(category_id),
                    }
                )

    def panda_live_list(self, response):
        '''
        解析直播间列表页接口返回数据
        :param response:
        :return:
        '''
        if deal_status(response):
            return
        category_id = response.meta["category_id"]
        info_dict = json.loads(response.body.decode())
        items_list = info_dict["data"]["items"]
        if len(items_list) > 0:
            for items in items_list:
                item = Xj_starItem()
                item["view_num"] = items["person_num"]
                if int(item["view_num"]) > self.save_limit:
                    room_id = items["id"]
                    item["platform_id"] = self.panda_id
                    item["category_id"] = category_id
                    item["live_url"] = "https://www.panda.tv/{}".format(room_id)
                    item["name"] = items["userinfo"]["nickName"]
                    avatar_url = items["userinfo"]["avatar"]
                    item["avatar"] = get_avatar(avatar_url, "panda")
                    yield item

    # ------------战旗-------------
    def zhanqi_fir_parse(self, response):
        '''
        游戏分裂列表页
        :param response:
        :return:
        '''
        if deal_status(response):
            return
        li_list = response.xpath("//ul[@id='game-list-panel']/li")
        for li in li_list:
            game = li.xpath("./a/p/text()").extract_first()
            # category_id = self.sql.deal_game(game, self.zhanqi_id)
            category_id = self.sql.select_game_id(game)
            if category_id is None:
                data = "spider:{} 游戏分类库中没有该游戏分类!!!暂时将游戏分类设为默认值''. 游戏名:{} 平台id:{} time:{}".format(self.name, game, self.zhanqi_id, time_str())
                logging.error(data)
                category_id = ''
            data_id = li.xpath("./@data-id").extract_first()
            live_list_api = "http://www.zhanqi.tv/api/static/v2.1/game/live/{}/30/1.json".format(data_id)
            yield scrapy.Request(
                live_list_api,
                callback=self.zhanqi_live_list,
                dont_filter=True,
                meta={
                    "category_id": deepcopy(category_id),
                    "data_id": deepcopy(data_id)
                }
            )

    def zhanqi_live_list(self, response):
        '''
        解析直播间列表页信息
        :param response:
        :return:
        '''
        if deal_status(response):
            return
        category_id = response.meta["category_id"]
        data_id = response.meta["data_id"]
        # url解码
        code_url = urllib.parse.unquote(response.url)
        page = re.findall(r'/(\d+)\.json$', code_url)[0]
        info_dict = json.loads(response.body.decode())
        total_rooms = info_dict["data"]["cnt"]
        room_list = info_dict["data"]["rooms"]
        if len(room_list) > 0:
            for room in room_list:
                name = room["nickname"]
                live_url = "http://www.zhanqi.tv{}".format(room["url"])
                view_num = room["online"]
                if int(view_num) > self.save_limit:
                    yield scrapy.Request(
                        live_url,
                        callback=self.zhanqi_detail,
                        dont_filter=True,
                        meta={
                            "category_id": deepcopy(category_id),
                            "name": deepcopy(name),
                            "live_url": deepcopy(live_url),
                            "view_num": deepcopy(view_num)
                        }
                    )
        # 下一页
        total_pages = math.ceil(total_rooms / 30)
        if int(page) < total_pages:
            next_live_api = "http://www.zhanqi.tv/api/static/v2.1/game/live/{}/30/{}.json".format(data_id, int(page)+1)
            yield scrapy.Request(
                next_live_api,
                callback=self.zhanqi_live_list,
                dont_filter=True,
                meta={
                    "category_id": deepcopy(category_id),
                    "data_id": deepcopy(data_id),
                }
            )

    def zhanqi_detail(self, response):
        '''
        从直播间详情获取avatar_url
        :param response:
        :return:
        '''
        if deal_status(response):
            return
        item = Xj_starItem()
        item["platform_id"] = self.zhanqi_id
        item["category_id"] = response.meta["category_id"]
        item["name"] = response.meta["name"]
        item["live_url"] = response.meta["live_url"]
        item["view_num"] = response.meta["view_num"]
        avatar_url = response.xpath("//div[@id='js-room-anchor-info-area']/div[@class='img-box']/img/@src").extract_first()
        item["avatar"] = get_avatar(avatar_url, "zhanqi")
        yield item

    # ------------B站------------
    def bilibili_live_list(self, response):
        '''
        解析直播间列表信息
        :param response:
        :return:
        '''
        if deal_status(response):
            return
        info_dict = json.loads(response.body.decode())
        data_list = info_dict["data"]
        # 若无内容，停止执行
        if len(data_list) == 0:
            return
        # url解码
        code_url = urllib.parse.unquote(response.url)
        page = re.findall(r'&page=(\d+)&page_size=30$', code_url)[0]
        for data in data_list:
            item = Xj_starItem()
            item["view_num"] = data["online"]
            if item["view_num"] >= self.save_limit:
                game = data["area_name"]
                item["platform_id"] = self.bilibili_id
                item["category_id"] = self.sql.select_game_id(game)
                if item["category_id"] is None:
                    data_str = "spider:{} 游戏分类库中没有该游戏分类!!!暂时将游戏分类设为默认值''. 游戏名:{} 平台id:{} time:{}".format(self.name, game, self.bilibili_id, time_str())
                    logging.error(data_str)
                    item["category_id"] = ''
                item["name"] = data["uname"]
                item["live_url"] = "http://live.bilibili.com{}".format(data["link"])
                avatar_url = data["face"]
                item["avatar"] = get_avatar(avatar_url, "bilibili")
                yield item
        # 下一页
        next_live_api = "http://api.vc.bilibili.com/room/v1/area/getRoomList?parent_area_id=2&cate_id=0&area_id=0&sort_type=online&page={}&page_size=30"
        yield scrapy.Request(
            next_live_api.format(int(page)+1),
            callback=self.bilibili_live_list,
            dont_filter=True,
        )

    # ------------火猫------------
    def huomao_parse(self, response):
        if deal_status(response):
            return
        info_dict = json.loads(response.body.decode())
        if info_dict["code"] == 100:
            channel_list = info_dict["data"]["channelList"]
            for channel in channel_list:
                item = Xj_starItem()
                item["view_num"] = channel["originviews"]
                if int(item["view_num"]) > self.save_limit:
                    game = channel["gameCname"]
                    item["platform_id"] = self.huomao_id
                    item["category_id"] = self.sql.select_game_id(game)
                    if item["category_id"] is None:
                        data_str = "spider:{} 游戏分类库中没有该游戏分类!!!暂时将游戏分类设为默认值''. 游戏名:{} 平台id:{} time:{}".format(self.name, game, self.huomao_id, time_str())
                        logging.error(data_str)
                        item["category_id"] = ''
                    item["name"] = channel["nickname"]
                    # 去除未转义字符
                    if "'" in item["name"]:
                        item["name"] = item["name"].replace("'", "")
                    if '"' in item["name"]:
                        item["name"] = item["name"].replace('"', '')
                    item["live_url"] = "https://www.huomao.com/{}".format(channel["room_number"])
                    yield scrapy.Request(
                        item["live_url"],
                        callback=self.huomao_avatar,
                        # 蚂蚁请求头
                        # headers=generate_sign(),
                        meta={
                            "item": deepcopy(item)
                        }
                    )

    def huomao_avatar(self, response):
        if deal_status(response):
            return
        item = response.meta["item"]
        avatar = re.findall(r'"normal":"(.*?)"', response.body.decode())
        if len(avatar) > 0:
            avatar_url = avatar[0].replace('\\', '')
            item["avatar"] = get_avatar(avatar_url, "huomao")
            yield item

    def errback_handle(self, failure):
        '''
        请求错误处理
        :param failure:
        :return:
        '''
        logging.critical(repr(failure))
        pass
