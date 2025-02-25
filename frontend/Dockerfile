# 构建阶段
FROM node:16 as builder

# 设置工作目录
WORKDIR /app

# 复制 package.json 和 package-lock.json
COPY package*.json ./

# 安装依赖
RUN npm install

# 复制源代码
COPY . .

# 添加构建参数
ARG BUILD_DATE
ENV VITE_APP_BUILD_DATE=${BUILD_DATE}

# 构建应用
RUN npm run build

# 生产阶段
FROM nginx:1.21.3

# 从构建阶段复制构建结果到 nginx 目录
COPY --from=builder /app/dist /usr/share/nginx/html

# 复制 nginx 配置
COPY nginx.conf /etc/nginx/conf.d/default.conf

# 暴露端口
EXPOSE 80

# 启动 nginx
CMD ["nginx", "-g", "daemon off;"]
