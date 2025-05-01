FROM ubuntu:22.04

RUN apt-get update -qq && \
    apt-get install -yq --no-install-recommends stress-ng strace && \
    useradd -u 1000 -m appuser && \
    rm -rf /var/lib/apt/lists/*

COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

USER appuser
ENTRYPOINT ["/entrypoint.sh"]