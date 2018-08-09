# xingji100_spider
主播数据平台基础数据抓取，包括斗鱼、企鹅、熊猫、b站、全民、虎牙、龙珠、战旗、火猫

spiders介绍：
* xj_star:主要抓取主播在线热度、主播名、主播直播url、主播头像图片
          游戏id和平台id来源于xingji数据库
* xj_update_games:主要抓取游戏名，平台id来源于xingji数据库
* xj_view_live:主要抓取主播开关播时间、主播开播时的在线观看人数
               为减轻数据库压力，待抓取url的查询工作采用缓存文件的机制
* xj_anchor_data:主要抓取各直播间关注量、各主播百度指数、各主播微博粉丝量、各主播贴吧粉丝量
                游戏id、平台id、主播id来源于xingji数据库
                为减轻数据库压力，带抓取url的查询工作采用缓存文件的机制
* xj_gift_value：主要抓取各直播平台礼物名，礼物单价，作为礼物对照表与抓取的弹幕一起计算礼物总价值

middlewares介绍：
包括中间件：
* 斗鱼延时请求中间件：SleepMiddleware
* 蚂蚁代理中间件：MayiProxyMiddleware
* 芝麻代理中间件：ZhimaProxyMiddleware
* 讯代理动态转发中间件：XunProxyMiddleware

pipelines介绍：
为减轻数据库压力，插入数据操作统一为在抓取时数据存入内存，批量insert

sql_handle介绍：
spider运行时查询数据库的工具集

tools介绍：
spider使用的其他工具集
