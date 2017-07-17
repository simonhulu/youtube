# -*- coding: utf-8 -*-
DEBUG = True # 启动Flask的Debug模式
PRODUCT = True
VERSION = 1.1
if PRODUCT:
    USEPROXY = False
    TMPSTOREPATH = "/mnt/blockstorage/media/video/"
else:
    USEPROXY = True
    TMPSTOREPATH = "/Users/zhangshijie/Downloads/"
DROPBOXTMPSTOREPATH = "/media/video/"
LANGUAGES = {
    'en': 'English',
    'zh': 'Chinese'
}
