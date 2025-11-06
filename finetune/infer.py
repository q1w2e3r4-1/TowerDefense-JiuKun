from vllm import LLM, SamplingParams

# dont use this
# 指向你下载的本地目录
llm = LLM(
    model="/home/models/Qwen3-4B",
    trust_remote_code=True,        # 必须！
    dtype="auto",                  # 自动选择 bfloat16 / float16
    tensor_parallel_size=1,         
    max_model_len=2048,            # 根据模型最大长度设置
    # enforce_eager=True,
    gpu_memory_utilization=0.7,
    # max_num_seqs = 8,

    reasoning_parser="deepseek_r1",  # 必须与模型匹配
)

sampling_params = SamplingParams(temperature=0.7, top_p=0.8, max_tokens=256)

prompts = [
    "Please introduce yourself."
]

outputs = llm.generate(prompts, sampling_params)

for output in outputs:
    print(output.prompt)
    print(output.outputs[0].text)
    print("-" * 50)
