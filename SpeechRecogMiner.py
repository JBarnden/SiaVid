from pipeline import DataMiner, Acquirer
from SpeechRecognition.SpeechRecognition import SpeechRecognitionAdapter
import datetime
import wave
import contextlib

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
        # Convert duration in seconds to miliseconds
        duration = getAudioDuration(path)*1000
        outfile = "./tmp/" + path
        chunkNo = 0
        startMS = 0
        endMS = 0

        paths = []

        audioRemaining = True
        while audioRemaining:
            # Set start and end times for slice
            startMS += endMS
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
            outfileTemp = outfile + str(chunkNo)

            # Write slice to numbered outfile
            self.slice(path, outfile, startMS, endMS)

            # Append path to outfile
            paths.append(outfileTemp)
            # Increment chunk number
            chunkNo+=1

        return paths


    def slice(self, infile, outfile, startMS, endMS):
        """
            Takes a slice from infile, from startMS to endMS.
            Write slice to outfile

        :param infile: file to take a slice from.
        :param outfile: where the slice will be saved.
        :param startMS: where to the slice starts in microseconds.
        :param endMS: where the slice ends in microseconds.
        :return:
        """
        width = infile.getsampwidth()
        rate = infile.getframerate()
        fpms = rate / 1000 # frames per ms
        length = (endMS - startMS) * fpms
        startIndex = startMS * fpms

        out = wave.open(outfile, 'w')
        out.setparams((infile.getnchannels(), width, rate, length, infile.getcompattype(), infile.getcompatname()))

        infile.rewind()
        anchor = infile.tell()
        infile.setpos(anchor+startIndex)
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
        st = datetime.time(0, 0, 0)
        et = datetime.time(0, 0, 0)

        for path in data:
            if not isinstance(data, basestring):
                raise TypeError(data, "SpeechRecogMiner: 'data' must be string or list of strings.")

            duration = getAudioDuration(path)

            # Set start and end times of this chunk
            st = et
            et = st + datetime.timedelta(seconds=duration)

            # Populate an SRT chunk for this audio file and append it to the list
            chunks.append(self.populate_SRT_chunk(data, st, et))

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

        # Return hypothesis as SRT chunk
        return "".join([startTime.hour, ":", startTime.minute, ":", startTime.second, ":", startTime.microsecond,
                        " --> ",
                        endTime.hour, ":", endTime.minute, ":", endTime.second, ":", endTime.microsecond,
                        "\n", hypothesis])


if __name__ == '__main__':
    audioFilePath = "SpeechRecognition/TestData/How-boredom-can-lead-to-your-most-brilliant-ideas-Manoush-Zomorodi.wav"

    # Set up a 'wavToChunks' acquirer to split an audio file in to new files, each one 3 seconds long
    audioAcquirer = wavToChunks(offsetS=3)
    # Break audio file down
    listOfPaths = audioAcquirer.acquire(audioFilePath)

    # Instantiate a Speech Recognition miner, setting the language code
    SRMiner = SpeechRecogMiner(language='en-US')

    # Get a list of SRT chunks from the SR Miner
    SRTChunks = SRMiner.build(listOfPaths)



