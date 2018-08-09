# -*- coding: utf-8 -*-

# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: http://doc.scrapy.org/en/latest/topics/item-pipeline.html
import time
import logging
import pymysql
import re
from twisted.enterprise import adbapi
from .tools import time_str
# from pymongo import MongoClient


class Xj_starPipeline(object):
    '''
    将主播基础数据保存在xj_star表中
    '''
    def __init__(self, dbpool, cursor):
        self.start_time = 0
        self.dbpool = dbpool
        self.cursor = cursor
        self.insert_list = list()

    @classmethod
    def from_crawler(cls, crawler):
        settings = crawler.settings
        dbparams = dict(
            host=settings['MYSQL_HOST'],
            port=settings['MYSQL_PORT'],
            db=settings['MYSQL_DB'],
            user=settings['MYSQL_USER'],
            passwd=settings['MYSQL_PASSWD'],
            charset=settings['CHARSET']
        )
        dbpool = adbapi.ConnectionPool('pymysql', **dbparams)
        connect = pymysql.connect(**dbparams)
        connect.autocommit(1)
        cursor = connect.cursor()
        return cls(dbpool, cursor)

    def open_spider(self, spider):
        self.start_time = int(time.time())

    def process_item(self, item, spider):
        view_num = self.select_view_num(item)
        if view_num is None:
            # self.dbpool.runInteraction(self.insert_db, item)
            # 批量插入
            self.insert_list.append(self.make_data(item))
        else:
            if int(item["view_num"]) > int(view_num):
                self.dbpool.runInteraction(self.update_view_num, item)
            else:
                self.dbpool.runInteraction(self.update_time, item)
        return item

    def close_spider(self, spider):
        '''
        计算运行时长
        :param spider:
        :return:
        '''
        self.insert_all()
        final_time = int(time.time())
        cost_time = final_time - self.start_time
        logging.error("-*spider:xj_star  cost_time:{}s*-".format(cost_time))

    def select_db(self, item):
        sql = "SELECT * FROM xj_star WHERE name=%s"
        result = self.cursor.execute(sql, item["name"])
        return result

    def make_data(self, item):
        '''构造数据字符串'''
        data_str = "(0,'{}',{},'','{}','{}','{}','','','','','','','',{},{},{},1,'',0,0,1.0),".format(item["category_id"], item["platform_id"], item["name"], item["avatar"], item["live_url"], int(item["view_num"]), int(time.time()), int(time.time()))
        return data_str

    def insert_all(self):
        '''将insert_list中数据通过全列多行插入存入数据库'''
        sql_str = str()
        if len(self.insert_list) > 0:
            for i in self.insert_list:
                sql_str += i
            sql = "INSERT INTO xj_star VALUES %s" % sql_str
            sql_result = sql.rstrip(',')
            self.cursor.execute(sql_result)

    def insert_db(self, cursor, item):
        sql = "INSERT INTO xj_star VALUES(0,%s,%s,'',%s,%s,%s,'','','','','','','',%s,%s,%s,1,'',0,0,1.0)"
        try:
            cursor.execute(
                sql,
                [
                    item["category_id"],
                    item["platform_id"],
                    item["name"],
                    item["avatar"],
                    item["live_url"],
                    int(item["view_num"]),
                    int(time.time()),
                    int(time.time())
                ]
            )
        except Exception as error:
            data = "spider:xj_star 数据insert失败!!! error:{} 主播名:{} 主播地址:{}".format(error, item["name"], item["live_url"])
            logging.error(data)

    def update_time(self, cursor, item):
        # sql = "UPDATE xj_star SET live_url=%s,update_time=%s WHERE name=%s"
        sql = "UPDATE xj_star SET name=%s,update_time=%s WHERE live_url=%s"
        # cursor.execute(
        #     sql,
        #     [
        #         item["live_url"],
        #         int(time.time()),
        #         item["name"]
        #     ]
        # )
        cursor.execute(
            sql,
            [
                item["name"],
                int(time.time()),
                item["live_url"]
            ]
        )

    def update_view_num(self, cursor, item):
        '''
        更新时view_num若没有大于数据库中已存，则不更新view_num
        :param cursor:
        :param item:
        :return:
        '''
        # sql = "UPDATE xj_star SET view_num=%s,live_url=%s,update_time=%s WHERE name=%s"
        sql = "UPDATE xj_star SET view_num=%s,name=%s,update_time=%s WHERE live_url=%s"
        # cursor.execute(
        #     sql,
        #     [
        #         int(item["view_num"]),
        #         item["live_url"],
        #         int(time.time()),
        #         item["name"]
        #     ]
        # )
        cursor.execute(
            sql,
            [
                int(item["view_num"]),
                item["name"],
                int(time.time()),
                item["live_url"]
            ]
        )

    def select_view_num(self, item):
        # sql = "SELECT view_num FROM xj_star WHERE name=%s"
        sql = "SELECT view_num FROM xj_star WHERE live_url=%s"
        # result = self.cursor.execute(sql, item["name"])
        result = self.cursor.execute(sql, item["live_url"])
        if result > 0:
            return self.cursor.fetchone()[0]
        else:
            return None


