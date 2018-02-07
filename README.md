# Video indexing and search

This project seeks to provide an extensible, plugin-based means of extracting data from video files (either local or hosted on a service such as YouTube) and providing it in a searchable form to the user.

## Contents

* [Dependencies](#markdown-header-dependencies)
* [Pipeline](#markdown-header-pipeline)
  * [Storage](#markdown-header-storage)
  * [Calling](#markdown-header-calling)
* [Plugins](#markdown-header-plugins)
* [Plugin Interfaces](#markdown-header-plugin-interfaces)
  * [Acquirer](#markdown-header-acquirer)
  * [DataMiner](#markdown-header-dataminer)
  * [SearchEngine](#markdown-header-searchengine)
* [Building a Pipeline](#markdown-header-building-a-pipeline)
  * [Example 1](#markdown-header-example-1)
  * [Example 2](#markdown-header-example-2)

## Dependencies

`Pipeline` relies on `threading` for asynchronous plugin calls.

Several Dataminer plugins rely on `re`.

TrieSearch relies on `set`.

The web backend provided in `sample.py` relies on `json`, `sys`, `os`, `threading` and `flask`.

The speech recognition plugins rely on TODO: add speech recognition information

## Pipeline

The pipeline is populated with various plugins and provides a unified way to call and pass data between them:

### Storage
* Inside the pipeline:
    * `acquire{}` holds a dictionary of `Acquirer`s indexed by `acquireTag`
    * `mine{}` holds a dictionary of `DataMiner`s indexed by `minerTag`
    * `search{}` holds a dictionary of `SearchEngine`s indexed by `searchTag`

    * `rawData{}` holds the output of an `Acquirer`, indexed by `acquireTag`
    * `corpus{}` holds the output of a `DataMiner`, indexed by `corpusTag`
* Outside the pipeline:
    * The defined temp directory (default `'./tmp/'`) holds interstitial files.
    * The storage directory (default `'./store/'`) may hold saved corpuses at a future time.

Large corpuses should be cleared when no longer necessary, by calling `clearCorpus(corpusTag)`. Data stored in the temp directory can be periodically cleared using standard system tools.

### Calling

Examples of how to call pipeline methods and pass data are given in `pipelinetest.py` and `testAsync.py`, and in [Building a Pipeline](#markdown-header-building-a-pipeline).

## Plugins

Plugins should all inherit from one of the base classes, as follows:

* Acquirer
* DataMiner
* SearchEngine

They may also inherit from a subclass of one of those - a ReadFileWithCheese might inherit from a ReadFileAcquirer which inherits from Acquirer.

Asynchronous calling of plugins is all handled in the base classes - as long as `Acquirer`s implement the `acquire()` method and `DataMiner`s implement the `build()` method, they should behave equivalently regardless of whether they are called via `Pipeline.performAcquire()`/`Pipeline.buildCorpus()` or `Pipeline.performAsyncAquire()`/`Pipeline.buildAsyncCorpus()`.

Any setup specific to a given instance of a plugin should be done in the plugin's constructor; once allocated in the pipeline a plugin can only be replaced, not adjusted.

```Python
search = MySearch(someSetupArgs)
pipe.addSearch(search, 'mysearch')
pipe.performSearch('someCorpus', 'mysearch', ['term1', 'term2'])

search2 = MySearch(someOtherSetupArgs)
pipe.removeSearch('mysearch')
pipe.addSearch(search2, 'mysearch')
pipe.performSearch('someCorpus', 'mysearch', ['term3', 'term4'])
```

## Plugin interfaces

Each plugin has a common interface which specifies how the pipeline talks to it:

### Acquirer

```python
Acquirer.performAcquire(self, *args)
Acquirer.performAsyncAcquire(self, target, *args)
Acquirer.checkStatus(self)
Acquirer.acquire(self, *args)
```

`performAcquire()` exists in the base Acquirer class, and calls the `acquire()` method in the same thread.  This is the blocking version.

`performAsyncAcquire()` exists in the base Acquirer class, and calls the `acquire()` method in a new thread, to allow for non-blocking acquisition.  The `checkStatus()` method should be polled for completion of asynchronous acquisition. `target` holds a tuple consisting of a reference to the `rawData` dict, and the tag to be updated within that dict with the results.

`checkStatus()` exists in the base Acquirer class and returns the current status code of the plugin.

`acquire()` should be implemented in each class that inherits from `Acquirer` to allow for some kind of acquisition specific to that class; for instance the `PassThroughAcquirer` makes a copy of the supplied file in the `'./tmp/'` folder and returns the path of this new file.  It should return the data to be entered into the `rawData` dictionary and a return code (`0` is assumed if none is specified).

### DataMiner

```python
DataMiner.buildCorpus(self, data)
DataMiner.buildAsyncCorpus(self, data)
DataMiner.checkStatus(self)
DataMiner.build(self, data)
```

`buildCorpus()` exists in the base class and calls the `build()` method in the same thread.  This is the blocking version.

`buildAsyncCorpus()` exists in the base DataMiner class, and calls the `acquire()` method in a new thread, to allow for non-blocking acquisition. The `checkStatus()` method should be polled for completion of asynchronous acquisition.  `target` holds a tuple consisting of a reference to the `corpus` dict, and the tag to be updated within that dict with the results.

`checkStatus()` exists in the base DataMiner class and returns the current status code of the plugin.

`build()` should be implemented in each class that inherits from `DataMiner` to allow for some kind of corpus processing specific to that class, for instance the `SRTTrieMiner` processes a .srt file into a list of `SRTChunk`s and a `Trie` containing references to those chunks. It should return data to be entered into the `corpus` dictionary and a return code (`0` is assumed if none is specified).

### SearchEngine

```Python
SearchEngine.performSearch(self, corpus, terms)
```

`performSearch()` should be implemented in each class that inherits from `SearchEngine` to allow for some kind of search specific to that class, for instance the `TrieSearch` searches a `Trie` containing references to `SRTChunk`s for given terms and returns results.


## Building a pipeline

The underlying pieces of data that are through the pipeline via the `rawData` and `corpus` dictionaries are essentially arbitrary - all that is important is that the plugin producing the data and the plugin receiving the data agree on what that data should be. For instance:

### Example 1

 A `ReadFileAcquirer` tagged as 'readfile' reads the specified file and returns a list of individual lines, which is stored in `rawData` directly.
 A `ListSRTChunkMiner` tagged as 'srtchunk' expects to receive a list of lines, and builds a list of chunks and a dictionary mapping words to the chunks that contain those words.
 A `ReverseIndexSearch` tagged as 'risearch' expects to receive a dictionary mapping words to the chunks containing them, and produces search results:

* `ReadFileAcquirer.acquire('./somefile.srt')` __->__ `rawData['readfile']`
* `rawData['readfile']`__:__ `['line 1', 'line 2', 'line 3']`
* `rawData['readfile']` __->__ `ListSRTChunkMiner.build(rawData['readfile'])` __->__ `corpus['srtchunk']`
* `corpus['srtchunk']`__:__ `{'word1': [somechunk, somechunk, somechunk], 'word2': [somechunk, somechunk, somechunk]}`
* `corpus['srtchunk']` __->__ `ReverseIndexSearch(corpus['srtchunk'], ['term1', 'term2'])` __->__ `[result1, result2, result3]`

```python
pipeline.performAcquire('./somefile.srt', 'readfile')
>>> Acquiring to data 'readfile' using Acquirer 'readfile'
pipeline.buildCorpus('srtchunk', 'srtchunk', 'readfile')
>>> Building corpus 'srtchunk' from rawData 'readfile' using miner 'srtchunk'

pipeline.performSearch('srtchunk', 'risearch', ['term1', 'term2'])
>>> Performing search on corpus 'srtchunk' with engine 'risearch', terms '['term1', 'term2']'
```

### Example 2

 A `YoutubeAudioDownloader` tagged as 'ytaudio' downloads audio from a Youtube video and writes segments of a given length out to its specified temp directory, and returns a list of filenames for those segments, which is stored in `rawData`.
 A `VoiceSRTChunkMiner` tagged as 'voicerec' expects to receive a list of filenames; it reads each file in turn, runs speech recognition on it to build an SRTChunk, and adds these to a list.  It then generates a dictionary mapping words to the chunks that contain those words.
 An `SRTTrieMiner` tagged as 'triemine' expects to receive a dictionary mapping words to the chunks that contain those words, and builds a searchable trie from such a dictionary.
 A `TrieSearch` tagged as 'triesearch' expects to receive a trie mapping word stems to chunks containing those words, and produces search results.

* `YoutubeAudioDownloader.acquire('https://www.youtube.com/watch?v=SOMEID')` __->__ `rawData['ytaudio'], ./tmp/file1.mp3 ./tmp/file2.mp3 ...` 
* `rawData['ytaudio']`__:__ `['file1.mp3', 'file2.mp3', 'file3.mp3' ...]`
* `rawData['ytaudio']` __->__ `VoiceSRTChunkMiner.build(rawData['ytaudio']), ./tmp/file1.mp3 ./tmp/file2.mp3 ...` __->__ `corpus['srtchunk']`
* `corpus['srtchunk']`__:__ `{'word1': [somechunk, somechunk, somechunk], 'word2': [somechunk, somechunk, somechunk]}`
* `corpus['srtchunk']` __->__ `SRTTrieMiner.build(corpus['srtchunk'])` __->__ `corpus['triesearch']`
* `corpus['triesearch']` __->__ `TrieSearch(corpus['triesearch'], ['term1', 'term2'])` __->__ `[result1, result2, result3]`

```python
pipeline.performAcquire( 'ytaudio', 'https://www.youtube.com/watch?v=SOMEID')
>>> Acquiring to data 'ytaudio' using Acquirer 'ytaudio'
pipeline.buildCorpus('voicerec', 'srtchunk', 'ytaudio')
>>> Building corpus 'srtchunk' from rawData 'ytaudio' using miner 'voicerec'
pipeline.reprocess('triemine', 'srtchunk', 'triesearch')
>>> Reprocessing corpus 'srtchunk' to corpus 'triesearch' using miner 'triemine'

pipeline.performSearch('triesearch', 'triesearch', ['term1', 'term2'])
>>> Performing search on corpus 'trieminer' with engine 'triesearch', terms '['term1', 'term2']'
```


## Timelines

`Timeline`s provide a succint way of specifying functionality as one bundled end-to-end process.  It allows for the specification of a given timeline's user-friendly name, the timeline's `Acquirer` and `SearchEngine`, and any `DataMiner`s that are involved in producing searchable output.  The `Pipeline.generateTimeline()` method handles producing a corpus using a `Timeline` specification.

In this format, the timeline specified in [example 2](#markdown-header-example-2) might be written thus:

```python
ytAudioRec = Timeline()
ytAudioRec.prettyName = "Youtube Audio Speech Recognition" # user-friendly name
ytAudioRec.acquirer = 'ytaudio'
ytAudioRec.miner = ['voicerec', 'triemine'] # Data miners to apply, in order
ytAudioRec.corpus = ['srtchunk', 'triesearch'] # intermediary corpuses to use, in order
ytAudioRec.search = 'triesearch'

pipeline.generateTimeline(ytAudioRec, 'https://www.youtube.com/watch?v=SOMEID') # generate the corpus
>>> Acquiring to data 'ytaudio' using Acquirer 'ytaudio'
>>> Building corpus 'srtchunk' from rawData 'ytaudio' using miner 'voicerec'
>>> Reprocessing corpus 'srtchunk' to corpus 'triesearch' using miner 'triemine'
>>> Done.

pipeline.performSearch(ytAudioRec.search, ytAudioRec.corpus[-1], ['term1', 'term2'])
>>> Performing search on corpus 'trieminer' with engine 'triesearch', terms '['term1', 'term2']'
```

`Pipeline.generateTimeline()` can be called either synchronously or asynchronously by the application:

```python
from threading import Thread

pl = Pipeline()
# pipeline setup goes here...

tl = Timeline()
# timeline setup goes here...

# These calls are equivalent, except that the former blocks and the latter does not

pl.generateTimeline(tl, acquireArgs)
# ready

t = Thread(target=pl.generateTimeline, args=(tl, acquireArgs))
t.start()
while tl.status != 0:
  sleep(0.5)
# ready
```