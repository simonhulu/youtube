from enum import IntEnum
from mongoengine import *
connect('youtube')
class Comment(EmbeddedDocument)
class YoutubeFileType(IntEnum):
       unknow, video,audio = range(3)


class YoutubeDownloadTaskType(IntEnum):
    unknow, onlyVideo, onlyAudio,merge1080P = range(4)

class YoutubeDownloadStatus(IntEnum):
    unknow, init, start,downloading,done,error = range(6)

class YoutubeTaskStatus(IntEnum):
    unknow, init, start,downloading,done,error = range(6)

class YoutubeDownloadTask:
    def __init__(self,type,status,vid):
        self.type = type
        self.vid = vid;
        self.status = status
class YoutubeFileDownloadData:
    def __init__(self,filestorepath,contentlength,fileype,downloadStatus,url,ext,taskid):
        self.filestorepath = filestorepath;
        self.contentlength = contentlength;
        self.filetype = fileype
        self.downloadStatus = downloadStatus
        self.url = url;
        self.ext = ext;
        self.taskid = taskid ;