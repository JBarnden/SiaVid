import json

from flask import Flask, request

from pipeline import Pipeline
from exampleplugins import SRTTrieMiner, TrieSearch, YoutubeSRTAcquirer

app = Flask(__name__)

pl = Pipeline()
timelines = []
url = ''

# Register route handlers for URLs...

@app.route("/setURL", methods=['POST'])
def setURL(timeline):
    url = request.form['uri']

@app.route("/getTimelines/")
def listMiners():
	return json.dumps(timelines)

@app.route("/getMiners/")
def listMiners():
	return json.dumps(pl.listMiners())

@app.route("/status/<miner>")
def checkReady(miner):
    if miner in pl.listMiners():
        pass
        #return status of miner
        #return json.dumps(pl.mine[miner].getStatus()
    else:
        #return some error we haven't worked out yet
        return json.dumps(False)

@app.route("/search/<search>", methods=['POST'])
def doSearch(search):
    if search in pl.listSearch():
        terms = request.form['searchterms'] # TODO: Sanitising of search terms
        results = pl.performSearch(search, terms)
        return json.dumps(results)
    else:
        #return some error we haven't worked out yet
        return json.dumps(False)

@app.route("add/<timeline>", methods=['GET'])
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

    # we pre-specify the timelines we want to offer...
    timelines.add('spokenword', 'objectsinscene', 'someothertimeline')

    # add our various pipeline components here
    pl.addAcquirer(YoutubeSRTAcquirer(), 'youtubesubs') # downloads subtitles from Youtube
    # pl.addAcquirer(YoutubeSegmentVideo(), 'segmentvideo') # downloads video from Youtube and segments it for speech recognition
    pl.addMiner(SRTTrieMiner(), 'subtitles') # Processes SRT into a trie
    pl.addSearch(TrieSearch(), 'triesearch')


    app.run(host='0.0.0.0')