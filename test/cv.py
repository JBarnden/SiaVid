from cvtest import FaceList, FaceChunk, FaceSearchMiner, FaceSearch
from pipeline import Pipeline

import pickle

filename = './FaceClusterer_output.p'
corpus = None

with open(filename, "r") as file:
    corpus = pickle.load(file)

#print corpus[0], corpus[1]
#print corpus[1].cluster

fs = FaceSearchMiner()

newCorpus, status = fs.build(corpus)

print newCorpus[0], newCorpus[1][0]

search = FaceSearch()

print "\n\n"
results = search.performSearch(newCorpus, ['0'])

print len(results), len(newCorpus[1][0])

for result in results:
    if result not in newCorpus[1][0]:
        print "Missing result in corpus 0"


print "\n\n"
results = search.performSearch(newCorpus, ['1'])
print len(results), len(newCorpus[1][1])
for result in results:
    if result not in newCorpus[1][1]:
        print "Missing result in corpus 1"

print "\n\n"
results = search.performSearch(newCorpus, ['2'])
print len(results), len(newCorpus[1][2])
for result in results:
    if result not in newCorpus[1][2]:
        print "Missing result in corpus 2"