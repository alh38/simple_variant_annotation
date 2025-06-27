FROM python:3.11-slim

# Install essential tools
RUN apt-get update && apt-get install -y \
    wget \
    unzip \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Install Java 21 manually
RUN wget -q https://github.com/adoptium/temurin21-binaries/releases/download/jdk-21.0.1+12/OpenJDK21U-jre_x64_linux_hotspot_21.0.1_12.tar.gz && \
    mkdir -p /opt/java && \
    tar -xzf OpenJDK21U-jre_x64_linux_hotspot_21.0.1_12.tar.gz -C /opt/java --strip-components=1 && \
    rm OpenJDK21U-jre_x64_linux_hotspot_21.0.1_12.tar.gz

ENV JAVA_HOME=/opt/java
ENV PATH="${JAVA_HOME}/bin:${PATH}"

RUN pip install pysam pytest

# Set working directory
WORKDIR /app

RUN wget -q https://snpeff.blob.core.windows.net/versions/snpEff_latest_core.zip \
    && unzip snpEff_latest_core.zip \
    && rm snpEff_latest_core.zip

COPY src/ ./src/

ENV PYTHONPATH="/app/src:${PYTHONPATH}"
