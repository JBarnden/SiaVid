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

import json, sys
import os
from threading import Thread
from time import sleep

from flask import Flask, request, make_response, redirect

from pipeline import Pipeline, Timeline, statuses, READY, WAIT, OUT_OF_DATE, ERROR
from exampleplugins import VSSChunkMiner, TrieMiner, TrieSearch, ReadFileAcquirer, \
    AlwaysFailAcquirer, YoutubeAutoVSSAcquirer, FileToLineMiner, YoutubeAudioAcquirer, \
    SRTChunkListToRIDict, YoutubeVideoAcquirer
from SpeechRecogMiner import AudioSplitSpeechRecog
from faceRecognitionPlugins import VideoFaceFinder, FaceVectoriser, FaceClusterer, \
    FaceSearchMiner, FaceSearch

app = Flask(__name__, static_url_path='', static_folder=os.getcwd() + '/Frontend-Web')

pl = Pipeline()
timelines = {}
faceTimelines = []

# initial URL - changed by /setURL
url = "https://www.youtube.com/watch?v=wGkvyN6s9cY"

# Register route handlers for URLs...
@app.route("/")
def root():
    return redirect('/index.html')

@app.route("/setURL", methods=['POST'])
def setURL():
    """ Saves current data, updates the internal video URL and clears
        stored data
    """

    global url

    id = url.split("=")[1] # get youtube ID.

    for timeline in timelines:
        if timeline not in faceTimelines:
            print "Saving timeline {}".format(timeline)
            pl.saveCorpus(timelines[timeline].corpus[-1], id)

    url = request.form['uri']
    url = url.encode("ascii")

    pl.clearMemory()

    resp = make_response(json.dumps("URL updated"))
    resp.headers['Access-Control-Allow-Origin'] = '*'
    return resp

@app.route("/getTimelines/")
def getSearch():
    result = []
    timelineList = {}

    for name in timelines:
        timelineList[name] = timelines[name].prettyName

    result.append(timelineList)
    result.append(faceTimelines)

    resp = make_response(json.dumps(result))
    resp.headers['Access-Control-Allow-Origin'] = '*'
    return resp

@app.route("/status/<timeline>")
def checkReady(timeline):
    """ Returns a given timeline's status
    """

    status = None # default sentinel value
    
    if timeline in timelines:
        status = timelines[timeline].status

    # return the status
    resp = make_response(json.dumps(statuses[status]))
    resp.headers['Access-Control-Allow-Origin'] = '*'

    return resp

@app.route("/search/<timeline>", methods=['POST'])
def doSearch(timeline):
    """ Performs a search on a given timeline
    """

    convertedResults = None # Sentinel value

    if timeline in timelines:

        if timelines[timeline].status == READY:

            search = timelines[timeline].search
            corpus = timelines[timeline].corpus[-1]

            terms = request.form['searchterms'] # TODO: Sanitising of search terms
            terms = terms.encode("ascii").lower()
            terms = terms.strip()
            terms = terms.split(" ")

            results = pl.performSearch(corpus, search, terms)

            # Convert to serialisable format...
            if len(results) > 0:
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
    """ Trigger acquisition and processing for a new timeline, unless
        a previously saved corpus is available.
    """ 

    result = None

    if timeline in timelines:
        global url
        id = url.split("=")[1]

        result = timeline

        if timeline not in faceTimelines and pl.loadCorpus(timelines[timeline].corpus[-1], id):
            timelines[timeline].status = READY
        else:
            regenerate(timeline)

    resp = make_response(json.dumps(result))
    resp.headers['Access-Control-Allow-Origin'] = '*'
    return resp

@app.route("/regen/<timeline>", methods=['GET'])
def regen(timeline):
    """ Allows for explicit regeneration of a timeline
    """

    result = None

    if timeline in timelines:
        result = timeline
        regenerate(timeline)

    resp = make_response(json.dumps(result))
    resp.headers['Access-Control-Allow-Origin'] = '*'
    return resp   

def regenerate(timeline):
    """ Generates a corpus using the given timeline, in a separate thread
    """

    t = Thread(target=pl.generateTimeline, name = timeline, args=(timelines[timeline], url))
    t.start()

# Special-cased route for acquiring face information
@app.route("/getfaces/<timeline>", methods=['GET'])
def getFaces(timeline):
    faces = []
    if timeline in timelines:
        corpus = pl.getCorpus(timelines[timeline].corpus[-1])
        faces = corpus[0]

    resp = make_response(json.dumps(faces))
    resp.headers['Access-Control-Allow-Origin'] = '*'
    return resp       

# Initial setup...