class Xj_update_gamesPipeline(object):
    '''
    更新xj_anchor_category中的游戏分类
    '''
    def __init__(self, dbpool, cursor):
        self.start_time = 0
        self.dbpool = dbpool
        self.cursor = cursor
        self.insert_list = list()

    @classmethod
    def from_crawler(cls, crawler):
        settings = crawler.settings
        dbparams = dict(
            host=settings['MYSQL_HOST'],
            port=settings['MYSQL_PORT'],
            db=settings['MYSQL_DB'],
            user=settings['MYSQL_USER'],
            passwd=settings['MYSQL_PASSWD'],
            charset=settings['CHARSET']
        )
        dbpool = adbapi.ConnectionPool('pymysql', **dbparams)
        connect = pymysql.connect(**dbparams)
        connect.autocommit(1)
        cursor = connect.cursor()
        return cls(dbpool, cursor)

    def open_spider(self, spider):
        self.start_time = int(time.time())

    def process_item(self, item, spider):
        result = self.select_db(item)
        if result == 0:
            # self.dbpool.runInteraction(self.insert_db, item)
            # 批量插入
            self.insert_list.append(self.make_data(item))
        return item

    def close_spider(self, spider):
        '''
        计算运行时长
        :param spider:
        :return:
        '''
        self.insert_all()
        final_time = int(time.time())
        cost_time = final_time - self.start_time
        logging.error("-*spider:xj_update_games  cost_time:{}s*-".format(cost_time))

    def select_db(self, item):
        '''
        查询数据库
        :param item:
        :return:
        '''
        sql = "SELECT * FROM xj_anchor_category WHERE name=%s"
        result = self.cursor.execute(sql, [item["name"]])
        return result

    def make_data(self, item):
        '''构造数据字符串'''
        data_str = "(0,'{}','',0,0,{},{},1,0,'',''),".format(item["name"], int(time.time()), int(time.time()))
        return data_str

    def insert_all(self):
        '''将insert_list中数据通过全列多行插入存入数据库'''
        sql_str = str()
        if len(self.insert_list) > 0:
            for i in self.insert_list:
                sql_str += i
            sql = "INSERT INTO xj_anchor_category VALUES %s" % sql_str
            sql_result = sql.rstrip(',')
            self.cursor.execute(sql_result)

    def insert_db(self, cursor, item):
        '''
        添加数据库
        :param item:
        :return:
        '''
        sql = "INSERT INTO xj_anchor_category VALUES(0,%s,'',0,0,%s,%s,1,0,'','')"
        cursor.execute(sql, [
            item["name"],
            int(time.time()),
            int(time.time())
        ])


