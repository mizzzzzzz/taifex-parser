import requests
import shutil
import datetime
from bs4 import BeautifulSoup
import pandas as pd

import pytesseract
from PIL import Image
import cv2

import captchaSolver

class TWOptionParser():
	def __init__(self):
		self.selectedCode = ''
		self.selectedCommodity = ''
		self.selectedCommodity2 = ''
		self.selectedSettleMonth = ''
		self.selectedType = ''
		self.captcha = '000000'
		self.date = datetime.datetime.now().strftime('%Y%m%d')    
		#self.date = "20181001"        
		self.solver = captchaSolver.CaptchaSolver('captcha_model.hdf5')

	def start(self):
		self.prepareData()
		#self.postDailyOption()

	def prepareData(self):
		#self.getMarketCode()
		self.getCaptcha()
		#self.getCommodityList()
		#self.getSettleMonth()
		#self.getType()

	def getCaptcha(self):
		res = requests.get('http://www.taifex.com.tw/cht/captcha', stream=True)

		if res.status_code != requests.codes.ok:
			raise Exception("Get Captcha Failed")
		
		with open('captcha.jpg', 'wb') as out_file:
			res.raw.decode_content = True
			shutil.copyfileobj(res.raw, out_file)

		self.captcha = self.resolveCaptcha('captcha.jpg')
		print(self.captcha)
		
		#os.remove('captcha.jpg')
	def resolveCaptcha(self, imagePathStr):
		return self.solver.solve(imagePathStr)

	# def resolveCaptcha(self, imagePathStr):
		# img = cv2.imread('captcha.jpg')
		# img = cv2.fastNlMeansDenoisingColored(img, None, 30, 30, 7, 51)
		# img = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
		# cv2.imwrite('ok.jpg', img)
		# cv2.imshow('image', img)

		# return pytesseract.image_to_string(img, config='--psm 7 digits')
	
	def getMarketCode(self):
		self.printBreakLine()
		
		res = requests.get('http://www.taifex.com.tw/cht/3/dailyOptions')

		if res.status_code != requests.codes.ok:
			raise Exception("Get Market Code Failed")

		soup = BeautifulSoup(res.text, features="html.parser")
		marketCode = [str(x.text) for x in soup.find(id="MarketCode").find_all('option')]
		
		for index, code in enumerate(marketCode):
			if index != 0:
				print(index, ": ", code)

		while self.selectedCode == '':
			self.selectedCode = input("交易時段: ")

	def getCommodityList(self):
		self.printBreakLine()
		
		payload = {
			'queryDate': str(self.date),
			'marketcode': 0
		}

		res = requests.get('http://www.taifex.com.tw/cht/3/getFcmOptcontract.do', params=payload)
		
		if res.status_code != requests.codes.ok:
			raise Exception("Get Commodity List Failed")

		for com in res.json()['commodityList']:
			print(com['FDAILYR_KIND_ID'], com['FDAILYR_PROD_SUBTYPE'], com['FDAILYR_NAME'])
		for com in res.json()['commodity2List']:
			print(com['FDAILYR_KIND_ID'], com['FDAILYR_PROD_SUBTYPE'], com['FDAILYR_NAME'])
		
		input_com = input("契約: ")
		if any(input_com == com['FDAILYR_KIND_ID'] for com in res.json()['commodity2List']):
			self.selectedCommidity = 'STO'
			self.selectedCommidity2 = input_com
		else:
			self.selectedCommidity = input_com
			self.selectedCommidity2 = ''

	def getSettleMonth(self):
		self.printBreakLine()

		payload = {
			'queryDate': str(self.date),
			'marketcode': 0,
			'commodityId': self.selectedCommodity
		}
		res = requests.get('http://www.taifex.com.tw/cht/3/getFcmOptSetMonth.do', params=payload)
		
		if res.status_code != requests.codes.ok:
			raise Exception("Get Settle Month Failed")
		
		for setMon in res.json()['setMonList']:
			print(setMon['FDAILYR_SETTLE_MONTH'])
			
		self.selectedSettleMonth = input("到期月份(週別): ")

	def getType(self):
		self.printBreakLine()

		payload = {
			'queryDate': str(self.date),
			'marketcode': 0,
			'commodityId': str(self.selectedCommodity),
			'settlemon': str(self.selectedSettleMonth)
		}
		res = requests.get('http://www.taifex.com.tw/cht/3/getFcmOptionsType.do', params=payload)
		
		if res.status_code != requests.codes.ok:
			raise Exception("Get Type Failed")
		
		for typeId in res.json()['typeList']:
			print(typeId['FDAILYR_PC_CODE'])
			
		self.selectedType = input("買/賣權: ")

	def postDailyOption(self):
		self.printBreakLine()

		payload = {
			'captcha': self.captcha,
			'commodity_id2t': self.selectedCommidity2,
			'commodity_idt': self.selectedCommidity,
			'commodityId': self.selectedCommidity,
			'commodityId2': self.selectedCommidity2,
			'curpage': '',
			'doQuery': '1',
			'doQueryPage': '',
			'marketcode': self.selectedCode,
			'MarketCode': self.selectedCode,
			'pccode': self.selectedType,
			'queryDate': self.date,
			'queryDateAh': self.date,
			'settlemon': self.selectedSettleMonth,
			'totalpage': ''
		}
		self.printCurrentSetting()
		
		res = requests.post('http://www.taifex.com.tw/cht/3/dailyOptions', data=payload)
		
		if res.status_code != requests.codes.ok:
			raise Exception("Get Type Failed")

		#print(res.text)

	def printCurrentSetting(self):
		print('交易時段: ', self.selectedCode)
		print('契約: ', self.selectedCommidity)
		if self.selectedCommidity == 'STO':
			print('契約2: ', self.selectedCommidity2)
		print('到期月份(週別): ', self.selectedSettleMonth)
		print('買/賣權: ', self.selectedType)
		print('Captcha: ', self.captcha)
		
	def printBreakLine(self):
		print('=================================')
		
def main():  
	parser = TWOptionParser()
	parser.start()
main()
