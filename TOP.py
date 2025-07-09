import re
from ORCA import ORCA
from Invariant import INVARIANT
from Solar import Solar
from Umbra import UMBRA
from concurrent.futures import ThreadPoolExecutor, as_completed
import re

class TOP5:
    def __init__(self, symbol):
        self._SYMBOL = symbol
        self._ORCA = ORCA(self._SYMBOL)
        self._Invariant = INVARIANT(self._SYMBOL)
        self._Solar = Solar(symbol)
        self._Umbra = UMBRA()
        self._dexes = []
        if self._SYMBOL in ('ETH', 'tETH', 'USDC'):
            self._dexes = [self._Solar, self._ORCA, self._Invariant, self._Umbra]
        else:
            self._dexes = [self._ORCA, self._Invariant, self._Umbra]
        self._top5_keys = []

    def fetch_all(self):
        with ThreadPoolExecutor() as executor:
            futures = [executor.submit(dex.fetch_data) for dex in self._dexes if hasattr(dex, 'fetch_data')]
            for f in as_completed(futures):
                try:
                    f.result()
                except Exception as e:
                    print(f'Error fetching DEX data: {e}')

    def theBestYield(self):
        dicts = []
        if self._SYMBOL in ('ETH', 'tETH', 'USDC'):
            dicts = [self._Solar.bestYield24(), self._ORCA.bestYield24(), self._Invariant.bestYield24()]
        else:
            dicts = [self._ORCA.bestYield24(), self._Invariant.bestYield24()]

        for idx, d in enumerate(dicts):
            print(f"DEX {idx} bestYield24 returned:", type(d), d)
        dicts = [d for d in dicts if isinstance(d, dict) and d]

        all_entries = []
        for d in dicts:
            for k, v in d.items():
                url = None
                if isinstance(v, set):
                    url = next(iter(v))
                elif isinstance(v, dict):
                    url = list(v.values())[0] if v else None
                elif isinstance(v, str):
                    url = v
                else:
                    url = None
                match = re.search(r'[|]\s*([\d.]+)[%％]', k)  # <- look for '|' separator
                apr = float(match.group(1)) if match else 0
                all_entries.append((k, url, apr))

        top5 = sorted(all_entries, key=lambda x: x[2], reverse=True)[:5]
        self._top5_keys = [k for k, _, _ in top5]
        return [(k, url) for k, url, _ in top5 if url]

    def poolsActivity(self):
        merged_activities = {}
        sources = []
        if self._SYMBOL in ('ETH', 'tETH', 'USDC'):
            sources = [self._Solar.poolActivities(), self._ORCA.poolActivities(), self._Invariant.poolActivities()]
        else:
            sources = [self._ORCA.poolActivities(), self._Invariant.poolActivities()]
        for d in sources:
            merged_activities.update(d)
        keys = getattr(self, '_top5_keys', [])
        return {k: merged_activities.get(k) for k in keys}
    def tvlData(self):
        merged_activities = {}
        sources = []
        if self._SYMBOL in ('ETH', 'tETH', 'USDC'):
            sources = [self._Solar.tvlData(), self._ORCA.tvlData(), self._Invariant.tvlData()]
        else:
            sources = [self._ORCA.tvlData(), self._Invariant.tvlData()]
        for d in sources:
            merged_activities.update(d)
        keys = getattr(self, '_top5_keys', [])
        return {k: merged_activities.get(k) for k in keys}
    def topPointsPools(self, dex):
        if dex == 'Invariant':
            pools_dict = self._Invariant.topPoolsWithPoints()
        elif dex == 'Umbra':
            pools_dict = self._Umbra.topPoolsWithPoints()
        sorted_items = sorted(
            pools_dict.items(),
            key=lambda x: float(re.search(r'([\d.]+)％', x[0]).group(1)),
            reverse=True
        )
        return dict(sorted_items)
    def topPointsPoolsActivity(self, dex):
        if dex == 'Invariant':
            pools_dict = self._Invariant.poolsWithPointsActivity()
        elif dex == 'Umbra':
            pools_dict = self._Umbra.poolsWithPointsActivity()

        assert all(re.search(r'([\d.]+)％', k) for k in pools_dict.keys()), "BAD KEY FORMAT"
        sorted_items = sorted(
            pools_dict.items(),
            key=lambda x: float(re.search(r'([\d.]+)％', x[0]).group(1)),
            reverse=True
        )
        return dict(sorted_items)
    def topPointsPooolsTVL(self, dex):
        if dex == 'Invariant':
            pools_dict = self._Invariant.poolsWithPointsTVL()
        elif dex == 'Umbra':
            pools_dict = self._Umbra.poolsWithPointsTVL()
        sorted_items = sorted(
            pools_dict.items(),
            key=lambda x: float(re.search(r'([\d.]+)％', x[0]).group(1)),
            reverse=True
        )
        return dict(sorted_items)


    





            
            
            