class Xj_anchor_dataPipeline(object):
    '''
    更新或添加xj_anchor_data表中数据
    '''
    def __init__(self, dbpool, cursor):
        self.start_time = 0
        self.dbpool = dbpool
        self.cursor = cursor
        self.insert_list = list()
        # self.mongo_host = mongo_host,
        # self.mongo_port = mongo_port
        # self.mongo_db = mongo_db
        # self.platform_dict = {
        #     "11": "douyu",
        #     "8": "quanmin",
        #     "7": "huya",
        #     "4": "longzhu",
        #     "14": "egame",
        #     "10": "panda",
        #     "9": "zhanqi",
        #     "16": "bilibili",
        #     "6": "huomao",
        # }

    @classmethod
    def from_crawler(cls, crawler):
        settings = crawler.settings
        dbparams = dict(
            host=settings['MYSQL_HOST'],
            port=settings['MYSQL_PORT'],
            db=settings['MYSQL_DB'],
            user=settings['MYSQL_USER'],
            passwd=settings['MYSQL_PASSWD'],
            charset=settings['CHARSET']
        )
        dbpool = adbapi.ConnectionPool('pymysql', **dbparams)
        connect = pymysql.connect(**dbparams)
        connect.autocommit(1)
        cursor = connect.cursor()
        # mongo_host = settings['MONGO_HOST']
        # mongo_port = settings['MONGO_PORT']
        # mongo_db = settings['MONGO_DB']
        return cls(dbpool, cursor)

    def open_spider(self, spider):
        self.start_time = int(time.time())

    def process_item(self, item, spider):
        # new_item = self.count_danmu(item)
        # self.dbpool.runInteraction(self.insert_db, new_item)
        # self.dbpool.runInteraction(self.insert_db, item)
        # 批量插入
        self.insert_list.append(self.make_data(item))
        return item

    def close_spider(self, spider):
        '''
        计算运行时长
        :param spider:
        :return:
        '''
        self.insert_all()
        final_time = int(time.time())
        cost_time = final_time - self.start_time
        logging.error("-*spider:xj_anchor_data  cost_time:{}s*-".format(cost_time))

    def make_data(self, item):
        '''构造数据字符串'''
        date = time.strftime('%Y-%m-%d', time.localtime(int(time.time())))
        data_str = "({},{},{},{},{},'{}',{},{},{}),".format(int(item["anchor_id"]), int(item["weibo_fans"]), int(item["tieba_fans"]), int(item["followers"]), int(item["quotient"]), date, int(time.time()), int(time.time()), int(item["category_id"]))
        return data_str

    def insert_all(self):
        '''将insert_list中数据通过全列多行插入存入数据库'''
        sql_str = str()
        if len(self.insert_list) > 0:
            for i in self.insert_list:
                sql_str += i
            sql = "INSERT INTO xj_anchor_data (anchor_id,weibo_fans,tieba_fans,followers,quotient,date,add_time,update_time,category_id) VALUES %s" % sql_str
            sql_result = sql.rstrip(',')
            self.cursor.execute(sql_result)

    def insert_db(self, cursor, item):
        '''
        插入数据
        1.anchor_id 2.weibo_fans 3.tieba_fans 4.followers 5.quotient 6.date 7.add_time 8.update_time 9.category_id
        :param cursor:
        :param item:
        :return:
        '''
        if item["category_id"] == '':
            item["category_id"] = 0
            data = "spider:xj_anchor_data 未查询到游戏分类值 主播id:{} time:{}".format(item["anchor_id"], time_str())
            logging.error(data)
        date = time.strftime('%Y-%m-%d', time.localtime(int(time.time())))
        sql = "INSERT INTO xj_anchor_data VALUES(0,%s,%s,0,%s,0,%s,0,%s,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,%s,%s,%s,%s)"
        cursor.execute(sql, [
            int(item["anchor_id"]),
            int(item["weibo_fans"]),
            int(item["tieba_fans"]),
            int(item["followers"]),
            int(item["quotient"]),
            # int(item["danmu"]),
            date,
            int(time.time()),
            int(time.time()),
            int(item["category_id"])
        ])

    # def count_danmu(self, item):
    #     '''
    #     统计弹幕总量
    #     :param item:
    #     :return:
    #     '''
    #     connect = MongoClient(host=self.mongo_host, port=self.mongo_port)
    #     db = connect[self.mongo_db]
    #     coll = db[self.platform_dict[str(item["platform_id"])]]
    #     item["danmu"] = coll.find({"anchor_id": str(item["anchor_id"])}).count()
    #     return item


