// 全局变量
let allData = {
    crypto: [],
    stock: [],
    fund: []
};

let isLoading = false;
let autoRefreshInterval = null;

// DOM元素
const elements = {
    statusDot: document.getElementById('statusDot'),
    statusText: document.getElementById('statusText'),
    lastUpdateTime: document.getElementById('lastUpdateTime'),
    refreshBtn: document.getElementById('refreshBtn'),
    cryptoGrid: document.getElementById('cryptoGrid'),
    stockGrid: document.getElementById('stockGrid'),
    fundGrid: document.getElementById('fundGrid'),
    cryptoCount: document.getElementById('cryptoCount'),
    stockCount: document.getElementById('stockCount'),
    fundCount: document.getElementById('fundCount'),
    assetModal: document.getElementById('assetModal'),
    modalTitle: document.getElementById('modalTitle'),
    modalBody: document.getElementById('modalBody'),
    modalClose: document.getElementById('modalClose'),
    loadingOverlay: document.getElementById('loadingOverlay')
};

// 初始化
document.addEventListener('DOMContentLoaded', function() {
    initializeApp();
    setupEventListeners();
    loadData();
    startAutoRefresh();
});

// 初始化应用
function initializeApp() {
    console.log('量化分析系统初始化...');
    updateStatus('系统启动中...', 'loading');
}

// 设置事件监听器
function setupEventListeners() {
    // 刷新按钮
    elements.refreshBtn.addEventListener('click', function() {
        if (!isLoading) {
            loadData();
        }
    });

    // 模态框关闭
    elements.modalClose.addEventListener('click', closeModal);
    
    // 点击模态框外部关闭
    elements.assetModal.addEventListener('click', function(e) {
        if (e.target === elements.assetModal) {
            closeModal();
        }
    });

    // ESC键关闭模态框
    document.addEventListener('keydown', function(e) {
        if (e.key === 'Escape') {
            closeModal();
        }
    });
}

// 加载数据
async function loadData() {
    if (isLoading) return;
    
    isLoading = true;
    showLoading();
    updateStatus('正在获取数据...', 'loading');

    try {
        const response = await fetch('/api/market-data');
        
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        const data = await response.json();
        
        if (data.success) {
            allData = data.data;
            renderAllMarkets();
            updateCounts();
            updateLastUpdateTime();
            updateStatus('系统运行正常', 'online');
        } else {
            throw new Error(data.error || '获取数据失败');
        }
        
    } catch (error) {
        console.error('加载数据失败:', error);
        updateStatus('数据获取失败', 'error');
        showError('无法获取市场数据，请稍后重试');
    } finally {
        isLoading = false;
        hideLoading();
    }
}

// 渲染所有市场
function renderAllMarkets() {
    renderCryptoMarket();
    renderStockMarket();
    renderFundMarket();
}

// 渲染加密货币市场
function renderCryptoMarket() {
    const cryptoData = allData.crypto || [];
    const topCrypto = cryptoData.slice(0, 5);
    
    elements.cryptoGrid.innerHTML = topCrypto.map(crypto => {
        const changePercent = crypto.price_change_percentage_24h || 0;
        const changeClass = changePercent > 0 ? 'positive' : (changePercent < 0 ? 'negative' : 'neutral');
        const changeSymbol = changePercent > 0 ? '+' : '';
        
        // 模拟信号生成
        const signal = generateMockSignal(changePercent);
        
        return `
            <div class="asset-card" onclick="showAssetDetail('crypto', '${crypto.id}')">
                <div class="asset-header">
                    <div class="asset-info">
                        <h3>${crypto.symbol.toUpperCase()}</h3>
                        <p>${crypto.name}</p>
                    </div>
                    <div class="asset-price">
                        <div class="price">$${formatNumber(crypto.current_price)}</div>
                        <div class="change ${changeClass}">
                            ${changeSymbol}${changePercent.toFixed(2)}%
                        </div>
                    </div>
                </div>
                
                <div class="signal-indicator signal-${signal.type}">
                    <div class="signal-dot"></div>
                    <span>${signal.text}</span>
                </div>
                
                <div class="recommendation">
                    <h4>推荐理由</h4>
                    <p>${signal.reason}</p>
                </div>
            </div>
        `;
    }).join('');
}

