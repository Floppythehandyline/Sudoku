from __future__ import annotations
import sys
from typing import Optional, Tuple
import numpy as np

def puzzle_to_array(p) -> np.ndarray:
    # Normalize various dokusan puzzle representations into a flat int array.
    try:
        arr = np.array(p)
        if arr.size == 81 and arr.dtype != object:
            return arr.astype(int).flatten()
    except Exception:
        pass

    if isinstance(p, str):
        chars = list(p)
        chars = ["0" if c in ". " else c for c in chars]
        return np.array(chars, dtype=int)

    try:
        flat = list(p)
        flat_flat = []
        for x in flat:
            if isinstance(x, (list, tuple, np.ndarray)):
                flat_flat.extend(list(x))
            else:
                flat_flat.append(x)
        if len(flat_flat) == 81:
            flat_flat = ["0" if (isinstance(x, str) and x in ". ") else x for x in flat_flat]
            return np.array(flat_flat, dtype=int)
    except Exception:
        pass

    for attr in ("board", "to_list", "to_array", "as_list", "as_array", "rows", "cells", "grid"):
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
                    flat_flat = ["0" if (isinstance(x, str) and x in ". ") else x for x in flat_flat]
                    return np.array(flat_flat, dtype=int)
            except Exception:
                continue

    s = str(p)
    chars = [c for c in s if c.isdigit() or c in ". "]
    if len(chars) >= 81:
        chars = chars[:81]
        chars = ["0" if c in '. ' else c for c in chars]
        return np.array(chars, dtype=int)

    raise ValueError(f"unrecognized puzzle format or wrong size: {type(p)}")


