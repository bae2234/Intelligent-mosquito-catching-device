from flask import Flask, request, jsonify
from ultralytics import YOLO
import requests
import time
import threading

app = Flask(__name__)

# --- 标签映射字典 ---#
# 将模型输出的标签映射到对应的中文
label_mapping = {
    "BWYC": "白纹伊蚊雌",
    "BWYX": "白纹伊蚊雄",
    "DSKC": "淡色库蚊雌",
    "DSKX": "淡色库蚊雄",
    "PCMC": "膨橱毛纹雌",
    "PCMX": "膨橱毛纹雄",
    "SRAC": "骚扰阿纹雌",
    "SRAX": "骚扰阿蚊雄",
    "YWC": "小摇蚊雌",
    "YWX": "小摇蚊雄",
    "ZJKC": "致卷库蚊雌",
    "ZJKX": "致卷库蚊雄"
}

# --- 1. 加载你训练好的模型 ---
# 建议在服务启动时就加载模型，不要放在接口函数里，否则每次请求都会卡顿
print("正在加载模型...")
model = YOLO('/home/ubuntu/Intelligent-mosquito-catching-device/models/best.pt')  # 模型文件路径
print("模型加载完成！")

def run_inference_and_callback(image_path, image_id, callback_url):
    """
    后台执行推理任务，并在完成后通过 Webhook 回调主服务器
    """
    try:
        start_time = time.time()
        
        # --- 2. 使用模型进行预测 ---
        # conf=0.5 表示置信度大于 0.5 才算识别到
        # save=False 因为我们只需要数据，不需要保存画好框的图
        results = model(image_path, conf=0.3, save=True) 
        
        # --- 3. 格式化结果 ---
        # YOLOv8 可能返回多张图的结果（如果传入的是列表），这里我们只处理一张
        result = results[0]
        
        objects_list = []
        
        # 遍历识别到的每一个物体
        for box in result.boxes:
            # 获取类别名称 (例如 'mosquito')
            class_id = int(box.cls[0])
            class_name = model.names[class_id]
            
            # 获取置信度
            confidence = float(box.conf[0])
            
            # 获取坐标 (YOLO默认返回 x1, y1, x2, y2)
            x1, y1, x2, y2 = box.xyxy[0].tolist()
            
            # 转换为前端需要的格式 [x, y, width, height] (左上角坐标 + 宽高)
            x = int(x1)
            y = int(y1)
            w = int(x2 - x1)
            h = int(y2 - y1)
            
            # --- 添加蚊子种类和雌雄识别 ---
            # 使用标签映射字典将英文标签转化为中文
            chinese_label = label_mapping.get(class_name, class_name)  # 如果没有映射，使用原标签
            
            # 从中文标签中提取种类和雌雄信息
            # 初始化种类和雌雄信息
            mosquito_species = "普通蚊子"  # 默认值
            mosquito_gender = "未知"      # 默认值
            
            # 提取种类信息（去掉最后一个字，因为最后一个字通常是性别）
            if len(chinese_label) > 1:
                mosquito_species = chinese_label[:-1]  # 去掉最后一个字
                # 提取雌雄信息（最后一个字）
                last_char = chinese_label[-1]
                if last_char == "雌":
                    mosquito_gender = "雌性"
                elif last_char == "雄":
                    mosquito_gender = "雄性"
            
            obj_data = {
                "class": class_name,  # 原始标签
                "chinese_class": chinese_label,  # 中文标签
                "confidence": round(confidence, 2),
                "bbox": [x, y, w, h],
                "type": "adult",  # 如果你的模型没有分公母，这里可以是固定值或后续逻辑判断
                "species": mosquito_species,  # 蚊子种类
                "gender": mosquito_gender     # 蚊子雌雄
            }
            objects_list.append(obj_data)

        # 构造最终 JSON
        analyze_time = int((time.time() - start_time) * 1000) # 毫秒
        
        # 统计不同种类和性别的蚊子数量
        species_count = {}
        gender_count = {}
        
        for obj in objects_list:
            # 统计种类
            species = obj.get("species", "普通蚊子")
            species_count[species] = species_count.get(species, 0) + 1
            
            # 统计性别
            gender = obj.get("gender", "未知")
            gender_count[gender] = gender_count.get(gender, 0) + 1
        
        payload = {
            "image_id": image_id,
            "status": "success",
            "result": {
                "objects": objects_list,
                "total_count": len(objects_list),
                "species_count": species_count,  # 不同种类的数量
                "gender_count": gender_count,    # 不同性别的数量
                "analyze_time": analyze_time
            }
        }

        # --- 4. 回调主服务器 (Callback) ---
        print(f"识别完成，正在回调: {callback_url}")
        requests.post(callback_url, json=payload)

    except Exception as e:
        print(f"识别出错: {e}")
        # 出错也可以回调通知主服务
        requests.post(callback_url, json={
            "image_id": image_id, 
            "status": "failed", 
            "error": str(e)
        })

@app.route('/api/analyze', methods=['POST'])
def analyze():
    """
    接收主服务的调用请求
    """
    data = request.json
    image_id = data.get('image_id')
    image_path = data.get('image_path')     # 图片在磁盘上的路径
    callback_url = data.get('callback_url') # 处理完后通知谁

    if not image_path or not callback_url:
        return jsonify({"error": "Missing parameters"}), 400

    # 使用线程异步处理，让接口立即返回，不阻塞主服务
    thread = threading.Thread(
        target=run_inference_and_callback, 
        args=(image_path, image_id, callback_url)
    )
    thread.start()

    return jsonify({"message": "Task received, processing started..."})

if __name__ == '__main__':
    # 视觉服务运行在 8000 端口，避免和主 Flask (通常 5000) 冲突
    app.run(port=8000, debug=True)