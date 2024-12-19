# 使用 Node.js 镜像
FROM node:16-alpine
# 使用 nginx 镜像
FROM nginx:alpine
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

# 删除默认的 nginx 网站
RUN rm -rf /usr/share/nginx/html/*

# 将打包后的文件复制到 nginx 的静态文件目录
COPY dist/ /usr/share/nginx/html/

# 启动开发服务器
CMD ["npm", "run", "dev"]

# 启动 nginx 服务
CMD ["nginx", "-g", "daemon off;"]
