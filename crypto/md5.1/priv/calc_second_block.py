from ast import literal_eval
from tqdm import trange
import math
import os
import random

# For reproducibility
seed = os.urandom(10)
print('seed', seed.hex())
random.seed(seed)

# MD5 Implementation from https://rosettacode.org/wiki/MD5/Implementation#Python
rotate_amounts = [7, 12, 17, 22, 7, 12, 17, 22, 7, 12, 17, 22, 7, 12, 17, 22,
                  5,  9, 14, 20, 5,  9, 14, 20, 5,  9, 14, 20, 5,  9, 14, 20,
                  4, 11, 16, 23, 4, 11, 16, 23, 4, 11, 16, 23, 4, 11, 16, 23,
                  6, 10, 15, 21, 6, 10, 15, 21, 6, 10, 15, 21, 6, 10, 15, 21]

constants = [int(abs(math.sin(i+1)) * 2**32) & 0xFFFFFFFF for i in range(64)]

init_values = [0x67452301, 0xefcdab89, 0x98badcfe, 0x10325476]

functions = 16*[lambda b, c, d: (b & c) | (~b & d)] + \
        16*[lambda b, c, d: (d & b) | (~d & c)] + \
        16*[lambda b, c, d: b ^ c ^ d] + \
        16*[lambda b, c, d: c ^ (b | ~d)]

functions_mod = 16*[lambda b, c, d: (b & c) | (~b & d)] + \
        16*[lambda b, c, d: (d & b) | (~d & c)] + \
        16*[lambda b, c, d: b ^ c ^ d] + \
        16*[lambda b, c, d: c ^ (~b | d)]

index_functions = 16*[lambda i: i] + \
                  16*[lambda i: (5*i + 1)%16] + \
                  16*[lambda i: (3*i + 5)%16] + \
                  16*[lambda i: (7*i)%16]

def left_rotate(x, amount):
    x &= 0xFFFFFFFF
    return ((x<<amount) | (x>>(32-amount))) & 0xFFFFFFFF

def _md5(message, aux_functions):

    hash_pieces = init_values[:]
    qs = []

    for chunk_ofst in range(0, len(message), 64):
        a, b, c, d = hash_pieces
        chunk = message[chunk_ofst:chunk_ofst+64]
        for i in range(64):
            f = aux_functions[i](b, c, d)
            g = index_functions[i](i)
            to_rotate = a + f + constants[i] + int.from_bytes(chunk[4*g:4*g+4], byteorder='little')
            new_b = (b + left_rotate(to_rotate, rotate_amounts[i])) & 0xFFFFFFFF
            qs.append(new_b)
            a, b, c, d = d, new_b, b, c
        for i, val in enumerate([a, b, c, d]):
            hash_pieces[i] += val
            hash_pieces[i] &= 0xFFFFFFFF
    
    return hash_pieces, qs

def md5_orig(message):
    return _md5(message, functions)

def md5_mod(message):
    return _md5(message, functions_mod)

# Recalculate the message blocks from the given states
def recalculate_m(state1, state2, init):
    m = [None for _ in range(16)]

    # The starting state of the other one
    init2 = [ v ^ 0x80000000 for v in init ]

    for i in range(16):
        func = lambda b, c, d: (b & c) | (~b & d)
        index_func = lambda i: i

        tarr1 = ([init[0], init[3], init[2], init[1]] + state1)[i:i+4]
        tarr2 = ([init2[0], init2[3], init2[2], init2[1]] + state2)[i:i+4]

        F1 = func(tarr1[-1], tarr1[-2], tarr1[-3])
        F2 = func(tarr2[-1], tarr2[-2], tarr2[-3])

        G = index_func(i)

        tr1 = left_rotate((state1[i] - tarr1[-1]) & 0xFFFFFFFF, 32 - rotate_amounts[i])
        tr2 = left_rotate((state2[i] - tarr2[-1]) & 0xFFFFFFFF, 32 - rotate_amounts[i])

        m1 = (tr1 - tarr1[0] - F1 - constants[i]) & 0xFFFFFFFF
        m2 = (tr2 - tarr2[0] - F2 - constants[i]) & 0xFFFFFFFF

        assert m1 ^ m2 == 0
        if m[G] is not None:
            assert m[G] == m1
        else:
            m[G] = m1

    return m

