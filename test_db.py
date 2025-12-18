import sqlite3
import os

# 测试数据库初始化
DB_PATH = './iot.db'

print(f"Testing database initialization for {DB_PATH}")
print(f"Database file exists: {os.path.exists(DB_PATH)}")
if os.path.exists(DB_PATH):
    print(f"Database file size: {os.path.getsize(DB_PATH)} bytes")

# 尝试连接并创建表
conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()

print("\nTrying to create tables...")

# 创建用户表
try:
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
    print("✓ users table created successfully")
except Exception as e:
    print(f"✗ Error creating users table: {e}")

# 创建设备表
try:
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS devices (
        device_id TEXT PRIMARY KEY,
        name TEXT NOT NULL,
        status TEXT DEFAULT 'active',
        created_at TEXT DEFAULT CURRENT_TIMESTAMP
    )
    ''')
    print("✓ devices table created successfully")
except Exception as e:
    print(f"✗ Error creating devices table: {e}")

# 创建图片表
try:
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS images (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        device_id TEXT NOT NULL,
        image_path TEXT NOT NULL,
        original_filename TEXT NOT NULL,
        receive_time TEXT NOT NULL
    )
    ''')
    print("✓ images table created successfully")
except Exception as e:
    print(f"✗ Error creating images table: {e}")

# 创建用户设备关联表
try:
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS user_devices (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        device_id TEXT NOT NULL,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users (id),
        FOREIGN KEY (device_id) REFERENCES devices (device_id),
        UNIQUE (user_id, device_id)
    )
    ''')
    print("✓ user_devices table created successfully")
except Exception as e:
    print(f"✗ Error creating user_devices table: {e}")

# 插入管理员账号
try:
    cursor.execute("SELECT * FROM users WHERE username='admin'")
    if not cursor.fetchone():
        cursor.execute("INSERT INTO users (username, password, role) VALUES (?, ?, ?)", ('admin', '123456', 'admin'))
        print("✓ Admin account inserted successfully")
    else:
        print("✓ Admin account already exists")
except Exception as e:
    print(f"✗ Error inserting admin account: {e}")

conn.commit()
conn.close()

print("\nDatabase initialization test completed!")
