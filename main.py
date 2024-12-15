from flask import Flask, request, jsonify, make_response
from flask_cors import CORS
import random
import json
import os
from datetime import datetime
import sqlite3

app = Flask(__name__)
CORS(app)

# 使用SQLite数据库存储记录
DB_FILE = 'game_records.db'

def init_db():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    # 创建用户表
    c.execute('''CREATE TABLE IF NOT EXISTS users
                 (user_id TEXT PRIMARY KEY, 
                  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)''')
    
    # 创建分数记录表
    c.execute('''CREATE TABLE IF NOT EXISTS scores
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  user_id TEXT,
                  score INTEGER,
                  difficulty TEXT,
                  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                  FOREIGN KEY (user_id) REFERENCES users (user_id))''')
    
    # 创建最高分表
    c.execute('''CREATE TABLE IF NOT EXISTS high_scores
                 (user_id TEXT,
                  difficulty TEXT,
                  score INTEGER,
                  updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                  PRIMARY KEY (user_id, difficulty),
                  FOREIGN KEY (user_id) REFERENCES users (user_id))''')
    conn.commit()
    conn.close()

# 初始化数据库
init_db()

@app.route('/init_user', methods=['GET'])
def init_user():
    response = make_response(jsonify({'success': True}))
    user_id = request.cookies.get('user_id')
    
    if not user_id:
        # 生成新用户ID
        user_id = f"user_{random.randint(10000, 99999)}"
        response.set_cookie('user_id', user_id, max_age=30*24*60*60)  # 30天过期
        
        # 将新用户添加到数据库
        conn = sqlite3.connect(DB_FILE)
        c = conn.cursor()
        c.execute('INSERT INTO users (user_id) VALUES (?)', (user_id,))
        conn.commit()
        conn.close()
    
    return response

@app.route('/save_score', methods=['POST'])
def save_score():
    data = request.json
    user_id = request.cookies.get('user_id')
    if not user_id:
        return jsonify({'error': '未找到用户ID'}), 400
    
    score = data.get('score', 0)
    difficulty = data.get('difficulty', 'medium')
    
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    
    try:
        # 保存分数记录
        c.execute('''INSERT INTO scores (user_id, score, difficulty)
                    VALUES (?, ?, ?)''', (user_id, score, difficulty))
        
        # 更新最高分
        c.execute('''INSERT INTO high_scores (user_id, difficulty, score)
                    VALUES (?, ?, ?)
                    ON CONFLICT(user_id, difficulty) DO UPDATE SET
                    score = CASE WHEN excluded.score > score THEN excluded.score ELSE score END,
                    updated_at = CURRENT_TIMESTAMP
                    WHERE user_id = ? AND difficulty = ?''',
                 (user_id, difficulty, score, user_id, difficulty))
        
        conn.commit()
        return jsonify({'success': True})
    except Exception as e:
        conn.rollback()
        return jsonify({'error': str(e)}), 500
    finally:
        conn.close()

@app.route('/get_records', methods=['GET'])
def get_records():
    user_id = request.cookies.get('user_id')
    if not user_id:
        return jsonify({'error': '未找到用户ID'}), 400
    
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    
    try:
        # 获取最高分
        c.execute('''SELECT difficulty, score FROM high_scores
                    WHERE user_id = ?''', (user_id,))
        high_scores = {row[0]: row[1] for row in c.fetchall()}
        
        # 获取最近10条记录
        c.execute('''SELECT score, difficulty, created_at
                    FROM scores
                    WHERE user_id = ?
                    ORDER BY created_at DESC
                    LIMIT 10''', (user_id,))
        history = [{'score': row[0],
                   'difficulty': row[1],
                   'date': row[2]} for row in c.fetchall()]
        
        # 获取统计信息
        c.execute('''SELECT 
                        COUNT(*) as total_games,
                        SUM(score) as total_score,
                        AVG(score) as avg_score
                    FROM scores
                    WHERE user_id = ?''', (user_id,))
        stats = c.fetchone()
        
        return jsonify({
            'high_scores': {
                'easy': high_scores.get('easy', 0),
                'medium': high_scores.get('medium', 0),
                'hard': high_scores.get('hard', 0)
            },
            'history': history,
            'stats': {
                'total_games': stats[0],
                'total_score': stats[1] or 0,
                'avg_score': round(stats[2] or 0, 1)
            }
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        conn.close()

@app.route('/generate_question', methods=['GET'])
def generate_question():
    # 获取难度配置
    difficulty = request.args.get('difficulty', 'medium')
    
    if difficulty == 'easy':
        num1 = random.randint(1, 50)
        num2 = random.randint(1, 50)
        operations = ['+', '-']
    elif difficulty == 'hard':
        num1 = random.randint(1, 100)
        num2 = random.randint(1, 100)
        operations = ['+', '-', '*']
    else:  # medium
        num1 = random.randint(1, 100)
        num2 = random.randint(1, 100)
        operations = ['+', '-']
    
    operation = random.choice(operations)
    
    # 确保减法时大数在前
    if operation == '-':
        num1, num2 = max(num1, num2), min(num1, num2)
    
    question = f"{num1} {operation} {num2}"
    answer = eval(question)
    return jsonify({'question': question, 'answer': answer})

@app.route('/check_answer', methods=['POST'])
def check_answer():
    data = request.json
    user_answer = data['answer']
    correct_answer = data['correct_answer']
    
    if user_answer == correct_answer:
        return jsonify({'result': '正确'})
    else:
        return jsonify({'result': '错误'})

@app.route('/')
def index():
    return app.send_static_file('index.html')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
