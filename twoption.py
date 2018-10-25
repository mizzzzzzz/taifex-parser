import rfc6266
import requests
import shutil
from bs4 import BeautifulSoup
import pandas as pd
import os
import time

from PIL import Image
import cv2

import captchaSolver

class TWOptionParser():
    
    def __init__(self, solver):
        print('Parse TW Option')
        self.directory = './twoption/'
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
        self.solver = solver
        self.createFolder()

    def createFolder(self):
        if not os.path.exists(self.directory):
            os.makedirs(self.directory)

    def auto(self):
        start_time = time.time()
        self.getSession()
        self.getQueryDate()
        self.getMarketCode()
        print('\tDone!')
        print("Elapsed time:", time.time() - start_time, "seconds")

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

    def getQueryDate(self):
        res = self.session.get(self.TargetURL, headers=self.header)

        if res.status_code != requests.codes.ok:
            raise Exception("Get Query Data Failed")

        soup = BeautifulSoup(res.text, features="html.parser")
        self.QueryDate = soup.find(id="queryDate").get('value')
        self.QueryDateAh = soup.find(id="queryDateAh").get('value')

    def getMarketCode(self):
        res = self.session.get(self.TargetURL, headers=self.header)

        if res.status_code != requests.codes.ok:
            raise Exception("Get Market Code Failed")

        soup = BeautifulSoup(res.text, features="html.parser")
        marketCode = [str(x.text) for x in soup.find(id="MarketCode").find_all('option')]
        
        for index, code in enumerate(marketCode):
            if index != 0:
                self.MarketCode = index - 1
                self.getCommodityList()

    def getCommodityList(self):
        payload = {
            'queryDate': str(self.QueryDate if self.MarketCode == '0' else self.QueryDateAh),
            'marketcode': 0
        }

        res = self.session.get('http://www.taifex.com.tw/cht/3/getFcmOptcontract.do', params=payload, headers=self.header)
        
        if res.status_code != requests.codes.ok:
            raise Exception("Get Commodity List Failed")


        for com in res.json()['commodityList']:
            self.Commodity = com['FDAILYR_KIND_ID']
            self.Commodity2 = ''
            self.getSettleMonth()

        for com in res.json()['commodity2List']:
            self.Commodity = 'STO'
            self.Commodity2 = com['FDAILYR_KIND_ID']
            self.getSettleMonth()

    def getSettleMonth(self):
        payload = {
            'queryDate': str(self.QueryDate if self.MarketCode == '1' else self.QueryDateAh),
            'marketcode': 0,
            'commodityId': self.Commodity2 if self.Commodity == 'STO' else self.Commodity
        }

        res = self.session.get('http://www.taifex.com.tw/cht/3/getFcmOptSetMonth.do', params=payload, headers=self.header)
        
        if res.status_code != requests.codes.ok:
            raise Exception("Get Settle Month Failed")

        for setMon in res.json()['setMonList']:
            self.SettleMonth = setMon['FDAILYR_SETTLE_MONTH']
            self.getType()


    def getType(self):
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
            self.Type = typeId['FDAILYR_PC_CODE']
            self.postDailyOption()
            self.postDownloadCsv()

    def getCaptcha(self):
        res = self.session.get('http://www.taifex.com.tw/cht/captcha', stream=True, headers=self.header)

        if res.status_code != requests.codes.ok:
            raise Exception("Get Captcha Failed")
        
        with open(self.directory + 'Captcha.jpg', 'wb') as out_file:
            res.raw.decode_content = True
            shutil.copyfileobj(res.raw, out_file)

        self.cookies = res.cookies
        self.Captcha = self.resolveCaptcha(self.directory + 'Captcha.jpg')
        #img = cv2.imread('Captcha.jpg')
        #cv2.imshow('image', img)
        print('Captcha: ', self.Captcha)    
        #os.remove('Captcha.jpg')

    def resolveCaptcha(self, imagePathStr):
        return self.solver.solve(imagePathStr)

    def postDailyOption(self):
        payload = {
            'captcha': str(self.Captcha),
            'commodity_id2t': str(self.Commodity2),
            'commodity_idt': str(self.Commodity),
            'commodityId': str(self.Commodity),
            'commodityId2': str(self.Commodity2),
            'curpage': '',
            'doQuery': '1',
            'doQueryPage': '',
            'marketcode': str(self.MarketCode),
            'MarketCode': str(self.MarketCode),
            'pccode': str(self.Type),
            'queryDate': str(self.QueryDate),
            'queryDateAh': str(self.QueryDateAh),
            'settlemon': str(self.SettleMonth),
            'totalpage': ''
        }

        res = self.session.post(self.TargetURL, data=payload, headers=self.header, cookies=self.cookies)
        
        if res.status_code != requests.codes.ok:
            raise Exception("Post Option Failed")

    def postDownloadCsv(self):
	    print('.', end='')
        payload = {
            'captcha': '',
            'commodity_id2t': str(self.Commodity2),
            'commodity_idt': str(self.Commodity),
            'commodityId': str(self.Commodity),
            'commodityId2': str(self.Commodity2),
            'curpage': '1',
            'doQuery': '1',
            'doQueryPage': '',
            'marketcode': str(self.MarketCode),
            'MarketCode': str(self.MarketCode),
            'pccode': str(self.Type),
            'queryDate': str(self.QueryDate),
            'queryDateAh': str(self.QueryDateAh),
            'settlemon': str(self.SettleMonth),
            'totalpage': ''
        }

        res = self.session.post(self.DownURL, data=payload, headers=self.header, cookies=self.cookies)
        
        if res.status_code != requests.codes.ok:
            raise Exception("Post Download Failed")

        if res.headers.get('Content-Disposition') == None:
            print('Download Failed', self.MarketCode, self.Commodity, self.Commodity2, self.SettleMonth, self.Type)
            return

        fileName = rfc6266.parse_requests_response(res).filename_unsafe

        with open(self.directory + fileName, 'wb') as fd:
            for chunk in res.iter_content(256):
                fd.write(chunk)

    def printBreakLine(self):
        print('=================================')
        
def main():
    parser = TWOptionParser(captchaSolver.CaptchaSolver('Captcha_model.hdf5'))
    parser.auto()

if __name__ == '__main__':
    main()
