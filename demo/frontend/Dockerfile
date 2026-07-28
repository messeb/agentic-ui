# syntax=docker/dockerfile:1
# Standalone: build from this directory.
#   docker build -t agentic-ui-demo-frontend .
FROM node:26-slim AS build
RUN corepack enable
WORKDIR /app

# Dependency layer (cached until the lockfile changes). pnpm avoids the npm
# arborist resolver bug. pnpm-workspace.yaml carries the build allowlist (esbuild
# etc.) — it MUST be present here or the native builds get skipped.
COPY package.json pnpm-lock.yaml pnpm-workspace.yaml ./
RUN --mount=type=cache,id=pnpm,target=/root/.local/share/pnpm/store \
    pnpm install --frozen-lockfile

# App source (includes the vendored manifest under shared/).
COPY . .
RUN pnpm run build

FROM node:26-slim AS runtime
WORKDIR /app
ENV NODE_ENV=production \
    NUXT_HOST=0.0.0.0 \
    NUXT_PORT=3000
COPY --from=build /app/.output ./.output
USER node
EXPOSE 3000
CMD ["node", ".output/server/index.mjs"]
