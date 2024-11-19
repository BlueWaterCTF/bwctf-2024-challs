from tqdm import trange
import math

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

####################################################################################################
# Step 1: Extract q_i's from the collision pair given from https://eprint.iacr.org/2008/391.pdf
####################################################################################################

msg = [
    0x68106ac6, 0x2094ed6b, 0xa3ec34eb, 0xf4383dff, 0x157fe4d, 0xeff04e4e, 0x1119f00b, 0x22172e32,
    0xc55102b0, 0x99355658, 0x97874ee2, 0x2c408161, 0xf55b1a3f, 0x31e6ad3c, 0x6ed9a43b, 0x4116f7b6,
    0xec434329, 0xccab7e9a, 0x32b86260, 0x82c53b56, 0xad5ff512, 0xedeab6b5, 0x3e2c15ea, 0x4a564948,
    0x292cf96c, 0x684ad345, 0x63cb649d, 0xc2b7e49e, 0xa7cfd089, 0x127c0548, 0xc2906aa4, 0x66e94d25
]

msg_bytes = b''.join(v.to_bytes(4, 'little') for v in msg)
_, q1 = md5_orig(msg_bytes)

msg[8] ^= (1 << 31)
msg_bytes = b''.join(v.to_bytes(4, 'little') for v in msg)
_, q2 = md5_orig(msg_bytes)

# Extracted q1 ~ q24, which will be reused to run step 9~11 of https://eprint.iacr.org/2008/391.pdf
state1 = q1[:24] + [None] * 40
state2 = q2[:24] + [None] * 40

####################################################################################################
# Step 2: Re-run step 9~11 of https://eprint.iacr.org/2008/391.pdf, with the modified MD5 function
####################################################################################################

path_5_t = '****0000 00*00000 00000000 0000****'.replace(' ', '')
path_6_t = '00001111 11011111 11111111 11110000'.replace(' ', '')
path_10_t = '00000*+0 000*00*0 0*0*000* 00001*00'.replace(' ', '')
path_11_t = '11111*+1 11101101 10101110 11111^11'.replace(' ', '')

# Based on the Q4 and Q9 tunnel
# NOTE: What is a tunnel? Check this: https://eprint.iacr.org/2006/105.pdf
free_bits_b1 = [ i for i in range(32) if path_5_t[i] == '0' and path_6_t[i] == '1' ]
fixed_bits_b1 = [ i for i in range(32) if i not in free_bits_b1 ]
free_bits_a3 = [ i for i in range(32) if path_10_t[i] == '0' and path_11_t[i] == '1' ]
fixed_bits_a3 = [ i for i in range(32) if i not in free_bits_a3 ]

# Recalculate the message blocks from the given states
def recalculate_m(state1, state2):
    m = [None for _ in range(16)]

    for i in range(16):
        func = lambda b, c, d: (b & c) | (~b & d)
        index_func = lambda i: i

        tarr1 = ([init_values[0], init_values[3], init_values[2], init_values[1]] + state1)[i:i+4]
        tarr2 = ([init_values[0], init_values[3], init_values[2], init_values[1]] + state2)[i:i+4]

        F1 = func(tarr1[-1], tarr1[-2], tarr1[-3])
        F2 = func(tarr2[-1], tarr2[-2], tarr2[-3])
        G = index_func(i)

        tr1 = left_rotate((state1[i] - tarr1[-1]) & 0xFFFFFFFF, 32 - rotate_amounts[i])
        tr2 = left_rotate((state2[i] - tarr2[-1]) & 0xFFFFFFFF, 32 - rotate_amounts[i])

        m1 = (tr1 - tarr1[0] - F1 - constants[i]) & 0xFFFFFFFF
        m2 = (tr2 - tarr2[0] - F2 - constants[i]) & 0xFFFFFFFF

        assert m1 ^ m2 == (0 if G != 8 else 0x80000000)
        if m[G] is not None:
            assert m[G] == m1
        else:
            m[G] = m1

    return m

def check_differential(diff, idx, state1, state2):
    diff = diff.replace(' ', '')

    for i in range(32):
        if diff[i] == '+':
            if (state1[idx] >> i) & 1 != 0 or (state2[idx] >> i) & 1 != 1:
                return False
            continue
        elif diff[i] == '-':
            if (state1[idx] >> i) & 1 != 1 or (state2[idx] >> i) & 1 != 0:
                return False
            continue
        elif diff[i] == 'd':
            if (state1[idx] >> i) & 1 == (state2[idx] >> i) & 1:
                return False
            continue

        if (state1[idx] >> i) & 1 != (state2[idx] >> i) & 1:
            return False

        if diff[i] == '0':
            if (state1[idx] >> i) & 1 != 0:
                return False
        elif diff[i] == '1':
            if (state1[idx] >> i) & 1 != 1:
                return False
        elif diff[i] == '^':
            if (state1[idx] >> i) & 1 != (state1[idx - 1] >> i) & 1:
                return False

    return True

