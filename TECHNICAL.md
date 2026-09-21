# 技术实现文档

## 一、项目架构概览

本项目是一个基于 Flask 的轻量级 Web 应用，采用 **分层架构** 设计，主要分为以下几个层次：

```
┌─────────────────────────────────────────────────────┐
│                    前端层 (Frontend)                 │
│              src/templates/index.html               │
│              HTML + CSS + JavaScript                 │
└─────────────────────────────┬───────────────────────┘
                              │ HTTP POST /api/generate
┌─────────────────────────────▼───────────────────────┐
│                    路由层 (Routes)                   │
│                   src/app.py                        │
│              Flask 路由 + 请求处理                    │
└─────────────────────────────┬───────────────────────┘
                              │ 调用 Service 方法
┌─────────────────────────────▼───────────────────────┐
│                    服务层 (Service)                  │
│           src/services/testcase_service.py          │
│          业务逻辑 + 数据格式化                        │
└─────────────────────────────┬───────────────────────┘
                              │ 调用 LLM API
┌─────────────────────────────▼───────────────────────┐
│                   客户端层 (Client)                  │
│                 src/llm_client.py                   │
│           OpenAI SDK + 大模型 API 调用                │
└─────────────────────────────┬───────────────────────┘
                              │ HTTP 请求
┌─────────────────────────────▼───────────────────────┐
│                    外部服务 (External)               │
│              智谱AI GLM-4-Flash API                  │
└─────────────────────────────────────────────────────┘
```

---

## 二、文件详解

### 2.1 `src/app.py` — Flask 应用入口

**职责**: 定义路由、处理 HTTP 请求、协调各层调用

**核心代码解析**:

```python
from flask import Flask, render_template, request, jsonify
from .services.testcase_service import TestCaseService

app = Flask(__name__)
app.config['JSON_AS_ASCII'] = False

service = TestCaseService()
```

- `Flask(__name__)`: 创建 Flask 应用实例，`__name__` 用于确定应用根目录
- `app.config['JSON_AS_ASCII'] = False`: 允许 JSON 响应包含中文（否则中文会被转义为 Unicode 编码）
- `TestCaseService()`: 实例化服务层对象，作为全局单例使用

**路由定义**:

```python
@app.route('/')
def index():
    return render_template('index.html')
```

- `@app.route('/')`: 装饰器，将根路径 `/` 映射到 `index` 函数
- `render_template('index.html')`: 渲染 `src/templates/index.html` 模板文件

```python
@app.route('/api/generate', methods=['POST'])
def generate_test_cases():
    data = request.get_json()
    content = data.get('content', '')
    content_type = data.get('type', 'prd')
    
    if content_type == 'user_story':
        result = service.generate_from_user_story(content)
    else:
        result = service.generate_from_prd(content)
    
    return jsonify(result)
```

- `methods=['POST']`: 仅接受 POST 请求
- `request.get_json()`: 解析请求体中的 JSON 数据
- `jsonify(result)`: 将 Python 字典转换为 JSON 响应

---

### 2.2 `src/services/testcase_service.py` — 服务层

**职责**: 封装业务逻辑、数据校验、结果格式化

**核心设计**:

```python
class TestCaseService:
    def __init__(self):
        self.llm_client = LLMClient()
```

- 在 `__init__` 中实例化 `LLMClient`，建立与大模型客户端的连接

**两个核心方法**:

```python
def generate_from_prd(self, prd_content):
    if not prd_content or not prd_content.strip():
        return {"error": "PRD内容不能为空"}
    
    result = self.llm_client.generate_test_cases(prd_content)
    
    if result.startswith("API调用失败"):
        return {"error": result}
    
    return {"success": True, "content": result}
```

- **数据校验**: 检查输入是否为空
- **调用 LLM**: 委托给 `LLMClient.generate_test_cases()`
- **结果处理**: 根据返回值判断成功/失败，统一封装为标准格式

```python
def generate_from_user_story(self, user_story):
    if not user_story or not user_story.strip():
        return {"error": "用户故事内容不能为空"}
    
    prd_content = f"""用户故事：{user_story}

请根据以上用户故事，分析需求并生成测试用例。"""
    
    return self.generate_from_prd(prd_content)
```

- **格式转换**: 将用户故事格式转换为 PRD 格式，复用 `generate_from_prd` 方法
- **DRY 原则**: Don't Repeat Yourself，避免代码重复

---

### 2.3 `src/llm_client.py` — 大模型客户端（核心）

**职责**: 封装大模型 API 调用、配置管理、Prompt 工程

