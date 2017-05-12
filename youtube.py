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
import re

compiled_regex_type = type(re.compile(''))
try:
    compat_str = unicode  # Python 2
except NameError:
    compat_str = str
NO_DEFAULT = object()
app = Flask(__name__)
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

@app.route('/getVideoUrl/')
def getVideoUrl():

    youtubeUrl = request.args.get('url');
    url = "";
    print(youtubeUrl)
    imeilires = Imeili100Result()
    vurl = extractor.extractVideo(youtubeUrl)
    imeilires.status = int(Imeili100ResultStatus.ok)
    imeilires.res = vurl;
    print(vurl)
    return jsonify(imeilires.__dict__)




if __name__ == '__main__':
    app.run(host='0.0.0.0',debug=True)




