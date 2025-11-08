from openai import OpenAI

# 创建一个指向您本地服务器的客户端实例
# 注意：base_url 指向您启动服务的地址和端口
client = OpenAI(
    api_key="token-dummy", # vLLM 服务器默认不需要真实 API Key，但客户端库要求提供一个
    base_url="http://localhost:8000/v1" # 这是 vLLM 服务的默认地址
)

# 发送聊天补全请求
response = client.chat.completions.create(
    model="/home/models/Qwen3-4B", # 这个模型名称可以是您启动时使用的路径或任意名称，如果未指定 --served-model-name
    messages=[
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user", "content": "你好，请介绍一下你自己。"} # 您的输入提示
    ],
    temperature=0.7, # 可选参数
    max_tokens=512,  # 可选参数，控制生成的最大 token 数
    # stream=True # 如果您想流式接收输出，可以取消注释此行
)

# 打印生成的回复
print(response.choices[0].message.content)