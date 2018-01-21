from time import gmtime, strftime

# Library require manual installation (pip install SpeechRecognition)
import speech_recognition as sr



class SpeechRecognitionAdapter(object):
    def __init__(self):
        # Create instance of recognizer object accessible
        # to all class methods
        self.r = sr.Recognizer()

        # List of supported language codes (for Sphinx)
        self.SL = ['en-US']

    def read_audio_data(self, audioFilePath, **kwargs):
        # "values below energy threshold are considered silence, values above the threshold are considered speech"
        #     - https://github.com/Uberi/speech_recognition/blob/master/reference/library-reference.rst#recognizer_instanceenergy_threshold--300
        """
        This function is used by the speech_to_text method to convert a
        sound file to suitable input for an SR engine.

        :param kwargs:
            'startTime' - where to start recording from, default is None
            (read from start).

            'recordDuration' - how long to record for, default is None
            (read until end of stream)
        :return: Audio data instance (input to an SR engine)
        """
        kwargs.setdefault('startTime', None)
        kwargs.setdefault('recordDuration', None)
        kwargs.setdefault('energyThreshold', -1)

        if kwargs['energyThreshold'] > -1:
            self.r.energy_threshold = kwargs['energyThreshold']
        else:
            # recognizer will automatically adjust energy threshold based on "the currently ambient noise level while listening"
            #    - https://github.com/Uberi/speech_recognition/blob/master/reference/library-reference.rst#recognizer_instancedynamic_energy_threshold--true
            self.r.dynamic_energy_threshold = True

        # Open audio file for reading, storing it as an AudioFile instance called "source".
        try:
            with sr.AudioFile(audioFilePath) as source:
                # "Record" audio from source, returns "AudioData" instance
                #    - https://github.com/Uberi/speech_recognition/blob/master/reference/library-reference.rst#recognizer_instancerecordsource-duration--none-offset--none
                return self.r.record(source, kwargs['recordDuration'], kwargs['startTime'])
        except (RuntimeError, TypeError, IOError):
            print "SR Adapter: failed to read audio data"

    # Currently outputs text
    def speech_to_text(self, audioFilePath, language='en-US', **kwargs):
        """
            Takes the path of an audio file, decodes it, and attempts to recognize speech within the decoded
            audio using one or more SR engines.

        :param audioFilePath:
            Path to the audio file containing speech.
        :param Language:
            By default, the dynamic energy threshold is applied.
        :param kwargs:
            "energy-threshold" (int):
            Values below the energy threshold are considered as silence,
            values above considered as speech.
            If energy-threshold is -1, the dynamic energy threshold will be used.
            (see https://github.com/Uberi/speech_recognition/blob/master/reference/library-reference.rst#recognizer_instanceenergy_threshold--300)


            Different engines can be enabled/disabled like so:
                - sphinx=True/False (True by default)
                - gsr=True/False (False by default)
                - wit=True/False (False by default)

            Verbose output can also be toggled with:
                - verbose=True/False (False by default)
                If false, function just returns the best possible prediction.
                If true, function returns a more detailed output.  E.g. for sphinx,
                verbose output would return a pocketsphinx.Decoder object with scores and
                confidence values for the generated hypothesis and its segments.
        :return:
        """

        kwargs.setdefault("energyThreshold", -1)
        kwargs.setdefault("sphinx", True)
        kwargs.setdefault("gsr", False)
        kwargs.setdefault("wit", False)
        kwargs.setdefault("verbose", False)

        # Create "Recognizer" object, this holds SR settings and functionality.
        recognizer = sr.Recognizer()

        # Function returns a list of hypotheses if multiple engines are enabled through kwargs.
        output = []

        if kwargs["energyThreshold"] > -1:
            recognizer.energy_threshold = kwargs["energyThreshold"]
        else:
            # recognizer will automatically adjust energy threshold based on "the currently ambient noise level while listening"
            #    - https://github.com/Uberi/speech_recognition/blob/master/reference/library-reference.rst#recognizer_instancedynamic_energy_threshold--true
            recognizer.dynamic_energy_threshold = True

        # Open audio file for reading, storing it as an AudioFile instance called "source".
        with sr.AudioFile(audioFilePath) as source:
            # "Record" audio from source, returns "AudioData" instance
            # https://github.com/Uberi/speech_recognition/blob/master/reference/library-reference.rst#recognizer_instancerecordsource-duration--none-offset--none
            audio = recognizer.record(source)

            sphinxText = None
            witAIText = None
            googleSRText = None

            # Following inspired by: https://github.com/Uberi/speech_recognition/blob/master/examples/audio_transcribe.py
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

    def language_supported(self, language):
        if language in self.SL:
            return True
        else:
            return False

    # Function calculates the distance/difference between two strings
    # 'hypothesis' and 'reference' using the levenshtein distance algorithm.
    # Ref: http://www.python-course.eu/levenshtein_distance.php
    def word_error_rate(self, hypothesis, reference, **kwargs):
        kwargs.setdefault('insCost', 1)
        kwargs.setdefault('delCost', 1)
        kwargs.setdefault('subCost', 1)

        insCost = kwargs['insCost']
        delCost = kwargs['delCost']
        subCost = kwargs['subCost']

        #  Convert everything to lower case (token normalisation)
        #  Compare each result item against transcript, count number of differing words (incorrect guesses)
        #  Generate accuracy rating for each result in results

        # Initialise width and height of matrix
        rows = len(hypothesis)+1
        cols = len(reference)+1
        # Initialise all matrix values to 0
        D = [[0 for x in range(cols)] for x in range(rows)]

        for i in range(1, rows):
            D[i][0] = i*delCost

        for i in range(1, cols):
            D[0][i] = i*insCost

        # Complete table
        for col in range(1, cols):
            for row in range(1, rows):
                # If there is no difference between hyp and ref
                # strings at this position, cost is 0 (they're the same)
                if hypothesis[row-1] == reference[col-1]:
                    cost = 0
                else:
                    # hyp and ref at this position are not equal,
                    # look for shortest path between hyp and ref strings
                    # (either insertion, deletion, or substitution).
                    cost = subCost
                    D[row][col] = min(D[row-1][col]+delCost,
                                      D[row][col-1]+insCost,
                                      D[row-1][col-1]+cost)

        # Return final levenshtein distance between strings.
        return D[rows-1][cols-1]


