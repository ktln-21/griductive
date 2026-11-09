"""
Complete Unit Test Suite for Griductive Solver (CSC14003 - Project 2).
Validates:
1. DPLL SAT Solver correctness (SAT, UNSAT, unit propagation, contradictions).
2. CNF Encoder vs Direct Semantic Evaluator (Exhaustive 2^9 = 512 assignments for all 8 clue types).
3. Strict Architectural Role Separation (LogicAgent does not access hidden solution).
4. Full 55-Level No-Guess Verification (Every level in levels_manifest.json solves 100% via deduction).
"""
import itertools
import json
import os
import sys
import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from core.engine import GameEngine
from core.models import Character, Clue, ClueType, Role, VerdictResult
from core.regions import (
    get_all_cells,
    get_boundary,
    get_col_cells,
    get_common_neighbors,
    get_corners,
    get_neighbors,
    get_row_cells,
)
from core.semantics import evaluate_clue_directly
from solver.agent import DeductiveLogicAgent
from solver.cnf_encoder import CNFEncoder
from solver.dpll import DPLLSolver


# ---------------------------------------------------------
# Test 1: DPLL Basics
# ---------------------------------------------------------
def test_dpll_correctness():
    solver = DPLLSolver()

    # Empty formula -> SAT
    sat, model, _ = solver.solve([], [1, 2])
    assert sat is True

    # Empty clause -> UNSAT
    sat, model, _ = solver.solve([[]], [1, 2])
    assert sat is False

    # Simple SAT: (A or B) and (not A or B) -> B must be True
    sat, model, _ = solver.solve([[1, 2], [-1, 2]], [1, 2])
    assert sat is True
    assert model[2] is True

    # Direct contradiction: (A) and (-A) -> UNSAT
    sat, model, _ = solver.solve([[1], [-1]], [1])
    assert sat is False

    # Formula requiring branching and backtracking:
    # 2 variables, all 4 combinations forbidden:
    clauses_branch_unsat = [[1, 2], [1, -2], [-1, 2], [-1, -2]]
    sat, _, m = solver.solve(clauses_branch_unsat, [1, 2])
    assert sat is False
    assert m.decisions >= 1
    assert m.backtracks >= 1