这是本项目**最重要的文件**，所有与大模型相关的逻辑都在这里实现。

#### 2.3.1 配置加载

```python
import os
from dotenv import load_dotenv
from openai import OpenAI
import httpx

load_dotenv()

class LLMClient:
    def __init__(self):
        self.api_key = os.getenv("LLM_API_KEY")
        self.base_url = os.getenv("LLM_BASE_URL", "https://open.bigmodel.cn/api/paas/v4/")
        self.model = os.getenv("LLM_MODEL", "glm-4-flash")
```

- `load_dotenv()`: 加载 `.env` 文件中的环境变量
- `os.getenv(key, default)`: 读取环境变量，支持默认值

**环境变量说明**:

| 变量名 | 作用 | 默认值 |
|--------|------|--------|
| `LLM_API_KEY` | API 密钥（必须配置） | 无 |
| `LLM_BASE_URL` | API 服务地址 | `https://open.bigmodel.cn/api/paas/v4/` |
| `LLM_MODEL` | 使用的模型名称 | `glm-4-flash` |

#### 2.3.2 HTTP 客户端配置

```python
http_client = httpx.Client(
    timeout=httpx.Timeout(60.0, connect=10.0),
    follow_redirects=True
)

self.client = OpenAI(
    api_key=self.api_key,
    base_url=self.base_url,
    http_client=http_client
)
```

- **httpx.Client**: 自定义 HTTP 客户端，设置超时时间
  - `timeout=60.0`: 总超时 60 秒（大模型响应可能较慢）
  - `connect=10.0`: 连接超时 10 秒
- **OpenAI 客户端**: 使用官方 SDK，但通过 `base_url` 指向智谱AI的服务器

#### 2.3.3 Prompt 工程

```python
system_prompt = """你是一个专业的软件测试工程师，擅长根据产品需求文档（PRD）和用户故事（User Story）生成结构化的测试用例。

请按照以下格式输出测试用例：
```
## 测试用例列表

### TC-001: 用例标题
**前置条件**: [描述测试前需要满足的条件]
**测试步骤**:
1. [步骤1描述]
2. [步骤2描述]
**预期结果**: [描述预期的输出或行为]
```

请确保：
1. 每个测试用例包含：用例编号、用例标题、前置条件、测试步骤、预期结果
2. 测试用例覆盖正常场景和异常场景
3. 步骤清晰、可执行
4. 预期结果明确、可验证
"""
```

- **System Prompt**: 定义角色和输出格式，引导模型按照指定格式输出
- **格式约束**: 使用 Markdown 格式，便于前端展示

```python
user_prompt = f"""请根据以下产品需求/用户故事生成结构化的测试用例：

---
{prd_content}
---

请输出详细的测试用例，覆盖各种场景。"""
```

- **User Prompt**: 包含用户输入的内容，使用分隔符 `---` 明确区分

#### 2.3.4 API 调用（核心代码）

```python
response = self.client.chat.completions.create(
    model=self.model,
    messages=[
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt}
    ],
    temperature=0.3,
    max_tokens=2000
)

content = response.choices[0].message.content
return content
```

**参数详解**:

| 参数 | 作用 | 说明 |
|------|------|------|
| `model` | 指定模型 | `glm-4-flash` 是智谱AI的免费模型 |
| `messages` | 对话历史 | 包含 system 和 user 角色 |
| `temperature` | 温度系数 | 0-2 之间，越低输出越稳定确定，越高越随机 |
| `max_tokens` | 最大输出长度 | 控制响应内容的长度上限 |

**响应解析**:
- `response.choices[0]`: 获取第一个（也是唯一一个）选择
- `.message.content`: 获取消息内容

---

### 2.4 `src/templates/index.html` — 前端页面

**职责**: 用户交互界面、API 请求、结果展示

#### 2.4.1 HTML 结构

```html
<div class="tabs">
    <button class="tab active" onclick="switchTab('prd')">产品需求 (PRD)</button>
    <button class="tab" onclick="switchTab('user_story')">用户故事 (User Story)</button>
</div>
<textarea id="inputContent"></textarea>
<button class="btn" onclick="generateTestCases()">生成测试用例</button>
<div class="result" id="result">
    <div class="result-content" id="resultContent"></div>
</div>
```

- **Tabs**: 切换输入类型（PRD / User Story）
- **Textarea**: 用户输入区域
- **Button**: 触发生成操作
- **Result**: 展示生成的测试用例

#### 2.4.2 JavaScript 请求逻辑

