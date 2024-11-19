The program runs a little arm vm with a modified `qemu-system-arm` binary, which is compiled with the vulnerable driver.

The vm size has been reduced to 4.5 Megabytes, with a boot time of only between 1 or 2 seconds (depending on processor), and will be in idle time most of the time..So should not be too heavy on cpu.

Here is the usage of the provided scripts:

`build-docker.sh` is for building the docker.

`run-docker.sh`will launch the docker, and will export the internal port 1337 to external port 1337 (external port can be changed as needed)

When the user will connect on exported port, it will launch the `start-vm.sh`script inside the docker, that will launch the qemu binary to start the vm. A timeout of 120 seconds is set, to turn off the vm after some time, enough for the user to launch his exploit and get the flag, to be sure that many qemu instances are not left running.. The timeout can be adjusted too.

The `con.sh`script is just an helper to connect to the vm in raw mode to allow ctrl+C and so..



The user will be provided almost the same files, with a dummy flag of course, to be able to develop his exploit first locally on his docker instance. And will just use the remote instance when his exploit is ready.

The user will also be provided with a diff patch file , with the driver modification to the original qemu 8.2 source code.

To be able to analyse the vulnerability.

The challenge is supposed to be of medium difficulty. Medium-hard maybe.

