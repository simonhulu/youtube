from flask import Flask
from flask import request
from flask import render_template
import youtube_dl
from flask import jsonify
from Imeili100Result import Imeili100Result,Imeili100ResultStatus
app = Flask(__name__)

@app.route('/')
def hello_world():
    return render_template('youtubescreenshot.html')

@app.route('/getVideoUrl/')
def getVideoUrl():

    youtubeUrl = request.args.get('url');
    url = "";
    imeilires = Imeili100Result()
    with youtube_dl.YoutubeDL() as ydl:
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

