from flask import Flask, request, jsonify, send_from_directory, render_template_string, session, redirect, url_for
import os
import json
import gzip
import sqlite3
from datetime import datetime
from werkzeug.utils import secure_filename
from flask_socketio import SocketIO, emit

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key'

# 配置
app.config['UPLOAD_FOLDER'] = '/data/images/'
app.config['LOGS_FOLDER'] = '/data/logs/'
app.config['STATIC_FOLDER'] = 'static'
app.config['DB_PATH'] = './iot.db'
app.config['PERMANENT_SESSION_LIFETIME'] = 3600  # 1小时
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs(app.config['LOGS_FOLDER'], exist_ok=True)
os.makedirs(app.config['STATIC_FOLDER'], exist_ok=True)

# 创建数据库表
conn = sqlite3.connect(app.config['DB_PATH'])
cursor = conn.cursor()

# 创建用户表
cursor.execute('''
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT NOT NULL UNIQUE,
    password TEXT NOT NULL,
    role TEXT NOT NULL DEFAULT 'device',
    device_id TEXT,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP
)
''')

# 创建设备表
cursor.execute('''
CREATE TABLE IF NOT EXISTS devices (
    device_id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    status TEXT DEFAULT 'active',
    created_at TEXT DEFAULT CURRENT_TIMESTAMP
)
''')

# 创建图片表
cursor.execute('''
CREATE TABLE IF NOT EXISTS images (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    device_id TEXT NOT NULL,
    image_path TEXT NOT NULL,
    original_filename TEXT NOT NULL,
    receive_time TEXT DEFAULT CURRENT_TIMESTAMP
)
''')

# 插入管理员账号
cursor.execute("SELECT * FROM users WHERE username='admin'")
if not cursor.fetchone():
    cursor.execute("INSERT INTO users (username, password, role) VALUES (?, ?, ?)", ('admin', '123456', 'admin'))

conn.commit()
conn.close()

# 初始化SocketIO
socketio = SocketIO(app)

# WebSocket客户端连接事件
@socketio.on('connect')
def handle_connect():
    print('WebSocket客户端已连接')
    emit('connected', {'message': '已连接到服务器'})

# WebSocket客户端断开连接事件
@socketio.on('disconnect')
def handle_disconnect():
    print('WebSocket客户端已断开连接')

# 向前端推送数据的工具函数
def push_data_to_frontend(data_type, data):
    """向前端推送数据"""
    socketio.emit(data_type, data)
    print(f"已向前端推送{data_type}数据: {data}")

# 认证装饰器
def login_required(f):
    from functools import wraps
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'username' not in session:
            # 检查是否是API请求（URL包含/api/或Content-Type是application/json）
            if '/api/' in request.path or request.headers.get('Content-Type') == 'application/json':
                # 对于API请求，返回JSON格式的未授权响应
                return jsonify({'code': 401, 'msg': '未登录'})
            else:
                # 对于普通页面请求，执行重定向
                return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

