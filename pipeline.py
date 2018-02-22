from threading import Thread, current_thread, Lock
from time import sleep
import logging

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
handler = logging.StreamHandler()
handler.setFormatter(logging.Formatter('[%(threadName)s] %(message)s'))
logger.addHandler(handler)

statuses = ['READY','WAIT','ERROR','OUT_OF_DATE']
READY = 0
WAIT = 1
ERROR = 2
OUT_OF_DATE = 3

class Timeline:
	""" Holds a series of steps used in generating and
		searching a timeline
	"""

	def getStatus(self):
		return self.status

	def __init__(self, prettyName="", acquirer=None, miner=None, corpus=None, search=None):
		self.prettyName = prettyName
		self.acquirer = acquirer
		self.miner = miner
		self.corpus = corpus
		self.search = search
		self.status = OUT_OF_DATE
		self.successfulAcquirer=None
		
class Acquirer:
	""" Basic definition for data acquisition class """

	def __init__(self, tempDir='./tmp/'):
		self.tempDir = tempDir
		self.status = OUT_OF_DATE
		self.lock = Lock()

	def performAcquire(self, *args):
		""" calls self.acquire() in this thread """

		if self.status != READY:
			self.status = WAIT
			result = self.acquire(*args)
				
			if type(result) == tuple:
				self.status = result[1]
				result = result[0]
			else:
				self.status = READY

			return result

	def performAsyncAcquire(self, target, *args):
		""" Calls self.acquire() in another thread """

		# Create thread and dispatch
		t = Thread(target=self.doAsync, args=(target, args))
		t.start()

	def doAsync(self, target, args):
		""" Thread harness that calls and handles returns
			from acquire(), and sets plugin status.

			args is any acquirer arguments
			target is a tuple of (rawDataDict, acquireTag)
		"""

		if self.status != READY:
			self.status = WAIT
			result = self.acquire(*args)
			
			if type(result) == tuple:
				target[0][target[1]] = result[0]
				self.status = result[1]
			else:
				target[0][target[1]] = result
				self.status = READY

	def acquire(self, *args):
		""" Do something to acquire data. 
			This can e.g return text data directly
			or write extracted frames out to files
			and return list of resulting filenames
			etc.

			acquire MUST return some data, and may
			also return a new status code
		"""
		
		rawData = None

		# Do some kind of processing here

		return rawData, READY

	def checkStatus(self):
		""" Returns plugin status """
		return self.status

	def setStatus(self, status):
		""" Sets plugin status """
		self.status = status

class SearchEngine:
	""" Basic definition for SearchEngine class """

	def performSearch(self, corpus, terms):
		"""	Do something to extract results from corpus
			based on terms. Any method is appropriate
		"""
			
		results = []

		results.append("") # Search method here

		return results

class DataMiner:
	""" Basic definition for DataMiner class """

	def __init__(self, tempDir='./tmp/'):
		self.tempDir = tempDir
		self.status = OUT_OF_DATE
		self.lock = Lock()		

	def buildCorpus(self, args):
		""" calls self.build() in this thread """

		if self.status != READY:
			self.status = WAIT
			result = self.build(args)
			
			if type(result) == tuple:
				self.status = result[1]
				result = result[0]
			else:
				self.status = READY

			return result

	def buildAsyncCorpus(self, target, data):
		""" Starts a thread to run doBuild asynchronously with
			a given target and dataset.
		"""

		# Create thread and dispatch
		t = Thread(target=self.doAsync, args=(target, data))
		t.start()

	def doAsync(self, target, data):
		""" Thread harness that calls and handles returns
			from build(), and sets plugin status.

			data is data to be processed in some way
			target is a tuple of (corpusDict, corpusTag)
		"""

		if self.status != READY:
			self.status = WAIT
			result = self.build(data)

			if type(result) == tuple:
				target[0][target[1]] = result[0]
				self.status = result[1]
			else:
				target[0][target[1]] = result
				self.status = READY

	def build(self, data):
		""" Do something to convert data from an Acquirer
			either into a searchable corpus or an intermediate
			corpus for further processing by another DataMiner.
			The process doesn't matter, only that its output is
			consistent between this DataMiner and the receiving
			DataMiner or SearchEngine.

			build() MUST return some corpus and may also return
			a new status code.
		"""

		corpus = [] # Holds processed data
	
		corpus.append(data) # Processing here

		return corpus, READY

	def checkStatus(self):
		""" Returns plugin status """
		return self.status

	def setStatus(self, status):
		""" Sets plugin status """
		self.status = status

