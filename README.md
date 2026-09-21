# PRD/用户故事转测试用例

一个轻量级的Python Web应用，用于将产品需求文档（PRD）或用户故事（User Story）自动转换为结构化的测试用例。

## 功能特点

- 📝 支持输入产品需求文档（PRD）或用户故事（User Story）
- 🤖 调用大模型API自动解析需求并生成测试用例
- 📋 生成结构化测试用例（用例编号、前置条件、测试步骤、预期结果）
- 🎨 简洁美观的Web界面

## 技术栈

- **后端**: Flask 2.3.3
- **大模型**: 智谱AI GLM-4-Flash
- **API协议**: OpenAI兼容接口

# API调用说明

### 调用位置

API调用位于 [src/llm\_client.py](src/llm_client.py) 文件第55-65行：

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
```

### 调用方式

1. 使用官方 `openai` Python库
2. 通过 `base_url` 参数指定智谱AI的API地址
3. 通过 `api_key` 参数传入API密钥
4. 发送标准的Chat Completions请求格式

<br />

## 快速开始

### 环境要求

- Python 3.9+
- pip

### 安装步骤

1. **克隆项目**

   ```bash
   git clone https://github.com/Hiirag1/prd-to-testcase.git
   cd prd-to-testcase
   ```

2. **安装依赖**

   ```bash
   pip install -r requirements.txt
   ```

3. **配置API Key**

   ```bash
   cp .env.example .env
   ```

   编辑 `.env` 文件，填入API Key：

   ```env
   LLM_API_KEY=your_api_key_here
   LLM_BASE_URL=https://open.bigmodel.cn/api/paas/v4/
   LLM_MODEL=glm-4-flash
   ```

4. **启动应用**

   ```bash
   python -m src.app
   ```

5. **访问应用**

   打开浏览器访问 `http://localhost:5000`

## 使用示例

### 输入PRD

```
功能：用户登录模块
需求：
1. 用户可以通过手机号+验证码登录
2. 用户可以通过邮箱+密码登录
3. 连续5次输错密码需等待10分钟
```

### 输入用户故事

```
作为一个用户，我希望能够通过手机号快捷登录，以便快速访问我的账户。
```

### 输出格式

```
## 测试用例列表

### TC-001: 手机号验证码登录成功
**前置条件**: 用户已注册手机号，且手机号可用
**测试步骤**:
1. 进入登录页面
2. 选择"手机号登录"方式
3. 输入正确的手机号
4. 点击"获取验证码"
5. 输入收到的验证码
6. 点击"登录"按钮
**预期结果**: 用户成功登录，跳转到首页

### TC-002: 邮箱密码登录失败（密码错误）
**前置条件**: 用户已注册邮箱账号
**测试步骤**:
1. 进入登录页面
2. 选择"邮箱登录"方式
3. 输入正确的邮箱
4. 输入错误的密码
5. 点击"登录"按钮
**预期结果**: 提示"密码错误"，登录失败
```

## 项目结构

```
prd-to-testcase/
├── src/
│   ├── __init__.py
│   ├── app.py              # Flask应用入口
│   ├── llm_client.py       # 大模型API客户端（API调用位置）
│   ├── services/
│   │   ├── __init__.py
│   │   └── testcase_service.py  # 测试用例生成服务
│   └── templates/
│       └── index.html      # 前端页面
├── .env                    # 环境变量配置（包含API Key）
├── .env.example            # 环境变量示例
├── .gitignore
├── requirements.txt        # 依赖列表
└── README.md
```

