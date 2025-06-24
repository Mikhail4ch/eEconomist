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
        self._totalStaked = None
        self._fetch_total_staked()

    def _fetch_total_staked(self):
        try:
            response = requests.get(self._api, headers=headers, timeout=8)
            data = response.json()
            # Look for $BITZ by symbol if possible!
            tokens = data['data']['tokens']
            for token in tokens:
                if token.get('symbol', '').upper() == 'BITZ':
                    self._totalStaked = float(token['balance'])
                    return
            # fallback: use first token (legacy)
            self._totalStaked = float(tokens[0]['balance'])
        except Exception as e:
            self._totalStaked = 0

    def _get_apr(self):
        if not self._totalStaked or self._totalStaked == 0:
            return 0
        return round(self._rewardPool / self._totalStaked * 100, 3)

    def findOutApr(self):
        apr = self._get_apr()
        return f'24H APR = {apr}％'

    def aprForCalc(self):
        return self._get_apr()

    def annualAPR(self):
        if not self._totalStaked or self._totalStaked == 0:
            return "Annual APR = N/A"
        apr = self._rewardPool / self._totalStaked * 365 * 100
        return f'Annual APR = {round(apr, 2)}％'

    def howMuchEarnDaily(self, staked):
        apr = self.aprForCalc()
        amount = staked * apr / 100
        return f'Daily you will earn:\n{round(amount, 3)} $BITZ'

    def howMuchEarnWeekly(self, staked):
        apr = self.aprForCalc()
        amount = staked * apr / 100 * 7
        return f'Weekly you will earn:\n{round(amount, 3)} $BITZ'

    def howMuchEarnMonthly(self, staked):
        apr = self.aprForCalc()
        amount = staked * apr / 100 * 30.417  # Avg days/month
        return f'Monthly you will earn:\n{round(amount, 3)} $BITZ'

    def howMuchYearly(self, staked):
        apr = self.aprForCalc()
        amount = staked * apr / 100 * 365
        return f'Annually you will earn:\n{round(amount, 3)} $BITZ'


