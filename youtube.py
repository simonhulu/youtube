# -*- coding: utf-8 -*-
from flask import Flask,Response,send_file,make_response
from flask import g,request,session
from flask import render_template
from functools import wraps
import youtube_dl
from flask import jsonify
import json
from Imeili100Result import Imeili100Result,Imeili100ResultStatus
from unidecode import unidecode
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
from flask_babel import Babel
import dropbox
compiled_regex_type = type(re.compile(''))
try:
    compat_str = unicode  # Python 2
except NameError:
    compat_str = str
NO_DEFAULT = object()
app = Flask(__name__)
app.config.from_object("config")
babel = Babel(app)
dbx = dropbox.Dropbox('pIR-KPDmuyAAAAAAAAAAETOCjOuDKXGZwqnK8giZ3TQJxEvLMiTD8BYhAb6ptysT')
client = MongoClient()
db = client['youtube']
tmpstorepath = app.config['TMPSTOREPATH']
dropboxtmpstorepath = app.config['DROPBOXTMPSTOREPATH']
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

# def match_languages(f):
#     @wraps(f)
#
#     def decorated(*args, **kwargs):
#         '''Decorator to determine preferred language by Accept
#         Language Header. Switching Languages is provided through
#         an injected unordered list.
#         '''
#
#         cookie = request.cookies.get("App-Language")
#         '''Ping flask for available languages'''
#         AVAILABLE_LOCALES = flask.g.i10n.get_available_locales()
#         if not cookie in AVAILABLE_LOCALES: cookie = None
#
#         if cookie is None:
#             UA_langs = request.headers.get('Accept-Language').split(",")
#             matches = filter(lambda x: x.split(";")[0] in AVAILABLE_LOCALES, UA_langs)
#             lang = matches[0] if matches else AVAILABLE_LOCALES[0]
#             pass_language()
#
#         '''Set best match as global language'''
#         flask.g.lang = cookie if cookie else lang
#         return f(*args, **kwargs)
#
#     return decorated
#
# def pass_language():
#     @after_this_request
#     def set_lang_cookie(response):
#         response.set_cookie('App-Language', flask.g.lang)
#         return response
@babel.localeselector
def get_locale():
    # if a user is logged in, use the locale from the user settings
    print "===================="
    try:
        language = session['language']
        print "language======"+language;
    except KeyError:
        language = None
    if language is not None:
        return language
    # otherwise try to guess the language from the user accept
    # header the browser transmits.  We support de/fr/en in this
    # example.  The best match wins.
    return request.accept_languages.best_match(app.config['LANGUAGES'].keys())

@babel.timezoneselector
def get_timezone():
    user = getattr(g, 'user', None)
    if user is not None:
        return user.timezone

@app.route('/language/<language>')
def set_language(language=None):
    if language in app.config['LANGUAGES']:
        session['language'] = language

    return redirect("/", code=302)
@app.route('/downloadpage/')
def downloadpage(language=None):


    return render_template('downloadpage.html')

@app.route('/')
def hello_world():
    supported_languages = ["en", "zh"]
    lang = get_locale()
    if lang == "zh":
        return redirect("/cn/", code=302)
    return render_template('youtubescreenshot.html')
@app.route('/feedback')
def feedbackpage():
    return render_template('community.html')

@app.route('/cn/')
def index_cn():
    return render_template('youtubescreenshot_zh.html')

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

