"""
Deductive Logic Agent for Griductive Solver.
Performs rigorous deductive reasoning without guessing via SAT entailment check.
Maintains deduction trace, provides hints, performs uniqueness checks, and runs auto-solve.
"""
from dataclasses import dataclass, field
import time
from typing import Any, Dict, List, Optional, Tuple
from core.models import Clue, PublicKnowledgeState, Role
from solver.cnf_encoder import CNFEncoder
from solver.dpll import DPLLMetrics, DPLLSolver


@dataclass
class DeductionStep:
    step_number: int
    target_cell: str
    verdict: Role
    active_clue_ids: List[str]
    sat_queries_count: int
    newly_revealed_clue: Optional[str] = None
    metrics: DPLLMetrics = field(default_factory=DPLLMetrics)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "step_number": self.step_number,
            "target_cell": self.target_cell,
            "verdict": self.verdict.value,
            "active_clue_ids": self.active_clue_ids,
            "sat_queries_count": self.sat_queries_count,
            "newly_revealed_clue": self.newly_revealed_clue,
            "decisions": self.metrics.decisions,
            "propagations": self.metrics.propagations,
            "backtracks": self.metrics.backtracks,
            "runtime_ms": round(self.metrics.runtime_ms, 2),
        }


class DeductiveLogicAgent:
    def __init__(self):
        self.solver = DPLLSolver()
        self.deduction_trace: List[DeductionStep] = []
        self.cumulative_metrics = DPLLMetrics()
        self.total_sat_calls: int = 0

    def reset(self) -> None:
        """Reset the agent's state, trace, and metrics."""
        self.deduction_trace = []
        self.cumulative_metrics = DPLLMetrics()
        self.total_sat_calls = 0

    def check_entailment(
        self,
        public_state: PublicKnowledgeState,
        cell_id: str
    ) -> Role:
        """
        Tests whether the status of cell_id is logically entailed by KB_t.
        Returns:
            Role.CRIMINAL if KB_t |= C_i (KB_t ^ not C_i is UNSAT)
            Role.INNOCENT if KB_t |= not C_i (KB_t ^ C_i is UNSAT)
            Role.UNKNOWN if neither is forced (both are SAT)
        """
        encoder = CNFEncoder(public_state.size)
        kb_clauses = encoder.build_kb(public_state)
        var = encoder.cell_to_var(cell_id)
        all_vars = list(range(1, encoder.total_cells + 1))

        # Test 1: KB ^ not C_i (var is False, so clause is [[-var]])
        kb_not_c = [list(c) for c in kb_clauses] + [[-var]]
        self.total_sat_calls += 1
        sat_not_c, _, m1 = self.solver.solve(kb_not_c, all_vars)
        self.cumulative_metrics.add(m1)

        if not sat_not_c:
            # KB ^ not C_i is UNSAT => KB entails C_i (CRIMINAL)
            return Role.CRIMINAL

        # Test 2: KB ^ C_i (var is True, so clause is [[var]])
        kb_c = [list(c) for c in kb_clauses] + [[var]]
        self.total_sat_calls += 1
        sat_c, _, m2 = self.solver.solve(kb_c, all_vars)
        self.cumulative_metrics.add(m2)

        if not sat_c:
            # KB ^ C_i is UNSAT => KB entails not C_i (INNOCENT)
            return Role.INNOCENT

        # Neither is forced -> Unknown
        return Role.UNKNOWN

    def find_next_forced_cell(
        self,
        public_state: PublicKnowledgeState
    ) -> Optional[Tuple[str, Role, int, DPLLMetrics]]:
        """
        Iterates through unrevealed cells in deterministic Row-Major order.
        Returns (cell_id, forced_role, sat_queries, step_metrics) for the first entailed cell found.
        """
        encoder = CNFEncoder(public_state.size)
        kb_clauses = encoder.build_kb(public_state)
        all_vars = list(range(1, encoder.total_cells + 1))

        # Check if KB itself is satisfiable
        sat_base, _, m_base = self.solver.solve(kb_clauses, all_vars)
        self.total_sat_calls += 1
        self.cumulative_metrics.add(m_base)
        if not sat_base:
            return None

        unrevealed = public_state.unrevealed_cell_ids
        for cid in unrevealed:
            var = encoder.cell_to_var(cid)
            step_metrics = DPLLMetrics()
            queries = 0

            # Test KB ^ not C_i
            kb_not_c = [list(c) for c in kb_clauses] + [[-var]]
            sat_not_c, _, m1 = self.solver.solve(kb_not_c, all_vars)
            step_metrics.add(m1)
            queries += 1

            if not sat_not_c:
                self.cumulative_metrics.add(step_metrics)
                self.total_sat_calls += queries
                return cid, Role.CRIMINAL, queries, step_metrics

            # Test KB ^ C_i
            kb_c = [list(c) for c in kb_clauses] + [[var]]
            sat_c, _, m2 = self.solver.solve(kb_c, all_vars)
            step_metrics.add(m2)
            queries += 1

            if not sat_c:
                self.cumulative_metrics.add(step_metrics)
                self.total_sat_calls += queries
                return cid, Role.INNOCENT, queries, step_metrics

            self.cumulative_metrics.add(step_metrics)
            self.total_sat_calls += queries

        return None

    def get_hint(self, public_state: PublicKnowledgeState) -> Optional[Dict[str, Any]]:
        """
        Returns a hint structure for the next forced move:
        {
            'cell_id': str,
            'verdict': Role,
            'character_name': str,
            'active_clue_ids': list[str],
            'reason': str
        }
        """
        result = self.find_next_forced_cell(public_state)
        if result is None:
            return None

        cid, role, _, _ = result
        char = public_state.characters.get(cid)
        name = char.name if char else cid
        active_clues = list(public_state.revealed_clues.keys())

        return {
            "cell_id": cid,
            "verdict": role,
            "character_name": name,
            "active_clue_ids": active_clues,
            "reason": f"From current clues, {name} ({cid}) is strictly proved to be {role.value}.",
        }

    def step_solve(self, engine: Any) -> Optional[DeductionStep]:
        """
        Performs one step of deductive resolution on the engine.
        Finds the first forced cell, submits verdict, updates engine, and records trace.
        """
        public_state = engine.get_public_state()
        result = self.find_next_forced_cell(public_state)
        if result is None:
            return None

        cid, forced_role, sat_queries, metrics = result
        active_clues = list(public_state.revealed_clues.keys())

        # Submit verdict to engine
        engine.submit_verdict(cid, forced_role, self)

        # Check newly revealed clue
        newly_revealed = engine.revealed_clues.get(cid)
        new_clue_text = newly_revealed.text if newly_revealed else None

        step = DeductionStep(
            step_number=len(self.deduction_trace) + 1,
            target_cell=cid,
            verdict=forced_role,
            active_clue_ids=active_clues,
            sat_queries_count=sat_queries,
            newly_revealed_clue=new_clue_text,
            metrics=metrics,
        )
        self.deduction_trace.append(step)
        return step

    def auto_solve(self, engine: Any) -> bool:
        """
        Runs deductive solver iteratively until the board is completely solved
        or no further deduction is possible without guessing.
        Returns True if 100% solved, False if stuck.
        """
        while not engine.is_solved():
            step = self.step_solve(engine)
            if step is None:
                # Stuck! Cannot solve without guessing
                return False
        return True

    def check_uniqueness(self, all_clues: List[Clue], size: int) -> Tuple[bool, int]:
        """
        Checks whether the full set of clues produces a UNIQUE solution.
        Encodes all clues into CNF and searches for up to 2 models.
        Returns (is_unique: bool, num_models: int).
        """
        encoder = CNFEncoder(size)
        all_clauses = []
        for clue in all_clues:
            all_clauses.extend(encoder.encode_clue(clue))

        all_vars = list(range(1, encoder.total_cells + 1))
        models = self.solver.find_models(all_clauses, all_vars, max_solutions=2)
        count = len(models)
        return (count == 1), count
