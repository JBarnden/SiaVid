import re

class SRTChunk:
	""" Defines a Chunk of an SRT file - some content that exists between
		a startTime and an endTime """

	def __init__(self):
		self.content = []
		self.startTime = 0
		self.endTime = 0

	def getFullText(self):
		return " ".join(self.content)
		

class SRTChunker:
	""" Takes a .srt subtitle file and converts it into an array of Chunks and
		a reverse-indexed lookup table by whole words """

	file = 0
	chunks = []

	words = {}

	def __init__(self, filename):
		""" Reads provided file, chunks it and runs tagWords on each chunk """

		with open(filename, "r") as file:
			chunk = None
			identifier = True # sentinel for skipping Identifier lines
		
			for line in file:
				line = line.strip() # trims leading/trailing whitespace etc.

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
		""" Takes a timestamp in .srt (hh:mm:ss,mmm) format and
			converts it to a (float) number of seconds """

		timestamp, millis = timestamp.split(",")
		stamp = map(int, timestamp.split(":"))
		
		seconds = stamp[0]*3600 + stamp[1]*60 + stamp[2] + float(millis)/1000
		return seconds

	def tagWords(self, chunk):
		""" Adds a reference to the current chunk to each word
			in the Words dictionary """

		for word in chunk.getFullText().split(" "):
			
			# isolate actual word - no punctuation on either side
			tmp = re.search("([A-Za-z']+)", word)

			if tmp:
				word = tmp.group(1)

			word = word.lower()

			if not self.words.has_key(word):
				self.words[word] = []
			self.words[word].append(chunk)

