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
from flask import abort, redirect, url_for
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
from flask import current_app
from ffmpeg import FFMPegRunner
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
tmpstorepath = app.config['TMPSTOREPATH']
g_redis = redis.StrictRedis(host='localhost',port=6379,db=0)

service_args = [
    '--proxy=127.0.0.1:1080',
    '--proxy-type=socks5',
    ]
# firefox_capabilities = DesiredCapabilities.CHROME
# firefox_capabilities['marionette'] = True
# driver = webdriver.PhantomJS(executable_path='/usr/local/bin/phantomjs')
# driver = webdriver.Chrome(executable_path='/usr/local/bin/chromedriver',service_args=service_args)

extractor = MyYoutubeExtractor(useproxy=app.config['USEPROXY']);
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

@app.route('/record/<vid>/',methods = ['GET', 'POST'])
def record(vid):
    if vid:
        #判断数据库里面有没有
        try:
            task = YoutubeDownloadTask.objects.get({"vid":vid})
        except YoutubeDownloadTask.DoesNotExist:
            task = None
        #直接有未完成task 显示下载界面
        if task and task.status > YoutubeTaskStatus.error:
            return  render_template("record1080P.html",taskid = task._id)
        #没有找到task 创建

        vdicstr = g_redis.get(vid)
        if vdicstr:
            vdic = json.loads(vdicstr)
            info = vdic["info"];
            if info:
               task =  startRecord(vid,info)
               if task:
                   return render_template("record1080P.html",taskid = task._id)
        else:
            #获取info 创建task
            youtubeUrl = "https://www.youtube.com/watch?v=" + vid
            vurl = extractor.extractVideo(youtubeUrl)
            if vurl:
                g_redis.set(vid, json.dumps({"info": vurl}))
                g_redis.expire(vid, 3600)
                task = startRecord(vid,vurl)
                if task:
                    return render_template("record1080P.html",taskid =  task._id)
    return render_template('record1080P.html',taskid="no taskid")

@app.route('/validlink/',methods = ['GET', 'POST'])
def validlink():
    youtubeUrl = request.form['url'];
    imeilires = Imeili100Result()
    try:
       vid =  extractor.extract_id(youtubeUrl)
    except:
        imeilires.status = int(Imeili100ResultStatus.failed)
        imeilires.res = {"errMsg":"invalid Link"};
        return jsonresponse(imeilires)
    imeilires.status = int(Imeili100ResultStatus.ok)
    imeilires.res = {"vid":vid}
    return jsonresponse(imeilires)


@app.route('/cleandownload/',methods = ['GET', 'POST'])
def cleandownload():
    files =  YoutubeFileDownloadData.objects.all()
    for data in files:
        try:
            deleteDownloaddata(data)
        except Exception as e:
            return e.message
    return "success"

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
        try:
            task = YoutubeDownloadTask.objects.get({"_id":ObjectId(taskid)})
        except YoutubeDownloadTask.DoesNotExist:
            print "no task"
            imeilires.status = int(Imeili100ResultStatus.failed)
            imeilires.res = {"errMsg": "task is error"};
            return jsonresponse(imeilires)
        if task:
            if task.type == int(YoutubeDownloadTaskType.merge1080P):
                videofile = (YoutubeFileDownloadData.objects.get({"task":ObjectId(taskid),"filetype":int(YoutubeFileType.video)}))
                audiofile = (YoutubeFileDownloadData.objects.get(
                    {"task": ObjectId(taskid), "filetype": int(YoutubeFileType.audio)}))
                if videofile is None or audiofile is None or videofile.downloadStatus == int(YoutubeDownloadStatus.error) or audiofile.downloadStatus == int(YoutubeDownloadStatus.error) :
                    imeilires.status = int(Imeili100ResultStatus.failed)
                    imeilires.res = {"errMsg": "task is error"};
                    return jsonresponse(imeilires)
                if videofile.downloadStatus >= YoutubeDownloadStatus.done  and videofile.downloadStatus >= YoutubeDownloadStatus.done:
                    imeilires.status = int(Imeili100ResultStatus.ok)
                    imeilires.res = {"progress": 1};
                    return jsonresponse(imeilires)
                elif videofile.downloadStatus == YoutubeDownloadStatus.error or videofile.downloadStatus == YoutubeDownloadStatus.error:
                    imeilires.status = int(Imeili100ResultStatus.failed)
                    imeilires.res = {"errMsg": "task is error"};
                    return jsonresponse(imeilires)
                else:
                    totle = videofile.contentlength + audiofile.contentlength
                    savedBytes = os.path.getsize(tmpstorepath+videofile.filestorepath) + os.path.getsize(tmpstorepath+audiofile.filestorepath)
                    try:
                        progress = float("{0:.2f}".format(float(savedBytes)/float(totle)))
                    except Exception as e:
                        progress = 0 ;
                    imeilires.status = int(Imeili100ResultStatus.ok)
                    imeilires.res = {"progress": progress};
                    return jsonresponse(imeilires)
    imeilires.status = int(Imeili100ResultStatus.failed)
    imeilires.res = {"errMsg": "task is error"};
    return jsonresponse(imeilires)

