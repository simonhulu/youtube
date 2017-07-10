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
from MyYoutubeExtractor import MyYoutubeExtractor
from fake_useragent import UserAgent
import requests
import pycurl
from StringIO import StringIO
import dropbox
import jsonpickle
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

# driver = webdriver.PhantomJS(executable_path='/usr/local/bin/phantomjs',service_args=service_args)
# driver = webdriver.Chrome(executable_path='/usr/local/bin/chromedriver',service_args=service_args)
# driver.set_window_size(1920, 1080)



if __name__ == '__main__':

    # youtubeUrl = "www.youtube.com/watch?v=rBJ2OSWFKkA";
    # m = re.match(MyYoutubeExtractor._VALID_URL, youtubeUrl, re.VERBOSE)
    # print m

    print os.stat("/media/video/2017/6/22/videoplayback123456789asdfhfgfggsdsdsd.3gp")
    dbx = dropbox.Dropbox('pIR-KPDmuyAAAAAAAAAAETOCjOuDKXGZwqnK8giZ3TQJxEvLMiTD8BYhAb6ptysT')
    for entry in dbx.files_list_folder('').entries:
        print(entry.name)
    file_path = "/Users/zhangshijie/Library/Caches/com.apple.helpd/SDMHelpData/Other/zh_CN/lsm_map"
    dest_path = "/media/video/2017/6/22/videoplayback123456789asdfhfgfggsdsdsd.3gp"
    f = open(file_path)
    file_size = os.path.getsize(file_path)

    CHUNK_SIZE = 4 * 1024 * 1024

    if file_size <= CHUNK_SIZE:

        print dbx.files_upload(f, dest_path)

    else:
        try:
            upload_session_start_result = dbx.files_upload_session_start(f.read(CHUNK_SIZE))
            cursor = dropbox.files.UploadSessionCursor(session_id=upload_session_start_result.session_id,
                                                       offset=f.tell())
            commit = dropbox.files.CommitInfo(path=dest_path)

            while f.tell() < file_size:
                if ((file_size - f.tell()) <= CHUNK_SIZE):
                    print dbx.files_upload_session_finish(f.read(CHUNK_SIZE),
                                                          cursor,
                                                          commit)
                    print "100%"
                else:
                    dbx.files_upload_session_append(f.read(CHUNK_SIZE),
                                                    cursor.session_id,
                                                    cursor.offset)
                    cursor.offset = f.tell()
                    print cursor.offset*100/file_size
        except Exception as e:
            print e
    #
    # try:
    #     c = 5/0
    # except Exception as e:
    #     c = 0
    # print c
    #
    # extractor = MyYoutubeExtractor(useproxy=True);
    # youtubeie = YoutubeIE();
    # url = "https://www.youtube.com/watch?v=79CmjcIYfas";
    # video_id = "HGxRiReJQdk";
    # test = True
    # ydl_opts = {
    #     "proxy":"socks5://127.0.0.1:1080"
    # }
    # if test:
    #     # with youtube_dl.YoutubeDL(ydl_opts) as ydl:
    #     #     ydl.add_default_info_extractors()
    #     #     res = ydl.download([url])
    #     # import mechanize
    #     #
    #     # br = mechanize.Browser()
    #     # resp = br.open("http://www.google.com")
    #     # print resp.info()  # headers
    #     # print resp.read()  # content
    #
    #     dic = extractor.extractVideo("https://youtu.be/f23QAm83pno")
    #     print(dic)
    #
    # else:
    #     dic =  extractor.bestVideo(url)
    #     print(dic)



