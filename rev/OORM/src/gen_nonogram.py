from z3 import *
import random

BSIZE = 40

def print_board(board):
    height, width = len(board), len(board[0])

    for i in range(height):
        s = ""
        for j in range(width):
            s += str(board[i][j]) + " "
        print(s)

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

def gen(height, width, seed=None):
    if seed is not None:
        random.seed(seed)
    
    board = [[ None for j in range(width) ] for i in range(height)]

    for i in range(height):
        for j in range(width):
            pool = [0, 0, 1, 1, 1]

            if i > 0 and board[i - 1][j] != 0:
                pool += [board[i - 1][j]] * 2
            if j > 0 and board[i][j - 1] != 0:
                pool += [board[i][j - 1]] * 2
            
            board[i][j] = random.choice(pool)

    row_hint, col_hint = gen_hint(board)
    return board, row_hint, col_hint

def solve(size, row_hint, col_hint):
    height, width = size

    X = [ [ Int("X_{}_{}".format(i, j)) for j in range(width) ] for i in range(height)]
    R = [ [ ( Int("Rstart_{}_{}".format(i, j)), Int("Rend_{}_{}".format(i, j)) ) for j in range(len(row_hint[i])) ] for i in range(height) ]
    C = [ [ ( Int("Cstart_{}_{}".format(i, j)), Int("Cend_{}_{}".format(i, j)) ) for j in range(len(col_hint[i])) ] for i in range(width) ]
    sol = Solver()

    for i in range(height):
        for j in range(len(row_hint[i])):
            sol.add( And(0 <= R[i][j][0], R[i][j][0] < width) )
            sol.add( And(0 <= R[i][j][1], R[i][j][1] < width) )
            sol.add( R[i][j][1] == R[i][j][0] + row_hint[i][j] - 1)
        
        for j in range(len(row_hint[i]) - 1):
            sol.add( R[i][j][1] + 1 < R[i][j + 1][0] )
        
        for j in range(width):
            zero_cond = True
            for k in range(len(row_hint[i])):
                sol.add( If( And(R[i][k][0] <= j, j <= R[i][k][1]), X[i][j] == 1, True) )
                zero_cond = And(zero_cond, Not(And(R[i][k][0] <= j, j <= R[i][k][1])))
            sol.add( If(zero_cond, X[i][j] == 0, True) )
    
    for i in range(width):
        for j in range(len(col_hint[i])):
            sol.add( And(0 <= C[i][j][0], C[i][j][0] < height) )
            sol.add( And(0 <= C[i][j][1], C[i][j][1] < height) )
            sol.add( C[i][j][1] == C[i][j][0] + col_hint[i][j] - 1)
        
        for j in range(len(col_hint[i]) - 1):
            sol.add( C[i][j][1] + 1 < C[i][j + 1][0] )
        
        for j in range(height):
            zero_cond = True
            for k in range(len(col_hint[i])):
                sol.add( If( And(C[i][k][0] <= j, j <= C[i][k][1]), X[j][i] == 1, True) )
                zero_cond = And(zero_cond, Not(And(C[i][k][0] <= j, j <= C[i][k][1])))
            sol.add( If(zero_cond, X[j][i] == 0, True) )
    
    sol_count = 0
    solutions = []

    while sol_count <= 100 and sol.check() == sat:
        model = sol.model()
        board = [ [ model[X[i][j]].as_long() for j in range(width) ] for i in range(height) ]

        solutions.append(board)
        sol_count += 1

        cond = True
        for i in range(height):
            for j in range(width):
                cond = And(cond, X[i][j] == board[i][j])
        
        sol.add(Not(cond))
    
    return sol_count, solutions

# For board generation
while True:
    board, row_hint, col_hint = gen(BSIZE, BSIZE)
    sol_count, solutions = solve((BSIZE, BSIZE), row_hint, col_hint)
    
    if sol_count == 1:
        for r1, r2 in zip(board, solutions[0]):
            assert r1 == r2
        break

print_board(board)
