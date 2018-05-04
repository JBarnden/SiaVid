from pipeline import DataMiner, SearchEngine, READY, ERROR
from sklearn.cluster import AffinityPropagation
from sets import Set
import timeit

import cv2, os

class FaceList:
	""" Binds a list of captured faces to the time index where it was captured
	"""
	def __init__(self, time):
		self.time = time
		self.content = []
		self.cluster = None

class FaceChunk:
	""" A list of which faces appear within a given chunk of time
	"""
	def __init__(self):
		self.__init__(None, None, None)

	def __init__(self, startTime, endTime):
		self.startTime = startTime
		self.endTime = endTime

class VideoFaceFinder(DataMiner):
	""" Takes a video and returns a list of FaceLists holding extracted faces
	"""

	def __init__(self, tempDir = './tmp/', sampleRate = 0.5, outputSize = (100,100), cascades = None):
		DataMiner.__init__(self, tempDir)
		self.sampleRate = sampleRate # number of samples per second
		self.outputSize = outputSize

		# This can be amended per-plugin
		if cascades != None:
			self.cascades = cascades
		else:
			self.cascades = [
				cv2.CascadeClassifier("./haar/haarcascade_frontalface_alt.xml"),
				cv2.CascadeClassifier("./haar/haarcascade_profileface.xml")
			]

	def build(self, data):
		""" Returns a list of time-indexed FaceLists holding Faces """

		results = []
		cap = cv2.VideoCapture(data)
		if not cap.isOpened():
			return results, ERROR

		fps = cap.get(cv2.cv.CV_CAP_PROP_FPS) # video FPS

		grain = fps/self.sampleRate # offset for sampleRate samples per second
		currFrame = 0 # starting frame

		while(cap.isOpened()): # loop through video in steps of size 'grain'
			print("Processing frame " + str(currFrame))

			ret, frame = cap.read()

			if ret == False: # have we run out of video?
				break

			# build a new FaceList with time index and 
			# add the list of discovered faces

			chunk = FaceList(currFrame/fps) 
			chunk.content = self.findFaces(frame, self.cascades)

			# If any extracted faces, store chunk for returning
			if len(chunk.content) > 0:
				results.append(chunk)

			# advance video capture position
			currFrame += grain
			cap.set(cv2.CV_CAP_PROP_POS_FRAMES, currFrame)

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
				face = grey[y:y+h, x:x+w]
				face = cv2.resize(face, self.outputSize, interpolation = cv2.INTER_CUBIC)

				detectedFaces.append(face)
				i += 1

		return detectedFaces


class FaceVectoriser(DataMiner):

	def build(self, data):
		"""
			Receives list of FaceLists with extracted face images, returns new list
			of FaceLists with LBP converted faces.
		"""

		output = []

		for chunk in data:
			newChunk = FaceList(chunk.time)

			# Get all faces from this chunk/frame
			faces = []
			for face in chunk.content:
				faces.append(face)

			# Set up and train OpenCV's LBPH recognizer
			# (to get its feature encodings)
			r = cv2.face.LBPHFaceRecognizer_create()
			r.train(faces)
			# Retrieve encoded features
			LBP_vectors = r.getHistograms()
			# Format features for sklearn classifier
			LBP_vectors = [x.tolist() for x in LBP_vectors]
			LBP_vectors = [x[0] for x in LBP_vectors]

			for LBP_vec in LBP_vectors:
				newChunk.content.append(LBP_vec)

			output.append(newChunk)
		
		return output, READY

class FaceClusterer(DataMiner):

	def __init__(self, damping=0.5, max_iter=300):
		DataMiner.__init__(self)
		# Initialize Affinity Propagation clustering algorithm with constructor assigned parameters
		self.clf = AffinityPropagation(damping=damping, max_iter=max_iter)

	def build(self, data):
		""" Receives list of FaceLists holding LBP representations.  Trains based on total set
			and then clusters presented faces using trained model.
			Returns list consisting of [k, FaceList0, ..., FaceListn]
		"""
		clf = self.clf

		# Get all faces from the list of chunks
		face_data = []
		for chunk in data:
			for LBP_vec in chunk.content:
				face_data.append(LBP_vec)

		# Cluster the faces
		clf.fit(face_data)

		# Get cluster labels from the clustering algorithm
		labels = clf.labels_

		return data, READY

class FaceSearchMiner(DataMiner):
	def __init__(self, chunkSize=3, faceFolder='./face/'):
		self.chunkSize = chunkSize # ultimate length of chunks
		self.faceFolder = faceFolder # folder for outputting faces
		if not os.path.isdir(faceFolder):
			os.makedirs(faceFolder)

	def build(self, data):
		""" Receives list of [clusterCount, FaceList0, ..., FaceListn]
			Selects one image representing each cluster and outputs it to faceFolder/[index].png
			Returns reverse-indexed dict of Clusters by clusterID, containing FaceChunks with
			startTime and endTime.
		"""
		
		clusters = {}

		# sliding window for current chunk
		start = 0
		end = self.chunkSize

		for face in data[1:]:
			# Do we need to move window along?
			while end < face.time:				
				start = end
				end += self.chunkSize

			# add a new cluster indexed by current ID if necessary
			if face.cluster not in clusters:
				clusters[face.cluster] = []

			clusters[face.cluster].append(FaceChunk(start, end))

		return clusters, READY

class FaceSearch(SearchEngine):
	def performSearch(self, corpus, terms):
		""" Return a set of start and end times encompassing the union of
			all classes referred to in terms.
		"""

		results = Set() # only want unique results
		
		for term in terms:
			term = int(term)
			if term not in corpus:
				continue
			for result in corpus[term]:
				results.add(result)
		
		return results

if __name__ == '__main__':
	tempDir = './tmp/faceoutput/'
	ff = VideoFaceFinder(tempDir)
	fv = FaceVectoriser()

	fc = FaceClusterer('./Frontend-Web/faces/')
	fm = FaceSearchMiner()
	fs = FaceSearch()

	if not os.path.isdir(tempDir):
		os.makedirs(tempDir)

	#chunks, status = ff.build('./tmp/wGkvyN6s9cY.mp4')
	#print len(chunks), chunks[0]
	#processedChunks, status = fv.build(chunks)
	#print len(processedChunks), processedChunks[0]

	#for i in range(0, len(chunks)):
		
	#	for j in range(0, len(chunks[i].content)):
	#		print("Outputting face " + str(j) + ", time: " + str(chunks[i].time))
	#		cv2.imwrite(tempDir + str(chunks[i].time) + "_" + str(j) + '.png', chunks[i].content[j])
	#		cv2.imwrite(tempDir + str(chunks[i].time) + "_p" + str(j) + '.png', processedChunks[i].content[j])

	input = [2, FaceList(49.0), FaceList(50.0), FaceList(50.0), FaceList(54.0), FaceList(71.0)]
	input[1].cluster = 0
	input[2].cluster = 0
	input[3].cluster = 1
	input[4].cluster = 0
	input[5].cluster = 1

	corpus, status = fm.build(input)

	result = fs.performSearch(corpus, ["1", "3"])

	print result
	for chunk in result:
		print chunk.startTime, chunk.endTime

	#ff.build('./tmp/wGkvyN6s9cY.mp4')
	#print timeit.timeit("ff.build('./tmp/wGkvyN6s9cY.mp4')", setup="from __main__ import FaceFinder; ff = FaceFinder('./tmp/faceoutput/')",number=1)
	
	
