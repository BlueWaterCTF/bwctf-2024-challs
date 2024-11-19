#!/bin/sh
docker run -it -p 1337:1337 --cap-add sys_ptrace pbctf-qemu
