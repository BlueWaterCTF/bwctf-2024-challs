#!/bin/sh


# This script uses 2 fifos to communicate.
# Exploit.py uses those FIFOs as can be seen.
# This emulates running it locally. 
python3 exploit.py /tmp/sandbox_stdin /tmp/sandbox_stdout
