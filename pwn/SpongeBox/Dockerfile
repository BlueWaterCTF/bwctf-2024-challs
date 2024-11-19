# Use the official Ubuntu base image
FROM ubuntu:latest

# Set environment variables to avoid prompts during package installation
ENV DEBIAN_FRONTEND=noninteractive

# Update package lists and install GCC, GDB, Vim, and some useful tools
RUN apt-get update && \
    apt-get install -y \
    gcc \
    gdb \
    vim \
    build-essential \
    python3 \
    && rm -rf /var/lib/apt/lists/*

# Set the working directory inside the container
WORKDIR /usr/src/app

# Copy all files from the current directory to the container
COPY . .

RUN gcc -w -o sandbox sandbox.c 

COPY ./flag /flag
RUN chown root:root /flag && chmod 400 /flag

# Set the default command to launch a bash shell when the container starts
CMD ["./sandbox"]

