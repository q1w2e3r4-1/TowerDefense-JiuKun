from openai import OpenAI

client = OpenAI(
    base_url="http://localhost:8000/v1",
    api_key="token-abc123"  # 任意非空字符串
)

response = client.chat.completions.create(
    model="Qwen/Qwen3-4B-Thinking-2507",
    messages=[
        {"role": "user", "content": "Please introduce yourself. I'm a student in the 6th grade, so keep it simple and fun."}
    ],
    max_tokens=256,
    temperature=0.7,
    stream=False
)

print(response.choices[0].message.content)