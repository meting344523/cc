import numpy as np
import pandas as pd
from typing import List, Dict, Any, Optional, Tuple
from loguru import logger

class TechnicalIndicators:
    """技术指标计算类"""
    
    @staticmethod
    def sma(prices: List[float], period: int) -> List[float]:
        """
        简单移动平均线 (Simple Moving Average)
        
        Args:
            prices: 价格列表
            period: 周期
            
        Returns:
            List[float]: SMA值列表
        """
        if len(prices) < period:
            return []
        
        sma_values = []
        for i in range(period - 1, len(prices)):
            sma = sum(prices[i - period + 1:i + 1]) / period
            sma_values.append(sma)
        
        return sma_values
    
    @staticmethod
    def ema(prices: List[float], period: int) -> List[float]:
        """
        指数移动平均线 (Exponential Moving Average)
        
        Args:
            prices: 价格列表
            period: 周期
            
        Returns:
            List[float]: EMA值列表
        """
        if len(prices) < period:
            return []
        
        multiplier = 2 / (period + 1)
        ema_values = []
        
        # 第一个EMA值使用SMA
        first_ema = sum(prices[:period]) / period
        ema_values.append(first_ema)
        
        # 计算后续EMA值
        for i in range(period, len(prices)):
            ema = (prices[i] * multiplier) + (ema_values[-1] * (1 - multiplier))
            ema_values.append(ema)
        
        return ema_values
    
    @staticmethod
    def rsi(prices: List[float], period: int = 14) -> List[float]:
        """
        相对强弱指数 (Relative Strength Index)
        
        Args:
            prices: 价格列表
            period: 周期，默认14
            
        Returns:
            List[float]: RSI值列表
        """
        if len(prices) < period + 1:
            return []
        
        # 计算价格变化
        price_changes = []
        for i in range(1, len(prices)):
            price_changes.append(prices[i] - prices[i-1])
        
        # 分离上涨和下跌
        gains = [max(change, 0) for change in price_changes]
        losses = [abs(min(change, 0)) for change in price_changes]
        
        rsi_values = []
        
        # 计算第一个RSI值
        avg_gain = sum(gains[:period]) / period
        avg_loss = sum(losses[:period]) / period
        
        if avg_loss == 0:
            rsi_values.append(100)
        else:
            rs = avg_gain / avg_loss
            rsi = 100 - (100 / (1 + rs))
            rsi_values.append(rsi)
        
        # 计算后续RSI值
        for i in range(period, len(price_changes)):
            avg_gain = (avg_gain * (period - 1) + gains[i]) / period
            avg_loss = (avg_loss * (period - 1) + losses[i]) / period
            
            if avg_loss == 0:
                rsi_values.append(100)
            else:
                rs = avg_gain / avg_loss
                rsi = 100 - (100 / (1 + rs))
                rsi_values.append(rsi)
        
        return rsi_values
    
    @staticmethod
    def macd(prices: List[float], fast_period: int = 12, slow_period: int = 26, signal_period: int = 9) -> Dict[str, List[float]]:
        """
        MACD指标 (Moving Average Convergence Divergence)
        
        Args:
            prices: 价格列表
            fast_period: 快线周期，默认12
            slow_period: 慢线周期，默认26
            signal_period: 信号线周期，默认9
            
        Returns:
            Dict: 包含MACD线、信号线和柱状图的字典
        """
        if len(prices) < slow_period:
            return {'macd': [], 'signal': [], 'histogram': []}
        
        # 计算快慢EMA
        fast_ema = TechnicalIndicators.ema(prices, fast_period)
        slow_ema = TechnicalIndicators.ema(prices, slow_period)
        
        # 对齐数据长度
        start_index = slow_period - fast_period
        fast_ema_aligned = fast_ema[start_index:]
        
        # 计算MACD线
        macd_line = []
        for i in range(len(slow_ema)):
            macd_line.append(fast_ema_aligned[i] - slow_ema[i])
        
        # 计算信号线
        signal_line = TechnicalIndicators.ema(macd_line, signal_period)
        
        # 计算柱状图
        histogram = []
        start_index = len(macd_line) - len(signal_line)
        for i in range(len(signal_line)):
            histogram.append(macd_line[start_index + i] - signal_line[i])
        
        return {
            'macd': macd_line,
            'signal': signal_line,
            'histogram': histogram
        }
    
    @staticmethod
    def bollinger_bands(prices: List[float], period: int = 20, std_dev: float = 2) -> Dict[str, List[float]]:
        """
        布林带 (Bollinger Bands)
        
        Args:
            prices: 价格列表
            period: 周期，默认20
            std_dev: 标准差倍数，默认2
            
        Returns:
            Dict: 包含上轨、中轨、下轨的字典
        """
        if len(prices) < period:
            return {'upper': [], 'middle': [], 'lower': []}
        
        middle_band = TechnicalIndicators.sma(prices, period)
        upper_band = []
        lower_band = []
        
        for i in range(period - 1, len(prices)):
            # 计算标准差
            price_slice = prices[i - period + 1:i + 1]
            std = np.std(price_slice)
            
            middle = middle_band[i - period + 1]
            upper_band.append(middle + (std * std_dev))
            lower_band.append(middle - (std * std_dev))
        
        return {
            'upper': upper_band,
            'middle': middle_band,
            'lower': lower_band
        }
    
    @staticmethod
    def volume_analysis(volumes: List[float], period: int = 20) -> Dict[str, Any]:
        """
        成交量分析
        
        Args:
            volumes: 成交量列表
            period: 周期
            
        Returns:
            Dict: 成交量分析结果
        """
        if len(volumes) < period:
            return {'avg_volume': 0, 'volume_ratio': 1, 'is_abnormal': False}
        
        # 计算平均成交量
        avg_volume = sum(volumes[-period:]) / period
        
        # 当前成交量比率
        current_volume = volumes[-1] if volumes else 0
        volume_ratio = current_volume / avg_volume if avg_volume > 0 else 1
        
        # 判断是否异常
        is_abnormal = volume_ratio > 1.5  # 超过平均值1.5倍认为异常
        
        return {
            'avg_volume': avg_volume,
            'current_volume': current_volume,
            'volume_ratio': volume_ratio,
            'is_abnormal': is_abnormal
        }
    
    @staticmethod
    def support_resistance_levels(prices: List[float], highs: List[float], lows: List[float], 
                                 window: int = 5) -> Dict[str, List[float]]:
        """
        支撑位和阻力位识别
        
        Args:
            prices: 收盘价列表
            highs: 最高价列表
            lows: 最低价列表
            window: 窗口大小
            
        Returns:
            Dict: 支撑位和阻力位列表
        """
        if len(prices) < window * 2 + 1:
            return {'support': [], 'resistance': []}
        
        support_levels = []
        resistance_levels = []
        
        # 寻找局部最低点作为支撑位
        for i in range(window, len(lows) - window):
            is_support = True
            current_low = lows[i]
            
            # 检查左右窗口内是否为最低点
            for j in range(i - window, i + window + 1):
                if j != i and lows[j] < current_low:
                    is_support = False
                    break
            
            if is_support:
                support_levels.append(current_low)
        
        # 寻找局部最高点作为阻力位
        for i in range(window, len(highs) - window):
            is_resistance = True
            current_high = highs[i]
            
            # 检查左右窗口内是否为最高点
            for j in range(i - window, i + window + 1):
                if j != i and highs[j] > current_high:
                    is_resistance = False
                    break
            
            if is_resistance:
                resistance_levels.append(current_high)
        
        return {
            'support': support_levels,
            'resistance': resistance_levels
        }
    
    @staticmethod
    def calculate_volatility(prices: List[float], period: int = 20) -> float:
        """
        计算价格波动率
        
        Args:
            prices: 价格列表
            period: 周期
            
        Returns:
            float: 波动率
        """
        if len(prices) < period + 1:
            return 0.0
        
        # 计算收益率
        returns = []
        for i in range(1, len(prices)):
            if prices[i-1] != 0:
                ret = (prices[i] - prices[i-1]) / prices[i-1]
                returns.append(ret)
        
        if len(returns) < period:
            return 0.0
        
        # 取最近period个收益率
        recent_returns = returns[-period:]
        
        # 计算标准差
        mean_return = sum(recent_returns) / len(recent_returns)
        variance = sum((r - mean_return) ** 2 for r in recent_returns) / len(recent_returns)
        
        return variance ** 0.5
    
    @staticmethod
    def k_line_pattern_analysis(opens: List[float], highs: List[float], 
                              lows: List[float], closes: List[float]) -> Dict[str, Any]:
        """
        K线形态分析
        
        Args:
            opens: 开盘价列表
            highs: 最高价列表
            lows: 最低价列表
            closes: 收盘价列表
            
        Returns:
            Dict: K线形态分析结果
        """
        if len(closes) < 3:
            return {'pattern': 'insufficient_data', 'signal': 'neutral'}
        
        # 获取最近3根K线
        recent_opens = opens[-3:]
        recent_highs = highs[-3:]
        recent_lows = lows[-3:]
        recent_closes = closes[-3:]
        
        patterns = []
        
        # 检测锤头线
        if TechnicalIndicators._is_hammer(recent_opens[-1], recent_highs[-1], 
                                        recent_lows[-1], recent_closes[-1]):
            patterns.append('hammer')
        
        # 检测十字星
        if TechnicalIndicators._is_doji(recent_opens[-1], recent_closes[-1], 
                                      recent_highs[-1], recent_lows[-1]):
            patterns.append('doji')
        
        # 检测吞没形态
        if len(recent_closes) >= 2:
            if TechnicalIndicators._is_bullish_engulfing(recent_opens[-2:], recent_closes[-2:]):
                patterns.append('bullish_engulfing')
            elif TechnicalIndicators._is_bearish_engulfing(recent_opens[-2:], recent_closes[-2:]):
                patterns.append('bearish_engulfing')
        
        # 确定信号
        signal = 'neutral'
        if 'hammer' in patterns or 'bullish_engulfing' in patterns:
            signal = 'bullish'
        elif 'bearish_engulfing' in patterns:
            signal = 'bearish'
        
        return {
            'patterns': patterns,
            'signal': signal
        }
    
    @staticmethod
    def _is_hammer(open_price: float, high: float, low: float, close: float) -> bool:
        """检测锤头线形态"""
        body = abs(close - open_price)
        upper_shadow = high - max(open_price, close)
        lower_shadow = min(open_price, close) - low
        
        # 锤头线特征：下影线长，上影线短，实体小
        return (lower_shadow > body * 2 and 
                upper_shadow < body * 0.5 and 
                body > 0)
    
    @staticmethod
    def _is_doji(open_price: float, close: float, high: float, low: float) -> bool:
        """检测十字星形态"""
        body = abs(close - open_price)
        total_range = high - low
        
        # 十字星特征：实体很小
        return body < total_range * 0.1 if total_range > 0 else False
    
    @staticmethod
    def _is_bullish_engulfing(opens: List[float], closes: List[float]) -> bool:
        """检测看涨吞没形态"""
        if len(opens) < 2 or len(closes) < 2:
            return False
        
        # 前一根为阴线，后一根为阳线，且完全吞没
        prev_bearish = closes[0] < opens[0]
        curr_bullish = closes[1] > opens[1]
        engulfing = opens[1] < closes[0] and closes[1] > opens[0]
        
        return prev_bearish and curr_bullish and engulfing
    
    @staticmethod
    def _is_bearish_engulfing(opens: List[float], closes: List[float]) -> bool:
        """检测看跌吞没形态"""
        if len(opens) < 2 or len(closes) < 2:
            return False
        
        # 前一根为阳线，后一根为阴线，且完全吞没
        prev_bullish = closes[0] > opens[0]
        curr_bearish = closes[1] < opens[1]
        engulfing = opens[1] > closes[0] and closes[1] < opens[0]
        
        return prev_bullish and curr_bearish and engulfing

# 全局技术指标实例
technical_indicators = TechnicalIndicators()

