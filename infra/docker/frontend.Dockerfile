FROM node:20-alpine

WORKDIR /app/frontend

COPY frontend/package.json /app/frontend/package.json
COPY frontend/tsconfig.json /app/frontend/tsconfig.json
COPY frontend/next.config.ts /app/frontend/next.config.ts
COPY frontend/next-env.d.ts /app/frontend/next-env.d.ts

RUN npm install

COPY frontend /app/frontend

CMD ["npm", "run", "dev", "--", "--hostname", "0.0.0.0", "--port", "3000"]
