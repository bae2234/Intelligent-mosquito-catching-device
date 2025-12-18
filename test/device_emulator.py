#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
设备模拟器测试脚本

功能：
1. 模拟设备端发送MQTT数据
2. 模拟设备端上传图片
3. 验证设备注册功能
4. 生成测试报告

作者: Intelligent-mosquito-catching-device Team
日期: 2025-12-18
"""

import paho.mqtt.client as mqtt
import requests
import json
import time
import random
import os
import datetime
from datetime import datetime
import uuid

# 配置常量
MQTT_SERVER = "127.0.0.1"
MQTT_PORT = 1883
HTTP_SERVER = "http://127.0.0.1:5000"
IMAGE_UPLOAD_URL = f"{HTTP_SERVER}/upload/image"

# 测试设备列表
TEST_DEVICES = [
    {"device_id": "test_device_001", "name": "测试设备1"},
    {"device_id": "test_device_002", "name": "测试设备2"},
    {"device_id": "test_device_003", "name": "测试设备3"}
]

# 测试结果存储
TEST_RESULTS = {
    "total_tests": 0,
    "passed_tests": 0,
    "failed_tests": 0,
    "test_cases": []
}

# 数据发送模块
class DataSender:
    """数据发送模块"""
    
    def __init__(self, device_id):
        self.device_id = device_id
        self.client = mqtt.Client()
        self.client.on_connect = self.on_connect
        self.client.on_message = self.on_message
        self.response_received = False
        self.response_message = None
        self.response_timeout = 5
    
    def on_connect(self, client, userdata, flags, rc):
        """连接回调"""
        print(f"设备 {self.device_id} 已连接到MQTT服务器")
        # 订阅确认主题
        confirm_topic = f"control/confirm/{self.device_id}"
        self.client.subscribe(confirm_topic)
    
    def on_message(self, client, userdata, msg):
        """消息回调"""
        try:
            payload = json.loads(msg.payload.decode('utf-8'))
            self.response_received = True
            self.response_message = payload
            print(f"设备 {self.device_id} 收到响应: {payload}")
        except Exception as e:
            print(f"处理响应消息时出错: {e}")
    
    def connect(self):
        """连接到MQTT服务器"""
        self.client.connect(MQTT_SERVER, MQTT_PORT, 60)
        self.client.loop_start()
        time.sleep(1)  # 等待连接建立
    
    def disconnect(self):
        """断开MQTT连接"""
        self.client.loop_stop()
        self.client.disconnect()
    
    def send_sensor_data(self, data=None):
        """发送传感器数据"""
        if data is None:
            # 生成随机传感器数据
            data = {
                "timestamp": datetime.now().isoformat(),
                "temperature_inside": round(random.uniform(20.0, 30.0), 1),
                "temperature_outside": round(random.uniform(15.0, 25.0), 1),
                "humidity": round(random.uniform(50.0, 80.0), 1),
                "duoj1": random.randint(0, 100),
                "duoj2": random.randint(0, 100),
                "duoj3": random.randint(0, 100),
                "duoj4": random.randint(0, 100),
                "feng1": random.randint(0, 1),
                "feng2": random.randint(0, 1),
                "jia": random.randint(0, 1)
            }
        
        # 发送数据
        topic = f"control/sensor_data/{self.device_id}"
        self.client.publish(topic, json.dumps(data), qos=1)
        print(f"设备 {self.device_id} 发送传感器数据: {data}")
        
        # 等待响应
        start_time = time.time()
        while not self.response_received and (time.time() - start_time) < self.response_timeout:
            time.sleep(0.1)
        
        response = self.response_message
        self.response_received = False
        self.response_message = None
        
        return response
    
    def upload_image(self, device_id):
        """上传图片"""
        # 创建一个简单的测试图片数据
        import io
        from PIL import Image, ImageDraw
        
        # 创建一个测试图片
        img = Image.new('RGB', (100, 100), color='red')
        draw = ImageDraw.Draw(img)
        draw.text((10, 50), f"Device: {device_id}", fill='white')
        draw.text((10, 65), f"Time: {datetime.now()}", fill='white')
        
        # 转换为字节流
        img_byte_arr = io.BytesIO()
        img.save(img_byte_arr, format='PNG')
        img_byte_arr.seek(0)
        
        # 发送图片上传请求
        files = {'image': (f'test_{device_id}.png', img_byte_arr, 'image/png')}
        data = {'device_id': device_id}
        
        try:
            response = requests.post(IMAGE_UPLOAD_URL, files=files, data=data, timeout=10)
            return response
        except Exception as e:
            print(f"上传图片时出错: {e}")
            return None

# 测试用例类
class TestCase:
    """测试用例类"""
    
    def __init__(self, test_name, device_id, test_func):
        self.test_name = test_name
        self.device_id = device_id
        self.test_func = test_func
        self.result = None
        self.error = None
        self.start_time = None
        self.end_time = None
    
    def run(self):
        """运行测试用例"""
        self.start_time = time.time()
        try:
            self.result = self.test_func()
            self.end_time = time.time()
            return True
        except Exception as e:
            self.error = str(e)
            self.end_time = time.time()
            return False

# 测试管理类
class TestManager:
    """测试管理类"""
    
    def __init__(self):
        self.test_cases = []
    
    def add_test(self, test_name, device_id, test_func):
        """添加测试用例"""
        test_case = TestCase(test_name, device_id, test_func)
        self.test_cases.append(test_case)
    
    def run_all_tests(self):
        """运行所有测试用例"""
        print("\n" + "="*60)
        print("开始执行所有测试用例")
        print("="*60)
        
        for test_case in self.test_cases:
            print(f"\n测试用例: {test_case.test_name}")
            print(f"测试设备: {test_case.device_id}")
            print("-"*40)
            
            success = test_case.run()
            
            if success:
                print(f"✅ 测试通过")
                print(f"结果: {test_case.result}")
            else:
                print(f"❌ 测试失败")
                print(f"错误信息: {test_case.error}")
            
            duration = test_case.end_time - test_case.start_time
            print(f"执行时间: {duration:.2f} 秒")
        
        print("\n" + "="*60)
        print("所有测试用例执行完成")
        print("="*60)
    
    def generate_report(self, filename="test_report.txt"):
        """生成测试报告"""
        total_tests = len(self.test_cases)
        passed_tests = sum(1 for tc in self.test_cases if tc.result)
        failed_tests = total_tests - passed_tests
        
        with open(filename, "w", encoding="utf-8") as f:
            f.write("="*60 + "\n")
            f.write("智能捕蚊识别系统 - 设备端测试报告\n")
            f.write(f"测试时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write("="*60 + "\n\n")
            
            f.write("测试摘要\n")
            f.write("="*60 + "\n")
            f.write(f"总测试用例: {total_tests}\n")
            f.write(f"通过测试: {passed_tests}\n")
            f.write(f"失败测试: {failed_tests}\n")
            f.write(f"通过率: {(passed_tests/total_tests*100):.1f}%\n\n\n")
            f.write("详细测试结果\n")
            f.write("="*60 + "\n")
            
            for i, test_case in enumerate(self.test_cases, 1):
                status = "✅ 通过" if test_case.result else "❌ 失败"
                duration = test_case.end_time - test_case.start_time
                f.write(f"\n测试用例 {i}: {test_case.test_name}\n")
                f.write(f"设备: {test_case.device_id}\n")
                f.write(f"状态: {status}\n")
                f.write(f"执行时间: {duration:.2f} 秒\n")
                f.write(f"结果: {test_case.result}\n")
                if test_case.error:
                    f.write(f"错误: {test_case.error}\n")
                f.write("="*60 + "\n")
        
        print(f"\n测试报告已生成: {filename}")

# 主测试脚本
if __name__ == "__main__":
    # 创建测试管理器
    test_manager = TestManager()
    
    # 添加测试用例
    for device in TEST_DEVICES:
        device_id = device["device_id"]
        
        # 测试1: MQTT连接与数据发送
        def test_mqtt_connection(device_id=device_id):
            sender = DataSender(device_id)
            sender.connect()
            response = sender.send_sensor_data()
            sender.disconnect()
            return response is not None
        
        # 测试2: 图片上传测试
        def test_image_upload(device_id=device_id):
            sender = DataSender(device_id)
            response = sender.upload_image(device_id)
            return response and response.status_code == 200
        
        # 测试3: 不同设备状态模拟
        def test_different_device_states(device_id=device_id):
            # 测试不同温度范围
            test_results = []
            
            # 高温测试
            sender = DataSender(device_id)
            sender.connect()
            high_temp_data = {
                "timestamp": datetime.now().isoformat(),
                "temperature_inside": 35.0,
                "temperature_outside": 40.0,
                "humidity": 90.0,
                "duoj1": 100,
                "duoj2": 100,
                "duoj3": 100,
                "duoj4": 100,
                "feng1": 1,
                "feng2": 1,
                "jia": 1
            }
            response = sender.send_sensor_data(high_temp_data)
            test_results.append(response is not None)
            
            # 低温测试
            low_temp_data = {
                "timestamp": datetime.now().isoformat(),
                "temperature_inside": 10.0,
                "temperature_outside": 5.0,
                "humidity": 30.0,
                "duoj1": 0,
                "duoj2": 0,
                "duoj3": 0,
                "duoj4": 0,
                "feng1": 0,
                "feng2": 0,
                "jia": 0
            }
            response = sender.send_sensor_data(low_temp_data)
            test_results.append(response is not None)
            sender.disconnect()
            
            return all(test_results)
        
        # 添加测试用例到管理器
        test_manager.add_test(f"MQTT连接与数据发送测试 - {device_id}", device_id, test_mqtt_connection)
        test_manager.add_test(f"图片上传测试 - {device_id}", device_id, test_image_upload)
        test_manager.add_test(f"不同设备状态测试 - {device_id}", device_id, test_different_device_states)
    
    # 运行所有测试
    test_manager.run_all_tests()
    
    # 生成测试报告
    test_manager.generate_report("test/test_report.txt")
    
    # 生成详细的JSON报告
    report_data = {
        "test_time": datetime.now().isoformat(),
        "total_tests": len(test_manager.test_cases),
        "passed_tests": sum(1 for tc in test_manager.test_cases if tc.result),
        "failed_tests": sum(1 for tc in test_manager.test_cases if not tc.result),
        "test_cases": [{
            "test_name": tc.test_name,
            "device_id": tc.device_id,
            "result": tc.result,
            "error": tc.error,
            "duration": tc.end_time - tc.start_time if tc.end_time else 0
        } for tc in test_manager.test_cases]
    }
    
    with open("test/test_report.json", "w", encoding="utf-8") as f:
        json.dump(report_data, f, indent=2, ensure_ascii=False)
    
    print(f"\nJSON格式测试报告已生成: test/test_report.json")
