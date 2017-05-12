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
from fake_useragent import UserAgent
import requests
compiled_regex_type = type(re.compile(''))
try:
    compat_str = unicode  # Python 2
except NameError:
    compat_str = str
NO_DEFAULT = object()
class MyYoutubeExtractor(InfoExtractor):
    IE_DESC = 'YouTube.com'
    _VALID_URL = r"""(?x)^
                         (
                             (?:https?://|//)                                    # http(s):// or protocol-independent URL
                             (?:(?:(?:(?:\w+\.)?[yY][oO][uU][tT][uU][bB][eE](?:-nocookie)?\.com/|
                                (?:www\.)?deturl\.com/www\.youtube\.com/|
                                (?:www\.)?pwnyoutube\.com/|
                                (?:www\.)?yourepeat\.com/|
                                tube\.majestyc\.net/|
                                youtube\.googleapis\.com/)                        # the various hostnames, with wildcard subdomains
                             (?:.*?\#/)?                                          # handle anchor (#/) redirect urls
                             (?:                                                  # the various things that can precede the ID:
                                 (?:(?:v|embed|e)/(?!videoseries))                # v/ or embed/ or e/
                                 |(?:                                             # or the v= param in all its forms
                                     (?:(?:watch|movie)(?:_popup)?(?:\.php)?/?)?  # preceding watch(_popup|.php) or nothing (like /?v=xxxx)
                                     (?:\?|\#!?)                                  # the params delimiter ? or # or #!
                                     (?:.*?[&;])??                                # any other preceding param (like /?s=tuff&v=xxxx or ?s=tuff&amp;v=V36LpHqtcDY)
                                     v=
                                 )
                             ))
                             |(?:
                                youtu\.be|                                        # just youtu.be/xxxx
                                vid\.plus|                                        # or vid.plus/xxxx
                                zwearz\.com/watch|                                # or zwearz.com/watch/xxxx
                             )/
                             |(?:www\.)?cleanvideosearch\.com/media/action/yt/watch\?videoId=
                             )
                         )?                                                       # all until now is optional -> you can pass the naked ID
                         ([0-9A-Za-z_-]{11})                                      # here is it! the YouTube video ID
                         (?!.*?\blist=
                            (?:
                                %(playlist_id)s|                                  # combined list/video URLs are handled by the playlist IE
                                WL                                                # WL are handled by the watch later IE
                            )
                         )
                         (?(1).+)?                                                # if we found the ID, everything can follow
                         $""" % {'playlist_id': YoutubeBaseInfoExtractor._PLAYLIST_ID_RE}
    _NEXT_URL_RE = r'[\?&]next_url=([^&]+)'
    _formats = {
        '5': {'ext': 'flv', 'width': 400, 'height': 240, 'acodec': 'mp3', 'abr': 64, 'vcodec': 'h263'},
        '6': {'ext': 'flv', 'width': 450, 'height': 270, 'acodec': 'mp3', 'abr': 64, 'vcodec': 'h263'},
        '13': {'ext': '3gp', 'acodec': 'aac', 'vcodec': 'mp4v'},
        '17': {'ext': '3gp', 'width': 176, 'height': 144, 'acodec': 'aac', 'abr': 24, 'vcodec': 'mp4v'},
        '18': {'ext': 'mp4', 'width': 640, 'height': 360, 'acodec': 'aac', 'abr': 96, 'vcodec': 'h264'},
        '22': {'ext': 'mp4', 'width': 1280, 'height': 720, 'acodec': 'aac', 'abr': 192, 'vcodec': 'h264'},
        '34': {'ext': 'flv', 'width': 640, 'height': 360, 'acodec': 'aac', 'abr': 128, 'vcodec': 'h264'},
        '35': {'ext': 'flv', 'width': 854, 'height': 480, 'acodec': 'aac', 'abr': 128, 'vcodec': 'h264'},
        # itag 36 videos are either 320x180 (BaW_jenozKc) or 320x240 (__2ABJjxzNo), abr varies as well
        '36': {'ext': '3gp', 'width': 320, 'acodec': 'aac', 'vcodec': 'mp4v'},
        '37': {'ext': 'mp4', 'width': 1920, 'height': 1080, 'acodec': 'aac', 'abr': 192, 'vcodec': 'h264'},
        '38': {'ext': 'mp4', 'width': 4096, 'height': 3072, 'acodec': 'aac', 'abr': 192, 'vcodec': 'h264'},
        '43': {'ext': 'webm', 'width': 640, 'height': 360, 'acodec': 'vorbis', 'abr': 128, 'vcodec': 'vp8'},
        '44': {'ext': 'webm', 'width': 854, 'height': 480, 'acodec': 'vorbis', 'abr': 128, 'vcodec': 'vp8'},
        '45': {'ext': 'webm', 'width': 1280, 'height': 720, 'acodec': 'vorbis', 'abr': 192, 'vcodec': 'vp8'},
        '46': {'ext': 'webm', 'width': 1920, 'height': 1080, 'acodec': 'vorbis', 'abr': 192, 'vcodec': 'vp8'},
        '59': {'ext': 'mp4', 'width': 854, 'height': 480, 'acodec': 'aac', 'abr': 128, 'vcodec': 'h264'},
        '78': {'ext': 'mp4', 'width': 854, 'height': 480, 'acodec': 'aac', 'abr': 128, 'vcodec': 'h264'},

        # 3D videos
        '82': {'ext': 'mp4', 'height': 360, 'format_note': '3D', 'acodec': 'aac', 'abr': 128, 'vcodec': 'h264',
               'preference': -20},
        '83': {'ext': 'mp4', 'height': 480, 'format_note': '3D', 'acodec': 'aac', 'abr': 128, 'vcodec': 'h264',
               'preference': -20},
        '84': {'ext': 'mp4', 'height': 720, 'format_note': '3D', 'acodec': 'aac', 'abr': 192, 'vcodec': 'h264',
               'preference': -20},
        '85': {'ext': 'mp4', 'height': 1080, 'format_note': '3D', 'acodec': 'aac', 'abr': 192, 'vcodec': 'h264',
               'preference': -20},
        '100': {'ext': 'webm', 'height': 360, 'format_note': '3D', 'acodec': 'vorbis', 'abr': 128, 'vcodec': 'vp8',
                'preference': -20},
        '101': {'ext': 'webm', 'height': 480, 'format_note': '3D', 'acodec': 'vorbis', 'abr': 192, 'vcodec': 'vp8',
                'preference': -20},
        '102': {'ext': 'webm', 'height': 720, 'format_note': '3D', 'acodec': 'vorbis', 'abr': 192, 'vcodec': 'vp8',
                'preference': -20},

        # Apple HTTP Live Streaming
        '91': {'ext': 'mp4', 'height': 144, 'format_note': 'HLS', 'acodec': 'aac', 'abr': 48, 'vcodec': 'h264',
               'preference': -10},
        '92': {'ext': 'mp4', 'height': 240, 'format_note': 'HLS', 'acodec': 'aac', 'abr': 48, 'vcodec': 'h264',
               'preference': -10},
        '93': {'ext': 'mp4', 'height': 360, 'format_note': 'HLS', 'acodec': 'aac', 'abr': 128, 'vcodec': 'h264',
               'preference': -10},
        '94': {'ext': 'mp4', 'height': 480, 'format_note': 'HLS', 'acodec': 'aac', 'abr': 128, 'vcodec': 'h264',
               'preference': -10},
        '95': {'ext': 'mp4', 'height': 720, 'format_note': 'HLS', 'acodec': 'aac', 'abr': 256, 'vcodec': 'h264',
               'preference': -10},
        '96': {'ext': 'mp4', 'height': 1080, 'format_note': 'HLS', 'acodec': 'aac', 'abr': 256, 'vcodec': 'h264',
               'preference': -10},
        '132': {'ext': 'mp4', 'height': 240, 'format_note': 'HLS', 'acodec': 'aac', 'abr': 48, 'vcodec': 'h264',
                'preference': -10},
        '151': {'ext': 'mp4', 'height': 72, 'format_note': 'HLS', 'acodec': 'aac', 'abr': 24, 'vcodec': 'h264',
                'preference': -10},

        # DASH mp4 video
        '133': {'ext': 'mp4', 'height': 240, 'format_note': 'DASH video', 'vcodec': 'h264'},
        '134': {'ext': 'mp4', 'height': 360, 'format_note': 'DASH video', 'vcodec': 'h264'},
        '135': {'ext': 'mp4', 'height': 480, 'format_note': 'DASH video', 'vcodec': 'h264'},
        '136': {'ext': 'mp4', 'height': 720, 'format_note': 'DASH video', 'vcodec': 'h264'},
        '137': {'ext': 'mp4', 'height': 1080, 'format_note': 'DASH video', 'vcodec': 'h264'},
        '138': {'ext': 'mp4', 'format_note': 'DASH video', 'vcodec': 'h264'},
    # Height can vary (https://github.com/rg3/youtube-dl/issues/4559)
        '160': {'ext': 'mp4', 'height': 144, 'format_note': 'DASH video', 'vcodec': 'h264'},
        '212': {'ext': 'mp4', 'height': 480, 'format_note': 'DASH video', 'vcodec': 'h264'},
        '264': {'ext': 'mp4', 'height': 1440, 'format_note': 'DASH video', 'vcodec': 'h264'},
        '298': {'ext': 'mp4', 'height': 720, 'format_note': 'DASH video', 'vcodec': 'h264', 'fps': 60},
        '299': {'ext': 'mp4', 'height': 1080, 'format_note': 'DASH video', 'vcodec': 'h264', 'fps': 60},
        '266': {'ext': 'mp4', 'height': 2160, 'format_note': 'DASH video', 'vcodec': 'h264'},

        # Dash mp4 audio
        '139': {'ext': 'm4a', 'format_note': 'DASH audio', 'acodec': 'aac', 'abr': 48, 'container': 'm4a_dash'},
        '140': {'ext': 'm4a', 'format_note': 'DASH audio', 'acodec': 'aac', 'abr': 128, 'container': 'm4a_dash'},
        '141': {'ext': 'm4a', 'format_note': 'DASH audio', 'acodec': 'aac', 'abr': 256, 'container': 'm4a_dash'},
        '256': {'ext': 'm4a', 'format_note': 'DASH audio', 'acodec': 'aac', 'container': 'm4a_dash'},
        '258': {'ext': 'm4a', 'format_note': 'DASH audio', 'acodec': 'aac', 'container': 'm4a_dash'},
        '325': {'ext': 'm4a', 'format_note': 'DASH audio', 'acodec': 'dtse', 'container': 'm4a_dash'},
        '328': {'ext': 'm4a', 'format_note': 'DASH audio', 'acodec': 'ec-3', 'container': 'm4a_dash'},

        # Dash webm
        '167': {'ext': 'webm', 'height': 360, 'width': 640, 'format_note': 'DASH video', 'container': 'webm',
                'vcodec': 'vp8'},
        '168': {'ext': 'webm', 'height': 480, 'width': 854, 'format_note': 'DASH video', 'container': 'webm',
                'vcodec': 'vp8'},
        '169': {'ext': 'webm', 'height': 720, 'width': 1280, 'format_note': 'DASH video', 'container': 'webm',
                'vcodec': 'vp8'},
        '170': {'ext': 'webm', 'height': 1080, 'width': 1920, 'format_note': 'DASH video', 'container': 'webm',
                'vcodec': 'vp8'},
        '218': {'ext': 'webm', 'height': 480, 'width': 854, 'format_note': 'DASH video', 'container': 'webm',
                'vcodec': 'vp8'},
        '219': {'ext': 'webm', 'height': 480, 'width': 854, 'format_note': 'DASH video', 'container': 'webm',
                'vcodec': 'vp8'},
        '278': {'ext': 'webm', 'height': 144, 'format_note': 'DASH video', 'container': 'webm', 'vcodec': 'vp9'},
        '242': {'ext': 'webm', 'height': 240, 'format_note': 'DASH video', 'vcodec': 'vp9'},
        '243': {'ext': 'webm', 'height': 360, 'format_note': 'DASH video', 'vcodec': 'vp9'},
        '244': {'ext': 'webm', 'height': 480, 'format_note': 'DASH video', 'vcodec': 'vp9'},
        '245': {'ext': 'webm', 'height': 480, 'format_note': 'DASH video', 'vcodec': 'vp9'},
        '246': {'ext': 'webm', 'height': 480, 'format_note': 'DASH video', 'vcodec': 'vp9'},
        '247': {'ext': 'webm', 'height': 720, 'format_note': 'DASH video', 'vcodec': 'vp9'},
        '248': {'ext': 'webm', 'height': 1080, 'format_note': 'DASH video', 'vcodec': 'vp9'},
        '271': {'ext': 'webm', 'height': 1440, 'format_note': 'DASH video', 'vcodec': 'vp9'},
        # itag 272 videos are either 3840x2160 (e.g. RtoitU2A-3E) or 7680x4320 (sLprVF6d7Ug)
        '272': {'ext': 'webm', 'height': 2160, 'format_note': 'DASH video', 'vcodec': 'vp9'},
        '302': {'ext': 'webm', 'height': 720, 'format_note': 'DASH video', 'vcodec': 'vp9', 'fps': 60},
        '303': {'ext': 'webm', 'height': 1080, 'format_note': 'DASH video', 'vcodec': 'vp9', 'fps': 60},
        '308': {'ext': 'webm', 'height': 1440, 'format_note': 'DASH video', 'vcodec': 'vp9', 'fps': 60},
        '313': {'ext': 'webm', 'height': 2160, 'format_note': 'DASH video', 'vcodec': 'vp9'},
        '315': {'ext': 'webm', 'height': 2160, 'format_note': 'DASH video', 'vcodec': 'vp9', 'fps': 60},

        # Dash webm audio
        '171': {'ext': 'webm', 'acodec': 'vorbis', 'format_note': 'DASH audio', 'abr': 128},
        '172': {'ext': 'webm', 'acodec': 'vorbis', 'format_note': 'DASH audio', 'abr': 256},

        # Dash webm audio with opus inside
        '249': {'ext': 'webm', 'format_note': 'DASH audio', 'acodec': 'opus', 'abr': 50},
        '250': {'ext': 'webm', 'format_note': 'DASH audio', 'acodec': 'opus', 'abr': 70},
        '251': {'ext': 'webm', 'format_note': 'DASH audio', 'acodec': 'opus', 'abr': 160},

        # RTMP (unnamed)
        '_rtmp': {'protocol': 'rtmp'},
    }
    _SUBTITLE_FORMATS = ('ttml', 'vtt')

    _GEO_BYPASS = False

    IE_NAME = 'youtube'
    _TESTS = [
        {
            'url': 'https://www.youtube.com/watch?v=BaW_jenozKc&t=1s&end=9',
            'info_dict': {
                'id': 'BaW_jenozKc',
                'ext': 'mp4',
                'title': 'youtube-dl test video "\'/\\ä↭𝕐',
                'uploader': 'Philipp Hagemeister',
                'uploader_id': 'phihag',
                'uploader_url': r're:https?://(?:www\.)?youtube\.com/user/phihag',
                'upload_date': '20121002',
                'license': 'Standard YouTube License',
                'description': 'test chars:  "\'/\\ä↭𝕐\ntest URL: https://github.com/rg3/youtube-dl/issues/1892\n\nThis is a test video for youtube-dl.\n\nFor more information, contact phihag@phihag.de .',
                'categories': ['Science & Technology'],
                'tags': ['youtube-dl'],
                'duration': 10,
                'like_count': int,
                'dislike_count': int,
                'start_time': 1,
                'end_time': 9,
            }
        },
        {
            'url': 'https://www.youtube.com/watch?v=UxxajLWwzqY',
            'note': 'Test generic use_cipher_signature video (#897)',
            'info_dict': {
                'id': 'UxxajLWwzqY',
                'ext': 'mp4',
                'upload_date': '20120506',
                'title': 'Icona Pop - I Love It (feat. Charli XCX) [OFFICIAL VIDEO]',
                'alt_title': 'I Love It (feat. Charli XCX)',
                'description': 'md5:f3ceb5ef83a08d95b9d146f973157cc8',
                'tags': ['Icona Pop i love it', 'sweden', 'pop music', 'big beat records', 'big beat', 'charli',
                         'xcx', 'charli xcx', 'girls', 'hbo', 'i love it', "i don't care", 'icona', 'pop',
                         'iconic ep', 'iconic', 'love', 'it'],
                'duration': 180,
                'uploader': 'Icona Pop',
                'uploader_id': 'IconaPop',
                'uploader_url': r're:https?://(?:www\.)?youtube\.com/user/IconaPop',
                'license': 'Standard YouTube License',
                'creator': 'Icona Pop',
            }
        },
        {
            'url': 'https://www.youtube.com/watch?v=07FYdnEawAQ',
            'note': 'Test VEVO video with age protection (#956)',
            'info_dict': {
                'id': '07FYdnEawAQ',
                'ext': 'mp4',
                'upload_date': '20130703',
                'title': 'Justin Timberlake - Tunnel Vision (Explicit)',
                'alt_title': 'Tunnel Vision',
                'description': 'md5:64249768eec3bc4276236606ea996373',
                'duration': 419,
                'uploader': 'justintimberlakeVEVO',
                'uploader_id': 'justintimberlakeVEVO',
                'uploader_url': r're:https?://(?:www\.)?youtube\.com/user/justintimberlakeVEVO',
                'license': 'Standard YouTube License',
                'creator': 'Justin Timberlake',
                'age_limit': 18,
            }
        },
        {
            'url': '//www.YouTube.com/watch?v=yZIXLfi8CZQ',
            'note': 'Embed-only video (#1746)',
            'info_dict': {
                'id': 'yZIXLfi8CZQ',
                'ext': 'mp4',
                'upload_date': '20120608',
                'title': 'Principal Sexually Assaults A Teacher - Episode 117 - 8th June 2012',
                'description': 'md5:09b78bd971f1e3e289601dfba15ca4f7',
                'uploader': 'SET India',
                'uploader_id': 'setindia',
                'uploader_url': r're:https?://(?:www\.)?youtube\.com/user/setindia',
                'license': 'Standard YouTube License',
                'age_limit': 18,
            }
        },
        {
            'url': 'https://www.youtube.com/watch?v=BaW_jenozKc&v=UxxajLWwzqY',
            'note': 'Use the first video ID in the URL',
            'info_dict': {
                'id': 'BaW_jenozKc',
                'ext': 'mp4',
                'title': 'youtube-dl test video "\'/\\ä↭𝕐',
                'uploader': 'Philipp Hagemeister',
                'uploader_id': 'phihag',
                'uploader_url': r're:https?://(?:www\.)?youtube\.com/user/phihag',
                'upload_date': '20121002',
                'license': 'Standard YouTube License',
                'description': 'test chars:  "\'/\\ä↭𝕐\ntest URL: https://github.com/rg3/youtube-dl/issues/1892\n\nThis is a test video for youtube-dl.\n\nFor more information, contact phihag@phihag.de .',
                'categories': ['Science & Technology'],
                'tags': ['youtube-dl'],
                'duration': 10,
                'like_count': int,
                'dislike_count': int,
            },
            'params': {
                'skip_download': True,
            },
        },
        {
            'url': 'https://www.youtube.com/watch?v=a9LDPn-MO4I',
            'note': '256k DASH audio (format 141) via DASH manifest',
            'info_dict': {
                'id': 'a9LDPn-MO4I',
                'ext': 'm4a',
                'upload_date': '20121002',
                'uploader_id': '8KVIDEO',
                'uploader_url': r're:https?://(?:www\.)?youtube\.com/user/8KVIDEO',
                'description': '',
                'uploader': '8KVIDEO',
                'license': 'Standard YouTube License',
                'title': 'UHDTV TEST 8K VIDEO.mp4'
            },
            'params': {
                'youtube_include_dash_manifest': True,
                'format': '141',
            },
            'skip': 'format 141 not served anymore',
        },
        # DASH manifest with encrypted signature
        {
            'url': 'https://www.youtube.com/watch?v=IB3lcPjvWLA',
            'info_dict': {
                'id': 'IB3lcPjvWLA',
                'ext': 'm4a',
                'title': 'Afrojack, Spree Wilson - The Spark ft. Spree Wilson',
                'description': 'md5:12e7067fa6735a77bdcbb58cb1187d2d',
                'duration': 244,
                'uploader': 'AfrojackVEVO',
                'uploader_id': 'AfrojackVEVO',
                'upload_date': '20131011',
                'license': 'Standard YouTube License',
            },
            'params': {
                'youtube_include_dash_manifest': True,
                'format': '141/bestaudio[ext=m4a]',
            },
        },
        # JS player signature function name containing $
        {
            'url': 'https://www.youtube.com/watch?v=nfWlot6h_JM',
            'info_dict': {
                'id': 'nfWlot6h_JM',
                'ext': 'm4a',
                'title': 'Taylor Swift - Shake It Off',
                'alt_title': 'Shake It Off',
                'description': 'md5:95f66187cd7c8b2c13eb78e1223b63c3',
                'duration': 242,
                'uploader': 'TaylorSwiftVEVO',
                'uploader_id': 'TaylorSwiftVEVO',
                'upload_date': '20140818',
                'license': 'Standard YouTube License',
                'creator': 'Taylor Swift',
            },
            'params': {
                'youtube_include_dash_manifest': True,
                'format': '141/bestaudio[ext=m4a]',
            },
        },
        # Controversy video
        {
            'url': 'https://www.youtube.com/watch?v=T4XJQO3qol8',
            'info_dict': {
                'id': 'T4XJQO3qol8',
                'ext': 'mp4',
                'duration': 219,
                'upload_date': '20100909',
                'uploader': 'The Amazing Atheist',
                'uploader_id': 'TheAmazingAtheist',
                'uploader_url': r're:https?://(?:www\.)?youtube\.com/user/TheAmazingAtheist',
                'license': 'Standard YouTube License',
                'title': 'Burning Everyone\'s Koran',
                'description': 'SUBSCRIBE: http://www.youtube.com/saturninefilms\n\nEven Obama has taken a stand against freedom on this issue: http://www.huffingtonpost.com/2010/09/09/obama-gma-interview-quran_n_710282.html',
            }
        },
        # Normal age-gate video (No vevo, embed allowed)
        {
            'url': 'https://youtube.com/watch?v=HtVdAasjOgU',
            'info_dict': {
                'id': 'HtVdAasjOgU',
                'ext': 'mp4',
                'title': 'The Witcher 3: Wild Hunt - The Sword Of Destiny Trailer',
                'description': r're:(?s).{100,}About the Game\n.*?The Witcher 3: Wild Hunt.{100,}',
                'duration': 142,
                'uploader': 'The Witcher',
                'uploader_id': 'WitcherGame',
                'uploader_url': r're:https?://(?:www\.)?youtube\.com/user/WitcherGame',
                'upload_date': '20140605',
                'license': 'Standard YouTube License',
                'age_limit': 18,
            },
        },
        # Age-gate video with encrypted signature
        {
            'url': 'https://www.youtube.com/watch?v=6kLq3WMV1nU',
            'info_dict': {
                'id': '6kLq3WMV1nU',
                'ext': 'mp4',
                'title': 'Dedication To My Ex (Miss That) (Lyric Video)',
                'description': 'md5:33765bb339e1b47e7e72b5490139bb41',
                'duration': 247,
                'uploader': 'LloydVEVO',
                'uploader_id': 'LloydVEVO',
                'uploader_url': r're:https?://(?:www\.)?youtube\.com/user/LloydVEVO',
                'upload_date': '20110629',
                'license': 'Standard YouTube License',
                'age_limit': 18,
            },
        },
        # video_info is None (https://github.com/rg3/youtube-dl/issues/4421)
        {
            'url': '__2ABJjxzNo',
            'info_dict': {
                'id': '__2ABJjxzNo',
                'ext': 'mp4',
                'duration': 266,
                'upload_date': '20100430',
                'uploader_id': 'deadmau5',
                'uploader_url': r're:https?://(?:www\.)?youtube\.com/user/deadmau5',
                'creator': 'deadmau5',
                'description': 'md5:12c56784b8032162bb936a5f76d55360',
                'uploader': 'deadmau5',
                'license': 'Standard YouTube License',
                'title': 'Deadmau5 - Some Chords (HD)',
                'alt_title': 'Some Chords',
            },
            'expected_warnings': [
                'DASH manifest missing',
            ]
        },
        # Olympics (https://github.com/rg3/youtube-dl/issues/4431)
        {
            'url': 'lqQg6PlCWgI',
            'info_dict': {
                'id': 'lqQg6PlCWgI',
                'ext': 'mp4',
                'duration': 6085,
                'upload_date': '20150827',
                'uploader_id': 'olympic',
                'uploader_url': r're:https?://(?:www\.)?youtube\.com/user/olympic',
                'license': 'Standard YouTube License',
                'description': 'HO09  - Women -  GER-AUS - Hockey - 31 July 2012 - London 2012 Olympic Games',
                'uploader': 'Olympic',
                'title': 'Hockey - Women -  GER-AUS - London 2012 Olympic Games',
            },
            'params': {
                'skip_download': 'requires avconv',
            }
        },
        # Non-square pixels
        {
            'url': 'https://www.youtube.com/watch?v=_b-2C3KPAM0',
            'info_dict': {
                'id': '_b-2C3KPAM0',
                'ext': 'mp4',
                'stretched_ratio': 16 / 9.,
                'duration': 85,
                'upload_date': '20110310',
                'uploader_id': 'AllenMeow',
                'uploader_url': r're:https?://(?:www\.)?youtube\.com/user/AllenMeow',
                'description': 'made by Wacom from Korea | 字幕&加油添醋 by TY\'s Allen | 感謝heylisa00cavey1001同學熱情提供梗及翻譯',
                'uploader': '孫艾倫',
                'license': 'Standard YouTube License',
                'title': '[A-made] 變態妍字幕版 太妍 我就是這樣的人',
            },
        },
        # url_encoded_fmt_stream_map is empty string
        {
            'url': 'qEJwOuvDf7I',
            'info_dict': {
                'id': 'qEJwOuvDf7I',
                'ext': 'webm',
                'title': 'Обсуждение судебной практики по выборам 14 сентября 2014 года в Санкт-Петербурге',
                'description': '',
                'upload_date': '20150404',
                'uploader_id': 'spbelect',
                'uploader': 'Наблюдатели Петербурга',
            },
            'params': {
                'skip_download': 'requires avconv',
            },
            'skip': 'This live event has ended.',
        },
        # Extraction from multiple DASH manifests (https://github.com/rg3/youtube-dl/pull/6097)
        {
            'url': 'https://www.youtube.com/watch?v=FIl7x6_3R5Y',
            'info_dict': {
                'id': 'FIl7x6_3R5Y',
                'ext': 'mp4',
                'title': 'md5:7b81415841e02ecd4313668cde88737a',
                'description': 'md5:116377fd2963b81ec4ce64b542173306',
                'duration': 220,
                'upload_date': '20150625',
                'uploader_id': 'dorappi2000',
                'uploader_url': r're:https?://(?:www\.)?youtube\.com/user/dorappi2000',
                'uploader': 'dorappi2000',
                'license': 'Standard YouTube License',
                'formats': 'mincount:32',
            },
        },
        # DASH manifest with segment_list
        {
            'url': 'https://www.youtube.com/embed/CsmdDsKjzN8',
            'md5': '8ce563a1d667b599d21064e982ab9e31',
            'info_dict': {
                'id': 'CsmdDsKjzN8',
                'ext': 'mp4',
                'upload_date': '20150501',
            # According to '<meta itemprop="datePublished"', but in other places it's 20150510
                'uploader': 'Airtek',
                'description': 'Retransmisión en directo de la XVIII media maratón de Zaragoza.',
                'uploader_id': 'UCzTzUmjXxxacNnL8I3m4LnQ',
                'license': 'Standard YouTube License',
                'title': 'Retransmisión XVIII Media maratón Zaragoza 2015',
            },
            'params': {
                'youtube_include_dash_manifest': True,
                'format': '135',  # bestvideo
            },
            'skip': 'This live event has ended.',
        },
        {
            # Multifeed videos (multiple cameras), URL is for Main Camera
            'url': 'https://www.youtube.com/watch?v=jqWvoWXjCVs',
            'info_dict': {
                'id': 'jqWvoWXjCVs',
                'title': 'teamPGP: Rocket League Noob Stream',
                'description': 'md5:dc7872fb300e143831327f1bae3af010',
            },
            'playlist': [{
                'info_dict': {
                    'id': 'jqWvoWXjCVs',
                    'ext': 'mp4',
                    'title': 'teamPGP: Rocket League Noob Stream (Main Camera)',
                    'description': 'md5:dc7872fb300e143831327f1bae3af010',
                    'duration': 7335,
                    'upload_date': '20150721',
                    'uploader': 'Beer Games Beer',
                    'uploader_id': 'beergamesbeer',
                    'uploader_url': r're:https?://(?:www\.)?youtube\.com/user/beergamesbeer',
                    'license': 'Standard YouTube License',
                },
            }, {
                'info_dict': {
                    'id': '6h8e8xoXJzg',
                    'ext': 'mp4',
                    'title': 'teamPGP: Rocket League Noob Stream (kreestuh)',
                    'description': 'md5:dc7872fb300e143831327f1bae3af010',
                    'duration': 7337,
                    'upload_date': '20150721',
                    'uploader': 'Beer Games Beer',
                    'uploader_id': 'beergamesbeer',
                    'uploader_url': r're:https?://(?:www\.)?youtube\.com/user/beergamesbeer',
                    'license': 'Standard YouTube License',
                },
            }, {
                'info_dict': {
                    'id': 'PUOgX5z9xZw',
                    'ext': 'mp4',
                    'title': 'teamPGP: Rocket League Noob Stream (grizzle)',
                    'description': 'md5:dc7872fb300e143831327f1bae3af010',
                    'duration': 7337,
                    'upload_date': '20150721',
                    'uploader': 'Beer Games Beer',
                    'uploader_id': 'beergamesbeer',
                    'uploader_url': r're:https?://(?:www\.)?youtube\.com/user/beergamesbeer',
                    'license': 'Standard YouTube License',
                },
            }, {
                'info_dict': {
                    'id': 'teuwxikvS5k',
                    'ext': 'mp4',
                    'title': 'teamPGP: Rocket League Noob Stream (zim)',
                    'description': 'md5:dc7872fb300e143831327f1bae3af010',
                    'duration': 7334,
                    'upload_date': '20150721',
                    'uploader': 'Beer Games Beer',
                    'uploader_id': 'beergamesbeer',
                    'uploader_url': r're:https?://(?:www\.)?youtube\.com/user/beergamesbeer',
                    'license': 'Standard YouTube License',
                },
            }],
            'params': {
                'skip_download': True,
            },
        },
        {
            # Multifeed video with comma in title (see https://github.com/rg3/youtube-dl/issues/8536)
            'url': 'https://www.youtube.com/watch?v=gVfLd0zydlo',
            'info_dict': {
                'id': 'gVfLd0zydlo',
                'title': 'DevConf.cz 2016 Day 2 Workshops 1 14:00 - 15:30',
            },
            'playlist_count': 2,
            'skip': 'Not multifeed anymore',
        },
        {
            'url': 'https://vid.plus/FlRa-iH7PGw',
            'only_matching': True,
        },
        {
            'url': 'https://zwearz.com/watch/9lWxNJF-ufM/electra-woman-dyna-girl-official-trailer-grace-helbig.html',
            'only_matching': True,
        },
        {
            # Title with JS-like syntax "};" (see https://github.com/rg3/youtube-dl/issues/7468)
            # Also tests cut-off URL expansion in video description (see
            # https://github.com/rg3/youtube-dl/issues/1892,
            # https://github.com/rg3/youtube-dl/issues/8164)
            'url': 'https://www.youtube.com/watch?v=lsguqyKfVQg',
            'info_dict': {
                'id': 'lsguqyKfVQg',
                'ext': 'mp4',
                'title': '{dark walk}; Loki/AC/Dishonored; collab w/Elflover21',
                'alt_title': 'Dark Walk',
                'description': 'md5:8085699c11dc3f597ce0410b0dcbb34a',
                'duration': 133,
                'upload_date': '20151119',
                'uploader_id': 'IronSoulElf',
                'uploader_url': r're:https?://(?:www\.)?youtube\.com/user/IronSoulElf',
                'uploader': 'IronSoulElf',
                'license': 'Standard YouTube License',
                'creator': 'Todd Haberman, Daniel Law Heath & Aaron Kaplan',
            },
            'params': {
                'skip_download': True,
            },
        },
        {
            # Tags with '};' (see https://github.com/rg3/youtube-dl/issues/7468)
            'url': 'https://www.youtube.com/watch?v=Ms7iBXnlUO8',
            'only_matching': True,
        },
        {
            # Video with yt:stretch=17:0
            'url': 'https://www.youtube.com/watch?v=Q39EVAstoRM',
            'info_dict': {
                'id': 'Q39EVAstoRM',
                'ext': 'mp4',
                'title': 'Clash Of Clans#14 Dicas De Ataque Para CV 4',
                'description': 'md5:ee18a25c350637c8faff806845bddee9',
                'upload_date': '20151107',
                'uploader_id': 'UCCr7TALkRbo3EtFzETQF1LA',
                'uploader': 'CH GAMER DROID',
            },
            'params': {
                'skip_download': True,
            },
            'skip': 'This video does not exist.',
        },
        {
            # Video licensed under Creative Commons
            'url': 'https://www.youtube.com/watch?v=M4gD1WSo5mA',
            'info_dict': {
                'id': 'M4gD1WSo5mA',
                'ext': 'mp4',
                'title': 'md5:e41008789470fc2533a3252216f1c1d1',
                'description': 'md5:a677553cf0840649b731a3024aeff4cc',
                'duration': 721,
                'upload_date': '20150127',
                'uploader_id': 'BerkmanCenter',
                'uploader_url': r're:https?://(?:www\.)?youtube\.com/user/BerkmanCenter',
                'uploader': 'The Berkman Klein Center for Internet & Society',
                'license': 'Creative Commons Attribution license (reuse allowed)',
            },
            'params': {
                'skip_download': True,
            },
        },
        {
            # Channel-like uploader_url
            'url': 'https://www.youtube.com/watch?v=eQcmzGIKrzg',
            'info_dict': {
                'id': 'eQcmzGIKrzg',
                'ext': 'mp4',
                'title': 'Democratic Socialism and Foreign Policy | Bernie Sanders',
                'description': 'md5:dda0d780d5a6e120758d1711d062a867',
                'duration': 4060,
                'upload_date': '20151119',
                'uploader': 'Bernie 2016',
                'uploader_id': 'UCH1dpzjCEiGAt8CXkryhkZg',
                'uploader_url': r're:https?://(?:www\.)?youtube\.com/channel/UCH1dpzjCEiGAt8CXkryhkZg',
                'license': 'Creative Commons Attribution license (reuse allowed)',
            },
            'params': {
                'skip_download': True,
            },
        },
        {
            'url': 'https://www.youtube.com/watch?feature=player_embedded&amp;amp;v=V36LpHqtcDY',
            'only_matching': True,
        },
        {
            # YouTube Red paid video (https://github.com/rg3/youtube-dl/issues/10059)
            'url': 'https://www.youtube.com/watch?v=i1Ko8UG-Tdo',
            'only_matching': True,
        },
        {
            # Rental video preview
            'url': 'https://www.youtube.com/watch?v=yYr8q0y5Jfg',
            'info_dict': {
                'id': 'uGpuVWrhIzE',
                'ext': 'mp4',
                'title': 'Piku - Trailer',
                'description': 'md5:c36bd60c3fd6f1954086c083c72092eb',
                'upload_date': '20150811',
                'uploader': 'FlixMatrix',
                'uploader_id': 'FlixMatrixKaravan',
                'uploader_url': r're:https?://(?:www\.)?youtube\.com/user/FlixMatrixKaravan',
                'license': 'Standard YouTube License',
            },
            'params': {
                'skip_download': True,
            },
        },
        {
            # YouTube Red video with episode data
            'url': 'https://www.youtube.com/watch?v=iqKdEhx-dD4',
            'info_dict': {
                'id': 'iqKdEhx-dD4',
                'ext': 'mp4',
                'title': 'Isolation - Mind Field (Ep 1)',
                'description': 'md5:8013b7ddea787342608f63a13ddc9492',
                'duration': 2085,
                'upload_date': '20170118',
                'uploader': 'Vsauce',
                'uploader_id': 'Vsauce',
                'uploader_url': r're:https?://(?:www\.)?youtube\.com/user/Vsauce',
                'license': 'Standard YouTube License',
                'series': 'Mind Field',
                'season_number': 1,
                'episode_number': 1,
            },
            'params': {
                'skip_download': True,
            },
            'expected_warnings': [
                'Skipping DASH manifest',
            ],
        },
        {
            # itag 212
            'url': '1t24XAntNCY',
            'only_matching': True,
        },
        {
            # geo restricted to JP
            'url': 'sJL6WA-aGkQ',
            'only_matching': True,
        },
        {
            'url': 'https://www.youtube.com/watch?v=MuAGGZNfUkU&list=RDMM',
            'only_matching': True,
        },
    ]


    def __init__(self):
        pass


    def report_rtmp_download(self):
        """Indicate the download will use the RTMP protocol."""
        print('RTMP download detected')

    def report_information_extraction(self, video_id):
        """Report attempt to extract video information."""
        print('%s: Extracting video information' % video_id)

    @classmethod
    def extract_id(cls, url):
        mobj = re.match(cls._VALID_URL, url, re.VERBOSE)
        if mobj is None:
            raise ExtractorError('Invalid URL: %s' % url)
        video_id = mobj.group(2)
        return video_id

    def downloadpage(self,url):
        # tt = urllib2.urlopen(url)
        # Configuration
        ua = UserAgent()
        header = {'User-Agent':str(ua.ie)}
        webcontent = requests.get(url,header,verify=True)
        webcontent.raise_for_status()
        return webcontent.text ;
    def _html_search_meta(self, name, html, display_name=None, fatal=False, **kwargs):
        if not isinstance(name, (list, tuple)):
            name = [name]
        if display_name is None:
            display_name = name[0]
        return self._html_search_regex(
            [self._meta_regex(n) for n in name],
            html, display_name, fatal=fatal, group='content', **kwargs)


    def _sort_formats(self, formats, field_preference=None):
        if not formats:
            raise ExtractorError('No video formats found')

        for f in formats:
            # Automatically determine tbr when missing based on abr and vbr (improves
            # formats sorting in some cases)
            if 'tbr' not in f and f.get('abr') is not None and f.get('vbr') is not None:
                f['tbr'] = f['abr'] + f['vbr']

        def _formats_key(f):
            # TODO remove the following workaround
            # from ..utils import determine_ext
            if not f.get('ext') and 'url' in f:
                f['ext'] = determine_ext(f['url'])

            if isinstance(field_preference, (list, tuple)):
                return tuple(
                    f.get(field)
                    if f.get(field) is not None
                    else ('' if field == 'format_id' else -1)
                    for field in field_preference)

            preference = f.get('preference')
            if preference is None:
                preference = 0
                if f.get('ext') in ['f4f', 'f4m']:  # Not yet supported
                    preference -= 0.5

            protocol = f.get('protocol') or determine_protocol(f)
            proto_preference = 0 if protocol in ['http', 'https'] else (-0.5 if protocol == 'rtsp' else -0.1)

            if f.get('vcodec') == 'none':  # audio only
                preference -= 50
                # if self._downloader.params.get('prefer_free_formats'):
                ORDER = ['aac', 'mp3', 'm4a', 'webm', 'ogg', 'opus']
                # else:
                #     ORDER = ['webm', 'opus', 'ogg', 'mp3', 'aac', 'm4a']
                ext_preference = 0
                try:
                    audio_ext_preference = ORDER.index(f['ext'])
                except ValueError:
                    audio_ext_preference = -1
            else:
                if f.get('acodec') == 'none':  # video only
                    preference -= 40
                # if self._downloader.params.get('prefer_free_formats'):
                ORDER = ['flv', 'mp4', 'webm']
                # else:
                #     ORDER = ['webm', 'flv', 'mp4']
                try:
                    ext_preference = ORDER.index(f['ext'])
                except ValueError:
                    ext_preference = -1
                audio_ext_preference = 0

            return (
                preference,
                f.get('language_preference') if f.get('language_preference') is not None else -1,
                f.get('quality') if f.get('quality') is not None else -1,
                f.get('tbr') if f.get('tbr') is not None else -1,
                f.get('filesize') if f.get('filesize') is not None else -1,
                f.get('vbr') if f.get('vbr') is not None else -1,
                f.get('height') if f.get('height') is not None else -1,
                f.get('width') if f.get('width') is not None else -1,
                proto_preference,
                ext_preference,
                f.get('abr') if f.get('abr') is not None else -1,
                audio_ext_preference,
                f.get('fps') if f.get('fps') is not None else -1,
                f.get('filesize_approx') if f.get('filesize_approx') is not None else -1,
                f.get('source_preference') if f.get('source_preference') is not None else -1,
                f.get('format_id') if f.get('format_id') is not None else '',
            )
        formats.sort(key=_formats_key)


    def _search_regex(self, pattern, string, name,default=NO_DEFAULT, fatal=True, flags=0, group=None):
        """
        Perform a regex search on the given string, using a single or a list of
        patterns returning the first matching group.
        In case of failure return a default value or raise a WARNING or a
        RegexNotFoundError, depending on fatal, specifying the field name.
        """
        if isinstance(pattern, (str, compat_str, compiled_regex_type)):
            mobj = re.search(pattern, string, 0)
        else:
            for p in pattern:
                mobj = re.search(p, string, 0)
                if mobj:
                    break
        if mobj:
            if group is None:
                # return the first matching group
                return next(g for g in mobj.groups() if g is not None)
            else:
                return mobj.group(group)
        elif default is not NO_DEFAULT:
            return default
        return None

    def report_video_info_webpage_download(self,video_id):
        print('%s: Downloading video info webpage' % video_id)

    def get_ytplayer_config(self,video_id, webpage):
        patterns = (
            # User data may contain arbitrary character sequences that may affect
            # JSON extraction with regex, e.g. when '};' is contained the second
            # regex won't capture the whole JSON. Yet working around by trying more
            # concrete regex first keeping in mind proper quoted string handling
            # to be implemented in future that will replace this workaround (see
            # https://github.com/rg3/youtube-dl/issues/7468,
            # https://github.com/rg3/youtube-dl/pull/7599)
            r';ytplayer\.config\s*=\s*({.+?});ytplayer',
            r';ytplayer\.config\s*=\s*({.+?});',
        )
        config = self._search_regex(
            patterns, webpage, 'ytplayer.config', default=None)
        if config:
            pass;
            return self._parse_json(
                uppercase_escape(config), video_id, fatal=False)
    def real_extractor(self,url):
        url, smuggled_data = unsmuggle_url(url, {})

        proto = 'http'

        start_time = None
        end_time = None
        parsed_url = compat_urllib_parse_urlparse(url)
        for component in [parsed_url.fragment, parsed_url.query]:
            query = compat_parse_qs(component)
            if start_time is None and 't' in query:
                start_time = parse_duration(query['t'][0])
            if start_time is None and 'start' in query:
                start_time = parse_duration(query['start'][0])
            if end_time is None and 'end' in query:
                end_time = parse_duration(query['end'][0])

        # Extract original video URL from URL with redirection, like age verification, using next_url parameter
        mobj = re.search(self._NEXT_URL_RE, url)
        if mobj:
            url = proto + '://www.youtube.com/' + compat_urllib_parse_unquote(mobj.group(1)).lstrip('/')
        video_id = self.extract_id(url)

        # Get video webpage
        url = proto + '://www.youtube.com/watch?v=%s&gl=US&hl=en&has_verified=1&bpctr=9999999999' % video_id
        video_webpage = self.downloadpage(url)

        # Attempt to extract SWF player URL
        mobj = re.search(r'swfConfig.*?"(https?:\\/\\/.*?watch.*?-.*?\.swf)"', video_webpage)
        if mobj is not None:
            player_url = re.sub(r'\\(.)', r'\1', mobj.group(1))
        else:
            player_url = None

        dash_mpds = []

        def add_dash_mpd(video_info):
            pass
            # dash_mpd = video_info.get('dashmpd')
            # if dash_mpd and dash_mpd[0] not in dash_mpds:
            #     dash_mpds.append(dash_mpd[0])

        # Get video info
        embed_webpage = None
        is_live = None
        if re.search(r'player-age-gate-content">', video_webpage) is not None:
            age_gate = True
            # We simulate the access to the video from www.youtube.com/v/{video_id}
            # this can be viewed without login into Youtube
            url = proto + '://www.youtube.com/embed/%s' % video_id
            embed_webpage =  self.downloadpage(url) #self._download_webpage(url, video_id, 'Downloading embed webpage')
            data = compat_urllib_parse_urlencode({
                'video_id': video_id,
                'eurl': 'https://youtube.googleapis.com/v/' + video_id,
                'sts': self._search_regex(
                    r'"sts"\s*:\s*(\d+)', embed_webpage, 'sts', default=''),
            })
            video_info_url = proto + '://www.youtube.com/get_video_info?' + data
            video_info_webpage = self.downloadpage(video_info_url)#self._download_webpage(
                # video_info_url, video_id,
                # note='Refetching age-gated info webpage',
                # errnote='unable to download video info webpage')
            video_info = compat_parse_qs(video_info_webpage)
            add_dash_mpd(video_info)
        else:
            age_gate = False
            video_info = None
            # Try looking directly into the video webpage
            ytplayer_config = self.get_ytplayer_config(video_id, video_webpage)
            if ytplayer_config:
                args = ytplayer_config['args']
                if args.get('url_encoded_fmt_stream_map'):
                    # Convert to the same format returned by compat_parse_qs
                    video_info = dict((k, [v]) for k, v in args.items())
                    add_dash_mpd(video_info)
                # Rental video is not rented but preview is available (e.g.
                # https://www.youtube.com/watch?v=yYr8q0y5Jfg,
                # https://github.com/rg3/youtube-dl/issues/10532)
                if not video_info and args.get('ypc_vid'):
                    return self.url_result(
                        args['ypc_vid'], YoutubeIE.ie_key(), video_id=args['ypc_vid'])
                if args.get('livestream') == '1' or args.get('live_playback') == 1:
                    is_live = True
            if not video_info :
                # We also try looking in get_video_info since it may contain different dashmpd
                # URL that points to a DASH manifest with possibly different itag set (some itags
                # are missing from DASH manifest pointed by webpage's dashmpd, some - from DASH
                # manifest pointed by get_video_info's dashmpd).
                # The general idea is to take a union of itags of both DASH manifests (for example
                # video with such 'manifest behavior' see https://github.com/rg3/youtube-dl/issues/6093)
                self.report_video_info_webpage_download(video_id)
                for el_type in ['&el=info', '&el=embedded', '&el=detailpage', '&el=vevo', '']:
                    video_info_url = (
                        '%s://www.youtube.com/get_video_info?&video_id=%s%s&ps=default&eurl=&gl=US&hl=en'
                        % (proto, video_id, el_type))
                    video_info_webpage = self.downloadpage(video_info_url) #self._download_webpage(
                    #     video_info_url,
                    #     video_id, note=False,
                    #     errnote='unable to download video info webpage')
                    get_video_info = compat_parse_qs(video_info_webpage)
                    if get_video_info.get('use_cipher_signature') != ['True']:
                        add_dash_mpd(get_video_info)
                    if not video_info:
                        video_info = get_video_info
                    if 'token' in get_video_info:
                        # Different get_video_info requests may report different results, e.g.
                        # some may report video unavailability, but some may serve it without
                        # any complaint (see https://github.com/rg3/youtube-dl/issues/7362,
                        # the original webpage as well as el=info and el=embedded get_video_info
                        # requests report video unavailability due to geo restriction while
                        # el=detailpage succeeds and returns valid data). This is probably
                        # due to YouTube measures against IP ranges of hosting providers.
                        # Working around by preferring the first succeeded video_info containing
                        # the token if no such video_info yet was found.
                        if 'token' not in video_info:
                            video_info = get_video_info
                        break
        if 'token' not in video_info:
            if 'reason' in video_info:
                if 'The uploader has not made this video available in your country.' in video_info['reason']:
                    regions_allowed = self._html_search_meta(
                        'regionsAllowed', video_webpage, default=None)
                    countries = regions_allowed.split(',') if regions_allowed else None
                    self.raise_geo_restricted(
                        msg=video_info['reason'][0], countries=countries)
                raise ExtractorError(
                    'YouTube said: %s' % video_info['reason'][0],
                    expected=True, video_id=video_id)
            else:
                raise ExtractorError(
                    '"token" parameter not in video info for unknown reason',
                    video_id=video_id)

        # title
        if 'title' in video_info:
            video_title = video_info['title'][0]
        else:
            print('Unable to extract video title')
            video_title = '_'

        # description
        video_description = get_element_by_id("eow-description", video_webpage)
        if video_description:
            video_description = re.sub(r'''(?x)
                        <a\s+
                            (?:[a-zA-Z-]+="[^"]*"\s+)*?
                            (?:title|href)="([^"]+)"\s+
                            (?:[a-zA-Z-]+="[^"]*"\s+)*?
                            class="[^"]*"[^>]*>
                        [^<]+\.{3}\s*
                        </a>
                    ''', r'\1', video_description)
            video_description = clean_html(video_description)
        else:
            fd_mobj = re.search(r'<meta name="description" content="([^"]+)"', video_webpage)
            if fd_mobj:
                video_description = unescapeHTML(fd_mobj.group(1))
            else:
                video_description = ''

        if 'multifeed_metadata_list' in video_info and not smuggled_data.get('force_singlefeed', False):
            #no playlist
            # if not self._downloader.params.get('noplaylist'):
            #     entries = []
            #     feed_ids = []
            #     multifeed_metadata_list = video_info['multifeed_metadata_list'][0]
            #     for feed in multifeed_metadata_list.split(','):
            #         # Unquote should take place before split on comma (,) since textual
            #         # fields may contain comma as well (see
            #         # https://github.com/rg3/youtube-dl/issues/8536)
            #         feed_data = compat_parse_qs(compat_urllib_parse_unquote_plus(feed))
            #         entries.append({
            #             '_type': 'url_transparent',
            #             'ie_key': 'Youtube',
            #             'url': smuggle_url(
            #                 '%s://www.youtube.com/watch?v=%s' % (proto, feed_data['id'][0]),
            #                 {'force_singlefeed': True}),
            #             'title': '%s (%s)' % (video_title, feed_data['title'][0]),
            #         })
            #         feed_ids.append(feed_data['id'][0])
            #     self.to_screen(
            #         'Downloading multifeed video (%s) - add --no-playlist to just download video %s'
            #         % (', '.join(feed_ids), video_id))
            #     return self.playlist_result(entries, video_id, video_title, video_description)
            self.to_screen('Downloading just video %s because of --no-playlist' % video_id)

        if 'view_count' in video_info:
            view_count = int(video_info['view_count'][0])
        else:
            view_count = None

        # Check for "rental" videos
        if 'ypc_video_rental_bar_text' in video_info and 'author' not in video_info:
            raise ExtractorError(
                '"rental" videos not supported. See https://github.com/rg3/youtube-dl/issues/359 for more information.',
                expected=True)

        # Start extracting information
        self.report_information_extraction(video_id)

        # uploader
        if 'author' not in video_info:
            raise ExtractorError('Unable to extract uploader name')
        video_uploader = compat_urllib_parse_unquote_plus(video_info['author'][0])

        # uploader_id
        video_uploader_id = None
        video_uploader_url = None
        mobj = re.search(
            r'<link itemprop="url" href="(?P<uploader_url>https?://www.youtube.com/(?:user|channel)/(?P<uploader_id>[^"]+))">',
            video_webpage)
        if mobj is not None:
            video_uploader_id = mobj.group('uploader_id')
            video_uploader_url = mobj.group('uploader_url')
        else:
            self._downloader.report_warning('unable to extract uploader nickname')

        # thumbnail image
        # We try first to get a high quality image:
        m_thumb = re.search(r'<span itemprop="thumbnail".*?href="(.*?)">',
                            video_webpage, re.DOTALL)
        if m_thumb is not None:
            video_thumbnail = m_thumb.group(1)
        elif 'thumbnail_url' not in video_info:
            self._downloader.report_warning('unable to extract video thumbnail')
            video_thumbnail = None
        else:  # don't panic if we can't find it
            video_thumbnail = compat_urllib_parse_unquote_plus(video_info['thumbnail_url'][0])

        # upload date
        upload_date = self._html_search_meta(
            'datePublished', video_webpage, 'upload date', default=None)
        if not upload_date:
            upload_date = self._search_regex(
                [r'(?s)id="eow-date.*?>(.*?)</span>',
                 r'id="watch-uploader-info".*?>.*?(?:Published|Uploaded|Streamed live|Started) on (.+?)</strong>'],
                video_webpage, 'upload date', default=None)
            if upload_date:
                upload_date = ' '.join(re.sub(r'[/,-]', r' ', mobj.group(1)).split())
        upload_date = unified_strdate(upload_date)

        video_license = self._html_search_regex(
            r'<h4[^>]+class="title"[^>]*>\s*License\s*</h4>\s*<ul[^>]*>\s*<li>(.+?)</li',
            video_webpage, 'license', default=None)

        m_music = re.search(
            r'<h4[^>]+class="title"[^>]*>\s*Music\s*</h4>\s*<ul[^>]*>\s*<li>(?P<title>.+?) by (?P<creator>.+?)(?:\(.+?\))?</li',
            video_webpage)
        if m_music:
            video_alt_title = remove_quotes(unescapeHTML(m_music.group('title')))
            video_creator = clean_html(m_music.group('creator'))
        else:
            video_alt_title = video_creator = None

        m_episode = re.search(
            r'<div[^>]+id="watch7-headline"[^>]*>\s*<span[^>]*>.*?>(?P<series>[^<]+)</a></b>\s*S(?P<season>\d+)\s*•\s*E(?P<episode>\d+)</span>',
            video_webpage)
        if m_episode:
            series = m_episode.group('series')
            season_number = int(m_episode.group('season'))
            episode_number = int(m_episode.group('episode'))
        else:
            series = season_number = episode_number = None

        m_cat_container = self._search_regex(
            r'(?s)<h4[^>]*>\s*Category\s*</h4>\s*<ul[^>]*>(.*?)</ul>',
            video_webpage, 'categories', default=None)
        if m_cat_container:
            category = self._html_search_regex(
                r'(?s)<a[^<]+>(.*?)</a>', m_cat_container, 'category',
                default=None)
            video_categories = None if category is None else [category]
        else:
            video_categories = None

        video_tags = [
            unescapeHTML(m.group('content'))
            for m in re.finditer(self._meta_regex('og:video:tag'), video_webpage)]

        def _extract_count(count_name):
            return str_to_int(self._search_regex(
                r'-%s-button[^>]+><span[^>]+class="yt-uix-button-content"[^>]*>([\d,]+)</span>'
                % re.escape(count_name),
                video_webpage, count_name, default=None))

        like_count = _extract_count('like')
        dislike_count = _extract_count('dislike')

        # subtitles
        # video_subtitles = self.extract_subtitles(video_id, video_webpage)
        # automatic_captions = self.extract_automatic_captions(video_id, video_webpage)

        video_duration = try_get(
            video_info, lambda x: int_or_none(x['length_seconds'][0]))
        if not video_duration:
            video_duration = parse_duration(self._html_search_meta(
                'duration', video_webpage, 'video duration'))

        # annotations
        # video_annotations = None
        # if self._downloader.params.get('writeannotations', False):
        #     video_annotations = self._extract_annotations(video_id)

        if 'conn' in video_info and video_info['conn'][0].startswith('rtmp'):
            self.report_rtmp_download()
            formats = [{
                'format_id': '_rtmp',
                'protocol': 'rtmp',
                'url': video_info['conn'][0],
                'player_url': player_url,
            }]
        elif len(video_info.get('url_encoded_fmt_stream_map', [''])[0]) >= 1 or len(
                video_info.get('adaptive_fmts', [''])[0]) >= 1:
            encoded_url_map = video_info.get('url_encoded_fmt_stream_map', [''])[0] + ',' + \
                              video_info.get('adaptive_fmts', [''])[0]
            if 'rtmpe%3Dyes' in encoded_url_map:
                raise ExtractorError(
                    'rtmpe downloads are not supported, see https://github.com/rg3/youtube-dl/issues/343 for more information.',
                    expected=True)
            formats_spec = {}
            fmt_list = video_info.get('fmt_list', [''])[0]
            if fmt_list:
                for fmt in fmt_list.split(','):
                    spec = fmt.split('/')
                    if len(spec) > 1:
                        width_height = spec[1].split('x')
                        if len(width_height) == 2:
                            formats_spec[spec[0]] = {
                                'resolution': spec[1],
                                'width': int_or_none(width_height[0]),
                                'height': int_or_none(width_height[1]),
                            }
            formats = []
            for url_data_str in encoded_url_map.split(','):
                url_data = compat_parse_qs(url_data_str)
                if 'itag' not in url_data or 'url' not in url_data:
                    continue
                format_id = url_data['itag'][0]
                url = url_data['url'][0]

                if 'sig' in url_data:
                    url += '&signature=' + url_data['sig'][0]
                elif 's' in url_data:
                    encrypted_sig = url_data['s'][0]
                    ASSETS_RE = r'"assets":.+?"js":\s*("[^"]+")'

                    jsplayer_url_json = self._search_regex(
                        ASSETS_RE,
                        embed_webpage if age_gate else video_webpage,
                        'JS player URL (1)', default=None)
                    if not jsplayer_url_json and not age_gate:
                        # We need the embed website after all
                        if embed_webpage is None:
                            embed_url = proto + '://www.youtube.com/embed/%s' % video_id
                            embed_webpage = self.downloadpage(embed_url)#self._download_webpage(
                                # embed_url, video_id, 'Downloading embed webpage')
                        jsplayer_url_json = self._search_regex(
                            ASSETS_RE, embed_webpage, 'JS player URL')

                    player_url = json.loads(jsplayer_url_json)
                    if player_url is None:
                        player_url_json = self._search_regex(
                            r'ytplayer\.config.*?"url"\s*:\s*("[^"]+")',
                            video_webpage, 'age gate player URL')
                        player_url = json.loads(player_url_json)

                    # if self._downloader.params.get('verbose'):
                    #     if player_url is None:
                    #         player_version = 'unknown'
                    #         player_desc = 'unknown'
                    #     else:
                    #         if player_url.endswith('swf'):
                    #             player_version = self._search_regex(
                    #                 r'-(.+?)(?:/watch_as3)?\.swf$', player_url,
                    #                 'flash player', fatal=False)
                    #             player_desc = 'flash player %s' % player_version
                    #         else:
                    #             player_version = self._search_regex(
                    #                 [r'html5player-([^/]+?)(?:/html5player(?:-new)?)?\.js',
                    #                  r'(?:www|player)-([^/]+)(?:/[a-z]{2}_[A-Z]{2})?/base\.js'],
                    #                 player_url,
                    #                 'html5 player', fatal=False)
                    #             player_desc = 'html5 player %s' % player_version
                    #
                    #     parts_sizes = self._signature_cache_id(encrypted_sig)
                    #     self.to_screen('{%s} signature length %s, %s' %
                    #                    (format_id, parts_sizes, player_desc))

                    signature = self._decrypt_signature(
                        encrypted_sig, video_id, player_url, age_gate)
                    url += '&signature=' + signature
                if 'ratebypass' not in url:
                    url += '&ratebypass=yes'

                dct = {
                    'format_id': format_id,
                    'url': url,
                    'player_url': player_url,
                }
                if format_id in self._formats:
                    dct.update(self._formats[format_id])
                if format_id in formats_spec:
                    dct.update(formats_spec[format_id])

                # Some itags are not included in DASH manifest thus corresponding formats will
                # lack metadata (see https://github.com/rg3/youtube-dl/pull/5993).
                # Trying to extract metadata from url_encoded_fmt_stream_map entry.
                mobj = re.search(r'^(?P<width>\d+)[xX](?P<height>\d+)$', url_data.get('size', [''])[0])
                width, height = (int(mobj.group('width')), int(mobj.group('height'))) if mobj else (None, None)

                more_fields = {
                    'filesize': int_or_none(url_data.get('clen', [None])[0]),
                    'tbr': float_or_none(url_data.get('bitrate', [None])[0], 1000),
                    'width': width,
                    'height': height,
                    'fps': int_or_none(url_data.get('fps', [None])[0]),
                    'format_note': url_data.get('quality_label', [None])[0] or url_data.get('quality', [None])[0],
                }
                for key, value in more_fields.items():
                    if value:
                        dct[key] = value
                type_ = url_data.get('type', [None])[0]
                if type_:
                    type_split = type_.split(';')
                    kind_ext = type_split[0].split('/')
                    if len(kind_ext) == 2:
                        kind, _ = kind_ext
                        dct['ext'] = mimetype2ext(type_split[0])
                        if kind in ('audio', 'video'):
                            codecs = None
                            for mobj in re.finditer(
                                    r'(?P<key>[a-zA-Z_-]+)=(?P<quote>["\']?)(?P<val>.+?)(?P=quote)(?:;|$)', type_):
                                if mobj.group('key') == 'codecs':
                                    codecs = mobj.group('val')
                                    break
                            if codecs:
                                dct.update(parse_codecs(codecs))
                formats.append(dct)
        elif video_info.get('hlsvp'):
            manifest_url = video_info['hlsvp'][0]
            formats = []
            m3u8_formats = self._extract_m3u8_formats(
                manifest_url, video_id, 'mp4', fatal=False)
            for a_format in m3u8_formats:
                itag = self._search_regex(
                    r'/itag/(\d+)/', a_format['url'], 'itag', default=None)
                if itag:
                    a_format['format_id'] = itag
                    if itag in self._formats:
                        dct = self._formats[itag].copy()
                        dct.update(a_format)
                        a_format = dct
                a_format['player_url'] = player_url
                # Accept-Encoding header causes failures in live streams on Youtube and Youtube Gaming
                a_format.setdefault('http_headers', {})['Youtubedl-no-compression'] = 'True'
                formats.append(a_format)
        else:
            unavailable_message = self._html_search_regex(
                r'(?s)<h1[^>]+id="unavailable-message"[^>]*>(.+?)</h1>',
                video_webpage, 'unavailable message', default=None)
            if unavailable_message:
                raise ExtractorError(unavailable_message, expected=True)
            raise ExtractorError('no conn, hlsvp or url_encoded_fmt_stream_map information found in video info')

        # Look for the DASH manifest
        # if self._downloader.params.get('youtube_include_dash_manifest', True):
        #     dash_mpd_fatal = True
        #     for mpd_url in dash_mpds:
        #         dash_formats = {}
        #         try:
        #             def decrypt_sig(mobj):
        #                 s = mobj.group(1)
        #                 dec_s = self._decrypt_signature(s, video_id, player_url, age_gate)
        #                 return '/signature/%s' % dec_s
        #
        #             mpd_url = re.sub(r'/s/([a-fA-F0-9\.]+)', decrypt_sig, mpd_url)
        #
        #             for df in self._extract_mpd_formats(
        #                     mpd_url, video_id, fatal=dash_mpd_fatal,
        #                     formats_dict=self._formats):
        #                 # Do not overwrite DASH format found in some previous DASH manifest
        #                 if df['format_id'] not in dash_formats:
        #                     dash_formats[df['format_id']] = df
        #                 # Additional DASH manifests may end up in HTTP Error 403 therefore
        #                 # allow them to fail without bug report message if we already have
        #                 # some DASH manifest succeeded. This is temporary workaround to reduce
        #                 # burst of bug reports until we figure out the reason and whether it
        #                 # can be fixed at all.
        #                 dash_mpd_fatal = False
        #         except (ExtractorError, KeyError) as e:
        #             self.report_warning(
        #                 'Skipping DASH manifest: %r' % e, video_id)
        #         if dash_formats:
        #             # Remove the formats we found through non-DASH, they
        #             # contain less info and it can be wrong, because we use
        #             # fixed values (for example the resolution). See
        #             # https://github.com/rg3/youtube-dl/issues/5774 for an
        #             # example.
        #             formats = [f for f in formats if f['format_id'] not in dash_formats.keys()]
        #             formats.extend(dash_formats.values())

        # Check for malformed aspect ratio
        stretched_m = re.search(
            r'<meta\s+property="og:video:tag".*?content="yt:stretch=(?P<w>[0-9]+):(?P<h>[0-9]+)">',
            video_webpage)
        if stretched_m:
            w = float(stretched_m.group('w'))
            h = float(stretched_m.group('h'))
            # yt:stretch may hold invalid ratio data (e.g. for Q39EVAstoRM ratio is 17:0).
            # We will only process correct ratios.
            if w > 0 and h > 0:
                ratio = w / h
                for f in formats:
                    if f.get('vcodec') != 'none':
                        f['stretched_ratio'] = ratio

        self._sort_formats(formats)

        # self.mark_watched(video_id, video_info)

        return {
            'id': video_id,
            'uploader': video_uploader,
            'uploader_id': video_uploader_id,
            'uploader_url': video_uploader_url,
            'upload_date': upload_date,
            'license': video_license,
            'creator': video_creator,
            'title': video_title,
            'alt_title': video_alt_title,
            'thumbnail': video_thumbnail,
            'description': video_description,
            'categories': video_categories,
            'tags': video_tags,
            # 'subtitles': video_subtitles,
            # 'automatic_captions': automatic_captions,
            'duration': video_duration,
            'age_limit': 18 if age_gate else 0,
            # 'annotations': video_annotations,
            'webpage_url': proto + '://www.youtube.com/watch?v=%s' % video_id,
            'view_count': view_count,
            'like_count': like_count,
            'dislike_count': dislike_count,
            'average_rating': float_or_none(video_info.get('avg_rating', [None])[0]),
            'formats': formats,
            'is_live': is_live,
            'start_time': start_time,
            'end_time': end_time,
            'series': series,
            'season_number': season_number,
            'episode_number': episode_number,
        }
    def youtubeformats(self):
        return self._formats;


    def extractVideo(self,url):
        dic = self.real_extractor(url)
        wformats = []
        for d  in dic['formats']:
            if not (int(d['format_id']) >78):
                url = d['url'];
                response = requests.head(url)
                d['filesize']  =  response.headers['Content-Length']
                wformats.append(d)

        dic['formats'] = wformats;
        return dic
    def bestVideo(self,url):
        dic = self.extractVideo(url);
        vdic = dic['formats'][-1];
        return vdic['url']



