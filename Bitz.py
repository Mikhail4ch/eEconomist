import requests
from fake_useragent import FakeUserAgent
import json

headers = {
    'user-agent': FakeUserAgent().random
}

class BITZ:
    def __init__(self):
        self._rewardPool = 720
        self._api = 'https://api.eclipsescan.xyz/v1/account/tokens?address=5FgZ9W81khmNXG8i96HSsG7oJiwwpKnVzmHgn9ZnqQja'
        self._currentAPR = 0
    def findOutApr(self):
        response = requests.get(self._api, headers=headers)
        data = json.loads(response.text)
        totalStaked = data['data']['tokens'][0]['balance']
        self._currentAPR = round(self._rewardPool/totalStaked*100,3)
        return self._currentAPR
    def aprForCalc(self):
        response = requests.get(self._api, headers=headers)
        data = json.loads(response.text)
        totalStaked = data['data']['tokens'][0]['balance']
        self._currentAPR = round(self._rewardPool/totalStaked*100,3)
        return self._currentAPR
    def annualAPR(self):
        response = requests.get(self._api, headers=headers)
        data = json.loads(response.text)
        totalStaked = data['data']['tokens'][0]['balance']
        self._currentAPR = round(self._rewardPool/totalStaked*365*100)
        return self._currentAPR
    def howMuchEarnDaily(self, staked):
        amount = staked * self.aprForCalc()
        return f'Daily you will earn:\n{round(amount/100,3)} $BITZ'
    def howMuchEarnWeekly(self,staked):
        amount = staked * self.aprForCalc()
        return f'Weekly you will earn:\n{round(amount/100*7,3)} $BITZ'
    def howMuchEarnMonthly(self,staked):
        amount = staked * self.aprForCalc()
        return f'Monthly you will earn:\n{round(amount/100*30.4167,3)} $BITZ'
    def howMuchYearly(self,staked):
        amount = staked * self.aprForCalc()
        return f'Annually you will earn:\n{round(amount/100*365,3)} $BITZ'