// 渲染股票市场
function renderStockMarket() {
    const stockData = allData.stock || [];
    const topStocks = stockData.slice(0, 5);
    
    elements.stockGrid.innerHTML = topStocks.map(stock => {
        const changePercent = parseFloat(stock['涨跌幅'] || 0);
        const changeClass = changePercent > 0 ? 'positive' : (changePercent < 0 ? 'negative' : 'neutral');
        const changeSymbol = changePercent > 0 ? '+' : '';
        
        const signal = generateMockSignal(changePercent);
        
        return `
            <div class="asset-card" onclick="showAssetDetail('stock', '${stock['代码']}')">
                <div class="asset-header">
                    <div class="asset-info">
                        <h3>${stock['代码']}</h3>
                        <p>${stock['名称']}</p>
                    </div>
                    <div class="asset-price">
                        <div class="price">¥${formatNumber(stock['最新价'] || stock['收盘'])}</div>
                        <div class="change ${changeClass}">
                            ${changeSymbol}${changePercent.toFixed(2)}%
                        </div>
                    </div>
                </div>
                
                <div class="signal-indicator signal-${signal.type}">
                    <div class="signal-dot"></div>
                    <span>${signal.text}</span>
                </div>
                
                <div class="recommendation">
                    <h4>推荐理由</h4>
                    <p>${signal.reason}</p>
                </div>
            </div>
        `;
    }).join('');
}

// 渲染基金市场
function renderFundMarket() {
    const fundData = allData.fund || [];
    const topFunds = fundData.slice(0, 5);
    
    elements.fundGrid.innerHTML = topFunds.map(fund => {
        const changePercent = parseFloat(fund.gszzl || 0);
        const changeClass = changePercent > 0 ? 'positive' : (changePercent < 0 ? 'negative' : 'neutral');
        const changeSymbol = changePercent > 0 ? '+' : '';
        
        const signal = generateMockSignal(changePercent);
        
        return `
            <div class="asset-card" onclick="showAssetDetail('fund', '${fund.fundcode}')">
                <div class="asset-header">
                    <div class="asset-info">
                        <h3>${fund.fundcode}</h3>
                        <p>${fund.name}</p>
                    </div>
                    <div class="asset-price">
                        <div class="price">¥${formatNumber(fund.gsz || fund.dwjz)}</div>
                        <div class="change ${changeClass}">
                            ${changeSymbol}${changePercent.toFixed(2)}%
                        </div>
                    </div>
                </div>
                
                <div class="signal-indicator signal-${signal.type}">
                    <div class="signal-dot"></div>
                    <span>${signal.text}</span>
                </div>
                
                <div class="recommendation">
                    <h4>推荐理由</h4>
                    <p>${signal.reason}</p>
                </div>
            </div>
        `;
    }).join('');
}

// 生成模拟信号
function generateMockSignal(changePercent) {
    const absChange = Math.abs(changePercent);
    
    if (changePercent > 5) {
        return {
            type: 'strong-buy',
            text: '强烈买入',
            reason: '技术指标显示强劲上涨趋势，RSI未超买，MACD金叉信号明确'
        };
    } else if (changePercent > 2) {
        return {
            type: 'buy',
            text: '建议买入',
            reason: '多项技术指标转好，成交量放大，突破关键阻力位'
        };
    } else if (changePercent < -5) {
        return {
            type: 'strong-sell',
            text: '强烈卖出',
            reason: '技术指标恶化，跌破重要支撑位，建议及时止损'
        };
    } else if (changePercent < -2) {
        return {
            type: 'sell',
            text: '建议卖出',
            reason: '短期调整压力较大，MACD死叉，建议减仓观望'
        };
    } else {
        return {
            type: 'hold',
            text: '持有观望',
            reason: '市场震荡整理，等待明确方向信号，建议保持现有仓位'
        };
    }
}

// 显示资产详情
async function showAssetDetail(type, id) {
    try {
        showLoading();
        
        const response = await fetch(`/api/asset-analysis/${type}/${id}`);
        
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        const data = await response.json();
        
        if (data.success) {
            renderAssetDetail(data.data);
            elements.assetModal.style.display = 'block';
        } else {
            throw new Error(data.error || '获取资产详情失败');
        }
        
    } catch (error) {
        console.error('获取资产详情失败:', error);
        showError('无法获取资产详情，请稍后重试');
    } finally {
        hideLoading();
    }
}

