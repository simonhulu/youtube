from flask import Flask
from flask import request
from flask import render_template
import youtube_dl
from flask import jsonify
from pytube import YouTube
# not necessary, just for demo purposes.
from pprint import pprint
from Imeili100Result import Imeili100Result,Imeili100ResultStatus
app = Flask(__name__)

@app.route('/')
def hello_world():
    return render_template('youtubescreenshot.html')

@app.route('/getVideoUrl/')
def getVideoUrl():
    yt = YouTube("http://www.youtube.com/watch?v=Ik-RsDGPI5Y")

    # Once set, you can see all the codec and quality options YouTube has made
    # available for the perticular video by printing videos.

    print(yt.get_videos())
    youtubeUrl = request.args.get('url');
    url = "";
    imeilires = Imeili100Result()
    ydl_opts = {"source-address":"104.154.23.74"}
    with youtube_dl.YoutubeDL(ydl_opts) as ydl:
        ydl.add_default_info_extractors()
        res = ydl.extract_info(youtubeUrl, False)
        formats = res['formats'];
        lastformat = formats[-1];
        url = lastformat['url'];
        imeilires.status = Imeili100ResultStatus.ok
        imeilires.res = url;
    return jsonify(imeilires.__dict__)


@app.route('/projects')
def about():
    return 'The about page'

if __name__ == '__main__':
    app.run(host='0.0.0.0')

