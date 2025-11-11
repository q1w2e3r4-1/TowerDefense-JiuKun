#!/bin/bash
# 启动vllm服务的脚本
MODEL_PATH="$1"
PORT=8000
HOST=127.0.0.1
EXTRA_ARGS="${@:2}"

if [ -z "$MODEL_PATH" ]; then
  echo "用法: $0 <model_path> [extra_args...]"
  exit 1
fi

vllm serve --model "$MODEL_PATH" --port "$PORT" --host "$HOST" --max-model-len 32768 $EXTRA_ARGS
