# One image with every toolchain the shared/*/run_all.sh suites need.
# python:3.12 matches CI's python-version; trixie's apt carries JDK 21 (CI's java-version).
FROM python:3.12-slim-trixie

# One RUN layer: deleting the apt lists in a later layer would not shrink this one.
# No python3 here: the base image already provides 3.12, apt would add a second (3.13).
RUN apt-get update \
 && apt-get install -y --no-install-recommends \
        build-essential \
        openjdk-21-jdk-headless \
        rustc \
 && rm -rf /var/lib/apt/lists/*

WORKDIR /lab

# Last on purpose: source changes every commit, so only this layer rebuilds.
COPY . .

CMD ["bash"]
