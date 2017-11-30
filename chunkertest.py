from chunker import SRTChunker, SRTChunk 

chunker = SRTChunker("Inception.srt")

for x in chunker.words["cobb"]:
	print x.startTime, x.endTime, x.content

#for x in chunker.words.keys():
#        print x