# 登录页面
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        conn = sqlite3.connect(app.config['DB_PATH'])
        cursor = conn.cursor()
        
        # 检查用户是否存在
        cursor.execute("SELECT * FROM users WHERE username=? AND password=?", (username, password))
        user = cursor.fetchone()
        
        if user:
            # 登录成功，保存到session
            session['username'] = username
            session['role'] = user[3]  # role在第4列
            session['device_id'] = user[4]  # device_id在第5列
            session.permanent = True
            
            conn.close()
            return redirect(url_for('index'))
        else:
            conn.close()
            return render_template_string('''
                <!DOCTYPE html>
                <html lang="zh-CN">
                <head>
                    <meta charset="UTF-8">
                    <meta name="viewport" content="width=1200, initial-scale=1.0, maximum-scale=5.0, user-scalable=yes">
                    <title>登录失败</title>
                    <style>
                        body {
                            font-family: Arial, sans-serif;
                            background-color: #f5f5f5;
                            display: flex;
                            justify-content: center;
                            align-items: center;
                            height: 100vh;
                            margin: 0;
                        }
                        .login-container {
                            background-color: white;
                            padding: 30px;
                            border-radius: 8px;
                            box-shadow: 0 2px 10px rgba(0, 0, 0, 0.1);
                            max-width: 400px;
                            width: 100%;
                        }
                        .error {
                            color: red;
                            margin-bottom: 20px;
                            text-align: center;
                        }
                        input[type="text"], input[type="password"] {
                            width: 100%;
                            padding: 12px;
                            margin: 8px 0;
                            border: 1px solid #ddd;
                            border-radius: 4px;
                            box-sizing: border-box;
                        }
                        input[type="submit"] {
                            width: 100%;
                            background-color: #4CAF50;
                            color: white;
                            padding: 12px;
                            border: none;
                            border-radius: 4px;
                            cursor: pointer;
                            font-size: 16px;
                        }
                        input[type="submit"]:hover {
                            background-color: #45a049;
                        }
                        h2 {
                            text-align: center;
                            margin-bottom: 20px;
                            color: #333;
                        }
                    </style>
                </head>
                <body>
                    <div class="login-container">
                        <h2>智能捕蚊识别系统</h2>
                        <div class="error">用户名或密码错误，请重试</div>
                        <form method="POST">
                            <input type="text" name="username" placeholder="用户名/设备ID" required><br>
                            <input type="password" name="password" placeholder="密码" required><br>
                            <input type="submit" value="登录">
                        </form>
                    </div>
                </body>
                </html>
            ''')
    
    # GET请求，显示登录页面
    return render_template_string('''
        <!DOCTYPE html>
        <html lang="zh-CN">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=1200, initial-scale=1.0, maximum-scale=5.0, user-scalable=yes">
            <title>登录 - 智能捕蚊识别系统</title>
            <style>
                body {
                    font-family: Arial, sans-serif;
                    background-color: #f5f5f5;
                    display: flex;
                    justify-content: center;
                    align-items: center;
                    height: 100vh;
                    margin: 0;
                }
                .login-container {
                    background-color: white;
                    padding: 30px;
                    border-radius: 8px;
                    box-shadow: 0 2px 10px rgba(0, 0, 0, 0.1);
                    max-width: 400px;
                    width: 100%;
                }
                input[type="text"], input[type="password"] {
                    width: 100%;
                    padding: 12px;
                    margin: 8px 0;
                    border: 1px solid #ddd;
                    border-radius: 4px;
                    box-sizing: border-box;
                }
                input[type="submit"] {
                    width: 100%;
                    background-color: #4CAF50;
                    color: white;
                    padding: 12px;
                    border: none;
                    border-radius: 4px;
                    cursor: pointer;
                    font-size: 16px;
                }
                input[type="submit"]:hover {
                    background-color: #45a049;
                }
                h2 {
                    text-align: center;
                    margin-bottom: 20px;
                    color: #333;
                }
                .info {
                    text-align: center;
                    margin-top: 15px;
                    font-size: 14px;
                    color: #666;
                }
            </style>
        </head>
        <body>
            <div class="login-container">
                <h2>智能捕蚊识别系统</h2>
                <form method="POST">
                    <input type="text" name="username" placeholder="用户名/设备ID" required><br>
                    <input type="password" name="password" placeholder="密码" required><br>
                    <input type="submit" value="登录">
                </form>
                <div class="info">设备登录：使用设备ID作为用户名，密码123456</div>
                <div class="info">管理员登录：用户名admin，密码123456</div>
            </div>
        </body>
        </html>
    ''')

# 登出
@app.route('/logout')
def logout():
    session.pop('username', None)
    session.pop('role', None)
    session.pop('device_id', None)
    return redirect(url_for('login'))

# 用于存储设备注册时间，防止频繁注册
registration_times = {}

# 用于缓存已注册的设备ID，减少数据库查询
registered_devices = set()

# 设备ID格式正则表达式（允许字母、数字、下划线和连字符，长度3-20）
import re
DEVICE_ID_PATTERN = re.compile(r'^[a-zA-Z0-9_-]{3,20}$')

def auto_register_device(device_id):
    """自动注册设备的通用函数"""
    import time
    
    # 1. 设备ID格式验证
    if not DEVICE_ID_PATTERN.match(device_id):
        print(f"❌ [自动注册] 设备ID格式无效: {device_id}")
        return False
    
    # 2. 检查缓存，减少数据库查询
    if device_id in registered_devices:
        print(f"ℹ️  [自动注册] 设备已在缓存中: {device_id}")
        return True
    
    # 3. 限制注册频率（同一设备ID，60秒内只能注册一次）
    current_time = time.time()
    if device_id in registration_times:
        if current_time - registration_times[device_id] < 60:
            print(f"❌ [自动注册] 注册频率过高，请稍后再试: {device_id}")
            return False
    registration_times[device_id] = current_time
    
    conn = None
    cursor = None
    
    try:
        conn = sqlite3.connect(app.config['DB_PATH'])
        cursor = conn.cursor()
        
        # 4. 检查设备是否已存在于用户表
        cursor.execute("SELECT * FROM users WHERE username=?", (device_id,))
        user_exists = cursor.fetchone() is not None
        
        if not user_exists:
            # 注册设备用户
            cursor.execute("INSERT INTO users (username, password, role, device_id) VALUES (?, ?, ?, ?)", 
                          (device_id, '123456', 'device', device_id))
            print(f"🔧 [自动注册] 成功注册设备用户: {device_id}")
        
        # 5. 检查设备是否已存在于设备表
        cursor.execute("SELECT * FROM devices WHERE device_id=?", (device_id,))
        device_exists = cursor.fetchone() is not None
        
        if not device_exists:
            # 创建设备记录
            cursor.execute("INSERT INTO devices (device_id, name) VALUES (?, ?)", 
                          (device_id, f'设备{device_id}'))
            print(f"🔧 [自动注册] 成功创建设备记录: {device_id}")
        
        # 6. 提交事务
        conn.commit()
        
        # 7. 更新缓存
        registered_devices.add(device_id)
        
        print(f"✅ [自动注册] 设备注册成功: {device_id}")
        return True
    except sqlite3.IntegrityError as e:
        print(f"❌ [自动注册] 设备注册冲突: {device_id}, 错误: {e}")
        if conn:
            conn.rollback()
        # 即使发生冲突，也将设备ID添加到缓存（因为设备可能已经存在）
        registered_devices.add(device_id)
        return True
    except Exception as e:
        print(f"❌ [自动注册] 设备注册失败: {device_id}, 错误: {type(e).__name__}: {e}")
        if conn:
            conn.rollback()
        return False
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

