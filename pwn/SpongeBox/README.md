# SpongeBox BWCTF 2024

## General Information
**Category**: pwn 

**Author**: [j0nathanj](https://x.com/j0nathanj) 

**Description**:
> SpongeBob lives in a pineapple under the sea. SpongeBox is a cutting-edge sandbox.

**Private files**: `solution/` contains the exploit and a short writeup.

**If we want to give hints**: Described in `hints/`.

**Public Files**: `SpongeBox.tar.gz`

## How to run the challenge
If you want to manually exploit it, without the kCTF connecting stdin/stdout of the challenge to a socket, then you need to modify the entry point of the Dockerfile to be `/bin/bash` and manually run the challenge from within, like descreibed in `solution/README.md`.

Otherwise, just run the following commands to start the container.
First, build the docker image:
```bash
docker build -t spongebox .
```

Then, run the container:
```bash
docker run --privileged -it spongebox
```

This should start the challenge, and given the fact that kCTF is already spinning, you should be able to communicate with the challenge directly.
