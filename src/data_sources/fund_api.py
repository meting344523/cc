import requests
import json
import re
import time
from typing import List, Dict, Optional, Any
from datetime import datetime, timedelta
from loguru import logger

from src.utils.rate_limiter import rate_limit
from src.utils.cache_manager import cached
from src.config.settings import Config

class FundAPI:
    """天天基金网数据获取类"""
    
    def __init__(self):
        self.base_url = "http://fundgz.1234567.com.cn"
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Referer': 'http://fund.eastmoney.com/'
        })
        
    @rate_limit('fund', 20, 500)  # 每分钟20次，每小时500次
    @cached('fund_realtime_data', expire_time=300)  # 缓存5分钟
    def get_fund_realtime_data(self, fund_code: str) -> Optional[Dict[str, Any]]:
        """
        获取基金实时数据
        
        Args:
            fund_code: 基金代码
            
        Returns:
            Dict: 基金实时数据
        """
        try:
            url = f"{self.base_url}/js/{fund_code}.js"
            response = self.session.get(url, timeout=10)
            response.raise_for_status()
            
            # 解析JSONP响应
            content = response.text
            # 提取JSON数据
            json_match = re.search(r'jsonpgz\((.*?)\);', content)
            if not json_match:
                logger.warning(f"无法解析基金数据: {fund_code}")
                return None
                
            json_str = json_match.group(1)
            fund_data = json.loads(json_str)
            
            logger.debug(f"获取基金实时数据: {fund_code}")
            return fund_data
            
        except requests.exceptions.RequestException as e:
            logger.error(f"获取基金实时数据失败 ({fund_code}): {str(e)}")
            return None
        except json.JSONDecodeError as e:
            logger.error(f"解析基金数据失败 ({fund_code}): {str(e)}")
            return None
    
    @rate_limit('fund', 20, 500)
    @cached('fund_historical_data', expire_time=1800)  # 缓存30分钟
    def get_fund_historical_data(self, fund_code: str, start_date: Optional[str] = None, 
                               end_date: Optional[str] = None) -> Optional[List[Dict[str, Any]]]:
        """
        获取基金历史净值数据
        
        Args:
            fund_code: 基金代码
            start_date: 开始日期 (YYYY-MM-DD)
            end_date: 结束日期 (YYYY-MM-DD)
            
        Returns:
            List[Dict]: 历史净值数据
        """
        try:
            # 设置默认日期范围
            if not end_date:
                end_date = datetime.now().strftime("%Y-%m-%d")
            if not start_date:
                start_date = (datetime.now() - timedelta(days=365)).strftime("%Y-%m-%d")
            
            # 天天基金历史净值API
            url = f"http://api.fund.eastmoney.com/f10/lsjz"
            params = {
                'callback': 'jQuery',
                'fundCode': fund_code,
                'pageIndex': 1,
                'pageSize': 365,  # 获取一年数据
                'startDate': start_date,
                'endDate': end_date,
                '_': int(time.time() * 1000)
            }
            
            response = self.session.get(url, params=params, timeout=15)
            response.raise_for_status()
            
            # 解析JSONP响应
            content = response.text
            json_match = re.search(r'jQuery\d*_\d*\((.*?)\);', content)
            if not json_match:
                logger.warning(f"无法解析基金历史数据: {fund_code}")
                return None
                
            json_str = json_match.group(1)
            response_data = json.loads(json_str)
            
            if response_data.get('ErrCode') != 0:
                logger.warning(f"基金历史数据API错误: {fund_code}, {response_data.get('ErrMsg')}")
                return None
            
            data_list = response_data.get('Data', {}).get('LSJZList', [])
            
            logger.debug(f"获取基金历史数据: {fund_code}, {len(data_list)}条记录")
            return data_list
            
        except requests.exceptions.RequestException as e:
            logger.error(f"获取基金历史数据失败 ({fund_code}): {str(e)}")
            return None
        except json.JSONDecodeError as e:
            logger.error(f"解析基金历史数据失败 ({fund_code}): {str(e)}")
            return None
    
    @rate_limit('fund', 20, 500)
    @cached('fund_basic_info', expire_time=3600)  # 缓存1小时
    def get_fund_basic_info(self, fund_code: str) -> Optional[Dict[str, Any]]:
        """
        获取基金基本信息
        
        Args:
            fund_code: 基金代码
            
        Returns:
            Dict: 基金基本信息
        """
        try:
            # 天天基金基本信息API
            url = f"http://fundgz.1234567.com.cn/js/{fund_code}.js"
            response = self.session.get(url, timeout=10)
            response.raise_for_status()
            
            # 解析JSONP响应获取基本信息
            content = response.text
            json_match = re.search(r'jsonpgz\((.*?)\);', content)
            if not json_match:
                return None
                
            json_str = json_match.group(1)
            basic_data = json.loads(json_str)
            
            # 获取更详细的基金信息
            detail_url = f"http://api.fund.eastmoney.com/f10/jbgk"
            detail_params = {
                'callback': 'jQuery',
                'fundCode': fund_code,
                '_': int(time.time() * 1000)
            }
            
            detail_response = self.session.get(detail_url, params=detail_params, timeout=15)
            if detail_response.status_code == 200:
                detail_content = detail_response.text
                detail_match = re.search(r'jQuery\d*_\d*\((.*?)\);', detail_content)
                if detail_match:
                    detail_json = json.loads(detail_match.group(1))
                    if detail_json.get('ErrCode') == 0:
                        detail_data = detail_json.get('Datas', [])
                        if detail_data:
                            basic_data.update(detail_data[0])
            
            logger.debug(f"获取基金基本信息: {fund_code}")
            return basic_data
            
        except Exception as e:
            logger.error(f"获取基金基本信息失败 ({fund_code}): {str(e)}")
            return None
    
    def get_multiple_funds_data(self, fund_codes: List[str]) -> List[Dict[str, Any]]:
        """
        批量获取多个基金的实时数据
        
        Args:
            fund_codes: 基金代码列表
            
        Returns:
            List[Dict]: 基金数据列表
        """
        funds_data = []
        
        for fund_code in fund_codes:
            try:
                fund_data = self.get_fund_realtime_data(fund_code)
                if fund_data:
                    funds_data.append(fund_data)
                
                # 请求间隔，避免过于频繁
                time.sleep(0.5)
                
            except Exception as e:
                logger.error(f"获取基金数据失败 ({fund_code}): {str(e)}")
                continue
        
        logger.info(f"批量获取基金数据完成: {len(funds_data)}/{len(fund_codes)}")
        return funds_data
    
    def get_fund_technical_data(self, fund_code: str, days: int = 30) -> Optional[Dict[str, Any]]:
        """
        获取基金技术分析数据
        
        Args:
            fund_code: 基金代码
            days: 历史天数
            
        Returns:
            Dict: 技术分析数据
        """
        try:
            # 获取实时数据
            realtime_data = self.get_fund_realtime_data(fund_code)
            if not realtime_data:
                return None
            
            # 获取历史数据
            end_date = datetime.now().strftime("%Y-%m-%d")
            start_date = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")
            
            historical_data = self.get_fund_historical_data(fund_code, start_date, end_date)
            
            result = {
                'fund_code': fund_code,
                'fund_name': realtime_data.get('name', ''),
                'latest_nav': float(realtime_data.get('dwjz', 0)),  # 单位净值
                'estimated_nav': float(realtime_data.get('gsz', 0)),  # 估算净值
                'change_pct': float(realtime_data.get('gszzl', 0)),  # 估算涨跌幅
                'update_time': realtime_data.get('gztime', ''),
                'historical_count': len(historical_data) if historical_data else 0
            }
            
            # 如果有历史数据，计算一些基础指标
            if historical_data and len(historical_data) > 1:
                navs = [float(item.get('DWJZ', 0)) for item in historical_data if item.get('DWJZ')]
                if navs:
                    result.update({
                        'max_nav': max(navs),
                        'min_nav': min(navs),
                        'avg_nav': sum(navs) / len(navs),
                        'nav_volatility': self._calculate_volatility(navs)
                    })
            
            return result
            
        except Exception as e:
            logger.error(f"获取基金技术数据失败 ({fund_code}): {str(e)}")
            return None
    
    def _calculate_volatility(self, values: List[float]) -> float:
        """计算波动率"""
        if len(values) < 2:
            return 0.0
            
        # 计算日收益率
        returns = []
        for i in range(1, len(values)):
            if values[i-1] != 0:
                ret = (values[i] - values[i-1]) / values[i-1]
                returns.append(ret)
        
        if not returns:
            return 0.0
        
        # 计算标准差
        mean_return = sum(returns) / len(returns)
        variance = sum((r - mean_return) ** 2 for r in returns) / len(returns)
        
        return variance ** 0.5

# 全局基金API实例
fund_api = FundAPI()

