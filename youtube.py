# -*- coding: utf-8 -*-
from flask import Flask
from flask import request
from flask import render_template
import youtube_dl
from flask import jsonify
import json
from Imeili100Result import Imeili100Result,Imeili100ResultStatus
from selenium import webdriver
from selenium.webdriver.support import expected_conditions
from selenium.webdriver.common.by import By
from selenium.common.exceptions import  *
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
from selenium.webdriver.support.ui import WebDriverWait
from MyYoutubeExtractor import MyYoutubeExtractor
import pycurl
from StringIO import StringIO
import requests
import redis
import uuid
from datetime import date
from downloadfile import *
import threading
import os
from pymongo import MongoClient
from bson.objectid import ObjectId
import subprocess
import re



compiled_regex_type = type(re.compile(''))
try:
    compat_str = unicode  # Python 2
except NameError:
    compat_str = str
NO_DEFAULT = object()
app = Flask(__name__)
client = MongoClient()
db = client['youtube']

g_redis = redis.StrictRedis(host='localhost',port=6379,db=0)
tmpstorepath = "/Users/zhangshijie/Downloads/"
service_args = [
    '--proxy=127.0.0.1:1080',
    '--proxy-type=socks5',
    ]
# firefox_capabilities = DesiredCapabilities.CHROME
# firefox_capabilities['marionette'] = True
# driver = webdriver.PhantomJS(executable_path='/usr/local/bin/phantomjs')
# driver = webdriver.Chrome(executable_path='/usr/local/bin/chromedriver',service_args=service_args)
extractor = MyYoutubeExtractor();
@app.route('/')
def hello_world():
    return render_template('youtubescreenshot.html')
@app.route('/feedback')
def feedbackpage():
    return render_template('community.html')

@app.route('/downloadsrt/')
def downloadsrt():
    #listsubtitles
    ydl_opts = {
        'listsubtitles': True,
    }
    with youtube_dl.YoutubeDL(ydl_opts) as ydl:
        ydl.add_default_info_extractors()
        res = ydl.download(["https://www.youtube.com/watch?v=HGxRiReJQdk"])
        print(type(res))
    return render_template('downloadsrt.html')

@app.route('/record1080/',methods = ['GET', 'POST'])
def record1080():
    vid = request.form['vid'];
    if vid:
        vdicstr = g_redis.get(vid)
        if vdicstr:
            vdic = json.loads(vdicstr)
            info = vdic["info"];
            if info:
                betstaudio = info['best_audio'];
                betstvideo = info['best_video'];
                if betstaudio and betstvideo :
                    #存储task
                    downloaddataTaskcollection = db['youtube_downloadTask'];
                    task =  YoutubeDownloadTask(YoutubeDownloadTaskType.merge1080P,int(YoutubeTaskStatus.init),vid)
                    taskid = downloaddataTaskcollection.insert_one(task.__dict__).inserted_id

                    # Start new Threads
                    videoDownload = preparedownload(vid,int(YoutubeFileType.video),betstvideo['url'],betstvideo['ext'],str(taskid))
                    audioDownload = preparedownload(vid,int(YoutubeFileType.audio),betstaudio['url'],betstaudio['ext'],str(taskid))
                    downloaddatacollection = db['youtube_downloadfile'];
                    downloaddatacollection.insert_one(videoDownload.__dict__)
                    downloaddatacollection.insert_one(audioDownload.__dict__)
                    thread1 = DownloadYoutubeThread(videoDownload)
                    thread2 = DownloadYoutubeThread(audioDownload)
                    thread1.start()
                    thread2.start()
    return "no"






def preparedownload(vid,type,url,ext,taskid):
    #创建唯一文件名

    tempfilename = str(uuid.uuid4())+"."+ext;
    today = date.today()
    #创建以日期为标准的文件目录 相对路径 不包含文件名
    filestorepath = str(today.year) + "/" + str(today.month) + "/" + str(today.day)
    #文件的完全路径
    filepath = filestorepath + "/" + tempfilename
    #判断存储路径 不存在就创建
    if not os.path.exists(tmpstorepath+filestorepath):
        os.makedirs(tmpstorepath+filestorepath)
    #获得 文件大小
    response = requests.head(url,proxies={"http":"http://127.0.0.1:8118","https":"https://127.0.0.1:8118"})
    contentlength = response.headers['Content-Length']
    downloaddata =  YoutubeFileDownloadData(filepath,contentlength,type,int(YoutubeDownloadStatus.init),url,ext,taskid)
    return downloaddata

