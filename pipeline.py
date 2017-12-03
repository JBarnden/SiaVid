from chunker import SRTChunk, SRTChunker


class Acquirer:
	""" Basic definition for data acquisition class """

	def acquire(self, *args):
		""" 	Do something to acquire data. 
			This can e.g return text data directly
			or write extracted frames out to files
			and return list of resulting filenames
			etc. """
		pass

class AcquirerAdapter:
	""" Holds an Acquirer and mediates requests to it """

	def __init__(self, acquirer):
		self.acquirer = acquirer

	def acquire(self, *args):
		return self.acquirer.acquire(*args)

class ReadFileAcquirer(Acquirer):
	""" Example Acquirer that reads from a given filename into a list """

	def __init__(self, filename):
		self.filename = filename

	def acquire(self):
		lines = []

		with open(self.filename, "r") as file:
			lines = file.readlines()

		return lines

class SearchEngine:
	""" Basic definition for SearchEngine class """

	def performSearch(self, corpus, terms):
		"""	Do something to extract results from corpus
			based on terms. Any method is appropriate """
			
		results = []

		results.append("") # Search method here

		return results

class SearchAdapter:
	""" Holds a SearchEngine and mediates requests to it """

	def __init__(self, engine):
		self.engine = engine

	def performSearch(self, corpus, terms):
		return self.engine.performSearch(corpus, terms)

class SearchInFirstLine(SearchEngine):
	""" Example SearchEngine that finds the first instance of a given
		substring in the first element of the corpus provided """

	def performSearch(self, corpus, terms):
		""" Simple example search: Finds substring 'terms' in first
			line of corpus """

		result = [] # holds search results

		result.append(corpus[0].find(terms))

		return result

class DataMiner:
	""" Basic definition for DataMiner class """

	def provideRawData(self, someData):
		self.data = someData;
		pass

	def buildCorpus(self, data):
		corpus = [] # Holds processed data
		
		corpus.append(data) # Processing here

		return corpus

class DataMinerAdapter:
	""" Holds a DataMiner and mediates requests to it """

	def __init__(self, dataMiner):
		self.miner = dataMiner
 
	def buildCorpus(self, data):
		return self.miner.buildCorpus(data)


class SplitDataMiner(DataMiner):
	""" Example DataMiner that splits raw input data at occurences
		of 'e' """

	def buildCorpus(self, data):
		results = []
		for item in data:
			halves = item.split('e')
			results.append(halves[0])
			results.append(halves[1])
		return results

class Pipeline:
	def __init__(self):
		self.acquire = {}
		self.mine = {}
		self.search = {}

		self.corpus = {}

	def listAcquirers(self):
		""" Returns list of currently registered acquirers """

		return self.acquire.keys()

	def addAcquire(self, acquirer, tag):
		""" Add a new acquirer tagged 'tag' """

		print "Adding acquirer '{0}'.".format(tag)
		self.acquire[tag] = acquirer

	def removeAcquire(self, tag):
		""" Remove the acquirer tagged 'tag' """

		if self.acquire.has_key(tag):
			print "Deleting acquirer '{0}'.".format(tag)			
			del self.acquire[tag]
		else:
			print "No acquirer '{0}'.".format(tag)

	def listMiners(self):
		""" Returns list of currently registered data miners """

		return self.mine.keys()

	def addMiner(self, miner, tag):
		""" Add a new data miner tagged 'tag' """

		print "Adding miner '{0}'.".format(tag)
		self.mine[tag] = miner

	def removeMiner(self, tag):
		""" Remove the data miner tagged 'tag' """

		if self.mine.has_key(tag):
			print "Deleting miner '{0}'.".format(tag)			
			del self.acquire[tag]
		else:
			print "No miner '{0}'.".format(tag)

	def listSearch(self):
		""" Returns list of currently registered search engines """

		return self.search.keys()


	def addSearch(self, search, tag):
		""" Add a new search engine tagged 'tag' """

		print "Adding search '{0}'.".format(tag)
		self.search[tag] = search

	def removeSearch(self, tag):
		""" Remove the search engine tagged 'tag' """

		if self.search.has_key(tag):
			print "Deleting search '{0}'.".format(tag)			
			del self.search[tag]
		else:
			print "No search '{0}'.".format(tag)

	def performSearch(self, corpusTag, searchTag, searchTerms):
		""" Perform a search on a given corpus with a given search engine, using searchterms
			Returns a list of results """

		print "Performing search on corpus '{0}' with engine '{1}', terms '{2}'".format(corpusTag, searchTag, searchTerms)

		if not self.search.has_key(searchTag):
			print "No search '{0}' available.".format(searchTag)
			return

		if not self.corpus.has_key(corpusTag):
			print "No corpus '{0}' available.".format(corpusTag)
			return

		return self.search[searchTag].performSearch(self.corpus[corpusTag], searchTerms)

	def acquireAndBuildCorpus(self, acquireTag, minerTag, corpusTag, *acquireArgs):
		""" Acquire input and generate a corpus from it with a given miner in one step """

		print acquireArgs
		buildCorpus(corpusTag, minerTag, acquire[acquireTag].acquire(*acquireArgs))

	def buildCorpus(self, minerTag, corpusTag, data):

		""" Generate a corpus from a given dataset using a given miner """
		self.corpus[corpusTag] = self.mine[minerTag].buildCorpus(data)
		


