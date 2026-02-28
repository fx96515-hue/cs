FROM node:lts-alpine AS deps
WORKDIR /usr/src/app
COPY package.json package-lock.json* ./
RUN npm ci

FROM node:lts-alpine AS builder
WORKDIR /usr/src/app
COPY --from=deps /usr/src/app/node_modules ./node_modules
COPY . .
ENV NEXT_TELEMETRY_DISABLED=1
RUN npm run build

FROM node:lts-alpine AS runner
ENV NODE_ENV=production
ENV PORT=3000
WORKDIR /usr/src/app
COPY --from=builder /usr/src/app/.next/standalone ./
COPY --from=builder /usr/src/app/.next/static ./.next/static
EXPOSE 3000
CMD ["node", "server.js"]
