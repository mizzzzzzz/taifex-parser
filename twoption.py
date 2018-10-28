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
                self.getCommodityList(index - 1)

    def getCommodityList(self, marketCode):
        payload = {
            'queryDate': str(self.QueryDate if marketCode == 0 else self.QueryDateAh),
            'marketcode': 0
        }

        res = self.session.get('http://www.taifex.com.tw/cht/3/getFcmOptcontract.do', params=payload, headers=self.header)
        
        if res.status_code != requests.codes.ok:
            raise Exception("Get Commodity List Failed")


        for com in res.json()['commodityList']:
            self.getSettleMonth(marketCode, com['FDAILYR_KIND_ID'], '')

        for com in res.json()['commodity2List']:
            self.getSettleMonth(marketCode, 'STO', com['FDAILYR_KIND_ID'])

    def getSettleMonth(self, marketCode, commodity, commodity2):
        payload = {
            'queryDate': str(self.QueryDate if marketCode == 0 else self.QueryDateAh),
            'marketcode': 0,
            'commodityId': commodity2 if commodity == 'STO' else commodity
        }

        res = self.session.get('http://www.taifex.com.tw/cht/3/getFcmOptSetMonth.do', params=payload, headers=self.header)
        
        if res.status_code != requests.codes.ok:
            raise Exception("Get Settle Month Failed")

        for setMon in res.json()['setMonList']:
            self.getType(marketCode, commodity, commodity2, setMon['FDAILYR_SETTLE_MONTH'])


    def getType(self, marketCode, commodity, commodity2, setMon):
        payload = {
            'queryDate': str(self.QueryDate if marketCode == 0 else self.QueryDateAh),
            'marketcode': 0,
            'commodityId': commodity if commodity == 'STO' else commodity,
            'settlemon': str(setMon)
        }
        res = self.session.get('http://www.taifex.com.tw/cht/3/getFcmOptionsType.do', params=payload, headers=self.header)
        
        if res.status_code != requests.codes.ok:
            raise Exception("Get Type Failed")
        
        for typeId in res.json()['typeList']:            
            self.postDailyOption(marketCode, commodity, commodity2, setMon, typeId['FDAILYR_PC_CODE'])
            self.postDownloadCsv(marketCode, commodity, commodity2, setMon, typeId['FDAILYR_PC_CODE'])

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

    def postDailyOption(self, marketCode, commodity, commodity2, setMon, pcCode):
        payload = {
            'captcha': str(self.Captcha),
            'commodity_id2t': str(commodity2),
            'commodity_idt': str(commodity),
            'commodityId': str(commodity),
            'commodityId2': str(commodity2),
            'curpage': '',
            'doQuery': '1',
            'doQueryPage': '',
            'marketcode': str(marketCode),
            'MarketCode': str(marketCode),
            'pccode': str(pcCode),
            'queryDate': str(self.QueryDate),
            'queryDateAh': str(self.QueryDateAh),
            'settlemon': str(setMon),
            'totalpage': ''
        }

        res = self.session.post(self.TargetURL, data=payload, headers=self.header, cookies=self.cookies)
        
        if res.status_code != requests.codes.ok:
            raise Exception("Post Option Failed")

    def postDownloadCsv(self, marketCode, commodity, commodity2, setMon, pcCode):
        print('.', end='')
        payload = {
            'captcha': '',
           'commodity_id2t': str(commodity2),
            'commodity_idt': str(commodity),
            'commodityId': str(commodity),
            'commodityId2': str(commodity2),
            'curpage': '1',
            'doQuery': '1',
            'doQueryPage': '',
            'marketcode': str(marketCode),
            'MarketCode': str(marketCode),
            'pccode': str(pcCode),
            'queryDate': str(self.QueryDate),
            'queryDateAh': str(self.QueryDateAh),
            'settlemon': str(setMon),
            'totalpage': ''
        }

        res = self.session.post(self.DownURL, data=payload, headers=self.header, cookies=self.cookies)
        
        if res.status_code != requests.codes.ok:
            raise Exception("Post Download Failed")

        if res.headers.get('Content-Disposition') == None:
            print('Download Failed', marketCode, commodity, commodity2, setMon, pcCode)
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
