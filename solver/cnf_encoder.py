"""
CNF Encoder for Griductive clues.
Converts high-level clues and knowledge into standard CNF (DIMACS format list of lists of integers).
Uses deterministic variable mapping and supports primary & auxiliary variables.
Pure Python implementation with NO external SAT solvers.
"""
import itertools
from typing import Dict, List, Optional, Set, Tuple
from core.models import Clue, ClueType, PublicKnowledgeState, Role
from core.regions import rc_from_cell_id


class CNFEncoder:
    def __init__(self, size: int):
        self.size = size
        self.total_cells = size * size
        self._next_aux_var = self.total_cells + 1

    def cell_to_var(self, cell_id: str) -> int:
        """
        Maps a cell_id ('A1', 'C2', etc.) to a 1-based variable index in row-major order.
        1 to size*size.
        """
        r, c = rc_from_cell_id(cell_id)
        if not (0 <= r < self.size and 0 <= c < self.size):
            raise ValueError(f"Cell ID {cell_id} out of bounds for size {self.size}")
        return r * self.size + c + 1

    def var_to_cell(self, var: int) -> str:
        """Inverse mapping: variable index to cell_id."""
        if not (1 <= var <= self.total_cells):
            raise ValueError(f"Variable {var} is not a primary cell variable")
        idx = var - 1
        r = idx // self.size
        c = idx % self.size
        col_letter = chr(ord('A') + c)
        return f"{col_letter}{r + 1}"

    def new_aux_var(self) -> int:
        """Allocates a new auxiliary variable starting from size*size + 1."""
        var = self._next_aux_var
        self._next_aux_var += 1
        return var

    @property
    def aux_var_count(self) -> int:
        return self._next_aux_var - (self.total_cells + 1)

    def encode_fact(self, cell_id: str, role: Role) -> List[List[int]]:
        """
        FACT(i, role):
        - CRIMINAL -> [[+v_i]]
        - INNOCENT -> [[-v_i]]
        """
        v = self.cell_to_var(cell_id)
        if role == Role.CRIMINAL:
            return [[v]]
        elif role == Role.INNOCENT:
            return [[-v]]
        else:
            return []

    def encode_same(self, cell_1: str, cell_2: str) -> List[List[int]]:
        """
        SAME(i, j): C_i <-> C_j
        CNF: (not C_i or C_j) and (C_i or not C_j)
        -> [[-v_i, v_j], [v_i, -v_j]]
        """
        v1 = self.cell_to_var(cell_1)
        v2 = self.cell_to_var(cell_2)
        return [[-v1, v2], [v1, -v2]]

    def encode_different(self, cell_1: str, cell_2: str) -> List[List[int]]:
        """
        DIFFERENT(i, j): C_i XOR C_j
        CNF: (not C_i or not C_j) and (C_i or C_j)
        -> [[-v1, -v2], [v1, v2]]
        """
        v1 = self.cell_to_var(cell_1)
        v2 = self.cell_to_var(cell_2)
        return [[-v1, -v2], [v1, v2]]

    def encode_at_least(self, k: int, cells: List[str], target_role: Role = Role.CRIMINAL) -> List[List[int]]:
        """
        AT_LEAST(k, R): sum_{i in R} (cell == target_role) >= k.
        For criminals:
          If k <= 0: [] (always true)
          If k > |R|: [[]] (UNSAT)
          Else: for every combination of size |R| - k + 1, clause of positive literals.
        For innocents:
          Equivalent to AT_MOST(|R| - k, R) for criminals.
        """
        n = len(cells)
        if target_role == Role.INNOCENT:
            return self.encode_at_most(n - k, cells, Role.CRIMINAL)

        if k <= 0:
            return []
        if k > n:
            return [[]]  # Empty clause is UNSAT

        vars_list = [self.cell_to_var(c) for c in cells]
        subset_size = n - k + 1
        clauses = []
        for combo in itertools.combinations(vars_list, subset_size):
            clauses.append(list(combo))
        return clauses

    def encode_at_most(self, k: int, cells: List[str], target_role: Role = Role.CRIMINAL) -> List[List[int]]:
        """
        AT_MOST(k, R): sum_{i in R} (cell == target_role) <= k.
        For criminals:
          If k < 0: [[]] (UNSAT)
          If k >= |R|: [] (always true)
          Else: for every combination of size k + 1, clause of negative literals.
        For innocents:
          Equivalent to AT_LEAST(|R| - k, R) for criminals.
        """
        n = len(cells)
        if target_role == Role.INNOCENT:
            return self.encode_at_least(n - k, cells, Role.CRIMINAL)

        if k < 0:
            return [[]]
        if k >= n:
            return []

        vars_list = [self.cell_to_var(c) for c in cells]
        subset_size = k + 1
        clauses = []
        for combo in itertools.combinations(vars_list, subset_size):
            clauses.append([-v for v in combo])
        return clauses

    def encode_exactly(self, k: int, cells: List[str], target_role: Role = Role.CRIMINAL) -> List[List[int]]:
        """
        EXACTLY(k, R): combination of AT_LEAST(k, R) and AT_MOST(k, R).
        """
        clauses_at_least = self.encode_at_least(k, cells, target_role)
        if [[]] in clauses_at_least:
            return [[]]
        clauses_at_most = self.encode_at_most(k, cells, target_role)
        if [[]] in clauses_at_most:
            return [[]]
        return clauses_at_least + clauses_at_most

    def encode_parity(self, cells: List[str], is_odd: bool, target_role: Role = Role.CRIMINAL) -> List[List[int]]:
        """
        PARITY(R, is_odd): count of target_role cells in R has odd parity if is_odd else even.
        Encoded via canonical CNF (excluding every assignment with invalid parity).
        """
        n = len(cells)
        if n == 0:
            # Empty region has count 0 (even)
            if (0 % 2 == 1) == is_odd:
                return []
            else:
                return [[]]

        # Convert target_role innocent to criminals parity:
        # count_crim = n - count_inno
        effective_odd = is_odd
        if target_role == Role.INNOCENT:
            if n % 2 == 1:
                effective_odd = not is_odd

        vars_list = [self.cell_to_var(c) for c in cells]
        clauses = []
        # Enumerate all 2^n assignments to cells
        for bits in itertools.product([0, 1], repeat=n):
            crim_count = sum(bits)
            is_bits_odd = (crim_count % 2 == 1)
            if is_bits_odd != effective_odd:
                # This assignment is invalid, forbid it:
                clause = [(-v if b == 1 else v) for b, v in zip(bits, vars_list)]
                clauses.append(clause)
        return clauses

    def encode_compare_count(
        self,
        cells_a: List[str],
        cells_b: List[str],
        op: str,
        target_role: Role = Role.CRIMINAL
    ) -> List[List[int]]:
        """
        COMPARE_COUNT(R_A, R_B, op): count(R_A) op count(R_B).
        Simplifies disjoint parts: common cells cancel out.
        Generates canonical CNF clauses forbidding invalid assignments on distinct cells.
        """
        set_a = set(cells_a)
        set_b = set(cells_b)
        distinct_a = sorted(list(set_a - set_b))
        distinct_b = sorted(list(set_b - set_a))
        distinct_all = distinct_a + distinct_b

        na = len(distinct_a)
        nb = len(distinct_b)
        n_total = na + nb

        if n_total == 0:
            # Empty comparison: 0 op 0
            res = (0 == 0 if op in ("=", "==") else (0 > 0 if op == ">" else (0 < 0 if op == "<" else True)))
            return [] if res else [[]]

        target_bool = (target_role == Role.CRIMINAL)
        clauses = []

        # Enumerate assignments over distinct_all
        vars_all = [self.cell_to_var(c) for c in distinct_all]
        for bits in itertools.product([0, 1], repeat=n_total):
            bits_a = bits[:na]
            bits_b = bits[na:]

            count_a = sum(1 for b in bits_a if (b == 1) == target_bool)
            count_b = sum(1 for b in bits_b if (b == 1) == target_bool)

            valid = False
            if op in ("=", "=="):
                valid = (count_a == count_b)
            elif op == ">":
                valid = (count_a > count_b)
            elif op == "<":
                valid = (count_a < count_b)
            elif op == ">=":
                valid = (count_a >= count_b)
            elif op == "<=":
                valid = (count_a <= count_b)

            if not valid:
                clause = [(-v if b == 1 else v) for b, v in zip(bits, vars_all)]
                clauses.append(clause)

        return clauses

    def encode_clue(self, clue: Clue) -> List[List[int]]:
        """
        Encodes an arbitrary Clue into a list of CNF clauses.
        """
        ctype = clue.clue_type
        params = clue.params
        target_role = clue.target_role

        if ctype == ClueType.FACT:
            cid = params.get("cell_id", clue.source_cell)
            role = Role(params.get("role", Role.CRIMINAL.value))
            return self.encode_fact(cid, role)

        elif ctype == ClueType.SAME:
            return self.encode_same(params["cell_1"], params["cell_2"])

        elif ctype == ClueType.DIFFERENT:
            return self.encode_different(params["cell_1"], params["cell_2"])

        elif ctype == ClueType.AT_LEAST:
            k = int(params["k"])
            cells = params.get("region_cells", clue.referenced_cells)
            return self.encode_at_least(k, cells, target_role)

        elif ctype == ClueType.AT_MOST:
            k = int(params["k"])
            cells = params.get("region_cells", clue.referenced_cells)
            return self.encode_at_most(k, cells, target_role)

        elif ctype == ClueType.EXACTLY:
            k = int(params["k"])
            cells = params.get("region_cells", clue.referenced_cells)
            return self.encode_exactly(k, cells, target_role)

        elif ctype == ClueType.PARITY:
            is_odd = bool(params.get("is_odd", True))
            cells = params.get("region_cells", clue.referenced_cells)
            return self.encode_parity(cells, is_odd, target_role)

        elif ctype == ClueType.COMPARE_COUNT:
            cells_a = params.get("region_A_cells", [])
            cells_b = params.get("region_B_cells", [])
            op = params.get("op", "=")
            return self.encode_compare_count(cells_a, cells_b, op, target_role)

        else:
            raise ValueError(f"Unknown clue type: {ctype}")

    def build_kb(self, public_state: PublicKnowledgeState) -> List[List[int]]:
        """
        Builds complete CNF Knowledge Base KB_t from:
        - All revealed clues
        - Unit clauses of all currently revealed cells
        """
        kb_clauses: List[List[int]] = []

        # Revealed clues
        for clue in public_state.revealed_clues.values():
            clue_clauses = self.encode_clue(clue)
            kb_clauses.extend(clue_clauses)

        # Revealed cells as unit clauses
        for cid, role in public_state.revealed_cells.items():
            kb_clauses.extend(self.encode_fact(cid, role))

        return kb_clauses
