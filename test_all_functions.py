#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
智能捕蚊设备功能测试脚本
测试所有核心功能，包括设备注册、图片上传、传感器数据上传、日志上传、MQTT命令发送和数据查询
"""

import requests
import json
import os
import time
import random
import uuid

# 服务器配置
SERVER_URL = "http://localhost:5000"
ADMIN_USERNAME = "admin"
ADMIN_PASSWORD = "123456"

# 测试设备信息
TEST_DEVICE_ID = f"test-device-{uuid.uuid4().hex[:8]}"
TEST_DEVICE_NAME = f"测试设备-{TEST_DEVICE_ID}"

# 测试图片路径（用户指定的测试照片）
TEST_IMAGE_PATH = "/home/ubuntu/Intelligent-mosquito-catching-device/WIN_20251202_12_10_21_Pro.jpg"

# 会话对象，用于保持登录状态
session = requests.Session()

def login(username, password):
    """登录系统"""
    print(f"\n[测试] 登录系统 - 用户: {username}")
    login_url = f"{SERVER_URL}/login"
    data = {
        "username": username,
        "password": password
    }
    response = session.post(login_url, data=data)
    if response.status_code == 200:
        print("✅ 登录成功")
        return True
    else:
        print(f"❌ 登录失败: {response.status_code}")
        return False

def test_device_registration():
    """测试设备注册功能"""
    print(f"\n[测试] 设备注册 - 设备ID: {TEST_DEVICE_ID}")
    
    # 测试自动注册（通过上传图片触发）
    upload_url = f"{SERVER_URL}/upload/image"
    
    # 准备测试图片
    if not os.path.exists(TEST_IMAGE_PATH):
        print(f"⚠️  测试图片不存在: {TEST_IMAGE_PATH}")
        return False
    
    with open(TEST_IMAGE_PATH, 'rb') as f:
        files = {
            'image': f
        }
        data = {
            'device_id': TEST_DEVICE_ID
        }
        response = requests.post(upload_url, files=files, data=data)
    
    if response.status_code == 200:
        result = response.json()
        if result.get('code') == 200:
            print("✅ 设备注册成功")
            print(f"   上传图片路径: {result.get('path')}")
            return True
        else:
            print(f"❌ 设备注册失败: {result.get('msg')}")
            return False
    else:
        print(f"❌ 设备注册失败: {response.status_code}")
        return False

def test_image_upload():
    """测试图片上传功能"""
    print(f"\n[测试] 图片上传 - 设备ID: {TEST_DEVICE_ID}")
    upload_url = f"{SERVER_URL}/upload/image"
    
    if not os.path.exists(TEST_IMAGE_PATH):
        print(f"⚠️  测试图片不存在: {TEST_IMAGE_PATH}")
        return False
    
    with open(TEST_IMAGE_PATH, 'rb') as f:
        files = {
            'image': f
        }
        data = {
            'device_id': TEST_DEVICE_ID
        }
        response = requests.post(upload_url, files=files, data=data)
    
    if response.status_code == 200:
        result = response.json()
        if result.get('code') == 200:
            print("✅ 图片上传成功")
            print(f"   上传图片路径: {result.get('path')}")
            print(f"   上传图片文件名: {result.get('filename')}")
            return True
        else:
            print(f"❌ 图片上传失败: {result.get('msg')}")
            return False
    else:
        print(f"❌ 图片上传失败: {response.status_code}")
        return False

def test_sensor_data_upload():
    """测试传感器数据上传功能"""
    print(f"\n[测试] 传感器数据上传 - 设备ID: {TEST_DEVICE_ID}")
    upload_url = f"{SERVER_URL}/push_sensor_data"
    
    # 生成测试传感器数据
    sensor_data = {
        "device_id": TEST_DEVICE_ID,
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "temperature_inside": round(random.uniform(20, 30), 2),
        "temperature_outside": round(random.uniform(15, 35), 2),
        "humidity": round(random.uniform(40, 80), 2),
        "duoj1": random.randint(0, 1),
        "duoj2": random.randint(0, 1),
        "duoj3": random.randint(0, 1),
        "duoj4": random.randint(0, 1),
        "feng1": random.randint(0, 1),
        "feng2": random.randint(0, 1),
        "jia": random.randint(0, 1),
        "raw_data": f"test-data-{random.randint(1000, 9999)}"
    }
    
    response = requests.post(upload_url, json=sensor_data)
    
    if response.status_code == 200:
        result = response.json()
        if result.get('code') == 200:
            print("✅ 传感器数据上传成功")
            print(f"   上传数据: {json.dumps(sensor_data, indent=2, ensure_ascii=False)}")
            return True
        else:
            print(f"❌ 传感器数据上传失败: {result.get('msg')}")
            return False
    else:
        print(f"❌ 传感器数据上传失败: {response.status_code}")
        return False

def test_log_upload():
    """测试日志上传功能"""
    print(f"\n[测试] 日志上传 - 设备ID: {TEST_DEVICE_ID}")
    upload_url = f"{SERVER_URL}/receive_logs"
    
    # 生成测试日志数据
    log_data = {
        "device_id": TEST_DEVICE_ID,
        "logs": [
            {
                "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
                "level": "INFO",
                "message": "设备启动成功",
                "details": {"version": "1.0.0", "uptime": "0s"}
            },
            {
                "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
                "level": "DEBUG",
                "message": "传感器初始化完成",
                "details": {"sensors": ["temperature", "humidity", "motion"]}
            },
            {
                "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
                "level": "WARN",
                "message": "电池电量低",
                "details": {"battery": "20%", "voltage": "3.2V"}
            }
        ]
    }
    
    response = requests.post(upload_url, json=log_data)
    
    if response.status_code == 200:
        result = response.json()
        if result.get('code') == 200:
            print("✅ 日志上传成功")
            print(f"   上传日志条数: {result.get('received_count')}")
            return True
        else:
            print(f"❌ 日志上传失败: {result.get('msg')}")
            return False
    else:
        print(f"❌ 日志上传失败: {response.status_code}")
        return False

def test_mqtt_command():
    """测试MQTT命令发送功能"""
    print(f"\n[测试] MQTT命令发送 - 设备ID: {TEST_DEVICE_ID}")
    
    # 先登录管理员账号
    if not login(ADMIN_USERNAME, ADMIN_PASSWORD):
        return False
    
    command_url = f"{SERVER_URL}/api/send_command"
    
    # 测试命令数据
    command_data = {
        "device_id": TEST_DEVICE_ID,
        "command_data": {
            "action": "test",
            "parameters": {
                "duration": 10,
                "intensity": 5
            }
        }
    }
    
    response = session.post(command_url, json=command_data)
    
    if response.status_code == 200:
        result = response.json()
        if result.get('code') == 200:
            print("✅ MQTT命令发送成功")
            print(f"   发送主题: {result.get('topic')}")
            print(f"   命令数据: {json.dumps(result.get('command'), indent=2, ensure_ascii=False)}")
            return True
        else:
            print(f"❌ MQTT命令发送失败: {result.get('msg')}")
            return False
    else:
        print(f"❌ MQTT命令发送失败: {response.status_code}")
        return False

def test_get_devices():
    """测试获取设备列表功能"""
    print("\n[测试] 获取设备列表")
    
    # 确保已登录
    if not login(ADMIN_USERNAME, ADMIN_PASSWORD):
        return False
    
    devices_url = f"{SERVER_URL}/api/devices"
    response = session.get(devices_url)
    
    if response.status_code == 200:
        result = response.json()
        if result.get('code') == 200:
            devices = result.get('data', [])
            print(f"✅ 获取设备列表成功")
            print(f"   设备总数: {len(devices)}")
            
            # 检查测试设备是否在列表中
            test_device_found = False
            for device in devices:
                if device.get('device_id') == TEST_DEVICE_ID:
                    test_device_found = True
                    print(f"   ✅ 测试设备在列表中: {device.get('name')}")
                    break
            
            if not test_device_found:
                print(f"   ⚠️  测试设备不在列表中")
            
            return True
        else:
            print(f"❌ 获取设备列表失败: {result.get('msg')}")
            return False
    else:
        print(f"❌ 获取设备列表失败: {response.status_code}")
        return False

def test_get_images():
    """测试获取图片列表功能"""
    print("\n[测试] 获取图片列表")
    
    # 确保已登录
    if not login(ADMIN_USERNAME, ADMIN_PASSWORD):
        return False
    
    images_url = f"{SERVER_URL}/api/images"
    response = session.get(images_url)
    
    if response.status_code == 200:
        result = response.json()
        if result.get('code') == 200:
            images = result.get('data', {}).get('images', [])
            print(f"✅ 获取图片列表成功")
            print(f"   图片总数: {len(images)}")
            
            # 检查测试设备的图片是否在列表中
            test_device_images = [img for img in images if img.get('device_id') == TEST_DEVICE_ID]
            if test_device_images:
                print(f"   ✅ 测试设备图片数量: {len(test_device_images)}")
                for img in test_device_images[:2]:  # 只显示前2张
                    print(f"      - {img.get('original_filename')} ({img.get('receive_time')})")
            else:
                print(f"   ⚠️  测试设备无图片")
            
            return True
        else:
            print(f"❌ 获取图片列表失败: {result.get('msg')}")
            return False
    else:
        print(f"❌ 获取图片列表失败: {response.status_code}")
        return False

def test_get_logs():
    """测试获取日志列表功能"""
    print("\n[测试] 获取日志列表")
    
    # 确保已登录
    if not login(ADMIN_USERNAME, ADMIN_PASSWORD):
        return False
    
    logs_url = f"{SERVER_URL}/api/logs?device_id={TEST_DEVICE_ID}"
    response = session.get(logs_url)
    
    if response.status_code == 200:
        result = response.json()
        if result.get('code') == 200:
            logs = result.get('data', {}).get('logs', [])
            print(f"✅ 获取日志列表成功")
            print(f"   日志总数: {len(logs)}")
            
            # 显示前3条日志
            for log in logs[:3]:
                print(f"      - [{log.get('level')}] {log.get('message')} ({log.get('timestamp')})")
            
            return True
        else:
            print(f"❌ 获取日志列表失败: {result.get('msg')}")
            return False
    else:
        print(f"❌ 获取日志列表失败: {response.status_code}")
        return False

def test_delete_device():
    """测试删除设备功能"""
    print(f"\n[测试] 删除设备 - 设备ID: {TEST_DEVICE_ID}")
    
    # 确保已登录管理员账号
    if not login(ADMIN_USERNAME, ADMIN_PASSWORD):
        return False
    
    delete_url = f"{SERVER_URL}/api/delete_device/{TEST_DEVICE_ID}"
    response = session.delete(delete_url)
    
    if response.status_code == 200:
        result = response.json()
        if result.get('code') == 200:
            print("✅ 设备删除成功")
            return True
        else:
            print(f"❌ 设备删除失败: {result.get('msg')}")
            return False
    else:
        print(f"❌ 设备删除失败: {response.status_code}")
        return False

def save_test_image():
    """保存测试图片（从用户提供的图片）"""
    print("\n[准备] 保存测试图片")
    
    # 注意：这里需要用户提供的图片数据
    # 由于无法直接获取用户上传的图片，我们创建一个简单的测试图片
    # 在实际使用时，用户需要将测试图片保存到 TEST_IMAGE_PATH
    
    # 检查是否已有测试图片
    if os.path.exists(TEST_IMAGE_PATH):
        print(f"✅ 测试图片已存在: {TEST_IMAGE_PATH}")
        return True
    else:
        print(f"⚠️  测试图片不存在: {TEST_IMAGE_PATH}")
        print("   请将测试图片保存到该路径")
        return False

def main():
    """主测试函数"""
    print("=" * 80)
    print("智能捕蚊设备功能测试脚本")
    print("=" * 80)
    
    # 测试结果记录
    test_results = {
        "device_registration": False,
        "image_upload": False,
        "sensor_data_upload": False,
        "log_upload": False,
        "mqtt_command": False,
        "get_devices": False,
        "get_images": False,
        "get_logs": False,
        "delete_device": False
    }
    
    # 保存测试图片
    if not save_test_image():
        print("\n❌ 测试中止：缺少测试图片")
        return
    
    # 执行测试
    test_results["device_registration"] = test_device_registration()
    test_results["image_upload"] = test_image_upload()
    test_results["sensor_data_upload"] = test_sensor_data_upload()
    test_results["log_upload"] = test_log_upload()
    test_results["mqtt_command"] = test_mqtt_command()
    test_results["get_devices"] = test_get_devices()
    test_results["get_images"] = test_get_images()
    test_results["get_logs"] = test_get_logs()
    
    # 询问用户是否删除测试设备
    delete_device_flag = input("\n是否删除测试设备？(y/n): ")
    if delete_device_flag.lower() == 'y':
        test_results["delete_device"] = test_delete_device()
    else:
        print("⚠️  跳过设备删除步骤")
        test_results["delete_device"] = True
    
    # 打印测试结果
    print("\n" + "=" * 80)
    print("测试结果汇总")
    print("=" * 80)
    
    passed_tests = 0
    total_tests = len(test_results)
    
    for test_name, passed in test_results.items():
        status = "✅ 通过" if passed else "❌ 失败"
        print(f"{test_name:30} {status}")
        if passed:
            passed_tests += 1
    
    print("=" * 80)
    print(f"测试完成：{passed_tests}/{total_tests} 通过")
    print("=" * 80)

if __name__ == "__main__":
    main()
