import numpy as np
import pandas as pd
from typing import List, Dict, Any, Optional, Tuple
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score
from loguru import logger
import joblib
import os

from src.analysis.technical_indicators import TechnicalIndicators
from src.config.settings import Config

class MLPredictor:
    """机器学习预测器"""
    
    def __init__(self):
        self.config = Config()
        self.model = LogisticRegression(random_state=42)
        self.scaler = StandardScaler()
        self.is_trained = False
        self.feature_names = []
        
    def prepare_features(self, price_data: Dict[str, List[float]]) -> Optional[np.ndarray]:
        """
        准备特征数据
        
        Args:
            price_data: 包含OHLCV数据的字典
            
        Returns:
            np.ndarray: 特征矩阵
        """
        try:
            opens = price_data.get('open', [])
            highs = price_data.get('high', [])
            lows = price_data.get('low', [])
            closes = price_data.get('close', [])
            volumes = price_data.get('volume', [])
            
            if len(closes) < 30:  # 至少需要30天数据
                return None
            
            features = []
            
            # 技术指标特征
            rsi = TechnicalIndicators.rsi(closes, 14)
            macd_data = TechnicalIndicators.macd(closes, 12, 26, 9)
            bb_data = TechnicalIndicators.bollinger_bands(closes, 20, 2)
            sma_5 = TechnicalIndicators.sma(closes, 5)
            sma_20 = TechnicalIndicators.sma(closes, 20)
            ema_12 = TechnicalIndicators.ema(closes, 12)
            ema_26 = TechnicalIndicators.ema(closes, 26)
            
            # 确定最小长度
            min_length = min(len(rsi), len(macd_data['macd']), len(bb_data['middle']), 
                           len(sma_5), len(sma_20), len(ema_12), len(ema_26))
            
            if min_length == 0:
                return None
            
            # 构建特征矩阵
            for i in range(min_length):
                feature_row = []
                
                # 价格相关特征
                current_price = closes[-(min_length-i)]
                prev_price = closes[-(min_length-i+1)] if (min_length-i+1) <= len(closes) else current_price
                
                # 价格变化率
                price_change = (current_price - prev_price) / prev_price if prev_price != 0 else 0
                feature_row.append(price_change)
                
                # RSI
                feature_row.append(rsi[i] / 100.0)  # 归一化到0-1
                
                # MACD
                feature_row.append(macd_data['macd'][i])
                feature_row.append(macd_data['signal'][i] if i < len(macd_data['signal']) else 0)
                feature_row.append(macd_data['histogram'][i] if i < len(macd_data['histogram']) else 0)
                
                # 布林带位置
                bb_position = ((current_price - bb_data['lower'][i]) / 
                             (bb_data['upper'][i] - bb_data['lower'][i])) if bb_data['upper'][i] != bb_data['lower'][i] else 0.5
                feature_row.append(bb_position)
                
                # 移动平均线
                sma5_ratio = current_price / sma_5[i] if sma_5[i] != 0 else 1
                sma20_ratio = current_price / sma_20[i] if sma_20[i] != 0 else 1
                ema12_ratio = current_price / ema_12[i] if ema_12[i] != 0 else 1
                ema26_ratio = current_price / ema_26[i] if ema_26[i] != 0 else 1
                
                feature_row.extend([sma5_ratio, sma20_ratio, ema12_ratio, ema26_ratio])
                
                # 成交量特征
                if volumes and len(volumes) > (min_length-i):
                    current_volume = volumes[-(min_length-i)]
                    avg_volume = sum(volumes[-(min_length-i+10):-(min_length-i)]) / 10 if len(volumes) >= (min_length-i+10) else current_volume
                    volume_ratio = current_volume / avg_volume if avg_volume != 0 else 1
                    feature_row.append(volume_ratio)
                else:
                    feature_row.append(1.0)
                
                # 波动率
                volatility = TechnicalIndicators.calculate_volatility(closes[:-(min_length-i-1)] if (min_length-i-1) > 0 else closes, 10)
                feature_row.append(volatility)
                
                # K线形态特征
                if len(opens) > (min_length-i) and len(highs) > (min_length-i) and len(lows) > (min_length-i):
                    pattern_data = TechnicalIndicators.k_line_pattern_analysis(
                        opens[:-(min_length-i-1)] if (min_length-i-1) > 0 else opens,
                        highs[:-(min_length-i-1)] if (min_length-i-1) > 0 else highs,
                        lows[:-(min_length-i-1)] if (min_length-i-1) > 0 else lows,
                        closes[:-(min_length-i-1)] if (min_length-i-1) > 0 else closes
                    )
                    
                    # 将形态信号转换为数值
                    signal_value = 1 if pattern_data['signal'] == 'bullish' else (-1 if pattern_data['signal'] == 'bearish' else 0)
                    feature_row.append(signal_value)
                else:
                    feature_row.append(0)
                
                features.append(feature_row)
            
            # 设置特征名称
            self.feature_names = [
                'price_change', 'rsi', 'macd', 'macd_signal', 'macd_histogram',
                'bb_position', 'sma5_ratio', 'sma20_ratio', 'ema12_ratio', 'ema26_ratio',
                'volume_ratio', 'volatility', 'pattern_signal'
            ]
            
            return np.array(features)
            
        except Exception as e:
            logger.error(f"准备特征数据失败: {str(e)}")
            return None
    
    def prepare_labels(self, closes: List[float], prediction_days: int = 3, target_return: float = 0.05) -> Optional[np.ndarray]:
        """
        准备标签数据
        
        Args:
            closes: 收盘价列表
            prediction_days: 预测天数
            target_return: 目标收益率
            
        Returns:
            np.ndarray: 标签数组
        """
        try:
            labels = []
            
            for i in range(len(closes) - prediction_days):
                current_price = closes[i]
                future_price = closes[i + prediction_days]
                
                # 计算未来收益率
                return_rate = (future_price - current_price) / current_price if current_price != 0 else 0
                
                # 标签：1表示达到目标收益率，0表示未达到
                label = 1 if return_rate >= target_return else 0
                labels.append(label)
            
            return np.array(labels)
            
        except Exception as e:
            logger.error(f"准备标签数据失败: {str(e)}")
            return None
    
    def train_model(self, training_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        训练模型
        
        Args:
            training_data: 训练数据列表
            
        Returns:
            Dict: 训练结果
        """
        try:
            all_features = []
            all_labels = []
            
            logger.info(f"开始训练模型，数据量: {len(training_data)}")
            
            # 处理每个样本的数据
            for data in training_data:
                features = self.prepare_features(data['price_data'])
                labels = self.prepare_labels(
                    data['price_data']['close'], 
                    self.config.MODEL_PARAMS['prediction_days'],
                    self.config.MODEL_PARAMS['target_return']
                )
                
                if features is not None and labels is not None:
                    # 确保特征和标签长度匹配
                    min_length = min(len(features), len(labels))
                    if min_length > 0:
                        all_features.extend(features[:min_length])
                        all_labels.extend(labels[:min_length])
            
            if len(all_features) == 0:
                return {'success': False, 'error': '没有有效的训练数据'}
            
            X = np.array(all_features)
            y = np.array(all_labels)
            
            # 数据标准化
            X_scaled = self.scaler.fit_transform(X)
            
            # 分割训练和测试集
            X_train, X_test, y_train, y_test = train_test_split(
                X_scaled, y, 
                test_size=1-self.config.MODEL_PARAMS['train_test_split'], 
                random_state=42,
                stratify=y if len(np.unique(y)) > 1 else None
            )
            
            # 训练模型
            self.model.fit(X_train, y_train)
            self.is_trained = True
            
            # 评估模型
            y_pred = self.model.predict(X_test)
            y_pred_proba = self.model.predict_proba(X_test)[:, 1]
            
            metrics = {
                'accuracy': accuracy_score(y_test, y_pred),
                'precision': precision_score(y_test, y_pred, zero_division=0),
                'recall': recall_score(y_test, y_pred, zero_division=0),
                'f1_score': f1_score(y_test, y_pred, zero_division=0)
            }
            
            logger.info(f"模型训练完成，准确率: {metrics['accuracy']:.3f}")
            
            return {
                'success': True,
                'metrics': metrics,
                'training_samples': len(X_train),
                'test_samples': len(X_test),
                'feature_count': X.shape[1]
            }
            
        except Exception as e:
            logger.error(f"模型训练失败: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    def predict(self, price_data: Dict[str, List[float]]) -> Optional[Dict[str, Any]]:
        """
        进行预测
        
        Args:
            price_data: 价格数据
            
        Returns:
            Dict: 预测结果
        """
        if not self.is_trained:
            logger.warning("模型未训练，无法进行预测")
            return None
        
        try:
            features = self.prepare_features(price_data)
            if features is None:
                return None
            
            # 取最新的特征
            latest_features = features[-1:] if len(features) > 0 else None
            if latest_features is None:
                return None
            
            # 标准化
            features_scaled = self.scaler.transform(latest_features)
            
            # 预测
            probability = self.model.predict_proba(features_scaled)[0, 1]
            prediction = self.model.predict(features_scaled)[0]
            
            # 获取特征重要性（系数）
            feature_importance = {}
            if hasattr(self.model, 'coef_') and len(self.feature_names) == len(self.model.coef_[0]):
                for i, name in enumerate(self.feature_names):
                    feature_importance[name] = float(self.model.coef_[0][i])
            
            return {
                'probability': float(probability),
                'prediction': int(prediction),
                'confidence': 'high' if probability > 0.7 or probability < 0.3 else 'medium',
                'feature_importance': feature_importance
            }
            
        except Exception as e:
            logger.error(f"预测失败: {str(e)}")
            return None
    
    def save_model(self, filepath: str) -> bool:
        """
        保存模型
        
        Args:
            filepath: 文件路径
            
        Returns:
            bool: 是否成功
        """
        try:
            model_data = {
                'model': self.model,
                'scaler': self.scaler,
                'is_trained': self.is_trained,
                'feature_names': self.feature_names
            }
            
            os.makedirs(os.path.dirname(filepath), exist_ok=True)
            joblib.dump(model_data, filepath)
            
            logger.info(f"模型已保存到: {filepath}")
            return True
            
        except Exception as e:
            logger.error(f"保存模型失败: {str(e)}")
            return False
    
    def load_model(self, filepath: str) -> bool:
        """
        加载模型
        
        Args:
            filepath: 文件路径
            
        Returns:
            bool: 是否成功
        """
        try:
            if not os.path.exists(filepath):
                logger.warning(f"模型文件不存在: {filepath}")
                return False
            
            model_data = joblib.load(filepath)
            
            self.model = model_data['model']
            self.scaler = model_data['scaler']
            self.is_trained = model_data['is_trained']
            self.feature_names = model_data['feature_names']
            
            logger.info(f"模型已加载: {filepath}")
            return True
            
        except Exception as e:
            logger.error(f"加载模型失败: {str(e)}")
            return False

# 全局ML预测器实例
ml_predictor = MLPredictor()

