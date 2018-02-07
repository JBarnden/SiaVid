from pipeline import DataMiner, Acquirer, Pipeline
from SpeechRecognition.SpeechRecognition import SpeechRecognitionAdapter
from shutil import copyfile, rmtree
import datetime
import wave
import contextlib
import os

# Application class just stores a pipeline object and makes sure
# the tmp directory exists.
class Application(object):
    def __init__(self, tmpDir):
        # Check if temp directory exists, if not create it.
        if not os.path.exists(tmpDir):
            os.makedirs(tmpDir)

        # Store path to temp directory
        self.tmpDir = tmpDir
        # Create pipeline
        self.pl = Pipeline()

    def acquireAndBuildCorpus(self, acquireTag, minerTag, corpusTag, *acquireArgs):
        # Append filename to set tmpDir path (this assumes the first arg to an acquirer
        # will be a path), this feels a bit 'hackie'.
        args = list(acquireArgs)
        args[0] = self.tmpDir + acquireArgs[0]
        # Convert args back to tuple
        acquireArgs = tuple(args)
        # Call the pipeline function
        self.pl.acquireAndBuildCorpus(acquireTag, minerTag, corpusTag, *acquireArgs)

    def clean(self):
        # Delete all files in temp directory
        for f in os.listdir(self.tmpDir):
            fpath = os.path.join(self.tmpDir, f)
            try:
                if os.path.isfile(fpath):
                    os.unlink(fpath)
            except Exception as e:
                print e


    def clear(self):
        # Clear and delete the temp directory
        rmtree(self.tmpDir)

# Get duration of a wav file in seconds (used by miners).
def getAudioDuration(path):
    # Check duration of the audio in this file
    with contextlib.closing(wave.open(path, 'r')) as audio:
        frames = audio.getnframes()
        rate = audio.getframerate()
        # Get duration in seconds
        duration = frames / float(rate)
        return duration

class AudioSplitter(DataMiner):

    def __init__(self, offsetS):
        """
        Takes an input wav file and outputs several wav files based on given offset.

        :param offsetS: offset in seconds
        """
        DataMiner.__init__(self)

        if not isinstance(offsetS, int):
            raise TypeError(offsetS, "wavToChunks: expected 'int' for offset.")

        # Offset in miliseconds
        self.offsetMS = offsetS*1000

    def build(self, path):
        # Check that path is valid
        if not os.path.isfile(path):
            raise IOError(path, "SR Acquirer: Invalid path given.")

        # Separate path from file extension
        fName, fExt = os.path.splitext(path)

        # Get duration of audio file in microseconds
        duration = getAudioDuration(path)*1000

        # chunkNo is appended to the end of a file name
        chunkNo = 0
        endMS = 0
        paths = []

        audioRemaining = True
        while audioRemaining:
            # Set start and end times for slice
            startMS = endMS
            endMS = startMS + self.offsetMS

            if endMS > duration:
                # Prevent from reading more data than actually exists
                endMS = duration
                # We reached eof.
                audioRemaining = False
            elif endMS == duration:
                # We reached eof.
                audioRemaining = False

            # Append chunkNo to end of file name
            outfile = fName + str(chunkNo) + '_' + fExt

            # Write slice to numbered outfile
            self.slice(path, outfile, startMS, endMS)

            # Append path to outfile
            paths.append(outfile)
            # Increment chunk number
            chunkNo+=1

        return paths

    def slice(self, path, outfile, startMS, endMS):
        """
            Takes a slice from infile, from startMS to endMS.
            Write slice to outfile

        :param infile: file to take a slice from.
        :param outfile: where the slice will be saved.
        :param startMS: where to the slice starts in microseconds.
        :param endMS: where the slice ends in microseconds.
        :return:
        """
        # Create outfile if it doesn't exist
        if not os.path.isfile(outfile):
            open(path, 'a').close()

        # Open original audio file, get width and rate
        with contextlib.closing(wave.open(path, 'r')) as infile:
            width = infile.getsampwidth()
            rate = infile.getframerate()

            # get frames per ms
            fpms = rate / 1000
            # Calculate the length this slice should be
            length = (endMS - startMS) * fpms
            # Work out where the slice should start
            startIndex = startMS * fpms

            # Open the outfile for writing
            out = wave.open(outfile, 'w')
            out.setparams((infile.getnchannels(), width, rate, length, infile.getcomptype(), infile.getcompname()))

            # Set appropriate start position on the infile.
            infile.rewind()
            anchor = infile.tell()
            infile.setpos(anchor+startIndex)
            # Write frames to the outfile
            out.writeframes(infile.readframes(length))

