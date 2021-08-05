FROM python:3.7-slim
MAINTAINER Hannah Bast <bast@cs.uni-freiburg.de>

EXPOSE 8080
ENTRYPOINT python -m http.server --directory /www 8080

# docker rm -f wikidata-types.webserver; docker build -f webserver.Dockerfile -t wikidata-types.webserver . && docker run -it -d --restart=unless-stopped -p 7017:8080 -v $(pwd):/www --name wikidata-types.webserver wikidata-types.webserver; docker logs -f wikidata-types.webserver
