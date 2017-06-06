# -*- coding: utf-8 -*-
from flask import Flask,Response
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
from utils import YTBJSONEncoder,jsonresponse
import jsonpickle
from youtube_dl.utils import *
compiled_regex_type = type(re.compile(''))
try:
    compat_str = unicode  # Python 2
except NameError:
    compat_str = str
NO_DEFAULT = object()
app = Flask(__name__)
app.config.from_object("config")
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
    return render_template('downloadsrt.html')

@app.route('/convertStatus/',methods = ['GET', 'POST'])
def convertStatus():
    taskid = request.form['taskid'];
    imeilires = Imeili100Result()
    if taskid:
        task = YoutubeDownloadTask.objects.get({"_id":ObjectId(taskid)})
        imeilires.status = int(Imeili100ResultStatus.ok)
        imeilires.res = task
        return jsonpickle.encode(imeilires,unpicklable=False)
    imeilires.status = int(Imeili100ResultStatus.failed)
    imeilires.res = {"errMsg":"没有task"}
    return

@app.route('/record1080/',methods = ['GET', 'POST'])
def record1080():
    vid = request.form['vid'];
    imeilires = Imeili100Result()
    if vid:
        #判断数据库里面有没有

        try:
            task = YoutubeDownloadTask.objects.get({"vid":vid})
        except YoutubeDownloadTask.DoesNotExist:
            task = None
        if task and task > YoutubeTaskStatus.error:
            imeilires.res = task
            imeilires.status = int(Imeili100ResultStatus.ok);
            return jsonpickle.encode(imeilires,unpicklable=False)

        vdicstr = g_redis.get(vid)
        if vdicstr:
            vdic = json.loads(vdicstr)
            info = vdic["info"];
            if info:
               task =  startRecord(vid,info)
               if task:
                   imeilires.res = task
                   imeilires.status = int(Imeili100ResultStatus.ok);
                   return jsonpickle.encode(imeilires,unpicklable=False)
        else:
            youtubeUrl = "https://www.youtube.com/watch?v=" + vid
            vurl = extractor.extractVideo(youtubeUrl)
            if vurl:
                g_redis.set(vid, json.dumps({"info": vurl}))
                g_redis.expire(vid, 3600)
                task = startRecord(vid,vurl)
                if task:
                    imeilires.res = task
                    imeilires.status = int(Imeili100ResultStatus.ok);
                    return jsonpickle.encode(imeilires,unpicklable=False)
    imeilires.status = int(Imeili100ResultStatus.failed);
    imeilires.res = {"errMsg":"error"}
    return jsonpickle.encode(imeilires,unpicklable=False)

def startRecord(vid,vinfo):
    betstaudio = vinfo['best_audio'];
    betstvideo = vinfo['best_video'];
    if betstaudio and betstvideo:
        # 存储task
        task = YoutubeDownloadTask(type=YoutubeDownloadTaskType.merge1080P, status=int(YoutubeTaskStatus.init),
                                   vid=vid).save()
        # Start new Threads
        videoDownload = preparedownload(vid, int(YoutubeFileType.video), betstvideo['url'], betstvideo['ext'], task)
        audioDownload = preparedownload(vid, int(YoutubeFileType.audio), betstaudio['url'], betstaudio['ext'], task)
        thread1 = DownloadYoutubeThread(videoDownload)
        thread2 = DownloadYoutubeThread(audioDownload)
        thread1.start()
        thread2.start()
        return task
    return None


def createUniqueFileName(ext):
    tempfilename = str(uuid.uuid4()) + "." + ext;
    return tempfilename

def getSavePath():
    """存储文件的相对路径 不含文件名"""
    today = date.today()
    # 创建以日期为标准的文件目录 相对路径 不包含文件名
    filestorepath = str(today.year) + "/" + str(today.month) + "/" + str(today.day)+"/"
    return filestorepath

def getSaveFullPath():
    """存储文件的全路径，不含文件名"""
    filepath = tmpstorepath + getSavePath()
    return filepath

def preparedownload(vid,type,url,ext,task):
    #创建唯一文件名
    tempfilename = createUniqueFileName(ext=ext);
    filestorepath = getSavePath()
    #文件的完全路径
    filepath = filestorepath + tempfilename
    #判断存储路径 不存在就创建
    if not os.path.exists(tmpstorepath+filestorepath):
        os.makedirs(tmpstorepath+filestorepath)
    #获得 文件大小
    if app.config['USEPROXY']:
        response = requests.head(url,proxies={"http":"http://127.0.0.1:8118","https":"https://127.0.0.1:8118"})
    else:
        response = requests.head(url)
    contentlength = response.headers['Content-Length']
    downloaddata =  YoutubeFileDownloadData(filestorepath = filepath,contentlength = contentlength,filetype = type,downloadStatus = int(YoutubeDownloadStatus.init),url=url,ext=ext,task=task).save()
    return downloaddata

