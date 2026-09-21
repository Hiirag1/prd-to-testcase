from ..llm_client import LLMClient

class TestCaseService:
    def __init__(self):
        self.llm_client = LLMClient()

    def generate_from_prd(self, prd_content):
        if not prd_content or not prd_content.strip():
            return {"error": "PRD内容不能为空"}

        result = self.llm_client.generate_test_cases(prd_content)
        
        if result.startswith("API调用失败"):
            return {"error": result}
        
        return {"success": True, "content": result}

    def generate_from_user_story(self, user_story):
        if not user_story or not user_story.strip():
            return {"error": "用户故事内容不能为空"}

        prd_content = f"""用户故事：{user_story}

请根据以上用户故事，分析需求并生成测试用例。"""
        
        return self.generate_from_prd(prd_content)