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
import pycurl
from StringIO import StringIO
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

    # youtubeUrl = "www.youtube.com/watch?v=rBJ2OSWFKkA";
    # m = re.match(MyYoutubeExtractor._VALID_URL, youtubeUrl, re.VERBOSE)
    # print m

    extractor = MyYoutubeExtractor(useproxy=True);
    youtubeie = YoutubeIE();
    url = "https://www.youtube.com/watch?v=79CmjcIYfas";
    video_id = "HGxRiReJQdk";
    test = True
    ydl_opts = {
        "proxy":"socks5://127.0.0.1:1080"
    }
    if test:
        # with youtube_dl.YoutubeDL(ydl_opts) as ydl:
        #     ydl.add_default_info_extractors()
        #     res = ydl.download([url])
        # import mechanize
        #
        # br = mechanize.Browser()
        # resp = br.open("http://www.google.com")
        # print resp.info()  # headers
        # print resp.read()  # content
        re_duration = re.compile('Duration: (\d{2}):(\d{2}):(\d{2}).(\d{2})[^\d]*', re.U)
        re_position = re.compile('time=(\d{2}):(\d{2}):(\d{2})\.(\d{2})\d*', re.U | re.I)
        duration_match = re_position.search("frame=15720 fps=10476 q=-1.0 size=  169021kB time=00:10:28.72 bitrate=2202")
        hours = int(duration_match.group(1))
        minutes = int(duration_match.group(2))
        sec = int(duration_match.group(3))
        print  hours*3600+minutes*60+sec
        # dic = extractor.extractVideo("https://www.youtube.com/watch?v=RDZg9I9uAlc")
        # print(dic)

    else:
        dic =  extractor.bestVideo(url)
        print(dic)



