from pipeline import DataMiner, SearchEngine, Acquirer, OUT_OF_DATE, WAIT, READY, ERROR
from time import sleep
import re


class SplitDataMiner(DataMiner):
	""" Example DataMiner that splits raw input data at occurences
		of 'e' """

	def build(self, data):
		results = []
		for item in data:
			halves = item.split('e')
			results.append(halves[0])
			results.append(halves[1])
		return results

class SplitDataMinerWithDelay(SplitDataMiner):

    def build(self, data):
        sleep(10)
        SplitDataMiner.build(self, data)

class SearchInFirstLine(SearchEngine):
	""" Example SearchEngine that finds the first instance of a given
		substring in the first element of the corpus provided """

	def performSearch(self, corpus, terms):
		""" Simple example search: Finds substring 'terms' in first
			line of corpus """

		result = [] # holds search results

		result.append(corpus[0].find(terms))

		return result

class ReadFileAcquirer(Acquirer):
	""" Example Acquirer that reads from a given filename into a list """

	def acquire(self, filename):
		lines = []
		
		with open(filename, "r") as file:
			lines = file.readlines()

		return lines

class AlwaysFailAcquirer(Acquirer):
	""" Example acquirer that always fails. """

	def acquire(self, args):
		return None, ERROR

###################################################################################

class PassThroughAcquirer(Acquirer):
	""" Copies the file to ./tmp and returns path of new file """

	def acquire(self, filename):

		# strip off any path elements before filename
		slashIndex = filename.rfind("/")
		if slashIndex > 0:
			slashIndex += 1

		workingCopy = "./tmp/" + filename[slashIndex:]
		
		with open(workingCopy, 'w') as outfile:
			with open(filename, 'r') as infile:
				lines = infile.readlines()
				for line in lines:
					outfile.write(line)

		return workingCopy

import youtube_dl, os

class YoutubeAutoVSSAcquirer(Acquirer):
	def __init__(self, tempDir='./tmp/', options = None):
		Acquirer.__init__(self, tempDir)
		if options == None: # Set default options
			self.setOptions({
				'writeautomaticsub': True,
				'outtmpl': unicode(self.tempDir + '%(id)s.%(ext)s'),
				'skip_download': True,
				'quiet': True
			})

	def setOptions(self, opts):
		self.ydl_opts = opts

	def acquire(self, *url):
		self.subfilename = self.tempDir + url[0].split("=")[1] + '.en.vtt'
    
		with youtube_dl.YoutubeDL(self.ydl_opts) as ydl:
			ydl.download(url)

		if not os.path.isfile(self.subfilename):
			print self.subfilename, "does not exist."
			return '', ERROR

		return self.subfilename, READY

class YoutubeMediaAcquirer(Acquirer):
	def __init__(self, tempDir='./tmp/'):
		Acquirer.__init__(self, tempDir)
		self.setOptions({
			'writeautomaticsub': True,
    		'outtmpl': unicode(self.tempDir + '%(id)s.%(ext)s'),
    		'skip_download': False,
			'quiet': False
		})

	def filenameCatcher(self, event):
		print "Catcher triggered:", event
		if event['status'] == 'finished':
			self.subfilename = event['filename']

	def setOptions(self, opts):
		opts['progress_hooks']=[self.filenameCatcher]
		self.ydl_opts = opts
		

	def acquire(self, *url):
		self.subfilename = ''
    
		with youtube_dl.YoutubeDL(self.ydl_opts) as ydl:
			ydl.download(url)

		if self.subfilename == '':
			print "ERROR"
			return self.subfilename, ERROR

		return self.subfilename, READY


class YoutubeVideoAcquirer(Acquirer):
	def __init__(self, tempDir='./tmp/'):
		Acquirer.__init__(self, tempDir)
		self.setOptions({
			'keepvideo': True,
			'format':'best',
			'outtmpl': unicode(self.tempDir + '%(id)s.%(ext)s'),
			'skip_download': False,
			'quiet': False,
		})

	def filenameCatcher(self, event):
		print "Catcher triggered:", event
		if event['status'] == 'finished':
			self.videoFileName = event['filename']

	def setOptions(self, opts):
		opts['progress_hooks'] = [self.filenameCatcher]
		self.ydl_opts = opts

	def acquire(self, *url):
		self.videoFileName = ''

		with youtube_dl.YoutubeDL(self.ydl_opts) as ydl:
			ydl.download(url)

		if self.videoFileName == '':
			print "ERROR"
			return self.videoFileName, ERROR

		return self.videoFileName, READY


