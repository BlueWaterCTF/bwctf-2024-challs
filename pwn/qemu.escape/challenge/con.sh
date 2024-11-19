#!/bin/sh
# if you want to connect to vm , and be able to use Ctrl+C,  connect in raw mode
#
stty raw -echo;nc 127.0.0.1 1337;stty -raw echo
