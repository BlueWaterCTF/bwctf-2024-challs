#!/bin/bash

echo "Starting sandbox"
mkfifo /tmp/sandbox_stdin
mkfifo /tmp/sandbox_stdout

./sandbox < /tmp/sandbox_stdin > /tmp/sandbox_stdout