# Find the second block based on the section 5.2 of https://eprint.iacr.org/2008/391.pdf
def find_second_block(start):
    for t in range(16384):
        # Step 1: Randomly set q_1 ~ q_16
        state1 = [random.getrandbits(31) | (1 << 31) for _ in range(16)]

        # q_8: ******^* ******** ******** ^****^*+
        for i in [6, 24, 29]:
            state1[7] &= 0xFFFFFFFF - (1 << i)
            state1[7] |= ((state1[6] >> i) & 1) << i

        # q_9:  00000000 00000000 00000000 0000000+
        # q_10: 11111111 11111111 11111111 1111111+
        state1[9] = 1 << 31
        state1[10] = 0xFFFFFFFF
        state2 = [ state1[i] & 0x7FFFFFFF for i in range(16) ]

        try:
            m = recalculate_m(state1, state2, start)
        except AssertionError:
            continue

        state1 += [None] * 48
        state2 += [None] * 48

        # Step 2: Compute q_17 ~ q_24
        flag = True
        for i in range(16, 24):
            F1 = functions_mod[i](state1[i - 1], state1[i - 2], state1[i - 3])
            F2 = functions_mod[i](state2[i - 1], state2[i - 2], state2[i - 3])
            G = index_functions[i](i)

            to_rotate1 = state1[i - 4] + F1 + constants[i] + m[G]
            to_rotate2 = state2[i - 4] + F2 + constants[i] + m[G]

            state1[i] = (state1[i - 1] + left_rotate(to_rotate1, rotate_amounts[i])) & 0xFFFFFFFF
            state2[i] = (state2[i - 1] + left_rotate(to_rotate2, rotate_amounts[i])) & 0xFFFFFFFF

            if state1[i] ^ state2[i] != 0x80000000:
                flag = False
                break 

        if not flag:
            continue

        # Step 3 & 4
        # Usually this is enough. Theoretically it should be 2 ** 31
        for it in trange(2 ** 24):
            state1[8], state2[8] = (1 << 31) | it, it

            # Q9 tunnel
            for i in [8, 9, 12]:
                F = functions_mod[i](state1[i - 1], state1[i - 2], state1[i - 3])
                tr = left_rotate((state1[i] - state1[i - 1]) & 0xFFFFFFFF, 32 - rotate_amounts[i])
                m[i] = (tr - state1[i - 4] - F - constants[i]) & 0xFFFFFFFF
            
            flag = True
            for i in range(24, 64):
                F1 = functions_mod[i](state1[i - 1], state1[i - 2], state1[i - 3])
                F2 = functions_mod[i](state2[i - 1], state2[i - 2], state2[i - 3])
                G = index_functions[i](i)

                to_rotate1 = state1[i - 4] + F1 + constants[i] + m[G]
                to_rotate2 = state2[i - 4] + F2 + constants[i] + m[G]

                state1[i] = (state1[i - 1] + left_rotate(to_rotate1, rotate_amounts[i])) & 0xFFFFFFFF
                state2[i] = (state2[i - 1] + left_rotate(to_rotate2, rotate_amounts[i])) & 0xFFFFFFFF

                if state1[i] ^ state2[i] != 0x80000000:
                    flag = False
                    break 
            
            if not flag:
                continue
            
            print("FOUND")
            print(', '.join(hex(v) for v in m))

            return m

with open('first.txt', 'r') as f:
    lines = f.read().strip().split('\n')

for line in lines:
    first_block = literal_eval(line)
    state, _ = md5_mod(b''.join(v.to_bytes(4, 'little') for v in first_block))
    second_block = find_second_block(state)    

    if second_block:
        m1 = b''.join(v.to_bytes(4, 'little') for v in first_block + second_block)
        state1, _ = md5_mod(m1)

        first_block[8] ^= 1 << 31
        m2 = b''.join(v.to_bytes(4, 'little') for v in first_block + second_block)
        state2, _ = md5_mod(m2)

        assert state1 == state2

        with open('second.txt', 'a') as f:
            f.write(m1.hex() + '\n')
            f.write(m2.hex() + '\n')
