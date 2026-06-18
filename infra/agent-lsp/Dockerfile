# syntax=docker/dockerfile:1

FROM golang:1.26-bookworm AS builder
RUN apt-get update \
 && apt-get install -y --no-install-recommends git ca-certificates \
 && rm -rf /var/lib/apt/lists/*
WORKDIR /src
RUN git clone --depth 1 https://github.com/blackwell-systems/agent-lsp.git .
ENV GOTOOLCHAIN=auto
RUN go mod download
RUN CGO_ENABLED=0 GOOS=linux go build -trimpath -ldflags="-s -w" \
    -o /out/agent-lsp ./cmd/agent-lsp/

FROM debian:bookworm-slim

RUN apt-get update \
 && apt-get install -y --no-install-recommends \
      ca-certificates curl git nodejs npm 
RUN npm install -g \
      pyright \
      vscode-html-language-server \
      typescript-language-server typescript \
      vscode-langservers-extracted \
      dockerfile-language-server-nodejs \
 && rm -rf /var/lib/apt/lists/*

COPY --from=builder /out/agent-lsp /usr/local/bin/agent-lsp
COPY --from=builder /src/docker/entrypoint.sh /usr/local/bin/entrypoint.sh
COPY --from=builder /src/docker/lsp-servers.yaml /etc/agent-lsp/lsp-servers.yaml

RUN chmod +x /usr/local/bin/entrypoint.sh \
 && mkdir -p /var/cache/lsp-servers /workspace \
 && groupadd --gid 65532 nonroot \
 && useradd --uid 65532 --gid 65532 --no-create-home --shell /usr/sbin/nologin nonroot \
 && chown -R nonroot:nonroot /var/cache/lsp-servers /workspace

ENV HOME=/tmp
WORKDIR /workspace
USER nonroot

ENTRYPOINT ["/usr/local/bin/entrypoint.sh"]
CMD []