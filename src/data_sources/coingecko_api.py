import requests
import time
from typing import List, Dict, Optional, Any
from loguru import logger

from src.utils.rate_limiter import rate_limit
from src.utils.cache_manager import cached
from src.config.settings import Config

class CoinGeckoAPI:
    """CoinGecko API数据获取类"""
    
    def __init__(self):
        self.base_url = "https://api.coingecko.com/api/v3"
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'QuantitativeAnalysisSystem/1.0'
        })
        
    @rate_limit('coingecko', 10, 1000)  # 每分钟10次，每小时1000次
    @cached('coingecko_coins_list', expire_time=3600)  # 缓存1小时
    def get_coins_list(self) -> List[Dict[str, Any]]:
        """
        获取所有支持的加密货币列表
        
        Returns:
            List[Dict]: 包含币种信息的列表
        """
        try:
            url = f"{self.base_url}/coins/list"
            response = self.session.get(url, timeout=30)
            response.raise_for_status()
            
            coins_data = response.json()
            logger.info(f"获取到 {len(coins_data)} 个加密货币")
            
            return coins_data
            
        except requests.exceptions.RequestException as e:
            logger.error(f"获取加密货币列表失败: {str(e)}")
            return []
    
    @rate_limit('coingecko', 10, 1000)
    @cached('coingecko_markets', expire_time=300)  # 缓存5分钟
    def get_markets_data(self, vs_currency: str = 'usd', per_page: int = 250, page: int = 1) -> List[Dict[str, Any]]:
        """
        获取市场数据（分页）
        
        Args:
            vs_currency: 对标货币，默认USD
            per_page: 每页数量，最大250
            page: 页码
            
        Returns:
            List[Dict]: 市场数据列表
        """
        try:
            url = f"{self.base_url}/coins/markets"
            params = {
                'vs_currency': vs_currency,
                'order': 'market_cap_desc',
                'per_page': min(per_page, 250),  # API限制最大250
                'page': page,
                'sparkline': 'false',
                'price_change_percentage': '1h,24h,7d'
            }
            
            response = self.session.get(url, params=params, timeout=30)
            response.raise_for_status()
            
            markets_data = response.json()
            logger.info(f"获取到第{page}页市场数据，共{len(markets_data)}个币种")
            
            return markets_data
            
        except requests.exceptions.RequestException as e:
            logger.error(f"获取市场数据失败 (页码: {page}): {str(e)}")
            return []
    
    @rate_limit('coingecko', 10, 1000)
    @cached('coingecko_coin_detail', expire_time=600)  # 缓存10分钟
    def get_coin_detail(self, coin_id: str) -> Optional[Dict[str, Any]]:
        """
        获取单个币种详细信息
        
        Args:
            coin_id: 币种ID
            
        Returns:
            Dict: 币种详细信息
        """
        try:
            url = f"{self.base_url}/coins/{coin_id}"
            params = {
                'localization': 'false',
                'tickers': 'false',
                'market_data': 'true',
                'community_data': 'false',
                'developer_data': 'false',
                'sparkline': 'false'
            }
            
            response = self.session.get(url, params=params, timeout=30)
            response.raise_for_status()
            
            coin_data = response.json()
            logger.debug(f"获取币种详情: {coin_id}")
            
            return coin_data
            
        except requests.exceptions.RequestException as e:
            logger.error(f"获取币种详情失败 ({coin_id}): {str(e)}")
            return None
    
    @rate_limit('coingecko', 10, 1000)
    @cached('coingecko_price_history', expire_time=1800)  # 缓存30分钟
    def get_price_history(self, coin_id: str, days: int = 30) -> Optional[Dict[str, Any]]:
        """
        获取价格历史数据
        
        Args:
            coin_id: 币种ID
            days: 历史天数
            
        Returns:
            Dict: 历史价格数据
        """
        try:
            url = f"{self.base_url}/coins/{coin_id}/market_chart"
            params = {
                'vs_currency': 'usd',
                'days': days,
                'interval': 'daily' if days > 1 else 'hourly'
            }
            
            response = self.session.get(url, params=params, timeout=30)
            response.raise_for_status()
            
            history_data = response.json()
            logger.debug(f"获取价格历史: {coin_id}, {days}天")
            
            return history_data
            
        except requests.exceptions.RequestException as e:
            logger.error(f"获取价格历史失败 ({coin_id}): {str(e)}")
            return None
    
    def get_all_markets_data(self, max_pages: int = 10) -> List[Dict[str, Any]]:
        """
        获取所有市场数据（多页）
        
        Args:
            max_pages: 最大页数限制
            
        Returns:
            List[Dict]: 所有市场数据
        """
        all_data = []
        
        for page in range(1, max_pages + 1):
            page_data = self.get_markets_data(page=page)
            
            if not page_data:
                break
                
            all_data.extend(page_data)
            
            # 如果返回数据少于250个，说明已经是最后一页
            if len(page_data) < 250:
                break
                
            # 页面间隔，避免请求过快
            time.sleep(1)
        
        logger.info(f"总共获取到 {len(all_data)} 个加密货币市场数据")
        return all_data
    
    def get_top_coins_by_market_cap(self, limit: int = 100) -> List[Dict[str, Any]]:
        """
        获取按市值排序的顶级加密货币
        
        Args:
            limit: 数量限制
            
        Returns:
            List[Dict]: 顶级加密货币数据
        """
        pages_needed = (limit + 249) // 250  # 向上取整
        all_data = []
        
        for page in range(1, pages_needed + 1):
            per_page = min(250, limit - len(all_data))
            page_data = self.get_markets_data(per_page=per_page, page=page)
            
            if not page_data:
                break
                
            all_data.extend(page_data)
            
            if len(all_data) >= limit:
                break
                
            time.sleep(1)
        
        return all_data[:limit]

# 全局CoinGecko API实例
coingecko_api = CoinGeckoAPI()

