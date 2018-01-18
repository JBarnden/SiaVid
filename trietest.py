#!/usr/bin/python

from trie import Trie, TrieNode
from TrieMiner import TrieMiner, TrieSearch


miner = TrieMiner("Inception.srt")

trie = miner.getTrie()

searches = ['mea', 'fac', 'hel']

print "#### Searching for {}".format(searches) 

ts = TrieSearch(trie)

for result in ts.search(searches):
	
                print "-> Start: {0}; end: {1}; Content: {2}".format(result.startTime, result.endTime, result.content)

