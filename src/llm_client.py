import os
import logging
from dotenv import load_dotenv
from openai import OpenAI
import httpx

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class LLMClient:
    def __init__(self):
        self.api_key = os.getenv("LLM_API_KEY")
        self.base_url = os.getenv("LLM_BASE_URL", "https://open.bigmodel.cn/api/paas/v4/")
        self.model = os.getenv("LLM_MODEL", "glm-4-flash")
        
        http_client = httpx.Client(
            timeout=httpx.Timeout(60.0, connect=10.0),
            follow_redirects=True
        )
        
        self.client = OpenAI(
            api_key=self.api_key,
            base_url=self.base_url,
            http_client=http_client
        )

    def generate_test_cases(self, prd_content):
        system_prompt = """你是一个专业的软件测试工程师，擅长根据产品需求文档（PRD）和用户故事（User Story）生成结构化的测试用例。

请按照以下格式输出测试用例：
```
## 测试用例列表

### TC-001: 用例标题
**前置条件**: [描述测试前需要满足的条件]
**测试步骤**:
1. [步骤1描述]
2. [步骤2描述]
3. [步骤3描述]
**预期结果**: [描述预期的输出或行为]

### TC-002: 用例标题
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

        user_prompt = f"""请根据以下产品需求/用户故事生成结构化的测试用例：

---
{prd_content}
---

请输出详细的测试用例，覆盖各种场景。"""

        try:
            logger.info(f"开始调用大模型API，模型: {self.model}")
            logger.info(f"请求内容长度: {len(prd_content)} 字符")
            
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
            logger.info(f"API调用成功，响应内容长度: {len(content)} 字符")
            return content
        except Exception as e:
            logger.error(f"API调用失败: {str(e)}")
            return f"API调用失败: {str(e)}"