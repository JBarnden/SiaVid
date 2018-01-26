from pipeline import Pipeline, DataMiner, Acquirer
from time import sleep
import sys

from threading import Thread

class DelayAcquirer(Acquirer):
    """ Acquirer that sleeps for args[0] seconds and then
        stores args[1]
    """

    def acquire(self, *args):
        args = args[0]
        sleep(int(args[0]))
        return args[1]

class DelayMiner(DataMiner):
    """ Data miner that sleeps for args[0] seconds and then
        stores args[1]
    """

    def build(self, data):
        sleep(data[0])
        return data[1]

pipe = Pipeline()

pipe.addAcquirer(DelayAcquirer(), 'da')
pipe.addMiner(DelayMiner(), 'delay')

print "\n ########################## Using blocking versions in an external thread ##################\n"

t = Thread(target=pipe.acquireAndBuildCorpus, args=('da', 'delay', 'delay', [1, [2,"lalala"]], 0))
t.start()

while (not pipe.rawData.has_key('da') or pipe.acquire['da'].checkStatus() > 0) or (not pipe.corpus.has_key('delay') or pipe.mine['delay'].checkStatus() > 0):
    print "Waiting..."
    sleep(0.5)

print "rawData['da']:", pipe.rawData['da']
print "corpus['delay']:", pipe.corpus['delay']

print "\n ########################## Using asynchronous versions in internal threads ##################\n"

pipe.performAsyncAcquire('da', [1, [2,"lalala"]], 0)
#pipe.performAcquire('da', [1, [2,"lalala"]])

while pipe.acquire['da'].checkStatus() != 0:
    print "Waiting for acquire..."
    sleep(0.5)

print "rawData['da']:", pipe.rawData['da']

pipe.buildAsyncCorpus('delay', 'delay', 'da')
while pipe.mine['delay'].checkStatus() != 0:
    print "Waiting for mine..."
    sleep(0.5)

print "corpus['delay']:", pipe.corpus['delay']