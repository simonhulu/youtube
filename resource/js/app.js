function parseURL(url) {
        var parser = document.createElement('a'),
            searchObject = {},
            queries, split, i;
        // Let the browser do the work
        parser.href = url;
        // Convert query string to object
        queries = parser.search.replace(/^\?/, '').split('&');
        for( i = 0; i < queries.length; i++ ) {
            split = queries[i].split('=');
            searchObject[split[0]] = split[1];
        }
        return {
            protocol: parser.protocol,
            host: parser.host,
            hostname: parser.hostname,
            port: parser.port,
            pathname: parser.pathname,
            search: parser.search,
            searchObject: searchObject,
            hash: parser.hash
        };
    }
    var vo = document.getElementById("vid");;
    var aspectRatio;
    var targetWidth;
    var targetHeight;
    var resizeW;
    var resizeH;
    var canvas = document.getElementById("canvas");
    $(document).ready(function(){
        var formats ;
        var videotitle;
        var subtitles;

        $('.showbtn').click(function(e){
            var videoUrl = $('#videourl').val().trim();

            var videoId = parseURL(videoUrl).searchObject.v
            if(videoId == "" || !videoId)
            {
                alert("Invalid youtube link");
                return;
            }
            $('#mainshot').attr('src',"http://img.youtube.com/vi/"+videoId+"/maxresdefault.jpg");
            $('.downloadpreview img').attr('src',"http://img.youtube.com/vi/"+videoId+"/maxresdefault.jpg");
            var imgObjs = ($(".thumbnails").find(".thumbnailimg"))
            for(var i=0;i<imgObjs.length;i++)
            {
                var imgObj =imgObjs[i];
                var url = "http://img.youtube.com/vi/"+videoId+"/"+i+".jpg";
                imgObj.src = url;
                var a = $(imgObj).siblings(".thumbbtn");
                a.attr("href",url) ;
                a.attr("download" , "thumbnail.jpg");
                switch(i){
                case 0:
                    imgObj.alt="hqdefault.jpg";
                break;
                default:
                imgObj.alt="thumbnail_"+i+".jpg";
                break;
                }
                var img = new Image();

                img.onload = (function(imgObj) {
                    return function() {
                       console.log(this.width+"x"+this.height);
                       $(imgObj).nextAll('p').text('Size: '+this.width+"x"+this.height+".");
                    }
                })(imgObj);
                img.src = url;

            }
            var $this = $(this);
            $this.button('loading');
            $.ajax({type: "POST", url:"/getVideoUrl",data: { url: encodeURI(videoUrl) }}).done(function(res) {
                $this.button('reset');
                if(res.status !=0)
                {
                    var errMsg = res.res['errMsg'];
                    alert(errMsg);
                    return;
                }
                var res = res.res;
                formats = res['formats'];
                subtitles = res['subtitles'];
                videotitle = res['title'];
                var bestFormat = formats[formats.length-1];
                vurl = bestFormat['url'] ;
                $('#ytvideo video').attr('src',vurl);
                $('#ytvideo video').get(0).addEventListener("loadedmetadata",function(){
                     aspectRatio = vo.videoWidth/vo.videoHeight;
                     targetWidth = vo.videoWidth;
                     targetHeight = parseInt(targetWidth/aspectRatio,10);
                     canvas.width = targetWidth;
                     canvas.height = targetHeight;
                });
                $('.thumbnailsdiv').show();
                $('.videoarea').show();
                $('.canvasarea').show();

                $('.videolist').empty()
                for(var i = 0 ;i<formats.length;i++)
                {
                    var d = formats[i];
                    var height = d['height'];
                    var formatnote = d['format_note'];
                    var des = "";
                    var filesize = parseFloat(d['filesize'])
                    var filesizeinmb = parseInt(filesize*0.00000095367432);
                    var resolution = d['resolution'];
                    var url = d['url'];

                    if(height <360){
                        des = "Youtube Video <b>Mobile Version (3GP)</b>, Resolution:"+resolution+", Size : "+filesizeinmb+"mb ";
                    }else if(height <480)
                    {
                        des = "Youtube Video <b>Standard Quality (360p)</b>, Resolution:"+resolution+", Size : "+filesizeinmb+"mb ";
                    }else if(height<720)
                    {
                        des = "Youtube Video <b>High Quality (480p)</b>, Resolution:"+resolution+", Size : "+filesizeinmb+"mb ";
                    }else
                    {
                        des = "Youtube Video <b>High Quality ("+formatnote+")</b>, Resolution"+resolution+":, Size : "+filesizeinmb+"mb "
                    }
                    $('.videolist').append($("<div class='radio'><label><input type='radio' name='optradio' value="+i+">"+des+"</label></div>").click(selectdownload))
                }
                if(subtitles)
                {
                    for(var k in subtitles)
                    {
                        lang_subtitles = subtitles[k];
                        for (var  i = 0 ;i<lang_subtitles.length;i++)
                        {
                            lang_subtitle = lang_subtitles[i];
                            var ext = lang_subtitle['ext'];
                            var url = lang_subtitle["url"];
                            des = "Youtube Video Subtitle  "+k+" subtitles."+ext;
                            $('.videolist').append($("<div class='radio'><label><input type='radio' name='optradio' value="+url+">"+des+"</label></div>").click(subtitledownload))
                        }
                    }
                }
                $(".detectevideo").show();

            }).fail(function(){
               alert("failed");
               $this.button('reset')
            });
        })

        $('#snap').bind('click',function(){
            $('#mainshot').hide();
            printScreenshots();
        });

        function printScreenshots(){
        console.log(resizeW)
        console.log(targetWidth)
            targetWidth = resizeW || targetWidth;
            targetHeight = resizeH || targetHeight
            $('#resizeWidth').val(targetWidth);
            $('#resizeHeight').val(targetHeight);
            canvas.width = targetWidth;
            canvas.height = targetHeight;
            $(canvas).width(targetWidth);
            $(canvas).height(targetHeight);
            $('#canvas').show();
            var context = canvas.getContext("2d");
            context.fillRect(0,0,targetWidth,targetHeight);
            context.drawImage(vo,0,0,targetWidth,targetHeight);
            $(".screenshotsarea").show();
        }

        $('.downloadvidebtn').click(function(e){
            e.preventDefault();
            var href = $(this).attr('href');
            location.href = href;
        })

        function subtitledownload(){
//            var subtitle = subtitles[0];
//            var subtitleurl = subtitle['url'];
//            var ext = subtitle['ext'];
            var url = $('.radio input:checked').val();
            $('.downloadvidebtn').attr('href',url);
            $('.downloadvidebtn').attr('download',"subtitle");
        }

        function selectdownload(){
            var index = $('.radio input:checked').val();
            var format = formats[index];
            var ext = format['ext'];
            $('.downloadvidebtn').attr('href',format['url']+"&title="+(videotitle+"."+ext));
            $('.downloadvidebtn').attr('download',videotitle+"."+ext);
        }



        $('#resize').bind('click',function(){
            var tempW = parseInt($('#resizeWidth').val(),10);
            var tempH = parseInt($('#resizeHeight').val(),10);
            if(tempW > 0 && tempH > 0)
            {
                resizeW = tempW;
                resizeH = tempH;
            }else if(tempW > 0 && (!tempH || tempH <=0) )
            {
                tempH = parseInt(tempW/aspectRatio);
                resizeW = tempW;
                resizeHeight = tempH;
            }else if(tempH > 0 && (!tempW || tempW <=0) ){
                tempW = parseInt(tempH*aspectRatio);
                resizeW = tempW;
                resizeH = tempH;
            }else{
                resizeW = targetWidth;
                resizeH = targetHeight;
            }
            $('#resizeWidth').val(resizeW);
            $('#resizeHeight').val(resizeH);
            $('#canvas').width(resizeW);
            $('#canvas').height(resizeH);
            printScreenshots();
        });
    })