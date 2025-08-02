import json
import time
import hashlib
from typing import Any, Optional, Dict
from loguru import logger

class MemoryCache:
    """内存缓存管理器（用于无Redis环境）"""
    
    def __init__(self):
        self._cache: Dict[str, Dict[str, Any]] = {}
        
    def get(self, key: str) -> Optional[Any]:
        """获取缓存值"""
        if key in self._cache:
            cache_data = self._cache[key]
            # 检查是否过期
            if cache_data['expire_time'] > time.time():
                logger.debug(f"缓存命中: {key}")
                return cache_data['value']
            else:
                # 删除过期缓存
                del self._cache[key]
                logger.debug(f"缓存过期: {key}")
        return None
        
    def set(self, key: str, value: Any, expire_time: int = 300):
        """设置缓存值"""
        self._cache[key] = {
            'value': value,
            'expire_time': time.time() + expire_time,
            'created_time': time.time()
        }
        logger.debug(f"缓存设置: {key}, 过期时间: {expire_time}秒")
        
    def delete(self, key: str):
        """删除缓存"""
        if key in self._cache:
            del self._cache[key]
            logger.debug(f"缓存删除: {key}")
            
    def clear(self):
        """清空所有缓存"""
        self._cache.clear()
        logger.info("所有缓存已清空")
        
    def cleanup_expired(self):
        """清理过期缓存"""
        current_time = time.time()
        expired_keys = [
            key for key, data in self._cache.items()
            if data['expire_time'] <= current_time
        ]
        
        for key in expired_keys:
            del self._cache[key]
            
        if expired_keys:
            logger.info(f"清理了 {len(expired_keys)} 个过期缓存")
            
    def get_stats(self) -> Dict[str, Any]:
        """获取缓存统计信息"""
        current_time = time.time()
        active_count = sum(
            1 for data in self._cache.values()
            if data['expire_time'] > current_time
        )
        
        return {
            'total_keys': len(self._cache),
            'active_keys': active_count,
            'expired_keys': len(self._cache) - active_count
        }

class CacheManager:
    """缓存管理器"""
    
    def __init__(self, default_expire_time: int = 300):
        self.default_expire_time = default_expire_time
        self.cache = MemoryCache()
        
    def _generate_key(self, prefix: str, *args, **kwargs) -> str:
        """生成缓存键"""
        # 将参数转换为字符串并生成哈希
        key_data = f"{prefix}:{str(args)}:{str(sorted(kwargs.items()))}"
        return hashlib.md5(key_data.encode()).hexdigest()[:16]
        
    def get_or_set(self, prefix: str, func, *args, expire_time: Optional[int] = None, **kwargs):
        """获取缓存或执行函数并缓存结果"""
        cache_key = self._generate_key(prefix, *args, **kwargs)
        
        # 尝试从缓存获取
        cached_result = self.cache.get(cache_key)
        if cached_result is not None:
            return cached_result
            
        # 执行函数并缓存结果
        try:
            result = func(*args, **kwargs)
            expire_time = expire_time or self.default_expire_time
            self.cache.set(cache_key, result, expire_time)
            return result
        except Exception as e:
            logger.error(f"函数执行失败: {func.__name__}, 错误: {str(e)}")
            raise
            
    def invalidate_prefix(self, prefix: str):
        """删除指定前缀的所有缓存"""
        # 由于使用哈希键，无法直接按前缀删除，这里清空所有缓存
        # 在生产环境中可以考虑使用Redis的模式匹配删除
        self.cache.clear()
        logger.info(f"已清空前缀为 {prefix} 的缓存")
        
    def cleanup(self):
        """清理过期缓存"""
        self.cache.cleanup_expired()
        
    def get_stats(self) -> Dict[str, Any]:
        """获取缓存统计"""
        return self.cache.get_stats()

# 全局缓存管理器实例
cache_manager = CacheManager()

def cached(prefix: str, expire_time: Optional[int] = None):
    """
    装饰器：为函数添加缓存功能
    
    Args:
        prefix: 缓存键前缀
        expire_time: 过期时间（秒），None使用默认值
    """
    def decorator(func):
        def wrapper(*args, **kwargs):
            return cache_manager.get_or_set(prefix, func, *args, expire_time=expire_time, **kwargs)
        return wrapper
    return decorator

