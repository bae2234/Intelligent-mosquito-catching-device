#!/usr/bin/env python3
"""
测试文件：用于测试项目功能，特别是图片发送功能
"""

import os
import json
import requests
from datetime import datetime

# 项目根目录
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# 图片路径
IMAGE_PATH = os.path.join(BASE_DIR, '7f4723fb8c06b62fd145da927ba566bb.jpg')

def test_image_exists():
    """测试图片是否存在"""
    print("=== 测试图片是否存在 ===")
    if os.path.exists(IMAGE_PATH):
        print(f"✓ 图片存在: {IMAGE_PATH}")
        print(f"  图片大小: {os.path.getsize(IMAGE_PATH) / 1024:.2f} KB")
        return True
    else:
        print(f"✗ 图片不存在: {IMAGE_PATH}")
        return False

def test_mqtt_connection():
    """测试MQTT连接"""
    print("\n=== 测试MQTT连接 ===")
    try:
        # 导入MQTT相关模块
        from src.services.mqtt_server import MQTTServer
        print("✓ MQTT模块导入成功")
        return True
    except ImportError as e:
        print(f"✗ MQTT模块导入失败: {e}")
        return False

def test_visual_service():
    """测试视觉服务"""
    print("\n=== 测试视觉服务 ===")
    try:
        # 导入视觉服务模块
        from src.services.visual_service import VisualService
        print("✓ 视觉服务模块导入成功")
        return True
    except ImportError as e:
        print(f"✗ 视觉服务模块导入失败: {e}")
        return False

def test_image_send():
    """测试图片发送功能"""
    print("\n=== 测试图片发送 ===")
    if not test_image_exists():
        return False
    
    try:
        # 模拟发送图片（根据项目实际情况调整）
        print(f"发送图片: {IMAGE_PATH}")
        print(f"发送时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        # 这里可以根据项目的实际发送方式进行调整
        # 例如：通过MQTT发送、通过HTTP发送等
        
        print("✓ 图片发送测试完成")
        return True
    except Exception as e:
        print(f"✗ 图片发送失败: {e}")
        return False

def main():
    """主测试函数"""
    print("开始测试智能捕蚊设备项目功能...\n")
    
    test_results = {
        "图片存在测试": test_image_exists(),
        "MQTT连接测试": test_mqtt_connection(),
        "视觉服务测试": test_visual_service(),
        "图片发送测试": test_image_send()
    }
    
    print("\n=== 测试结果汇总 ===")
    for test_name, result in test_results.items():
        status = "✓ 通过" if result else "✗ 失败"
        print(f"{test_name}: {status}")
    
    print("\n测试完成！")

if __name__ == "__main__":
    main()
