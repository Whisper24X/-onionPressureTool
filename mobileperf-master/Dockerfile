# 使用 Python 作为基础镜像
FROM python:3.9-slim

# 设置工作目录
WORKDIR /app


# 复制 requirements 文件并安装依赖
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

ENV PYTHONPATH="/app"

# 复制 Flask 应用代码
COPY mobileperf /app/mobileperf

#ENV PYTHONPATH="/app/mobileperf-master:${PYTHONPATH}"


# 暴露 Flask 服务端口
EXPOSE 5500

# 运行 Flask 应用
CMD ["python", "mobileperf/interface/app.py"]

