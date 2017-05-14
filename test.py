# coding: utf-8
import youtube_dl

from utils import uppercase_escape
import re
from youtube_dl.extractor.youtube import YoutubeBaseInfoExtractor
from youtube_dl.extractor.youtube import  YoutubeIE
from youtube_dl.extractor.common import InfoExtractor, SearchInfoExtractor
from youtube_dl.downloader.common import FileDownloader
from youtube_dl.utils import *
from youtube_dl.compat import *
import socket
import socks
import urllib2
from selenium import webdriver
from selenium.webdriver.support import expected_conditions
from selenium.webdriver.common.by import By
from selenium.common.exceptions import  *
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
from selenium.webdriver.support.ui import WebDriverWait
from MyYoutubeExtractor import MyYoutubeExtractor
from fake_useragent import UserAgent
import requests
compiled_regex_type = type(re.compile(''))
try:
    compat_str = unicode  # Python 2
except NameError:
    compat_str = str
NO_DEFAULT = object()



service_args = [
    '--proxy=127.0.0.1:1080',
    '--proxy-type=socks5',
    ]
firefox_capabilities = DesiredCapabilities.CHROME
firefox_capabilities['marionette'] = True
# driver = webdriver.PhantomJS(executable_path='/usr/local/bin/phantomjs',service_args=service_args)
# driver = webdriver.Chrome(executable_path='/usr/local/bin/chromedriver',service_args=service_args)
# driver.set_window_size(1920, 1080)



if __name__ == '__main__':
    extractor = MyYoutubeExtractor();
    youtubeie = YoutubeIE();
    url = "https://www.youtube.com/watch?v=Mp9he8nZs8I";
    video_id = "Mp9he8nZs8I";
    test = True
    if test:
        # with youtube_dl.YoutubeDL() as ydl:
        #     ydl.add_default_info_extractors()
        #     res = ydl.extract_info(url, False)
        # import mechanize
        #
        # br = mechanize.Browser()
        # resp = br.open("http://www.google.com")
        # print resp.info()  # headers
        # print resp.read()  # content

        dic = extractor.extractVideo(url)
        print(dic)
    else:
        dic =  extractor.bestVideo(url)
        print(dic)