@app.route('/record/<vid>/<tasktype>/<formatid>/',methods = ['GET', 'POST'])
def record(vid,tasktype,formatid):
    if vid:
        #判断数据库里面有没有
        try:
            expectstatus = YoutubeTaskStatus.convertdone
            def RepresentsInt(s):
                try:
                    int(s)
                    return True
                except ValueError:
                    return False
            if RepresentsInt(tasktype):
                tasktype = int(tasktype)
            else:
                abort(400)
            if tasktype == int(YoutubeDownloadTaskType.normal):
                expectstatus = YoutubeTaskStatus.downloadDone
            tasksCursor = YoutubeDownloadTask.objects.raw({"vid":vid,"status":{"$gte":int(expectstatus)}})
            tasks = list(tasksCursor);
            task = None
            for itask in tasks:
                filepath = tmpstorepath + itask.resultfilepath;
                if os.path.isfile(filepath) :
                    task = itask;
                    break;
        except YoutubeDownloadTask.DoesNotExist:
            task = None
        #直接有未完成task 显示下载界面
        if task:
            return  render_template("record1080P.html",taskid = task._id)
        #没有找到task 创建

        vdicstr = g_redis.get(vid)
        if vdicstr:
            vdic = json.loads(vdicstr)
            info = vdic["info"];
            if info:
               task =  startRecord(vid,info,tasktype,formatid)
               if task:
                   return render_template("record1080P.html",taskid = task._id)
        else:
            #获取info 创建task
            youtubeUrl = "https://www.youtube.com/watch?v=" + vid
            vurl = extractor.extractVideo(youtubeUrl)
            if vurl:
                g_redis.set(vid, json.dumps({"info": vurl}))
                g_redis.expire(vid, 3600)
                task = startRecord(vid,vurl,tasktype,formatid)
                if task:
                    return render_template("record1080P.html",taskid =  task._id)
    return render_template('record1080P.html',taskid="no taskid")


def request_wants_json():
    best = request.accept_mimetypes.best_match(['application/json', 'text/html'])
    return best == 'application/json' and request.accept_mimetypes[best] > request.accept_mimetypes['text/html']

def requestVal(key):
        if request.values:
            return  request.values[key]
        else:
            if request.data:
                str = request.data;
                ijson = jsonpickle.decode(str)
                print ijson
                return  ijson[key]
            else:
                return  request.json[key]


@app.route('/validlink/',methods = ['GET', 'POST'])
def validlink():
    """
    request.args: the key/value pairs in the URL query string
    request.form: the key/value pairs in the body, from a HTML post form, or JavaScript request that isn't JSON encoded
    request.files: the files in the body, which Flask keeps separate from form. HTML forms must use enctype=multipart/form-data or files will not be uploaded.
    request.values: combined args and form, preferring args if keys overlap
    from flask import json

@app.route('/messages', methods = ['POST'])
def api_message():

    if request.headers['Content-Type'] == 'text/plain':
        return "Text Message: " + request.data

    elif request.headers['Content-Type'] == 'application/json':
        return "JSON Message: " + json.dumps(request.json)

    elif request.headers['Content-Type'] == 'application/octet-stream':
        f = open('./binary', 'wb')
        f.write(request.data)
                f.close()
        return "Binary message written!"

    else:
        return "415 Unsupported Media Type ;)"
    """
    youtubeUrl = None
    try:
        youtubeUrl = requestVal('url')
    except Exception as e:
        print  e
        abort(400)
    imeilires = Imeili100Result()
    try:
       vid =  extractor.extract_id(youtubeUrl)
       print vid
    except Exception as e:
        print  e
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


@app.route('/fetchTask/',methods = ['GET', 'POST'])
def fetchTask():
    vid = requestVal('vid')
    format_id = requestVal('format_id')
    tasktype = requestVal('tasktype')
    imeilires = Imeili100Result()
    if vid:
        vdicstr = g_redis.get(vid)
        if vdicstr:
            vdic = json.loads(vdicstr)
            info = vdic["info"];
            if info:
                res = createTask(vid,info,format_id,tasktype)
                task = None;
                if res['task']:
                    task = res['task']
                    task.videoInfo = jsonpickle.decode(task.videoInfo)
                    res['task'] = task
                if res['downloadata']:
                    downloadatas = res['downloadata']
                    lastdownloads = []
                    for download in downloadatas:
                        download.format = jsonpickle.decode(download.format)
                        download.task = str(task._id)
                        lastdownloads.append(download)
                    res['downloadata'] = lastdownloads
                imeilires.status = int(Imeili100ResultStatus.ok);
                imeilires.res = res
                return jsonresponse(imeilires)
        youtubeUrl = "https://www.youtube.com/watch?v=" + vid
        vurl = extractor.extractVideo(youtubeUrl)
        if vurl:
            g_redis.set(vid, json.dumps({"info": vurl}))
            g_redis.expire(vid, 3600)
            res = createTask(vid, vurl, format_id, tasktype)
            if res['task']:
                task = res['task']
                task.videoInfo = jsonpickle.decode(task.videoInfo)
                res['task'] = task
            if res['downloadata']:
                downloadata = res['downloadata']
                downloadata.format = jsonpickle.decode(downloadata.format)
                res['downloadata'] = downloadata
            imeilires.status = int(Imeili100ResultStatus.ok);
            imeilires.res = res
            return jsonresponse(imeilires)
    imeilires.status = Imeili100ResultStatus.failed;
    imeilires.res = {"errMsg":"error"}
    return jsonresponse(imeilires)

