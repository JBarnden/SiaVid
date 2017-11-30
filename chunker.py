from pattern.en import parse, pprint
import re

class SRTChunk:
	def __init__(self):
		self.content = []
		startTime = 0
		endTime = 0

	def getFullText(self):
		return " ".join(self.content)
		

class SRTChunker:
	file = 0
	chunks = []

	words = {}

	def __init__(self, filename):
		file = open(filename, "r")

		line = file.readline().strip()
		with open(filename, "r") as file:
			chunk = None
			identifier = True
		
			for line in file:
				line = line.strip()

				# strip out HTML-style codes
				line = re.sub(r"<.+>", "", line)

				if ("-->" in line):
					if chunk:			# if we have an existing chunk, save it...
						self.tagWords(chunk)	# Add chunk reference to words in chunk
						self.chunks.append(chunk)

					chunk = SRTChunk()		# ... and make a new one


					chunk.startTime, chunk.endTime = map(self.timestampToSeconds, line.split(" --> "))

				elif identifier == True: 		# skip message identifier lines following blank lines
					identifier = False

				elif line != "":			# append line to content
					chunk.content.append(line)

				else:					# blank line found, skip next identifier line
					identifier = True

	def timestampToSeconds(self, timestamp):
		timestamp, millis = timestamp.split(",")
		stamp = map(int, timestamp.split(":"))
		
		seconds = stamp[0]*3600 + stamp[1]*60 + stamp[2] + float(millis)/1000
		return seconds

	def tagWords(self, chunk):
		""" Adds a reference to the current chunk to each word
			in the Words dictionary """

		for word in chunk.getFullText().split(" "):
			
			# isolate actual word
			tmp = re.search("([A-Za-z']+)", word)
			if tmp:
				word = tmp.group(1)

			word = word.lower()

			if not self.words.has_key(word):
				self.words[word] = []
			self.words[word].append(chunk)

	def nextChunk():
		pass


