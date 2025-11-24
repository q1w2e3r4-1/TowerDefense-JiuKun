#!/bin/bash
# 启动vllm服务的脚本
set -x
MODEL_PATH="$1"
LORA_PATH="$2"
PORT=8000
HOST=127.0.0.1
EXTRA_ARGS="${@:3}"

if [ -z "$MODEL_PATH" ]; then
  echo "用法: $0 <model_path> [extra_args...]"
  exit 1
fi

vllm serve "$MODEL_PATH" --enable-lora \
    --lora-modules qwen-lora=$LORA_PATH --port "$PORT" --host "$HOST" --max-model-len 65536 $EXTRA_ARGS
