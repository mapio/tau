FROM alpine:3.10
LABEL maintainer="Massimo Santini santini@di.unimi.it"
RUN apk add --no-cache --update python3 py-gevent; \
    python3 -m pip install flask flask-mail
EXPOSE 8000
RUN mkdir -p /app/tau
COPY tau /app/tau
COPY run.py /app
WORKDIR /app
CMD ["python3", "run.py"]
