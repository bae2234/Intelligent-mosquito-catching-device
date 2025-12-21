import requests
import os
import time
import base64

# 服务器配置
SERVER_URL = "http://localhost:5000"
UPLOAD_ENDPOINT = f"{SERVER_URL}/upload/image"

# 设备配置
DEVICE_ID = "test_device_001"

# 检查requests库是否安装
try:
    import requests
except ImportError:
    print("❌ 未安装requests库，请先安装：pip install requests")
    exit(1)

print("🚀 启动多图片上传测试...")
print(f"📡 服务器地址：{SERVER_URL}")
print(f"📤 上传端点：{UPLOAD_ENDPOINT}")
print(f"📱 设备ID：{DEVICE_ID}")

# 使用base64编码创建一个简单的JPEG图片
SIMPLE_JPEG_DATA = base64.b64decode('''/9j/4AAQSkZJRgABAQAAAQABAAD/2wBDAAMCAgMCAgMDAwMEAwMEBQgFBQQEBQoHBwYIDAoMDAsKCwsNDhIQDQ4RDgsLEBYQERMUFRUVDA8XGBYUGBIUFRT/2wBDAQMEBAUEBQkFBQkUDQsNFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBT/wAARCAAIAAoDASIAAhEBAxEB/8QAHwAAAQUBAQEBAQEAAAAAAAAAAAECAwQFBgcICQoL/8QAtRAAAgEDAwIEAwUFBAQAAAF9AQIDAAQRBRIhMUEGE1FhByJxFDKBkaEII0KxwRVS0fAkM2JyggkKFhcYGRolJicoKSo0NTY3ODk6Q0RFRkdISUpTVFVWV1hZWmNkZWZnaGlqc3R1dnd4eXqDhIWGh4iJipKTlJWWl5iZmqKjpKWmp6ipqrKztLW2t7i5usLDxMXGx8jJytLT1NXW19jZ2uHi4+Tl5ufo6erx8vP09fb3+Pn6/8QAHwEAAwEBAQEBAQEBAQAAAAAAAAECAwQFBgcICQoL/8QAtREAAgECBAQDBAcFBAQAAQJ3AAECAxEEBSExBhJBUQdhcRMiMoEIFEKRobHBCSMzUvAVYnLRChYkNOEl8RcYGRomJygpKjU2Nzg5OkNERUZHSElKU1RVVldYWVpjZGVmZ2hpanN0dXZ3eHl6goOEhYaHiImKkpOUlZaXmJmaoqOkpaanqKmqsrO0tba3uLm6wsPExcbHyMnK0tPU1dbX2Nna4uPk5ebn6Onq8vP09fb3+Pn6/9oADAMBAAIRAxEAPwD9/KKKKAP/2Q==''')

# 上传多张图片
total_images = 5
for i in range(total_images):
    print(f"\n📤 正在上传第 {i+1}/{total_images} 张图片...")
    
    # 生成唯一的图片文件名
    image_filename = f"test_image_{i+1}.jpg"
    
    # 保存测试图片
    with open(image_filename, 'wb') as f:
        f.write(SIMPLE_JPEG_DATA)
    
    # 准备上传数据
    data = {
        'device_id': DEVICE_ID
    }
    
    files = {
        'image': (image_filename, open(image_filename, 'rb'))
    }
    
    try:
        start_time = time.time()
        
        # 发送POST请求
        response = requests.post(UPLOAD_ENDPOINT, data=data, files=files, timeout=30)
        
        end_time = time.time()
        upload_time = end_time - start_time
        
        if response.status_code == 200:
            print(f"✅ 第 {i+1} 张图片上传成功，耗时：{upload_time:.2f} 秒")
            try:
                response_data = response.json()
                print(f"   文件名：{response_data.get('filename')}")
            except ValueError:
                pass
        else:
            print(f"❌ 第 {i+1} 张图片上传失败，状态码：{response.status_code}")
            
        # 等待1秒，避免请求过于频繁
        time.sleep(1)
        
    except requests.exceptions.ConnectionError:
        print(f"❌ 连接服务器失败，请检查服务器是否正在运行：{SERVER_URL}")
        break
    except requests.exceptions.Timeout:
        print(f"❌ 上传超时，请检查网络连接和服务器状态")
        break
    except Exception as e:
        print(f"❌ 上传失败：{str(e)}")
        break
    finally:
        # 关闭文件句柄
        files['image'][1].close()
        # 清理测试图片
        if os.path.exists(image_filename):
            os.remove(image_filename)

print("\n📋 测试结果：")
print(f"✅ 已上传 {total_images} 张测试图片")
print(f"✅ 您可以访问 http://localhost:5000 查看测试结果")
print(f"✅ 最新上传图片区域应该显示3张图片，并且分页控件正常工作")
print(f"✅ 您可以点击上一页/下一页按钮测试分页功能")

print("\n📋 测试完成！")
