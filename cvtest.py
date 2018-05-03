from pipeline import DataMiner, READY, ERROR

import cv2, os

class Face:
	def __init__(self):
		# set up face parameters here
		pass

class FaceChunk:
	def __init__(self, time):
		self.time = time
		self.content = []

class FaceFinder(DataMiner):
	def __init__(self, tempDir = './tmp/', sampleRate = 0.5, chunkSize = 5):
		DataMiner.__init__(self, tempDir)
		self.sampleRate = sampleRate # number of samples per second
		self.chunkSize = chunkSize # final length of chunks returned

		# This can be amended per-plugin
		self.cascades = [
			cv2.CascadeClassifier("haarcascade_frontalface_alt.xml"),
			cv2.CascadeClassifier("haarcascade_profileface.xml")
		]

	def build(self, data):
		""" Returns a list of time-indexed FaceChunks holding Faces """

		results = []
		cap = cv2.VideoCapture(data)
		fps = cap.get(cv2.cv.CV_CAP_PROP_FPS) # video FPS

		grain = fps/self.sampleRate # offset for x samples per second

		while(cap.isOpened()): # loop through video in steps of size 'grain'
			currFrame = cap.get(cv2.cv.CV_CAP_PROP_POS_FRAMES)

			print("Processing frame " + str(currFrame))

			ret, frame = cap.read()

			if ret == False: # have we run out of video?
				break

			cap.set(cv2.cv.CV_CAP_PROP_POS_FRAMES, currFrame + grain)

			# build a new FaceChunk with time index and 
			# add the list of discovered faces

			chunk = FaceChunk(currFrame/fps) 
			chunk.content = self.findFaces(frame, self.cascades)

			# output stuff for testing purposes only

			if len(chunk.content) > 0:
				cv2.imwrite(self.tempDir + str(chunk.time) + '.png', frame)

			i = 0
			for face in chunk.content:
				print("Outputting face " + str(i) + ", time: " + str(chunk.time))
				cv2.imwrite(self.tempDir + str(chunk.time) + "_" + str(i) + '.png', face)
				i += 1

			# output done

			# Chunk now contains a time index and a set of
			# images showing one cropped face each. We want
			# to convert these to feature vectors

			chunk.content = faceToVector(chunk.content)

			# return final processed faces
			results.append(chunk)

		cap.release()
		return results, READY

	def findFaces(self, frame, cascade):
		grey = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

		detectedFaces = []
		i = 0

		for cascade in self.cascades:
			faces = cascade.detectMultiScale(grey, scaleFactor=1.1, minSize=(80,80), minNeighbors=5)

			# store crops of faces

			if len(faces) > 0:
				print "Faces found."
			
			for x, y, w, h in faces:
				detectedFaces.append(grey[y:y+h, x:x+w])
				i += 1

		return detectedFaces


	def faceToVector(self, faces):
		# Turn a face image(?) into a feature vector somehow
		return faces


if __name__ == '__main__':
	ff = FaceFinder('./tmp/faceoutput/')
	if not os.path.isdir('./tmp/faceoutput/'):
		os.makedirs('./tmp/faceoutput/')

	ff.build('./tmp/wGkvyN6s9cY.mp4')
	
