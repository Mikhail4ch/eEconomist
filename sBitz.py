import discord
import asyncio
import requests
from fake_useragent import FakeUserAgent

headers = {
    'user-agent': FakeUserAgent().random
}

class sBITZ:
    def __init__(self):
        self._rewardPool = 720
        self._api = 'https://api.eclipsescan.xyz/v1/account/tokens?address=5FgZ9W81khmNXG8i96HSsG7oJiwwpKnVzmHgn9ZnqQja'
        self._totalStaked = None
        self._fetch_data()

    def _fetch_data(self):
        try:
            response = requests.get(self._api, headers=headers, timeout=8)
            data = response.json()
            tokens = data['data']['tokens']
            for token in tokens:
                if token.get('symbol', '').upper() == 'BITZ':
                    self._totalStaked = float(token['balance'])
                    break
            else:
                self._totalStaked = float(tokens[0]['balance'])
        except Exception:
            self._totalStaked = 0

    def _get_apr(self):
        if not self._totalStaked or self._totalStaked == 0:
            return 0
        return round(self._rewardPool / self._totalStaked * 100, 3)
    
    def calculate_daily_compounding_yield(self, compounding_interval_seconds=10):
        apr = self._get_apr() * 365 / 100
        n_yearly = (365 * 24 * 60 * 60) // compounding_interval_seconds
        n_daily = (24 * 60 * 60) // compounding_interval_seconds
        daily_yield = (1 + apr / n_yearly) ** n_daily - 1
        return round(daily_yield * 100, 3)

    def calculate_apy(self, compounding_interval_seconds=10):
        apr = self._get_apr() * 365 / 100
        seconds_per_year = 365 * 24 * 60 * 60
        n = seconds_per_year // compounding_interval_seconds
        apy = (1 + apr / n) ** n - 1
        return int(round(apy*100,0))
    
    def howMuchEarnDaily(self, initial_amount):
        apr = self._get_apr() * 365 / 100
        periods_per_day = 8640  # every 10 seconds
        periods_per_year = periods_per_day * 365
        t_years = 1 / 365
        final_value = initial_amount * (1 + apr / periods_per_year) ** (periods_per_year * t_years)
        profit = final_value - initial_amount
        return f'Daily you will earn:\n{round(profit,3)} $BITZ'
    
    def howMuchEarnWeekly(self, initial_amount):
        apr = self._get_apr() * 365 / 100
        periods_per_day = 8640  # every 10 seconds
        periods_per_year = periods_per_day * 365
        t_years = 7 / 365
        final_value = initial_amount * (1 + apr / periods_per_year) ** (periods_per_year * t_years)
        profit = final_value - initial_amount
        return f'Weekly you will earn:\n{round(profit,3)} $BITZ'
    
    def howMuchEarnMonthly(self, initial_amount):
        apr = self._get_apr() * 365 / 100
        periods_per_day = 8640  # every 10 seconds
        periods_per_year = periods_per_day * 365
        t_years = 30.436875 / 365
        final_value = initial_amount * (1 + apr / periods_per_year) ** (periods_per_year * t_years)
        profit = final_value - initial_amount
        return f'Monthly you will earn:\n{round(profit,3)} $BITZ'
    
    def howMuchYearly(self, initial_amount):
        apr = self._get_apr() * 365 / 100
        periods_per_day = 8640  # every 10 seconds
        periods_per_year = periods_per_day * 365
        t_years = 365 / 365
        final_value = initial_amount * (1 + apr / periods_per_year) ** (periods_per_year * t_years)
        profit = final_value - initial_amount
        return f'Annually you will earn:\n{round(profit,3)} $BITZ'

      



    