class SpeechRecogMiner(DataMiner):

    def __init__(self, language, **kwargs):
        """

        :param language:
        :param offset: datetime.time object specifying offset for each chunk
        :param kwargs:
        """
        DataMiner.__init__(self)
        self.SRA = SpeechRecognitionAdapter()

        # Language code that determines the dataset to be used by
        # the Recognizer (currently only en-US supported).
        # Exception handling for incompatible language is handled in SRA.
        self.language = language
        # Kwargs are passed to the speech_to_text function (See SpeechRecognition/Readme.md)
        self.config = kwargs


    def build(self, data):
        """

        :param data: a single path, or list of paths to audio files.
        :return: a list of srt chunks.
        """
        if not isinstance(data, list):
            data = [data]

        chunks = []
        et = datetime.timedelta(seconds=0)

        for path in data:
            if not isinstance(path, basestring):
                raise TypeError(data, "SpeechRecogMiner: 'data' must be string or list of strings.")

            # Get duration of this clip
            duration = getAudioDuration(path)

            # Set start time to previous end time
            st = et
            # Set end time to start time + duration
            et = st + datetime.timedelta(seconds=duration)

            # Populate an SRT chunk for this audio file and append it to the list
            chunks.append(self.populate_SRT_chunk(path, st, et))

        # Return the list of SRT chunks
        return chunks


    def populate_SRT_chunk(self, pathToAudio, startTime, endTime):
        """

        :param pathToAudio: self explanatory
        :param startTime: start time of this chunk
        :param endTime: end time of this chunk
        :return:
        """
        from chunker import SRTChunk

        # Get hypothesis from Recognizer
        hypothesis = self.SRA.speech_to_text(pathToAudio, self.language, **self.config)

        # Populate and return an SRTChunk object
        chunk = SRTChunk()
        chunk.content = hypothesis
        chunk.startTime = startTime.seconds
        chunk.endTime = endTime.seconds
        return chunk

class StringRepeater(Acquirer):
    """
        Always returns the path it was
        given at instantiation.
    """
    def __init__(self, path):
        self.path = path

    def performAcquire(self, *args):
        return self.path

"""
    This class combines the functionality of the audio splitter
    and the Speech Recognition Miner in to a single DataMiner object.

    This is the Miner that should be used with the YoutubeDL audio acquirer.
"""
class AudioSplitSpeechRecog(DataMiner):
    def __init__(self, offsetS, languageTag):
        DataMiner.__init__(self)
        self.splitter = AudioSplitter(offsetS)
        self.SRMiner = SpeechRecogMiner(languageTag)

    def build(self, audioPath):
        # Split audio in to multiple chunks based on offset.
        listOfPaths = self.splitter.build(audioPath)

        # Populate and return a series of SRTChunk objects.
        srtChunks = self.SRMiner.build(listOfPaths)

        return srtChunks

"""
    Function used for test output
"""
def pretty_srt_chunk(SRTChunk):
    """
        returns a formatted, printable string from it's content.

    :return: pretty SRT chunk string
    """
    st = datetime.timedelta(seconds=SRTChunk.startTime)
    et = datetime.timedelta(seconds=SRTChunk.endTime)

    return ''.join([st.__str__(), ' --> ', et.__str__(), "  ", SRTChunk.content])

if __name__ == '__main__':

    """
        This test assumes that all data we're working with will be stored in the application
        temporary directory, so we need only specify file names.
    """
    # Create application with ref to temporary files dir & configure pipeline
    app = Application('/media/sf_VM_Share/tmp/')

    audioFile = "How-boredom-can-lead-to-your-most-brilliant-ideas-Manoush-Zomorodi.wav"

    # Copy audio file to tmp directory.  In a real scenario, an audio download acquirer
    # would be used to download audio from a video and return a path to it
    copyfile('./SpeechRecognition/TestData/' + audioFile,
             app.tmpDir + audioFile)

    # Set up a string repeater acquirer with a path to the audio file (which just repeats a given string)
    app.pl.addAcquirer(StringRepeater(app.tmpDir + audioFile), 'repeater')

    # Add a SRMiner
    app.pl.addMiner(AudioSplitSpeechRecog(offsetS=3,languageTag='en-US'), 'SRMiner')

    app.pl.reportStatus()

    """
        Build a corpus of SRT chunks with the SR Miner
    """
    # Build a corpus of SRT chunks with using the audio acquirer and SRMiner
    print "Building a corpus of SRT chunks with the SR Miner and Acquirer"
    #app.acquireAndBuildCorpus('audioSplitter', 'SRMiner', 'SRCorpus', audioFile)
    app.pl.acquireAndBuildCorpus('repeater', 'SRMiner', 'SRCorpus')

    app.pl.reportStatus()

    # Clean temp dir contents (without deleting the dir)
    app.clean()

    print "Corpus Entries:"
    # Check the corpus directly
    SRTChunks = app.pl.corpus['SRCorpus']

    # Print all chunks
    for c in SRTChunks:
        print pretty_srt_chunk(c)





