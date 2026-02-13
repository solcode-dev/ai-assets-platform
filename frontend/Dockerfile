FROM node:20-alpine AS base

WORKDIR /app

# package.json과 package-lock.json을 먼저 복사
COPY package*.json ./

# .next 디렉토리 미리 생성 및 node 사용자 권한 부여
RUN mkdir -p /app/.next && chown -R node:node /app

# node 사용자로 전환하여 이후 작업 수행
USER node

RUN npm install

COPY --chown=node:node . .

# 개발 모드용
CMD ["npm", "run", "dev"]