def load_srt(pathToSubsFile, readFrom=0):
    import string

    """
    Read an srt file and return a lowercase string containing no numeric characters,
    newline characters, or punctuation.

    :param readFrom: the index position of the line to begin reading from
    (where 0 is the first line).
    :return: lowercase string containing no numeric values or punctuation
    (matching format of SR output for use in WER function).
    """
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

            # Copy each character from subs back in to subs unless character is digit.
            # ISSUE: some subtitle files use numeric values (e.g. when speaker says a number)
            #   instead of spelling numbers as words, this could potentially effect the accuracy
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

if __name__ == '__main__':

    """
        Test Word Error Rate Calculator
    """

    SRA = SpeechRecognitionAdapter()

    hypothesis = "I like chicken a lot"
    ref = "like chicken load"

    # Works:
    wer = SRA.word_error_rate(hypothesis.split(" "), ref.split(" "))

    # Doesn't work:
    wer = SRA.word_error_rate("abc def", "xyz def")

    # Works:
    wer = SRA.word_error_rate("abc","xyz")

    """
        Test speech recognition
    """

    # path to audio file
    audioPath = "Dataset/How-boredom-can-lead-to-your-most-brilliant-ideas-Manoush-Zomorodi.wav"
    # Path to reference transcript (SRT format)
    refPath = "Dataset/How-boredom-can-lead-to-your-most-brilliant-ideas-Manoush-Zomorodi.txt"

    # Get text from sphinx with default settings
    print "Passing audio to engine..."
    hypothesis = SRA.speech_to_text(audioPath)
    print "Finished decoding and recognizing audio"

    print "\nHypothesis: " + hypothesis

    # Load reference transcript (SRT format) for WER calculation
    ref = load_srt(refPath, 19)

    # Calculate and output word error rate (value from objective function)
    wer = SRA.word_error_rate(hypothesis, ref)
    print "\nWord Error Rate: " + str(wer)