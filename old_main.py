import numpy as np
from dokusan import generators, stats

puzzle = generators.random_sudoku(avg_rank=200)


def puzzle_to_array(p):
    # If it's already an array-like with 81 elements
    try:
        arr = np.array(p)
        if arr.size == 81 and arr.dtype != object:
            return arr.astype(int).flatten()
    except Exception:
        pass

    # If it's a string of 81 chars
    if isinstance(p, str):
        chars = list(p)
        chars = ['0' if c in '. ' else c for c in chars]
        return np.array(chars, dtype=int)

    # Try converting any iterable (including dokusan.Sudoku which may be iterable)
    try:
        flat = list(p)
        # flatten nested rows if necessary
        flat_flat = []
        for x in flat:
            if isinstance(x, (list, tuple, np.ndarray)):
                flat_flat.extend(list(x))
            else:
                flat_flat.append(x)
        if len(flat_flat) == 81:
            flat_flat = ['0' if (isinstance(x, str) and x in '. ') else x for x in flat_flat]
            return np.array(flat_flat, dtype=int)
    except Exception:
        pass

    # Try common attributes used by board objects
    for attr in ('board', 'to_list', 'to_array', 'as_list', 'as_array', 'rows', 'cells', 'grid'):
        if hasattr(p, attr):
            val = getattr(p, attr)
            try:
                if callable(val):
                    val = val()
                flat = list(val)
                flat_flat = []
                for x in flat:
                    if isinstance(x, (list, tuple, np.ndarray)):
                        flat_flat.extend(list(x))
                    else:
                        flat_flat.append(x)
                if len(flat_flat) == 81:
                    flat_flat = ['0' if (isinstance(x, str) and x in '. ') else x for x in flat_flat]
                    return np.array(flat_flat, dtype=int)
            except Exception:
                continue

    # As a last resort, try extracting digits and dots from stringification
    s = str(p)
    chars = [c for c in s if c.isdigit() or c in '. ']
    if len(chars) >= 81:
        chars = chars[:81]
        chars = ['0' if c in '. ' else c for c in chars]
        return np.array(chars, dtype=int)

    raise ValueError(f'unrecognized puzzle format or wrong size: {type(p)}')


arr = puzzle_to_array(puzzle)
if arr.size != 81:
    raise ValueError(f'Expected 81 elements, got {arr.size}')

matrix = arr.reshape((9, 9))

SIZE = 9

def show_result(matrix):
    for r_index, row in enumerate(matrix):
        string = ""
        for c_index, col in enumerate(row):
            string += " {} ".format(col)
            if (c_index + 1) % 3 == 0 and (c_index + 1) != SIZE:
                string += "|"
        print(string)
        if (r_index + 1) % 3 == 0 and (r_index + 1) != SIZE:
            print("-" * (SIZE * 3 + 2))

print('Initial puzzle:')
show_result(matrix)


def validate(row, col, num):
    global matrix
    for i in range(9):
        if matrix[row][i] == num:
            return False
    for i in range(9):
        if matrix[i][col] == num:
            return False
    x0 = (col // 3) * 3
    y0 = (row // 3) * 3
    for i in range(3):
        for j in range(3):
            if matrix[y0 + i][x0 + j] == num:
                return False
    return True


def solve():
    global matrix
    for row in range(9):
        for col in range(9):
            if matrix[row][col] == 0:
                for number in range(1, 10):
                    if validate(row, col, number):
                        matrix[row][col] = number
                        if solve():
                            return True
                        matrix[row][col] = 0
                return False
    return True


if solve():
    print('\nSolved puzzle:')
    show_result(matrix)
else:
    print('\nNo solution found')
