from PIL import Image, ImageDraw, ImageFont
import numpy as np
from keras.models import Sequential
from keras.models import load_model
from keras.models import Model
from keras.layers import Input, Dense, Dropout, Flatten, Conv2D, MaxPooling2D
from keras.utils  import np_utils
from keras.callbacks import ModelCheckpoint, EarlyStopping, TensorBoard
import csv
import time

import imageProcessor

class CaptchaSolver:
	numOfDigit = 6
	numOfDomain = 10
	def __init__(self, modelPath):
		self.model = load_model(modelPath)
		self.imageProcessor = imageProcessor.ImageProcessor()
	
	def solve(self, captchaPath):
		self.imageProcessor.process(captchaPath)
		captchaImg = np.stack([np.array(Image.open(captchaPath)) / 255.0])
		captcha = self.model.predict(captchaImg)
		result = ''
		for index in range(self.numOfDigit):
			result += str(np.argmax(captcha[index]))
		return result