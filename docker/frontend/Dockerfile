# syntax=docker/dockerfile:1
# Build context: ./frontend   |   Application code & package.json are added in S1-T6.
FROM node:25-alpine AS base
WORKDIR /app
ENV NEXT_TELEMETRY_DISABLED=1

# ---- dependency layer ----
FROM base AS deps
COPY package.json package-lock.json* ./
RUN if [ -f package-lock.json ]; then npm ci; else npm install; fi

# ---- development image (hot reload) ----
FROM deps AS development
ENV NODE_ENV=development
COPY . .
EXPOSE 3000
CMD ["npm", "run", "dev"]

# ---- build stage ----
FROM deps AS build
ENV NODE_ENV=production
# NEXT_PUBLIC_* must be present at BUILD time (Next inlines them into the bundle).
ARG NEXT_PUBLIC_API_URL
ARG NEXT_PUBLIC_WS_URL
ARG NEXT_PUBLIC_APP_ENV
ENV NEXT_PUBLIC_API_URL=$NEXT_PUBLIC_API_URL \
    NEXT_PUBLIC_WS_URL=$NEXT_PUBLIC_WS_URL \
    NEXT_PUBLIC_APP_ENV=$NEXT_PUBLIC_APP_ENV
COPY . .
RUN npm run build

# ---- production image (Next standalone output) ----
FROM base AS production
ENV NODE_ENV=production
COPY --from=build /app/.next/standalone ./
COPY --from=build /app/.next/static ./.next/static
COPY --from=build /app/public ./public
EXPOSE 3000
CMD ["node", "server.js"]
