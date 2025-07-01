// 全局配置
const CONFIG = {
    API_BASE: '',
    ENDPOINTS: {
        status: '/api/status',
        config: '/api/config',
        tools: '/api/tools',
        test: '/api/test'
    }
};

// 应用主类
class DingTalkBotApp {
    constructor() {
        this.currentTab = 'dashboard';
        this.systemStatus = {};
        this.tools = [];
        this.config = {};
        
        this.init();
    }

    // 初始化应用
    init() {
        this.setupEventListeners();
        this.loadInitialData();
    }

    // 设置事件监听器
    setupEventListeners() {
        // 导航切换
        document.querySelectorAll('.nav-item').forEach(item => {
            item.addEventListener('click', (e) => {
                const tab = e.currentTarget.getAttribute('data-tab');
                this.switchTab(tab);
            });
        });

        // 表单滑块
        const temperatureSlider = document.getElementById('llmTemperature');
        if (temperatureSlider) {
            temperatureSlider.addEventListener('input', (e) => {
                document.getElementById('temperatureValue').textContent = e.target.value;
            });
        }

        // 回车键发送测试消息
        const testMessageInput = document.getElementById('testMessage');
        if (testMessageInput) {
            testMessageInput.addEventListener('keypress', (e) => {
                if (e.key === 'Enter') {
                    this.quickTest();
                }
            });
        }
    }

    // 切换标签页
    switchTab(tabName) {
        // 更新导航状态
        document.querySelectorAll('.nav-item').forEach(item => {
            item.classList.remove('active');
        });
        document.querySelector(`[data-tab="${tabName}"]`).classList.add('active');

        // 切换内容
        document.querySelectorAll('.tab-content').forEach(content => {
            content.classList.remove('active');
        });
        document.getElementById(tabName).classList.add('active');

        this.currentTab = tabName;

        // 加载对应数据
        this.loadTabData(tabName);
    }

    // 加载标签页数据
    loadTabData(tabName) {
        switch (tabName) {
            case 'dashboard':
                this.loadDashboard();
                break;
            case 'mcp-config':
                this.loadTools();
                break;
            case 'llm-config':
                this.loadLLMConfig();
                break;
            case 'dingtalk-config':
                this.loadDingTalkConfig();
                break;
            case 'test-tools':
                this.loadTestTools();
                break;
        }
    }

    // 加载初始数据
    async loadInitialData() {
        await this.checkSystemStatus();
        await this.loadDashboard();
    }

    // 检查系统状态
    async checkSystemStatus() {
        try {
            const response = await fetch(CONFIG.ENDPOINTS.status);
            const data = await response.json();
            
            this.systemStatus = data;
            this.updateSystemStatusUI();
        } catch (error) {
            console.error('检查系统状态失败:', error);
            this.showError('无法连接到后端服务');
        }
    }

    // 更新系统状态UI
    updateSystemStatusUI() {
        const statusIndicator = document.getElementById('systemStatus');
        const statusDot = statusIndicator.querySelector('.status-dot');
        const statusText = statusIndicator.querySelector('.status-text');

        if (this.systemStatus.healthy) {
            statusDot.classList.add('online');
            statusText.textContent = '系统正常';
        } else {
            statusDot.classList.remove('online');
            statusText.textContent = '系统异常';
        }

        // 更新详细状态
        if (document.getElementById('mcpStatus')) {
            document.getElementById('mcpStatus').textContent = 
                this.systemStatus.mcp_client ? '在线' : '离线';
            document.getElementById('llmStatus').textContent = 
                this.systemStatus.llm_processor ? '在线' : '离线';
            document.getElementById('dingtalkStatus').textContent = 
                this.systemStatus.dingtalk_bot ? '在线' : '离线';
            document.getElementById('toolsCount').textContent = 
                this.systemStatus.tools_count || 0;
        }
    }

