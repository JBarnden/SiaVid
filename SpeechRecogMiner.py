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
                print "e"

    def clear(self):
        # Clear and delete the temp directory
        rmtree(self.tmpDir)

# Get duration of a wav file in seconds (used by miner and acquirer).
def getAudioDuration(path):
    # Check duration of the audio in this file
    with contextlib.closing(wave.open(path, 'r')) as audio:
        frames = audio.getnframes()
        rate = audio.getframerate()
        # Get duration in seconds
        duration = frames / float(rate)
        return duration

class wavToChunks(Acquirer):

    def __init__(self, offsetS):
        """
        Takes an input wav file and outputs several wav files based on given offset.

        :param offsetS: offset in seconds
        """
        if not isinstance(offsetS, int):
            raise TypeError(offsetS, "wavToChunks: expected 'int' for offset.")

        # Offset in miliseconds
        self.offsetMS = offsetS*1000

    def acquire(self, path):
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
        # Get hypothesis from Recognizer
        hypothesis = self.SRA.speech_to_text(pathToAudio, self.language, **self.config)

        # Format timestamps
        startTS = startTime.__str__()
        endTS = endTime.__str__()
        # Return hypothesis as SRT chunk
        return "{0} --> {1}\n".format(startTS, endTS) + hypothesis

    def getTimestamp(self, timedelta):
        """

        :param timedelta: datetime.timedelta object
        :return: string timestamp in the format: "HH:MM:SS"
        """
        s = timedelta.total_seconds()
        hours, remainder = divmod(s, 3600)
        minutes, seconds = divmod(remainder, 60)

        return "{0}:{1}:{2}".format(hours, minutes, seconds)


if __name__ == '__main__':

    """
        Create application with ref to temporary files dir & configure pipeline
        (Had to set a weird temp dir as my VM ran out of disk space)
    """
    app = Application('./tmp/')

    audioFile = "How-boredom-can-lead-to-your-most-brilliant-ideas-Manoush-Zomorodi.wav"

    # Copy audio file to tmp directory, this would be done with a YoutubeDL acquirer.
    copyfile('./SpeechRecognition/TestData/' + audioFile,
             app.tmpDir + audioFile)

    """
        This test assumes that all data we're working with will be stored in the application
        temporary directory, so we need only specify file names.
    """

    # Set up a 'wavToChunks' acquirer to split an audio file in to new files, each one 3 seconds long
    app.pl.addAcquirer(wavToChunks(offsetS=3), 'audioAcquirer')
    # Instantiate a Speech Recognition miner, setting the language code
    app.pl.addMiner(SpeechRecogMiner(language='en-US'),'SRMiner')

    app.pl.reportStatus()

    """
        Build a corpus of SRT chunks with the SR Miner
    """
    # Build a corpus of SRT chunks with using the audio acquirer and SRMiner
    print "Building a corpus of SRT chunks with the SR Miner and Acquirer"
    app.acquireAndBuildCorpus('audioAcquirer', 'SRMiner', 'SRCorpus', audioFile)
    app.pl.reportStatus()

    # Clean temp dir contents (without deleting the dir)
    app.clean()

    print "Corpus Entries:"
    # Check the corpus directly
    SRTChunks = app.pl.corpus['SRCorpus']

    # Print all chunks
    for c in SRTChunks:
        print c



    # More processing...

    # Delete temp dir and contents now application cycle has finished.
    app.clear()






