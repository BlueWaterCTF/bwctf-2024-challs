FROM ubuntu:22.04@sha256:965fbcae990b0467ed5657caceaec165018ef44a4d2d46c7cdea80a9dff0d1ea

RUN apt update && apt install -y socat python3 python3-pip

COPY ./dist/main.py /
COPY ./flag /

CMD socat TCP-LISTEN:23235,reuseaddr,fork EXEC:"python3 /main.py"

EXPOSE 23235