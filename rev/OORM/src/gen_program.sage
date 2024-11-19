from tqdm import trange
import random

BSIZE = 20

def gen_hint(board):
    height, width = len(board), len(board[0])

    row_hint = [ [] for i in range(height) ]
    for i in range(height):
        count = 0
        for j in range(width):
            if board[i][j]:
                count += 1
            else:
                if count:
                    row_hint[i].append(count)
                count = 0
        
        if count:
            row_hint[i].append(count)

    col_hint = [ [] for i in range(width) ]
    for i in range(width):
        count = 0
        for j in range(height):
            if board[j][i]:
                count += 1
            else:
                if count:
                    col_hint[i].append(count)
                count = 0
        
        if count:
            col_hint[i].append(count)

    return row_hint, col_hint

def load_board():
    with open('board.txt', 'r') as f:
        data = f.read()

    board = []
    for line in data.split('\n'):
        arr = []
        for value in line.split(' '):
            if len(value) > 0:
                arr.append(int(value))
            if len(arr) == BSIZE:
                break
        board.append(arr)
        if len(board) == BSIZE:
            break
        
    row_hint, col_hint = gen_hint(board)

    return board, row_hint, col_hint

##########################################################################

board, row_hint, col_hint = load_board()

number_to_cell = [ (i, j) for j in range(BSIZE) for i in range(BSIZE) ]
# random.shuffle(number_to_cell)
cell_to_number = { cell: num for num, cell in enumerate(number_to_cell) }

row_in_and_outs = [ [ [] for j in range(BSIZE) ] for i in range(BSIZE) ]
row_start_end = []
col_in_and_outs = [ [ [] for j in range(BSIZE) ] for i in range(BSIZE) ]
col_start_end = []

tag_pool = list(range(1, 2 ** 15))

for i in trange(BSIZE):
    hint = row_hint[i]
    states = []
    for j in range(len(hint)):
        states += [ (j, k) for k in range(0, hint[j] + 1) ]
    states.append( (len(hint), 0) ) # The end
    states.append( None ) # Fail

    
    prev_state_nums = random.sample(tag_pool, len(states))
    start_value = prev_state_nums[0]

    for j in range(BSIZE):
        state_nums = random.sample(tag_pool, len(states))

        for k, v in enumerate(states):
            inp = prev_state_nums[k]
            if v is None:
                out = state_nums[k]

                row_in_and_outs[i][j] += [
                    (inp, 0, out),
                    (inp, 1, out)
                ]
            elif v[-1] == 0:
                out0 = state_nums[k]
                out1 = state_nums[k + 1]

                row_in_and_outs[i][j] += [
                    (inp, 0, out0),
                    (inp, 1, out1)
                ]
            else:
                if states[k + 1] == (v[0], v[1] + 1):
                    out0 = state_nums[-1] # Fail
                    out1 = state_nums[k + 1]
                    row_in_and_outs[i][j] += [
                        (inp, 0, out0),
                        (inp, 1, out1)
                    ]
                else:
                    out0 = state_nums[k + 1]
                    out1 = state_nums[-1] # Fail
                    row_in_and_outs[i][j] += [
                        (inp, 0, out0),
                        (inp, 1, out1)
                    ]
        
        prev_state_nums = state_nums
    
    end_value = (prev_state_nums[-3], prev_state_nums[-2])
    row_start_end.append((start_value, end_value))

for i in trange(BSIZE):
    hint = col_hint[i]
    states = []
    for j in range(len(hint)):
        states += [ (j, k) for k in range(0, hint[j] + 1) ]
    states.append( (len(hint), 0) ) # The end
    states.append( None ) # Fail

    prev_state_nums = random.sample(tag_pool, len(states))
    start_value = prev_state_nums[0]

    for j in range(BSIZE):
        state_nums = random.sample(tag_pool, len(states))

        for k, v in enumerate(states):
            inp = prev_state_nums[k]
            if v is None:
                out = state_nums[k]

                col_in_and_outs[j][i] += [
                    (inp, 0, out),
                    (inp, 1, out)
                ]
            elif v[-1] == 0:
                out0 = state_nums[k]
                out1 = state_nums[k + 1]

                col_in_and_outs[j][i] += [
                    (inp, 0, out0),
                    (inp, 1, out1)
                ]
            else:
                if states[k + 1] == (v[0], v[1] + 1):
                    out0 = state_nums[-1] # Fail
                    out1 = state_nums[k + 1]
                    col_in_and_outs[j][i] += [
                        (inp, 0, out0),
                        (inp, 1, out1)
                    ]
                else:
                    out0 = state_nums[k + 1]
                    out1 = state_nums[-1] # Fail
                    col_in_and_outs[j][i] += [
                        (inp, 0, out0),
                        (inp, 1, out1)
                    ]
        
        prev_state_nums = state_nums
    
    end_value = (prev_state_nums[-3], prev_state_nums[-2])
    col_start_end.append((start_value, end_value))

