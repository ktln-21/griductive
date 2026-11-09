"""
Direct Semantic Evaluator for Griductive clues.
Evaluates clues directly on full cell assignments (mapping cell_id -> bool)
without using CNF encoding or SAT solvers.
Used for ground truth verification, cross-validation, and level generation.
"""
from typing import Dict, List
from core.models import Clue, ClueType, Role


def count_role_matches(cells: List[str], target_role: Role, assignment: Dict[str, bool]) -> int:
    """
    Count how many cells in 'cells' have the target_role in 'assignment'.
    assignment: Dict mapping cell_id -> bool (True: CRIMINAL, False: INNOCENT).
    """
    target_bool = (target_role == Role.CRIMINAL)
    return sum(1 for cid in cells if assignment.get(cid) == target_bool)


def evaluate_clue_directly(clue: Clue, assignment: Dict[str, bool]) -> bool:
    """
    Directly evaluate whether a Clue is satisfied by the given complete assignment.
    assignment: Dict[str, bool] where True = CRIMINAL, False = INNOCENT.
    Returns: bool (True if the assignment satisfies the clue, False otherwise).
    """
    ctype = clue.clue_type
    params = clue.params
    target_role = clue.target_role

    if ctype == ClueType.FACT:
        cell_id = params.get("cell_id", clue.source_cell)
        expected_role = Role(params.get("role", Role.CRIMINAL.value))
        expected_bool = (expected_role == Role.CRIMINAL)
        return assignment.get(cell_id) == expected_bool

    elif ctype == ClueType.SAME:
        c1 = params["cell_1"]
        c2 = params["cell_2"]
        return assignment.get(c1) == assignment.get(c2)

    elif ctype == ClueType.DIFFERENT:
        c1 = params["cell_1"]
        c2 = params["cell_2"]
        return assignment.get(c1) != assignment.get(c2)

    elif ctype == ClueType.AT_LEAST:
        k = int(params["k"])
        cells = params.get("region_cells", clue.referenced_cells)
        count = count_role_matches(cells, target_role, assignment)
        return count >= k

    elif ctype == ClueType.AT_MOST:
        k = int(params["k"])
        cells = params.get("region_cells", clue.referenced_cells)
        count = count_role_matches(cells, target_role, assignment)
        return count <= k

    elif ctype == ClueType.EXACTLY:
        k = int(params["k"])
        cells = params.get("region_cells", clue.referenced_cells)
        count = count_role_matches(cells, target_role, assignment)
        return count == k

    elif ctype == ClueType.PARITY:
        is_odd = bool(params.get("is_odd", True))
        cells = params.get("region_cells", clue.referenced_cells)
        count = count_role_matches(cells, target_role, assignment)
        return (count % 2 == 1) == is_odd

    elif ctype == ClueType.COMPARE_COUNT:
        cells_a = params.get("region_A_cells", [])
        cells_b = params.get("region_B_cells", [])
        op = params.get("op", "=")
        count_a = count_role_matches(cells_a, target_role, assignment)
        count_b = count_role_matches(cells_b, target_role, assignment)

        if op in ("=", "=="):
            return count_a == count_b
        elif op == ">":
            return count_a > count_b
        elif op == "<":
            return count_a < count_b
        elif op == ">=":
            return count_a >= count_b
        elif op == "<=":
            return count_a <= count_b
        else:
            raise ValueError(f"Unsupported comparison operator: {op}")

    else:
        raise ValueError(f"Unknown clue type: {ctype}")
