import requests
from fake_useragent import FakeUserAgent
import json

headers = {
    'user-agent': FakeUserAgent().random
}

class Solar:
    def __init__(self, symbol):
        self._SYMBOL = symbol.upper()

    def fetch_data(self):
        url = 'https://api.solarstudios.co/pools/info/list?poolType=standard&poolSortField=default&sortType=desc&pageSize=100&page=1'
        response = requests.get(url, headers=headers)
        data = json.loads(response.text)
        self._DATA = data['data']['data']
        self._poolActivity = {}
        self._tvlData = {}

    def bestYield24(self):
        result = {}
        for pool in self._DATA:
            symbols = {pool['mintA']['symbol'].upper(), pool['mintB']['symbol'].upper()}
            pool_id = pool['id']
            pool_url = f"https://app.solarstudios.co/pool/{pool_id}"
            daily_yield = round(pool['day']['apr'] / 365, 3)
            tvl = pool.get('tvl', 0)
            volume = pool['day'].get('volume', 0)
            activity = round(volume / tvl, 3) if tvl else 0

            if {'ETH', 'TETH'} == symbols:
                key = f"ETH/tETH (Solar) : {daily_yield}％"
                result[key] = {pool_url}
                self._poolActivity[key] = activity
                self._tvlData[key] = int(round(tvl,0))
            elif {'ETH', 'USDC'} == symbols:
                key = f"ETH/USDC (Solar) | {daily_yield}％"
                result[key] = {pool_url}
                self._poolActivity[key] = activity
                self._tvlData[key] = int(round(tvl,0)) 

        return result

    def poolActivities(self):
        return self._poolActivity
    def tvlData(self):
        return self._tvlData




