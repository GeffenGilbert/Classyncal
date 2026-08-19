# Two stages: build the static bundle with node, then hand it to a tiny image
# whose only job is to drop the files into a volume Caddy serves. Node is not
# in the running stack at all - it exists for the length of the build.
FROM node:22-alpine AS build
WORKDIR /app

COPY package.json package-lock.json ./
RUN npm ci

COPY . .

# Vite inlines env vars at BUILD time, not runtime - so this has to be a build
# arg. Changing it means rebuilding the image, not restarting a container.
ARG VITE_BACKEND_ORIGIN
ENV VITE_BACKEND_ORIGIN=$VITE_BACKEND_ORIGIN
RUN npm run build

FROM alpine:3
COPY --from=build /app/dist /dist-src
# Runs once per `up`, republishes the bundle into the shared volume, exits.
CMD ["sh", "-c", "rm -rf /dist/* && cp -a /dist-src/. /dist/ && echo published $(ls /dist | wc -l) entries"]