class Pipeline:
	def __init__(self):
		self.acquire = {}
		self.mine = {}
		self.search = {}

		self.rawData = {}
		self.corpus = {}

	def listAcquirers(self):
		""" Returns list of currently registered acquirers """

		return self.acquire.keys()

	def addAcquirer(self, acquirer, tag):
		""" Add a new acquirer tagged 'tag' """

		logger.info("Adding acquirer '{0}'.".format(tag))
		self.acquire[tag] = acquirer

	def removeAcquirer(self, tag):
		""" Remove the acquirer tagged 'tag' """

		if self.acquire.has_key(tag):
			logger.info("Deleting acquirer '{0}'.".format(tag))
			del self.acquire[tag]
			if self.rawData.has_key(tag):
				del self.rawData[tag]
		else:
			logger.error("No acquirer '{0}'.".format(tag))

	def listMiners(self):
		""" Returns list of currently registered data miners """

		return self.mine.keys()

	def addMiner(self, miner, tag):
		""" Add a new data miner tagged 'tag' """

		logger.info("Adding miner '{0}'.".format(tag))
		self.mine[tag] = miner

	def removeMiner(self, tag):
		""" Remove the data miner tagged 'tag' """

		if self.mine.has_key(tag):
			logger.info("Deleting miner '{0}'.".format(tag))
			del self.acquire[tag]
		else:
			logger.error("No miner '{0}'.".format(tag))

	def listSearch(self):
		""" Returns list of currently registered search engines """

		return self.search.keys()

	def addSearch(self, search, tag):
		""" Add a new search engine tagged 'tag' """

		logger.info("Adding search '{0}'.".format(tag))
		self.search[tag] = search

	def removeSearch(self, tag):
		""" Remove the search engine tagged 'tag' """

		if self.search.has_key(tag):
			logger.info("Deleting search '{0}'.".format(tag))
			del self.search[tag]
		else:
			logger.error("No search '{0}'.".format(tag))

	def performSearch(self, corpusTag, searchTag, searchTerms):
		""" Perform a search on a given corpus with a given search engine, using searchterms
			Returns a list of results """

		logger.info("Performing search on corpus '{0}' with engine '{1}', terms '{2}'".format(corpusTag, searchTag, searchTerms))

		if not self.search.has_key(searchTag):
			logger.error("No search '{0}' available.".format(searchTag))
			return

		if not self.corpus.has_key(corpusTag):
			logger.error("No corpus '{0}' available.".format(corpusTag))
			return

		return self.search[searchTag].performSearch(self.corpus[corpusTag], searchTerms)

	def performAcquire(self, acquireTag, *acquireArgs):
		""" Performs an Acquire using the tagged Acquirer and stores
			the results in rawData with the acquirer's tag """

		t = current_thread().name

		with self.acquire[acquireTag].lock:
			if self.acquire[acquireTag].status != READY:
				logger.info("Acquiring to data '{}' using Acquirer '{}'".format(acquireTag, acquireTag))
				self.rawData[acquireTag] = self.acquire[acquireTag].performAcquire(*acquireArgs)
			elif self.acquire[acquireTag].status == READY:
				logger.info("Data '{}' already exists; skipping.".format(acquireTag))

	def performAsyncAcquire(self, acquireTag, *acquireArgs):
		""" Performs an Acquire using the tagged Acquirer and stores
			the results in rawData with the acquirer's tag """

		logger.info("Acquiring to data '{0}' using Acquirer '{1}'".format(acquireTag, acquireTag))
		target = (self.rawData, acquireTag)
		self.acquire[acquireTag].performAsyncAcquire(target, *acquireArgs)

	def acquireAndBuildCorpus(self, acquireTag, minerTag, corpusTag, *acquireArgs):
		""" Acquire input and generate a corpus from it with a given miner in one step """

		self.performAcquire(acquireTag, *acquireArgs)
		self.buildCorpus(minerTag, corpusTag, acquireTag)

	def buildCorpus(self, minerTag, corpusTag, acquireTag):
		""" Generate a corpus from a given dataset using a given miner """

		t = current_thread().name
		
		with self.mine[minerTag].lock:
			if self.mine[minerTag].status != READY:
				logger.info("Building corpus '{}' from rawData '{}' using miner '{}'".format(corpusTag, acquireTag, minerTag))
				self.corpus[corpusTag] = self.mine[minerTag].buildCorpus(self.rawData[acquireTag])
			elif self.mine[minerTag].status == READY:
				logger.info("Corpus '{}' already exists; skipping.".format(corpusTag))

	def buildAsyncCorpus(self, minerTag, corpusTag, acquireTag):
		""" Generate a corpus from a given dataset using a given miner """

		logger.info("Building corpus '{0}' from rawData '{1}' using miner '{2}'".format(corpusTag, acquireTag, minerTag))
		target = (self.corpus, corpusTag)
		self.mine[minerTag].buildAsyncCorpus(target, self.rawData[acquireTag])
	
	def reprocess(self, minerTag, sourceCorpusTag, destCorpusTag):
		""" Run an existing corpus through a secondary DataMiner """

		t = current_thread().name

		with self.mine[minerTag].lock:
			if self.mine[minerTag].status != READY:
				logger.info("Reprocessing corpus '{}' to corpus '{}' using miner '{}'".format(sourceCorpusTag, destCorpusTag, minerTag))
				self.corpus[destCorpusTag] = self.mine[minerTag].buildCorpus(self.corpus[sourceCorpusTag])
			elif self.mine[minerTag].status == READY:
				logger.info("Corpus '{}' already exists; skipping.".format(destCorpusTag))


	def reportStatus(self):
		print len(self.acquire), "Acquirers registered:", self.listAcquirers()
		print len(self.mine), "Data Miners registered:", self.listMiners()
		print len(self.search), "Search Engines registered:", self.listSearch()
		print len(self.corpus), "corpuses registered:", self.corpus.keys()

	def getAcquireStatus(self, acquireTag):
		return self.acquire[acquireTag].checkStatus()

	def setAcquireStatus(self, acquireTag, status):
		self.acquire[acquireTag].setStatus(status)

	def getMinerStatus(self, minerTag):
		return self.mine[minerTag].checkStatus()
	
	def setMinerStatus(self, minerTag, status):
		self.mine[minerTag].setStatus(status)

	def resetTimeline(self, timeline):
		""" Walks backwards through a timeline's plugins until it finds
			one that is in WAIT, setting OUT_OF_DATE.
			Finally sets the timeline itself OUT_OF_DATE.
		"""
		
		# More than one data miner
		if type(timeline.miner) != list:
			timeline.miner = [timeline.miner]

		for miner in reversed(timeline.miner):
			if self.getMinerStatus(miner) == WAIT:
				break # stop if we find one in WAIT
			logger.info("Setting {} to OUT_OF_DATE...".format(miner))
			self.setMinerStatus(miner, OUT_OF_DATE)
		else:
			if self.getAcquireStatus(timeline.acquirer) != WAIT:
				self.setAcquireStatus(timeline.acquirer, OUT_OF_DATE)

		timeline.status = OUT_OF_DATE

	def generateTimeline(self, timeline, *acquireArgs):
		""" Given a timeline, takes the steps necessary to prepare that
			timeline for search, and updates its status as necessary.
		"""

		# TODO: Proper error handling.

		t = current_thread().name
		timeline.status = WAIT

		# result will hold ERROR only if this timeline triggered the error
		result = None

		# Ensure we always have a list of Acquirers
		if type(timeline.acquirer) != list:
			timeline.acquirer = [timeline.acquirer]

		acquireIndex = 0 # stores the index of the successful acquirer, if any

		# attempt each acquire in sequence and attempt to acquire using it
		for ac in timeline.acquirer:
			self.performAcquire(ac, *acquireArgs)

			if self.getAcquireStatus(ac) == READY:
				timeline.succesfulAcquirer = acquireIndex
				break # stop at first instance of successful acquire
			
			acquireIndex += 1
		else: # Log error state and do not proceed
			timeline.status = ERROR
			logger.error("No successful acquisition among acquirers {}".format(timeline.acquirer))
			return

		# Ensure we always have a list of DataMiners
		if type(timeline.miner) != list:
			timeline.miner = [timeline.miner]

		# perform initial mine
		result = self.buildCorpus(timeline.miner[0], timeline.corpus[0], timeline.acquirer[acquireIndex])

		# Did the prior mine complete successfully?
		if self.getMinerStatus(timeline.miner[0]) == ERROR:
			timeline.status = ERROR
			logger.error("Error in miner {}.".format(timeline.miner[0]))
			return

		# process remaining miner steps, if any
		for index in range(1, len(timeline.miner)):

			result = self.reprocess(timeline.miner[index], timeline.corpus[index-1], timeline.corpus[index])

			# check for errors
			if self.getMinerStatus(timeline.miner[index]) == ERROR:
				logger.error("Error in miner {}.".format(timeline.miner[index]))
				timeline.status = ERROR
				return

		logger.info("{} done.".format(timeline.prettyName))
		timeline.status = READY
