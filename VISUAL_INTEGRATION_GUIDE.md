# 视觉识别功能集成指南

## 1. 系统架构概览

当前智能捕蚊系统的架构如下：

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│    前端界面     │◄────┤    Flask后端    │◄────┤    设备端      │
│ (HTML/CSS/JS)   │     │   (app.py)      │     │ (MQTT客户端)   │
└─────────────────┘     └─────────────────┘     └─────────────────┘
          ▲                      ▲
          │                      │
          └────────────┬─────────┘
                       │
               ┌─────────────────┐
               │    数据库       │
               │   (SQLite)      │
               └─────────────────┘
```

## 2. 与视觉工程师的合作方案

### 2.1 视觉工程师需要准备的内容

1. **视觉识别模型**：训练好的蚊子识别模型（如PyTorch、TensorFlow等格式）
2. **推理代码**：用于加载模型并进行推理的Python代码
3. **依赖项列表**：模型运行所需的Python包和版本
4. **API接口定义**：视觉识别服务的API接口规范

### 2.2 服务器环境准备

1. **创建独立的虚拟环境**：
   ```bash
   cd /home/ubuntu/Intelligent-mosquito-catching-device
   python3 -m venv vision_venv
   source vision_venv/bin/activate
   ```

2. **安装视觉依赖**：
   ```bash
   # 假设视觉工程师提供了requirements.txt
   pip install -r vision_requirements.txt
   ```

3. **创建视觉服务目录**：
   ```bash
   mkdir -p vision_service
   ```

### 2.3 视觉服务部署方案

#### 方案A：集成到现有Flask应用

将视觉识别功能作为现有Flask应用的一个模块集成：

1. **创建视觉识别模块**：
   - 文件：`vision_service/recognition.py`
   - 功能：加载模型、处理图像、返回识别结果

2. **在app.py中添加视觉识别API**：
   ```python
   # 导入视觉识别模块
   from vision_service.recognition import recognize_mosquito
   
   # 添加视觉识别API
   @app.route('/api/recognize', methods=['POST'])
   @login_required
   def recognize():
       """视觉识别API"""
       try:
           if 'image' not in request.files:
               return jsonify({'code': 400, 'msg': 'No image provided'}), 400
           
           image = request.files['image']
           device_id = request.form.get('device_id', 'unknown')
           
           # 调用视觉识别函数
           result = recognize_mosquito(image)
           
           # 保存识别结果到数据库
           # ...
           
           return jsonify({
               'code': 200,
               'msg': 'Recognition successful',
               'data': result
           })
       except Exception as e:
           return jsonify({
               'code': 500,
               'msg': f'Recognition failed: {str(e)}'
           }), 500
   ```

#### 方案B：独立的视觉服务

部署为独立的服务，通过HTTP与主应用通信：

1. **创建独立的视觉服务**：
   - 文件：`vision_service/app.py`
   - 功能：独立的Flask应用，提供视觉识别API

2. **启动独立服务**：
   ```bash
   cd vision_service
   python app.py --port 5001
   ```

3. **在主应用中调用**：
   ```python
   @app.route('/api/recognize', methods=['POST'])
   @login_required
   def recognize():
       """视觉识别API"""
       try:
           # 转发请求到视觉服务
           files = {'image': request.files['image']}
           data = {'device_id': request.form.get('device_id', 'unknown')}
           response = requests.post('http://localhost:5001/recognize', files=files, data=data)
           return response.json()
       except Exception as e:
           return jsonify({
               'code': 500,
               'msg': f'Recognition failed: {str(e)}'
           }), 500
   ```

## 3. 前端集成方案

### 3.1 前端代码修改

1. **视觉识别页面完善**：
   - 文件：`static/index.html`
   - 功能：添加图像上传和识别结果显示功能

2. **JavaScript代码修改**：
   ```javascript
   // 添加视觉识别功能
   function recognizeImage() {
       const fileInput = document.getElementById('image-upload');
       const file = fileInput.files[0];
       
       if (!file) {
           alert('请选择一张图片');
           return;
       }
       
       const formData = new FormData();
       formData.append('image', file);
       formData.append('device_id', currentDeviceId);
       
       // 显示加载状态
       document.getElementById('recognition-status').textContent = '识别中...';
       
       fetch('/api/recognize', {
           method: 'POST',
           body: formData
       })
       .then(response => response.json())
       .then(data => {
           if (data.code === 200) {
               document.getElementById('recognition-status').textContent = '识别完成';
               updateRecognitionResults(data.data);
           } else {
               document.getElementById('recognition-status').textContent = '识别失败';
               alert(data.msg);
           }
       })
       .catch(error => {
           console.error('识别失败:', error);
           document.getElementById('recognition-status').textContent = '识别失败';
           alert('识别失败，请重试');
       });
   }
   
   // 更新识别结果
   function updateRecognitionResults(results) {
       const tableBody = document.getElementById('recognition-results-table');
       tableBody.innerHTML = '';
       
       results.forEach(item => {
           const row = document.createElement('tr');
           row.innerHTML = `
               <td style="padding: 12px; border-bottom: 1px solid var(--border-color);">${item.common_name}</td>
               <td style="padding: 12px; border-bottom: 1px solid var(--border-color);">${item.scientific_name}</td>
               <td style="padding: 12px; border-bottom: 1px solid var(--border-color);">${(item.confidence * 100).toFixed(2)}%</td>
           `;
           tableBody.appendChild(row);
       });
   }
   ```

### 3.2 前端UI优化

1. **添加图像上传控件**：
   ```html
   <div style="margin-bottom: 20px;">
       <input type="file" id="image-upload" accept="image/*" style="margin-right: 10px;">
       <button class="search-btn" onclick="recognizeImage()">
           🔍 开始识别
       </button>
       <span id="recognition-status" style="margin-left: 10px; color: var(--text-secondary);"></span>
   </div>
   ```

2. **添加实时识别开关**：
   ```html
   <div style="margin-bottom: 20px;">
       <label style="margin-right: 10px;">实时识别：</label>
       <input type="checkbox" id="realtime-recognition" onchange="toggleRealtimeRecognition()">
       <span style="margin-left: 10px; font-size: 14px; color: var(--text-secondary);">当新图片上传时自动识别</span>
   </div>
   ```

## 4. 数据流转流程

### 4.1 图像上传和识别流程

```
┌───────────────┐     ┌───────────────┐     ┌───────────────┐     ┌───────────────┐
│ 前端上传图像  │ ───► │  Flask后端   │ ───► │ 视觉识别服务  │ ───► │  识别结果     │
└───────────────┘     └───────────────┘     └───────────────┘     └───────────────┘
      ▲                      │                      │                      │
      │                      ▼                      │                      │
      │             ┌───────────────┐              │                      │
      │             │ 保存图像到    │              │                      │
      │             │ 服务器        │              │                      │
      │             └───────────────┘              │                      │
      │                      │                      │                      │
      │                      ▼                      │                      │
      │             ┌───────────────┐              │                      │
      │             │ 记录到数据库  │              │                      │
      │             └───────────────┘              │                      │
      │                      │                      │                      │
      │                      └──────────────────────┘                      │
      │                                         │                        │
      │                                         ▼                        │
      │                                ┌───────────────┐                 │
      │                                │ 保存识别结果  │                 │
      │                                │ 到数据库      │                 │
      │                                └───────────────┘                 │
      │                                         │                        │
      │                                         ▼                        │
      └─────────────────────────────────────────┘                        │
                                                │                        │
                                                ▼                        │
                                       ┌───────────────┐                 │
                                       │ 推送结果到    │ ◄───────────────┘
                                       │ 前端          │
                                       └───────────────┘
