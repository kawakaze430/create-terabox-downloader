FROM python:3.12-slim-bookworm@sha256:935c3c5b12357a7e10caa9c1e6ca5692344d97cf229832ef584be2cec9fc03df AS api

ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
WORKDIR /app

COPY services/api/requirements.lock ./
RUN --mount=type=secret,id=build_ca \
    if [ -f /run/secrets/build_ca ]; then export PIP_CERT=/run/secrets/build_ca; fi \
    && python -m pip install --no-cache-dir -r requirements.lock \
    && python -m pip check \
    && install -d -m 0700 -o 10001 -g 10001 /var/lib/transfers /var/lib/transfers/storage

COPY --chown=10001:10001 services/api/app ./app
USER 10001:10001

FROM node:24-bookworm-slim@sha256:dc26ae92c9fb15cf6b1d63e20f0944b2efe0f115b20e00be48fb23fceb061c54 AS web-build

ENV NEXT_TELEMETRY_DISABLED=1
ARG NEXT_PUBLIC_ENABLE_MANAGED_TRANSFERS=0
ENV NEXT_PUBLIC_ENABLE_MANAGED_TRANSFERS=$NEXT_PUBLIC_ENABLE_MANAGED_TRANSFERS \
    NEXT_PUBLIC_API_BASE_URL=""

WORKDIR /app
COPY apps/web/package.json apps/web/package-lock.json ./
RUN --mount=type=secret,id=build_ca \
    if [ -f /run/secrets/build_ca ]; then export NODE_EXTRA_CA_CERTS=/run/secrets/build_ca; fi \
    && npm ci --no-audit --no-fund

COPY apps/web/app ./app
COPY apps/web/next-env.d.ts apps/web/next.config.ts apps/web/tsconfig.json ./
RUN npm run build && npm prune --omit=dev --offline --no-audit --no-fund

FROM node:24-bookworm-slim@sha256:dc26ae92c9fb15cf6b1d63e20f0944b2efe0f115b20e00be48fb23fceb061c54 AS web

WORKDIR /app
ENV NODE_ENV=production NEXT_TELEMETRY_DISABLED=1
COPY --from=web-build --chown=node:node /app/package.json /app/next.config.ts ./
COPY --from=web-build --chown=node:node /app/.next ./.next
COPY --from=web-build /app/node_modules ./node_modules
USER node
CMD ["npm", "run", "start", "--", "--hostname", "0.0.0.0"]