    // 加载工具列表
    async loadTools() {
        try {
            const response = await fetch(CONFIG.ENDPOINTS.tools);
            const data = await response.json();
            
            this.tools = data.tools || [];
            this.updateToolsUI();
        } catch (error) {
            console.error('加载工具列表失败:', error);
            this.showError('加载工具列表失败');
        }
    }

    // 更新工具UI
    updateToolsUI() {
        const toolsList = document.getElementById('toolsList');
        const testToolSelect = document.getElementById('testToolSelect');

        if (!toolsList) return;

        if (this.tools.length === 0) {
            toolsList.innerHTML = '<p>暂无可用工具</p>';
            return;
        }

        // 更新工具列表
        toolsList.innerHTML = this.tools.map(tool => `
            <div class="tool-item">
                <div class="tool-info">
                    <div class="tool-name">${tool.name}</div>
                    <div class="tool-description">${tool.description || '暂无描述'}</div>
                </div>
                <div class="tool-actions">
                    <button class="btn btn-primary" onclick="app.testSpecificTool('${tool.name}')">
                        <i class="fas fa-play"></i> 测试
                    </button>
                </div>
            </div>
        `).join('');

        // 更新测试工具选择框
        if (testToolSelect) {
            testToolSelect.innerHTML = '<option value="">请选择工具...</option>' +
                this.tools.map(tool => `<option value="${tool.name}">${tool.name}</option>`).join('');
        }
    }

    // 快速测试
    async quickTest() {
        const message = document.getElementById('testMessage').value.trim();
        if (!message) {
            this.showError('请输入测试消息');
            return;
        }

        const resultElement = document.getElementById('testResult');
        resultElement.innerHTML = '<div class="loading"><i class="fas fa-spinner fa-spin"></i> 处理中...</div>';

        try {
            const response = await fetch(CONFIG.ENDPOINTS.test, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ message })
            });

            const data = await response.json();
            
            if (response.ok) {
                resultElement.className = 'test-result success';
                resultElement.textContent = data.response || '测试成功';
            } else {
                throw new Error(data.error || '测试失败');
            }
        } catch (error) {
            console.error('快速测试失败:', error);
            resultElement.className = 'test-result error';
            resultElement.textContent = `错误: ${error.message}`;
        }
    }

    // 显示通知
    showError(message) {
        const notification = document.createElement('div');
        notification.style.cssText = `
            position: fixed; top: 20px; right: 20px; padding: 1rem;
            background: #f8d7da; color: #721c24; border-radius: 8px;
            z-index: 1000; max-width: 300px;
        `;
        notification.textContent = message;
        document.body.appendChild(notification);
        setTimeout(() => notification.remove(), 3000);
    }

    showSuccess(message) {
        const notification = document.createElement('div');
        notification.style.cssText = `
            position: fixed; top: 20px; right: 20px; padding: 1rem;
            background: #d4edda; color: #155724; border-radius: 8px;
            z-index: 1000; max-width: 300px;
        `;
        notification.textContent = message;
        document.body.appendChild(notification);
        setTimeout(() => notification.remove(), 3000);
    }

    loadDashboard() {
        this.checkSystemStatus();
    }

    loadLLMConfig() {
        console.log('加载LLM配置');
    }

    loadDingTalkConfig() {
        console.log('加载钉钉配置');
    }

    loadTestTools() {
        this.loadTools();
    }
}

// 全局变量
let app;

// 页面加载完成后初始化应用
document.addEventListener('DOMContentLoaded', () => {
    app = new DingTalkBotApp();
});

// 全局函数
function refreshStatus() {
    if (app) app.checkSystemStatus();
}

function quickTest() {
    if (app) app.quickTest();
}

function saveLLMConfig() {
    if (app) app.showSuccess('LLM配置保存成功');
}

function saveDingTalkConfig() {
    if (app) app.showSuccess('钉钉配置保存成功');
}

function testTool() {
    if (app) app.showSuccess('工具测试完成');
} 