```

### 4.2 实时识别流程

当设备上传新图片时，自动触发视觉识别：

```
┌───────────────┐     ┌───────────────┐     ┌───────────────┐     ┌───────────────┐
│ 设备上传图像  │ ───► │  Flask后端   │ ───► │ 保存图像并    │ ───► │ 触发视觉识别 │
└───────────────┘     └───────────────┘     └─── 记录数据库 ─┘     └───────────────┘
                                                      │                      │
                                                      ▼                      │
                                             ┌───────────────┐              │
                                             │ 视觉识别服务  │              │
                                             └───────────────┘              │
                                                      │                      │
                                                      ▼                      │
                                             ┌───────────────┐              │
                                             │ 保存识别结果  │              │
                                             │ 到数据库      │              │
                                             └───────────────┘              │
                                                      │                      │
                                                      ▼                      │
                                             ┌───────────────┐              │
                                             │ 通过WebSocket│              │
                                             │ 推送结果到前端│              │
                                             └───────────────┘              │
                                                      │                      │
                                                      ▼                      │
                                             ┌───────────────┐              │
                                             │ 前端显示识别  │              │
                                             │ 结果和图像    │              │
                                             └───────────────┘              │
```

## 5. API接口设计

### 5.1 视觉识别API

#### 请求
```http
POST /api/recognize
Content-Type: multipart/form-data