print("Randomize done")

##########################################################################

with open('template.c', 'r') as f:
    template = f.read()

# Setup constructors

template = template.replace('#define BSIZE', f'#define BSIZE {BSIZE}')
template = template.replace('%400s', f'%{BSIZE * BSIZE // 4}s')

code = ""
for i in range(BSIZE):
    num = cell_to_number[(i, 0)]
    val = row_start_end[i][0]
    code += f"    row_values[{num}] = {val};\n"

for i in range(BSIZE):
    num = cell_to_number[(0, i)]
    val = col_start_end[i][0]
    code += f"    col_values[{num}] = {val};\n"

template = template.replace('// NOTE: START_VALUES', code)

code = ""
for i in range(BSIZE ** 2):
    code += f"    row_func_{i},\n"
template = template.replace('// NOTE: ROW_FUNC_PTRS', code)

code = ""
for i in range(BSIZE ** 2):
    code += f"    col_func_{i},\n"
template = template.replace('// NOTE: COL_FUNC_PTRS', code)

print("Code init part done")

##########################################################################

# Setup functions

code, template_end = template.split('// NOTE: FUNCS\n')

P.<x> = PolynomialRing(GF(2 ** 16 + 1))

for i in trange(BSIZE ** 2):
    x, y = number_to_cell[i]
    points = [ ((i1 << 1) | i2, o) for i1, i2, o in row_in_and_outs[x][y] ]
    f = P.lagrange_polynomial(points)
    coefs = f.coefficients(sparse=False)

    code += f"void row_func_{i}(uint64_t inp1, uint64_t inp2) {{\n"
    code += f"    uint64_t x = (inp1 << 1) | inp2, out = {coefs[0]};\n"
    code += f"    uint64_t t = x;\n"

    for c in coefs[1:]:
        code += f"    out = (out + {c} * t) % 65537;\n"
        code += f"    t = (t * x) % 65537;\n"
    
    if y == BSIZE - 1:
        v1, v2 = row_start_end[x][1]
        code += f"    if (out == {v1} || out == {v2})\n"
        code += f"        answer_count++;\n"
    else:
        nxt = cell_to_number[(x, y + 1)]
        code += f"    row_values[{nxt}] = out;\n"

    code += "}\n"

for i in trange(BSIZE ** 2):
    x, y = number_to_cell[i]
    points = [ ((i1 << 1) | i2, o) for i1, i2, o in col_in_and_outs[x][y] ]
    f = P.lagrange_polynomial(points)
    coefs = f.coefficients(sparse=False)

    code += f"void col_func_{i}(uint64_t inp1, uint64_t inp2) {{\n"
    code += f"    uint64_t x = (inp1 << 1) | inp2, out = {coefs[0]};\n"
    code += f"    uint64_t t = x;\n"

    for c in coefs[1:]:
        code += f"    out = (out + {c} * t) % 65537;\n"
        code += f"    t = (t * x) % 65537;\n"
    
    if x == BSIZE - 1:
        v1, v2 = col_start_end[y][1]
        code += f"    if (out == {v1} || out == {v2})\n"
        code += f"        answer_count++;\n"
    else:
        nxt = cell_to_number[(x + 1, y)]
        code += f"    col_values[{nxt}] = out;\n"

    code += "}\n"

code += template_end

with open('main.c', 'w') as f:
    f.write(code)

del code

print("Code func part done")

##########################################################################

# Answer generation

answer = ''

v = 0
for i in range(BSIZE ** 2):
    x, y = number_to_cell[i]
    v |= board[x][y] << (i % 4)

    if i % 4 == 3:
        answer += f"{v:x}"
        v = 0

with open('answer.txt', 'w') as f:
    f.write(answer)

print("Answer gen done")