# 设备用户注册（根据设备ID自动创建） - 保留原有接口，兼容旧设备
@app.route('/upload/image', methods=['POST'])
def upload_image():
    """接收设备上传的图片"""
    if 'image' not in request.files:
        return jsonify({'code': 400, 'msg': 'No image part'}), 400
    
    file = request.files['image']
    device_id = request.form.get('device_id', 'unknown')
    original_filename = file.filename
    
    # 自动注册设备
    if device_id != 'unknown':
        auto_register_device(device_id)
    
    if file:
        # 生成安全文件名
        filename = secure_filename(f"{device_id}_{file.filename}")
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)
        
        # 将图片信息保存到数据库
        conn = sqlite3.connect(app.config['DB_PATH'])
        cursor = conn.cursor()
        cursor.execute("INSERT INTO images (device_id, image_path, original_filename, receive_time) VALUES (?, ?, ?, ?)",
                      (device_id, filepath, original_filename, datetime.now().isoformat()))
        conn.commit()
        conn.close()
        
        # 推送图片上传信息到前端
        image_data = {
            'device_id': device_id,
            'filename': filename,
            'path': filepath,
            'timestamp': datetime.now().isoformat(),
            'size': os.path.getsize(filepath),
            'original_filename': original_filename
        }
        push_data_to_frontend('new_image', image_data)
        
        return jsonify({
        'code': 200, 
        'msg': 'Upload success', 
        'path': filepath,
        'filename': filename
    })

@app.route('/')
@login_required
def index():
    """首页"""
    return send_from_directory(app.config['STATIC_FOLDER'], 'index.html')

# 获取当前登录用户信息
@app.route('/api/user_info')
@login_required
def get_user_info():
    return jsonify({
        'username': session['username'],
        'role': session['role'],
        'device_id': session['device_id']
    })

# 获取设备列表（管理员可查看所有设备，普通用户只能查看自己的设备）
@app.route('/api/devices')
@login_required
def get_devices():
    conn = sqlite3.connect(app.config['DB_PATH'])
    cursor = conn.cursor()
    
    # 根据用户角色获取设备信息
    if session['role'] == 'admin':
        # 管理员获取所有设备信息
        cursor.execute("SELECT * FROM devices")
    else:
        # 普通用户只能获取自己的设备信息
        cursor.execute("SELECT * FROM devices WHERE device_id = ?", (session['device_id'],))
    
    devices = cursor.fetchall()
    
    device_list = []
    # 获取所有图片信息
    cursor.execute("SELECT id, device_id, image_path, original_filename, receive_time FROM images ORDER BY receive_time DESC")
    all_images = cursor.fetchall()
    
    # 按设备ID分组图片
    images_by_device = {}
    for image in all_images:
        image_id, device_id, image_path, original_filename, receive_time = image
        if device_id not in images_by_device:
            images_by_device[device_id] = []
        images_by_device[device_id].append({
            'id': image_id,
            'image_path': image_path,
            'original_filename': original_filename,
            'receive_time': receive_time
        })
    
    for device in devices:
        device_id, name, status, created_at = device
        location = "未知位置"  # 设备表中没有location字段，设置默认值
        
        # 获取该设备的最新图片（只取第一张，即最新的）
        device_images = images_by_device.get(device_id, [])
        latest_image = device_images[0] if device_images else None
        
        # 为每个设备创建一个条目，无论是否有图片
        device_list.append({
            'device_id': device_id,
            'name': name,
            'status': status,
            'location': location,
            'created_at': created_at,
            'latest_image': latest_image
        })
    
    conn.close()
    
    return jsonify({
        'code': 200,
        'msg': 'success',
        'data': device_list
    })