@app.route('/downloadProgress',methods = ['GET', 'POST'])
def downloadProgress():
    taskid = request.form['taskid'];
    imeilires = Imeili100Result()
    if taskid:
        task = YoutubeDownloadTask.objects.get({"_id":ObjectId(taskid)})
        if task:
            if task.type == int(YoutubeDownloadTaskType.merge1080P):
                videofile = (YoutubeFileDownloadData.objects.get({"task":ObjectId(taskid),"filetype":int(YoutubeFileType.video)}))
                audiofile = (YoutubeFileDownloadData.objects.get(
                    {"task": ObjectId(taskid), "filetype": int(YoutubeFileType.audio)}))
                if videofile is None or audiofile is None:
                    raise  Exception("task 下找不到 video或者audio")
                if videofile.downloadStatus == YoutubeDownloadStatus.done and videofile.downloadStatus == YoutubeDownloadStatus.done:
                    imeilires.status = int(Imeili100ResultStatus.ok)
                    imeilires.res = {"progress": 1};
                    return jsonpickle.encode(imeilires, unpicklable=False)
                else:
                    totle = videofile.contentlength + audiofile.contentlength
                    savedBytes = os.path.getsize(tmpstorepath+videofile.filestorepath) + os.path.getsize(tmpstorepath+audiofile.filestorepath)
                    progress = float("{0:.2f}".format(float(savedBytes)/float(totle)));
                    imeilires.status = int(Imeili100ResultStatus.ok)
                    imeilires.res = {"progress": progress};
                    return jsonpickle.encode(imeilires,unpicklable=False)
    imeilires.status = int(Imeili100ResultStatus.failed)
    imeilires.res = {"errMsg": "task is error"};
    return jsonpickle.encode(imeilires,unpicklable=False)




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
        return jsonresponse(imeilires)
    vid = m.group(1)
    youtubeUrl = "https://www.youtube.com/watch?v="+vid
    try:
        vurl = extractor.extractVideo(youtubeUrl)
    except ExtractorError as e:
        imeilires.status = int(Imeili100ResultStatus.failed)
        imeilires.res = {"errMsg":e.message};
        return jsonresponse(imeilires)
    imeilires.status = int(Imeili100ResultStatus.ok)
    imeilires.res = vurl;
    g_redis.set(vid,json.dumps({"info":vurl}))
    g_redis.expire(vid,3600)

    return jsonresponse(imeilires)

def download(downloaddata):
    downloaddata.downloadStatus = int(YoutubeDownloadStatus.start)
    downloaddata.save()
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
    if app.config['USEPROXY']:
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
        downloaddata.downloadStatus = int(YoutubeDownloadStatus.error)
        downloaddata.save()
        return
    c.close()
    downloaddata.downloadStatus = int(YoutubeDownloadStatus.done)
    downloaddata.save()
    print "download done====================" + downloaddata.filestorepath
    startconvert(downloaddata)

def startconvert(downloaddata):

    task = downloaddata.task
    files = list(YoutubeFileDownloadData.objects.raw({'task':task._id}))
    alldone = True
    for data in files:
        if data.downloadStatus != int(YoutubeDownloadStatus.done):
            alldone = False
            break;
    if alldone:
        task.status =  int(YoutubeTaskStatus.downloadDone)
        task.save()
        if task.type == int(YoutubeDownloadTaskType.merge1080P):
            videofile = None
            audiofile = None
            for data in files:
                if data.filetype == int(YoutubeFileType.video):
                    videofile = data
                    continue;
                if data.filetype == int(YoutubeFileType.audio):
                    audiofile = data;
            ext = "mp4"
            relativepath = getSavePath()+createUniqueFileName(ext)
            task.resultfilepath = relativepath
            task.status = int(YoutubeTaskStatus.converting)
            task.save()
            output = tmpstorepath + relativepath
            command = "ffmpeg -i {videofile} -i {audiofile} -map 0 -map 1 -acodec copy -vcodec copy {output}".format(videofile = (tmpstorepath+videofile.filestorepath),audiofile=(tmpstorepath+audiofile.filestorepath),output=output)
            ret = subprocess.call(command,shell=True)
            if ret == 0:
                task.status = int(YoutubeTaskStatus.convertdone)
            else:
                task.status = int(YoutubeTaskStatus.converterror)
            task.save()
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

    app.run(host='0.0.0.0',debug=app.config['DEBUG'])




