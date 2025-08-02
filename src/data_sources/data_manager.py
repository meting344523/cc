import asyncio
import threading
import time
from typing import Dict, List, Any, Optional
from datetime import datetime
from loguru import logger

from src.data_sources.coingecko_api import coingecko_api
from src.data_sources.akshare_api import akshare_api
from src.data_sources.fund_api import fund_api
from src.config.settings import Config
from src.utils.cache_manager import cache_manager

class DataManager:
    """数据管理器 - 统一管理所有数据源"""
    
    def __init__(self):
        self.config = Config()
        self.last_update_times = {
            'crypto': 0,
            'stock': 0,
            'fund': 0
        }
        self.data_cache = {
            'crypto': [],
            'stock': [],
            'fund': []
        }
        self.is_running = False
        self.update_thread = None
        
    def start_data_updates(self):
        """启动数据更新线程"""
        if not self.is_running:
            self.is_running = True
            self.update_thread = threading.Thread(target=self._update_loop, daemon=True)
            self.update_thread.start()
            logger.info("数据更新线程已启动")
    
    def stop_data_updates(self):
        """停止数据更新线程"""
        self.is_running = False
        if self.update_thread and self.update_thread.is_alive():
            self.update_thread.join(timeout=5)
        logger.info("数据更新线程已停止")
    
    def _update_loop(self):
        """数据更新循环"""
        while self.is_running:
            try:
                current_time = time.time()
                
                # 检查加密货币数据是否需要更新
                if (current_time - self.last_update_times['crypto'] >= 
                    self.config.UPDATE_INTERVALS['crypto']):
                    self._update_crypto_data()
                    self.last_update_times['crypto'] = current_time
                
                # 检查股票数据是否需要更新
                if (current_time - self.last_update_times['stock'] >= 
                    self.config.UPDATE_INTERVALS['stock']):
                    self._update_stock_data()
                    self.last_update_times['stock'] = current_time
                
                # 检查基金数据是否需要更新
                if (current_time - self.last_update_times['fund'] >= 
                    self.config.UPDATE_INTERVALS['fund']):
                    self._update_fund_data()
                    self.last_update_times['fund'] = current_time
                
                # 清理过期缓存
                cache_manager.cleanup()
                
                # 休眠10秒后继续检查
                time.sleep(10)
                
            except Exception as e:
                logger.error(f"数据更新循环异常: {str(e)}")
                time.sleep(30)  # 出错后等待30秒
    
    def _update_crypto_data(self):
        """更新加密货币数据"""
        try:
            logger.info("开始更新加密货币数据")
            
            # 获取前100名加密货币数据
            crypto_data = coingecko_api.get_top_coins_by_market_cap(limit=100)
            
            if crypto_data:
                self.data_cache['crypto'] = crypto_data
                logger.info(f"加密货币数据更新完成: {len(crypto_data)}个币种")
            else:
                logger.warning("加密货币数据更新失败")
                
        except Exception as e:
            logger.error(f"更新加密货币数据异常: {str(e)}")
    
    def _update_stock_data(self):
        """更新股票数据"""
        try:
            logger.info("开始更新股票数据")
            
            # 获取涨幅排行榜前100名
            stock_data = akshare_api.get_top_stocks(sort_by="涨跌幅", limit=100)
            
            if stock_data:
                self.data_cache['stock'] = stock_data
                logger.info(f"股票数据更新完成: {len(stock_data)}只股票")
            else:
                logger.warning("股票数据更新失败")
                
        except Exception as e:
            logger.error(f"更新股票数据异常: {str(e)}")
    
    def _update_fund_data(self):
        """更新基金数据"""
        try:
            logger.info("开始更新基金数据")
            
            # 获取配置中的基金代码池数据
            fund_codes = self.config.FUND_CODES
            fund_data = fund_api.get_multiple_funds_data(fund_codes)
            
            if fund_data:
                self.data_cache['fund'] = fund_data
                logger.info(f"基金数据更新完成: {len(fund_data)}只基金")
            else:
                logger.warning("基金数据更新失败")
                
        except Exception as e:
            logger.error(f"更新基金数据异常: {str(e)}")
    
    def get_crypto_data(self, limit: int = 50) -> List[Dict[str, Any]]:
        """
        获取加密货币数据
        
        Args:
            limit: 返回数量限制
            
        Returns:
            List[Dict]: 加密货币数据
        """
        return self.data_cache['crypto'][:limit]
    
    def get_stock_data(self, limit: int = 50) -> List[Dict[str, Any]]:
        """
        获取股票数据
        
        Args:
            limit: 返回数量限制
            
        Returns:
            List[Dict]: 股票数据
        """
        return self.data_cache['stock'][:limit]
    
    def get_fund_data(self, limit: int = 50) -> List[Dict[str, Any]]:
        """
        获取基金数据
        
        Args:
            limit: 返回数量限制
            
        Returns:
            List[Dict]: 基金数据
        """
        return self.data_cache['fund'][:limit]
    
    def get_all_data(self) -> Dict[str, Any]:
        """
        获取所有市场数据
        
        Returns:
            Dict: 包含所有市场数据
        """
        return {
            'crypto': self.get_crypto_data(50),
            'stock': self.get_stock_data(50),
            'fund': self.get_fund_data(30),
            'last_update_times': {
                'crypto': datetime.fromtimestamp(self.last_update_times['crypto']).strftime('%Y-%m-%d %H:%M:%S') if self.last_update_times['crypto'] else 'Never',
                'stock': datetime.fromtimestamp(self.last_update_times['stock']).strftime('%Y-%m-%d %H:%M:%S') if self.last_update_times['stock'] else 'Never',
                'fund': datetime.fromtimestamp(self.last_update_times['fund']).strftime('%Y-%m-%d %H:%M:%S') if self.last_update_times['fund'] else 'Never'
            }
        }
    
    def force_update_all(self):
        """强制更新所有数据"""
        logger.info("开始强制更新所有数据")
        
        try:
            self._update_crypto_data()
            self._update_stock_data()
            self._update_fund_data()
            
            # 更新时间戳
            current_time = time.time()
            for market in self.last_update_times:
                self.last_update_times[market] = current_time
                
            logger.info("强制更新所有数据完成")
            
        except Exception as e:
            logger.error(f"强制更新数据异常: {str(e)}")
    
    def get_data_status(self) -> Dict[str, Any]:
        """
        获取数据状态信息
        
        Returns:
            Dict: 数据状态信息
        """
        current_time = time.time()
        
        status = {
            'is_running': self.is_running,
            'data_counts': {
                'crypto': len(self.data_cache['crypto']),
                'stock': len(self.data_cache['stock']),
                'fund': len(self.data_cache['fund'])
            },
            'last_updates': {},
            'next_updates': {},
            'cache_stats': cache_manager.get_stats()
        }
        
        for market in self.last_update_times:
            last_time = self.last_update_times[market]
            if last_time > 0:
                status['last_updates'][market] = datetime.fromtimestamp(last_time).strftime('%Y-%m-%d %H:%M:%S')
                next_time = last_time + self.config.UPDATE_INTERVALS[market]
                status['next_updates'][market] = datetime.fromtimestamp(next_time).strftime('%Y-%m-%d %H:%M:%S')
            else:
                status['last_updates'][market] = 'Never'
                status['next_updates'][market] = 'Pending'
        
        return status

# 全局数据管理器实例
data_manager = DataManager()

