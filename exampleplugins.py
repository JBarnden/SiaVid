from pipeline import DataMiner, SearchEngine, Acquirer
from time import sleep

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

	def __init__(self, filename):
		self.filename = filename

	def acquire(self):
		lines = []

		with open(self.filename, "r") as file:
			lines = file.readlines()

		return lines

###################################################################################

import youtube-dl

class YoutubeSRTAcquirer(Acquirer):
	def __init__(self):
		self.ydl_opts = {
			'writeautomaticsub': True,
    		'outtmpl': unicode('./tmp/%(id)s.%(ext)s'),
    		'skip_download': True,
    		'quiet': True,
		}
	def setOptions(self, opts):
		self.ydl_opts = opts

	def acquire(self, url):
		subfilename = ''

		with youtube_dl.YoutubeDL(self.ydl_opts) as ydl:
    		ydl.download(url)
			
		subfilename = url.split("=")[1]
		print subfilename
		return subfilename

import re
from chunker import SRTChunk

class SRTChunkMiner(DataMiner):
	""" Takes a filename, returns a dict lists of chunks, indexed by word """

	def build(self, data):
		words = {}
		chunks = []

		with open(data, "r") as file:
			chunk = None
			identifier = True # sentinel for skipping Identifier lines
		
			for line in file:
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


from trie import Trie, TrieNode


class SRTTrieMiner(DataMiner):
	def build(self, data):

		trie = Trie()
		for word in data.keys():
			if word != '':
				target = trie.getSubtree(word)
				if target == None:
					target = TrieNode()
					trie.addSubtree(word, target)
				else:
					target = target.root

				for item in data[word]:
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


	def search(self, corpus, terms):
		""" For each search term, get the trie rooted at it add children to results  """

		results = Set() # only want unique results
		
		for term in terms:
			candidates = corpus.getSubtree(term)

			if candidates is None:
				continue

			root = candidates.getNode("")

			self.walkTrie(root, results)				
		
		return results	