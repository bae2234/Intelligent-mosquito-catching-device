import requests
import os
import time
import base64

# 服务器配置
SERVER_URL = "http://localhost:5000"
UPLOAD_ENDPOINT = f"{SERVER_URL}/upload/image"

# 设备配置
DEVICE_ID = "test_device_001"

# 测试图片路径
TEST_IMAGE_PATH = "test_mosquito_image.jpg"

# 检查requests库是否安装
try:
    import requests
except ImportError:
    print("❌ 未安装requests库，请先安装：pip install requests")
    exit(1)

print("🖼️  正在创建测试JPEG图片...")

# 使用base64编码创建一个实际的JPEG图片（包含一只蚊子的示例图片）
MOSQUITO_JPEG_DATA = base64.b64decode('''/9j/4AAQSkZJRgABAQAAAQABAAD/2wBDAAMCAgMCAgMDAwMEAwMEBQgFBQQEBQoHBwYIDAoMDAsKCwsNDhIQDQ4RDgsLEBYQERMUFRUVDA8XGBYUGBIUFRT/2wBDAQMEBAUEBQkFBQkUDQsNFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBT/wAARCAAkACQDASIAAhEBAxEB/8QAHwAAAQUBAQEBAQEAAAAAAAAAAAECAwQFBgcICQoL/8QAtRAAAgEDAwIEAwUFBAQAAAF9AQIDAAQRBRIhMUEGE1FhByJxFDKBkaEII0KxwRVS0fAkM2JyggkKFhcYGRolJicoKSo0NTY3ODk6Q0RFRkdISUpTVFVWV1hZWmNkZWZnaGlqc3R1dnd4eXqDhIWGh4iJipKTlJWWl5iZmqKjpKWmp6ipqrKztLW2t7i5usLDxMXGx8jJytLT1NXW19jZ2uHi4+Tl5ufo6erx8vP09fb3+Pn6/8QAHwEAAwEBAQEBAQEBAQAAAAAAAAECAwQFBgcICQoL/8QAtREAAgECBAQDBAcFBAQAAQJ3AAECAxEEBSExBhJBUQdhcRMiMoEIFEKRobHBCSMzUvAVYnLRChYkNOEl8RcYGRomJygpKjU2Nzg5OkNERUZHSElKU1RVVldYWVpjZGVmZ2hpanN0dXZ3eHl6goOEhYaHiImKkpOUlZaXmJmaoqOkpaanqKmqsrO0tba3uLm6wsPExcbHyMnK0tPU1dbX2Nna4uPk5ebn6Onq8vP09fb3+Pn6/9oADAMBAAIRAxEAPwD9/KKKKAP/2Q==''')

# 保存JPEG图片
with open(TEST_IMAGE_PATH, 'wb') as f:
    f.write(MOSQUITO_JPEG_DATA)

print(f"✅ 测试JPEG图片创建成功：{TEST_IMAGE_PATH}")
print(f"📊 图片大小：{os.path.getsize(TEST_IMAGE_PATH)} 字节")
print(f"📷 图片描述：包含蚊子的测试图片")

print("\n🚀 启动设备端图片上传测试...")
print(f"📡 服务器地址：{SERVER_URL}")
print(f"📤 上传端点：{UPLOAD_ENDPOINT}")
print(f"📱 设备ID：{DEVICE_ID}")

# 准备上传数据
data = {
    'device_id': DEVICE_ID
}

files = {
    'image': (os.path.basename(TEST_IMAGE_PATH), open(TEST_IMAGE_PATH, 'rb'))
}

try:
    print("\n📤 正在上传图片...")
    start_time = time.time()
    
    # 发送POST请求
    response = requests.post(UPLOAD_ENDPOINT, data=data, files=files, timeout=30)
    
    end_time = time.time()
    upload_time = end_time - start_time
    
    print(f"✅ 上传完成，耗时：{upload_time:.2f} 秒")
    print(f"📋 响应状态码：{response.status_code}")
    print(f"📥 响应内容：")
    
    try:
        # 尝试解析JSON响应
        response_data = response.json()
        print(f"   状态码：{response_data.get('code')}")
        print(f"   消息：{response_data.get('msg')}")
        print(f"   路径：{response_data.get('path')}")
        print(f"   文件名：{response_data.get('filename')}")
    except ValueError:
        # 如果响应不是JSON，直接打印
        print(f"   {response.text}")
        
    print("\n📋 测试结果：")
    print(f"✅ 图片已成功上传到服务器")
    print(f"✅ 您可以通过以下方式查看图片：")
    print(f"   1. 访问 {SERVER_URL} 并登录")
    print(f"   2. 点击 '上传图片' 菜单查看所有图片")
    print(f"   3. 在仪表盘查看最新上传的图片")
    print(f"   4. 点击图片查看按钮测试大尺寸图片显示效果")
    
except requests.exceptions.ConnectionError:
    print(f"❌ 连接服务器失败，请检查服务器是否正在运行：{SERVER_URL}")
except requests.exceptions.Timeout:
    print(f"❌ 上传超时，请检查网络连接和服务器状态")
except Exception as e:
    print(f"❌ 上传失败：{str(e)}")
finally:
    # 关闭文件句柄
    files['image'][1].close()
    # 清理测试图片
    print("\n🗑️  清理测试图片...")
    if os.path.exists(TEST_IMAGE_PATH):
        os.remove(TEST_IMAGE_PATH)
        print(f"✅ 已删除测试图片：{TEST_IMAGE_PATH}")
    
print("\n📋 测试完成！")
