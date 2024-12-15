const BASE_URL = 'http://127.0.0.1:5000';

function startGame(difficulty) {
    // 保存难度设置到 localStorage
    localStorage.setItem('gameDifficulty', difficulty);
    
    // 跳转到游戏页面并传递难度参数
    window.location.href = `index.html?difficulty=${difficulty}`;
}

async function initUser() {
    try {
        const response = await fetch(`${BASE_URL}/init_user`, {
            credentials: 'include'
        });
        if (!response.ok) {
            throw new Error('初始化用户失败');
        }
        const data = await response.json();
        console.log('用户初始化成功:', data.user_id);
    } catch (error) {
        console.error('初始化用户失败:', error);
    }
}

async function viewRecords() {
    try {
        const response = await fetch(`${BASE_URL}/get_records`, {
            credentials: 'include'
        });
        if (!response.ok) {
            throw new Error('获取记录失败');
        }
        
        const records = await response.json();
        
        let message = '游戏记录\n\n';
        message += '最高分：\n';
        message += `简单模式：${records.high_scores.easy}\n`;
        message += `中等模式：${records.high_scores.medium}\n`;
        message += `困难模式：${records.high_scores.hard}\n\n`;
        
        message += '游戏统计：\n';
        message += `总游戏次数：${records.stats.total_games}\n`;
        message += `总得分：${records.stats.total_score}\n`;
        message += `平均分：${records.stats.avg_score}\n\n`;
        
        message += '最近记录：\n';
        records.history.forEach(record => {
            message += `${record.date}: ${record.score}分 (${record.difficulty}模式)\n`;
        });
        
        alert(message);
    } catch (error) {
        alert('获取记录失败，请确保已登录并且服务器正常运行');
        console.error('错误:', error);
    }
}

function openSettings() {
    const modal = document.getElementById('settings-modal');
    modal.style.display = 'block';
    loadSettings();
}

function closeSettings() {
    const modal = document.getElementById('settings-modal');
    modal.style.display = 'none';
}

function loadSettings() {
    const settings = JSON.parse(localStorage.getItem('gameSettings')) || getDefaultSettings();
    document.getElementById('sound-setting').checked = settings.sound;
    document.getElementById('music-setting').checked = settings.music;
    document.getElementById('time-limit').value = settings.timeLimit;
    document.getElementById('theme-color').value = settings.theme;
}

function saveSettings() {
    const settings = {
        sound: document.getElementById('sound-setting').checked,
        music: document.getElementById('music-setting').checked,
        timeLimit: document.getElementById('time-limit').value,
        theme: document.getElementById('theme-color').value
    };
    localStorage.setItem('gameSettings', JSON.stringify(settings));
    applyTheme(settings.theme);
    closeSettings();
}

function resetSettings() {
    const defaultSettings = getDefaultSettings();
    localStorage.setItem('gameSettings', JSON.stringify(defaultSettings));
    loadSettings();
    applyTheme(defaultSettings.theme);
}

function getDefaultSettings() {
    return {
        sound: true,
        music: true,
        timeLimit: '0',
        theme: 'default'
    };
}

function applyTheme(theme) {
    const root = document.documentElement;
    const themes = {
        default: {
            primary: '#4CAF50',
            secondary: '#8BC34A'
        },
        blue: {
            primary: '#2196F3',
            secondary: '#64B5F6'
        },
        purple: {
            primary: '#9C27B0',
            secondary: '#BA68C8'
        },
        orange: {
            primary: '#FF9800',
            secondary: '#FFB74D'
        }
    };
    
    const colors = themes[theme] || themes.default;
    root.style.setProperty('--primary-color', colors.primary);
    root.style.setProperty('--secondary-color', colors.secondary);
}

// 页面加载时应用主题
window.addEventListener('load', () => {
    const settings = JSON.parse(localStorage.getItem('gameSettings')) || getDefaultSettings();
    applyTheme(settings.theme);
});

// 点击模态框外部关闭
window.onclick = function(event) {
    const modal = document.getElementById('settings-modal');
    if (event.target === modal) {
        closeSettings();
    }
}

// 页面加载时初始化用户
window.onload = initUser;

// 键盘导航支持
document.addEventListener('keydown', function(e) {
    const cards = document.querySelectorAll('.menu-card');
    let currentFocus = document.activeElement;
    
    switch(e.key) {
        case 'ArrowRight':
        case 'ArrowDown':
            e.preventDefault();
            if (currentFocus && currentFocus.classList.contains('menu-card')) {
                let nextCard = currentFocus.nextElementSibling;
                if (nextCard) nextCard.focus();
            } else {
                cards[0].focus();
            }
            break;
        case 'ArrowLeft':
        case 'ArrowUp':
            e.preventDefault();
            if (currentFocus && currentFocus.classList.contains('menu-card')) {
                let prevCard = currentFocus.previousElementSibling;
                if (prevCard) prevCard.focus();
            } else {
                cards[cards.length - 1].focus();
            }
            break;
        case 'Enter':
        case ' ':
            if (currentFocus && currentFocus.classList.contains('menu-card')) {
                currentFocus.click();
            }
            break;
    }
}); 