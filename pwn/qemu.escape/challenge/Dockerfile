FROM ubuntu:24.04

RUN apt update -y && apt install -y libfdt1 libslirp0 socat

WORKDIR /srv
COPY vm /srv
COPY start-vm.sh /srv/
COPY qemu-system-arm /srv/
COPY flag.txt /srv/

ENTRYPOINT ["socat", "tcp-l:1337,fork,reuseaddr", "EXEC:/srv/start-vm.sh"]