```javascript
async function generateTestCases() {
    const content = document.getElementById('inputContent').value.trim();
    
    const response = await fetch('/api/generate', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            content: content,
            type: currentType
        })
    });
    
    const data = await response.json();
    
    if (data.success && data.content) {
        resultContent.textContent = data.content;
        result.classList.add('show');
    }
}
```

- **fetch API**: 发送 HTTP POST 请求
- **JSON.stringify**: 将 JavaScript 对象转换为 JSON 字符串
- **response.json()**: 解析 JSON 响应

---

## 三、API 接入详解

### 3.1 为什么选择 OpenAI 兼容协议

大多数国产大模型厂商（智谱AI、阿里云、DeepSeek 等）都提供了 **OpenAI 兼容接口**，这意味着：

1. **代码复用**: 使用同一套 `openai` Python 库，可以调用不同厂商的模型
2. **学习成本低**: 只需要学习 OpenAI 的 API 格式
3. **迁移方便**: 切换模型时只需修改配置，不需要改代码

### 3.2 如何切换模型

**方法**: 修改 `.env` 文件中的配置

```env
# 智谱AI GLM-4-Flash（推荐，永久免费）
LLM_API_KEY=your_api_key_here
LLM_BASE_URL=https://open.bigmodel.cn/api/paas/v4/
LLM_MODEL=glm-4-flash

# 阿里云 通义千问（需要申请）
LLM_API_KEY=your_api_key_here
LLM_BASE_URL=https://dashscope.aliyuncs.com/compatible-mode/v1
LLM_MODEL=qwen-plus

# DeepSeek（注册赠送额度）
LLM_API_KEY=your_api_key_here
LLM_BASE_URL=https://api.deepseek.com
LLM_MODEL=deepseek-chat

# Google Gemini（需要科学上网）
LLM_API_KEY=your_api_key_here
LLM_BASE_URL=https://generativelanguage.googleapis.com/v1/
LLM_MODEL=gemini-1.5-flash
```

### 3.3 API Key 的常见问题

#### Q: 同一个用户的不同模型，API Key 是一样的吗？

**A: 取决于平台**

| 平台 | 不同模型是否共享 API Key |
|------|-------------------------|
| 智谱AI | **是**，一个 API Key 可以调用所有模型 |
| 阿里云百炼 | **是**，一个 API Key 可以调用 Qwen、DeepSeek、GLM 等多个模型 |
| DeepSeek | **是**，一个 API Key 可以调用所有 DeepSeek 模型 |
| Google AI Studio | **是**，一个 API Key 可以调用所有 Gemini 模型 |
| OpenAI | **是**，一个 API Key 可以调用所有 OpenAI 模型 |

**总结**: 大多数平台的 API Key 是账户级别的，同一个 Key 可以调用该账户有权限访问的所有模型。切换模型只需修改 `LLM_MODEL` 配置。

#### Q: API Key 的格式是什么样的？

**A: 不同平台格式不同**

- **智谱AI**: `xxxxxxxxxxxxxxxxxxxxxxxxxxxx.xxxxxxxxxxxxxx`（前半部分是用户ID，后半部分是密钥）
- **阿里云**: 通常是一个长字符串
- **DeepSeek**: 通常是 `sk-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx` 格式

#### Q: 如何获取免费 API Key？

**推荐步骤（以智谱AI为例）**:

1. 访问 https://open.bigmodel.cn/
2. 注册账号（支持手机号/邮箱）
3. 登录后进入"控制台"
4. 点击"API Keys" → "创建新密钥"
5. 复制生成的 API Key
6. 粘贴到 `.env` 文件中

### 3.4 常用模型对比

| 平台 | 模型 | 免费额度 | 特点 |
|------|------|----------|------|
| **智谱AI** | GLM-4-Flash | 永久免费，1并发 | 中文能力强，推荐学习使用 |
| **腾讯云** | 混元 Lite | 永久免费 | 256K 超长上下文 |
| **Google** | Gemini 1.5 | 每日免费 | 多模态能力强 |
| **Groq** | Llama 3.1 | 每日免费 | 推理速度极快 |
| **DeepSeek** | DeepSeek V3 | 注册赠送 | 代码能力强 |

### 3.5 API 调用注意事项

#### 3.5.1 速率限制

免费 API 通常有调用限制：
- **智谱AI**: 1并发（同时只能有1个请求）
- **Google**: 每分钟15次，每天1500次
- **Groq**: Llama 3.1 8B 每天14400次

**处理方式**: 在代码中添加重试机制（可选）