def createTask(vid,info,format_id,tasktype):
    if tasktype == YoutubeDownloadTaskType.merge1080P:
        betstaudio = info['best_audio'];
        betstvideo = info['best_video'];
        if betstaudio and betstvideo:
            # 存储task
            task = YoutubeDownloadTask(type=YoutubeDownloadTaskType.merge1080P, status=int(YoutubeTaskStatus.init),
                                       vid=vid, videoInfo=jsonpickle.encode(info)).save()
            # Start new Threads
            videoDownload = preparedownload(vid, int(YoutubeFileType.video), betstvideo['url'], betstvideo['ext'], task,
                                            format=jsonpickle.encode(betstvideo))
            audioDownload = preparedownload(vid, int(YoutubeFileType.audio), betstaudio['url'], betstaudio['ext'], task,
                                            format=jsonpickle.encode(betstaudio))
            return {'task':task,"downloadata":[videoDownload,audioDownload]}
        return None
    else:
        tempFormats = info['video_formats']+info['audio_formats'] + info['formats'];
        downloadFormat = None
        for format in tempFormats:
            if format['format_id'] == format_id :
                downloadFormat = format
                break;
        if downloadFormat != None:
            if tasktype <= YoutubeDownloadTaskType.normal and tasktype>YoutubeDownloadTaskType.unknow:

                task = YoutubeDownloadTask(type=tasktype, status=int(YoutubeTaskStatus.init),
                                       vid=vid, videoInfo=jsonpickle.encode(info)).save()
                videoDownload = preparedownload(vid, int(YoutubeFileType.video), downloadFormat['url'], downloadFormat['ext'],
                                                task,
                                                format=jsonpickle.encode(downloadFormat))
                return {'task':task,"downloadata":[videoDownload]}
            else:
                return None
        else:
            return  None
    return None

    vdicstr = g_redis.get(vid)
    if vdicstr:
        vdic = json.loads(vdicstr)
        info = vdic["info"];
        if info:
            task = startRecord(vid, info)

    else:
        # 获取info 创建task
        youtubeUrl = "https://www.youtube.com/watch?v=" + vid
        vurl = extractor.extractVideo(youtubeUrl)
        if vurl:
            g_redis.set(vid, json.dumps({"info": vurl}))
            g_redis.expire(vid, 3600)
            task = startRecord(vid, vurl)
            if task:
                return render_template("record1080P.html", taskid=task._id)

def startRecord(vid,vinfo,tasktype,formatId):
    if tasktype == int(YoutubeDownloadTaskType.merge1080P):
        betstaudio = vinfo['best_audio'];
        betstvideo = vinfo['best_video'];
        if betstaudio and betstvideo:
            # 存储task
            task = YoutubeDownloadTask(type=YoutubeDownloadTaskType.merge1080P, status=int(YoutubeTaskStatus.init),
                                       vid=vid,videoInfo = jsonpickle.encode(vinfo)).save()
            # Start new Threads
            videoDownload = preparedownload(vid, int(YoutubeFileType.video), betstvideo['url'], betstvideo['ext'], task,format=jsonpickle.encode(betstvideo))
            audioDownload = preparedownload(vid, int(YoutubeFileType.audio), betstaudio['url'], betstaudio['ext'], task,format=jsonpickle.encode(betstaudio))
            thread1 = DownloadYoutubeThread(videoDownload)
            thread2 = DownloadYoutubeThread(audioDownload)
            thread1.start()
            thread2.start()
            g_redis.set(task._id, jsonpickle.encode(task, unpicklable=False))
            g_redis.expire(task._id, 3600)
            return task
    elif tasktype == int(YoutubeDownloadTaskType.normal):
        formats = vinfo['formats']
        selectVideo = None
        for format in formats:
            if format['format_id'] == formatId:
                selectVideo = format
                break;
        if selectVideo:
            # 存储task
            task = YoutubeDownloadTask(type=YoutubeDownloadTaskType.normal, status=int(YoutubeTaskStatus.init),
                                       vid=vid,videoInfo = jsonpickle.encode(vinfo)).save()
            # Start new Threads
            videoDownload = preparedownload(vid, int(YoutubeFileType.mix), selectVideo['url'], selectVideo['ext'], task,format=jsonpickle.encode(selectVideo))
            task.resultfilepath =   videoDownload.filestorepath
            task.save()
            thread1 = DownloadYoutubeThread(videoDownload)
            thread1.start()
            g_redis.set(task._id, jsonpickle.encode(task, unpicklable=False))
            g_redis.expire(task._id, 3600)
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

