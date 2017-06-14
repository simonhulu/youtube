# -*- coding: utf-8 -*-
DEBUG = True # 启动Flask的Debug模式
PRODUCT = True
if PRODUCT:
    USEPROXY = False
    TMPSTOREPATH = "/media/video/"
else:
    USEPROXY = True
    TMPSTOREPATH = "/Users/zhangshijie/Downloads/"
