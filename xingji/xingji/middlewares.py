# -*- coding: utf-8 -*-

# Define here the models for your spider middleware
#
# See documentation in:
# http://doc.scrapy.org/en/latest/topics/spider-middleware.html

from scrapy import signals
import time
import random
import hashlib
import logging
import json


class XingjiSpiderMiddleware(object):
    # Not all methods need to be defined. If a method is not defined,
    # scrapy acts as if the spider middleware does not modify the
    # passed objects.

    @classmethod
    def from_crawler(cls, crawler):
        # This method is used by Scrapy to create your spiders.
        s = cls()
        crawler.signals.connect(s.spider_opened, signal=signals.spider_opened)
        return s

    def process_spider_input(self, response, spider):
        # Called for each response that goes through the spider
        # middleware and into the spider.

        # Should return None or raise an exception.
        return None

    def process_spider_output(self, response, result, spider):
        # Called with the results returned from the Spider, after
        # it has processed the response.

        # Must return an iterable of Request, dict or Item objects.
        for i in result:
            yield i

    def process_spider_exception(self, response, exception, spider):
        # Called when a spider or process_spider_input() method
        # (from other spider middleware) raises an exception.

        # Should return either None or an iterable of Response, dict
        # or Item objects.
        pass

    def process_start_requests(self, start_requests, spider):
        # Called with the start requests of the spider, and works
        # similarly to the process_spider_output() method, except
        # that it doesn’t have a response associated.

        # Must return only requests (not items).
        for r in start_requests:
            yield r

    def spider_opened(self, spider):
        spider.logger.info('Spider opened: %s' % spider.name)


class SleepMiddleware(object):
    '''斗鱼延时请求中间件'''
    def __init__(self, crawler):
        super(SleepMiddleware, self).__init__()
        self.user_agent_list = crawler.settings.get('USER_AGENT', [])

    @classmethod
    def from_crawler(cls, crawler):
        return cls(crawler)

    def process_request(self, request, spider):
        request.headers.setdefault(b"User-Agent", random.choice(self.user_agent_list))
        if request.url.find("douyu") > 0:
            time.sleep(0.4)


class MayiProxyMiddleware(object):
    '''蚂蚁代理中间件'''
    def __init__(self, crawler):
        super(MayiProxyMiddleware, self).__init__()
        self.appkey = crawler.settings.get('APPKEY')
        self.secret = crawler.settings.get('MAYI_SECRET')
        self.mayi_url = crawler.settings.get('MAYI_URL')
        self.mayi_port = crawler.settings.get('MAYI_PORT')
        self.mayi_proxy = 'http://{}:{}'.format(self.mayi_url, self.mayi_port)
        self.user_agent = crawler.settings.get('USER_AGENT')

    @classmethod
    def from_crawler(cls, crawler):
        return cls(crawler)

    def process_request(self, request, spider):
        proxies = {
            "http": self.mayi_proxy,
            "https": self.mayi_proxy
        }
        if request.url.find("douyu") > 0:
            # request.meta['proxy'] = proxies[random.choice(["http", "https"])]
            request.meta["proxy"] = proxies["http"]


class ZhimaProxyMiddleware(object):
    '''芝麻代理中间件'''
    def __init__(self):
        with open("ip_pool.txt", "r") as f:
            self.proxy_dict = json.loads(f.read())
            self.proxy_list = self.proxy_dict["proxy"]

    def process_request(self, request, spider):
        try:
            if request.url.find("douyu") > 0:
                request.meta["proxy"] = random.choice(self.proxy_list)["http"]
        except ValueError as error:
            logging.error("芝麻代理账户余额不足,{}".format(error))


class XunProxyMiddleware(object):
    '''迅代理动态转发中间件'''
    def __init__(self, crawler):
        super(XunProxyMiddleware, self).__init__()
        self.orderno = crawler.settings.get('ORDERNO')
        self.secret = crawler.settings.get('XUN_SECRET')
        self.ip = crawler.settings.get('XUN_IP')
        self.port = crawler.settings.get('XUN_PORT')
        self.http_proxy = "http://{}:{}".format(self.ip, self.port)
        self.https_proxy = "https://{}:{}".format(self.ip, self.port)

    @classmethod
    def from_crawler(cls, crawler):
        return cls(crawler)

    def process_request(self, request, spider):
        proxy = {
            "http": self.http_proxy,
            "https": self.https_proxy
        }
        if request.url.find("douyu") > 0:
            print("proxy")
            request.meta['proxy'] = proxy[random.choice(["http", "https"])]