def preparedownload(vid,type,url,ext,task,format=""):
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
    contentlength = 0
    downloaddata =  YoutubeFileDownloadData(filestorepath = filepath,contentlength = contentlength,filetype = type,downloadStatus = int(YoutubeDownloadStatus.init),url=url,ext=ext,task=task,format=format).save()
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
                elif videofile.downloadStatus >= YoutubeDownloadStatus.done  and audiofile.downloadStatus >= YoutubeDownloadStatus.done:
                    imeilires.status = int(Imeili100ResultStatus.ok)
                    imeilires.res = {"progress": 1};
                    return jsonresponse(imeilires)
                elif videofile.downloadStatus == YoutubeDownloadStatus.error or audiofile.downloadStatus == YoutubeDownloadStatus.error:
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
            else:
                videofile = (
                YoutubeFileDownloadData.objects.get({"task": ObjectId(taskid), "filetype": int(YoutubeFileType.mix)}))
                if videofile is None or videofile.downloadStatus == int(YoutubeDownloadStatus.error):
                    imeilires.status = int(Imeili100ResultStatus.failed)
                    imeilires.res = {"errMsg": "task is error"};
                    return jsonresponse(imeilires)
                elif videofile.downloadStatus >= YoutubeDownloadStatus.done  :
                    imeilires.status = int(Imeili100ResultStatus.ok)
                    imeilires.res = {"progress": 1};
                    return jsonresponse(imeilires)
                elif videofile.downloadStatus == YoutubeDownloadStatus.error :
                    imeilires.status = int(Imeili100ResultStatus.failed)
                    imeilires.res = {"errMsg": "task is error"};
                    return jsonresponse(imeilires)
                else:
                    totle = videofile.contentlength
                    savedBytes = os.path.getsize(tmpstorepath+videofile.filestorepath)
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

@app.route('/fetchVideo',methods = ['GET', 'POST'])
def fetchVideo():
    imeilires = Imeili100Result()
    if request.method == "GET":
        vurl = request.args['vurl'];
    else:
        vurl = request.form['vurl'];
    try:
       vid =  extractor.extract_id(vurl)
    except:
        imeilires.status = int(Imeili100ResultStatus.failed)
        imeilires.res = {"errMsg":"invalid Link"};
        return jsonresponse(imeilires)
    youtubeUrl = "https://www.youtube.com/watch?v=" + vid
    vurljsonstr = g_redis.get(vid)
    vurl = None
    if vurljsonstr:
        info = json.loads(vurljsonstr)
        if info:
            vurl = info["info"];
            imeilires.status = int(Imeili100ResultStatus.ok)
            custominfo = {"title":vurl['title'],'url':vurl['best_video']['url']}
            imeilires.res = custominfo;
            return jsonresponse(imeilires)
    try:
        vurl = extractor.extractVideo(youtubeUrl)
    except ExtractorError as e:
        imeilires.status = int(Imeili100ResultStatus.failed)
        imeilires.res = {"errMsg":e.message};
        return jsonresponse(imeilires)
    imeilires.status = int(Imeili100ResultStatus.ok)
    custominfo = {"title": vurl['title'], 'url': vurl['best_video']['url']}
    imeilires.res = custominfo;
    return jsonresponse(imeilires)
    g_redis.set(vid,json.dumps({"info":vurl}))
    g_redis.expire(vid,3600)

    return jsonresponse(imeilires)

