import time
import threading
from collections import defaultdict, deque
from typing import Dict, Optional
from loguru import logger

class RateLimiter:
    """API请求限速器"""
    
    def __init__(self):
        self._locks: Dict[str, threading.Lock] = defaultdict(threading.Lock)
        self._requests: Dict[str, deque] = defaultdict(deque)
        
    def wait_if_needed(self, api_name: str, requests_per_minute: int, requests_per_hour: Optional[int] = None):
        """
        检查是否需要等待以避免超过限速
        
        Args:
            api_name: API名称
            requests_per_minute: 每分钟请求限制
            requests_per_hour: 每小时请求限制（可选）
        """
        with self._locks[api_name]:
            current_time = time.time()
            
            # 清理过期的请求记录
            self._cleanup_old_requests(api_name, current_time)
            
            # 检查分钟级限制
            minute_requests = [t for t in self._requests[api_name] if current_time - t < 60]
            if len(minute_requests) >= requests_per_minute:
                wait_time = 60 - (current_time - minute_requests[0])
                if wait_time > 0:
                    logger.info(f"API {api_name} 达到分钟限制，等待 {wait_time:.2f} 秒")
                    time.sleep(wait_time)
                    
            # 检查小时级限制
            if requests_per_hour:
                hour_requests = [t for t in self._requests[api_name] if current_time - t < 3600]
                if len(hour_requests) >= requests_per_hour:
                    wait_time = 3600 - (current_time - hour_requests[0])
                    if wait_time > 0:
                        logger.info(f"API {api_name} 达到小时限制，等待 {wait_time:.2f} 秒")
                        time.sleep(wait_time)
            
            # 记录本次请求
            self._requests[api_name].append(current_time)
            
    def _cleanup_old_requests(self, api_name: str, current_time: float):
        """清理过期的请求记录"""
        # 保留最近1小时的记录
        while (self._requests[api_name] and 
               current_time - self._requests[api_name][0] > 3600):
            self._requests[api_name].popleft()
    
    def get_request_count(self, api_name: str) -> Dict[str, int]:
        """获取API请求统计"""
        with self._locks[api_name]:
            current_time = time.time()
            self._cleanup_old_requests(api_name, current_time)
            
            minute_count = len([t for t in self._requests[api_name] if current_time - t < 60])
            hour_count = len([t for t in self._requests[api_name] if current_time - t < 3600])
            
            return {
                'minute': minute_count,
                'hour': hour_count,
                'total': len(self._requests[api_name])
            }

# 全局限速器实例
rate_limiter = RateLimiter()

def rate_limit(api_name: str, requests_per_minute: int, requests_per_hour: Optional[int] = None):
    """
    装饰器：为函数添加限速功能
    
    Args:
        api_name: API名称
        requests_per_minute: 每分钟请求限制
        requests_per_hour: 每小时请求限制（可选）
    """
    def decorator(func):
        def wrapper(*args, **kwargs):
            rate_limiter.wait_if_needed(api_name, requests_per_minute, requests_per_hour)
            return func(*args, **kwargs)
        return wrapper
    return decorator