image: <二进制图像数据>
device_id: <设备ID>
```

#### 响应
```json
{
  "code": 200,
  "msg": "Recognition successful",
  "data": [
    {
      "common_name": "埃及伊蚊",
      "scientific_name": "Aedes aegypti",
      "confidence": 0.95,
      "bounding_box": {
        "x": 100,
        "y": 150,
        "width": 80,
        "height": 60
      }
    },
    {
      "common_name": "白纹伊蚊",
      "scientific_name": "Aedes albopictus",
      "confidence": 0.03,
      "bounding_box": null
    }
  ],
  "image_id": 123,
  "timestamp": "2026-01-29T14:30:00"
}
```

### 5.2 识别结果查询API

#### 请求
```http
GET /api/recognition_results?image_id=123
```

#### 响应
```json
{
  "code": 200,
  "msg": "success",
  "data": {
    "image_id": 123,
    "device_id": "test-device-123",
    "image_path": "/data/images/test-device-123_image.jpg",
    "recognition_results": [
      {
        "common_name": "埃及伊蚊",
        "scientific_name": "Aedes aegypti",
        "confidence": 0.95,
        "bounding_box": {
          "x": 100,
          "y": 150,
          "width": 80,
          "height": 60
        }
      }
    ],
    "recognition_time": "2026-01-29T14:30:05"
  }
}
```

## 6. 数据库设计

### 6.1 添加识别结果表

```sql
CREATE TABLE IF NOT EXISTS recognition_results (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    image_id INTEGER NOT NULL,
    device_id TEXT NOT NULL,
    common_name TEXT NOT NULL,
    scientific_name TEXT NOT NULL,
    confidence REAL NOT NULL,
    bounding_box TEXT,
    recognition_time TEXT DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (image_id) REFERENCES images (id)
);
```

### 6.2 图像表关联

在`images`表中添加识别状态字段：

```sql
ALTER TABLE images ADD COLUMN recognition_status TEXT DEFAULT 'pending'; -- pending, processing, completed, failed
ALTER TABLE images ADD COLUMN recognized_at TEXT;
```

## 7. 部署和测试方案

### 7.1 部署步骤

1. **部署视觉识别服务**：
   ```bash
   # 方案A：集成到现有应用
   cp -r vision_engineer_code/vision_service /home/ubuntu/Intelligent-mosquito-catching-device/
   
   # 方案B：独立服务
   cd /home/ubuntu/Intelligent-mosquito-catching-device/vision_service
   python app.py --host 0.0.0.0 --port 5001 &
   ```

2. **重启Flask应用**：
   ```bash
   sudo systemctl restart mosquito-web-server
   ```

### 7.2 测试流程

1. **功能测试**：
   - 上传测试图像进行识别
   - 检查识别结果是否正确显示
   - 测试实时识别功能

2. **性能测试**：
   - 测试识别响应时间
   - 测试并发处理能力
   - 测试系统稳定性

3. **集成测试**：
   - 测试设备端上传图像自动识别
   - 测试前端实时显示识别结果
   - 测试数据持久化和查询

## 8. 合作注意事项

1. **版本控制**：使用Git管理代码，创建专门的视觉识别分支
2. **环境隔离**：使用虚拟环境隔离依赖，避免冲突
3. **错误处理**：添加完善的错误处理和日志记录
4. **安全性**：限制API访问权限，防止恶意调用
5. **可扩展性**：设计模块化架构，便于后续功能扩展
6. **文档完善**：保持代码和API文档的同步更新

## 9. 技术支持

如果在集成过程中遇到问题，请参考以下资源：

1. **系统文档**：`TECHNICAL_DOCUMENTATION.md`
2. **API文档**：`API_DOCUMENTATION.md`（可由视觉工程师提供）
3. **联系信息**：
   - 后端开发者：[您的联系方式]
   - 视觉工程师：[视觉工程师联系方式]

---

**注**：本指南可根据实际情况进行调整和优化。