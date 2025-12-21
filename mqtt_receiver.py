import paho.mqtt.client as mqtt
import json
import sqlite3
import time

# 配置
MQTT_BROKER = "111.230.253.226" 
MQTT_PORT = 1883
SENSOR_TOPIC = "control/sensor_data/+"
DB_PATH = "./iot.db"

# 初始化数据库
def init_db():
    conn = sqlite3.connect(DB_PATH)
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

# 连接回调函数
def on_connect(client, userdata, flags, rc):
    print(f"📡 已连接到MQTT Broker，返回码: {rc}")
    client.subscribe(SENSOR_TOPIC, qos=1)
    print(f"📡 已订阅传感器数据主题: {SENSOR_TOPIC}")

# 消息回调函数
def on_message(client, userdata, msg):
    try:
        # 解析消息
        topic = msg.topic
        payload = json.loads(msg.payload.decode('utf-8'))
        
        # 提取设备ID
        topic_parts = topic.split('/')
        device_id = topic_parts[2]
        
        print(f"📩 收到传感器数据 - 设备ID: {device_id}")
        
        # 保存数据到数据库
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        
        # 准备数据
        timestamp = payload.get('timestamp', time.strftime('%Y-%m-%d %H:%M:%S'))
        temperature_inside = payload.get('temperature_inside', None)
        temperature_outside = payload.get('temperature_outside', None)
        humidity = payload.get('humidity', None)
        duoj1 = payload.get('duoj1', None)
        duoj2 = payload.get('duoj2', None)
        duoj3 = payload.get('duoj3', None)
        duoj4 = payload.get('duoj4', None)
        feng1 = payload.get('feng1', None)
        feng2 = payload.get('feng2', None)
        jia = payload.get('jia', None)
        raw_data = json.dumps(payload)
        
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
        
    except Exception as e:
        print(f"❌ 处理消息时出错: {e}")

# 初始化数据库
init_db()

# 创建MQTT客户端
client = mqtt.Client()
client.on_connect = on_connect
client.on_message = on_message

# 连接到MQTT broker
client.connect(MQTT_BROKER, MQTT_PORT, 60)

# 启动监听
print("🚀 MQTT接收器已启动，正在监听消息...")
try:
    client.loop_forever()
except KeyboardInterrupt:
    print("⏹️  MQTT接收器已停止")
except Exception as e:
    print(f"💥 MQTT接收器意外停止: {e}")