#!/bin/bash
# 启动vllm服务的脚本
set -x
MODEL_PATH="$1"
LORA_PATH="$2"
LORA_TAG=${3:-"default"}
PORT=8000
HOST=127.0.0.1
EXTRA_ARGS="${@:4}"

if [ -z "$MODEL_PATH" ]; then
  echo "用法: $0 <model_path> [extra_args...]"
  exit 1
fi

vllm serve "$MODEL_PATH" --enable-lora \
    --lora-modules qwen-lora-$LORA_TAG=$LORA_PATH --port "$PORT" --host "$HOST" --max-model-len 32768 $EXTRA_ARGS