```python
import time

def generate_test_cases_with_retry(self, prd_content, max_retries=3):
    for attempt in range(max_retries):
        try:
            return self.generate_test_cases(prd_content)
        except Exception as e:
            if "429" in str(e) and attempt < max_retries - 1:
                wait_time = 2 ** attempt  # 指数退避
                logger.info(f"请求被限流，等待 {wait_time} 秒后重试")
                time.sleep(wait_time)
            else:
                raise
```

#### 3.5.2 超时处理

大模型响应可能需要 10-30 秒，需要设置合理的超时时间：

```python
http_client = httpx.Client(
    timeout=httpx.Timeout(60.0, connect=10.0)  # 总超时60秒
)
```

#### 3.5.3 安全注意事项

1. **不要硬编码 API Key**: 使用 `.env` 文件管理
2. **不要提交 `.env` 到版本控制**: 已添加到 `.gitignore`
3. **不要在免费 API 中发送敏感信息**: 免费层的数据可能被用于模型训练
4. **使用 HTTPS**: 所有 API 调用都使用 HTTPS 协议

---

## 四、技术栈总结

| 层次 | 技术 | 版本 | 用途 |
|------|------|------|------|
| 后端框架 | Flask | 2.3.3 | Web 服务器、路由管理 |
| 大模型 SDK | openai | 1.35+ | 调用大模型 API |
| HTTP 客户端 | httpx | 0.28+ | 底层 HTTP 请求 |
| 环境变量 | python-dotenv | 1.0.1 | 加载 `.env` 文件 |
| 前端 | HTML/CSS/JavaScript | - | 用户界面 |

---

## 五、扩展建议

### 5.1 添加模型选择功能

在前端添加模型下拉框，让用户可以选择不同的模型：

```html
<select id="modelSelect">
    <option value="glm-4-flash">智谱AI GLM-4-Flash</option>
    <option value="qwen-plus">通义千问</option>
    <option value="deepseek-chat">DeepSeek</option>
</select>
```

后端修改为动态接收模型参数。

### 5.2 添加历史记录功能

使用 SQLite 数据库存储生成历史：

```python
import sqlite3

def save_history(content, result, model):
    conn = sqlite3.connect('history.db')
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO history (input_content, output_content, model, created_at)
        VALUES (?, ?, ?, datetime('now'))
    ''', (content, result, model))
    conn.commit()
    conn.close()
```

### 5.3 添加流式输出

支持流式响应（打字机效果），提升用户体验：

```python
response = self.client.chat.completions.create(
    model=self.model,
    messages=messages,
    stream=True  # 启用流式输出
)

for chunk in response:
    content = chunk.choices[0].delta.content
    if content:
        yield content
```

---

## 六、调试技巧

### 6.1 查看后端日志

启动应用后，终端会显示详细日志：

```
INFO:__main__:收到请求，类型: prd，内容长度: 100
INFO:llm_client:开始调用大模型API，模型: glm-4-flash
INFO:llm_client:API调用成功，响应内容长度: 500
INFO:__main__:处理完成，结果: success
```

### 6.2 查看前端控制台

按 F12 打开开发者工具，切换到"控制台"标签：

```
开始发送请求到 /api/generate
收到响应，状态码: 200
响应数据: {success: true, content: "## 测试用例列表..."}
请求结束
```

### 6.3 测试 API 连通性

使用 curl 或 Postman 测试：

```bash
curl -X POST http://localhost:5000/api/generate \
  -H "Content-Type: application/json" \
  -d '{"content": "测试登录功能", "type": "prd"}'
```

---

## 七、常见错误及解决

| 错误信息 | 原因 | 解决方法 |
|----------|------|----------|
| `API调用失败: Invalid API Key` | API Key 无效或格式错误 | 检查 `.env` 文件中的 API Key |
| `API调用失败: Model not found` | 模型名称错误 | 检查 `LLM_MODEL` 配置 |
| `API调用失败: 429 Too Many Requests` | 超出调用限制 | 稍后重试或更换平台 |
| `API调用失败: Connection timeout` | 网络超时 | 检查网络连接或增加超时时间 |
| `前端显示"网络请求失败"` | 后端服务未启动 | 运行 `python -m src.app` |

---

通过以上文档，你应该对项目的实现细节有了全面的了解。核心要点是：

1. **分层架构**: 前端 → 路由 → 服务 → 客户端 → 外部 API
2. **OpenAI 兼容协议**: 通过 `base_url` 切换不同厂商的 API
3. **环境变量配置**: 通过 `.env` 文件管理敏感信息
4. **Prompt 工程**: 通过 System Prompt 引导模型输出格式