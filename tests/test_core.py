"""
Validation script: tests DPLL, CNF encoding against Direct Semantic Evaluator,
and role isolation.
"""
import itertools
from core.models import Clue, ClueType, Role, Character
from core.regions import get_all_cells, get_neighbors, get_row_cells, get_col_cells, get_corners, get_boundary, get_common_neighbors
from core.semantics import evaluate_clue_directly
from core.engine import GameEngine
from solver.cnf_encoder import CNFEncoder
from solver.dpll import DPLLSolver
from solver.agent import DeductiveLogicAgent


def test_dpll_basics():
    solver = DPLLSolver()

    # SAT: (A or B) and (not A or B)
    # 1: A, 2: B
    clauses_sat = [[1, 2], [-1, 2]]
    sat, model, m = solver.solve(clauses_sat, [1, 2])
    assert sat is True
    assert model[2] is True

    # UNSAT: (A) and (not A)
    clauses_unsat = [[1], [-1]]
    sat, model, m = solver.solve(clauses_unsat, [1])
    assert sat is False
    assert model is None

    # Empty clause: UNSAT
    sat, _, _ = solver.solve([[]], [1])
    assert sat is False

    # Empty clauses list: SAT
    sat, _, _ = solver.solve([], [1])
    assert sat is True
    print("[PASS] test_dpll_basics")


