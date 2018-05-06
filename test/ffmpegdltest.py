import os, time
from pipeline import Acquirer, DataMiner, ERROR, READY
from youtube_dl import YoutubeDL
import ffmpeg

class YoutubeVideoDownloader(Acquirer):
	def __init__(self, tempDir='./tmp/', options = None):
		Acquirer.__init__(self, tempDir)

	   	if options == None: # default options
			self.setOptions({
			'writeautomaticsub': False,
	  		'outtmpl': unicode(self.tempDir + '%(id)s.%(ext)s'),
 			'skip_download': False,
			'format': 'bestvideo[height<=320]',
			'quiet': False
			})
		else:
			self.setOptions(options)

	def filenameCatcher(self, event):
		if event['status'] == 'finished':
			self.subfilename = event['filename']

	def setOptions(self, opts):
		opts['progress_hooks']=[self.filenameCatcher]
		self.ydl_opts = opts
		

	def acquire(self, *url):
		self.subfilename = ''

		with YoutubeDL(self.ydl_opts) as ydl:
			ydl.download(url)

		if self.subfilename == '':
			print "ERROR"
			return self.subfilename, ERROR

		return self.subfilename, READY

class FFmpegFrameExtractor(DataMiner):
	def __init__(self, tempDir='./tmp/', fps = 0.5, options = None):
		DataMiner.__init__(self, tempDir)

		self.fps = fps

		if options == None:
			# set defaults here
			self.options = {}
		else:
			self.options = options


	def build(self, data):
		input = self.tempDir + data

		name = os.path.splitext(data)[0]

		# Get output folder
		outputDir = os.path.join(self.tempDir, name)
		print(outputDir)

		if not os.path.isdir(outputDir):
			os.makedirs(outputDir)

		stream = ffmpeg.input(input)
		stream = ffmpeg.filter_(stream, 'fps', fps=0.25, round='up')
		stream = ffmpeg.output(stream, os.path.join(outputDir, '%04d.png'))
		result = ffmpeg.run(stream)

ac = YoutubeVideoDownloader()

#ac.performAcquire("https://www.youtube.com/watch?v=wGkvyN6s9cY", 1)

dm = FFmpegFrameExtractor()

thing = dm.build("wGkvyN6s9cY.mp4")
