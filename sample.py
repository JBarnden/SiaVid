import json, sys
from threading import Thread
from time import sleep

from flask import Flask, request, make_response

from pipeline import Pipeline
from exampleplugins import VSSChunkMiner, TrieMiner, TrieSearch, ReadFileAcquirer, YoutubeSRTAcquirer, FileToLineMiner

app = Flask(__name__)

class Timeline:
    def __init__(self):
        self.acquirer = None
        self.miner = None
        self.search = None
        self.prettyName = ""
        self.acquireArgs = ""

pl = Pipeline()
timelines = {}
url = "https://www.youtube.com/watch?v=wGkvyN6s9cY"

# Register route handlers for URLs...

@app.route("/setURL", methods=['POST'])
def setURL():
    global url
    url = request.form['uri']
    url = url.encode("ascii")
    resp = make_response(json.dumps("URL updated"))
    resp.headers['Access-Control-Allow-Origin'] = '*'
    return resp

@app.route("/getTimelines/")
def getSearch():
    result = {}

    for name in timelines:
        result[name] = timelines[name].prettyName

    resp = make_response(json.dumps(result))
    resp.headers['Access-Control-Allow-Origin'] = '*'
    return resp

@app.route("/status/<timeline>")
def checkReady(timeline):
    status = None # default sentinel value
    
    statuses = ["READY", "PENDING", "", "", "", "INIT"]

    if timeline in timelines:

        # get the name of the last miner on the timeline
        miner = timelines[timeline].miner
        if type(miner) == list:
            miner = miner[-1]
        
        # pull its status
        status = pl.mine[miner].checkStatus()

    # return the status
    resp = make_response(json.dumps(statuses[status]))
    resp.headers['Access-Control-Allow-Origin'] = '*'

    return resp

@app.route("/search/<timeline>", methods=['POST'])
def doSearch(timeline):

    convertedResults = False

    if timeline in timelines:
        search = timelines[timeline].search
        corpus = timelines[timeline].corpus[-1]

        terms = request.form['searchterms'] # TODO: Sanitising of search terms
        terms = terms.encode("ascii")
        terms = terms.split(" ")

        results = pl.performSearch(corpus, search, terms)

        # Convert to serialisable format...
        convertedResults = []
        for result in results:
            curr = {}
            curr['start'] = result.startTime
            curr['end'] = result.endTime
            convertedResults.append(curr)

    resp = make_response(json.dumps(convertedResults))
    resp.headers['Access-Control-Allow-Origin'] = '*'
    return resp

@app.route("/add/<timeline>", methods=['GET'])
def doAcquire(timeline):
    """ Trigger acquisition and processing for a new timeline """

    result = None

    if timeline in timelines:
        global url
        result = timeline

        t = Thread(target=generateTimeline, args=(timelines[timeline], url))
        t.start()

    resp = make_response(json.dumps(result))
    resp.headers['Access-Control-Allow-Origin'] = '*'
    return resp

def generateTimeline(timeline, *acquireArgs):

    if type(timeline.miner) == list:
        pl.acquireAndBuildCorpus(timeline.acquirer, timeline.miner[0], timeline.corpus[0], *acquireArgs)
        for index in range(1, len(timeline.miner)):
            pl.reprocess(timeline.miner[index], timeline.corpus[index-1], timeline.corpus[index])
    else:
        pl.acquireAndBuildCorpus(timeline.acquirer, timeline.miner, timeline.corpus, *acquireArgs)


# Initial setup stuff...

if __name__ == "__main__":

    # add our various pipeline components here
    pl.addAcquirer(YoutubeSRTAcquirer(), 'ytsub') # downloads an autogenerated VSS file from Youtube to temp folder
    pl.addMiner(FileToLineMiner(), 'fileline') # processes a file into a list of lines
    pl.addMiner(VSSChunkMiner(), 'vssminer') # processes a list of lines in VSS format into a list of SRTChunks
    pl.addMiner(TrieMiner(), 'trieminer') # Processes list of SRTChunks into a trie
    pl.addSearch(TrieSearch(), 'triesearch') # searches a trie

    # we pre-specify the timelines we want to offer...

    timelines['subtitles'] = Timeline()
    timelines['subtitles'].prettyName = "Downloaded Subtitles"
    timelines['subtitles'].acquirer = 'ytsub'
    timelines['subtitles'].miner = ['fileline', 'vssminer', 'trieminer']
    timelines['subtitles'].corpus = ['fileline', 'vssminer', 'trieminer']
    timelines['subtitles'].search = 'triesearch'

    # timelines['speechrec'] = Timeline()
    # timelines['speechrec'].prettyName = "Speech Recognition"
    # timelines['speechrec'].acquirer = 'ytaudiochunker'
    # timelines['speechrec'].miner = ['speechrec', 'trieminer']
    # timelines['speechrec'].corpus = ['speechrec', 'trieminer']
    # timelines['subtitles'].search = 'triesearch'


    app.run(host='0.0.0.0')