if __name__ == "__main__":

    print ""

    # add our various pipeline components here
    pl.addAcquirer(YoutubeAudioAcquirer(), 'ytaudio') # downloads a video from youtube (.webm), and converts it to wav for speech recognition
    pl.addAcquirer(AlwaysFailAcquirer(), 'fail') # Sample acquirer that does nothing but fail
    pl.addAcquirer(YoutubeAutoVSSAcquirer(), 'ytautosub') # downloads an autogenerated VSS file from Youtube to temp folder
    pl.addAcquirer(YoutubeVideoAcquirer(), 'ytvid') # Downloads a video from youtube at the highest possible quality
    pl.addMiner(FileToLineMiner(), 'fileline') # processes a file into a list of lines
    pl.addMiner(VSSChunkMiner(), 'vssminer') # processes a list of lines in VSS format into a list of SRTChunks
    pl.addMiner(VSSChunkMiner(), 'vssminer2') # processes a list of lines in VSS format into a list of SRTChunks
    pl.addMiner(AudioSplitSpeechRecog(3, 1, 'en-US'), 'speechRecog') # processes a single audio file in wav format into a list of SRTChunks
    pl.addMiner(SRTChunkListToRIDict(), 'chunkToRIDict') # builds a reverse-indexed dict of word => list of chunks containing word
    pl.addMiner(VideoFaceFinder(), 'faceFinder') # Finds faces in the frames of a video and outputs them.
    pl.addMiner(FaceVectoriser(), 'faceVec') # Encodes images of faces as LBP vectors.
    pl.addMiner(FaceClusterer(n_clusters=None), 'faceClust') # Assigns faces/face vectors to clusters
    pl.addMiner(FaceSearchMiner(faceFolder='./Frontend-Web/faces/'), 'faceSearchMine') # Formats the output from the FaceClusterer to be searchable
    pl.addMiner(TrieMiner(), 'trieminer') # Processes list of SRTChunks into a trie
    pl.addMiner(TrieMiner(), 'trieminer2') # Processes list of SRTChunks into a trie
    pl.addMiner(TrieMiner(), 'trieminer3') # Processes list of SRTChunks into a trie
    pl.addMiner(TrieMiner(), 'trieminerSR') # Processes list of SRTChunks into a trie
    pl.addSearch(TrieSearch(), 'triesearch') # searches a trie
    pl.addSearch(FaceSearch(), 'faceSearch') # Searches faces by cluster id across a timeline


    print ""

    # we pre-specify the timelines we want to offer...

    # Test timelines

    timelines['subtitles'] = Timeline(
        "Auto Subtitles",                 # prettyName
        ['fail', 'ytautosub'],                                # acquireTag
        ['fileline', 'vssminer', 'trieminer'],  # minerTags in order
        ['fileline', 'vssminer', 'trieminer'],  # corpusTags in order
        'triesearch'                            # searchTag
    )
    
    timelines['speechRecog'] = Timeline(
        "Speech Recognition",                   # prettyName
        'ytaudio',                              # acqireTag
        ['speechRecog', 'chunkToRIDict', 'trieminerSR'],         # minerTag
        ['speechRecog', 'chunkToRIDict', 'trieminerSR'],         # corpusTag
        'triesearch'                            # searchTag
    )

    timelines['subtitles2'] = Timeline(
        "Duplicate auto subs",                 # prettyName
        'ytautosub',                                # acquireTag
        ['fileline', 'vssminer', 'trieminer'],  # minerTags in order
        ['fileline', 'vssminer', 'trieminer'],  # corpusTags in order
        'triesearch'                            # searchTag
    )

    timelines['fail'] = Timeline(
        "This timeline always fails to acquire", # prettyName
        'fail',                                # acquireTag
        ['fileline', 'vssminer', 'trieminer2'],  # minerTags in order
        ['fileline', 'vssminer', 'trieminer2'],  # corpusTags in order
        'triesearch'                            # searchTag
    )
    timelines['alttrieminer'] = Timeline(
        "Secondary Trieminer",                 # prettyName
        'ytautosub',                                # acquireTag
        ['fileline', 'vssminer2', 'trieminer2'],  # minerTags in order
        ['fileline', 'vssminer2', 'trieminer2'],  # corpusTags in order
        'triesearch'                            # searchTag
    )

    faceTimelines.append('facerecog')
    timelines['facerecog'] = Timeline()
    timelines['facerecog'].prettyName = "Facial recognition"
    timelines['facerecog'].acquirer = 'ytvid'
    timelines['facerecog'].miner = ['faceFinder', 'faceVec', 'faceClust', 'faceSearchMine']
    timelines['facerecog'].corpus = ['faceFinder', 'faceVec', 'faceClust', 'faceSearchMine']
    timelines['facerecog'].search = 'faceSearch'

    # Test timelines done

    # Examples of complete timelines with fallthrough

    timelines['spokenword'] = Timeline(
        "Spoken Word [NOT IMPLEMENTED]",

        # Attempts to find user-created subs, falls back to auto subs,
        # and if none exist, attempts speech recognition

        ['ytusersub', 'ytautosub', 'ytspeechrec'], # outputs a VSS file
                                                   # to ./tmp/

        # reads a VSS file into an array, processes it through VSSminer
        # and builds a searchable trie using trieminer

        ['swfileline', 'swvssminer', 'swtrieminer'], # outputs a trie
        ['swfileline', 'swvssminer', 'swtrieminer'],

        # returns list of segments containing a given word and words
        # rooted on it
        'swtriesearch'
    )

    timelines['speaker'] = Timeline(
        "Speaker [NOT IMPLEMENTED]",

        # Acquires source frames
        ['ytframeextractor'], # outputs a collection of frames or short
                              # clips in ./tmp/ rather than downloading
                              # whole video

        ['identifyfaces', 'classifyfaces'], # outputs a list of segments,
                                            # the faces that appear in 
                                            # them, and which appear
                                            # to be speaking

        # Alternative:
        # ['ytvideodownloader'], # downloads entire video, requires an
                                 # extra dataminer step for extracting
                                 # individual frames at a given rate

        # ['extractframes', identifyfaces', 'classifyfaces']

        # returns list of segments containing a given named speaker
        'facesearch'
    )


    app.run(host='0.0.0.0', use_reloader=True, threaded=True)
