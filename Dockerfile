FROM python:3.10-slim

RUN apt-get update && \
    apt-get install -y curl git gcc libsodium-dev libsecp256k1-dev libgmp-dev make && \
    apt-get clean
RUN curl -sSL https://install.python-poetry.org | python3 -
ENV PATH="/root/.local/bin:${PATH}"
ARG BRANCH=main
ENV POETRY_HTTP_TIMEOUT=300
RUN git clone --branch $BRANCH https://github.com/baking-bad/etherlink-bridge.git /bridge
WORKDIR /bridge
RUN poetry install --no-root
ENTRYPOINT ["poetry", "run"]
CMD ["bash"]