@app.route('/downloadtask',methods = ['GET', 'POST'])
def downloadtask():
    if request.method == "GET":
        taskid = request.args['taskid'];
    else:
        taskid = request.form['taskid'];
    if taskid:
        try:
            task = YoutubeDownloadTask.objects.get({"_id": ObjectId(taskid)})
        except YoutubeDownloadTask.DoesNotExist:
            abort(404)

        if task  and    ((task.type != YoutubeDownloadTaskType.merge1080P and task.status>= YoutubeTaskStatus.downloadDone) or  (task.type == YoutubeDownloadTaskType.merge1080P and task.status > YoutubeTaskStatus.converterror)):

            vid = task.vid;
            file_basename = "download.mp4"
            server_path = task.resultfilepath;
            file_size = 0
            if os.path.isfile(tmpstorepath + server_path):
                file_size = os.path.getsize(tmpstorepath + server_path);
            files = list(YoutubeFileDownloadData.objects.raw({'task': ObjectId(taskid)}))
            # 全部下载完毕
            videofile = None
            for data in files:
                if data.filetype == int(YoutubeFileType.video) or data.filetype == int(YoutubeFileType.mix):
                    videofile = data
                    break

            if videofile:
                    title = "download"
                    if task.videoInfo:
                        try:
                            info = jsonpickle.decode(task.videoInfo);
                            title = info['title'];
                        except Exception as e:
                            title = "download"
                    file_basename = title+"." + videofile.ext;
                    response = make_response()
                    response.headers['Content-Description'] = 'File Transfer'
                    response.headers['Cache-Control'] = 'no-cache'
                    response.headers['Content-Type'] = 'application/octet-stream'
                    response.headers['Content-Disposition'] = "attachment; filename='%s'" % unidecode(file_basename)
                    response.headers['Content-Length'] = file_size
                    response.headers['X-Accel-Redirect'] = '/downloadvideo/'+server_path  # nginx: http://wiki.nginx.org/NginxXSendfile
                    return response
            return redirect(("/" + task.resultfilepath), code=302)
        taskjsonstr = g_redis.get(taskid)
        if taskjsonstr:
            taskdic = jsonpickle.decode(taskjsonstr)
            # return redirect(("/"+taskdic["resultfilepath"]),code=302)
            vid =  taskdic['vid'];
            vinfo = g_redis.get(vid);
            file_basename = "download.mp4"

            server_path = taskdic["resultfilepath"];
            server_path = task.resultfilepath;
            file_size = os.path.getsize(tmpstorepath +  server_path);
            files = list(YoutubeFileDownloadData.objects.raw({'task': ObjectId(taskid)}))
            # 全部下载完毕
            videofile = None
            for data in files:
                if data.filetype >= int(YoutubeFileType.video):
                    videofile = data
                    break
            if videofile:
                    title = "download"
                    if task.videoInfo:
                        try:
                            info = jsonpickle.decode(task.videoInfo);
                            title = info['title'];
                        except Exception as e:
                            title = "download"
                    file_basename = title+"." + videofile.ext;

            response = make_response()
            response.headers['Content-Description'] = 'File Transfer'
            response.headers['Cache-Control'] = 'no-cache'
            response.headers['Content-Type'] = 'application/octet-stream'
            response.headers['Content-Disposition'] = "attachment; filename='%s'" % unidecode(file_basename)
            response.headers['Content-Length'] = file_size
            response.headers['X-Accel-Redirect'] = '/downloadvideo/'+server_path  # nginx: http://wiki.nginx.org/NginxXSendfile
            return response
    abort(404)


@app.route('/convertProgress',methods = ['GET', 'POST'])
def convertProgress():
    taskid = request.form['taskid'];
    imeilires = Imeili100Result()
    progress = 0;
    if taskid:
        try:
            task = YoutubeDownloadTask.objects.get({"_id": ObjectId(taskid)})
        except YoutubeDownloadTask.DoesNotExist:
            imeilires.status = int(Imeili100ResultStatus.failed)
            imeilires.res = {"errMsg": "task is error"};
            return jsonresponse(imeilires)
        if task.type != int(YoutubeDownloadTaskType.merge1080P):
            imeilires.status = int(Imeili100ResultStatus.ok)
            imeilires.res = {"progress": 100};
            return jsonresponse(imeilires)
        if task.status > YoutubeTaskStatus.converterror:
            imeilires.status = int(Imeili100ResultStatus.ok)
            imeilires.res = {"progress": 100};
            return jsonresponse(imeilires)
        taskjsonstr = g_redis.get(taskid)
        if taskjsonstr:
            taskdic = jsonpickle.decode(taskjsonstr)
            progress =  taskdic["progress"]
            imeilires.status = int(Imeili100ResultStatus.ok)
            imeilires.res = {"progress": progress};
            return jsonresponse(imeilires)
        else:
            task = YoutubeDownloadTask.objects.get({"_id":ObjectId(taskid)})
            if task.status > YoutubeTaskStatus.converterror:
                imeilires.status = int(Imeili100ResultStatus.ok)
                imeilires.res = {"progress": 100};
                return jsonresponse(imeilires)
    imeilires.status = int(Imeili100ResultStatus.failed)
    imeilires.res = {"errMsg": "task is error"};
    return jsonresponse(imeilires)

