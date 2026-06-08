FROM python:3.10-slim

RUN apt-get update && \
    apt-get install -y curl git gcc libsodium-dev libsecp256k1-dev libgmp-dev make && \
    apt-get clean
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/
ARG BRANCH=main
WORKDIR /bridge
COPY . /bridge
RUN uv sync
ENTRYPOINT ["uv", "run"]
CMD ["bash"]