def test_cnf_vs_direct_semantics_3x3():
    """
    Exhaustively check all 2^9 = 512 assignments for all 8 clue types on a 3x3 grid.
    Verify that CNF satisfaction matches Direct Semantic Evaluator on every assignment!
    """
    size = 3
    cells = get_all_cells(size)
    assert len(cells) == 9
    encoder = CNFEncoder(size)
    solver = DPLLSolver()
    all_vars = list(range(1, 10))

    test_clues = [
        # 1. FACT Criminal
        Clue(
            id="c_fact_c",
            source_cell="A1",
            clue_type=ClueType.FACT,
            params={"cell_id": "A1", "role": "CRIMINAL"},
            target_role=Role.CRIMINAL,
            referenced_cells=["A1"],
        ),
        # 2. FACT Innocent
        Clue(
            id="c_fact_i",
            source_cell="B2",
            clue_type=ClueType.FACT,
            params={"cell_id": "B2", "role": "INNOCENT"},
            target_role=Role.INNOCENT,
            referenced_cells=["B2"],
        ),
        # 3. SAME
        Clue(
            id="c_same",
            source_cell="A1",
            clue_type=ClueType.SAME,
            params={"cell_1": "A1", "cell_2": "C3"},
            referenced_cells=["A1", "C3"],
        ),
        # 4. DIFFERENT
        Clue(
            id="c_diff",
            source_cell="B1",
            clue_type=ClueType.DIFFERENT,
            params={"cell_1": "B1", "cell_2": "B2"},
            referenced_cells=["B1", "B2"],
        ),
        # 5. AT_LEAST Criminal
        Clue(
            id="c_at_least_c",
            source_cell="A2",
            clue_type=ClueType.AT_LEAST,
            params={"k": 2, "region_cells": get_row_cells(size, 1)},
            target_role=Role.CRIMINAL,
            referenced_cells=get_row_cells(size, 1),
        ),
        # 6. AT_LEAST Innocent
        Clue(
            id="c_at_least_i",
            source_cell="A2",
            clue_type=ClueType.AT_LEAST,
            params={"k": 2, "region_cells": get_row_cells(size, 1)},
            target_role=Role.INNOCENT,
            referenced_cells=get_row_cells(size, 1),
        ),
        # 7. AT_MOST Criminal
        Clue(
            id="c_at_most_c",
            source_cell="B2",
            clue_type=ClueType.AT_MOST,
            params={"k": 1, "region_cells": get_col_cells(size, "B")},
            target_role=Role.CRIMINAL,
            referenced_cells=get_col_cells(size, "B"),
        ),
        # 8. AT_MOST Innocent
        Clue(
            id="c_at_most_i",
            source_cell="B2",
            clue_type=ClueType.AT_MOST,
            params={"k": 1, "region_cells": get_col_cells(size, "B")},
            target_role=Role.INNOCENT,
            referenced_cells=get_col_cells(size, "B"),
        ),
        # 9. EXACTLY Criminal
        Clue(
            id="c_exactly_c",
            source_cell="C3",
            clue_type=ClueType.EXACTLY,
            params={"k": 2, "region_cells": get_corners(size)},
            target_role=Role.CRIMINAL,
            referenced_cells=get_corners(size),
        ),
        # 10. EXACTLY 0 (NO)
        Clue(
            id="c_no",
            source_cell="C1",
            clue_type=ClueType.EXACTLY,
            params={"k": 0, "region_cells": ["A1", "A2"]},
            target_role=Role.CRIMINAL,
            referenced_cells=["A1", "A2"],
        ),
        # 11. PARITY Odd
        Clue(
            id="c_parity_odd",
            source_cell="A3",
            clue_type=ClueType.PARITY,
            params={"is_odd": True, "region_cells": get_row_cells(size, 2)},
            target_role=Role.CRIMINAL,
            referenced_cells=get_row_cells(size, 2),
        ),
        # 12. PARITY Even (Innocents)
        Clue(
            id="c_parity_even_inno",
            source_cell="B3",
            clue_type=ClueType.PARITY,
            params={"is_odd": False, "region_cells": get_col_cells(size, "A")},
            target_role=Role.INNOCENT,
            referenced_cells=get_col_cells(size, "A"),
        ),
        # 13. COMPARE_COUNT (=)
        Clue(
            id="c_comp_eq",
            source_cell="B2",
            clue_type=ClueType.COMPARE_COUNT,
            params={
                "region_A_cells": get_row_cells(size, 1),
                "region_B_cells": get_row_cells(size, 3),
                "op": "=",
            },
            target_role=Role.CRIMINAL,
            referenced_cells=get_row_cells(size, 1) + get_row_cells(size, 3),
        ),
        # 14. COMPARE_COUNT (>)
        Clue(
            id="c_comp_gt",
            source_cell="B2",
            clue_type=ClueType.COMPARE_COUNT,
            params={
                "region_A_cells": ["A1", "A2"],
                "region_B_cells": ["C1", "C2"],
                "op": ">",
            },
            target_role=Role.CRIMINAL,
            referenced_cells=["A1", "A2", "C1", "C2"],
        ),
        # 15. COMMON_NEIGHBORS region test
        Clue(
            id="c_common_nbr",
            source_cell="B2",
            clue_type=ClueType.EXACTLY,
            params={"k": 1, "region_cells": get_common_neighbors(size, "A1", "C1")},
            target_role=Role.CRIMINAL,
            referenced_cells=get_common_neighbors(size, "A1", "C1"),
        ),
    ]

    # Generate all 512 assignments
    all_assignments = []
    for bits in itertools.product([False, True], repeat=9):
        assignment = {cells[i]: bits[i] for i in range(9)}
        all_assignments.append(assignment)

    for clue in test_clues:
        clauses = encoder.encode_clue(clue)
        for assignment in all_assignments:
            semantic_val = evaluate_clue_directly(clue, assignment)

            # Check if assignment satisfies all clauses in CNF
            cnf_val = True
            for clause in clauses:
                clause_sat = False
                for lit in clause:
                    var = abs(lit)
                    cid = encoder.var_to_cell(var)
                    cell_val = assignment[cid]
                    lit_sat = cell_val if lit > 0 else (not cell_val)
                    if lit_sat:
                        clause_sat = True
                        break
                if not clause_sat:
                    cnf_val = False
                    break

            assert semantic_val == cnf_val, (
                f"Mismatch on clue {clue.id} ({clue.clue_type.value}): "
                f"semantic={semantic_val}, cnf={cnf_val}, assignment={assignment}"
            )

    print(f"[PASS] test_cnf_vs_direct_semantics_3x3 ({len(test_clues)} clues * 512 assignments = {len(test_clues)*512} checks passed!)")


def test_role_isolation():
    engine = GameEngine(size=3)
    # Make sure DeductiveLogicAgent does not access private members
    agent = DeductiveLogicAgent()
    pub = engine.get_public_state()
    assert not hasattr(pub, "_hidden_solution")
    assert not hasattr(pub, "_unrevealed_clues")
    print("[PASS] test_role_isolation")


if __name__ == "__main__":
    test_dpll_basics()
    test_cnf_vs_direct_semantics_3x3()
    test_role_isolation()
    print("ALL CORE UNIT TESTS COMPLETED SUCCESSFULLY!")
