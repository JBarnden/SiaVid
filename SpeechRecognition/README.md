# Speech Recognition Wrapper

This module provides a wrapper class for testing Speech Recognition engines included in the SpeechRecognition library (although the focus has primarily been on `pocketsphinx`).  The module can automatically evaluate a series of test cases (audio files and corresponding transcripts) from a given directory, using a word error rate calculator.

## Contents

* [Dependencies](#markdown-header-dependencies)
* [SpeechRecognitionWrapper](#markdown-header-speechrecognitionwrapper-class)
    * [Speech to Text](#markdown-header-speech-to-text)
    * [Evaluating a Hypothesis](#markdown-header-evaluating-a-hypothesis)
    * [Running a Bulk Evaluation](#markdown-header-running-a-bulk-evaluation)
* [Logger](#markdown-header-Logger)

## Dependencies
`SpeechRecognitionWrapper` relies on `SpeechRecognition 3.8.1+` for speech to text functionality, `string` for loading subtitle files, `time` to measure execution time, and `numpy` for the word error rate calculator.

## SpeechRecognitionWrapper class
Inside the class:
    * `_r` - an instance of a `SpeechRecognition` `Recognizer` object.
    * `SL` - a list of supported language codes for `pocketsphinx`

### Speech to Text<a id="SpeechToText">
The `speech_to_text` function takes the path to an audio file, decodes the file, and attempts to recognize speech within the decoded audio using one or more SR engines.

By default, the recognition language is US english (en-US) which is currently the only supported language.  For information on extending the available languages, see: https://github.com/Uberi/speech_recognition/blob/master/reference/pocketsphinx.rst

Engines can be enabled or disabled with keyword arguments (see function docstring for full details).  By default, only pocketsphinx is enabled.

The function returns one or more hypotheses (transcriptions of the audio file by the chosen engine), depending on the number of enabled recognition engines.

Example usage:
```Python
    """
        Transcribing an audio file with the Speech Recognition Wrapper.
    """
    SR = SpeechRecognitionWrapper()
    
    audioPath = '/path/to/audio.wav'
    
    # Get a hypothesis string from the audioPath, setting the language tyo en-US
    hypothesis = SR.speech_to_text(audioPath,'en-US')
    
    # Print the hypothesis string
    print hypothesis
```

### Evaluating a Hypothesis
A hypothesis can be evaluated agains a given reference transcript with the `word_error_rate` function.  The reference transcript must be stripped of any punctuation and normalised before being used for evaluation.  The `load_subs` function converts a subtitles file (VSS or srt) into an appropriate format for evaluation.

The word error rate is the Levenshtein Distance between reference and hypothesis strings, divided by the number of words in the reference string.  The Levenshtein Distance is described as the shortest distance between two strings (the minimum of the insertions, deletions and substitutions).  By default, insertions, deletions and substitutions all have an associated cost of 1, although the cost of each can be ammended via kwargs (see function docstring). 

Example of generating a hypothesis and evaluating it:
```Python
    """
        Transcribing an audio file with the Speech Recognition Wrapper,
        retrieving, and displaying its word error rate
    """
    SR = SpeechRecognitionWrapper()
    
    audioPath = '/path/to/audio.wav'
    
    # Get a hypothesis string from the audioPath, setting the language tyo en-US
    hypothesis = SR.speech_to_text(audioPath,'en-US')
    
    pathToSubtitles = 'path/to/subtitles'
    
    # Load a subtitle file to be used as a reference transcript
    reference = SR.load_subs(pathToSubtitles)
    
    # Calculate the word error rate between the reference and the hypothesis, assigning a different deletion cost of 2.
    WER = SR.word_error_rate(reference, hypothesis, delCost=2)
    
    print "Word Error Rate: " + str(WER*100) + "%"
```


### Running a Bulk Evaluation
The `evaluate` function enables the automatic evaluation of an engine with multiple audio files and corresponding transcripts.  In order for this to work, the reference transcripts must be `.txt` files, whose names match their corresponding audio files (e.g. `my_audio.wav` `my_audio.txt`).  The reference transcripts and audio files should also be in the same directory.
The function returns a dictionary of `(audioFileName, WordErrorRate)` items.

Example bulk evaluation:
```Python
    testDataDir = "TestData/"
    print "Testing speech recognition with test data in directory '" + testDataDir + "'"
    
    # Get list of test cases (audio files and corresponding reference transcripts) from test data directory
    testCaseList = SR.buildTestCaseList(testDataDir)
    print "found " + str(len(testCaseList)) + " test cases."
    # Evaluate SR engine (with default configuration) on test cases
    results = SR.evaluate(testCaseList, testDataDir)
    
    print "Evaluation complete.\n\nResults:"
    for case, wer in results.iteritems():
        print "Case: " + case + "\nWord Error Rate: " + str(wer*100) + "%"
```

In the future, the bulk evaluation function will be extended to support the alteration of recognition engine parameters.

# Logger
The `Logger` class was included to save anything sent to stdout to a text file for later review, this is particularly useful for debugging purposes.

Using the logger:
```Python
    # Redirect stdout (python print) to the logger class, which sends outstream
    # to console and to a log file at the same time.
    sys.stdout = Logger("SRLog.log")
    
    print "This is sent to both the console and the log file"
```