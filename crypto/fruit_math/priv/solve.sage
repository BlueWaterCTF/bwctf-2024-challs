load('save.sage')

from pwn import *
from tqdm import tqdm
import ast
import base64
import hashlib
import sys
import zlib

r = remote(sys.argv[1], sys.argv[2])

context.log_level = 'debug'

r.recvuntil(b'testcases = ')
testcases = ast.literal_eval(r.recvline().strip().decode())

messages = []
for alpha_v, beta_v in tqdm(testcases):
    at = eq_a(alpha=alpha_v, beta=beta_v)
    bt = eq_b(alpha=alpha_v, beta=beta_v)
    ct = eq_c(alpha=alpha_v, beta=beta_v)

    arr = []
    for i in range(1, 101):
        a, b, c = at(n=i), bt(n=i), ct(n=i)
        l = lcm([a.denominator(), b.denominator(), c.denominator()])
        a, b, c = l * a, l * b, l * c

        arr.append((a, b, c))
    messages.append(str(arr))

message = '/'.join(messages)
compressed = zlib.compress(message.encode())
proof = hashlib.sha256(compressed).hexdigest()
to_send = base64.b64encode(compressed)

r.sendlineafter(b'> ', proof.encode())
r.sendlineafter(b'> ', to_send)

r.recvuntil(b'Here is the flag: ')
print(r.recvline())
