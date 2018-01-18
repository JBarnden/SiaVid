#!/usr/bin/python

class TrieNode:
	def __init__(self):
		self.content = []
		self.children = {}

	def addChild(self, index, node):
		""" Adds the given node as a child of this one """
		
		if not self.children.has_key(index):
			self.children[index] = node

	def removeChild(self, index):
		if self.children.has_key(index):
			self.children.pop(index)

class Trie:
	def __init__(self, root = None):
		if root is None:
			self.root = TrieNode()
		else:
			self.root = root

	def removeSubtree(self, target):
		""" Removes a subtree rooted at node 'target' """
		result = self.getNode(target[:-1])
		result.children.pop(target[-1:]) 
		
	def addMissingNodes(self, missing, rootNode):
		for index in missing:
			rootNode.addChild(index, TrieNode())
			rootNode = rootNode.children[index]
		return rootNode

	def addSubtree(self, target, rootNode):
		""" Inserts another trie into the specified location in this one """

		missingNodes = 0

		result = self.getNode(target[:-1])

		# construct missing nodes if necessary
		while result is None:
			missingNodes += 1
			result = self.getNode(target[:-1-missingNodes])

		if missingNodes > 0:
			result = self.addMissingNodes(target[-1-missingNodes:-1], result)

		if result is not None:
			result.addChild(target[-1:], rootNode)
		
		

	def getSubtree(self, target):
		""" Returns new trie rooted at node 'target', or None if not found """
		
		result = self.getNode(target)

		if result is None:
			return result
		else:
			return Trie(result)
 
	def getNode(self, target):
		""" Returns a reference to the node 'target' or None if not found """

		result = self.root

		address = ""

		for step in target:
			address = address + step
			if (result.children.has_key(step)):
				result = result.children[step]
			else:
				result = None
				break
		return result
		
