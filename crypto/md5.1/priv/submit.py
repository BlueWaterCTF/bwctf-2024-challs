from pwn import *
import sys

with open('second.txt', 'r') as f:
    lines = f.readlines()

r = remote(sys.argv[1], sys.argv[2])

for i in range(10):
    r.sendlineafter(b'm1 > ', lines[2 * i].strip().encode())
    r.sendlineafter(b'm2 > ', lines[2 * i + 1].strip().encode())

r.interactive()
