from __future__ import unicode_literals
import youtube_dl
import ffprobe
import ffprobe3
import ffmpeg


class Acquirer:

    def performAcquire(self, *args):

        self.status = 0
		# TODO: do this in separate thread later:
        result = self.acquire(*args)
        self.status = 1

        return result
    def acquire(self, *args):
        """ 	Do something to acquire data. 
			This can e.g return text data directly
			or write extracted frames out to files
			and return list of resulting filenames
			etc. """
        pass



class YDLSettings(Acquirer):

    class MyLogger(object):
     def debug(self, msg):
         pass
     def warning(self, msg):
         pass
     def error(self, msg):
         print(msg)


    def my_hook(self, d):
        filename = d['filename']
        if d['status'] == 'finished':
            #Python 3 syntax, swap
            print 'Done downloading, now converting ...'
            print filename

    def __init__(self, ydl_opts):

        ydl_opts['progress_hooks']=[self.my_hook]
        self.ydl_opts=ydl_opts
       

 
    def acquire(self, video_url):
        #url = raw_input('Please enter the URL of the video you wish to download: ' )
        with youtube_dl.YoutubeDL(self.ydl_opts) as ydl:
             ydl.download([video_url])
             
     
defaultSettings=YDLSettings({'format': 'bestaudio/best',
         'forcejson':'true',
         'writeautomaticsub':'true',
         'writesubtitles':'true',
         'writeinfojson':'true',
         'writedescription':'true',
         'rejecttitle':'true',
         'outtmpl': unicode('./tmp/%(id)s.%(ext)s'),

      'postprocessors': [{
         'key': 'FFmpegExtractAudio',
         'preferredcodec': 'wav',
         'preferredquality': '192',

       }],
      'logger': YDLSettings.MyLogger(),
        #'progress_hooks': [],
        })

video_url=raw_input('Please enter the URL of the video you wish to download: ')

defaultSettings.acquire(video_url)