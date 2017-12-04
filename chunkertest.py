from chunker import SRTChunker, SRTChunk 


print "\n", "### Load 'Inception.srt', mine it using the SRTChunker, and search the resulting corpus for given words:"

chunker = SRTChunker("Inception.srt")

testWords = ['thing', 'test', 'bigger']

print "Search terms:", testWords

for word in testWords:
	print "\nResults for '{0}':\n".format(word)

	for x in chunker.words[word]:
	
		print "-> Start: {0}; end: {1}; Content: {2}".format(x.startTime, x.endTime, x.content)

print "\n"
