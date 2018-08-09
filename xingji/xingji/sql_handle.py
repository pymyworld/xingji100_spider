# sql语句处理
import pymysql
from .settings import *
import time
import logging
from .tools import time_str


class Sqlhandle(object):
    def __init__(self):
        dbparams = dict(
            host=MYSQL_HOST,
            port=MYSQL_PORT,
            user=MYSQL_USER,
            passwd=MYSQL_PASSWD,
            db=MYSQL_DB,
            charset=CHARSET
        )
        self.connect = pymysql.connect(**dbparams)
        # 自动提交
        self.connect.autocommit(1)
        self.cursor = self.connect.cursor()

    def select_game_id(self, game):
        '''
        查询游戏分类id
        :param game:
        :return:game_id
        '''
        sql = "SELECT id FROM xj_anchor_category WHERE name=%s"
        # 返回符合查询结果的数量
        if self.cursor.execute(sql, game) > 0:
            category_id = self.cursor.fetchone()[0]
            return category_id

    def insert_game(self, game):
        '''
        添加游戏分类并查询游戏id
        :param game:
        :return:
        '''
        sql = "INSERT INTO xj_anchor_category VALUES(0,%s,'',0,0,%s,%s,1,0)"
        add_time = int(time.time())
        update_time = int(time.time())
        # 成功插入一条
        if self.cursor.execute(sql, [game, add_time, update_time]) == 1:
            category_id = self.select_game_id(game)
            return category_id

    def deal_game(self, game, platform_id):
        '''
        处理游戏分类
        :param game:
        :param platform_id:
        :return:
        '''
        category_id = self.select_game_id(game)
        if category_id is None:
            category_id = self.insert_game(game)
            if category_id is None:
                # 日志
                data = 'data:{},platform_id:{},message:the {} insert xj_anchor_category failed!'.format(time_str(), platform_id, game)
                logging.error(data)
        return category_id

    # def select_anchor_info(self):
    #     '''
    #     从xj_star表中查询id和m_weibo
    #     :return:
    #     '''
    #     sql = "SELECT id,m_weibo FROM xj_star"
        # sql = "SELECT id,live_url from xj_star"
        # if self.cursor.execute(sql) > 0:
        #     return self.cursor.fetchall()

    def select_category_id_name(self, anchor_id):
        '''
        从xj_star中根据id来获取category_id和name
        :return: category_id, name
        '''
        sql = "SELECT category_id,name FROM xj_star WHERE id=%s"
        if self.cursor.execute(sql, [anchor_id, ]) > 0:
            result = self.cursor.fetchone()
            return result[0], result[1]
        else:
            return None

    def select_from_star(self, anchor_id, type_str):
        '''
        从xj_star表中根据type和id来获取数据
        :param anchor_id:
        :return:
        '''
        # if type_str == 'live':
        if type_str == 'weibo':
            # sql = "SELECT live_url FROM xj_star WHERE id=%s"
            sql = "SELECT m_weibo FROM xj_star WHERE id=%s"
            if self.cursor.execute(sql, [anchor_id, ]) > 0:
                return self.cursor.fetchone()[0]
        if type_str == 'tieba':
            sql = "SELECT tieba FROM xj_star WHERE id=%s"
            if self.cursor.execute(sql, [anchor_id, ]) > 0:
                return self.cursor.fetchone()[0]

    def select_id_live_url(self):
        '''
        从xj_star表中查询主播id和live_url
        :return:
        '''
        sql = "SELECT id,live_url FROM xj_star"
        if self.cursor.execute(sql) > 0:
            return self.cursor.fetchall()
