from pipeline import DataMiner, READY, ERROR

import cv2

class Face:
	def __init__(self):
		# set up face parameters here
		pass

class FaceChunk:
	def __init__(self):
		self.startTime = 0
		self.endTime = 0
		self.content = []

class FaceFinder(DataMiner):
	def __init__(self, tempDir = './tmp', sampleRate = 1, chunkSize = 5):
		DataMiner.__init__(self, tempDir)
		self.sampleRate = sampleRate # number of samples per second
		self.chunkSize = chunkSize # final length of chunks returned

	def build(self, data):
		""" Returns a list of time-indexed FaceChunks holding Faces """

		results = []
		cap = cv2.VideoCapture(data)
		fps = cap.get(cv2.cv.CV_CAP_PROP_FPS) # video FPS

		grain = fps/self.sampleRate # offset for x samples per second

		while(cap.isOpened()): # loop through video in steps of size 'grain'
			currFrame = cap.get(cv2.cv.CV_CAP_PROP_POS_FRAMES)

			ret, frame = cap.read()

			if ret == False: # have we run out of video?
				break

			faces = [] # find faces here

			chunk = FaceChunk()
			for face in faces:
				chunk.content.append(faceToVector(face))

			results.append()

		cap.release()
		return results, READY

	def faceToVector(face):
		# Turn a face image(?) into a feature vector somehow
		return []