class Xj_view_livePipeline(object):
    '''
    操作xj_anchor_live表和xj_count_anchor_view表
    通过开关播状态记录开关播时间，若开播则记录在线观看数，保留最大值


    开关播时间入库逻辑：
    a. 对于抓取到的start_time:
        通过判断当天日期数据库中有无start_time值和end_time值:
        1.没有start_time,没有end_time
            该start_time为抓取到的开播时间，需要入库
        2.有start_time,没有end_time
            正在直播,start_time无需入库
        3.有start_time,有end_time
            该主播当天再次直播，需要入库
    b. 对于抓取到的end_time:
        通过判断当天日期数据库中有无start_time值和end_time值:
        1.没有start_time,没有end_time
            主播未开播，end_time为无效时间，不入库
        2.有start_time, 没有end_time
            该end_time为抓取到的关播时间，需要入库
        3.有start_time,有end_time
            有完整开关播记录，end_time为无效时间，不入库
    '''
    def __init__(self, dbpool, cursor):
        self.start_time = 0
        self.dbpool = dbpool
        self.cursor = cursor
        self.date = time.strftime('%Y-%m-%d', time.localtime(int(time.time())))
        self.insert_list = list()

    @classmethod
    def from_crawler(cls, crawler):
        settings = crawler.settings
        dbparams = dict(
            host=settings['MYSQL_HOST'],
            port=settings['MYSQL_PORT'],
            db=settings['MYSQL_DB'],
            user=settings['MYSQL_USER'],
            passwd=settings['MYSQL_PASSWD'],
            charset=settings['CHARSET']
        )
        dbpool = adbapi.ConnectionPool('pymysql', **dbparams)
        connect = pymysql.connect(**dbparams)
        connect.autocommit(1)
        cursor = connect.cursor()
        return cls(dbpool, cursor)

    def open_spider(self, spider):
        self.start_time = int(time.time())

    def process_item(self, item, spider):
        if "start_time" in item.keys():
            result = self.select_start_end(item)
            if result is None:      # 抓取到该主播的今日开播时间
                # 将数据加入insert列表
                self.insert_list.append(self.make_data(item))
                # self.dbpool.runInteraction(self.insert_start_time, item)
                self.dbpool.runInteraction(self.insert_view, item)
            else:   # 该主播的今日开播时间以存在，说明正在直播，或者开始了再次的直播
                # index = len(result) - 1
                # if result[index][1] != 0 and int(item["start_time"]) > result[index][1]:
                if result[1] != 0 and int(item["start_time"]) > result[1]:
                    # self.dbpool.runInteraction(self.insert_start_time, item)
                    self.insert_list.append(self.make_data(item))
                views = self.select_view(item)
                if views is None:
                    self.dbpool.runInteraction(self.insert_view, item)
                    return
                if int(views[0]) < int(item["view_num"]):
                    self.dbpool.runInteraction(self.update_view, item)
        if "end_time" in item.keys():
            result = self.select_end_time(item)
            if result is not None:      # 抓取到该主播的关播时间
                # index = len(result) - 1
                # if int(result[index][0]) == 0:
                if int(result[0]) == 0:
                    self.dbpool.runInteraction(self.update_end_time, item)
        return item

    # 尝试通过修改查询sql语句来尝试，通过order by id 排序 limit 1 取第一条，进行之后的操作

    def close_spider(self, spider):
        '''
        计算运行时长
        :param spider:
        :return:
        '''
        self.insert_all()
        final_time = int(time.time())
        cost_time = final_time - self.start_time
        logging.error("-*spider:xj_view_live  cost_time:{}s*-".format(cost_time))

    def select_start_time(self, item):
        '''
        从xj_anchor_live中查询start_time
        :return:
        '''
        sql = "SELECT start_time FROM xj_anchor_live WHERE anchor_id=%s AND date=%s"
        result = self.cursor.execute(sql, [item["anchor_id"], self.date])
        if result > 0:
            return self.cursor.fetchone()
        else:
            return None

    def select_end_time(self, item):
        '''
        从xj_anchor_live中查询end_time
        :param item:
        :return:
        '''
        # sql = "SELECT end_time FROM xj_anchor_live WHERE anchor_id=%s AND date=%s"
        sql = "SELECT end_time FROM xj_anchor_live WHERE anchor_id=%s AND date=%s ORDER BY id DESC limit 1"
        result = self.cursor.execute(sql, [item["anchor_id"], self.date])
        if result > 0:
            # return self.cursor.fetchall()
            return self.cursor.fetchone()
        else:
            return None

    # 使用列表记录将要存库的数据，达到一定数量后通过普通字符串格式化构建sql语句，在爬虫结束时使用全列多行插入进行数据存取

    def insert_start_time(self, cursor, item):
        '''
        插入start_time
        :param cursor:
        :param item:
        :return:
        '''
        sql = "INSERT INTO xj_anchor_live VALUES(0,%s,%s,%s,%s)"
        date = time.strftime('%Y-%m-%d', time.localtime(int(time.time())))
        cursor.execute(sql, [
            int(item["anchor_id"]),
            date,
            int(item["start_time"]),
            0   # 先将结束时间设为0
            ])

    def make_data(self, item):
        '''构造数据字符串'''
        date = time.strftime('%Y-%m-%d', time.localtime(int(time.time())))
        data_str = "(0,{},'{}',{},0),".format(int(item["anchor_id"]), date, int(item["start_time"]))
        return data_str

    def insert_all(self):
        '''将insert_list中数据通过全列多行插入存入数据库'''
        sql_str = str()
        if len(self.insert_list) > 0:
            for i in self.insert_list:
                sql_str += i
            sql = "INSERT INTO xj_anchor_live VALUES %s" % sql_str
            sql_result = sql.rstrip(',')
            self.cursor.execute(sql_result)

    def update_end_time(self, cursor, item):
        '''
        更新end_time
        :param cursor:
        :param item:
        :return:
        '''
        sql = "UPDATE xj_anchor_live SET end_time=%s WHERE anchor_id=%s AND date=%s ORDER BY id DESC limit 1"
        date = time.strftime('%Y-%m-%d', time.localtime(int(time.time())))
        cursor.execute(sql, [
            int(item["end_time"]),
            int(item["anchor_id"]),
            date
        ])

    def select_start_end(self, item):
        '''
        查询今日有无完整的开关播记录
        :param item:
        :return:
        '''
        # sql = "SELECT start_time,end_time FROM xj_anchor_live WHERE anchor_id=%s AND date=%s"
        sql = "SELECT start_time,end_time FROM xj_anchor_live WHERE anchor_id=%s AND date=%s ORDER BY id DESC limit 1"
        result = self.cursor.execute(sql, [item["anchor_id"], self.date])
        if result > 0:
            # return self.cursor.fetchall()
            return self.cursor.fetchone()
        else:
            return None

    def insert_view(self, cursor, item):
        '''
        插入view_num
        :param cursor:
        :param item:
        :return:
        '''
        sql = "INSERT INTO xj_count_anchor_view VALUES(0,%s,%s,%s,%s)"
        date = time.strftime('%Y-%m-%d', time.localtime(int(time.time())))
        cursor.execute(sql, [
            int(item["anchor_id"]),
            date,
            int(item["view_num"]),
            int(time.time())
        ])

    def select_view(self, item):
        '''
        查询view_num
        :param item:
        :return:
        '''
        sql = "SELECT view_num FROM xj_count_anchor_view WHERE anchor_id=%s AND day=%s"
        result = self.cursor.execute(sql, [item["anchor_id"], self.date])
        if result > 0:
            return self.cursor.fetchone()
        else:
            return None

    def update_view(self, cursor, item):
        '''
        更新view_num
        :param cursor:
        :param item:
        :return:
        '''
        sql = "UPDATE xj_count_anchor_view SET view_num=%s,update_time=%s WHERE anchor_id=%s AND day=%s"
        date = time.strftime('%Y-%m-%d', time.localtime(int(time.time())))
        cursor.execute(sql, [
            int(item["view_num"]),
            int(time.time()),
            int(item["anchor_id"]),
            date
        ])