# Step 10-11 of Section 5.1
def brute_a3(state1, state2):
    # Deepcopy the states
    state1, state2 = state1[:], state2[:]

    # Collect the fixed bits of a3
    a3_base1, a3_base2 = 0, 0
    for i in fixed_bits_a3:
        a3_base1 |= ((state1[8] >> i) & 1) << i
        a3_base2 |= ((state2[8] >> i) & 1) << i

    # Recalculate the message blocks
    m = recalculate_m(state1, state2)

    for it in trange(2 ** len(free_bits_a3)):
        # Set q_9
        v1, v2 = a3_base1, a3_base2
        for i in range(len(free_bits_a3)):
            v1 |= ((it >> i) & 1) << free_bits_a3[i]
            v2 |= ((it >> i) & 1) << free_bits_a3[i]
        state1[8], state2[8] = v1, v2

        # Recalculate m8, m9 and m12 (Q9 tunnel)
        for i in [8, 9, 12]:
            F = functions_mod[i](state1[i - 1], state1[i - 2], state1[i - 3])
            tr = left_rotate((state1[i] - state1[i - 1]) & 0xFFFFFFFF, 32 - rotate_amounts[i])
            m[i] = (tr - state1[i - 4] - F - constants[i]) & 0xFFFFFFFF

        # Differential path from q_25 to q_64
        diffs = [
            "***^**** ******** *0****** ********",
            "******** ******** *1****** *****^^*",
            "******** ******** *+****** ********",
            "******** ******** ******** ********",
            "******** ******** *^****** *******0",
            "******** ******** ******** ********",
        ]

        # In the original paper, it should be '-' on q31~55, 57, 59, 61, 63
        # and '+' on q56, 58, 60, 62, 64.
        # However, the given example in the paper does not follow this :(
        diffs += ["******** ******** ******** *******d" for _ in range(34)]

        flag = True
        for i in range(24, 64):
            F1 = functions_mod[i](state1[i - 1], state1[i - 2], state1[i - 3])
            F2 = functions_mod[i](state2[i - 1], state2[i - 2], state2[i - 3])
            G = index_functions[i](i)

            to_rotate1 = state1[i - 4] + F1 + constants[i] + m[G]
            to_rotate2 = state2[i - 4] + F2 + constants[i] + (m[G] ^ 0x80000000 if G == 8 else m[G])

            # Additional conditions described on the section 4.4
            if i == 24: # \Sigma a7,26 = 1
                if (to_rotate1 >> 26) & 1 != 1:
                    flag = False
                    break
            elif i == 26: # \Sigma c7,3~17 = 0
                if (to_rotate1 >> 3) & 0b111111111111111 == 0b111111111111111:
                    flag = False
                    break
            elif i == 27: # \Sigma b7,29~31 = 1
                if (to_rotate1 >> 29) & 0b111 == 0b000:
                    flag = False
                    break
            elif i == 29:  # \Sigma c8, 17 = 0
                if (to_rotate1 >> 17) & 1 == 1:
                    flag = False
                    break

            state1[i] = (state1[i - 1] + left_rotate(to_rotate1, rotate_amounts[i])) & 0xFFFFFFFF
            state2[i] = (state2[i - 1] + left_rotate(to_rotate2, rotate_amounts[i])) & 0xFFFFFFFF

            if not check_differential(diffs[i - 24], i, state1, state2):
                flag = False
                break

        if not flag:
            continue
        
        print("FOUND")
        print(', '.join(hex(v) for v in m))

        with open('first.txt', 'a') as f:
            f.write('[' + ', '.join(hex(v) for v in m) + ']\n')


# Step 9 of Section 5.1
def brute_b1(state1, state2):
    # Deepcopy the states
    state1, state2 = state1[:], state2[:]

    # Collect the fixed bits of b1
    b1_base1, b1_base2 = 0, 0
    for i in fixed_bits_b1:
        b1_base1 |= ((state1[3] >> i) & 1) << i
        b1_base2 |= ((state2[3] >> i) & 1) << i

    for it in trange(2 ** len(free_bits_b1)):
        v1, v2 = b1_base1, b1_base2
        for i in range(len(free_bits_b1)):
            v1 |= ((it >> i) & 1) << free_bits_b1[i]
            v2 |= ((it >> i) & 1) << free_bits_b1[i]

        state1[3], state2[3] = v1, v2

        # Recalculate m4
        F = functions_mod[4](state1[3], state1[2], state1[1])
        tr = left_rotate((state1[4] - state1[3]) & 0xFFFFFFFF, 32 - rotate_amounts[4])
        m4 = (tr - state1[0] - F - constants[4]) & 0xFFFFFFFF

        # Recalculate b6
        F1 = functions_mod[23](state1[22], state1[21], state1[20])
        F2 = functions_mod[23](state2[22], state2[21], state2[20])
        tr1 = state1[19] + F1 + constants[23] + m4
        tr2 = state2[19] + F2 + constants[23] + m4

        # Check the condition \Sigma b6,9~11 != 101 from the section 4.4
        if (tr1 >> 9) & 0b111 == 0b101:
            continue
        
        state1[23] = (state1[22] + left_rotate(tr1, rotate_amounts[23])) & 0xFFFFFFFF
        state2[23] = (state2[22] + left_rotate(tr2, rotate_amounts[23])) & 0xFFFFFFFF

        if not check_differential("******** ******** ******** *****++*", 23, state1, state2):
            continue

        brute_a3(state1, state2)

brute_b1(state1, state2)
