import os
import sys
import signal
import atexit
from threading import Thread

# DON'T CHANGE THIS !!!
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from flask import Flask, send_from_directory
from flask_cors import CORS
from src.models.user import db
from src.routes.user import user_bp
from src.routes.market import market_bp
from src.data_sources.data_manager import data_manager
from src.utils.logger import logger
from src.config.settings import config

def create_app(config_name='default'):
    """应用工厂函数"""
    app = Flask(__name__, static_folder=os.path.join(os.path.dirname(__file__), 'static'))
    
    # 加载配置
    app.config.from_object(config[config_name])
    
    # 启用CORS
    CORS(app, origins="*", allow_headers=["Content-Type", "Authorization"])
    
    # 初始化数据库
    db.init_app(app)
    with app.app_context():
        db.create_all()
    
    # 注册蓝图
    app.register_blueprint(user_bp, url_prefix='/api')
    app.register_blueprint(market_bp, url_prefix='/api')
    
    # 静态文件路由
    @app.route('/', defaults={'path': ''})
    @app.route('/<path:path>')
    def serve(path):
        static_folder_path = app.static_folder
        if static_folder_path is None:
            return "Static folder not configured", 404

        if path != "" and os.path.exists(os.path.join(static_folder_path, path)):
            return send_from_directory(static_folder_path, path)
        else:
            index_path = os.path.join(static_folder_path, 'index.html')
            if os.path.exists(index_path):
                return send_from_directory(static_folder_path, 'index.html')
            else:
                return "index.html not found", 404
    
    # 健康检查端点
    @app.route('/health')
    def health_check():
        return {
            'status': 'healthy',
            'data_manager_running': data_manager.is_running,
            'message': '量化分析系统运行正常'
        }
    
    # 系统信息端点
    @app.route('/api/system-info')
    def system_info():
        return {
            'name': '量化分析系统',
            'version': '1.0.0',
            'description': '24小时全天候量化分析系统',
            'features': [
                '多市场实时数据接入',
                '智能技术指标分析',
                'AI机器学习预测',
                '买卖点识别',
                '风险控制策略'
            ],
            'data_sources': ['CoinGecko', 'AkShare', '天天基金网'],
            'status': 'running'
        }
    
    return app

def start_background_services():
    """启动后台服务"""
    logger.info("启动后台数据服务...")
    
    # 启动数据管理器
    data_manager.start_data_updates()
    
    # 初始化数据（异步）
    def init_data():
        try:
            logger.info("开始初始化数据...")
            data_manager.force_update_all()
            logger.info("数据初始化完成")
        except Exception as e:
            logger.error(f"数据初始化失败: {str(e)}")
    
    # 在后台线程中初始化数据
    init_thread = Thread(target=init_data, daemon=True)
    init_thread.start()

def stop_background_services():
    """停止后台服务"""
    logger.info("停止后台服务...")
    data_manager.stop_data_updates()

def signal_handler(signum, frame):
    """信号处理器"""
    logger.info(f"接收到信号 {signum}，正在关闭应用...")
    stop_background_services()
    sys.exit(0)

# 创建应用实例
app = create_app(os.getenv('FLASK_ENV', 'default'))

if __name__ == '__main__':
    # 注册信号处理器
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # 注册退出处理器
    atexit.register(stop_background_services)
    
    try:
        # 启动后台服务
        start_background_services()
        
        logger.info("量化分析系统启动中...")
        logger.info("访问地址: http://0.0.0.0:5000")
        
        # 启动Flask应用
        app.run(
            host='0.0.0.0', 
            port=int(os.getenv('PORT', 5000)), 
            debug=os.getenv('DEBUG', 'False').lower() == 'true',
            threaded=True
        )
        
    except KeyboardInterrupt:
        logger.info("用户中断，正在关闭应用...")
    except Exception as e:
        logger.error(f"应用启动失败: {str(e)}")
    finally:
        stop_background_services()

