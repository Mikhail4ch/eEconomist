import requests
from fake_useragent import FakeUserAgent
import json

headers = {
    'user-agent': FakeUserAgent().random
}

TOKEN_ADDRESS = {
    'ETH':  'So11111111111111111111111111111111111111112',
    'SOL':  'BeRUj3h7BqkbdfFU7FBNYbodgf8GCHodzKvF9aVjNNfL',
    'USDT': 'CEBP3CqAbW4zdZA57H2wfaSG1QNdzQ72GiQEbQXyW9Tm',
    'USDC': 'AKEWE7Bgh87GPp171b4cJPSSZfmZwQ3KaqYqXoKLNAEE',
    'BITZ': '64mggk2nXg6vHC1qCdsZdEFzd5QGN4id54Vbho4PswCF',
    'tETH': 'GU7NS9xCwgNPiAdJ69iusFrRfawjDDPjeMBovhV1d4kn',
    'TUSD': '27Kkn8PWJbKJsRZrxbsYDdedpUQKnJ5vNfserCxNEJ3R',
    'LAIKA': 'LaihKXA47apnS599tyEyasY2REfEzBNe4heunANhsMx',
    'MCT': '82kkga2kBcQNyV4VKJhGvE7Z58fFavVyuh5NapMVo7Qs'
}

POOLS_WITH_POINTS = {
    'ETH/tETH': '7MYrqThaB5FtJjnzbMcWrGCrq4RspBrcv1NYtUdZk9jE',
    'USDC/USDT': 'AiLuegKP9VM2AvPM25Uci1cfiKSaQaaAzuZUEH6wLr6X',
    'ETH/SOL': '97UtbZtTpfHM584eKwbRD1ATmrn35iyWQUpQRWKe7QgW',
    'ETH/USDC': '7dy1NBe3AoXqjXqKMvtJ5oTEWezabxK11E4TQJ2VU9dG',
    'USDC/SOL': 'E7CAqwLj3bjtcs2ti9iy3Ux2F6P6iskGNH9c8XAvJ67h',
    'ETH/BITZ': 'HLSgfWardM5bjNsp47DUHa5MbToBiFEVTwKceUoX1Bgn',
}

ADDRESS_TO_SYMBOL = {v: k for k, v in TOKEN_ADDRESS.items()}

class UMBRA:
    def __init__(self):
        url = 'https://api.umbra.finance/1/explore/pools?sortBy=totalValueLockedUsd&sortDirection=desc'
        response = requests.get(url, headers=headers)
        self._DATA = json.loads(response.text)
        self._poolActivity = {}
        self._tvlData = {}

    def topPoolsWithPoints(self):
        result = {}
        pools = self._DATA.get('result', [])

        # Reverse lookup for address to POOL_NAME
        addr_to_pool = {v: k for k, v in POOLS_WITH_POINTS.items()}

        for pool in pools:
            pool_addr = pool.get('address')
            pool_name = addr_to_pool.get(pool_addr)
            if not pool_name:
                continue

            apy = float(pool.get('apr', 0))
            daily_apr = round(apy / 365, 4)
            volume = float(pool.get('volume24HUsd', 0))
            fee = float(pool.get('feeRate', 0))
            tvl = float(pool.get('totalValueLockedUsd', 0))
            activity = round(volume / tvl, 4) if tvl else 0
            tokenX = ADDRESS_TO_SYMBOL.get(pool.get('token0'), pool.get('token0'))
            tokenY = ADDRESS_TO_SYMBOL.get(pool.get('token1'), pool.get('token1'))

            # The FIX is here:
            url = f"https://umbra.finance/add/clmm/{tokenX}/{tokenY}/{pool.get('ammConfigAddress')}"

            key = f"{pool_name} : {daily_apr}％"
            result[key] = url
            self._poolActivity[key] = activity
            self._tvlData[key] = int(round(tvl, 0))
        return result
    def poolsWithPointsActivity(self):
            return self._poolActivity 
    def poolsWithPointsTVL(self):
            return self._tvlData 
    

  