@app.route('/downloadtask',methods = ['GET', 'POST'])
def downloadtask():
    if request.method == "GET":
        taskid = request.args['taskid'];
    else:
        taskid = request.form['taskid'];
    if taskid:
        taskjsonstr = g_redis.get(taskid)
        if taskjsonstr:
            taskdic = jsonpickle.decode(taskjsonstr)
            return redirect(("/"+taskdic["resultfilepath"]),code=302)

    abort(404)


@app.route('/convertProgress',methods = ['GET', 'POST'])
def convertProgress():
    taskid = request.form['taskid'];
    imeilires = Imeili100Result()
    progress = 0;
    if taskid:
        taskjsonstr = g_redis.get(taskid)
        if taskjsonstr:
            taskdic = jsonpickle.decode(taskjsonstr)
            progress =  taskdic["progress"]
            imeilires.status = int(Imeili100ResultStatus.ok)
            imeilires.res = {"progress": progress};
            return jsonresponse(imeilires)
    imeilires.status = int(Imeili100ResultStatus.failed)
    imeilires.res = {"errMsg": "task is error"};
    return jsonresponse(imeilires)

@app.route('/getVideoUrl',methods = ['GET', 'POST'])
def getVideoUrl():

    youtubeUrl = request.form['url'];
    imeilires = Imeili100Result()
    try:
       vid =  extractor.extract_id(youtubeUrl)
    except:
        imeilires.status = int(Imeili100ResultStatus.failed)
        imeilires.res = {"errMsg":"invalid URL"};
        return jsonresponse(imeilires)
    youtubeUrl = "https://www.youtube.com/watch?v=" + vid
    vurljsonstr = g_redis.get(vid)
    vurl = None
    if vurljsonstr:
        info = json.loads(vurljsonstr)
        if info:
            vurl = info["info"];
            imeilires.status = int(Imeili100ResultStatus.ok)
            imeilires.res = vurl;
            return jsonresponse(imeilires)
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

