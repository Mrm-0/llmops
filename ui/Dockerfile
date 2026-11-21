# 前端构建镜像：Node 22 LTS（Vue 3.5 + Vite 需要 Node 20.19+/22.12+，Node 20 已于 2026-04 结束维护）
FROM node:22-alpine AS builder

WORKDIR /app/web

COPY package.json .
COPY yarn.lock .

# 国内 npm 源，加速依赖安装（yarn 1.x）
RUN yarn config set registry https://registry.npmmirror.com && yarn install --network-timeout 600000

COPY . .

# 配置接口前缀（前端请求走 /api，由外层 nginx 转发到 llmops-api）
ENV VITE_API_PREFIX=/api

RUN yarn build

# 二阶段：Nginx 托管 Vue 静态页面
FROM nginx:stable-alpine AS production
COPY --from=builder /app/web/dist /usr/share/nginx/html
COPY --from=builder /app/web/docker/nginx/nginx.conf /etc/nginx/conf.d/default.conf

RUN find /usr/share/nginx/html -type d -exec chmod 755 {} \; && \
    find /usr/share/nginx/html -type f -exec chmod 644 {} \;

EXPOSE 3000

CMD ["nginx", "-g", "daemon off;"]
