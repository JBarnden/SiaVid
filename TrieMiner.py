"""
    SiaVid - A pluggable, customisable framework for indexing and searching data retrieved and generated from video.
    Copyright (C) 2018  Gareth Morgan, James Barnden, Antonios Plessas

    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with this program.  If not, see <http://www.gnu.org/licenses/>.
"""

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