# ---------------------------------------------------------
# Test 2: CNF vs Direct Semantic Evaluator (Exhaustive 512)
# ---------------------------------------------------------
def test_cnf_vs_direct_semantics_exhaustive_3x3():
    size = 3
    cells = get_all_cells(size)
    assert len(cells) == 9
    encoder = CNFEncoder(size)

    test_clues = [
        Clue(
            id="t_fact_crim",
            source_cell="A1",
            clue_type=ClueType.FACT,
            params={"cell_id": "A1", "role": "CRIMINAL"},
            target_role=Role.CRIMINAL,
            referenced_cells=["A1"],
        ),
        Clue(
            id="t_fact_inno",
            source_cell="B2",
            clue_type=ClueType.FACT,
            params={"cell_id": "B2", "role": "INNOCENT"},
            target_role=Role.INNOCENT,
            referenced_cells=["B2"],
        ),
        Clue(
            id="t_same",
            source_cell="A1",
            clue_type=ClueType.SAME,
            params={"cell_1": "A1", "cell_2": "C3"},
            referenced_cells=["A1", "C3"],
        ),
        Clue(
            id="t_diff",
            source_cell="B1",
            clue_type=ClueType.DIFFERENT,
            params={"cell_1": "B1", "cell_2": "B2"},
            referenced_cells=["B1", "B2"],
        ),
        Clue(
            id="t_at_least_c",
            source_cell="A2",
            clue_type=ClueType.AT_LEAST,
            params={"k": 2, "region_cells": get_row_cells(size, 1)},
            target_role=Role.CRIMINAL,
            referenced_cells=get_row_cells(size, 1),
        ),
        Clue(
            id="t_at_least_i",
            source_cell="A2",
            clue_type=ClueType.AT_LEAST,
            params={"k": 2, "region_cells": get_row_cells(size, 1)},
            target_role=Role.INNOCENT,
            referenced_cells=get_row_cells(size, 1),
        ),
        Clue(
            id="t_at_most_c",
            source_cell="B2",
            clue_type=ClueType.AT_MOST,
            params={"k": 1, "region_cells": get_col_cells(size, "B")},
            target_role=Role.CRIMINAL,
            referenced_cells=get_col_cells(size, "B"),
        ),
        Clue(
            id="t_exactly_c",
            source_cell="C3",
            clue_type=ClueType.EXACTLY,
            params={"k": 2, "region_cells": get_corners(size)},
            target_role=Role.CRIMINAL,
            referenced_cells=get_corners(size),
        ),
        Clue(
            id="t_no_crim",
            source_cell="C1",
            clue_type=ClueType.EXACTLY,
            params={"k": 0, "region_cells": ["A1", "A2"]},
            target_role=Role.CRIMINAL,
            referenced_cells=["A1", "A2"],
        ),
        Clue(
            id="t_parity_odd",
            source_cell="A3",
            clue_type=ClueType.PARITY,
            params={"is_odd": True, "region_cells": get_row_cells(size, 2)},
            target_role=Role.CRIMINAL,
            referenced_cells=get_row_cells(size, 2),
        ),
        Clue(
            id="t_parity_even_inno",
            source_cell="B3",
            clue_type=ClueType.PARITY,
            params={"is_odd": False, "region_cells": get_col_cells(size, "A")},
            target_role=Role.INNOCENT,
            referenced_cells=get_col_cells(size, "A"),
        ),
        Clue(
            id="t_comp_eq",
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
        Clue(
            id="t_comp_gt",
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
        Clue(
            id="t_common_nbr",
            source_cell="B2",
            clue_type=ClueType.EXACTLY,
            params={"k": 1, "region_cells": get_common_neighbors(size, "A1", "C1")},
            target_role=Role.CRIMINAL,
            referenced_cells=get_common_neighbors(size, "A1", "C1"),
        ),
    ]

    all_assignments = []
    for bits in itertools.product([False, True], repeat=9):
        assignment = {cells[i]: bits[i] for i in range(9)}
        all_assignments.append(assignment)

    for clue in test_clues:
        clauses = encoder.encode_clue(clue)
        for assignment in all_assignments:
            semantic_val = evaluate_clue_directly(clue, assignment)

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
                f"Mismatch on clue {clue.id}: semantic={semantic_val}, cnf={cnf_val}"
            )


# ---------------------------------------------------------
# Test 3: Role Separation and Verdict Protocol
# ---------------------------------------------------------
def test_role_separation_and_verdict_protocol():
    engine = GameEngine(size=3)
    agent = DeductiveLogicAgent()
    pub = engine.get_public_state()

    # Agent cannot access hidden structures
    assert not hasattr(pub, "_hidden_solution")
    assert not hasattr(pub, "_unrevealed_clues")

    # Load small test case
    test_level = {
        "id": "test_sep",
        "name": "Test Separation",
        "chapter": 1,
        "size": 3,
        "characters": [
            {"cell_id": "A1", "name": "Abel", "occupation": "Guard"},
            {"cell_id": "B1", "name": "Bea", "occupation": "Detective"},
            {"cell_id": "C1", "name": "Clara", "occupation": "Cook"},
            {"cell_id": "A2", "name": "Derek", "occupation": "Clerk"},
            {"cell_id": "B2", "name": "Eliza", "occupation": "Doctor"},
            {"cell_id": "C2", "name": "Felix", "occupation": "Judge"},
            {"cell_id": "A3", "name": "Greta", "occupation": "Pilot"},
            {"cell_id": "B3", "name": "Hugo", "occupation": "Farmer"},
            {"cell_id": "C3", "name": "Iris", "occupation": "Florist"},
        ],
        "solution": {
            "A1": "CRIMINAL", "B1": "INNOCENT", "C1": "INNOCENT",
            "A2": "INNOCENT", "B2": "CRIMINAL", "C2": "INNOCENT",
            "A3": "CRIMINAL", "B3": "INNOCENT", "C3": "INNOCENT",
        },
        "clues": [
            {"id": "c1", "source_cell": "A1", "clue_type": "SAME", "params": {"cell_1": "A1", "cell_2": "A3"}, "text": "A1 and A3 SAME", "target_role": "CRIMINAL", "referenced_cells": ["A1", "A3"]}
        ],
        "initial_revealed": ["A1"],
    }
    engine.load_level(test_level)

    # A1 is already revealed -> ALREADY_REVEALED
    res_a1 = engine.submit_verdict("A1", Role.CRIMINAL, agent)
    assert res_a1 == VerdictResult.ALREADY_REVEALED

    # From A1 is CRIMINAL and A1 same A3, A3 is entailed to be CRIMINAL:
    # If user guesses INNOCENT for A3 -> CONTRADICTED!
    res_contra = engine.submit_verdict("A3", Role.INNOCENT, agent)
    assert res_contra == VerdictResult.CONTRADICTED

    # If user submits CRIMINAL for A3 -> ACCEPTED!
    res_acc = engine.submit_verdict("A3", Role.CRIMINAL, agent)
    assert res_acc == VerdictResult.ACCEPTED
    assert "A3" in engine.revealed_cells

    # B1 is neither entailed nor contradicted yet -> NOT_PROVABLE!
    res_np = engine.submit_verdict("B1", Role.INNOCENT, agent)
    assert res_np == VerdictResult.NOT_PROVABLE


# ---------------------------------------------------------
# Test 4: Full 55 Levels 100% Deductive Solve Verification
# ---------------------------------------------------------
def test_all_55_levels_solve_100_percent():
    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    manifest_path = os.path.join(project_root, "levels", "levels_manifest.json")
    assert os.path.exists(manifest_path), "levels_manifest.json must exist"

    with open(manifest_path, "r", encoding="utf-8") as f:
        levels = json.load(f)

    assert len(levels) == 55, f"Expected 55 levels, found {len(levels)}"
    chapters_found = {lvl["chapter"] for lvl in levels}
    assert chapters_found == {1, 2, 3, 4}, f"Expected all 4 chapters, found {chapters_found}"

    agent = DeductiveLogicAgent()
    for idx, lvl in enumerate(levels):
        size = lvl["size"]
        total_cells = size * size
        # Verify every single character has a clue attached
        assert len(lvl["clues"]) == total_cells, (
            f"Level {lvl['id']} only has {len(lvl['clues'])} clues for {total_cells} characters!"
        )
        clue_sources = {c["source_cell"] for c in lvl["clues"]}
        char_cells = {ch["cell_id"] for ch in lvl["characters"]}
        assert clue_sources == char_cells, f"Level {lvl['id']} is missing clues on some characters!"
        for c_data in lvl["clues"]:
            assert c_data.get("text", "").strip() != "", f"Empty clue text in {lvl['id']}"

        engine = GameEngine(size)
        engine.load_level(lvl)
        agent.reset()

        solved = agent.auto_solve(engine)
        assert solved is True, f"Level {lvl['id']} ({lvl['name']}) got stuck during auto_solve!"
        assert engine.is_solved() is True, f"Level {lvl['id']} did not reveal all cells!"
