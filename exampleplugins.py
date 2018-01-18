from pipeline import DataMiner, SearchEngine, Acquirer

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
