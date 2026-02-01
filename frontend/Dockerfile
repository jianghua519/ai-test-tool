FROM node:20-alpine as builder

WORKDIR /app

COPY ai-test-frontend/package.json ai-test-frontend/pnpm-lock.yaml ./
RUN npm install -g pnpm && pnpm install

COPY ai-test-frontend .
RUN pnpm build

FROM node:20-alpine

WORKDIR /app

COPY --from=builder /app/dist ./dist
COPY --from=builder /app/node_modules ./node_modules
COPY --from=builder /app/package.json ./package.json

EXPOSE 5173

CMD ["node", "dist/index.js"]