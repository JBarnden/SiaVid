from pipeline import *
from exampleplugins import *

### Basic test

pipe = Pipeline()

print ""

print "### Register and test a data miner that just splits input on 'e':"
print ""

pipe.addMiner(SplitDataMiner(), 'test')

pipe.rawData['test'] = ["test"]
print pipe.rawData['test']

pipe.buildCorpus('test', 'test', 'test')
print pipe.corpus['test']
print ""

# Component management

print "### Add a ReadFileAcquirer and check for existence, test it provides correct data, delete and check for non-existence:"
print "" 

# Add a ReadFileAcquirer acquisition module
pipe.addAcquirer(ReadFileAcquirer(), 'test')
print "Current Acquirers:", pipe.listAcquirers()		# Confirm acquirer added correctly

# Acquire data, test it's been returned correctly
pipe.performAcquire('test', './testdata/Inception.srt')
print len(pipe.rawData['test'])
print "Line 208:", pipe.rawData['test'][208]

pipe.removeAcquirer("test")		# remove acquirer
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
pipe.addSearch(SearchInFirstLine(), "firstline")
print "Current Searches:", pipe.listSearch()

# Add a test corpus and search within it using the search method tagged 'firstline'
result = pipe.performSearch("Test", "firstline", "e")
print "Result:", result

pipe.reportStatus()

print "\n###################################################################\n"

### End-to-end, example calls:

pipe = Pipeline()

filename = 'somefile'

pipe.addAcquirer(PassThroughAcquirer(), 'readfile')
pipe.addMiner(SRTTrieMiner(), 'trie')
pipe.addSearch(TrieSearch(), 'triesearch')

# use the readfile acquirer to read Inception.srt, process it into a search corpus with the chunkify data miner and store it in 'spokenword'.

pipe.acquireAndBuildCorpus('readfile', 'trie', 'trie', './testdata/Inception.srt')

# can also be done as two steps:

#pipe.performAcquire('readfile', './testdata/Inception.srt')
#pipe.buildCorpus('trie', 'trie', 'readfile')

# Now we can search the trie corpus with the triesearch search engine and provided search terms...

results = pipe.performSearch('trie', 'triesearch', ['conglomerate'])

# And pass results out to our GUI or whatever.

for result in results:
    print result.startTime, ">", result.endTime, ":", result.content