# experimental

## Pipeline

The pipeline is populated with various plugins and provides a unified way to call and pass data between them:

### Storage
* `acquire{}` holds a dictionary of `Acquirer`s indexed by `acquireTag`
* `mine{}` holds a dictionary of `DataMiner`s indexed by `minerTag`
* `search{}` holds a dictionary of `SearchEngine`s indexed by `searchTag`

* `rawData` holds the output of an `Acquirer`, indexed by `acquireTag`
* `corpus` holds the output of a `DataMiner`, indexed by `corpusTag`


### Calling

Examples of how to call pipeline methods and pass data are given in `pipelinetest.py` and `testAsync.py`.
(TODO: Expand this.)

## Plugins

Plugins should all inherit from one of the base classes, as follows:

* Acquirer
* DataMiner
* SearchEngine

They may also inherit from a subclass of one of those - a ReadFileWithCheese might inherit from a ReadFileAcquirer which inherits from Acquirer.

Any setup specific to that given instance should be done in the constructor; once they are allocated in the pipeline they can only be replaced, not adjusted.

```Python
search = MySearch(someSetupArgs)
pipe.addSearch(search, 'mysearch')
pipe.performSearch('someCorpus', 'mysearch', ['term1', 'term2'])

search2 = MySearch(someOtherSetupArgs)
pipe.removeSearch('mysearch')
pipe.addSearch(search, 'mysearch')
pipe.performSearch('someCorpus', 'mysearch', ['term3', 'term4'])
```

## Plugin interfaces

Each plugin has a common interface which specifies how it the pipeline talks to it:

### Acquirer
* performAcquire(self, *args)
* performAsyncAcquire(self, *args)
* checkStatus()
* acquire(self, *args)

`performAcquire()` exists in the base Acquirer class, and calls the `acquire()` method in the same thread.  This is the blocking version.

`performAsyncAcquire()` exists in the base Acquirer class, and calls the `acquire()` method in a new thread, to allow for non-blocking acquisition.  The `checkStatus()` method should be polled for completion of asynchronous acquisition.

`checkStatus()` exists in the base Acquirer class and returns the current status code of the plugin.

`acquire()` should be implemented in each class that inherits from Acquirer to allow for some kind of acquisition specific to that class; for instance the `PassThroughAcquirer` makes a copy of the supplied file in the './tmp/' folder and returns the path of this new file.  It should return data to be entered into the `rawData` dictionary and a return code (`0` is assumed if none is specified).

### DataMiner
* buildCorpus(self, data)
* buildAsyncCorpus(self, data)
* checkStatus()
* build(self, data)

`buildCorpus()` exists in the base class and calls the `build()` method in the same thread.  This is the blocking version.

`buildAsyncCorpus()` exists in the base DataMiner class, and calls the `acquire()` method in a new thread, to allow for non-blocking acquisition. The `checkStatus()` method should be polled for completion of asynchronous acquisition.

`checkStatus()` exists in the base DataMiner class and returns the current status code of the plugin.

`build()` should be implemented in each class that inherits from DataMiner to allow for some kind of corpus processing specific to that class, for instance the `SRTTrieMiner` processes a .srt file into a list of `SRTChunk`s and a trie containing references to those chunks. It should return data to be entered into the `corpus` dictionary and a return code (`0` is assumed if none is specified).

### SearchEngine

* performSearch(self, corpus, terms)

`performSearch` should be implemented in each class that inherits from SearchEngine to allow for some kind of search specific to that class, for instance the `TrieSearch` searches a trie containing references to `SRTChunk`s for given terms and returns results.


## Building a pipeline

The underlying pieces of data that are through the pipeline via the `rawData` and `corpus` dictionaries are essentially arbitrary - all that is important is that the plugin producing the data and the plugin receiving the data agree on what that data should be. For instance:

* A `ReadFileAcquirer` tagged as 'readfile' reads the specified file and returns a list of individual lines, which is stored in `rawData` directly.  A `ListSRTChunkMiner` tagged as 'srtchunk' expects to receive a list of lines, and builds a list of chunks and a dictionary mapping words to the chunks that contain those words. A `ReverseIndexSearch` tagged as 'risearch' expects to receive a dictionary mapping words to the chunks containing them, and produces search results:

    * ReadFileAcquirer.acquire('./somefile.srt') __->__ rawData['readfile']
    * rawData['readfile']: ['line 1', 'line 2', 'line 3']
    * rawData['readfile'] __->__ ListSRTChunkMiner.build(rawData['readfile']) __->__ corpus['srtchunk']
    * corpus['srtchunk']: {'word1': [somechunk, somechunk, somechunk], 'word2': [somechunk, somechunk, somechunk]}
    * corpus['srtchunk'] __->__ ReverseIndexSearch(corpus['srtchunk'], ['term1', 'term2']) __->__ [result1, result2, result3]

    ```
    pipeline.performAcquire('./somefile.srt', 'readfile')
    pipeline.buildCorpus('srtchunk', 'srtchunk', 'readfile')
    pipeline.performSearch('srtchunk', 'risearch', ['term1', 'term2'])
    ```

* A `YoutubeAudioDownloader` tagged as 'ytaudio' downloads audio from a Youtube video and writes segments of a given length out to its specified temp directory, and returns a list of filenames for those segments, which is stored in `rawData`. A `VoiceSRTChunkMiner` tagged as 'voicerec' expects to receive a list of filenames; it reads each file in turn, runs speech recognition on it to build an SRTChunk, and adds these to a list.  It then generates a dictionary mapping words to the chunks that contain those words. An `SRTTrieMiner` tagged as 'triemine' expects to receive a dictionary mapping words to the chunks that contain those words, and builds a searchable trie from such a dictionary.  A `TrieSearch` tagged as 'triesearch' expects to receive a trie mapping word stems to chunks containing those words, and produces search results.

    * YoutubeAudioDownloader.acquire('https://www.youtube.com/watch?v=JIGUHqV-aH8') __->__ rawData['ytaudio'], ./tmp/file1.mp3 ./tmp/file2.mp3 ... 
    * rawData['ytaudio']: ['file1.mp3', 'file2.mp3', 'file3.mp3' ...]
    * rawData['ytaudio'] __->__ VoiceSRTChunkMiner.build(rawData['ytaudio']), ./tmp/file1.mp3 ./tmp/file2.mp3 ... __->__ corpus['srtchunk']
    * corpus['srtchunk']: {'word1': [somechunk, somechunk, somechunk], 'word2': [somechunk, somechunk, somechunk]}
    * corpus['srtchunk'] __->__ SRTTrieMiner.build(corpus['srtchunk']) __->__ corpus['triesearch']
    * corpus['triesearch'] __->__ TrieSearch(corpus['triesearch'], ['term1', 'term2']) __->__ [result1, result2, result3]

    ```
    pipeline.performAcquire('https://www.youtube.com/watch?v=JIGUHqV-aH8', 'ytaudio')
    pipeline.buildCorpus('voicerec', 'srtchunk', 'ytaudio')
    pipeline.reprocess('triemine', 'srtchunk', 'triesearch')
    pipeline.performSearch('triesearch', 'triesearch', ['term1', 'term2'])
    ```