class Sudoku:
    SIZE = 9

    def __init__(self, board: np.ndarray):
        board = np.array(board)
        if board.size != 81:
            raise ValueError("board must contain 81 elements")
        self.board = board.reshape((9, 9)).astype(int)
        # เพิ่มตัวแปรเพื่อนับจำนวนการ Backtracks
        self.backtracks = 0

    @classmethod
    def from_dokusan(cls, p) -> "Sudoku":
        arr = puzzle_to_array(p)
        return cls(arr)

    def show(self) -> None:
        for r_index, row in enumerate(self.board):
            line = ""
            for c_index, val in enumerate(row):
                line += f" {val} "
                if (c_index + 1) % 3 == 0 and (c_index + 1) != self.SIZE:
                    line += "|"
            print(line)
            if (r_index + 1) % 3 == 0 and (r_index + 1) != self.SIZE:
                print("-" * (self.SIZE * 3 + 2))

    def validate(self, row: int, col: int, num: int) -> bool:
        # Row / column
        for i in range(self.SIZE):
            if self.board[row][i] == num:
                return False
            if self.board[i][col] == num:
                return False
        # 3x3 box
        x0 = (col // 3) * 3
        y0 = (row // 3) * 3
        for i in range(3):
            for j in range(3):
                if self.board[y0 + i][x0 + j] == num:
                    return False
        return True

    def find_empty(self) -> Optional[Tuple[int, int]]:
        """หาช่องว่างช่องแรกที่เจอ (Standard Backtracking)"""
        for r in range(self.SIZE):
            for c in range(self.SIZE):
                if self.board[r][c] == 0:
                    return (r, c)
        return None

    def count_valid_moves(self, row: int, col: int) -> int:
        """นับจำนวนตัวเลขที่เป็นไปได้ที่จะใส่ในช่องนั้นๆ (ใช้สำหรับ MRV)"""
        count = 0
        for n in range(1, 10):
            if self.validate(row, col, n):
                count += 1
        return count

    def find_empty_mrv(self) -> Optional[Tuple[int, int]]:
        """หาช่องว่างโดยใช้ Minimum Remaining Values (MRV) Heuristic"""
        min_moves = 10
        best_cell = None
        
        for r in range(self.SIZE):
            for c in range(self.SIZE):
                if self.board[r][c] == 0:
                    valid_moves = self.count_valid_moves(r, c)
                    if valid_moves < min_moves:
                        min_moves = valid_moves
                        best_cell = (r, c)
                        # Optimization: ถ้ามีแค่ 1 ค่าที่เป็นไปได้ เลือกช่องนี้ได้เลยทันที (Early Exit)
                        if min_moves == 1 or min_moves == 0:
                            return best_cell
        return best_cell

    def solve(self, use_mrv: bool = False) -> bool:
        # เลือกว่าจะใช้ MRV หรือแบบค้นหาปกติ
        empty = self.find_empty_mrv() if use_mrv else self.find_empty()
        
        if not empty:
            return True
        
        row, col = empty
        for n in range(1, 10):
            if self.validate(row, col, n):
                self.board[row][col] = n
                if self.solve(use_mrv):
                    return True
                
                # หากลงค่านี้แล้วไปต่อไม่ได้ ต้องย้อนกลับ (Backtrack)
                self.board[row][col] = 0
                self.backtracks += 1  # นับจำนวนการ Backtrack
                
        return False


LEVELS = {
    "easy": 30,
    "medium": 200,
    "hard": 700,
    "expert": 1000,
    "master": 1200,
    "hackerman": 1500,
    "god": 2000,
}


def _generate_and_solve(level: str = "medium", avg_rank: Optional[int] = None) -> int:
    try:
        from dokusan import generators
    except Exception:
        print("dokusan not available — install with: python -m pip install dokusan")
        raise

    if avg_rank is None:
        avg_rank = LEVELS.get(level, LEVELS["medium"])

    # สร้างปริศนา
    puzzle = generators.random_sudoku(avg_rank=avg_rank)
    arr = puzzle_to_array(puzzle)
    
    print(f"Initial puzzle (level={level}, avg_rank={avg_rank}):")
    sod_display = Sudoku(arr.copy())
    sod_display.show()

    # ทดสอบที่ 1: การค้นหาโดยไม่ใช้ Heuristic
    print("\n[1] Solving without Heuristic (Standard Backtracking)...")
    sod_standard = Sudoku(arr.copy())
    solved_standard = sod_standard.solve(use_mrv=False)
    print(f"-> Standard Backtracks count: {sod_standard.backtracks}")

    # ทดสอบที่ 2: การค้นหาโดยใช้ MRV Heuristic
    print("\n[2] Solving with Heuristic (MRV)...")
    sod_mrv = Sudoku(arr.copy())
    solved_mrv = sod_mrv.solve(use_mrv=True)
    print(f"-> MRV Backtracks count: {sod_mrv.backtracks}")

    if solved_mrv:
        print("\nSolved puzzle:")
        sod_mrv.show()
    else:
        print("\nNo solution found")
        
    return 0 if solved_mrv else 1


def select_level() -> str:
    print("=" * 50)
    print("Welcome to Sudoku Solver (with MRV Analysis)!")
    print("=" * 50)
    print("\nSelect difficulty level:")
    print("  1. Easy")
    print("  2. Medium")
    print("  3. Hard")
    print("  4. Expert")
    print("  5. Master")
    print("  6. Hackerman")
    print("  7. God")
    print()
    while True:
        choice = input("Enter choice (1/2/3/4/5/6/7) or 'q' to quit: ").strip().lower()
        if choice == "q":
            sys.exit(0)
        if choice == "1": return "easy"
        elif choice == "2": return "medium"
        elif choice == "3": return "hard"
        elif choice == "4": return "expert"
        elif choice == "5": return "master"
        elif choice == "6": return "hackerman"
        elif choice == "7": return "god"
        else:
            print("Invalid choice. Please enter 1, 2, 3, 4, 5, 6, 7, or 'q'.")


if __name__ == "__main__":
    try:
        while True:
            level = select_level()
            _generate_and_solve(level=level)
            print("\n" + "=" * 50)
            play_again = input("Play again? (y/n): ").strip().lower()
            if play_again != "y":
                print("Thanks for playing!")
                sys.exit(0)
    except Exception:
        sys.exit(2)