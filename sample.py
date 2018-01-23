import json

from flask import Flask, request, make_response

from pipeline import Pipeline
from exampleplugins import VSSTrieMiner, TrieSearch, PassThroughAcquirer, YoutubeSRTAcquirer

app = Flask(__name__)

class Timeline:
    def __init__(self):
        self.acquirer = None
        self.miner = None
        self.search = None
        self.prettyName = ""

pl = Pipeline()
timelines = {}
url = ''

# Register route handlers for URLs...

@app.route("/setURL", methods=['POST'])
def setURL(timeline):
    url = request.form['uri']

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
    resp = None
    
    if timeline in timelines:
        print "Timelines"
        resp = make_response(json.dumps('READY'))
        resp.headers['Access-Control-Allow-Origin'] = '*'
         
        #return status of miner
        #return json.dumps(pl.mine[miner].getStatus()
    else:
        #return some error we haven't worked out yet
        resp = make_response(json.dumps(False))
        resp.headers['Access-Control-Allow-Origin'] = '*'
    return resp

@app.route("/search/<search>", methods=['POST'])
def doSearch(search):
    print request.form['searchterms']

    resp = None

    if search in pl.listSearch():
        terms = request.form['searchterms'] # TODO: Sanitising of search terms
        terms = terms.split(" ")

        results = pl.performSearch(search, 'subtitles', terms)

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
    else:
        #return some error we haven't worked out yet
        resp = make_response(json.dumps(False))
        resp.headers['Access-Control-Allow-Origin'] = '*'
        return resp

@app.route("/add/<timeline>", methods=['GET'])
def doAcquire(timeline):
    """ Trigger acquisition and processing for a new timeline """

    if timeline == 'spokenword':

        # Only generate new corpus if we don't already have one
        if not pl.corpus.has_key('spokenword') or pl.corpus['spokenword'] == None:

            # start a thread to wait for download to be finished if necessary, and then process into a new corpus
            # TODO: Thread this

            # no subs?
            if not pl.rawData.has_key('youtubesubs', url):
                pl.performAcquire('youtubesubs') # attempt to download Youtube subtitles

                if pl.rawData['youtubesubs'] == None: # no subs on youtube?
                    
                    #if we haven't already downloaded the video, acquire it
                    if not pl.rawData.has_key('segmentvideo') or pl.rawData('segmentvideo') == None:
                        pl.performAcquire('segmentvideo') # download and segment video ready for speech recognition


                    pl.buildCorpus('speechrecognition', 'spokenword', 'segmentvideo')
                else:
                    pl.buildCorpus('')

    elif timeline == 'objectsinscene':
        # do stuff related to objects in scene
        pass
    elif timeline == 'someothertimeline':
        # do stuff related to some other timeline
        pass
    else:
        #return some error we haven't worked out yet
        return json.dumps(False)


# Initial setup stuff...

if __name__ == "__main__":

    # add our various pipeline components here
    pl.addAcquirer(PassThroughAcquirer(), 'pass') # downloads subtitles from Youtube
    pl.addMiner(VSSTrieMiner(), 'trieminer') # Processes SRT into a trie
    pl.addSearch(TrieSearch(), 'subtitles')

    pl.performAcquire('pass', 'paperclip.vtt')
    pl.buildCorpus('trieminer', 'subtitles', 'pass')

    results = pl.performSearch('subtitles', 'subtitles', ['guess'])
    for result in results:
        print "Converting result: {}->{} {}".format(result.startTime, result.endTime, result.getFullText())

    # we pre-specify the timelines we want to offer...
    timelines['subtitles'] = Timeline()
    timelines['subtitles'].prettyName = "Downloaded Subtitles"
    timelines['subtitles'].acquirer = 'pass'
    timelines['subtitles'].miner = 'trieminer'
    timelines['subtitles'].search = 'triesearch'
    
    # timelines['objectsinscene'] = Timeline()
    # timelines['objectsinscene'].prettyName = "Objects in Scene"
    # timelines['objectsinscene'].acquirer = 'youtubesubs'
    # timelines['objectsinscene'].miner = 'subtitles'
    # timelines['objectsinscene'].search = 'triesearch'
    
    # timelines['someothertimeline'] = Timeline()
    # timelines['someothertimeline'].prettyName = "Some other Timeline"
    # timelines['someothertimeline'].acquirer = 'youtubesubs'
    # timelines['someothertimeline'].miner = 'subtitles'
    # timelines['someothertimeline'].search = 'triesearch'


    app.run(host='0.0.0.0')