@app.route('/getVideoUrl',methods = ['GET', 'POST'])
def getVideoUrl():
    youtubeUrl = None;
    try:
        youtubeUrl = requestVal('url')
    except Exception as e:
        abort(400)
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
        if task.type == int(YoutubeDownloadTaskType.merge1080P):
            startconvert(downloaddata)
        else:
            task.status = int(YoutubeTaskStatus.downloadDone)
            task.save()
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

def deleteTaskdata(task):
    if task.type == YoutubeTaskStatus.dropboxdone:
        file_path = tmpstorepath + task.resultfilepath
        if os.path.isfile(file_path):
            os.remove(file_path)

def upload2DropBox(task):
    #刚刚转换完
    if task.type != YoutubeTaskStatus.dropboxing  :
        task.type = YoutubeTaskStatus.dropboxing;
        task.save()
        file_path = tmpstorepath + task.resultfilepath
        dest_path = dropboxtmpstorepath + task.resultfilepath
        f = open(file_path)
        file_size = os.path.getsize(file_path)
        CHUNK_SIZE = 4 * 1024 * 1024
        if file_size <= CHUNK_SIZE:

            dbx.files_upload(f, dest_path)
            task.type = YoutubeTaskStatus.dropboxdone
            task.save()
        else:
            try:
                upload_session_start_result = dbx.files_upload_session_start(f.read(CHUNK_SIZE))
                cursor = dropbox.files.UploadSessionCursor(session_id=upload_session_start_result.session_id,
                                                           offset=f.tell())
                commit = dropbox.files.CommitInfo(path=dest_path)

                while f.tell() < file_size:
                    if ((file_size - f.tell()) <= CHUNK_SIZE):
                        dbx.files_upload_session_finish(f.read(CHUNK_SIZE),
                                                              cursor,
                                                              commit)
                        task.type = YoutubeTaskStatus.dropboxdone
                        task.save()
                    else:
                        dbx.files_upload_session_append(f.read(CHUNK_SIZE),
                                                        cursor.session_id,
                                                        cursor.offset)
                        cursor.offset = f.tell()
                        print cursor.offset * 100 / file_size
            except Exception as e:
                task.type = YoutubeTaskStatus.dropboxerror
                task.save()


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
            print  command
            def status_handler(old, new):
                task.progress = new
                g_redis.set(task._id,jsonpickle.encode(task,unpicklable=False))
                g_redis.expire(task._id, 3600)
                if new == 100 :
                    task.status = int(YoutubeTaskStatus.convertdone)
                    task.save()
                    deleteDownloaddata(videofile)
                    deleteDownloaddata(audiofile)
                    # upload2DropBox(task)
            def finish_handler(err):
                if err:
                    print "==================converterror"
                    task.status = int(YoutubeTaskStatus.converterror)
                    task.save()
                else:
                    print "==================convertdone"
                    task.status = int(YoutubeTaskStatus.convertdone)
                    task.save()
                    task.progress = 100
                    g_redis.set(task._id, jsonpickle.encode(task, unpicklable=False))
                    g_redis.expire(task._id, 3600)
                    deleteDownloaddata(videofile)
                    deleteDownloaddata(audiofile)
                    # upload2DropBox(task)
            task.progress = 0
            g_redis.set(task._id, jsonpickle.encode(task, unpicklable=False))
            g_redis.expire(task._id, 3600)
            try:
                runner.run_session(command, status_handler=status_handler,finish_handler=finish_handler)
            except OSError:
                print "==================converterror"
                task.status = int(YoutubeTaskStatus.converterror)
            except ValueError:
                print "==================converterror"
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
    app.secret_key = '123456789'
    app.run(host='0.0.0.0',debug=app.config['DEBUG'])




