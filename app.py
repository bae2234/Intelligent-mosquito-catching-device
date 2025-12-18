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

# 插入管理员账号
cursor.execute("SELECT * FROM users WHERE username='admin'")
if not cursor.fetchone():
    cursor.execute("INSERT INTO users (username, password, role) VALUES (?, ?, ?)", ('admin', '123456', 'admin'))

conn.commit()
conn.close()

# 初始化SocketIO
# socketio = SocketIO(app)
socketio = SocketIO(app, async_mode='eventlet')

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
                    <meta name="viewport" content="width=device-width, initial-scale=1.0">
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
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
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
    for device in devices:
        device_id, name, status, created_at = device
        location = "未知位置"  # 设备表中没有location字段，设置默认值
        
        # 获取设备的最新图片信息
        cursor.execute("SELECT id, image_path, original_filename, receive_time FROM images WHERE device_id = ? ORDER BY receive_time DESC LIMIT 1",
                      (device_id,))
        latest_image = cursor.fetchone()
        
        image_info = {
            'id': latest_image[0] if latest_image else None,
            'image_path': latest_image[1] if latest_image else None,
            'original_filename': latest_image[2] if latest_image else None,
            'receive_time': latest_image[3] if latest_image else None
        }
        
        device_list.append({
            'device_id': device_id,
            'name': name,
            'status': status,
            'location': location,
            'created_at': created_at,
            'latest_image': image_info
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
    try:
        conn = sqlite3.connect(app.config['DB_PATH'])
        cursor = conn.cursor()
        
        # 获取图片信息，包括关联的设备ID
        cursor.execute("SELECT image_path, device_id FROM images WHERE id = ?", (image_id,))
        image = cursor.fetchone()
        
        if not image:
            conn.close()
            return jsonify({'code': 404, 'msg': '图片不存在'})
        
        image_path = image[0]
        device_id = image[1]
        
        # 检查权限：普通用户只能删除自己设备的图片
        if session['role'] != 'admin' and session['device_id'] != device_id:
            conn.close()
            return jsonify({'code': 403, 'msg': '无权限删除该图片'})
        
        # 删除图片文件
        if os.path.exists(image_path):
            os.remove(image_path)
        
        # 从数据库中删除图片记录
        cursor.execute("DELETE FROM images WHERE id = ?", (image_id,))
        
        # 删除关联的设备条目
        cursor.execute("DELETE FROM devices WHERE device_id = ?", (device_id,))
        
        # 删除用户设备关联
        cursor.execute("DELETE FROM user_devices WHERE device_id = ?", (device_id,))
        
        conn.commit()
        conn.close()
        
        return jsonify({'code': 200, 'msg': '图片和关联设备已成功删除'})
    except Exception as e:
        return jsonify({'code': 500, 'msg': f'删除失败: {str(e)}'})

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
def serve_image(filename):
    """提供图片文件的静态访问"""
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

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

if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=5000, debug=False)