### testing ###

pipe = Pipeline()

print ""


print "### Register and test a data miner that just splits input on 'e':"
print ""


pipe.addMiner(DataMinerAdapter(SplitDataMiner()), 'test')

pipe.buildCorpus('test', 'test', ["test"])
print pipe.corpus['test']
print ""


# Component management

print "### Add a ReadFileAcquirer and check for existence,, test it provides correct data, delete and check for non-existence:"
print ""


# Add a ReadFileAcquirer acquisition module
pipe.addAcquire(AcquirerAdapter(ReadFileAcquirer("Inception.srt")), "test")

print "Current Acquirers:", pipe.listAcquirers()		# Confirm acquirer added correctly

# Acquire data, test it's been returned correctly
print "Line 208:", pipe.acquire["test"].acquire()[208]

pipe.removeAcquire("test")		# remove acquirer
print "Current Acquirers:", pipe.listAcquirers()		# Confirm acquirer removed correctly

print ""


# Testing searching with a given corpus, Search and terms

print "### Add a Test corpus, Attempt to use a non-existent SearchEngine to search it, then add a FirstLineSearch, enumerate to check existence, and use that instead."
print ""


print "adding 'Test' corpus"
pipe.corpus['Test'] = ["This is a first line"]


# Searching with missing chunks:
pipe.performSearch("Test", "thing", "e")

# add a search method
pipe.addSearch(SearchAdapter(SearchInFirstLine()), "firstline")
print "Current Searches:", pipe.listSearch()

# Add a test corpus and search within it using the search method tagged 'firstline'
result = pipe.performSearch("Test", "firstline", "e")
print "Result:", result



# End-to-end, example calls:

"""

pipe = Pipeline()

filename = 'somefile'

pipe.addAcquirer(AcquirerAdaptor(ReadFileAcquirer(filename)), 'readfile')
pipe.addDataMiner(MinerAdaptor(ConvertToChunksMiner(), 'chunkify')
pipe.addSearch(SearchAdaptor(FindChunkSearch(), 'chunkSearch')

# use the readfile acquirer to read Inception.srt, process it into a search corpus with the chunkify data miner and store it in 'spokenword'.

pipe.acquireAndBuildCorpus('readfile', 'chunkify', 'spokenword', 'Inception.srt')

# Now we can search the spokenword corpus with the chunkSearch search engine and provided search terms...

results = pipe.performSearch('spokenword', 'chunkSearch', "Hello")

# And pass results out to our GUI or whatever.


"""
