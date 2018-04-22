from pipeline import DataMiner, Acquirer, Pipeline, OUT_OF_DATE, WAIT, READY, ERROR
from SpeechRecognition.SpeechRecognition import SpeechRecognitionWrapper
from shutil import copyfile, rmtree
from exampleplugins import YoutubeAudioAcquirer
import datetime
import wave
import contextlib
import os

# Application class just stores a pipeline object and makes sure
# the tmp directory exists.
class Application(object):
    """
        This just stores a pipeline object and makes sure
        the given temporary directory exists.  (only used for
        testing the speech recognition miner independently)
    """
    def __init__(self, tmpDir):
        # Check if temp directory exists, if not create it.
        if not os.path.exists(tmpDir):
            os.makedirs(tmpDir)

        # Store path to temp directory
        self.tmpDir = tmpDir
        # Create pipeline
        self.pl = Pipeline()

    def acquireAndBuildCorpus(self, acquireTag, minerTag, corpusTag, *acquireArgs):
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
    """
        Returns the duration of the audio file at path in seconds.
        This function is used by the AudioSplitter and SpeechRecognition
        miners.

    :param path: path to a wav file.
    :return: length of the wav file in seconds.
    """
    try:
        with contextlib.closing(wave.open(path, 'r')) as audio:
            frames = audio.getnframes()
            rate = audio.getframerate()
            # Get duration in seconds
            duration = frames / float(rate)
            return duration
    except Exception as e:
        return False

class AudioChunk(object):
    """
        A simple data structure representing a chunk of audio.
        This is used by SpeechRecogMiner
    """
    def __init__(self, startTime, endTime, fname):
        """

        :param startTime: start time of the audio chunk in milliseconds (with respect to the source audio)
        :param endTime:  end time of the audio chunk in milliseconds (with respect to the source audio)
        :param fname: file name with extension (not the full path)
        """
        self.startTime = startTime
        self.endTime = endTime
        self.fname = fname

