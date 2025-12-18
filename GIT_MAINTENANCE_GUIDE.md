# Git代码维护指南

## 1. 仓库初始化与配置

### 1.1 本地仓库初始化
```bash
# 创建新目录并初始化Git仓库
git init intelligent-mosquito-catching-device
cd intelligent-mosquito-catching-device

# 配置Git用户信息
git config --global user.name "Your Name"
git config --global user.email "your.email@example.com"

# 关联远程仓库
git remote add origin https://github.com/bae2234/Intelligent-mosquito-catching-device.git
```

### 1.2 克隆现有仓库
```bash
git clone https://github.com/bae2234/Intelligent-mosquito-catching-device.git
cd Intelligent-mosquito-catching-device
```

## 2. 代码提交流程

### 2.1 查看文件状态
```bash
# 查看当前仓库状态
git status

# 查看文件差异
git diff
# 查看特定文件差异
git diff <file_path>
```

### 2.2 添加与提交
```bash
# 添加单个文件到暂存区
git add <file_path>

# 添加所有修改到暂存区
git add -A

# 提交代码，使用有意义的提交信息
git commit -m "[功能] 实现了图片删除功能，删除图片时同时删除关联设备"
```

### 2.3 推送代码到远程仓库
```bash
# 推送到默认分支（main）
git push

# 推送到指定分支
git push origin <branch_name>

# 强制推送（用于重写历史，谨慎使用）
git push --force origin <branch_name>
```

## 3. 分支管理

### 3.1 查看分支
```bash
# 查看本地分支
git branch

# 查看所有分支（包括远程）
git branch -a
```

### 3.2 创建与切换分支
```bash
# 创建新分支
git branch <branch_name>

# 创建并切换到新分支
git checkout -b <branch_name>

# 切换到现有分支
git checkout <branch_name>
```

### 3.3 合并分支
```bash
# 切换到目标分支
git checkout main

# 合并源分支到当前分支
git merge <source_branch>
```

### 3.4 删除分支
```bash
# 删除本地分支
git branch -d <branch_name>

# 强制删除本地分支
git branch -D <branch_name>

# 删除远程分支
git push origin --delete <branch_name>
```

## 4. 解决冲突

### 4.1 查看冲突文件
```bash
git status
```

### 4.2 手动解决冲突
- 打开冲突文件，查找冲突标记 `<<<<<<<`、`=======`、`>>>>>>>`
- 手动编辑文件，保留需要的代码
- 删除冲突标记

### 4.3 提交解决后的代码
```bash
git add <conflict_file>
git commit -m "[修复] 解决合并冲突"
```

## 5. 代码回滚

### 5.1 回滚到上一次提交
```bash
# 保留修改，回滚到上一次提交
git reset HEAD~1

# 丢弃所有修改，强制回滚
git reset --hard HEAD~1
```

### 5.2 回滚到指定提交
```bash
# 查看提交历史
git log --oneline

# 回滚到指定提交（保留修改）
git reset <commit_hash>

# 回滚到指定提交（丢弃所有修改）
git reset --hard <commit_hash>
```

## 6. 远程仓库操作

### 6.1 拉取最新代码
```bash
# 拉取远程分支并合并到当前分支
git pull

# 拉取远程分支但不合并
git fetch
```

### 6.2 查看远程仓库信息
```bash
git remote -v
```

## 7. 代码维护最佳实践

### 7.1 提交规范
- 提交信息要清晰、简洁，说明本次提交的目的
- 推荐格式：`[类型] 描述信息`
  - 类型：功能、修复、优化、文档、测试等
  - 示例：`[功能] 实现了设备列表分页功能`

### 7.2 分支策略
- **main分支**：稳定版本，用于生产环境
- **develop分支**：开发分支，整合所有功能开发
- **feature分支**：特性分支，用于开发新功能
  - 命名规则：`feature/功能名称`
  - 示例：`feature/image_upload`
- **hotfix分支**：修复分支，用于修复生产环境bug
  - 命名规则：`hotfix/bug描述`
  - 示例：`hotfix/login_error`

### 7.3 代码质量
- 定期运行代码检查工具
- 编写测试用例
- 保持代码风格一致性

## 8. 解决常见问题

### 8.1 无法推送代码
- 检查网络连接
- 检查Git远程配置
- 检查是否有未提交的本地修改
- 检查分支权限

### 8.2 合并冲突
- 仔细阅读冲突信息
- 与团队成员沟通确认解决方案
- 保留有意义的代码

### 8.3 忘记提交某些文件
```bash
# 添加遗漏的文件
git add <file_path>
# 追加到上次提交
git commit --amend --no-edit
```

## 9. 其他常用命令

```bash
# 查看提交历史
git log
# 查看简洁的提交历史
git log --oneline
# 查看分支合并图
git log --graph --oneline --decorate --all

# 查看文件的修改历史
git blame <file_path>

# 临时保存修改
git stash
# 恢复临时保存的修改
git stash pop
# 查看所有临时保存
git stash list
```

## 10. 本次代码提交说明

### 10.1 已完成的工作
- ✅ 创建了新的Git分支 `new_initial_commit`
- ✅ 完成了代码的初始提交
- ✅ 关联了远程仓库
- ✅ 准备将代码推送到GitHub

### 10.2 代码结构
```
Intelligent-mosquito-catching-device/
├── app.py                # 主应用程序
├── mqtt_receiver.py      # MQTT消息接收处理
├── mqtt_server.py        # MQTT服务器实现
├── static/
│   └── index.html        # 前端页面
├── .gitignore            # Git忽略文件配置
├── TECHNICAL_DOCUMENTATION.md  # 技术文档
├── GIT_MAINTENANCE_GUIDE.md    # Git维护指南
└── test_db.py            # 数据库测试脚本
```

### 10.3 核心功能
- 设备管理：添加、删除、状态管理
- 图片管理：上传、查看、删除（删除图片时同时删除关联设备）
- 用户认证：管理员和设备登录
- 实时数据推送：WebSocket通信
- MQTT通信：设备数据接收和命令发送

---

**创建时间**: 2025-12-18
**版本**: 1.0