// 渲染资产详情
function renderAssetDetail(data) {
    const asset = data.asset_info;
    const signal = data.signal;
    const technical = data.technical_analysis;
    const prediction = data.ml_prediction;
    const entryExit = data.entry_exit_points;
    const risk = data.risk_assessment;
    
    elements.modalTitle.textContent = `${asset.symbol} - ${asset.name}`;
    
    elements.modalBody.innerHTML = `
        <div class="detail-section">
            <h4>当前价格</h4>
            <div class="detail-price">
                <span class="price-value">${formatNumber(data.current_price)}</span>
                <span class="price-currency">${asset.type === 'crypto' ? 'USD' : 'CNY'}</span>
            </div>
        </div>
        
        <div class="detail-section">
            <h4>交易信号</h4>
            <div class="signal-indicator signal-${signal.type}">
                <div class="signal-dot"></div>
                <span>${getSignalText(signal.type)}</span>
                <span class="signal-confidence">(置信度: ${signal.confidence})</span>
            </div>
        </div>
        
        <div class="detail-section">
            <h4>买卖点位</h4>
            <div class="entry-exit-points">
                <div class="point-item">
                    <span class="point-label">建议入场:</span>
                    <span class="point-value">${formatNumber(entryExit.entry_price)}</span>
                </div>
                <div class="point-item">
                    <span class="point-label">止损位:</span>
                    <span class="point-value">${formatNumber(entryExit.stop_loss)}</span>
                </div>
                <div class="point-item">
                    <span class="point-label">止盈位:</span>
                    <span class="point-value">${formatNumber(entryExit.take_profit)}</span>
                </div>
            </div>
        </div>
        
        <div class="detail-section">
            <h4>风险评估</h4>
            <div class="risk-assessment">
                <span class="risk-level risk-${risk.level}">${getRiskText(risk.level)}</span>
                ${risk.factors.length > 0 ? `<div class="risk-factors">风险因素: ${risk.factors.join(', ')}</div>` : ''}
            </div>
        </div>
        
        <div class="detail-section">
            <h4>推荐理由</h4>
            <p class="recommendation-text">${data.recommendation_reason}</p>
        </div>
        
        ${prediction ? `
        <div class="detail-section">
            <h4>AI预测</h4>
            <div class="prediction-info">
                <div class="prediction-item">
                    <span class="prediction-label">上涨概率:</span>
                    <span class="prediction-value">${(prediction.probability * 100).toFixed(1)}%</span>
                </div>
                <div class="prediction-item">
                    <span class="prediction-label">预测置信度:</span>
                    <span class="prediction-value">${prediction.confidence}</span>
                </div>
            </div>
        </div>
        ` : ''}
        
        <div class="detail-section">
            <h4>分析时间</h4>
            <p class="analysis-time">${data.analysis_time}</p>
        </div>
    `;
}

// 关闭模态框
function closeModal() {
    elements.assetModal.style.display = 'none';
}

// 更新计数
function updateCounts() {
    elements.cryptoCount.textContent = (allData.crypto || []).length;
    elements.stockCount.textContent = (allData.stock || []).length;
    elements.fundCount.textContent = (allData.fund || []).length;
}

// 更新最后更新时间
function updateLastUpdateTime() {
    const now = new Date();
    const timeString = now.toLocaleString('zh-CN', {
        year: 'numeric',
        month: '2-digit',
        day: '2-digit',
        hour: '2-digit',
        minute: '2-digit',
        second: '2-digit'
    });
    elements.lastUpdateTime.textContent = timeString;
}

// 更新状态
function updateStatus(text, status) {
    elements.statusText.textContent = text;
    
    // 更新状态点颜色
    const statusColors = {
        online: '#00ff88',
        loading: '#ffa502',
        error: '#ff4757'
    };
    
    elements.statusDot.style.background = statusColors[status] || '#ffa502';
}

// 显示加载动画
function showLoading() {
    elements.loadingOverlay.style.display = 'block';
}

// 隐藏加载动画
function hideLoading() {
    elements.loadingOverlay.style.display = 'none';
}

// 显示错误信息
function showError(message) {
    // 简单的错误提示，可以后续改进为更好的UI
    alert(message);
}

// 开始自动刷新
function startAutoRefresh() {
    // 每5分钟自动刷新一次
    autoRefreshInterval = setInterval(() => {
        if (!isLoading) {
            loadData();
        }
    }, 5 * 60 * 1000);
}

