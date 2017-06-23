FROM amazonlinux:latest

COPY . /app
WORKDIR /app

RUN yum install -y python27-virtualenv openssl-devel zip gcc
RUN make zip
