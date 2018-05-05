from pipeline import DataMiner, SearchEngine, READY, ERROR
from sets import Set
import numpy as np
import timeit
import random

import cv2, os


class FaceList:
	""" Binds a list of captured faces to the time index where it was captured
	"""
	def __init__(self, time):
		self.time = time
		self.content = []
		self.cluster = []
		self.LBP_Vectors = []

class FaceChunk:
	""" A list of which face cluster IDs appear within a given chunk of time
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
		# Total number of faces found (to print to console)
		faceCount = 0

		results = []
		cap = cv2.VideoCapture(data)
		if not cap.isOpened():
			return results, ERROR

		fps = cap.get(cv2.CAP_PROP_FPS) # video FPS


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
				faceCount += len(chunk.content)

			# advance video capture position
			currFrame += grain
			cap.set(cv2.CAP_PROP_POS_FRAMES, currFrame)

		cap.release()

		print "VideoFaceFounder found a total of " + str(faceCount) + " faces."

		return results, READY

	def findFaces(self, frame, cascade):
		grey = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

		detectedFaces = []
		i = 0

		for cascade in self.cascades:
			faces = cascade.detectMultiScale(grey, scaleFactor=1.1, minSize=(80,80), minNeighbors=5)

			# store crops of faces

			if len(faces) > 0:
				print "Found " + str(len(faces)) + " faces."
			
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
		print "Encoding images as LBP vectors"
		LBPVecCount = 0
		imageCount = 0

		for chunk in data:
			# Get all faces from this chunk/frame
			faces = []
			for face in chunk.content:
				faces.append(face)

			# Set up and train OpenCV's LBPH recognizer
			# (to get its feature encodings)
			r = cv2.face.LBPHFaceRecognizer_create()
			# Train argument requires labels (but they won't be used
			# and don't matter or affect this process)
			randLabels = range(0,len(faces))
			r.train(faces, np.asarray(randLabels))
			# Retrieve encoded features
			LBP_vectors = r.getHistograms()
			# Format features for sklearn classifier
			LBP_vectors = [x.tolist() for x in LBP_vectors]
			LBP_vectors = [x[0] for x in LBP_vectors]

			# Populate LBP_Vector list in the chunk
			chunk.LBP_Vectors.extend(LBP_vectors)

			# Update counts for console output
			imageCount += len(faces)
			LBPVecCount += len(LBP_vectors)

		print "Generated " + str(LBPVecCount) + " LBP vectors for " + str(imageCount) + " images."
		# Return updated list of chunks
		return data, READY

class FaceClusterer(DataMiner):

	def __init__(self, tmpDir='/tmp/faceoutput/', n_clusters=None):
		DataMiner.__init__(self, tmpDir)

		self.n_clusters = n_clusters
		from sklearn.cluster import AffinityPropagation, KMeans, DBSCAN

		if n_clusters is not None:
			# If a number of clusters was provided, use KMeans clustering
			self.clf = KMeans(n_clusters=n_clusters, n_jobs=-1)
		else:
			# Otherwise, try Affinity Propagation clustering
			self.clf = AffinityPropagation(damping=0.99, max_iter=80, convergence_iter=200)

	def build(self, data):
		""" Receives list of FaceLists holding LBP representations.  If no value for k is set,
			Samples are clustered by passing messages between pairs of samples (LBP vectors)
			until convergence or max iterations are reached (see report for more detail on Affinity Propagation).

			If number of clusters is set, KMeans clustering is used with the provided value, iteratively fitting
			the centroids to better fit their neighbourhoods.  In an attempt to avoid convergence to
			local minima, this implementation of k-means uses K-means++ initialization, which ensures a sufficient
			distance between centroids.  This has proven to provide better results than when randomly positioning
			centroids at initialization.

			Returns list consisting of [k, FaceList0, ..., FaceListn]
		"""
		if self.n_clusters is None:
			print "Number of clusters not set, the clustering algorithm will estimate the number of clusters."
		else:
			print "Number of clusters set, using k-means clustering with provided value."

		clf = self.clf

		# Get all faces from the list of chunks, and the number of
		# elements in each LBP vector list
		face_data = []
		for chunk in data:
			for LBP_vec in chunk.LBP_Vectors:
				face_data.append(LBP_vec)

		# Cluster the faces with Affinity Propagation
		clf.fit(face_data)

		# Get cluster labels for each LBP vector from the clustering algorithm
		# (labels are returned corresponding to the order of input data)
		labels = clf.labels_.tolist()
		# Get number of clusters
		numClust = clf.cluster_centers_.shape[0]

		# Assign cluster labels to faces
		for chunk in data:
			for face in chunk.content:
				chunk.cluster.append(labels.pop(0))

		print "All faces assigned to one of " + str(numClust) + " clusters."

		retList = [numClust]
		retList.extend(data)

		return retList, READY

class FaceSearchMiner(DataMiner):
	def __init__(self, chunkSize=3, faceFolder='./face/', faceLimit=3):
		self.chunkSize = chunkSize # ultimate length of chunks
		self.faceFolder = faceFolder # folder for outputting faces
		self.faceLimit = faceLimit # max number of faces per cluster
		if not os.path.isdir(faceFolder):
			os.makedirs(faceFolder)

	def build(self, data):
		""" Receives list of [clusterCount, FaceList0, ..., FaceListn]
			Selects up to faceLimit images representing each cluster and outputs it to
			faceFolder/[index].png
			Returns two-item list: [[], {}]
				- List of cluster counts ([3, 2, 1] indicates cluster 0 has 1 image, cluster
				1 has 2 and cluster 3 has 1) - this is read from the corpus to let the
				frontend know how many images it should expect in faceFolder.
				- reverse-indexed dict of Clusters by clusterID, containing FaceChunks with
				startTime and endTime.
		"""
		
		clusters = {}
		faceExamples = {}

		# sliding window for current chunk
		start = 0
		end = self.chunkSize

		for face in data[1:]:
			# Do we need to move window along?
			while end < face.time:				
				start = end
				end += self.chunkSize

			for cluster in range(0, len(face.clusters)):
				# get cluster id and face image
				clusterID = face.clusters[cluster]
				face = face.content[cluster]

				# add a new cluster indexed by current ID if necessary
				if face.clusters[cluster] not in clusters:
					clusters[cluster] = []
					faceExamples[cluster] = []

				clusters[clusterID].append(FaceChunk(start, end))
				faceExamples[clusterID].append(face)

		# Pick n < faceLimit faces to represent this cluster in the frontend

		clusterCounts = []
		for clusterID in range(0, len(faceExamples)):
			
			if len(faceExamples[clusterID]) > self.faceLimit:
				faceExamples[clusterID] = random.sample(faceExamples[clusterID], self.faceLimit)

			count = len(faceExamples[clusterID])
			clusterCounts.append(count)
			
			# save face images for this cluster
			for faceID in range(0, count):
				face = faceExamples[clusterID][faceID]
				filename = self.faceFolder + str(clusterID) + "_" + str(faceID)
				cv2.imwrite(filename, face)

		return [clusterCounts, clusters], READY

class FaceSearch(SearchEngine):
	def performSearch(self, corpus, terms):
		""" Return a set of start and end times encompassing the union of
			all classes referred to in terms.
			Expects a two-element list as output from FaceSearchMiner:
			[[clusterCounts], {searchcorpus}]
			Returns a list of FaceChunks for the clusters requested.
		"""

		results = Set() # only want unique results
		
		for term in terms:
			term = int(term)
			if term not in corpus[1]:
				continue
			for result in corpus[1][term]:
				results.add(result)
		
		return results


# Test functions
def save_images(faceLists):
	"""
	Saves images of extracted faces to the current directory.


	:param faceLists: a list of FaceList objects
	:return: List of file names
	"""
	fnames = []
	for c in chunks:
		faceInd = 0
		for face in c.content:
			fname = "frame_" + str(chunks.index(c)) + "_face_" + str(faceInd) + ".png"
			fnames.append(fname)
			cv2.imwrite(fname, face)
			faceInd += 1
	return fnames

def save_clusters(clusterChunks, baseDir="./clusters/"):
	"""
		Save images belonging to each cluster in a folder representing said cluster.

	:param clusterChunks: output from FaceCluster
	:param baseDir: Base directory in which to save cluster directories
	:return:
	"""
	numClusters = clusterChunks.pop(0)
	clusterDirs = {}

	# Make base directory
	if not os.path.exists(baseDir):
		os.makedirs(baseDir)

	# Make a directory for each cluster
	for c in range(0, numClusters):
		clusterDir = baseDir + 'Cluster '+str(c)+'/'
		clusterDirs[c] = clusterDir
		if not os.path.exists(clusterDir):
			os.makedirs(clusterDir)
		else:
			# Delete content if it exists
			for f in os.listdir(clusterDir):
				path = os.path.join(clusterDir, f)
				try:
					if os.path.isfile(path):
						os.unlink(path)
				except Exception as e:
					print e

	# Save cluster images
	image_paths = save_images(clusterChunks)
	clusters = []

	for chunk in clusterChunks:
		for clusterLabel in chunk.cluster:
			clusters.append(clusterLabel)

	# Move images to appropriate cluster dirs
	for i in range(0, len(image_paths)):
		clusterDir = clusterDirs[clusters[i]]
		try:
			os.rename(image_paths[i], clusterDir+image_paths[i])
		except Exception as e:
			print "We have an issue:"
			print e
			print "Moving on..."


if __name__ == '__main__':
	tempDir = '/tmp/faceoutput/'
	#testVidPath = './testdata/wouldILieToYouClip.mp4'
	testVidPath = './testdata/Richard-Ayoade-Krishnan-Guru-Murthy.mp4'

	if not os.path.isdir(tempDir):
		os.makedirs(tempDir)

	ff = VideoFaceFinder(tempDir)
	fv = FaceVectoriser()

	fc = FaceClusterer(tmpDir='./Frontend-Web/faces/')#, n_clusters=7)
	fm = FaceSearchMiner()
	fs = FaceSearch()

	# Find faces
	chunks, status = ff.build(testVidPath)
	print "Face Finder produced " + str(len(chunks)) + " chunks."

	#save_images(chunks)

	# Convert face images to LBP feature vectors
	processedChunks, status = fv.build(chunks)
	print len(processedChunks), processedChunks[0]

	# Get list of chunks where cluster list is populated with cluster ids for each face
	# in the chunk data.
	clusterAssignedChunks, status = fc.build(processedChunks)

	print "Created " + str(clusterAssignedChunks[0]) + " clusters."

	# Save a copy of FaceCluster output
	#import pickle
	#pickle.dump(clusterAssignedChunks, open("./testdata/FaceClusterer_output.p", "wb"))

	save_clusters(clusterAssignedChunks)
	print "clusters saved."

	exit(0)