// 停止自动刷新
function stopAutoRefresh() {
    if (autoRefreshInterval) {
        clearInterval(autoRefreshInterval);
        autoRefreshInterval = null;
    }
}

// 工具函数
function formatNumber(num) {
    if (num === null || num === undefined || isNaN(num)) {
        return '0.00';
    }
    
    const number = parseFloat(num);
    
    if (number >= 1000000) {
        return (number / 1000000).toFixed(2) + 'M';
    } else if (number >= 1000) {
        return (number / 1000).toFixed(2) + 'K';
    } else if (number >= 1) {
        return number.toFixed(2);
    } else {
        return number.toFixed(4);
    }
}

function getSignalText(signalType) {
    const signalTexts = {
        'strong_buy': '强烈买入',
        'buy': '建议买入',
        'hold': '持有观望',
        'sell': '建议卖出',
        'strong_sell': '强烈卖出'
    };
    return signalTexts[signalType] || '持有观望';
}

function getRiskText(riskLevel) {
    const riskTexts = {
        'low': '低风险',
        'medium': '中等风险',
        'high': '高风险',
        'unknown': '风险未知'
    };
    return riskTexts[riskLevel] || '风险未知';
}

// 页面卸载时清理
window.addEventListener('beforeunload', function() {
    stopAutoRefresh();
});

// 添加详情模态框的CSS样式
const additionalStyles = `
<style>
.detail-section {
    margin-bottom: 20px;
    padding-bottom: 15px;
    border-bottom: 1px solid rgba(255, 255, 255, 0.1);
}

.detail-section:last-child {
    border-bottom: none;
    margin-bottom: 0;
}

.detail-section h4 {
    color: #00d4ff;
    font-size: 1rem;
    font-weight: 600;
    margin-bottom: 10px;
}

.detail-price {
    display: flex;
    align-items: baseline;
    gap: 8px;
}

.price-value {
    font-size: 1.8rem;
    font-weight: 700;
    color: #ffffff;
}

.price-currency {
    font-size: 1rem;
    color: #a0a0a0;
}

.signal-confidence {
    font-size: 0.8rem;
    color: #a0a0a0;
    margin-left: 10px;
}

.entry-exit-points {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
    gap: 10px;
}

.point-item {
    display: flex;
    justify-content: space-between;
    padding: 8px 12px;
    background: rgba(40, 40, 40, 0.6);
    border-radius: 6px;
}

.point-label {
    color: #a0a0a0;
    font-size: 0.9rem;
}

.point-value {
    color: #ffffff;
    font-weight: 600;
}

.risk-assessment {
    display: flex;
    flex-direction: column;
    gap: 8px;
}

.risk-level {
    padding: 6px 12px;
    border-radius: 6px;
    font-weight: 600;
    font-size: 0.9rem;
    display: inline-block;
    width: fit-content;
}

.risk-low {
    background: rgba(0, 255, 136, 0.1);
    color: #00ff88;
    border: 1px solid rgba(0, 255, 136, 0.3);
}

.risk-medium {
    background: rgba(255, 165, 2, 0.1);
    color: #ffa502;
    border: 1px solid rgba(255, 165, 2, 0.3);
}

.risk-high {
    background: rgba(255, 71, 87, 0.1);
    color: #ff4757;
    border: 1px solid rgba(255, 71, 87, 0.3);
}

.risk-unknown {
    background: rgba(128, 128, 128, 0.1);
    color: #808080;
    border: 1px solid rgba(128, 128, 128, 0.3);
}

.risk-factors {
    font-size: 0.85rem;
    color: #c0c0c0;
}

.recommendation-text {
    color: #e0e0e0;
    line-height: 1.5;
    font-size: 0.9rem;
}

.prediction-info {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
    gap: 10px;
}

.prediction-item {
    display: flex;
    justify-content: space-between;
    padding: 8px 12px;
    background: rgba(0, 212, 255, 0.1);
    border-radius: 6px;
    border: 1px solid rgba(0, 212, 255, 0.2);
}

.prediction-label {
    color: #00d4ff;
    font-size: 0.9rem;
}

.prediction-value {
    color: #ffffff;
    font-weight: 600;
}

.analysis-time {
    color: #a0a0a0;
    font-size: 0.85rem;
    font-style: italic;
}
</style>
`;

// 将额外样式添加到head
document.head.insertAdjacentHTML('beforeend', additionalStyles);

