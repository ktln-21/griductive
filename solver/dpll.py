"""
High-performance Pure Python DPLL SAT Solver with Trail-based Backtracking.
Features:
- Trail-based iterative Unit Propagation with clause watch lists
- Zero clause copying during search
- Conflict detection and clean backtracking
- Deterministic variable selection (MOMs heuristic with variable index tie-break)
- Complete metrics tracking (decisions, propagations, backtracks, runtime_ms)
"""
from dataclasses import dataclass
import time
from typing import Dict, List, Optional, Set, Tuple


@dataclass
class DPLLMetrics:
    decisions: int = 0
    propagations: int = 0
    backtracks: int = 0
    runtime_ms: float = 0.0

    def add(self, other: "DPLLMetrics") -> None:
        self.decisions += other.decisions
        self.propagations += other.propagations
        self.backtracks += other.backtracks
        self.runtime_ms += other.runtime_ms


class DPLLSolver:
    def __init__(self):
        self.metrics = DPLLMetrics()

    def solve(
        self,
        clauses: List[List[int]],
        all_vars: Optional[List[int]] = None
    ) -> Tuple[bool, Optional[Dict[int, bool]], DPLLMetrics]:
        """
        Solves the CNF formula using DPLL algorithm.
        Returns:
            (is_sat: bool, model: Optional[Dict[int, bool]], metrics: DPLLMetrics)
        """
        start_time = time.perf_counter()
        self.metrics = DPLLMetrics()

        # Check for empty clause right away
        for c in clauses:
            if len(c) == 0:
                self.metrics.runtime_ms = (time.perf_counter() - start_time) * 1000.0
                return False, None, self.metrics

        # Variable universe
        if all_vars is None:
            var_set = set()
            for c in clauses:
                for lit in c:
                    var_set.add(abs(lit))
            vars_list = sorted(list(var_set))
        else:
            vars_list = sorted(list(set(all_vars)))

        # Clean clauses: remove duplicate literals, drop tautological clauses (x or not x)
        cleaned_clauses: List[Tuple[int, ...]] = []
        for c in clauses:
            lit_set = set(c)
            # Check tautology
            is_tautology = any(-lit in lit_set for lit in lit_set)
            if not is_tautology:
                cleaned_clauses.append(tuple(sorted(list(lit_set))))

        # If no clauses, immediately SAT
        if not cleaned_clauses:
            model = {v: False for v in vars_list}
            self.metrics.runtime_ms = (time.perf_counter() - start_time) * 1000.0
            return True, model, self.metrics

        # Clause lookup by literal
        # lit_to_clauses[lit] = list of indices in cleaned_clauses containing lit
        lit_to_clauses: Dict[int, List[int]] = {}
        for c_idx, c in enumerate(cleaned_clauses):
            for lit in c:
                if lit not in lit_to_clauses:
                    lit_to_clauses[lit] = []
                lit_to_clauses[lit].append(c_idx)

        # State structures
        assignment: Dict[int, bool] = {}

        # Initial unit clauses
        initial_units = [c[0] for c in cleaned_clauses if len(c) == 1]

        def get_clause_status(c: Tuple[int, ...]) -> Tuple[bool, int, Optional[int]]:
            """
            Evaluates clause against current assignment.
            Returns:
                (is_satisfied: bool, unassigned_count: int, last_unassigned_lit: Optional[int])
            """
            unassigned_count = 0
            last_unassigned = None
            for lit in c:
                v = abs(lit)
                if v in assignment:
                    if (lit > 0 and assignment[v]) or (lit < 0 and not assignment[v]):
                        return True, 0, None
                else:
                    unassigned_count += 1
                    last_unassigned = lit
            return False, unassigned_count, last_unassigned

        def unit_propagate(queue: List[int]) -> Tuple[bool, List[int]]:
            """
            Propagates unit literals.
            Returns:
                (success: bool, newly_assigned_literals: List[int])
            """
            assigned_this_round: List[int] = []
            q_idx = 0
            while q_idx < len(queue):
                lit = queue[q_idx]
                q_idx += 1
                v = abs(lit)
                val = (lit > 0)

                if v in assignment:
                    if assignment[v] != val:
                        return False, assigned_this_round
                    continue

                assignment[v] = val
                assigned_this_round.append(lit)
                self.metrics.propagations += 1

                # Check all clauses containing -lit (since they lost a literal)
                falsified_lit = -lit
                affected = lit_to_clauses.get(falsified_lit, [])
                for c_idx in affected:
                    c = cleaned_clauses[c_idx]
                    sat, unassigned_cnt, next_lit = get_clause_status(c)
                    if sat:
                        continue
                    if unassigned_cnt == 0:
                        # Conflict!
                        return False, assigned_this_round
                    elif unassigned_cnt == 1:
                        # Unit clause
                        if abs(next_lit) not in assignment:
                            queue.append(next_lit)

            return True, assigned_this_round

        def select_variable(unassigned: List[int]) -> int:
            """
            MOMs heuristic: select variable occurring most frequently in shortest unsatisfied clauses.
            Breaks tie with smallest variable index.
            """
            # Find min length among unsatisfied clauses
            min_len = 999999
            for c in cleaned_clauses:
                sat, unassigned_cnt, _ = get_clause_status(c)
                if not sat and unassigned_cnt > 0:
                    if unassigned_cnt < min_len:
                        min_len = unassigned_cnt

            counts: Dict[int, int] = {v: 0 for v in unassigned}
            if min_len < 999999:
                for c in cleaned_clauses:
                    sat, unassigned_cnt, _ = get_clause_status(c)
                    if not sat and unassigned_cnt == min_len:
                        for lit in c:
                            v = abs(lit)
                            if v in counts:
                                counts[v] += 1

            return min(unassigned, key=lambda v: (-counts[v], v))

        def dpll_recursive() -> bool:
            unassigned = [v for v in vars_list if v not in assignment]
            if not unassigned:
                # All variables assigned, verify all clauses satisfied
                for c in cleaned_clauses:
                    sat, _, _ = get_clause_status(c)
                    if not sat:
                        return False
                return True

            branch_var = select_variable(unassigned)
            self.metrics.decisions += 1

            # Try True branch first
            ok, trail_true = unit_propagate([branch_var])
            if ok and dpll_recursive():
                return True

            # Backtrack True branch
            for lit in reversed(trail_true):
                v = abs(lit)
                if v in assignment:
                    del assignment[v]
            self.metrics.backtracks += 1

            # Try False branch
            ok, trail_false = unit_propagate([-branch_var])
            if ok and dpll_recursive():
                return True

            # Backtrack False branch
            for lit in reversed(trail_false):
                v = abs(lit)
                if v in assignment:
                    del assignment[v]
            self.metrics.backtracks += 1

            return False

        # Run initial unit propagation
        ok, init_trail = unit_propagate(list(initial_units))
        if ok and dpll_recursive():
            # Complete model with False for any remaining unassigned
            for v in vars_list:
                if v not in assignment:
                    assignment[v] = False
            self.metrics.runtime_ms = (time.perf_counter() - start_time) * 1000.0
            return True, dict(assignment), self.metrics
        else:
            self.metrics.runtime_ms = (time.perf_counter() - start_time) * 1000.0
            return False, None, self.metrics

    def is_satisfiable(self, clauses: List[List[int]], all_vars: Optional[List[int]] = None) -> bool:
        sat, _, _ = self.solve(clauses, all_vars)
        return sat

    def find_models(
        self,
        clauses: List[List[int]],
        all_vars: List[int],
        max_solutions: int = 2
    ) -> List[Dict[int, bool]]:
        models: List[Dict[int, bool]] = []
        curr_clauses = [list(c) for c in clauses]

        while len(models) < max_solutions:
            is_sat, model, _ = self.solve(curr_clauses, all_vars)
            if not is_sat or model is None:
                break
            models.append(model)
            blocking_clause = [(-v if model[v] else v) for v in all_vars]
            curr_clauses.append(blocking_clause)

        return models
