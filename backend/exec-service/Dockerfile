FROM node:20-alpine

# 安装Playwright依赖
RUN apk add --no-cache \
    chromium \
    nss \
    freetype \
    harfbuzz \
    ca-certificates \
    ttf-freefont

# 设置Playwright使用系统Chromium
ENV PLAYWRIGHT_SKIP_BROWSER_DOWNLOAD=1
ENV PLAYWRIGHT_CHROMIUM_EXECUTABLE_PATH=/usr/bin/chromium-browser

WORKDIR /app

COPY package*.json ./
RUN npm install --production

# 安装Playwright浏览器
RUN npx playwright install chromium || true

COPY . .

EXPOSE 3001

CMD ["npm", "start"]
