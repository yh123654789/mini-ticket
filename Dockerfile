# 单服务部署镜像：前端编译进镜像，由 FastAPI 一起发出去。
# 适合 Render / Railway / 任意单容器环境 —— 一个地址同时提供页面和 API。

# ---------- 阶段 1：编译前端 ----------
FROM node:22-alpine AS web
WORKDIR /web
COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci
COPY frontend/tsconfig.json frontend/vite.config.ts frontend/vitest.config.ts frontend/index.html ./
COPY frontend/src ./src
RUN npm run build

# ---------- 阶段 2：后端 + 静态文件 ----------
FROM python:3.13-slim
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1
WORKDIR /app

COPY backend/requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY backend/app ./app
COPY --from=web /web/dist ./app/static

RUN mkdir -p /data
EXPOSE 8000

CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}"]
