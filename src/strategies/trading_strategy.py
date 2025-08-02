import numpy as np
from typing import List, Dict, Any, Optional, Tuple
from enum import Enum
from loguru import logger

from src.analysis.technical_indicators import TechnicalIndicators
from src.analysis.ml_predictor import ml_predictor
from src.config.settings import Config

class SignalType(Enum):
    """信号类型枚举"""
    STRONG_BUY = "strong_buy"
    BUY = "buy"
    HOLD = "hold"
    SELL = "sell"
    STRONG_SELL = "strong_sell"

class TradingStrategy:
    """交易策略类"""
    
    def __init__(self):
        self.config = Config()
        
    def analyze_asset(self, asset_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        分析资产并生成交易信号
        
        Args:
            asset_data: 资产数据
            
        Returns:
            Dict: 分析结果
        """
        try:
            # 提取价格数据
            price_data = self._extract_price_data(asset_data)
            if not price_data:
                return self._create_empty_result(asset_data)
            
            # 技术指标分析
            technical_analysis = self._technical_analysis(price_data)
            
            # 机器学习预测
            ml_prediction = ml_predictor.predict(price_data) if ml_predictor.is_trained else None
            
            # 综合信号生成
            signal = self._generate_signal(technical_analysis, ml_prediction)
            
            # 买卖点计算
            entry_exit_points = self._calculate_entry_exit_points(price_data, signal)
            
            # 风险评估
            risk_assessment = self._assess_risk(price_data, technical_analysis)
            
            # 推荐理由
            recommendation_reason = self._generate_recommendation_reason(
                technical_analysis, ml_prediction, signal
            )
            
            return {
                'asset_info': self._extract_asset_info(asset_data),
                'current_price': price_data['close'][-1] if price_data['close'] else 0,
                'signal': signal,
                'technical_analysis': technical_analysis,
                'ml_prediction': ml_prediction,
                'entry_exit_points': entry_exit_points,
                'risk_assessment': risk_assessment,
                'recommendation_reason': recommendation_reason,
                'analysis_time': self._get_current_time()
            }
            
        except Exception as e:
            logger.error(f"分析资产失败: {str(e)}")
            return self._create_empty_result(asset_data)
    
    def _extract_price_data(self, asset_data: Dict[str, Any]) -> Optional[Dict[str, List[float]]]:
        """从资产数据中提取价格数据"""
        try:
            # 根据不同数据源格式提取价格数据
            if 'current_price' in asset_data:  # CoinGecko格式
                return {
                    'close': [float(asset_data.get('current_price', 0))],
                    'high': [float(asset_data.get('high_24h', 0))],
                    'low': [float(asset_data.get('low_24h', 0))],
                    'volume': [float(asset_data.get('total_volume', 0))]
                }
            elif '收盘' in asset_data:  # AkShare格式
                return {
                    'close': [float(asset_data.get('收盘', 0))],
                    'open': [float(asset_data.get('开盘', 0))],
                    'high': [float(asset_data.get('最高', 0))],
                    'low': [float(asset_data.get('最低', 0))],
                    'volume': [float(asset_data.get('成交量', 0))]
                }
            elif 'dwjz' in asset_data:  # 基金格式
                return {
                    'close': [float(asset_data.get('dwjz', 0))],
                    'volume': [1.0]  # 基金没有成交量概念
                }
            
            return None
            
        except Exception as e:
            logger.error(f"提取价格数据失败: {str(e)}")
            return None
    
    def _technical_analysis(self, price_data: Dict[str, List[float]]) -> Dict[str, Any]:
        """技术指标分析"""
        try:
            closes = price_data.get('close', [])
            if len(closes) < 2:
                return {'indicators': {}, 'signals': []}
            
            # 模拟历史数据（实际应用中应该获取真实历史数据）
            historical_closes = self._generate_mock_historical_data(closes[-1], 30)
            
            indicators = {}
            signals = []
            
            # RSI分析
            rsi_values = TechnicalIndicators.rsi(historical_closes, 14)
            if rsi_values:
                current_rsi = rsi_values[-1]
                indicators['rsi'] = current_rsi
                
                if current_rsi < 30:
                    signals.append({'type': 'buy', 'reason': 'RSI超卖', 'strength': 'medium'})
                elif current_rsi > 70:
                    signals.append({'type': 'sell', 'reason': 'RSI超买', 'strength': 'medium'})
            
            # MACD分析
            macd_data = TechnicalIndicators.macd(historical_closes, 12, 26, 9)
            if macd_data['macd'] and macd_data['signal']:
                macd_line = macd_data['macd'][-1]
                signal_line = macd_data['signal'][-1]
                histogram = macd_data['histogram'][-1] if macd_data['histogram'] else 0
                
                indicators['macd'] = {
                    'macd': macd_line,
                    'signal': signal_line,
                    'histogram': histogram
                }
                
                if macd_line > signal_line and histogram > 0:
                    signals.append({'type': 'buy', 'reason': 'MACD金叉', 'strength': 'strong'})
                elif macd_line < signal_line and histogram < 0:
                    signals.append({'type': 'sell', 'reason': 'MACD死叉', 'strength': 'strong'})
            
            # 布林带分析
            bb_data = TechnicalIndicators.bollinger_bands(historical_closes, 20, 2)
            if bb_data['upper'] and bb_data['lower']:
                current_price = closes[-1]
                upper_band = bb_data['upper'][-1]
                lower_band = bb_data['lower'][-1]
                middle_band = bb_data['middle'][-1]
                
                indicators['bollinger_bands'] = {
                    'upper': upper_band,
                    'middle': middle_band,
                    'lower': lower_band,
                    'position': (current_price - lower_band) / (upper_band - lower_band) if upper_band != lower_band else 0.5
                }
                
                if current_price <= lower_band:
                    signals.append({'type': 'buy', 'reason': '价格触及布林带下轨', 'strength': 'medium'})
                elif current_price >= upper_band:
                    signals.append({'type': 'sell', 'reason': '价格触及布林带上轨', 'strength': 'medium'})
            
            # 移动平均线分析
            sma_5 = TechnicalIndicators.sma(historical_closes, 5)
            sma_20 = TechnicalIndicators.sma(historical_closes, 20)
            
            if sma_5 and sma_20:
                current_sma5 = sma_5[-1]
                current_sma20 = sma_20[-1]
                current_price = closes[-1]
                
                indicators['moving_averages'] = {
                    'sma_5': current_sma5,
                    'sma_20': current_sma20,
                    'price_vs_sma5': current_price / current_sma5 if current_sma5 != 0 else 1,
                    'price_vs_sma20': current_price / current_sma20 if current_sma20 != 0 else 1
                }
                
                if current_sma5 > current_sma20 and current_price > current_sma5:
                    signals.append({'type': 'buy', 'reason': '均线多头排列', 'strength': 'medium'})
                elif current_sma5 < current_sma20 and current_price < current_sma5:
                    signals.append({'type': 'sell', 'reason': '均线空头排列', 'strength': 'medium'})
            
            # 成交量分析
            volumes = price_data.get('volume', [])
            if volumes:
                volume_analysis = TechnicalIndicators.volume_analysis(volumes, 10)
                indicators['volume'] = volume_analysis
                
                if volume_analysis['is_abnormal'] and volume_analysis['volume_ratio'] > 2:
                    signals.append({'type': 'buy', 'reason': '成交量异常放大', 'strength': 'medium'})
            
            return {
                'indicators': indicators,
                'signals': signals
            }
            
        except Exception as e:
            logger.error(f"技术分析失败: {str(e)}")
            return {'indicators': {}, 'signals': []}
    
    def _generate_signal(self, technical_analysis: Dict[str, Any], 
                        ml_prediction: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        """生成综合交易信号"""
        try:
            signals = technical_analysis.get('signals', [])
            
            # 统计各类信号
            buy_signals = [s for s in signals if s['type'] == 'buy']
            sell_signals = [s for s in signals if s['type'] == 'sell']
            
            # 计算信号强度
            buy_strength = sum(2 if s['strength'] == 'strong' else 1 for s in buy_signals)
            sell_strength = sum(2 if s['strength'] == 'strong' else 1 for s in sell_signals)
            
            # 机器学习预测权重
            ml_weight = 0
            if ml_prediction:
                probability = ml_prediction.get('probability', 0.5)
                if probability > 0.6:
                    ml_weight = 2
                elif probability > 0.4:
                    ml_weight = 1
                else:
                    ml_weight = -1
            
            # 综合评分
            total_score = buy_strength - sell_strength + ml_weight
            
            # 确定信号类型
            if total_score >= 4:
                signal_type = SignalType.STRONG_BUY
            elif total_score >= 2:
                signal_type = SignalType.BUY
            elif total_score <= -4:
                signal_type = SignalType.STRONG_SELL
            elif total_score <= -2:
                signal_type = SignalType.SELL
            else:
                signal_type = SignalType.HOLD
            
            return {
                'type': signal_type.value,
                'strength': abs(total_score),
                'confidence': self._calculate_confidence(total_score, len(signals)),
                'buy_signals_count': len(buy_signals),
                'sell_signals_count': len(sell_signals),
                'ml_contribution': ml_weight,
                'total_score': total_score
            }
            
        except Exception as e:
            logger.error(f"生成信号失败: {str(e)}")
            return {
                'type': SignalType.HOLD.value,
                'strength': 0,
                'confidence': 'low',
                'buy_signals_count': 0,
                'sell_signals_count': 0,
                'ml_contribution': 0,
                'total_score': 0
            }
    
    def _calculate_entry_exit_points(self, price_data: Dict[str, List[float]], 
                                   signal: Dict[str, Any]) -> Dict[str, Any]:
        """计算买卖点"""
        try:
            current_price = price_data['close'][-1] if price_data['close'] else 0
            
            if current_price == 0:
                return {'entry_price': 0, 'stop_loss': 0, 'take_profit': 0}
            
            signal_type = signal.get('type', 'hold')
            
            if signal_type in ['buy', 'strong_buy']:
                # 买入点设置
                entry_price = current_price * 0.995  # 稍低于当前价格
                stop_loss = current_price * (1 - self.config.RISK_PARAMS['stop_loss_pct'])
                take_profit = current_price * (1 + self.config.RISK_PARAMS['take_profit_pct'])
                
            elif signal_type in ['sell', 'strong_sell']:
                # 卖出点设置
                entry_price = current_price * 1.005  # 稍高于当前价格
                stop_loss = current_price * (1 + self.config.RISK_PARAMS['stop_loss_pct'])
                take_profit = current_price * (1 - self.config.RISK_PARAMS['take_profit_pct'])
                
            else:
                # 持有状态
                entry_price = current_price
                stop_loss = current_price * (1 - self.config.RISK_PARAMS['stop_loss_pct'])
                take_profit = current_price * (1 + self.config.RISK_PARAMS['take_profit_pct'])
            
            return {
                'entry_price': round(entry_price, 4),
                'stop_loss': round(stop_loss, 4),
                'take_profit': round(take_profit, 4),
                'risk_reward_ratio': round(abs(take_profit - entry_price) / abs(entry_price - stop_loss), 2) if abs(entry_price - stop_loss) > 0 else 0
            }
            
        except Exception as e:
            logger.error(f"计算买卖点失败: {str(e)}")
            return {'entry_price': 0, 'stop_loss': 0, 'take_profit': 0, 'risk_reward_ratio': 0}
    
    def _assess_risk(self, price_data: Dict[str, List[float]], 
                    technical_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """风险评估"""
        try:
            closes = price_data.get('close', [])
            if not closes:
                return {'level': 'unknown', 'factors': []}
            
            risk_factors = []
            risk_score = 0
            
            # 波动率风险
            if len(closes) > 1:
                historical_closes = self._generate_mock_historical_data(closes[-1], 20)
                volatility = TechnicalIndicators.calculate_volatility(historical_closes, 20)
                
                if volatility > self.config.RISK_PARAMS['volatility_threshold']:
                    risk_factors.append('高波动率')
                    risk_score += 2
                elif volatility > self.config.RISK_PARAMS['volatility_threshold'] * 0.5:
                    risk_factors.append('中等波动率')
                    risk_score += 1
            
            # 技术指标风险
            indicators = technical_analysis.get('indicators', {})
            
            # RSI风险
            if 'rsi' in indicators:
                rsi = indicators['rsi']
                if rsi > 80 or rsi < 20:
                    risk_factors.append('RSI极值')
                    risk_score += 1
            
            # 布林带风险
            if 'bollinger_bands' in indicators:
                bb_position = indicators['bollinger_bands'].get('position', 0.5)
                if bb_position > 0.9 or bb_position < 0.1:
                    risk_factors.append('价格偏离均值')
                    risk_score += 1
            
            # 成交量风险
            if 'volume' in indicators:
                volume_ratio = indicators['volume'].get('volume_ratio', 1)
                if volume_ratio < 0.5:
                    risk_factors.append('成交量萎缩')
                    risk_score += 1
            
            # 确定风险等级
            if risk_score >= 4:
                risk_level = 'high'
            elif risk_score >= 2:
                risk_level = 'medium'
            else:
                risk_level = 'low'
            
            return {
                'level': risk_level,
                'score': risk_score,
                'factors': risk_factors,
                'volatility': volatility if 'volatility' in locals() else 0
            }
            
        except Exception as e:
            logger.error(f"风险评估失败: {str(e)}")
            return {'level': 'unknown', 'score': 0, 'factors': [], 'volatility': 0}
    
    def _generate_recommendation_reason(self, technical_analysis: Dict[str, Any], 
                                      ml_prediction: Optional[Dict[str, Any]], 
                                      signal: Dict[str, Any]) -> str:
        """生成推荐理由"""
        try:
            reasons = []
            
            # 技术指标理由
            signals = technical_analysis.get('signals', [])
            for s in signals:
                reasons.append(s['reason'])
            
            # 机器学习理由
            if ml_prediction and ml_prediction.get('probability', 0.5) != 0.5:
                probability = ml_prediction['probability']
                if probability > 0.6:
                    reasons.append(f'AI模型预测上涨概率{probability:.1%}')
                elif probability < 0.4:
                    reasons.append(f'AI模型预测下跌概率{1-probability:.1%}')
            
            # 综合信号理由
            signal_type = signal.get('type', 'hold')
            if signal_type in ['strong_buy', 'buy']:
                reasons.append('多项指标显示买入机会')
            elif signal_type in ['strong_sell', 'sell']:
                reasons.append('多项指标显示卖出信号')
            
            return '; '.join(reasons[:3]) if reasons else '暂无明确信号'
            
        except Exception as e:
            logger.error(f"生成推荐理由失败: {str(e)}")
            return '分析异常'
    
    def _generate_mock_historical_data(self, current_price: float, days: int) -> List[float]:
        """生成模拟历史数据（实际应用中应该获取真实数据）"""
        np.random.seed(42)  # 固定随机种子保证一致性
        
        prices = [current_price]
        for i in range(days - 1):
            # 模拟价格随机游走
            change = np.random.normal(0, 0.02)  # 2%的日波动率
            new_price = prices[-1] * (1 + change)
            prices.insert(0, max(new_price, current_price * 0.5))  # 防止价格过低
        
        return prices
    
    def _calculate_confidence(self, score: int, signal_count: int) -> str:
        """计算信号置信度"""
        if abs(score) >= 4 and signal_count >= 3:
            return 'high'
        elif abs(score) >= 2 and signal_count >= 2:
            return 'medium'
        else:
            return 'low'
    
    def _extract_asset_info(self, asset_data: Dict[str, Any]) -> Dict[str, str]:
        """提取资产基本信息"""
        if 'symbol' in asset_data:  # CoinGecko
            return {
                'symbol': asset_data.get('symbol', '').upper(),
                'name': asset_data.get('name', ''),
                'type': 'crypto'
            }
        elif '代码' in asset_data:  # AkShare
            return {
                'symbol': asset_data.get('代码', ''),
                'name': asset_data.get('名称', ''),
                'type': 'stock'
            }
        elif 'fundcode' in asset_data:  # Fund
            return {
                'symbol': asset_data.get('fundcode', ''),
                'name': asset_data.get('name', ''),
                'type': 'fund'
            }
        else:
            return {'symbol': '', 'name': '', 'type': 'unknown'}
    
    def _create_empty_result(self, asset_data: Dict[str, Any]) -> Dict[str, Any]:
        """创建空结果"""
        return {
            'asset_info': self._extract_asset_info(asset_data),
            'current_price': 0,
            'signal': {
                'type': SignalType.HOLD.value,
                'strength': 0,
                'confidence': 'low'
            },
            'technical_analysis': {'indicators': {}, 'signals': []},
            'ml_prediction': None,
            'entry_exit_points': {'entry_price': 0, 'stop_loss': 0, 'take_profit': 0},
            'risk_assessment': {'level': 'unknown', 'factors': []},
            'recommendation_reason': '数据不足',
            'analysis_time': self._get_current_time()
        }
    
    def _get_current_time(self) -> str:
        """获取当前时间"""
        from datetime import datetime
        return datetime.now().strftime('%Y-%m-%d %H:%M:%S')

# 全局交易策略实例
trading_strategy = TradingStrategy()

