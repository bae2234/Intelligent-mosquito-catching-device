import paho.mqtt.client as mqtt
import json
import sqlite3
import time
import threading
import os
import requests

class MQTTServer:
    def __init__(self):
        # 配置
        self.MQTT_BROKER = "localhost"# 本地MQTT Broker
        self.MQTT_PORT = 1883  
        self.SENSOR_TOPIC = "control/sensor_data/+"
        self.COMMAND_TOPIC = "control/command/+"
        self.DB_PATH = "./iot.db"
        self.IMAGE_PATH = "/data/images/"
        self.DATA_RETENTION_DAYS = 7  # 数据保留7天
        
        # 用于存储设备注册时间，防止频繁注册
        self.registration_times = {}
        
        # 设备ID格式正则表达式（允许字母、数字、下划线和连字符，长度3-20）
        import re
        self.DEVICE_ID_PATTERN = re.compile(r'^[a-zA-Z0-9_-]{3,20}$')
        
        # 初始化MQTT客户端
        self.client = mqtt.Client()
        self.client.on_connect = self.on_connect
        self.client.on_message = self.on_message
        
        # 连接到MQTT broker
        self.client.connect(self.MQTT_BROKER, self.MQTT_PORT, 60)
        
        # 初始化数据库
        self.init_db()
        
        # 启动数据清理线程
        self.start_data_cleanup()
    
    def init_db(self):
        """初始化数据库"""
        conn = sqlite3.connect(self.DB_PATH)
        c = conn.cursor()
        c.execute('''CREATE TABLE IF NOT EXISTS sensor_data (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    device_id TEXT NOT NULL,
                    timestamp TEXT,
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
                    )''')
        conn.commit()
        conn.close()
    
    def on_connect(self, client, userdata, flags, rc):
        """连接回调函数"""
        print(f"📡 已连接到MQTT Broker，返回码: {rc}")
        client.subscribe(self.SENSOR_TOPIC, qos=1)
        client.subscribe(self.COMMAND_TOPIC, qos=1)
        print(f"📡 已订阅传感器数据: {self.SENSOR_TOPIC}")
        print(f"📡 已订阅控制命令: {self.COMMAND_TOPIC}")
    
    def auto_register_device(self, device_id):
        """自动注册设备"""
        import time
        
        # 1. 设备ID格式验证
        if not self.DEVICE_ID_PATTERN.match(device_id):
            print(f"❌ [MQTT自动注册] 设备ID格式无效: {device_id}")
            return False
        
        # 2. 限制注册频率（同一设备ID，60秒内只能注册一次）
        current_time = time.time()
        if device_id in self.registration_times:
            if current_time - self.registration_times[device_id] < 60:
                print(f"❌ [MQTT自动注册] 注册频率过高，请稍后再试: {device_id}")
                return False
        self.registration_times[device_id] = current_time
        
        app_conn = None
        app_cursor = None
        
        try:
            # 连接到app.py使用的数据库
            app_db_path = './iot.db'
            app_conn = sqlite3.connect(app_db_path)
            app_cursor = app_conn.cursor()
            
            # 3. 检查设备是否已存在于用户表
            app_cursor.execute("SELECT * FROM users WHERE username=?", (device_id,))
            user_exists = app_cursor.fetchone() is not None
            
            if not user_exists:
                # 注册设备用户
                app_cursor.execute("INSERT INTO users (username, password, role, device_id) VALUES (?, ?, ?, ?)", 
                              (device_id, '123456', 'device', device_id))
                print(f"🔧 [MQTT自动注册] 成功注册设备用户: {device_id}")
            
            # 4. 检查设备是否已存在于设备表
            app_cursor.execute("SELECT * FROM devices WHERE device_id=?", (device_id,))
            device_exists = app_cursor.fetchone() is not None
            
            if not device_exists:
                # 创建设备记录
                app_cursor.execute("INSERT INTO devices (device_id, name) VALUES (?, ?)", 
                              (device_id, f'设备{device_id}'))
                print(f"🔧 [MQTT自动注册] 成功创建设备记录: {device_id}")
            
            # 5. 提交事务
            app_conn.commit()
            
            print(f"✅ [MQTT自动注册] 设备注册成功: {device_id}")
            return True
        except sqlite3.IntegrityError as e:
            print(f"❌ [MQTT自动注册] 设备注册冲突: {device_id}, 错误: {e}")
            if app_conn:
                app_conn.rollback()
            return True  # 即使发生冲突，也返回成功，因为设备可能已经存在
        except Exception as e:
            print(f"❌ [MQTT自动注册] 设备注册失败: {device_id}, 错误: {type(e).__name__}: {e}")
            if app_conn:
                app_conn.rollback()
            return False
        finally:
            if app_cursor:
                app_cursor.close()
            if app_conn:
                app_conn.close()
    
    def on_message(self, client, userdata, msg):
        """消息回调函数"""
        try:
            # 解析消息
            topic = msg.topic
            print(f"📩 收到消息 - 主题: {topic}")
            print(f"📋 消息内容: {msg.payload.decode('utf-8')}")
            
            payload = json.loads(msg.payload.decode('utf-8'))
            
            # 提取设备ID
            topic_parts = topic.split('/')
            if len(topic_parts) >= 3:
                device_id = topic_parts[2]
                print(f"🔌 设备ID: {device_id}")
            else:
                device_id = "unknown"
                print(f"❓ 无法从主题中提取设备ID: {topic}")
            
            # 自动注册设备
            print(f"🔧 尝试自动注册设备: {device_id}")
            self.auto_register_device(device_id)
            
            # 根据主题类型处理消息
            if topic.startswith("control/sensor_data/"):
                # 处理传感器数据
                print(f"📊 处理传感器数据 - 设备ID: {device_id}")
                self.save_sensor_data(device_id, payload)
                # 发送确认消息
                print(f"✅ 保存传感器数据成功，发送确认消息")
                self.send_confirm(device_id, payload)
            elif topic.startswith("control/command/"):
                # 处理控制命令
                print(f"⚙️  处理控制命令 - 设备ID: {device_id}")
                self.process_command(device_id, payload)
            else:
                print(f"❓ 未知主题类型: {topic}")
        except json.JSONDecodeError as e:
            print(f"❌ JSON解析错误: {e}")
            print(f"📋 原始消息: {msg.payload.decode('utf-8')}")
        except Exception as e:
            print(f"❌ 处理消息时出错: {type(e).__name__}: {e}")
            import traceback
            traceback.print_exc()
    
    def push_data_to_frontend(self, data):
        """将数据推送到前端"""
        try:
            print(f"\n📤 开始推送数据到前端:")
            print(f"📋 推送数据内容: {json.dumps(data, indent=2, ensure_ascii=False)}")
            
            # 调用app.py的push_sensor_data API端点
            print("🔌 调用 http://localhost:5000/push_sensor_data 端点")
            response = requests.post('http://localhost:5000/push_sensor_data', json=data, timeout=5)
            
            print(f"📩 收到响应: 状态码 {response.status_code}")
            print(f"📋 响应内容: {response.text}")
            
            if response.status_code == 200:
                print(f"✅ 已成功推送传感器数据到前端")
            else:
                print(f"❌ 推送数据到前端失败: {response.status_code}")
        except Exception as e:
            print(f"❌ 推送数据到前端时出错: {type(e).__name__}: {e}")
            import traceback
            traceback.print_exc()
    
    def save_sensor_data(self, device_id, data):
        """保存传感器数据到数据库"""
        try:
            conn = sqlite3.connect(self.DB_PATH)
            c = conn.cursor()
            
            # 准备数据
            timestamp = data.get('timestamp', time.strftime('%Y-%m-%d %H:%M:%S'))
            temperature_inside = data.get('temperature_inside', None)
            temperature_outside = data.get('temperature_outside', None)
            humidity = data.get('humidity', None)
            duoj1 = data.get('duoj1', None)
            duoj2 = data.get('duoj2', None)
            duoj3 = data.get('duoj3', None)
            duoj4 = data.get('duoj4', None)
            feng1 = data.get('feng1', None)
            feng2 = data.get('feng2', None)
            jia = data.get('jia', None)
            raw_data = json.dumps(data)
            
            # 插入数据
            c.execute('''INSERT INTO sensor_data (
                        device_id, timestamp, temperature_inside, temperature_outside, humidity,
                        duoj1, duoj2, duoj3, duoj4, feng1, feng2, jia, raw_data
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''',
                        (device_id, timestamp, temperature_inside, temperature_outside, humidity,
                         duoj1, duoj2, duoj3, duoj4, feng1, feng2, jia, raw_data))
            
            conn.commit()
            conn.close()
            print(f"💾 已保存传感器数据 - 设备ID: {device_id}")
            
            # 推送到前端
            sensor_data = {
                "device_id": device_id,
                "timestamp": timestamp,
                "temperature_inside": temperature_inside,
                "temperature_outside": temperature_outside,
                "humidity": humidity,
                "duoj1": duoj1,
                "duoj2": duoj2,
                "duoj3": duoj3,
                "duoj4": duoj4,
                "feng1": feng1,
                "feng2": feng2,
                "jia": jia
            }
            self.push_data_to_frontend(sensor_data)
        except Exception as e:
            print(f"❌ 保存传感器数据时出错: {e}")
    
    def send_confirm(self, device_id, original_data):
        """发送确认消息"""
        try:
            # 构造确认消息
            confirm_msg = {
                "device_id": device_id,
                "message_id": original_data.get('timestamp', ''),
                "status": "success"
            }
            
            # 发布确认消息
            confirm_topic = f"control/confirm/{device_id}"
            self.client.publish(confirm_topic, json.dumps(confirm_msg), qos=1)
            print(f"📤 已发送确认消息 - 主题: {confirm_topic}")
        except Exception as e:
            print(f"❌ 发送确认消息时出错: {e}")
    
    def process_command(self, device_id, command_data):
        """处理控制命令"""
        try:
            # 这里可以添加具体的命令处理逻辑
            command = command_data.get('command', '')
            params = command_data.get('params', {})
            
            print(f"⚙️ 处理控制命令 - 设备ID: {device_id}, 命令类型: {command}, 命令参数: {params}")
            
            # 示例：如果命令是"restart"，可以执行相应操作
            if command == "restart":
                print(f"🔄 执行重启命令 - 设备ID: {device_id}")
            
            # 发送命令执行结果确认
            self.send_confirm(device_id, command_data)
        except Exception as e:
            print(f"❌ 处理控制命令时出错: {e}")
    
    def start_data_cleanup(self):
        """启动数据清理线程"""
        def cleanup_task():
            while True:
                print(f"\n🗑️  开始执行定期数据清理...")
                self.clean_old_sensor_data()
                self.clean_old_images()
                print(f"✅ 数据清理完成，下次清理将在24小时后执行")
                time.sleep(86400)  # 每24小时执行一次清理
        
        cleanup_thread = threading.Thread(target=cleanup_task, daemon=True)
        cleanup_thread.start()
        print(f"🔄 数据清理线程已启动，将每24小时清理一次{self.DATA_RETENTION_DAYS}天前的数据")
    
    def clean_old_sensor_data(self):
        """清理旧的传感器数据"""
        try:
            conn = sqlite3.connect(self.DB_PATH)
            c = conn.cursor()
            
            # 计算截止时间（7天前）
            cutoff_time = time.strftime('%Y-%m-%d', time.localtime(time.time() - self.DATA_RETENTION_DAYS * 86400))
            
            # 删除旧数据
            c.execute("DELETE FROM sensor_data WHERE timestamp < ?", (cutoff_time,))
            deleted_count = c.rowcount
            
            conn.commit()
            conn.close()
            
            print(f"🗄️  已清理 {deleted_count} 条 {self.DATA_RETENTION_DAYS} 天前的传感器数据")
        except Exception as e:
            print(f"❌ 清理旧传感器数据时出错: {e}")
    
    def clean_old_images(self):
        """清理旧的图片文件"""
        try:
            # 计算7天前的时间戳
            cutoff_time = time.time() - self.DATA_RETENTION_DAYS * 86400
            
            deleted_count = 0
            total_size = 0
            
            # 遍历图片目录
            for root, dirs, files in os.walk(self.IMAGE_PATH):
                for file in files:
                    file_path = os.path.join(root, file)
                    
                    # 获取文件修改时间
                    if os.path.getmtime(file_path) < cutoff_time:
                        # 记录文件大小
                        file_size = os.path.getsize(file_path)
                        total_size += file_size
                        
                        # 删除文件
                        os.remove(file_path)
                        deleted_count += 1
            
            # 清理空目录
            for root, dirs, files in os.walk(self.IMAGE_PATH, topdown=False):
                for dir in dirs:
                    dir_path = os.path.join(root, dir)
                    if not os.listdir(dir_path):
                        os.rmdir(dir_path)
            
            print(f"🖼️  已清理 {deleted_count} 个 {self.DATA_RETENTION_DAYS} 天前的图片文件")
            print(f"📊 释放存储空间: {total_size / (1024 * 1024):.2f} MB")
        except Exception as e:
            print(f"❌ 清理旧图片文件时出错: {e}")
    
    def run(self):
        """启动服务器"""
        print("🚀 MQTT服务器已启动，正在监听消息...")
        try:
            self.client.loop_forever()
        except KeyboardInterrupt:
            print("⏹️  MQTT服务器已停止")
        except Exception as e:
            print(f"💥 MQTT服务器意外停止: {e}")

if __name__ == "__main__":
    server = MQTTServer()
    server.run()