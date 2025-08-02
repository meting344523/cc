import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    """系统配置类"""
    
    # Flask配置
    SECRET_KEY = os.getenv('SECRET_KEY', 'quantitative-analysis-secret-key-2024')
    DEBUG = os.getenv('DEBUG', 'False').lower() == 'true'
    
    # 数据库配置
    DATABASE_URL = os.getenv('DATABASE_URL', f'sqlite:///{os.path.join(os.path.dirname(os.path.dirname(__file__)), "database", "app.db")}')
    SQLALCHEMY_DATABASE_URI = DATABASE_URL
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Redis缓存配置
    REDIS_URL = os.getenv('REDIS_URL', 'redis://localhost:6379/0')
    CACHE_EXPIRE_TIME = int(os.getenv('CACHE_EXPIRE_TIME', '300'))  # 5分钟
    
    # API限速配置
    API_RATE_LIMIT = {
        'coingecko': {
            'requests_per_minute': 10,
            'requests_per_hour': 1000
        },
        'akshare': {
            'requests_per_minute': 30,
            'requests_per_hour': 1000
        },
        'fund': {
            'requests_per_minute': 20,
            'requests_per_hour': 500
        }
    }
    
    # 数据更新间隔（秒）
    UPDATE_INTERVALS = {
        'crypto': 60,      # 加密货币1分钟更新
        'stock': 300,      # 股票5分钟更新
        'fund': 600        # 基金10分钟更新
    }
    
    # 基金代码池（20-50只基金）
    FUND_CODES = [
        '000001',  # 华夏成长混合
        '110022',  # 易方达消费行业股票
        '161725',  # 招商中证白酒指数
        '000248',  # 汇添富中证主要消费ETF联接
        '519674',  # 银河创新成长混合
        '110011',  # 易方达中小盘混合
        '000083',  # 汇添富消费行业混合
        '001102',  # 前海开源国家比较优势混合
        '000991',  # 工银战略转型股票
        '001156',  # 申万菱信中证申万医药生物指数
        '000968',  # 广发养老指数
        '001618',  # 天弘中证电子ETF联接A
        '000209',  # 信诚新兴产业混合
        '001875',  # 前海开源沪港深优势精选混合
        '000751',  # 嘉实新兴产业股票
        '001549',  # 天弘中证计算机ETF联接A
        '000854',  # 鹏华养老产业股票
        '001632',  # 天弘中证证券保险ETF联接A
        '000390',  # 华商优势行业混合
        '001513',  # 华夏经济转型股票
        '002560',  # 诺安和鑫保本混合
        '000529',  # 广发竞争优势混合
        '001510',  # 富国新动力灵活配置混合A
        '000697',  # 汇添富移动互联股票
        '001717',  # 工银前沿医疗股票
        '000595',  # 嘉实泰和混合
        '001508',  # 富国新动力灵活配置混合C
        '000592',  # 建信改革红利股票
        '001838',  # 国投瑞银新兴产业混合
        '000913',  # 农银汇理主题轮动混合
    ]
    
    # 技术指标参数
    TECHNICAL_PARAMS = {
        'rsi_period': 14,
        'macd_fast': 12,
        'macd_slow': 26,
        'macd_signal': 9,
        'sma_short': 5,
        'sma_long': 20,
        'ema_short': 12,
        'ema_long': 26,
        'bb_period': 20,
        'bb_std': 2
    }
    
    # 预测模型参数
    MODEL_PARAMS = {
        'prediction_days': 3,      # 预测未来3天
        'target_return': 0.05,     # 目标涨幅5%
        'lookback_days': 30,       # 历史数据回看30天
        'train_test_split': 0.8    # 训练测试集分割比例
    }
    
    # 风险控制参数
    RISK_PARAMS = {
        'stop_loss_pct': 0.05,     # 止损5%
        'take_profit_pct': 0.15,   # 止盈15%
        'volatility_threshold': 0.3, # 波动率阈值
        'volume_threshold': 1.5     # 成交量异常阈值
    }

# 开发环境配置
class DevelopmentConfig(Config):
    DEBUG = True
    
# 生产环境配置
class ProductionConfig(Config):
    DEBUG = False
    
# 配置字典
config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}

