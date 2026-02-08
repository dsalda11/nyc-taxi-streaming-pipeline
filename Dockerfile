# Base image: ubuntu:22.04
FROM ubuntu:22.04

# ARGs
# https://docs.docker.com/engine/reference/builder/#understand-how-arg-and-from-interact
ARG TARGETPLATFORM=linux/amd64,linux/arm64
ARG DEBIAN_FRONTEND=noninteractive
ARG GITHUB_USER=LamuSamuel
ARG GITHUB_TOKEN=<Your_Secret>
RUN apt-get update && apt-get install -y wget gnupg software-properties-common netcat

RUN apt update && apt install -y git

RUN mkdir -p /cse511


RUN git clone https://${GITHUB_USER}:${GITHUB_TOKEN}@github.com/LamuSamuel/cse511.git /cse511


WORKDIR /cse511

RUN ls -la

RUN chmod +x dataset.sh

RUN ./dataset.sh


RUN wget -O - https://debian.neo4j.com/neotechnology.gpg.key | apt-key add - && \
    echo 'deb https://debian.neo4j.com stable latest' > /etc/apt/sources.list.d/neo4j.list && \
    add-apt-repository universe && \
    apt-get update && \
    apt-get install -y nano unzip neo4j python3-pip && \
    apt-get autoremove -y && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/*

ENV NEO4J_AUTH=neo4j/processingpipeline

RUN neo4j-admin dbms set-initial-password "processingpipeline"

RUN echo "server.default_listen_address=0.0.0.0" >> /etc/neo4j/neo4j.conf && \
    echo "server.http.listen_address=:7474" >> /etc/neo4j/neo4j.conf && \
    echo "server.bolt.listen_address=:7687" >> /etc/neo4j/neo4j.conf && \
    echo "server.bolt.advertised_address=:7687" >> /etc/neo4j/neo4j.conf && \
    echo "server.http.advertised_address=:7474" >> /etc/neo4j/neo4j.conf && \
    echo "dbms.security.procedures.unrestricted=gds.*,apoc.*" >> /etc/neo4j/neo4j.conf

RUN pip install pyarrow pandas neo4j

RUN wget -O /var/lib/neo4j/plugins/neo4j-graph-data-science-2.15.0.jar \
    https://graphdatascience.ninja/neo4j-graph-data-science-2.15.0.jar

EXPOSE 7474 7687
CMD ["/bin/bash", "-c", "\
    neo4j start && \
    echo 'Waiting for Neo4j...' && \
    for i in {1..30}; do nc -z localhost 7687 && break; echo 'Still waiting...'; sleep 2; done && \
    python3 /cse511/data_loader.py && \
    tail -f /dev/null"]
