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

Examples of how to call pipeline methods and pass data are given in `pipelinetest.py`.
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
* acquire(self, *args)

`performAcquire()` exists in the base Acquirer class, and calls the `acquire()` method in a new thread, to allow for non-blocking acquisition. (TODO: Thread not yet implemented, will need some thought about how to handle returns to Pipeline from it)

`acquire()` should be implemented in each class that inherits from Acquirer to allow for some kind of acquisition specific to that class; for instance the `PassThroughAcquirer` makes a copy of the supplied file in the './tmp/' folder and returns the path of this new file.

### DataMiner
* buildCorpus(self, data)
* build(self, data)

`buildCorpus()` exists in the base class and calls the `build()` method in a new thread, to allow for non-blocking acquisition. (TODO: Thread not yet implemented, will need some thought about how to handle returns to Pipeline from it)

`build()` should be implemented in each class that inherits from DataMiner to allow for some kind of corpus processing specific to that class, for instance the `SRTTrieMiner` processes a .srt file into a list of `SRTChunk`s and a trie containing references to those chunks.

### SearchEngine

* performSearch(self, corpus, terms)

`performSearch` should be implemented in each class that inherits from SearchEngine to allow for some kind of search specific to that class, for instance the `TrieSearch` searches a trie containing references to `SRTChunk`s for given terms and returns results.