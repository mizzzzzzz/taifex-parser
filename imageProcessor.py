from PIL import Image
import cv2

from skimage import transform, data
import matplotlib.pyplot as plt

import numpy as np
from sklearn.preprocessing import binarize

class ImageProcessor:
	width = 48
	height = 140
	def setRespaceSize(self, w, h):
		self.width = w
		self.height = h
		
	def process(self, imgPath):
		plt.rcParams.update({'figure.max_open_warning': 0}) #fix the memory error

		img = cv2.imread(imgPath)
		dst = cv2.fastNlMeansDenoisingColored(img, None, 30, 30 ,7 ,21)
		origHeight, origWidth, origChannel = img.shape
		
		plt.figure(figsize=(origWidth, origHeight), dpi=100)
		plt.axis('off')
		plt.imshow(dst)
		plt.subplots_adjust(top=1, bottom=0, left=0, right=1, hspace=0, wspace=0)
		plt.savefig(imgPath, dpi=10)

		img = cv2.imread(imgPath)	
		ret, thresh = cv2.threshold(img, 127, 255, cv2.THRESH_BINARY_INV)
		plt.imshow(thresh)
		
		plt.subplots_adjust(top=1, bottom=0, left=0, right=1, hspace=0, wspace=0)
		plt.imshow(thresh)

		newdst = transform.resize(thresh, (self.width, self.height), mode='reflect', anti_aliasing=True)
		plt.close()
		plt.figure(figsize=(self.height, self.width), dpi=100)
		plt.axis('off')
		plt.imshow(newdst)

		plt.subplots_adjust(top=1, bottom=0, left=0, right=1, hspace=0, wspace=0)
		plt.savefig(imgPath, dpi=1)
		plt.close()