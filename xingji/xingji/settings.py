# -*- coding: utf-8 -*-

# Scrapy settings for xingji project
#
# For simplicity, this file contains only settings considered important or
# commonly used. You can find more settings consulting the documentation:
#
#     http://doc.scrapy.org/en/latest/topics/settings.html
#     http://scrapy.readthedocs.org/en/latest/topics/downloader-middleware.html
#     http://scrapy.readthedocs.org/en/latest/topics/spider-middleware.html
import time


BOT_NAME = 'xingji'

SPIDER_MODULES = ['xingji.spiders']
NEWSPIDER_MODULE = 'xingji.spiders'

# 日志配置
LOG_FILE = "./log/spiderlog_{}.txt".format(time.strftime("%Y_%m_%d", time.localtime()))
LOG_LEVEL = "ERROR"
LOG_ENCODING = "utf-8"

# Crawl responsibly by identifying yourself (and your website) on the user-agent
USER_AGENT = [
    'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/64.0.3282.186 Safari/537.36',
    'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/62.0.3202.62 Safari/537.36'
    ]

# Obey robots.txt rules
ROBOTSTXT_OBEY = False

DUPEFILTER_DEBUG = True

# Configure maximum concurrent requests performed by Scrapy (default: 16)
CONCURRENT_REQUESTS = 16

# 捕获400,403,404状态码
HTTPERROR_ALLOWED_CODES = [400, 403, 404, 587, 588, 589]

# 设置所有爬虫运行时长不超过23小时,以不影响每天的定时任务
CLOSESPIDER_TIMEOUT = 82800

# mysql
MYSQL_HOST = 'xxxxxxxxxx'
MYSQL_PORT = 3306
MYSQL_DB = 'xxxxxxxxx'
MYSQL_USER = 'xxxx'
MYSQL_PASSWD = 'xxxx'
CHARSET = 'utf8mb4'

# mongo
# MONGO_HOST = "xxxxxxxxx"
# MONGO_PORT = 27017
# MONGO_DB = "xxxxxxx"

# 头像图片存储路径
avatar_path = "/static/upload/tv"

# 蚂蚁代理配置项
APPKEY = "xxxxxxxxx"
MAYI_SECRET = "xxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
MAYI_URL = "xxxxxxxxxxxxxxxx"
MAYI_PORT = "xxxx"

# Configure a delay for requests for the same website (default: 0)
# See http://scrapy.readthedocs.org/en/latest/topics/settings.html#download-delay
# See also autothrottle settings and docs
# DOWNLOAD_DELAY = 0.4
# The download delay setting will honor only one of:
#CONCURRENT_REQUESTS_PER_DOMAIN = 16
#CONCURRENT_REQUESTS_PER_IP = 16

# Disable cookies (enabled by default)
# COOKIES_ENABLED = False

# Disable Telnet Console (enabled by default)
#TELNETCONSOLE_ENABLED = False

# Override the default request headers:
#DEFAULT_REQUEST_HEADERS = {
#   'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
#   'Accept-Language': 'en',
#}

# Enable or disable spider middlewares
# See http://scrapy.readthedocs.org/en/latest/topics/spider-middleware.html
#SPIDER_MIDDLEWARES = {
#    'xingji.middlewares.XingjiSpiderMiddleware': 543,
#}

# Enable or disable downloader middlewares
# See http://scrapy.readthedocs.org/en/latest/topics/downloader-middleware.html
DOWNLOADER_MIDDLEWARES = {
    # 'xingji.middlewares.MyCustomDownloaderMiddleware': 543,
    # 'xingji.middlewares.SleepMiddleware': 300,
    # 'xingji.middlewares.MayiProxyMiddleware': 300,
    # 'xingji.middlewares.ZhimaProxyMiddleware': 300,
    # 'xingji.middlewares.XunProxyMiddleware': 300,
}

# Enable or disable extensions
# See http://scrapy.readthedocs.org/en/latest/topics/extensions.html
#EXTENSIONS = {
#    'scrapy.extensions.telnet.TelnetConsole': None,
#}

# Configure item pipelines
# See http://scrapy.readthedocs.org/en/latest/topics/item-pipeline.html
#ITEM_PIPELINES = {
#    'xingji.pipelines.XingjiPipeline': 300,
#}

# Enable and configure the AutoThrottle extension (disabled by default)
# See http://doc.scrapy.org/en/latest/topics/autothrottle.html
#AUTOTHROTTLE_ENABLED = True
# The initial download delay
#AUTOTHROTTLE_START_DELAY = 5
# The maximum download delay to be set in case of high latencies
#AUTOTHROTTLE_MAX_DELAY = 60
# The average number of requests Scrapy should be sending in parallel to
# each remote server
#AUTOTHROTTLE_TARGET_CONCURRENCY = 1.0
# Enable showing throttling stats for every response received:
#AUTOTHROTTLE_DEBUG = False

# Enable and configure HTTP caching (disabled by default)
# See http://scrapy.readthedocs.org/en/latest/topics/downloader-middleware.html#httpcache-middleware-settings
#HTTPCACHE_ENABLED = True
#HTTPCACHE_EXPIRATION_SECS = 0
#HTTPCACHE_DIR = 'httpcache'
#HTTPCACHE_IGNORE_HTTP_CODES = []
#HTTPCACHE_STORAGE = 'scrapy.extensions.httpcache.FilesystemCacheStorage'

