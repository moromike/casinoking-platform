FROM node:20-alpine

WORKDIR /app/frontend-v3

COPY frontend-v3/package.json /app/frontend-v3/package.json
COPY frontend-v3/tsconfig.json /app/frontend-v3/tsconfig.json
COPY frontend-v3/next.config.ts /app/frontend-v3/next.config.ts
COPY frontend-v3/next-env.d.ts /app/frontend-v3/next-env.d.ts

RUN npm install

COPY frontend-v3 /app/frontend-v3

CMD ["/bin/sh", "-lc", "npm run build && npm run start -- --hostname 0.0.0.0"]