class AudioSplitter(DataMiner):

    def __init__(self, chunkSize, offset=0, tempDir="./tmp/"):
        """
        Takes an input wav file and outputs a list of several wav files of "chunkSize"
        second length.  An offset can also be given, which creates an overlap
        across clips to prevent speech in audio being missed/split in half.

        :param chunkSize: preferred size of audio chunks in seconds.
        :param offset: subtracts "offset" seconds.
        """
        DataMiner.__init__(self, tempDir)

        if not isinstance(chunkSize, int):
            #raise TypeError(chunkSize, "wavToChunks: expected 'int' for offset.")
            self.status = ERROR
            
        # chunk size and offset converted to milliseconds
        self.chunkSizeMS = chunkSize*1000
        self.offsetMS = offset*1000

    def build(self, fname):
        """
        Splits the audio in the given file based on the chunk size and offset
        given at instantiation, and saves each chunk as an audio file in the
        temporary directory.

        :param fname: Name of the audio file to be split (inside the given temp
        directory).
        :return: a list of AudioChunk objects with paths to, and timestamps of the resulting audio files.
        """

        # Prepend temporary directory to file name
        path = self.tempDir + fname

        # Check that path is valid
        if not os.path.isfile(path):
            #raise IOError(path, "AudioSplitter: Invalid path given.")
            print "AudioSplitter: Invalid path given."
            self.status = ERROR

        # Separate path and file extension
        fpath, fExt = os.path.splitext(path)

        # Get duration of audio file in microseconds
        duration = getAudioDuration(path)*1000
        
        if duration is False:
            return None, ERROR

        # chunkNo is appended to the end of a file name
        chunkNo = 0
        endMS = 0
        #paths = []
        chunks = []

        audioRemaining = True
        while audioRemaining:
            # Set start and end times for chunk
            if chunkNo != 0:
                # If we're not on the first chunk, set start time to
                # previous end time minus the offset.
                startMS = endMS - self.offsetMS
            # Start time is 0 for the first chunk (start of the file)
            else: startMS = 0

            # Set end time of the chunk to the previous end time + chunk size.
            endMS = endMS + self.chunkSizeMS

            if endMS > duration:
                # Prevent from reading more data than actually exists
                endMS = duration
                # We reached eof.
                audioRemaining = False
            elif endMS == duration:
                # We reached eof.
                audioRemaining = False

            # Append chunkNo to end of file name
            outfile = fpath + '_' + str(chunkNo) + fExt

            # Write slice to numbered outfile
            success = self.slice(path, outfile, startMS, endMS)
            
            # Return if we have an error
            if not success:
            	print "AudioSplitter: Error writing audio chunk " + str(chunkNo)
            	print "chunk startMS: " + str(startMS) + ", endMS: " + str(endMS)
            	return chunks, ERROR

            # Get file name of new file for list of file names to return
            newFileName = fname.split(".")[0] + '_' + str(chunkNo) + fExt

            # Create audioChunk object and append it to the list of audio chunks
            chunk = AudioChunk(startMS, endMS, newFileName)

            # Append AudioChunk to list
            chunks.append(chunk)

            # Increment chunk number
            chunkNo+=1

        return chunks, READY

    def slice(self, path, outfile, startMS, endMS):
        """
        Takes a slice from the audio file at path, from startMS to endMS and
        writes the slice to the file at "outfile" (or creates the file if it
        doesn't exist).

        :param path: path of the file to take a slice from.
        :param outfile: path where the slice will be saved.
        :param startMS: where to the slice starts in microseconds.
        :param endMS: where the slice ends in microseconds.
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
            length = int((endMS - startMS) * fpms)
            # Work out where the slice should start
            startIndex = startMS * fpms
            
            try:
                # Open the outfile for writing
                out = wave.open(outfile, 'w')
                out.setparams((infile.getnchannels(), width, rate, length, infile.getcomptype(), infile.getcompname()))
                
                # Set appropriate start position on the infile.
                infile.rewind()
                anchor = infile.tell()
                infile.setpos(anchor+startIndex)
                # Write frames to the outfile
                out.writeframes(infile.readframes(length))
            except Exception as e:
                # We had a problem, return false
                return False
            
            # Return true on successful write
            return True

class SpeechRecogMiner(DataMiner):

    def __init__(self, language, offset=0, settings=None, tempDir="./tmp/"):
        """
        A speech recognition Data Miner class, making the Speech Recognition
        Wrapper functionality compatible with the pipeline plugin interface.

        :param language: The RFC5646 language tag corresponding to the
        recognition language to be used by the engine (default: en-US)
        :param offset: The offset in seconds, applied to the audio splitter.
        :param settings: a dictionary of any additional settings supported by
        the Speech Recognition Adapter (see Speech Recognition Wrapper
        documentation)
        """
        DataMiner.__init__(self, tempDir)
        self.SRA = SpeechRecognitionWrapper()

        # Language code that determines the dataset to be used by
        # the Recognizer (currently only en-US supported).
        # Exception handling for incompatible language is handled in SRA.
        self.language = language
        # Kwargs are passed to the speech_to_text function
        # (See SpeechRecognitionWrapper Documentation)
        self.config = settings

        # Offset applied in the audio splitter
        self.offsetS = offset


    def build(self, chunkList, nThreads=-1):
        """
        Passes audio from the file(s) in "data" to the Speech Recognition
        engine, and returns one or more timestamped hypotheses as SRTChunk
        objects.

        :param chunkList: a single AudioChunk object, or list of AudioChunk objects.
        to be transcribed within the given temporary directory.
        :return: a list of SRTChunk objects.
        """
        if not isinstance(chunkList, list):
            chunkList = [chunkList]

        chunks = []
        et = datetime.timedelta(seconds=0)
        # Offset in miliseconds
        #offsetS = self.offsetS*1000

        print "Speech Recognition: Received " + str(len(chunkList)) + " audio chunks."

        for c in chunkList:
            if not isinstance(c, AudioChunk):
                #raise TypeError(fname, "SpeechRecogMiner: 'fnames' must be string or list of strings.")
                print "SpeechRecogMiner: 'fnames' must be string or list of strings."
                return chunks, ERROR

            print "Processing audio chunks " + str((float(chunkList.index(c))/len(chunkList))*100) + "% complete."

            # Prepend temporary directory to the file name
            path = self.tempDir + c.fname

            # Get duration of this clip
            duration = getAudioDuration(path)
            
            if duration == False:
                return None, ERROR

            # Get start and end times of the chunk from the AudioChunk object
            st = datetime.timedelta(milliseconds=c.startTime)
            et = datetime.timedelta(milliseconds=c.endTime)

            # Populate an SRTChunk from this audio chunk with the Speech Recognition engine
            chunk = self.populate_SRT_chunk(path, st, et)
            
            if chunk != None:
            	chunks.append(chunk)
            else:
            	print "SpeechRecog Error: Problem occurred processing file " + c.fname
            	return chunks, ERROR

        # Return the list of SRT chunks
        return chunks, READY


    def populate_SRT_chunk(self, pathToAudio, startTime, endTime):
        """
        Passes the audio at "pathToAudio" to the speech recognition engine and
        returns a hypothesis in an SRTChunk object. To be called indirectly via
        the build function.

        :param pathToAudio: path to the audio file
        :param startTime: start time of this chunk
        :param endTime: end time of this chunk
        :return: An SRTChunk object containing a timestamped hypothesis.
        """
        from chunker import SRTChunk

        try:
            # Get hypothesis from Recognizer
            if self.config is not None:
                if not isinstance(self.config, dict): raise IOError(self.config, "SR settings must be dict!")
                hypothesis = self.SRA.speech_to_text(pathToAudio, self.language, **self.config)
            else:
                hypothesis = self.SRA.speech_to_text(pathToAudio, self.language)
            
            # Populate and return an SRTChunk object
            chunk = SRTChunk()
            chunk.content = [hypothesis]
            chunk.startTime = startTime.seconds
            chunk.endTime = endTime.seconds
        except Exception as e:
            return None

        return chunk

class AudioSplitSpeechRecog(DataMiner):
    """
        A composite data miner, combining the functionality of the audio
        splitter and speech recognition miners.
    """
    def __init__(self, chunkSize, offset, languageTag, settings=None, tempDir='./tmp/'):
        DataMiner.__init__(self, tempDir)

        self.splitter = AudioSplitter(chunkSize, offset, tempDir)
        self.SRMiner = SpeechRecogMiner(languageTag, offset, settings, tempDir)

    def build(self, audioPath):
        # Split audio in to multiple chunks based on offset.
        listOfPaths, status = self.splitter.build(audioPath)

        if status == ERROR:
            print "AudioSplitSpeechRecog: Audio splitter error, returning None."
            return None, ERROR
		
        # Populate and return a series of SRTChunk objects.
        srtChunks, status = self.SRMiner.build(listOfPaths)
        
        if status == ERROR:
        	print "AudioSplitSpeechRecog: SpeechRecog error, returning None."
        	return None, ERROR

        return srtChunks, READY

class StringRepeater(Acquirer):
    """
        Always returns the string it was
        given at instantiation when performAcquire is called.
        (for testing purposes)
    """
    def __init__(self, fname, tempDir="./tmp/"):
        Acquirer.__init__(self, tempDir)
        self.fname = fname

    def performAcquire(self, *args):
        return self.fname

def pretty_srt_chunk(SRTChunk):
    """
    Returns a formatted, printable string from it's content.
    This is used for standalone Speech Recognition testing.

    :return: pretty SRTChunk string
    """
    st = datetime.timedelta(seconds=SRTChunk.startTime)
    et = datetime.timedelta(seconds=SRTChunk.endTime)

    return ''.join([st.__str__(), ' --> ', et.__str__(), "  ", SRTChunk.content])

if __name__ == '__main__':
    # Set up temporary directory for testing
    tmp = 'tmp/'

    while True:
        opt = raw_input(
            "Tests:\n"
            "1  Test SR on local file\n"
            "2  Test with video URL\n"
            "3  Exit\n\n"
            "Selection: "
        )


        if opt == str(1):
            """
                Test 1: test speech recognition on a pre-downloaded file from
                test data folder.
            """

            # Create application with ref to temporary files dir & configure pipeline
            app = Application(tmp)

            #audioFile = "How-boredom-can-lead-to-your-most-brilliant-ideas-Manoush-Zomorodi.wav"
            audioFile = "30sec.wav"

            # Copy audio file to tmp directory.  In a real scenario, an audio download acquirer
            # would be used to download audio from a video and return a path to it
            copyfile('./SpeechRecognition/TestData/FunctionalityTesting/' + audioFile,
                     app.tmpDir + audioFile)

            # Set up a string repeater acquirer with a path to the audio file (which just repeats a given string)
            app.pl.addAcquirer(StringRepeater(audioFile, tmp), 'repeater')

            # Add a SRMiner
            app.pl.addMiner(AudioSplitSpeechRecog(chunkSize=3, offset=1,languageTag='en-US', tempDir=tmp), 'SRMiner')

            # Check pipeline contents
            app.pl.reportStatus()

            import time

           # Build a corpus of SRTChunk objects with the speech recognition miner, measuring execution time.
            start = time.time()
            app.acquireAndBuildCorpus('repeater', 'SRMiner', 'SRCorpus', audioFile)
            end = time.time()

            # Calculate execution time
            execTime = end - start

            # Performance report
            print "Built corpus from " + str(getAudioDuration(tmp+audioFile)/60) + " minute audio file in " \
                  + str(execTime/60) + " minutes."

            # Pipeline status report
            app.pl.reportStatus()

            # Display corpus entries in console
            print "Corpus Entries:"
            SRTChunks = app.pl.corpus['SRCorpus']
            #SRTChunks = corpus

            if SRTChunks is not None:
                # Print all chunks
                for c in SRTChunks:
                    print pretty_srt_chunk(c)

            # Clean temp dir contents (without deleting the dir)
            app.clean()

            # More processing...

            # Clear temp dir completely (Deleting dir)
            #app.clear()

        elif opt == str(2):
            """
                Test 2: Perform speech recognition on given video URL.
            """

            # # Query user for video url
            url = raw_input('Video url for Speech Recognition:\n')

            url = url.strip(' ')

            # youtube dl opts dict for downloading audio
            ydl_opts = {
                'outtmpl': unicode(tmp + '%(id)s.%(ext)s'),
                'format': 'bestaudio/best',
                'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'wav',
                'preferredquality': '192',
            }],
            }

            app = Application(tmp)

            # Configure audio acquirer
            ydl = YoutubeAudioAcquirer(tmp)

            # Add acquirer to pipeline
            app.pl.addAcquirer(ydl, 'ydl_audio')

            app.pl.addMiner(
                AudioSplitSpeechRecog(chunkSize=3, offset=1,languageTag='en-US', tempDir=tmp),
                'SRMiner'
            )

            # Report status
            app.pl.reportStatus()

            # Acquire and build corpus with the given url
            app.pl.acquireAndBuildCorpus('ydl_audio', 'SRMiner', 'SRCorpus', url)

            # Display corpus entries in console
            print "Corpus Entries:"
            SRTChunks = app.pl.corpus['SRCorpus']

            # Print all chunks
            for c in SRTChunks:
                print pretty_srt_chunk(c)

            # Clean temp dir content without deleting it
            app.clean()
        elif opt == str(3):
            exit(0)







