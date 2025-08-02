import akshare as ak
import pandas as pd
import time
from typing import List, Dict, Optional, Any
from loguru import logger
from datetime import datetime, timedelta

from src.utils.rate_limiter import rate_limit
from src.utils.cache_manager import cached
from src.config.settings import Config

class AkShareAPI:
    """AkShare数据获取类"""
    
    def __init__(self):
        self.session_initialized = False
        
    def _ensure_session(self):
        """确保AkShare会话已初始化"""
        if not self.session_initialized:
            try:
                # 设置AkShare的一些基本配置
                ak.tool_trade_date_hist_sina()  # 测试连接
                self.session_initialized = True
                logger.info("AkShare会话初始化成功")
            except Exception as e:
                logger.warning(f"AkShare会话初始化警告: {str(e)}")
                self.session_initialized = True  # 继续执行
    
    @rate_limit('akshare', 30, 1000)  # 每分钟30次，每小时1000次
    @cached('akshare_stock_list', expire_time=3600)  # 缓存1小时
    def get_stock_list(self) -> List[Dict[str, Any]]:
        """
        获取A股股票列表
        
        Returns:
            List[Dict]: 股票列表数据
        """
        self._ensure_session()
        
        try:
            # 获取沪深A股列表
            stock_list = []
            
            # 获取沪市A股
            try:
                sh_stocks = ak.stock_info_sh_name_code(symbol="主板A股")
                if not sh_stocks.empty:
                    sh_data = sh_stocks.to_dict('records')
                    for stock in sh_data:
                        stock['exchange'] = 'SH'
                    stock_list.extend(sh_data)
                    logger.info(f"获取沪市A股 {len(sh_data)} 只")
            except Exception as e:
                logger.error(f"获取沪市A股失败: {str(e)}")
            
            # 获取深市A股
            try:
                sz_stocks = ak.stock_info_sz_name_code(symbol="A股列表")
                if not sz_stocks.empty:
                    sz_data = sz_stocks.to_dict('records')
                    for stock in sz_data:
                        stock['exchange'] = 'SZ'
                    stock_list.extend(sz_data)
                    logger.info(f"获取深市A股 {len(sz_data)} 只")
            except Exception as e:
                logger.error(f"获取深市A股失败: {str(e)}")
            
            logger.info(f"总共获取A股列表 {len(stock_list)} 只")
            return stock_list
            
        except Exception as e:
            logger.error(f"获取股票列表失败: {str(e)}")
            return []
    
    @rate_limit('akshare', 30, 1000)
    @cached('akshare_realtime_data', expire_time=60)  # 缓存1分钟
    def get_realtime_data(self, symbol: str) -> Optional[Dict[str, Any]]:
        """
        获取股票实时数据
        
        Args:
            symbol: 股票代码
            
        Returns:
            Dict: 实时数据
        """
        self._ensure_session()
        
        try:
            # 获取实时行情
            realtime_data = ak.stock_zh_a_spot_em()
            
            if realtime_data.empty:
                return None
                
            # 查找指定股票
            stock_data = realtime_data[realtime_data['代码'] == symbol]
            
            if stock_data.empty:
                logger.warning(f"未找到股票数据: {symbol}")
                return None
            
            result = stock_data.iloc[0].to_dict()
            logger.debug(f"获取实时数据: {symbol}")
            
            return result
            
        except Exception as e:
            logger.error(f"获取实时数据失败 ({symbol}): {str(e)}")
            return None
    
    @rate_limit('akshare', 30, 1000)
    @cached('akshare_historical_data', expire_time=1800)  # 缓存30分钟
    def get_historical_data(self, symbol: str, period: str = "daily", 
                          start_date: Optional[str] = None, 
                          end_date: Optional[str] = None) -> Optional[pd.DataFrame]:
        """
        获取股票历史数据
        
        Args:
            symbol: 股票代码
            period: 周期 (daily, weekly, monthly)
            start_date: 开始日期 (YYYYMMDD)
            end_date: 结束日期 (YYYYMMDD)
            
        Returns:
            DataFrame: 历史数据
        """
        self._ensure_session()
        
        try:
            # 设置默认日期范围
            if not end_date:
                end_date = datetime.now().strftime("%Y%m%d")
            if not start_date:
                start_date = (datetime.now() - timedelta(days=365)).strftime("%Y%m%d")
            
            # 获取历史数据
            hist_data = ak.stock_zh_a_hist(
                symbol=symbol,
                period=period,
                start_date=start_date,
                end_date=end_date,
                adjust=""
            )
            
            if hist_data.empty:
                logger.warning(f"未获取到历史数据: {symbol}")
                return None
            
            logger.debug(f"获取历史数据: {symbol}, {len(hist_data)}条记录")
            return hist_data
            
        except Exception as e:
            logger.error(f"获取历史数据失败 ({symbol}): {str(e)}")
            return None
    
    @rate_limit('akshare', 30, 1000)
    @cached('akshare_market_overview', expire_time=300)  # 缓存5分钟
    def get_market_overview(self) -> Dict[str, Any]:
        """
        获取市场概览数据
        
        Returns:
            Dict: 市场概览
        """
        self._ensure_session()
        
        try:
            overview = {}
            
            # 获取上证指数
            try:
                sh_index = ak.stock_zh_index_spot_em(symbol="上证指数")
                if not sh_index.empty:
                    overview['sh_index'] = sh_index.iloc[0].to_dict()
            except Exception as e:
                logger.error(f"获取上证指数失败: {str(e)}")
            
            # 获取深证成指
            try:
                sz_index = ak.stock_zh_index_spot_em(symbol="深证成指")
                if not sz_index.empty:
                    overview['sz_index'] = sz_index.iloc[0].to_dict()
            except Exception as e:
                logger.error(f"获取深证成指失败: {str(e)}")
            
            # 获取创业板指
            try:
                cy_index = ak.stock_zh_index_spot_em(symbol="创业板指")
                if not cy_index.empty:
                    overview['cy_index'] = cy_index.iloc[0].to_dict()
            except Exception as e:
                logger.error(f"获取创业板指失败: {str(e)}")
            
            logger.info("获取市场概览数据完成")
            return overview
            
        except Exception as e:
            logger.error(f"获取市场概览失败: {str(e)}")
            return {}
    
    @rate_limit('akshare', 30, 1000)
    @cached('akshare_top_stocks', expire_time=300)  # 缓存5分钟
    def get_top_stocks(self, sort_by: str = "涨跌幅", limit: int = 100) -> List[Dict[str, Any]]:
        """
        获取排行榜股票
        
        Args:
            sort_by: 排序字段
            limit: 数量限制
            
        Returns:
            List[Dict]: 排行榜数据
        """
        self._ensure_session()
        
        try:
            # 获取实时行情数据
            all_stocks = ak.stock_zh_a_spot_em()
            
            if all_stocks.empty:
                return []
            
            # 按指定字段排序
            if sort_by in all_stocks.columns:
                sorted_stocks = all_stocks.sort_values(by=sort_by, ascending=False)
            else:
                sorted_stocks = all_stocks
            
            # 取前N只股票
            top_stocks = sorted_stocks.head(limit).to_dict('records')
            
            logger.info(f"获取排行榜股票: {sort_by}, {len(top_stocks)}只")
            return top_stocks
            
        except Exception as e:
            logger.error(f"获取排行榜股票失败: {str(e)}")
            return []
    
    def get_stock_technical_data(self, symbol: str, days: int = 30) -> Optional[Dict[str, Any]]:
        """
        获取股票技术分析数据
        
        Args:
            symbol: 股票代码
            days: 历史天数
            
        Returns:
            Dict: 技术分析数据
        """
        try:
            # 获取历史数据
            end_date = datetime.now().strftime("%Y%m%d")
            start_date = (datetime.now() - timedelta(days=days)).strftime("%Y%m%d")
            
            hist_data = self.get_historical_data(symbol, start_date=start_date, end_date=end_date)
            
            if hist_data is None or hist_data.empty:
                return None
            
            # 计算基础技术指标
            latest = hist_data.iloc[-1]
            
            result = {
                'symbol': symbol,
                'latest_price': latest.get('收盘', 0),
                'change_pct': latest.get('涨跌幅', 0),
                'volume': latest.get('成交量', 0),
                'turnover': latest.get('成交额', 0),
                'high': latest.get('最高', 0),
                'low': latest.get('最低', 0),
                'open': latest.get('开盘', 0),
                'data_count': len(hist_data),
                'date_range': f"{hist_data.iloc[0]['日期']} - {hist_data.iloc[-1]['日期']}"
            }
            
            return result
            
        except Exception as e:
            logger.error(f"获取技术分析数据失败 ({symbol}): {str(e)}")
            return None

# 全局AkShare API实例
akshare_api = AkShareAPI()