@app.route('/getVideoUrl',methods = ['GET', 'POST'])
def getVideoUrl():

    youtubeUrl = request.form['url'];
    regex = r"(?:www\.)?youtu\.?be(?:\.com)?\/?.*(?:watch|embed)?(?:.*v=|v\/|\/)([\w\-_]+)"
    pattern = re.compile(regex)
    m = pattern.search(youtubeUrl)

    imeilires = Imeili100Result()

    if m == None or m.group(1) == None:
        imeilires.status = int(Imeili100ResultStatus.failed)
        imeilires.res = {"errMsg":"invalid URL"};
        return jsonify(imeilires.__dict__)
    vid = m.group(1)
    youtubeUrl = "https://www.youtube.com/watch?v="+vid
    vurl = extractor.extractVideo(youtubeUrl)
    imeilires.status = int(Imeili100ResultStatus.ok)
    imeilires.res = vurl;
    g_redis.set(vid,json.dumps({"info":vurl}))
    return jsonify(imeilires.__dict__)

def download(downloaddata):
    downloaddatacollection = db['youtube_downloadfile'];

    downloaddatacollection.update_one({"filestorepath": downloaddata.filestorepath},
                                      {'$set': {'downloadStatus': int(YoutubeDownloadStatus.start)}})
    print 'start download====================='+str(int(YoutubeDownloadStatus.start))
    url = downloaddata.url
    destfilepath =  tmpstorepath+downloaddata.filestorepath
    c = pycurl.Curl()
    c.fp = None
    c.setopt(pycurl.FOLLOWLOCATION, 1)
    c.setopt(pycurl.MAXREDIRS, 5)
    c.setopt(pycurl.CONNECTTIMEOUT, 30)
    c.setopt(pycurl.TIMEOUT, 300)
    c.setopt(pycurl.NOSIGNAL, 1)
    c.setopt(pycurl.URL,url)
    c.setopt(pycurl.PROXYTYPE,pycurl.PROXYTYPE_HTTP)
    c.setopt(pycurl.PROXY, "127.0.0.1")
    c.setopt(pycurl.PROXYPORT, 8118)
    c.fp = open(destfilepath, "wb")
    c.setopt(pycurl.WRITEDATA,c.fp)
    c.filename = destfilepath;
    c.url = url
    try:
        c.perform()
    except pycurl.error,e:
        print "Posting to %s resulted in error: %s" % (url, e)
        downloaddatacollection.update_one({"filestorepath": downloaddata.filestorepath},
                                          {'$set': {'downloadStatus': int(YoutubeDownloadStatus.error)}})
        return
    c.close()
    downloaddatacollection.update_one({"filestorepath": downloaddata.filestorepath},
                                      {'$set': {'downloadStatus': int(YoutubeDownloadStatus.done)}})

    print "download done====================" + downloaddata.filestorepath
    startconvert(downloaddata)

def startconvert(downloaddata):

    taskid = downloaddata.taskid
    downloaddataTaskcollection = db['youtube_downloadTask'];
    task = downloaddataTaskcollection.find_one({"_id": ObjectId(taskid)})
    downloaddatacollection = db['youtube_downloadfile'];
    cursor = downloaddatacollection.find({"taskid":taskid})
    files = list(cursor)
    alldone = True
    for data in files:
        if data['downloadStatus'] != int(YoutubeDownloadStatus.done):
            alldone = False
            break;
    if alldone:
        downloaddataTaskcollection.update_one({"_id": ObjectId(taskid)},{'$set':{'status':int(YoutubeTaskStatus.done)}})
        if task['type'] == int(YoutubeDownloadTaskType.merge1080P):
            videofile = None
            audiofile = None
            for data in files:
                if data['filetype'] == int(YoutubeFileType.video):
                    videofile = data
                    continue;
                if data['filetype'] == int(YoutubeFileType.audio):
                    audiofile = data;
            output = os.path.dirname(os.path.realpath(tmpstorepath+videofile['filestorepath'])) +"/"+str(uuid.uuid4())+".avi"
            command = "ffmpeg -i {videofile} -i {audiofile} -map 0 -map 1 -acodec copy -vcodec copy {output}".format(videofile = (tmpstorepath+videofile['filestorepath']),audiofile=(tmpstorepath+audiofile['filestorepath']),output=output)
            subprocess.call(command,shell=True)
            print "convert done===================="
            return
class DownloadYoutubeThread (threading.Thread):
   def __init__(self, downloaddata):
      threading.Thread.__init__(self)
      self.downloaddata = downloaddata
   def run(self):

      #修改

      download(self.downloaddata)


if __name__ == '__main__':
    app.run(host='0.0.0.0',debug=True)




