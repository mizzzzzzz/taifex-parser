import rfc6266
import requests
import shutil
import datetime
from bs4 import BeautifulSoup
import pandas as pd
import os

from urllib.request import urlretrieve

from PIL import Image
import cv2

import captchaSolver

class TWOptionParser():
    def __init__(self):
        self.TargetURL = 'http://www.taifex.com.tw/cht/3/dailyOptions'
        self.DownURL = 'http://www.taifex.com.tw/cht/3/dailyOptionsDown'
        self.MarketCode = ''
        self.Commodity = ''
        self.Commodity2 = ''
        self.SettleMonth = ''
        self.Type = ''
        self.Captcha = ''
        self.QueryDate = ''
        self.QueryDateAh = ''
        self.solver = captchaSolver.CaptchaSolver('Captcha_model.hdf5')

    def start(self):
        self.getSession()
        self.prepareData()
        #self.mockData()
        self.postDailyOption()
        self.postDownloadCsv()

    def mockData(self):
        self.MarketCode = '0'
        self.Commodity = 'STO'
        self.Commodity2 = 'OOO'
        self.SettleMonth = '201811'
        self.Type = 'C'
        self.QueryDate = '20181023'
        self.QueryDateAh = '20181023'
        self.getCaptcha()

    def getSession(self):
        self.session = requests.session()
        self.header = {
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Encoding': 'gzip, deflate',
            'Accept-Language': 'zh-TW,zh;q=0.8,en-US;q=0.5,en;q=0.3',
            'Connection': 'keep-alive',
            'Content-Type': 'application/x-www-form-urlencoded',
            'Host': 'www.taifex.com.tw',
            'Referer': 'http://www.taifex.com.tw/cht/3/dailyOptions',
            'Upgrade-Insecure-Requests': '1',
            'User-Agent': 'Mozilla/5.0 (Windows NT 6.3; Win64; x64; rv:62.0) Gecko/20100101 Firefox/62.0'
        }
        self.getCaptcha()


    def prepareData(self):
        self.getQueryDate()
        self.getMarketCode()
        self.getCommodityList()
        self.getSettleMonth()
        self.getType()

    def getQueryDate(self):
        self.printBreakLine()
        
        res = self.session.get(self.TargetURL, headers=self.header)

        if res.status_code != requests.codes.ok:
            raise Exception("Get Query Data Failed")

        soup = BeautifulSoup(res.text, features="html.parser")
        self.QueryDate = soup.find(id="queryDate").get('value')
        self.QueryDateAh = soup.find(id="queryDateAh").get('value')

    def getMarketCode(self):
        self.printBreakLine()

        res = self.session.get(self.TargetURL, headers=self.header)

        if res.status_code != requests.codes.ok:
            raise Exception("Get Market Code Failed")

        soup = BeautifulSoup(res.text, features="html.parser")
        marketCode = [str(x.text) for x in soup.find(id="MarketCode").find_all('option')]
        
        for index, code in enumerate(marketCode):
            if index != 0:
                print(index - 1, ": ", code)

        while self.MarketCode == '':
            self.MarketCode = input("MarketCode: ")

    def getCommodityList(self):
        self.printBreakLine()
        
        payload = {
            'queryDate': str(self.QueryDate if self.MarketCode == '0' else self.QueryDateAh),
            'marketcode': 0
        }

        res = self.session.get('http://www.taifex.com.tw/cht/3/getFcmOptcontract.do', params=payload, headers=self.header)
        
        if res.status_code != requests.codes.ok:
                raise Exception("Get Commodity List Failed")
                for com in res.json()['commodityList']:
                        print(com['FDAILYR_KIND_ID'], com['FDAILYR_PROD_SUBTYPE'], com['FDAILYR_NAME'])
        for com in res.json()['commodity2List']:
            print(com['FDAILYR_KIND_ID'], com['FDAILYR_PROD_SUBTYPE'], com['FDAILYR_NAME'])
        
        input_com = input("Commodity: ")
        if any(input_com == com['FDAILYR_KIND_ID'] for com in res.json()['commodity2List']):
            self.Commodity = 'STO'
            self.Commodity2 = input_com
        else:
            self.Commodity = input_com
            self.Commodity2 = ''

    def getSettleMonth(self):
        self.printBreakLine()

        payload = {
            'queryDate': str(self.QueryDate if self.MarketCode == '1' else self.QueryDateAh),
            'marketcode': 0,
            'commodityId': self.Commodity2 if self.Commodity == 'STO' else self.Commodity
        }

        res = self.session.get('http://www.taifex.com.tw/cht/3/getFcmOptSetMonth.do', params=payload, headers=self.header)
        
        if res.status_code != requests.codes.ok:
            raise Exception("Get Settle Month Failed")

        for setMon in res.json()['setMonList']:
            print(setMon['FDAILYR_SETTLE_MONTH'])
            
        self.SettleMonth = input("Settle Month: ")

    def getType(self):
        self.printBreakLine()

        payload = {
            'queryDate': str(self.QueryDate if self.MarketCode == '1' else self.QueryDateAh),
            'marketcode': 0,
            'commodityId': self.Commodity2 if self.Commodity == 'STO' else self.Commodity,
            'settlemon': str(self.SettleMonth)
        }
        res = self.session.get('http://www.taifex.com.tw/cht/3/getFcmOptionsType.do', params=payload, headers=self.header)
        
        if res.status_code != requests.codes.ok:
            raise Exception("Get Type Failed")
        
        for typeId in res.json()['typeList']:
            print(typeId['FDAILYR_PC_CODE'])
            
        self.Type = input("Type: ")

    def getCaptcha(self):
        res = self.session.get('http://www.taifex.com.tw/cht/captcha', stream=True, headers=self.header)

        if res.status_code != requests.codes.ok:
            raise Exception("Get Captcha Failed")
        
        with open('Captcha.jpg', 'wb') as out_file:
            res.raw.decode_content = True
            shutil.copyfileobj(res.raw, out_file)

        self.cookies = res.cookies
        self.Captcha = self.resolveCaptcha('Captcha.jpg')
        #img = cv2.imread('Captcha.jpg')
        #cv2.imshow('image', img)
        print('Captcha: ', self.Captcha)    
        #os.remove('Captcha.jpg')

    def resolveCaptcha(self, imagePathStr):
        return self.solver.solve(imagePathStr)

    def postDailyOption(self):
        self.printBreakLine()

        payload = {
            'captcha': self.Captcha,
            'commodity_id2t': self.Commodity2,
            'commodity_idt': self.Commodity,
            'commodityId': self.Commodity,
            'commodityId2': self.Commodity2,
            'curpage': '',
            'doQuery': '1',
            'doQueryPage': '',
            'marketcode': self.MarketCode,
            'MarketCode': self.MarketCode,
            'pccode': self.Type,
            'queryDate': self.QueryDate,
            'queryDateAh': self.QueryDateAh,
            'settlemon': self.SettleMonth,
            'totalpage': ''
        }

        res = self.session.post(self.TargetURL, data=payload, headers=self.header, cookies=self.cookies)
        
        if res.status_code != requests.codes.ok:
            raise Exception("Post Option Failed")

    def postDownloadCsv(self):
        print('.', end='')
        payload = {
            'captcha': '',
            'commodity_id2t': self.Commodity2,
            'commodity_idt': self.Commodity,
            'commodityId': self.Commodity,
            'commodityId2': self.Commodity2,
            'curpage': '1',
            'totalpage': '1',
            'doQuery': '1',
            'doQueryPage': '',
            'marketcode': self.MarketCode,
            'MarketCode': self.MarketCode,
            'pccode': self.Type,
            'queryDate': self.QueryDate,
            'queryDateAh': self.QueryDateAh,
            'settlemon': self.SettleMonth
        }

        res = self.session.post(self.DownURL, data=payload, headers=self.header, cookies=self.cookies)
        
        if res.status_code != requests.codes.ok:
            raise Exception("Post Download Failed")

        if res.headers.get('Content-Disposition') == None:
            print('Download Failed', self.MarketCode, self.Commodity, self.Commodity2, self.SettleMonth, self.Type)
            return

        fileName = rfc6266.parse_requests_response(res).filename_unsafe

        with open(fileName, 'wb') as fd:
            for chunk in res.iter_content(256):
                fd.write(chunk)

    def printBreakLine(self):
        print('=================================')
        
def main():  
    parser = TWOptionParser()
    parser.start()
main()