class YoutubeAudioAcquirer(Acquirer):
	"""	
		Requires ffmpeg and ffprobe, or avprobe and avconv on the host system
		(apt-get install libav-tools installs avconv and avprobe
		on linux)
	"""
	def __init__(self, tempDir='./tmp/'):
		Acquirer.__init__(self, tempDir)
		self.downloadPath = ''
		self.setOptions({
                'outtmpl': unicode(tempDir + '%(id)s.%(ext)s'),
                'format': 'bestaudio/best',
                'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'wav',
                'preferredquality': '192',
            }],
            })

	def filenameCatcher(self, event):
		print "Catcher triggered:", event
		if event['status'] == 'finished':
			self.downloadPath = event['filename']

	def setOptions(self, opts):
		opts['progress_hooks'] = [self.filenameCatcher]
		self.ydl_opts = opts

	def acquire(self, *url):
		"""
			The acquire method attempts to download a video from a youtube url
			(webm format).  The video is then converted to wav (as stated in
			the initial options in init).
		"""
		self.downloadPath = ''

		with youtube_dl.YoutubeDL(self.ydl_opts) as ydl:
			ydl.download(url)

		if self.downloadPath == '':
			print "ERROR"
			return self.downloadPath, ERROR

		# Use ntpath to get file name (for compatibility with windows)
		import ntpath
		audioFileName = ntpath.basename(self.downloadPath)
		# File name returned has the extention ".webm", its replaced with ".wav"
		# manually (quick and dirty).
		audioFileName = audioFileName.split('.')[0] + ".wav"

		return audioFileName, READY

class FileToLineMiner(DataMiner):
	def build(self, data):
		lines = []
		
		with open(data, "r") as file:
			lines = file.readlines()
		
		return lines

import re
from chunker import SRTChunk

class SRTChunkListToRIDict(DataMiner):
	""" Takes a list of SRTChunks and builds a reverse-indexed dict of
		word => list of chunks containing word
	"""

	def build(self, data):
		words = {}

		for chunk in data:
			self.tagWords(chunk, words)

		return words

	def tagWords(self, chunk, words):
		""" Adds a reference to the current chunk to each word
			in the Words dictionary """
		usedwords = []

		for word in chunk.getFullText().split(" "):
			
			# isolate actual word - no punctuation on either side
			tmp = re.search("([A-Za-z']+)", word)

			if tmp:
				word = tmp.group(1)

			word = word.lower()

			if not word in usedwords:
				usedwords.append(word)

				if not words.has_key(word):
					words[word] = []
				words[word].append(chunk)


class SRTChunkMiner(DataMiner):
	""" Takes a filename, returns a dict of lists of chunks, indexed by word """

	def build(self, data):
		words = {}
		chunks = []

		chunk = None
		identifier = True # sentinel for skipping Identifier lines
		
		for line in data:
			line = line.strip() # trims leading/trailing whitespace etc.

			# strip out HTML-style codes
			line = re.sub(r"<.+>", "", line)

			if ("-->" in line):
				if chunk:			# if we have an existing chunk, save it...
					self.tagWords(chunk, words)	# Add chunk reference to words in chunk
					chunks.append(chunk)

				chunk = SRTChunk()		# ... and make a new one

				chunk.startTime, chunk.endTime = map(self.timestampToSeconds, line.split(" --> "))

			elif identifier == True: 		# skip message identifier lines following blank lines
				identifier = False

			elif line != "":			# append line to content
				chunk.content.append(line)

			else:					# blank line found, skip next identifier line
				identifier = True
		return words

	def timestampToSeconds(self, timestamp):
		""" Takes a timestamp in .srt (hh:mm:ss,mmm) format and
			converts it to a (float) number of seconds """

		timestamp, millis = timestamp.split(",")
		stamp = map(int, timestamp.split(":"))
		
		seconds = stamp[0]*3600 + stamp[1]*60 + stamp[2] + float(millis)/1000
		return seconds

	def tagWords(self, chunk, words):
		""" Adds a reference to the current chunk to each word
			in the Words dictionary """
		usedwords = []

		for word in chunk.getFullText().split(" "):
			
			# isolate actual word - no punctuation on either side
			tmp = re.search("([A-Za-z']+)", word)

			if tmp:
				word = tmp.group(1)

			word = word.lower()

			if not word in usedwords:
				usedwords.append(word)

				if not words.has_key(word):
					words[word] = []
				words[word].append(chunk)

