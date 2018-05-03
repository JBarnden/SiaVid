"""
	Dependencies:
	- SpeechRecognition 3.8.1+ (pip install SpeechRecognition)
	- PocketSphinx
	
"""
import speech_recognition as sr
import sys
from time import gmtime, strftime

class Logger(object):
    """
        Logger can be used to direct anything sent to the output stream (print)
        to both the console and a given log file.
    """
    def __init__(self, logFile):
        self.console = sys.stdout
        # Open log file for appending.
        self.log = open(logFile, "a")

    def write(self, message):
        self.console.write(message)
        self.log.write(message)


class SpeechRecognitionWrapper(object):
    """
        A wrapper class for the 'SpeechRecognition' library,
        created to make testing and optimising SR engines easier.

        Includes a method to format SRT files to be used as reference
        transcripts, and a Word-Error-Rate calculator to evaluate performance.
    """

    def __init__(self):
        """
            Initializes Recognizer instance and list of supported recognition
            language tags.
        """
        # Create instance of recognizer object accessible
        # to all class methods
        self._r = sr.Recognizer()

        # List of supported language codes (for Sphinx)
        self.SL = ['en-US']

    def read_audio_data(self, audioFilePath, **kwargs):
        # "values below energy threshold are considered silence, 
        # values above the threshold are considered speech"
        #     - https://github.com/Uberi/speech_recognition/blob/master/reference/library-reference.rst#recognizer_instanceenergy_threshold--300
        """
        This function is used by the speech_to_text method to convert a
        sound file to suitable input for an SR engine.

        :param kwargs:
            startTime - where to start recording from, default is None
            (read from start).

            recordDuration - how long to record for, default is None
            (read until end of stream)

            energyThreshold - Values below the energy threshold are considered
            as silence, values above considered as speech.  If energy-threshold
            is -1 (default), the dynamic energy threshold will be used.
            (see https://github.com/Uberi/speech_recognition/blob/master/reference/library-reference.rst#recognizer_instanceenergy_threshold--300)

        :return: Audio data instance (input to SR engines)
        """
        kwargs.setdefault('startTime', None)
        kwargs.setdefault('recordDuration', None)
        kwargs.setdefault('energyThreshold', -1)

        if kwargs['energyThreshold'] > -1:
            self._r.energy_threshold = kwargs['energyThreshold']
        else:
            # recognizer will automatically adjust energy threshold based on
            # "the currently ambient noise level while listening"
            #    - https://github.com/Uberi/speech_recognition/blob/master/reference/library-reference.rst#recognizer_instancedynamic_energy_threshold--true
            self._r.dynamic_energy_threshold = True

        # Open audio file for reading, storing it as an AudioFile instance
        # called "source".
        try:
            with sr.AudioFile(audioFilePath) as source:
                # "Record" audio from source, returns "AudioData" instance
                #    - https://github.com/Uberi/speech_recognition/blob/master/reference/library-reference.rst#recognizer_instancerecordsource-duration--none-offset--none
                return self._r.record(source, kwargs['recordDuration'], kwargs['startTime'])
        except (RuntimeError, TypeError, IOError):
            print "SR Wrapper: failed to read audio data"
            return None

    # Currently outputs text
    def speech_to_text(self, audioFilePath, language='en-US', **kwargs):
        """
            Takes the path to an audio file, decodes it, and attempts to 
            recognize speech within the decoded audio using one or more SR 
            engines.

        :param audioFilePath: Path to the audio file containing speech.
        :param language: The RFC5646 language tag corresponding to the
        recognition language to use. (default: en-US)
        :param kwargs:
            energy-threshold (int) - Values below the energy threshold are
            considered as silence, values above considered as speech.
            If energy-threshold is -1 (default), the dynamic energy threshold
            will be used.
            (see https://github.com/Uberi/speech_recognition/blob/master/reference/library-reference.rst#recognizer_instanceenergy_threshold--300)

            Different engines can be enabled/disabled like so:
                - sphinx=True/False (True by default)
                - gsr=True/False (False by default)
                - wit=True/False (False by default)

            Verbose output can also be toggled with:
                - verbose=True/False (False by default)
                If false, function just returns the best possible prediction.
                If true, function returns a more detailed output.  E.g. for
                sphinx, verbose output would return a pocketsphinx.Decoder
                object with scores and confidence values for the generated
                hypothesis and its segments.
        :return: One or more hypotheses
        (based on the number of enabled speech recognition engines)
        """

        kwargs.setdefault("energyThreshold", -1)
        kwargs.setdefault("sphinx", True)
        kwargs.setdefault("gsr", False)
        kwargs.setdefault("wit", False)
        kwargs.setdefault("verbose", False)

        recognizer = self._r
        # Function returns a list of hypotheses if multiple engines are enabled through kwargs.
        output = []

        # Function returns a list of hypotheses if multiple engines are enabled through kwargs.
        output = []

        if kwargs["energyThreshold"] > -1:
            recognizer.energy_threshold = kwargs["energyThreshold"]
        else:
            # recognizer will automatically adjust energy threshold based on
            # "the currently ambient noise level while listening"
            #    - https://github.com/Uberi/speech_recognition/blob/master/reference/library-reference.rst#recognizer_instancedynamic_energy_threshold--true
            recognizer.dynamic_energy_threshold = True

        # Open audio file for reading, storing it as an AudioFile instance
        # called "source".
        with sr.AudioFile(audioFilePath) as source:
            # "Record" audio from source, returns "AudioData" instance
            # https://github.com/Uberi/speech_recognition/blob/master/reference/library-reference.rst#recognizer_instancerecordsource-duration--none-offset--none
            audio = recognizer.record(source)

            sphinxText = None
            witAIText = None
            googleSRText = None

            # Following inspired by:
            # https://github.com/Uberi/speech_recognition/blob/master/examples/audio_transcribe.py
            # The rest of the API's require credentials or an API key

            # recognize speech using Sphinx
            if kwargs['sphinx']:
                try:
                    sphinxText = recognizer.recognize_sphinx(audio, language=language, show_all=kwargs["verbose"])
                    output.append(sphinxText)
                except sr.UnknownValueError:
                    print("Sphinx could not understand audio")
                except sr.RequestError as e:
                    print("Sphinx error; {0}".format(e))


            # recognize speech using Google Speech Recognition
            if kwargs['gsr']:
                try:
                    # for testing purposes, we're just using the default API key
                    # to use another API key, use `r.recognize_google(audio, key="GOOGLE_SPEECH_RECOGNITION_API_KEY")`
                    # instead of `r.recognize_google(audio)`
                    googleSRText = recognizer.recognize_google(audio)
                    output.append(googleSRText)
                except sr.UnknownValueError:
                    print("Google Speech Recognition could not understand audio")
                except sr.RequestError as e:
                    print("Could not request results from Google Speech Recognition service; {0}".format(e))

            # WIT IS NOT APPROPRIATE FOR THIS APPLICATION
            #  Wit requries a priori knowledge of what may be said to the application, which can only be specified
            #  via the web interface and not the API.
            # recognize with Wit.ai (requires API key)
            if kwargs['wit']:
                WIT_AI_KEY = "B2OIDI2UARU7WVW4UQRA4GQWK2HNPQEV"

                try:
                    witAIText = recognizer.recognize_wit(audio, key=WIT_AI_KEY)
                    output.append(witAIText)
                except sr.UnknownValueError:
                    print("Wit.ai Speech Recognition could not understand audio")
                except sr.RequestError as e:
                    print("Could not request results from Wit.ai Speech Recognition service; {0}".format(e))

            if len(output) == 1:
                return output[0]
            else:
                return output

    # Function returns true if the given language tag is supported.
    def language_supported(self, language):
        if language in self.SL:
            return True
        else:
            return False

    def word_error_rate(self, reference, hypothesis, **kwargs):
        """
        Calculates and returns the word error rate between given hypothesis and
        reference strings.  Different costs for insertions, deletions and
        substitutions can be applied via keyword arguments.

        The word error rate is the Levenshtein Distance between reference and
        hypothesis strings, divided by the number of words in the reference
        string.
        
        Refs:
            http://www.python-course.eu/levenshtein_distance.php
            https://martin-thoma.com/word-error-rate-calculation/

        The transcript normalization process could do with refining to improve
        formatting consistency, for example one transcript might use digits for
        numbers while another might have numbers as words, consistent formatting
        could be ensured by catching text and converting it to digits or
        vis-versa.

        :param hypothesis: hypothesis string (speech recognition output)
        :param reference: reference string (reference transcript to compare
        with hypothesis)
        :param kwargs:
            insCost (int) - the cost associated with an insertion (default is 1)
            delCost (int) - the cost associated with a deletion (default is 1)
            subCost (int) - the cost associated with a substitution (default is
            1)
            verbose (bool) - prints full calculations to console (default is
            False)

        :return: Levenshtein distance between the reference and hypothesis
        strings.
        """
        if not isinstance(hypothesis, basestring) \
            or not isinstance(reference, basestring):
            raise TypeError(hypothesis, "Hypothesis and reference must be strings.")

        kwargs.setdefault('insCost', 1)
        kwargs.setdefault('delCost', 1)
        kwargs.setdefault('subCost', 1)
        kwargs.setdefault('verbose', False)

        insCost = kwargs['insCost']
        delCost = kwargs['delCost']
        subCost = kwargs['subCost']

        #  Convert everything to lower case (token normalisation)
        hypothesis = hypothesis.lower()
        reference = reference.lower()

        from string import punctuation

        # Remove any punctuation
        hypothesis.translate(None, punctuation)
        reference.translate(None, punctuation)

        # Convert strings to lists
        hypothesis = hypothesis.split()
        reference = reference.split()

        import numpy
        # Initialise width and height of matrix
        D = numpy.zeros((len(reference)+1)*(len(hypothesis)+1), dtype=numpy.uint8)
        D = D.reshape((len(reference)+1, len(hypothesis)+1))

        for i in range(len(reference)+1):
            for j in range(len(hypothesis)):
                if i == 0:
                    D[0][j] = j
                elif j == 0:
                    D[i][0] = i

        # Calculation
        for i in range(1, len(reference)+1):
            for j in range(1, len(hypothesis)+1):
                if reference[i-1] == hypothesis[j-1]:
                    D[i][j] = D[i-1][j-1]
                else:
                    D[i][j] = min(D[i-1][j-1]+subCost,
                                  D[i][j-1]+insCost,
                                  D[i-1][j]+delCost)

        # Get Levenshtein distance (LD)
        ld = D[len(reference)][len(hypothesis)]

        if kwargs['verbose']:
            # Display calculations in console
            print "Reference word count: " + str(len(reference))
            print "Levenshtein distance = " + str(ld)
            print "Word Error Rate = " + str(ld) + " / " + str(len(reference)) + " = " + str(ld/float(len(reference)))

        # Return WER: LD/number of words in the reference string
        return ld/float(len(reference))

    def load_subs(self, pathToSubsFile, readFrom=0):
        """
        Read an subtitle file and return a lowercase string containing no
        numeric characters, newline characters, or punctuation. 
        This can then be used as a reference transcript for word error rate
        calculation.

        :param readFrom: the line to begin reading from
        (where 0 is the first line).
        :return: lowercase string containing no numeric values or punctuation
        (matching format of SR output for use as a reference script in WER
        calculation).
        """
        import string

        try:
            # Open the subtitle file as object f
            with open(pathToSubsFile, 'r') as f:
                # Break file in to array by newline characters
                fLines = f.readlines()

                # Combine all lines after index "readFrom" into a single string
                subStr= "".join(fLines[readFrom:])

                # Convert subs string to lower case, split newline characters
                subStr=subStr.replace('\n','').lower()

                # Remove punctuation
                subStr.translate(None, string.punctuation)

                # Copy each character from subs back in to subs unless character
                # is digit.
                # ISSUE: some subtitle files use numeric values
                # (e.g. when speaker says a number)
                #   instead of spelling numbers as words, this could potentially
                # effect the accuracy
                #    of the word error rate calculation.
                subStr = "".join([i for i in subStr if not i.isdigit()])

                # Replace remaining colons
                subStr = subStr.replace(':', ' ')

                return subStr

        except(IOError):
            RuntimeError("load_srt: failed to open file.")
            return False

        # Convert all text to lower case
        pass

    def evaluate(self, testCases, testDir, saveHypotheses=False):
        """
        Evaluate the hypotheses from a series of audio files against
        corresponding reference transcripts.
    
        :param testCases: list of [filename, refTranscriptPath] lists.
        :param testDir: path to the test data directory
        :param saveHypotheses: if True, hypotheses are saved as
        "SRHypothesis_CASE" where "CASE" is the file name of the given reference
        transcript.
        :return: result dictionary of (audio_filename, WordErrorRate) items.
        """
        if not isinstance(testCases, list):
            raise TypeError(testCases, "evaluate: testCases must be list of lists.")
    
        import time
        SR = SpeechRecognitionWrapper()
    
        results = {}
        caseNo = 1
        for case in testCases:
            # Generate path for SR engine
            path = testDir + case[0]
            # Recognize text (get hypothesis) and note execution time
            st = time.time()
            print "Passing Case " + str(caseNo) + " audio to SR engine."
            hyp = SR.speech_to_text(path)
            end = time.time()
            print "Case #" + str(caseNo) + " processed in " + str(end-st) + " seconds."
    
            if saveHypotheses:
                # Save hypothesis in text file
                f = open(testDir+"SRHypothesis_"+case[1], 'w+')
                f.write(hyp)
                f.close()
    
            # Get word error rate for this case using default cost settings
            # (see WER function documentation).
            wer = SR.word_error_rate(hyp,case[1],verbose=True)
            # Store results for this file in result dict.
            results[case[0]] = wer
    
            # Increment case number (for console output)
            caseNo += 1
    
        return results

    def buildTestCaseList(self, testDataDir):
        """
        Builds a test case list compatible with the evaluate function.  The given
        test data directory is expected to contain a list of audio files (.wav) and
        reference transcripts (.txt), where the names for corresponding audio and
        transcript files match (e.g. my_audio.wav - my_audio.txt).
    
        :param testDataDir: path to the test data directory.
        :return: Test case list compatible with the "evaluate" function
        """
        from os import listdir
        from os.path import isfile, join, splitext
    
        # Get all files from test data directory
        testFiles = [f for f in listdir(testDataDir) if isfile(join(testDataDir, f))]
    
        # List of test cases to be populated
        testCases = []
        # List of files to exclude from consideration (ones that are dealt with
        # below)
        exclude = []
    
        # Exclude all files that aren't txt or wav
        for f in testFiles:
            # Get file extention
            fExt = splitext(f)[1]
            if fExt != ".wav" and fExt != ".txt":
                exclude.append(f)
    
        for f in testFiles:
            if f not in exclude:
                # Separate file name and extension
                fname, fExt = splitext(f)
    
                for f2 in testFiles:
                    if f2 not in exclude and f != f2:
                        # Separate path and file extension
                        fname2, fExt2 = splitext(f2)
    
                        # If the names of the files match
                        if fname == fname2:
                            # If the first file is a wav...
                            if fExt == ".wav":
                                # The first file is the wav file, have that as first
                                # element in appended list.
                                testCases.append([fname + fExt, fname2 + fExt2])
                            else:
                                # The second file is the wav file.
                                testCases.append([fname2 + fExt2, fname + fExt])
    
                            # These files are dealt with, add them to exclude list
                            exclude.extend([f, f2])
        return testCases

if __name__ == '__main__':

    # Redirect stdout (python print) to the logger class, which sends outstream
    # to console and to a log file at the same time.
    sys.stdout = Logger("SRLog.log")

    print "Testing Word Error rate calculator"

    SR = SpeechRecognitionWrapper()


    ref = "This great machine can recognize speech"
    hyp = "This machine can wreck a nice beach"
    print "(1 deletion, 2 substitutions, 2 insertions)"

    print "reference = '" + ref +"'\nhypothesis = '" + hyp + "'\n"
    print "Expected WER = 0.8333... (cost of 5, divided by length of ref 6)\n" \
          "actual WER = " + str(SR.word_error_rate(ref, hyp)) + "\n\n"


    testDataDir = "TestData/"
    print "Testing speech recognition with test data in directory '" + testDataDir + "'"

    # Get list of test cases from test data directory
    testCaseList = SR.buildTestCaseList(testDataDir)
    print "found " + str(len(testCaseList)) + " test cases."
    # Evaluate SR engine (with default configuration) on test cases
    results = SR.evaluate(testCaseList, testDataDir)

    print "Evaluation complete.\n\nResults:"
    for case, wer in results.iteritems():
        print "Case: " + case + "\nWord Error Rate: " + str(wer*100) + "%"