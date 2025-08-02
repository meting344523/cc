from flask import Blueprint, jsonify, request
from loguru import logger

from src.data_sources.data_manager import data_manager
from src.strategies.trading_strategy import trading_strategy

market_bp = Blueprint('market', __name__)

@market_bp.route('/market-data', methods=['GET'])
def get_market_data():
    """获取所有市场数据"""
    try:
        # 确保数据管理器正在运行
        if not data_manager.is_running:
            data_manager.start_data_updates()
        
        # 获取所有市场数据
        all_data = data_manager.get_all_data()
        
        return jsonify({
            'success': True,
            'data': all_data,
            'message': '数据获取成功'
        })
        
    except Exception as e:
        logger.error(f"获取市场数据失败: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e),
            'message': '获取市场数据失败'
        }), 500

@market_bp.route('/asset-analysis/<asset_type>/<asset_id>', methods=['GET'])
def get_asset_analysis(asset_type, asset_id):
    """获取资产分析详情"""
    try:
        # 验证资产类型
        if asset_type not in ['crypto', 'stock', 'fund']:
            return jsonify({
                'success': False,
                'error': '不支持的资产类型',
                'message': '资产类型必须是 crypto、stock 或 fund'
            }), 400
        
        # 获取对应市场的数据
        market_data = getattr(data_manager, f'get_{asset_type}_data')(50)
        
        # 查找指定资产
        asset_data = None
        for asset in market_data:
            if asset_type == 'crypto' and asset.get('id') == asset_id:
                asset_data = asset
                break
            elif asset_type == 'stock' and asset.get('代码') == asset_id:
                asset_data = asset
                break
            elif asset_type == 'fund' and asset.get('fundcode') == asset_id:
                asset_data = asset
                break
        
        if not asset_data:
            return jsonify({
                'success': False,
                'error': '未找到指定资产',
                'message': f'未找到ID为 {asset_id} 的{asset_type}资产'
            }), 404
        
        # 进行策略分析
        analysis_result = trading_strategy.analyze_asset(asset_data)
        
        return jsonify({
            'success': True,
            'data': analysis_result,
            'message': '资产分析完成'
        })
        
    except Exception as e:
        logger.error(f"资产分析失败: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e),
            'message': '资产分析失败'
        }), 500

@market_bp.route('/data-status', methods=['GET'])
def get_data_status():
    """获取数据状态信息"""
    try:
        status = data_manager.get_data_status()
        
        return jsonify({
            'success': True,
            'data': status,
            'message': '状态获取成功'
        })
        
    except Exception as e:
        logger.error(f"获取数据状态失败: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e),
            'message': '获取数据状态失败'
        }), 500

@market_bp.route('/force-update', methods=['POST'])
def force_update_data():
    """强制更新所有数据"""
    try:
        # 启动数据管理器（如果未运行）
        if not data_manager.is_running:
            data_manager.start_data_updates()
        
        # 强制更新数据
        data_manager.force_update_all()
        
        return jsonify({
            'success': True,
            'message': '数据更新完成'
        })
        
    except Exception as e:
        logger.error(f"强制更新数据失败: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e),
            'message': '数据更新失败'
        }), 500

@market_bp.route('/recommendations', methods=['GET'])
def get_recommendations():
    """获取推荐资产列表"""
    try:
        # 获取查询参数
        market_type = request.args.get('type', 'all')  # all, crypto, stock, fund
        limit = int(request.args.get('limit', 5))
        
        recommendations = []
        
        if market_type in ['all', 'crypto']:
            crypto_data = data_manager.get_crypto_data(limit)
            for crypto in crypto_data:
                analysis = trading_strategy.analyze_asset(crypto)
                if analysis['signal']['type'] in ['buy', 'strong_buy']:
                    recommendations.append({
                        'type': 'crypto',
                        'data': crypto,
                        'analysis': analysis
                    })
        
        if market_type in ['all', 'stock']:
            stock_data = data_manager.get_stock_data(limit)
            for stock in stock_data:
                analysis = trading_strategy.analyze_asset(stock)
                if analysis['signal']['type'] in ['buy', 'strong_buy']:
                    recommendations.append({
                        'type': 'stock',
                        'data': stock,
                        'analysis': analysis
                    })
        
        if market_type in ['all', 'fund']:
            fund_data = data_manager.get_fund_data(limit)
            for fund in fund_data:
                analysis = trading_strategy.analyze_asset(fund)
                if analysis['signal']['type'] in ['buy', 'strong_buy']:
                    recommendations.append({
                        'type': 'fund',
                        'data': fund,
                        'analysis': analysis
                    })
        
        # 按信号强度排序
        recommendations.sort(key=lambda x: x['analysis']['signal']['strength'], reverse=True)
        
        return jsonify({
            'success': True,
            'data': recommendations[:limit],
            'message': f'获取到 {len(recommendations[:limit])} 个推荐'
        })
        
    except Exception as e:
        logger.error(f"获取推荐失败: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e),
            'message': '获取推荐失败'
        }), 500

@market_bp.route('/market-overview', methods=['GET'])
def get_market_overview():
    """获取市场概览"""
    try:
        # 获取各市场统计数据
        crypto_data = data_manager.get_crypto_data(100)
        stock_data = data_manager.get_stock_data(100)
        fund_data = data_manager.get_fund_data(50)
        
        # 计算统计信息
        overview = {
            'crypto': {
                'total_count': len(crypto_data),
                'avg_change': sum(c.get('price_change_percentage_24h', 0) for c in crypto_data) / len(crypto_data) if crypto_data else 0,
                'positive_count': sum(1 for c in crypto_data if c.get('price_change_percentage_24h', 0) > 0),
                'negative_count': sum(1 for c in crypto_data if c.get('price_change_percentage_24h', 0) < 0)
            },
            'stock': {
                'total_count': len(stock_data),
                'avg_change': sum(float(s.get('涨跌幅', 0)) for s in stock_data) / len(stock_data) if stock_data else 0,
                'positive_count': sum(1 for s in stock_data if float(s.get('涨跌幅', 0)) > 0),
                'negative_count': sum(1 for s in stock_data if float(s.get('涨跌幅', 0)) < 0)
            },
            'fund': {
                'total_count': len(fund_data),
                'avg_change': sum(float(f.get('gszzl', 0)) for f in fund_data) / len(fund_data) if fund_data else 0,
                'positive_count': sum(1 for f in fund_data if float(f.get('gszzl', 0)) > 0),
                'negative_count': sum(1 for f in fund_data if float(f.get('gszzl', 0)) < 0)
            }
        }
        
        return jsonify({
            'success': True,
            'data': overview,
            'message': '市场概览获取成功'
        })
        
    except Exception as e:
        logger.error(f"获取市场概览失败: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e),
            'message': '获取市场概览失败'
        }), 500

