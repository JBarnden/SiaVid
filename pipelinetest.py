from pipeline import *
from exampleplugins import *

if (True):

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

    pipe.reportStatus()

else:
    """
    # End-to-end, example calls:
    from exampleplugins import 

    pipe = Pipeline()

    filename = 'somefile'

    pipe.addAcquirer(AcquirerAdaptor(ReadFileAcquirer(filename)), 'readfile')
    pipe.addDataMiner(MinerAdaptor(ConvertToChunksMiner(), 'chunkify')
    pipe.addSearch(SearchAdaptor(FindChunkSearch()), 'chunkSearch')

    # use the readfile acquirer to read Inception.srt, process it into a search corpus with the chunkify data miner and store it in 'spokenword'.

    pipe.acquireAndBuildCorpus('readfile', 'chunkify', 'spokenword', 'Inception.srt')

    # Now we can search the spokenword corpus with the chunkSearch search engine and provided search terms...

    results = pipe.performSearch('spokenword', 'chunkSearch', "Hello")

    # And pass results out to our GUI or whatever.

    """
    pass