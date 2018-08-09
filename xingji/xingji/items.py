# -*- coding: utf-8 -*-

# Define here the models for your scraped items
#
# See documentation in:
# http://doc.scrapy.org/en/latest/topics/items.html

import scrapy


class Xj_starItem(scrapy.Item):
    # define the fields for your item here like:
    # name = scrapy.Field()
    '''主播基础数据'''
    category_id = scrapy.Field()    # 游戏分类id
    platform_id = scrapy.Field()    # 平台id
    name = scrapy.Field()   # 主播名
    avatar = scrapy.Field()    # 头像
    live_url = scrapy.Field()   # 直播地址
    view_num = scrapy.Field()   # 抓取时的在线热度
    add_time = scrapy.Field()   # 入库时间
    update_time = scrapy.Field()    # 更新时间
    is_publish = scrapy.Field()    # 是否上架,默认1


class Xj_update_gamesItem(scrapy.Item):
    '''更新游戏分类'''
    name = scrapy.Field()   # 游戏名
    add_time = scrapy.Field()   # 添加时间
    update_time = scrapy.Field()    # 更新时间


class Xj_view_liveItem(scrapy.Item):
    '''抓取开关播时间和在线人数'''
    anchor_id = scrapy.Field()  # 主播id:xj_anchor_live,xj_count_anchor_view
    data = scrapy.Field()    # 直播日期:xj_anchor_live,xj_count_anchor_view
    view_num = scrapy.Field()   # 直播在线人数:xj_count_anchor_view
    update_time = scrapy.Field()    # 更新时间:xj_count_anchor_view
    start_time = scrapy.Field()    # 直播开始时间:xj_anchor_live
    end_time = scrapy.Field()   # 直播结束时间:xj_anchor_live


class Xj_anchor_dataItem(scrapy.Item):
    '''每日记录'''
    anchor_id = scrapy.Field()  # 主播id，查库
    weibo_fans = scrapy.Field()  # 微博粉丝
    tieba_fans = scrapy.Field()  # 贴吧粉丝
    followers = scrapy.Field()  # 主播直播间订阅量
    quotient = scrapy.Field()   # 百度指数
    danmu = scrapy.Field()      # 弹幕量
    # live_time = scrapy.Field()  # 直播时长,通过子表xj_anchor_live得到
    # views = scrapy.Field()  # 观看人数，通过子表xj_count_anchor_view得到
    # gift = scrapy.Field()   # 礼物，通过子表xj_count_anchor_gift得到
    category_id = scrapy.Field()    # 游戏分类id，查库
    date = scrapy.Field()   # 日期 xxxx-xx-xx
    add_time = scrapy.Field()   # 添加时间
    update_time = scrapy.Field()    # 更新时间
    platform_id = scrapy.Field()    # 非数据库字段,用于在统计弹幕总量时的平台判断


class Xj_gift_value(scrapy.Item):
    '''礼物价值'''
    gift_id = scrapy.Field()    # 礼物id
    name = scrapy.Field()   # 礼物名
    platform_id = scrapy.Field()    # 平台id
    price = scrapy.Field()  # 礼物单价/￥
    add_time = scrapy.Field()   # 添加时间
    update_time = scrapy.Field()    # 更新时间

