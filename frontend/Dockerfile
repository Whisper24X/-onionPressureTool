# 使用 Node.js 镜像
FROM node:16-alpine

# 设置工作目录
WORKDIR /app

# 复制 package.json 和 package-lock.json
COPY package*.json ./

# 安装依赖项
RUN npm install

# 复制应用程序源代码
COPY . .

# 暴露应用程序运行的端口
EXPOSE 8080

# 启动开发服务器
CMD ["npm", "run", "serve"]
