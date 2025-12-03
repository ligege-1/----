# OODaiP 聊天助手

这是一个基于 Flask 和 Socket.IO 的实时聊天室应用，集成了 OpenAI 驱动的 AI 助手（@成小理），专为成都理工大学计算机与物联网专业学生设计，提供内卷程度测试和校园生活互动功能。

## ✨ 核心功能

1. **实时聊天室**
   - 多房间支持（默认群聊及自定义房间）
   - 实时消息推送（WebSocket）
   - 在线用户列表与人数统计
   - 简单的表情包与快捷指令支持

2. **AI 助手 (@成小理)**
   - **触发方式**: 在聊天框输入 `@成小理 [你的问题]`
   - **人设**: 成都理工大学计算机专业助手，风格接地气，熟悉校园生活（图书馆、实验室、李哥、王祥等梗）。
   - **功能**:
     - **内卷程度测试**: 根据姓名、专业、班级或学号（严格校验格式）生成趣味内卷评级（A-F级）。
     - **反内卷/内卷咨询**: 提供备考、竞赛、实习建议。
     - **校园文学创作**: 生成包含特定人物（李哥、王祥、涛李）的内卷故事。
   - **技术**: Server-Sent Events (SSE) 实现打字机流式回复。

3. **用户系统**
   - 简单的昵称登录与查重。
   - 房间切换与加入/离开通知。

## 🛠️ 技术栈

- **后端**: Python 3.11+, Flask, Flask-SocketIO, OpenAI (Python SDK)
- **前端**: HTML5, jQuery, Tailwind CSS (CDN), Socket.IO Client
- **运行环境**: Windows (开发环境), 支持跨平台部署

## 🚀 快速启动

### 1. 环境准备

确保已安装 Python 3.11 或更高版本。

```bash
# 克隆项目或下载源码
git clone <repository_url>
cd 聊天助手

# 创建虚拟环境 (可选但推荐)
python -m venv venv
# Windows 激活
.\venv\Scripts\activate
# Linux/Mac 激活
# source venv/bin/activate
```

### 2. 安装依赖

```bash
pip install -r requirements.txt
```

### 3. 配置文件

项目依赖 `config.json` 配置服务器列表（已包含默认配置）。如果需要修改 OpenAI API Key，请编辑 `app.py` 中的配置区域：

```python
# app.py
API_KEY = "your_api_key_here"
MODEL_NAME = "Qwen/Qwen2.5-7B-Instruct"
API_URL = "https://api.siliconflow.cn/v1/"
```

### 4. 启动服务

```bash
python app.py
```

启动后访问：`http://127.0.0.1:5001`

## 📂 项目结构

```
聊天助手/
├── app.py              # 主程序入口，包含 Flask 路由、SocketIO 事件、AI 接口逻辑
├── config.json         # 服务器与房间配置文件
├── requirements.txt    # Python 依赖列表
├── templates/          # HTML 模板
│   ├── login.html      # 登录页面
│   └── chat.html       # 聊天室主页面（含前端逻辑）
└── README.md           # 项目说明文档
```

## 🔧 关键配置说明

### AI 提示词 (System Prompt)
位于 `app.py` 的 `AI_SYSTEM_PROMPT` 变量中。修改此变量可调整 AI 的人设、回复风格及学号校验规则。

**当前学号规则**:
- 总长度 12 位
- 前 4 位：入学年份（如 2023）
- 第 5-8 位：专业代码（1912=计算机大类，1906=物联网）
- 后 4 位：班级 + 位次（如 0612 = 6班12号）

### 前端 AI 逻辑
位于 `templates/chat.html`。
- **触发**: 监听 `socket.on('message')`，检测到自己发送的消息以 `@成小理` 开头时触发。
- **流式响应**: 使用 `fetch` 请求 `/api/ai_chat`，通过 `ReadableStream` 解析 SSE 数据流。

## 📝 开发指南与后续计划

### 1. 历史记录持久化
- **现状**: 消息仅在内存中转发，重启或刷新后丢失。
- **计划**: 引入 SQLite 或 Redis 存储最近 50 条消息，并在用户加入房间时通过 `load_history` 事件推送。

### 2. 用户身份认证
- **现状**: 仅基于昵称的简单会话，无密码保护。
- **计划**: 增加注册/登录功能，或通过学号验证绑定真实身份。

### 3. 完善 AI 交互
- **现状**: 仅支持文本问答。
- **计划**: 增加上下文记忆（目前是单轮对话），让 AI 能记住之前的对话内容。

### 4. 界面优化
- **现状**: 基础 Tailwind 样式。
- **计划**: 增加移动端适配优化，支持图片/文件发送。

## 🤝 贡献
欢迎提交 Issue 或 Pull Request 改进代码！特别欢迎补充成理校园梗和内卷段子。