class Xj_gift_valuePipeline(object):
    '''
    更新或添加礼物价值
    '''
    def __init__(self, dbpool, cursor):
        self.start_time = 0
        self.dbpool = dbpool
        self.cursor = cursor
        self.insert_list = list()

    @classmethod
    def from_crawler(cls, crawler):
        settings = crawler.settings
        dbparams = dict(
            host=settings['MYSQL_HOST'],
            port=settings['MYSQL_PORT'],
            db=settings['MYSQL_DB'],
            user=settings['MYSQL_USER'],
            passwd=settings['MYSQL_PASSWD'],
            charset=settings['CHARSET']
        )
        dbpool = adbapi.ConnectionPool('pymysql', **dbparams)
        connect = pymysql.connect(**dbparams)
        connect.autocommit(1)
        cursor = connect.cursor()
        return cls(dbpool, cursor)

    def open_spider(self, spider):
        self.start_time = int(time.time())

    def process_item(self, item, spider):
        if float(item["price"]) != 0.0:
            save = self.select_db(item)
            if save is None:
                # self.insert_db(item)
                # self.dbpool.runInteraction(self.insert_db, item)
                # 批量操作
                self.insert_list.append(self.make_data(item))
        return item

    def close_spider(self, spider):
        '''
        计算运行时长
        :param spider:
        :return:
        '''
        self.insert_all()
        final_time = int(time.time())
        cost_time = final_time - self.start_time
        logging.error("-*spider:xj_gift_value  cost_time:{}s*-".format(cost_time))

    def select_db(self, item):
        sql = "SELECT * FROM xj_gift_value WHERE name=%s AND platform_id=%s"
        result = self.cursor.execute(sql, [item["name"], item["platform_id"]])
        if result > 0:
            return self.cursor.fetchall()
        else:
            return None

    def make_data(self, item):
        '''构造数据字符串'''
        data_str = "(0,'{}','{}',{},{},{},{}),".format(item["gift_id"], item["name"], int(item["platform_id"]), float(item["price"]), int(time.time()), int(time.time()))
        return data_str

    def insert_all(self):
        '''将insert_list中数据通过全列多行插入存入数据库'''
        sql_str = str()
        if len(self.insert_list) > 0:
            for i in self.insert_list:
                sql_str += i
            sql = "INSERT INTO xj_gift_value VALUES %s" % sql_str
            sql_result = sql.rstrip(',')
            self.cursor.execute(sql_result)

    def insert_db(self, cursor, item):
        sql = "INSERT INTO xj_gift_value VALUES(0,%s,%s,%s,%s,%s,%s)"
        cursor.execute(sql, [
            item["gift_id"],
            item["name"],
            int(item["platform_id"]),
            float(item["price"]),
            int(time.time()),
            int(time.time())
        ])