# 获取设备数据（根据权限）
@app.route('/api/sensor_data')
@login_required
def get_sensor_data():
    conn = sqlite3.connect(app.config['DB_PATH'])
    cursor = conn.cursor()
    
    if session['role'] == 'admin':
        # 管理员可以查看所有设备数据
        cursor.execute("SELECT * FROM sensor_data ORDER BY created_at DESC LIMIT 100")
    else:
        # 设备用户只能查看自己的设备数据
        cursor.execute("SELECT * FROM sensor_data WHERE device_id=? ORDER BY created_at DESC LIMIT 100", 
                      (session['device_id'],))
    
    rows = cursor.fetchall()
    conn.close()
    
    # 转换为JSON格式
    columns = ['id', 'device_id', 'timestamp', 'temperature_inside', 'temperature_outside', 
              'humidity', 'duoj1', 'duoj2', 'duoj3', 'duoj4', 'feng1', 'feng2', 'jia', 'raw_data', 'created_at']
    data = [dict(zip(columns, row)) for row in rows]
    
    return jsonify({
        'code': 200,
        'msg': 'success',
        'data': data
    })

# 视觉识别相关功能

# 创建视觉识别结果表
conn = sqlite3.connect(app.config['DB_PATH'])
cursor = conn.cursor()
cursor.execute('''
CREATE TABLE IF NOT EXISTS visual_recognition_results (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    image_id INTEGER NOT NULL,
    status TEXT NOT NULL,
    total_count INTEGER,
    analyze_time INTEGER,
    species_count TEXT,
    gender_count TEXT,
    objects TEXT,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP
)
''')
conn.commit()
conn.close()

