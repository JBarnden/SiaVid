from trie import Trie, TrieNode
from chunker import SRTChunker
from sets import Set


class TrieMiner:
	def __init__(self, filename):
		chunker = SRTChunker(filename)
		self.trie = Trie()
		for word in chunker.words:
			if word != '':
				target = TrieNode()
				self.trie.addSubtree(word, target)
				target.content.append(chunker.words[word])

	def getTrie(self):
		return self.trie 



class TrieSearch:
	def __init__(self, corpus):
		self.corpus = corpus

	def walkTrie(self, node, results):
		""" Walk the trie rooted at 'node', appending results as we go """

		for item in node.content:
			for result in item:
				results.add(result)

		for child in node.children:
			self.walkTrie(node.children[child], results)


	def search(self, terms):
		""" For each search term, get the trie rooted at it add children to results  """

		results = Set()
		
		for term in terms:
			candidates = self.corpus.getSubtree(term)

			if candidates is None:
				continue

			root = candidates.getNode("")

			self.walkTrie(root, results)				
		
		return results	