class ProgressStorage:
    def __init__(self,downloadata):
        self.contents = ''
        self.line = 0
        self.downloadata = downloadata
        self.download_t = 0 ;

    def progress(self,download_t, download_d, upload_t, upload_d):
        if self.download_t <=0 :
            self.download_t = download_t
            if self.download_t > 0:
                self.downloadata.contentlength= self.download_t
                self.downloadata.save()
    def store(self, buf):
        self.line = self.line + 1
        self.contents = "%s%i: %s" % (self.contents, self.line, buf)
        # print self.contents

    def __str__(self):
        return self.contents


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
    c.setopt(c.NOPROGRESS, False)
    c.setopt(pycurl.URL,url)
    s = ProgressStorage(downloaddata)

    c.setopt(c.XFERINFOFUNCTION, s.progress)
    if app.config['USEPROXY']:
        c.setopt(pycurl.PROXYTYPE,pycurl.PROXYTYPE_HTTP)
        c.setopt(pycurl.PROXY, "127.0.0.1")
        c.setopt(pycurl.PROXYPORT, 8118)
    c.fp = open(destfilepath, "wb")
    c.setopt(pycurl.WRITEDATA,c.fp)
    c.filename = destfilepath;
    c.url = url
    task = downloaddata.task;
    try:
        c.perform()
        contentlength = c.getinfo(c.CONTENT_LENGTH_DOWNLOAD)
        print "contentlength============"+str(contentlength)
        downloaddata.contentlength = contentlength
        downloaddata.downloadStatus = int(YoutubeDownloadStatus.done)
        downloaddata.save()
        print "download done====================" + downloaddata.filestorepath
        startconvert(downloaddata)
    except pycurl.error,e:
        print "Posting to %s resulted in error: %s" % (url, e)
        downloaddata.downloadStatus = int(YoutubeDownloadStatus.error)
        downloaddata.save()
        task.status = int(YoutubeTaskStatus.error)
        task.save()
        print "download error====================" + downloaddata.filestorepath
    c.close()


def deleteDownloaddata(downloaddata):
    absfilepath = tmpstorepath+ downloaddata.filestorepath
    if os.path.isfile(absfilepath) and  downloaddata.downloadStatus == int(YoutubeDownloadStatus.done) and downloaddata.downloadStatus != int(YoutubeDownloadStatus.discard):
        print "delete"+absfilepath
        os.remove(absfilepath)
        downloaddata.downloadStatus = int(YoutubeDownloadStatus.discard);
        downloaddata.save();
        return True
    else:
        return False



def startconvert(downloaddata):

    task = downloaddata.task
    if task.status <= int(YoutubeTaskStatus.error):
        return ;
    files = list(YoutubeFileDownloadData.objects.raw({'task':task._id}))
    alldone = True
    for data in files:
        if data.downloadStatus < int(YoutubeDownloadStatus.done):
            alldone = False
            break;
    #全部下载完毕
    if alldone:
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
            re_duration = re.compile('Duration: (\d{2}):(\d{2}):(\d{2}).(\d{2})[^\d]*', re.U)
            re_position = re.compile('time=(\d{2}):(\d{2}):(\d{2})\.(\d{2})\d*', re.U | re.I)
            command = "ffmpeg -i {videofile} -i {audiofile} -map 0 -map 1 -acodec copy -vcodec copy {output}".format(videofile = (tmpstorepath+videofile.filestorepath),audiofile=(tmpstorepath+audiofile.filestorepath),output=output)
            runner = FFMPegRunner()
            def status_handler(old, new):
                task.progress = new
                g_redis.set(task._id,jsonpickle.encode(task,unpicklable=False))
                g_redis.expire(task._id, 3600)
                if new == 100 :
                    task.status = int(YoutubeTaskStatus.convertdone)
                    task.save()
                    deleteDownloaddata(videofile)
                    deleteDownloaddata(audiofile)
            def finish_handler(err):
                if err:
                    task.status = int(YoutubeTaskStatus.converterror)
                    task.save()
                else:
                    task.status = int(YoutubeTaskStatus.convertdone)
                    task.save()
                    task.progress = 100
                    g_redis.set(task._id, jsonpickle.encode(task, unpicklable=False))
                    g_redis.expire(task._id, 3600)
                    deleteDownloaddata(videofile)
                    deleteDownloaddata(audiofile)
            task.progress = 0
            g_redis.set(task._id, jsonpickle.encode(task, unpicklable=False))
            g_redis.expire(task._id, 3600)
            try:
                runner.run_session(command, status_handler=status_handler,finish_handler=finish_handler)
            except OSError:
                print 1
                task.status = int(YoutubeTaskStatus.converterror)
            except ValueError:
                print 2
                task.status = int(YoutubeTaskStatus.converterror)
            task.save()

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




