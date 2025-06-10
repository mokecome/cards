#!/bin/bash
# 啟動 FastAPI 後端
cd "$(dirname "$0")"
echo "[INFO] 啟動 FastAPI 後端..."
nohup uvicorn main:app --host 0.0.0.0 --port 8006 --reload > backend/nohup_backend.log 2>&1 &
BACKEND_PID=$!
echo "[INFO] FastAPI 後端啟動於 PID $BACKEND_PID，log: backend/nohup_backend.log"

# 啟動 React 前端
cd frontend

echo "[INFO] 啟動 React 前端..."
nohup npm start > nohup_frontend.log 2>&1 &
FRONTEND_PID=$!
echo "[INFO] React 前端啟動於 PID $FRONTEND_PID，log: frontend/nohup_frontend.log"

cd ..
echo "[INFO] 前後端已於背景啟動。"
echo "[INFO] 前端：http://<你的IP>:1002"
echo "[INFO] 後端：http://<你的IP>:8006"
