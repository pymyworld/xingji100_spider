# -*- coding: utf-8 -*-
# 该爬虫更新各平台游戏分类，查询xj_anchor_category表，忽略以存在游戏分类，将新的游戏分类存库
# 每日运行一次,注意在运行xj_star爬虫时最好先运行本爬虫
import scrapy
import json
import urllib.parse
from ..tools import *
from ..items import Xj_update_gamesItem


class XjUpdateGamesSpider(scrapy.Spider):
    name = 'xj_update_games'
    custom_settings = {
        'ITEM_PIPELINES': {
            'xingji.pipelines.Xj_update_gamesPipeline': 100,
        }
    }
    start_urls = [
        'http://open.douyucdn.cn/api/RoomApi/game',
        'http://www.quanmin.tv/category/',
        'http://www.huya.com/g',
        'http://longzhu.com/games/',
        'http://egame.qq.com/gamelist/',
        'https://www.panda.tv/cate',
        'http://www.zhanqi.tv/games',
        'http://api.vc.bilibili.com/room/v1/area/getRoomList?parent_area_id=2&cate_id=0&area_id=0&sort_type=online&page=1&page_size=30',
        'https://www.huomao.com/game',
    ]

    def start_requests(self):
        for url in self.start_urls:
            if url.find('douyu') > 0:
                yield scrapy.Request(
                    url,
                    # 蚂蚁请求头
                    # headers=generate_sign(),
                    callback=self.douyu_parse,
                    meta={"url": url}
                )
            if url.find('quanmin') > 0:
                yield scrapy.Request(
                    url,
                    callback=self.quanmin_parse,
                )
            if url.find('huya') > 0:
                yield scrapy.Request(
                    url,
                    callback=self.huya_parse,
                )
            if url.find('longzhu') > 0:
                yield scrapy.Request(
                    url,
                    callback=self.longzhu_parse,
                )
            if url.find('egame') > 0:
                yield scrapy.Request(
                    url,
                    callback=self.egame_parse,
                )
            if url.find('panda') > 0:
                yield scrapy.Request(
                    url,
                    callback=self.panda_parse,
                )
            if url.find('zhanqi') > 0:
                yield scrapy.Request(
                    url,
                    callback=self.zhanqi_parse,
                )
            if url.find('bilibili') > 0:
                yield scrapy.Request(
                    url,
                    callback=self.bilibili_parse,
                    dont_filter=True
                )
            if url.find('huomao') > 0:
                yield scrapy.Request(
                    url,
                    callback=self.huomao_parse,
                )

    def douyu_parse(self, response):
        if deal_status(response):
            return
        info_dict = json.loads(response.body.decode())
        if len(info_dict["data"]) > 0:
            for element in info_dict["data"]:
                item = Xj_update_gamesItem()
                item["name"] = element["game_name"]
                yield item

    def quanmin_parse(self, response):
        if deal_status(response):
            return
        a_list = response.xpath("//div[@class='list_w-card_wrap']/a")
        for a in a_list:
            item = Xj_update_gamesItem()
            item["name"] = a.xpath("./p/text()").extract_first()
            yield item

    def huya_parse(self, response):
        if deal_status(response):
            return
        li_list = response.xpath("//ul[@id='js-game-list']/li")
        for li in li_list:
            item = Xj_update_gamesItem()
            item["name"] = li.xpath("./a/h3/text()").extract_first()
            yield item

    def longzhu_parse(self, response):
        if deal_status(response):
            return
        span_list = response.xpath("//div[@class='list-tag-con']/span")
        for span in span_list:
            # 游戏分类列表页导航分类名
            con_name = span.xpath("./text()").extract_first()
            longzhu_id_tag_api = "http://api.plu.cn/tga/games/tag?tag={}&callback=_callbacks_._1038oht".format(con_name)
            yield scrapy.Request(
                longzhu_id_tag_api,
                callback=self.longzhu_get_game,
                dont_filter=True,
            )

    def longzhu_get_game(self, response):
        if deal_status(response):
            return
        info_json = re.match(r"^_callbacks_\._1038oht\((.+)\)$", response.body.decode()).group(1)
        info_dict = json.loads(info_json)
        items_list = info_dict["data"]["items"]
        if len(items_list) != 0:
            for items in items_list:
                item = Xj_update_gamesItem()
                item["name"] = items["game"]["name"]
                yield item

    def egame_parse(self, response):
        if deal_status(response):
            return
        li_list = response.xpath("//ul[@class='livelist-mod']/li")
        for li in li_list:
            item = Xj_update_gamesItem()
            item["name"] = li.xpath("./a/p/text()").extract_first()
            yield item

    def panda_parse(self, response):
        if deal_status(response):
            return
        li_list = response.xpath("//div[@class='sort-container']/ul/li")
        for li in li_list:
            item = Xj_update_gamesItem()
            item["name"] = li.xpath(".//div[@class='cate-title']/text()").extract_first().strip()
            yield item

    def zhanqi_parse(self, response):
        if deal_status(response):
            return
        li_list = response.xpath("//ul[@id='game-list-panel']/li")
        for li in li_list:
            item = Xj_update_gamesItem()
            item["name"] = li.xpath("./a/p/text()").extract_first()
            yield item

    def bilibili_parse(self, response):
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
            item = Xj_update_gamesItem()
            item["name"] = data["area_name"]
            yield item
        # 下一页
        next_live_api = "http://api.vc.bilibili.com/room/v1/area/getRoomList?parent_area_id=2&cate_id=0&area_id=0&sort_type=online&page={}&page_size=30"
        yield scrapy.Request(
            next_live_api.format(int(page) + 1),
            callback=self.bilibili_parse,
            dont_filter=True,
        )

    def huomao_parse(self, response):
        if deal_status(response):
            return
        div_list = response.xpath("//div[@id='gamelist']/div")
        for div in div_list:
            item = Xj_update_gamesItem()
            item["name"] = div.xpath(".//p/text()").extract_first()
            yield item

