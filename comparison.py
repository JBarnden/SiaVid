from exampleplugins import SRTChunkMiner, SRTTrieMiner, TrieSearch

from trie import Trie

chunker = SRTChunkMiner()
triem = SRTTrieMiner()
tries = TrieSearch()

words = chunker.build('./Inception.srt')

terms = ["cobb", "darling", "subconscious"]

trie = triem.build(words)
results = tries.search(trie, terms)

def printTrie(root, parent):
	print "Parent is", parent

	for node in root.children:
		print "Descending into", node
		printTrie(root.children[node], parent + node)
	print "backing out."


for term in terms:
	print "Trie rooted at ", term, " -"
	printTrie(trie.getSubtree(term).root, term)

print "\n#### Chunks:"

x = 0
for term in terms:
	x += len(words[term])

print x, "found."

x = 0
thing = {}
for term in terms:
	for word in words[term]:
		if word in thing:
			x += 1
			print "Duplicate: ", word, thing[word], word.content
		else:
			thing[word] = word
print x, "duplicate(s)."


print "\n#### Triesearch:"

print len(results), "found."

for result in results:
	diff = True

	for term in terms:
		for word in words[term]:
			if word == result:
				
				diff = False
				break
		if diff == False:
			break
	else:
		print "Not in ChunkSearch: ", result.content

print "\n##### items found by ChunkSearch but not TrieSearch:\n"
for term in terms:
	for word in words[term]:
		diff = True
		
		for result in results:
			if word == result:
				
				diff = False
				break
		if diff == False:
			break
	else:
		print "Not found: ", result.content
