#!/bin/sh
timeout 120 /srv/qemu-system-arm -M virt,highmem=off -m 128 -initrd /srv/rootfs.cpio.zst -kernel /srv/zImage -nographic -append "rootnowait" -netdev user,id=net0 -device virtio-net-device,netdev=net0 -monitor /dev/null
