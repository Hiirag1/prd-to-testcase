from flask import Flask, render_template, request, jsonify
from .services.testcase_service import TestCaseService

app = Flask(__name__)
app.config['JSON_AS_ASCII'] = False

service = TestCaseService()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/generate', methods=['POST'])
def generate_test_cases():
    import logging
    logger = logging.getLogger(__name__)
    
    try:
        data = request.get_json()
        content = data.get('content', '')
        content_type = data.get('type', 'prd')
        
        logger.info(f"收到请求，类型: {content_type}，内容长度: {len(content)}")

        if content_type == 'user_story':
            result = service.generate_from_user_story(content)
        else:
            result = service.generate_from_prd(content)

        logger.info(f"处理完成，结果: {'success' if result.get('success') else 'error'}")
        
        if result.get('error'):
            logger.error(f"错误信息: {result['error']}")
        else:
            logger.info(f"生成内容长度: {len(result.get('content', ''))}")
            
        return jsonify(result)
    except Exception as e:
        logger.error(f"处理请求时发生异常: {str(e)}")
        return jsonify({"error": f"服务器内部错误: {str(e)}"}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)