class VSSChunkMiner(DataMiner):
	def build(self, data):
		words = {}
		chunks = []

		chunk = None
		skip = True

		for line in data:
			line = line.strip() # trims leading/trailing whitespace etc.

			if line == '##':
				skip = False
				continue

			if skip: continue

			# strip out HTML-style codes
			line = re.sub(r"<.*?>", "", line)

			if ("-->" in line):
				line = line[:29] 	# clip 'align' etc.
				if chunk:			# if we have an existing chunk, save it...
					self.tagWords(chunk, words)	# Add chunk reference to words in chunk
					chunks.append(chunk)

				chunk = SRTChunk()		# ... and make a new one

				chunk.startTime, chunk.endTime = map(self.timestampToSeconds, line.split(" --> "))
			elif line != "":			# append line to content
				chunk.content.append(line)

		return words

	def timestampToSeconds(self, timestamp):
		""" Takes a timestamp in .vss (hh:mm:ss.mmm) format and
			converts it to a (float) number of seconds """

		timestamp, millis = timestamp.split(".")
		stamp = map(int, timestamp.split(":"))
		
		seconds = stamp[0]*3600 + stamp[1]*60 + stamp[2] + float(millis)/1000
		return seconds		

	def tagWords(self, chunk, words):
		""" Adds a reference to the current chunk to each word
			in the Words dictionary """
		usedwords = []

		for word in chunk.getFullText().split(" "):
			
			# isolate actual word - no punctuation on either side
			tmp = re.search("([A-Za-z']+)", word)

			if tmp:
				word = tmp.group(1)

			word = word.lower()

			if not word in usedwords:
				usedwords.append(word)

				if not words.has_key(word):
					words[word] = []
				words[word].append(chunk)

from trie import Trie, TrieNode


class SRTTrieMiner(DataMiner):
	def build(self, data):

		# build list of actual lines for chunking
		lines = []
		
		with open(data, "r") as file:
			lines = file.readlines()

		# get our dict of word-indexed chunklists
		chunker = SRTChunkMiner()
		words = chunker.build(lines)

		# build a trie from chunklists
		trie = Trie()
		for word in words:
			if word != '':
				target = trie.getSubtree(word)
				if target == None:
					target = TrieNode()
					trie.addSubtree(word, target)
				else:
					target = target.root

				for item in words[word]:
					target.content.append(item)

		return trie

class VSSTrieMiner(DataMiner):
	def build(self, data):

		# build list of actual lines for chunking
		lines = []
		
		with open(data, "r") as file:
			lines = file.readlines()

		# get our dict of word-indexed chunklists
		chunker = VSSChunkMiner()
		words = chunker.build(lines)

		# build a trie from chunklists
		trie = Trie()
		for word in words:
			if word != '':
				target = trie.getSubtree(word)
				if target == None:
					target = TrieNode()
					trie.addSubtree(word, target)
				else:
					target = target.root

				for item in words[word]:
					target.content.append(item)

		return trie

class TrieMiner(DataMiner):
	def build(self, data):
		words = data

		# build a trie from chunklists
		trie = Trie()
		for word in words:
			if word != '':
				target = trie.getSubtree(word)
				if target == None:
					target = TrieNode()
					trie.addSubtree(word, target)
				else:
					target = target.root

				for item in words[word]:
					target.content.append(item)

		return trie



from sets import Set

class TrieSearch(SearchEngine):

	def walkTrie(self, node, results):
		""" Walk the trie rooted at 'node', appending results as we go """

		for item in node.content:
			results.add(item)

		for child in node.children:
			self.walkTrie(node.children[child], results)


	def performSearch(self, corpus, terms):
		""" For each search term, get the trie rooted at it add children to results  """

		results = Set() # only want unique results
		
		for term in terms:
			candidates = corpus.getSubtree(term)

			if candidates is None:
				continue

			root = candidates.getNode("")

			self.walkTrie(root, results)				
		
		return results	