# 视觉识别回调接口
@app.route('/api/callback', methods=['POST'])
def visual_callback():
    """接收视觉服务的识别结果"""
    try:
        data = request.get_json()
        image_id = data.get('image_id')
        status = data.get('status')
        result = data.get('result', {})
        
        # 存储识别结果到数据库
        conn = sqlite3.connect(app.config['DB_PATH'])
        cursor = conn.cursor()
        
        cursor.execute('''
        INSERT INTO visual_recognition_results 
        (image_id, status, total_count, analyze_time, species_count, gender_count, objects)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (
            image_id,
            status,
            result.get('total_count'),
            result.get('analyze_time'),
            json.dumps(result.get('species_count', {})),
            json.dumps(result.get('gender_count', {})),
            json.dumps(result.get('objects', []))
        ))
        
        conn.commit()
        conn.close()
        
        # 推送结果到前端
        push_data_to_frontend('visual_result', data)
        
        return jsonify({'code': 200, 'msg': 'Callback received successfully'})
    except Exception as e:
        print(f"Callback error: {str(e)}")
        return jsonify({'code': 500, 'msg': f'Callback error: {str(e)}'})

# 触发视觉分析API
@app.route('/api/trigger_analysis', methods=['POST'])
@login_required
def trigger_analysis():
    """触发视觉服务进行分析"""
    try:
        import requests
        
        data = request.get_json()
        image_id = data.get('image_id')
        image_path = data.get('image_path')
        
        if not image_id or not image_path:
            return jsonify({'code': 400, 'msg': 'Missing image_id or image_path'}), 400
        
        # 调用视觉服务
        visual_service_url = 'http://localhost:8000/api/analyze'
        callback_url = 'http://localhost:5000/api/callback'
        
        payload = {
            'image_id': image_id,
            'image_path': image_path,
            'callback_url': callback_url
        }
        
        response = requests.post(visual_service_url, json=payload)
        
        return jsonify({'code': 200, 'msg': 'Analysis triggered successfully', 'visual_response': response.json()})
    except Exception as e:
        return jsonify({'code': 500, 'msg': f'Failed to trigger analysis: {str(e)}'})

# 获取视觉识别结果
@app.route('/api/visual_results/<int:image_id>', methods=['GET'])
@login_required
def get_visual_results(image_id):
    """获取指定图片的视觉识别结果"""
    try:
        conn = sqlite3.connect(app.config['DB_PATH'])
        cursor = conn.cursor()
        
        cursor.execute('''
        SELECT * FROM visual_recognition_results WHERE image_id = ? ORDER BY created_at DESC LIMIT 1
        ''', (image_id,))
        
        result = cursor.fetchone()
        conn.close()
        
        if not result:
            return jsonify({'code': 404, 'msg': 'No visual recognition results found'})
        
        # 转换数据格式
        response_data = {
            'id': result[0],
            'image_id': result[1],
            'status': result[2],
            'total_count': result[3],
            'analyze_time': result[4],
            'species_count': json.loads(result[5]) if result[5] else {},
            'gender_count': json.loads(result[6]) if result[6] else {},
            'objects': json.loads(result[7]) if result[7] else [],
            'created_at': result[8]
        }
        
        return jsonify({'code': 200, 'msg': 'success', 'data': response_data})
    except Exception as e:
        return jsonify({'code': 500, 'msg': f'Failed to get visual results: {str(e)}'})

@app.route('/<path:filename>')
def serve_static(filename):
    """静态文件服务"""
    return send_from_directory(app.config['STATIC_FOLDER'], filename)

@app.route('/get_latest_sensor_data', methods=['GET'])
def get_latest_sensor_data():
    """获取最新的传感器数据"""
    try:
        # 检查是否已登录
        if 'username' not in session:
            # 对于API请求，返回JSON格式的未授权响应
            return jsonify({'code': 401, 'msg': '未登录'})
            
        conn = sqlite3.connect(app.config['DB_PATH'])
        c = conn.cursor()
        c.execute('''SELECT * FROM sensor_data ORDER BY created_at DESC LIMIT 10''')
        rows = c.fetchall()
        conn.close()
        
        # 转换为JSON格式
        columns = ['id', 'device_id', 'timestamp', 'temperature_inside', 'temperature_outside', 
                  'humidity', 'duoj1', 'duoj2', 'duoj3', 'duoj4', 'feng1', 'feng2', 'jia', 'raw_data', 'created_at']
        data = [dict(zip(columns, row)) for row in rows]
        
        return jsonify({
            'code': 200,
            'msg': 'success',
            'data': data
        })
    except Exception as e:
        return jsonify({
            'code': 500,
            'msg': f'Failed to get sensor data: {str(e)}'
        })

@app.route('/push_sensor_data', methods=['POST'])
def push_sensor_data():
    """接收传感器数据并推送到WebSocket"""
    try:
        sensor_data = request.get_json()
        if not sensor_data:
            return jsonify({'code': 400, 'msg': 'No data provided'}), 400
        
        # 推送传感器数据到前端
        push_data_to_frontend('sensor_data', sensor_data)
        
        # 将数据保存到数据库
        conn = sqlite3.connect(app.config['DB_PATH'])
        cursor = conn.cursor()
        
        # 确保sensor_data表存在
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS sensor_data (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            device_id TEXT NOT NULL,
            timestamp TEXT NOT NULL,
            temperature_inside REAL,
            temperature_outside REAL,
            humidity REAL,
            duoj1 INTEGER,
            duoj2 INTEGER,
            duoj3 INTEGER,
            duoj4 INTEGER,
            feng1 INTEGER,
            feng2 INTEGER,
            jia INTEGER,
            raw_data TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
        ''')
        
        # 准备插入数据
        device_id = sensor_data.get('device_id', 'unknown')
        timestamp = sensor_data.get('timestamp', datetime.now().isoformat())
        temperature_inside = sensor_data.get('temperature_inside')
        temperature_outside = sensor_data.get('temperature_outside')
        humidity = sensor_data.get('humidity')
        duoj1 = sensor_data.get('duoj1')
        duoj2 = sensor_data.get('duoj2')
        duoj3 = sensor_data.get('duoj3')
        duoj4 = sensor_data.get('duoj4')
        feng1 = sensor_data.get('feng1')
        feng2 = sensor_data.get('feng2')
        jia = sensor_data.get('jia')
        raw_data = json.dumps(sensor_data)
        
        # 插入数据
        cursor.execute('''
        INSERT INTO sensor_data (device_id, timestamp, temperature_inside, temperature_outside, 
                               humidity, duoj1, duoj2, duoj3, duoj4, feng1, feng2, jia, raw_data)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (device_id, timestamp, temperature_inside, temperature_outside, 
             humidity, duoj1, duoj2, duoj3, duoj4, feng1, feng2, jia, raw_data))
        
        conn.commit()
        conn.close()
        
        return jsonify({
            'code': 200,
            'msg': 'Data pushed successfully'
        })
    except Exception as e:
        return jsonify({
            'code': 500,
            'msg': f'Failed to push data: {str(e)}'
        })

# 图片删除API
@app.route('/api/delete_image/<int:image_id>', methods=['DELETE'])
@login_required
def delete_image(image_id):
    conn = None
    try:
        conn = sqlite3.connect(app.config['DB_PATH'])
        cursor = conn.cursor()
        
        # 获取图片信息，包括关联的设备ID
        cursor.execute("SELECT image_path, device_id FROM images WHERE id = ?", (image_id,))
        image = cursor.fetchone()
        
        if not image:
            return jsonify({'code': 404, 'msg': '图片不存在'})
        
        image_path = image[0]
        device_id = image[1]
        
        # 检查权限：普通用户只能删除自己设备的图片
        if session['role'] != 'admin' and session['device_id'] != device_id:
            return jsonify({'code': 403, 'msg': '无权限删除该图片'})
        
        # 删除图片文件
        if os.path.exists(image_path):
            os.remove(image_path)
        
        # 从数据库中删除图片记录
        cursor.execute("DELETE FROM images WHERE id = ?", (image_id,))
        
        # 删除关联的设备条目
        cursor.execute("DELETE FROM devices WHERE device_id = ?", (device_id,))
        
        # 删除用户设备关联（如果表存在）
        try:
            cursor.execute("DELETE FROM user_devices WHERE device_id = ?", (device_id,))
        except sqlite3.OperationalError:
            # 忽略表不存在的错误
            pass
        
        conn.commit()
        
        return jsonify({'code': 200, 'msg': '图片和关联设备已成功删除'})
    except Exception as e:
        if conn:
            conn.rollback()
        return jsonify({'code': 500, 'msg': f'删除失败: {str(e)}'})
    finally:
        if conn:
            conn.close()

# 图片查看API
@app.route('/api/view_image/<int:image_id>', methods=['GET'])
@login_required
def view_image(image_id):
    try:
        conn = sqlite3.connect(app.config['DB_PATH'])
        cursor = conn.cursor()
        
        # 获取图片信息
        cursor.execute("SELECT image_path, original_filename, receive_time, device_id FROM images WHERE id = ?", (image_id,))
        image = cursor.fetchone()
        
        if not image:
            conn.close()
            return jsonify({'code': 404, 'msg': '图片不存在'})
        
        image_path, original_filename, receive_time, device_id = image
        
        # 检查权限：普通用户只能查看自己设备的图片
        if session['role'] != 'admin' and session['device_id'] != device_id:
            conn.close()
            return jsonify({'code': 403, 'msg': '无权限查看该图片'})
        
        conn.close()
        
        # 获取文件大小
        try:
            file_size = os.path.getsize(image_path) if os.path.exists(image_path) else 0
        except Exception as e:
            file_size = 0
        
        # 返回图片信息和URL
        return jsonify({
            'code': 200,
            'msg': 'success',
            'data': {
                'image_path': image_path,
                'original_filename': original_filename,
                'filename': original_filename,  # 添加filename字段，与original_filename一致
                'receive_time': receive_time,
                'device_id': device_id,
                'image_url': f"/data/images/{os.path.basename(image_path)}",
                'size': file_size  # 添加文件大小字段
            }
        })
    except Exception as e:
        return jsonify({'code': 500, 'msg': f'获取图片失败: {str(e)}'})

# 静态文件服务 - 图片访问
@app.route('/data/images/<filename>')
@login_required
def serve_image(filename):
    """提供图片文件的静态访问，带访问控制"""
    # 检查权限：获取图片所属设备ID
    conn = sqlite3.connect(app.config['DB_PATH'])
    cursor = conn.cursor()
    
    # 根据文件名查找对应的设备ID
    cursor.execute("SELECT device_id FROM images WHERE image_path LIKE ?", (f"%{filename}",))
    result = cursor.fetchone()
    conn.close()
    
    if not result:
        # 图片不存在或无权访问
        abort(404)
    
    device_id = result[0]
    
    # 权限检查：管理员可以访问所有图片，普通用户只能访问自己设备的图片
    if session['role'] != 'admin' and session['device_id'] != device_id:
        abort(403)
    
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

@app.route('/api/images', methods=['GET'])
@login_required
def get_images():
    """获取图片列表，支持分页和权限控制"""
    try:
        # 获取分页参数
        page = int(request.args.get('page', 1))
        per_page = int(request.args.get('per_page', 10))
        if page < 1:
            page = 1
        if per_page < 1:
            per_page = 1
        elif per_page > 100:
            per_page = 100
        
        conn = sqlite3.connect(app.config['DB_PATH'])
        cursor = conn.cursor()
        
        # 根据用户角色构建查询
        if session['role'] == 'admin':
            # 管理员可以查看所有图片
            # 获取总数
            cursor.execute("SELECT COUNT(*) FROM images")
            total = cursor.fetchone()[0]
            
            # 获取分页数据
            offset = (page - 1) * per_page
            cursor.execute("""
                SELECT i.id, i.image_path, i.original_filename, i.receive_time, 
                       i.device_id, d.name as device_name
                FROM images i
                LEFT JOIN devices d ON i.device_id = d.device_id
                ORDER BY i.receive_time DESC
                LIMIT ? OFFSET ?
            """, (per_page, offset))
        else:
            # 普通用户只能查看自己设备的图片
            device_id = session['device_id']
            
            # 获取总数
            cursor.execute("SELECT COUNT(*) FROM images WHERE device_id = ?", (device_id,))
            total = cursor.fetchone()[0]
            
            # 获取分页数据
            offset = (page - 1) * per_page
            cursor.execute("""
                SELECT i.id, i.image_path, i.original_filename, i.receive_time, 
                       i.device_id, d.name as device_name
                FROM images i
                LEFT JOIN devices d ON i.device_id = d.device_id
                WHERE i.device_id = ?
                ORDER BY i.receive_time DESC
                LIMIT ? OFFSET ?
            """, (device_id, per_page, offset))
        
        images = cursor.fetchall()
        conn.close()
        
        # 格式化响应数据
        image_list = []
        for img in images:
            image_id, image_path, original_filename, receive_time, device_id, device_name = img
            filename = os.path.basename(image_path) if image_path else ''
            
            image_list.append({
                'id': image_id,
                'filename': filename,
                'original_filename': original_filename,
                'receive_time': receive_time,
                'device_id': device_id,
                'device_name': device_name
            })
        
        # 计算分页信息
        total_pages = (total + per_page - 1) // per_page
        
        return jsonify({
            'code': 200,
            'msg': 'success',
            'data': {
                'images': image_list,
                'pagination': {
                    'total': total,
                    'per_page': per_page,
                    'current_page': page,
                    'total_pages': total_pages
                }
            }
        })
        
    except Exception as e:
        print(f"❌ 获取图片列表失败: {e}")
        return jsonify({'code': 500, 'msg': '获取图片列表失败', 'error': str(e)})

@app.route('/receive_logs', methods=['POST'])
def receive_logs():
    """接收设备发送的日志"""
    try:
        # 检查是否为压缩数据
        if request.headers.get('Content-Encoding') == 'gzip':
            # 解压缩数据
            data = gzip.decompress(request.data)
            log_data = json.loads(data.decode('utf-8'))
        else:
            # 直接解析JSON数据
            log_data = request.get_json()
        
        # 获取设备ID（优先级：请求头 > 日志数据中的device_id > 默认为unknown）
        device_id = request.headers.get('X-Device-ID')
        if not device_id and 'device_id' in log_data:
            device_id = log_data['device_id']
        if not device_id:
            device_id = 'unknown'
        
        # 自动注册设备
        if device_id != 'unknown':
            auto_register_device(device_id)
        
        # 获取logs数组
        logs = log_data.get('logs', [])
        if not isinstance(logs, list):
            logs = [logs]
        
        # 创建设备日志目录
        device_log_dir = os.path.join(app.config['LOGS_FOLDER'], device_id)
        os.makedirs(device_log_dir, exist_ok=True)
        
        # 生成日志文件名（按日期）
        log_filename = f"{datetime.now().strftime('%Y-%m-%d')}.log"
        log_filepath = os.path.join(device_log_dir, log_filename)
        
        # 写入日志到文件
        with open(log_filepath, 'a', encoding='utf-8') as f:
            for log in logs:
                # 确保日志包含时间戳
                if 'timestamp' not in log:
                    log['timestamp'] = datetime.now().isoformat()
                
                # 写入日志行
                f.write(json.dumps(log, ensure_ascii=False) + '\n')
        
        # 返回成功响应
        return jsonify({
            'code': 200,
            'msg': 'Logs received successfully',
            'received_count': len(logs),
            'device_id': device_id
        })
    except Exception as e:
        return jsonify({
            'code': 500,
            'msg': f'Failed to receive logs: {str(e)}'
        }), 500

# 获取设备日志
@app.route('/api/logs')
@login_required
def get_device_logs():
    """获取设备日志，支持分页和筛选"""
    try:
        # 获取查询参数
        page = int(request.args.get('page', 1))
        per_page = int(request.args.get('per_page', 20))
        device_id = request.args.get('device_id')
        date = request.args.get('date')
        
        if page < 1:
            page = 1
        if per_page < 1 or per_page > 100:
            per_page = 20
        
        # 根据用户角色过滤设备ID
        allowed_device_ids = []
        conn = sqlite3.connect(app.config['DB_PATH'])
        cursor = conn.cursor()
        
        if session['role'] == 'admin':
            # 管理员可以查看所有设备
            if device_id:
                # 如果指定了设备ID，检查是否存在
                cursor.execute("SELECT device_id FROM devices WHERE device_id = ?", (device_id,))
                if cursor.fetchone():
                    allowed_device_ids = [device_id]
                else:
                    return jsonify({
                        'code': 404,
                        'msg': 'Device not found'
                    })
            else:
                # 获取所有设备ID
                cursor.execute("SELECT device_id FROM devices")
                allowed_device_ids = [row[0] for row in cursor.fetchall()]
        else:
            # 普通用户只能查看自己的设备
            allowed_device_ids = [session['device_id']]
        
        conn.close()
        
        # 读取日志文件
        all_logs = []
        
        for dev_id in allowed_device_ids:
            device_log_dir = os.path.join(app.config['LOGS_FOLDER'], dev_id)
            
            if not os.path.exists(device_log_dir):
                continue
            
            # 获取日志文件列表
            log_files = []
            for filename in os.listdir(device_log_dir):
                if filename.endswith('.log'):
                    if not date or filename == f"{date}.log":
                        log_files.append(os.path.join(device_log_dir, filename))
            
            # 按文件名排序（最新的日期在前面）
            log_files.sort(reverse=True)
            
            # 读取每个日志文件
            for log_file in log_files:
                try:
                    with open(log_file, 'r', encoding='utf-8') as f:
                        for line in f:
                            line = line.strip()
                            if line:
                                try:
                                    log_entry = json.loads(line)
                                    log_entry['device_id'] = dev_id
                                    log_entry['date'] = os.path.basename(log_file).replace('.log', '')
                                    all_logs.append(log_entry)
                                except json.JSONDecodeError:
                                    # 跳过无效的JSON行
                                    continue
                except Exception as e:
                    app.logger.error(f"Error reading log file {log_file}: {str(e)}")
        
        # 按时间戳排序（最新的日志在前面）
        all_logs.sort(key=lambda x: x.get('timestamp', ''), reverse=True)
        
        # 分页
        total = len(all_logs)
        start = (page - 1) * per_page
        end = start + per_page
        paginated_logs = all_logs[start:end]
        
        # 计算总页数
        total_pages = (total + per_page - 1) // per_page
        
        return jsonify({
            'code': 200,
            'msg': 'success',
            'data': {
                'logs': paginated_logs,
                'pagination': {
                    'current_page': page,
                    'per_page': per_page,
                    'total': total,
                    'total_pages': total_pages
                }
            }
        })
    except Exception as e:
        app.logger.error(f"Error getting device logs: {str(e)}")
        return jsonify({
            'code': 500,
            'msg': f'Error getting device logs: {str(e)}'
        })

# 添加MQTT客户端用于发布命令
import paho.mqtt.client as mqtt

# 初始化MQTT客户端用于发布命令
mqtt_client = mqtt.Client()
mqtt_client.connect("localhost", 1883, 60)
mqtt_client.loop_start()

# 发送MQTT命令API
@app.route('/api/send_command', methods=['POST'])
@login_required
def send_command():
    """发送MQTT控制命令"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'code': 400, 'msg': 'No data provided'}), 400
        
        device_id = data.get('device_id')
        command_data = data.get('command_data')
        
        if not device_id or not command_data:
            return jsonify({'code': 400, 'msg': 'Device ID and command data are required'}), 400
        
        # 检查设备是否存在
        conn = sqlite3.connect(app.config['DB_PATH'])
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM devices WHERE device_id = ?", (device_id,))
        device = cursor.fetchone()
        conn.close()
        
        if not device:
            return jsonify({'code': 404, 'msg': 'Device not found'}), 404
        
        # 发布MQTT命令到对应的主题
        topic = f"control/command/{device_id}"
        mqtt_client.publish(topic, json.dumps(command_data), qos=1)
        
        return jsonify({
            'code': 200,
            'msg': 'Command sent successfully',
            'topic': topic,
            'command': command_data
        })
    except Exception as e:
        return jsonify({
            'code': 500,
            'msg': f'Failed to send command: {str(e)}'
        }), 500

# 删除设备API
@app.route('/api/delete_device/<string:device_id>', methods=['DELETE'])
@login_required
def delete_device(device_id):
    """删除设备"""
    try:
        # 只有管理员可以删除设备
        if session['role'] != 'admin':
            return jsonify({'code': 403, 'msg': '无权限删除设备'}), 403
        
        conn = sqlite3.connect(app.config['DB_PATH'])
        cursor = conn.cursor()
        
        # 检查设备是否存在
        cursor.execute("SELECT * FROM devices WHERE device_id = ?", (device_id,))
        if not cursor.fetchone():
            conn.close()
            return jsonify({'code': 404, 'msg': '设备不存在'}), 404
        
        try:
            # 删除设备相关的所有图片记录
            cursor.execute("DELETE FROM images WHERE device_id = ?", (device_id,))
            
            # 删除设备相关的用户记录
            cursor.execute("DELETE FROM users WHERE device_id = ?", (device_id,))
            
            # 删除设备记录
            cursor.execute("DELETE FROM devices WHERE device_id = ?", (device_id,))
            
            # 提交事务
            conn.commit()
            conn.close()
            
            return jsonify({
                'code': 200,
                'msg': '设备删除成功'
            })
        except Exception as e:
            # 回滚事务
            conn.rollback()
            conn.close()
            return jsonify({
                'code': 500,
                'msg': f'删除设备时出错: {str(e)}'
            }), 500
    except Exception as e:
        return jsonify({
            'code': 500,
            'msg': f'删除设备失败: {str(e)}'
        }), 500

if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=5000, debug=False, allow_unsafe_werkzeug=True)