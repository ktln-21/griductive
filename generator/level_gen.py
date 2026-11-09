"""
Constructive No-Guess Level Generator for Griductive Solver.
Generates 55 verified No-Guess levels across 4 Chapters with:
- 100% honest, exact region-to-text correspondence (Row, Col, Neighbors, Common Neighbors, Corners, Boundary, Named Suspects)
- Every single character (N*N) having a meaningful clue attached
- 100% solvable by pure deductive logic (DeductiveLogicAgent.auto_solve) and unique solution (check_uniqueness).
"""
import json
import os
import random
import sys
import time
from typing import Any, Dict, List, Optional, Set, Tuple

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from core.models import Character, Clue, ClueType, PublicKnowledgeState, Role
from core.regions import (
    cell_id_from_rc,
    get_all_cells,
    get_boundary,
    get_col_cells,
    get_common_neighbors,
    get_corners,
    get_neighbors,
    get_row_cells,
    rc_from_cell_id,
)
from core.semantics import evaluate_clue_directly
from core.engine import GameEngine
from solver.agent import DeductiveLogicAgent


NAMES = [
    "Abel", "Bea", "Clara", "Derek", "Eliza", "Felix", "Greta", "Hugo",
    "Iris", "Jonas", "Kira", "Leo", "Mara", "Noah", "Otto", "Penny",
    "Quinn", "Rosa", "Silas", "Tara", "Ulric", "Vera", "Wyatt", "Xena", "Yuri", "Zara"
]

OCCUPATIONS = [
    "Guard", "Detective", "Cook", "Clerk", "Doctor", "Judge", "Pilot", "Farmer",
    "Florist", "Sailor", "Artist", "Tailor", "Miner", "Baker", "Smith", "Potter",
    "Barber", "Butler", "Waiter", "Nurse", "Banker", "Lawyer", "Writer", "Chemist", "Miller"
]


def create_character_map(size: int) -> Dict[str, Character]:
    all_cells = get_all_cells(size)
    char_map = {}
    for idx, cid in enumerate(all_cells):
        name = NAMES[idx % len(NAMES)]
        occ = OCCUPATIONS[idx % len(OCCUPATIONS)]
        char_map[cid] = Character(cell_id=cid, name=name, occupation=occ)
    return char_map


def render_clue_text(clue: Clue, char_map: Dict[str, Character]) -> str:
    ctype = clue.clue_type
    params = clue.params
    target_str = "Criminal" if clue.target_role == Role.CRIMINAL else "Innocent"
    target_str_plural = "Criminals" if clue.target_role == Role.CRIMINAL else "Innocents"

    if ctype == ClueType.FACT:
        cid = params.get("cell_id", clue.source_cell)
        name = char_map[cid].name if cid in char_map else cid
        role_str = params.get("role", Role.CRIMINAL.value)
        article = "an" if role_str == Role.INNOCENT.value else "a"
        return f"{name} ({cid}) is {article} {role_str}."

    elif ctype == ClueType.SAME:
        c1, c2 = params["cell_1"], params["cell_2"]
        n1 = char_map[c1].name if c1 in char_map else c1
        n2 = char_map[c2].name if c2 in char_map else c2
        return f"{n1} ({c1}) and {n2} ({c2}) have the SAME status."

    elif ctype == ClueType.DIFFERENT:
        c1, c2 = params["cell_1"], params["cell_2"]
        n1 = char_map[c1].name if c1 in char_map else c1
        n2 = char_map[c2].name if c2 in char_map else c2
        return f"{n1} ({c1}) and {n2} ({c2}) have DIFFERENT statuses."

    elif ctype == ClueType.EXACTLY:
        k = params["k"]
        reg_desc = params.get("region_desc", "the region")
        if k == 0:
            return f"NO {target_str_plural} in {reg_desc}."
        elif k == 1:
            return f"Exactly 1 {target_str} in {reg_desc}."
        else:
            return f"Exactly {k} {target_str_plural} in {reg_desc}."

    elif ctype == ClueType.AT_LEAST:
        k = params["k"]
        reg_desc = params.get("region_desc", "the region")
        return f"At least {k} {target_str if k == 1 else target_str_plural} in {reg_desc}."

    elif ctype == ClueType.AT_MOST:
        k = params["k"]
        reg_desc = params.get("region_desc", "the region")
        return f"At most {k} {target_str if k == 1 else target_str_plural} in {reg_desc}."

    elif ctype == ClueType.PARITY:
        is_odd = params.get("is_odd", True)
        reg_desc = params.get("region_desc", "the region")
        parity_word = "ODD" if is_odd else "EVEN"
        return f"An {parity_word} number of {target_str_plural} in {reg_desc}."

    elif ctype == ClueType.COMPARE_COUNT:
        op = params.get("op", "=")
        desc_a = params.get("region_A_desc", "region A")
        desc_b = params.get("region_B_desc", "region B")
        if op in ("=", "=="):
            return f"Equal number of {target_str_plural} in {desc_a} and {desc_b}."
        elif op == ">":
            return f"MORE {target_str_plural} in {desc_a} than in {desc_b}."
        elif op == "<":
            return f"FEWER {target_str_plural} in {desc_a} than in {desc_b}."

    return "A mysterious clue."


def build_all_true_regions(
    size: int,
    char_map: Dict[str, Character],
    chapter: int
) -> List[Tuple[str, List[str], str]]:
    """
    Returns a list of (region_kind, exact_cell_list, exact_natural_description).
    Every region's cell list matches its natural description 100%.
    """
    all_cells = get_all_cells(size)
    regions: List[Tuple[str, List[str], str]] = []

    # 1. Rows
    for r in range(1, size + 1):
        regions.append(("ROW", get_row_cells(size, r), f"Row {r}"))

    # 2. Columns
    for c_idx in range(size):
        col_letter = chr(ord("A") + c_idx)
        regions.append(("COL", get_col_cells(size, col_letter), f"Column {col_letter}"))

    # 3. Neighbors of each character
    for cid in all_cells:
        nbrs = get_neighbors(size, cid)
        if nbrs:
            cname = char_map[cid].name
            regions.append(("NEIGHBORS", nbrs, f"neighbors of {cname} ({cid})"))

    # 4. Advanced regions (Chapter >= 2)
    if chapter >= 2:
        corners = get_corners(size)
        regions.append(("CORNERS", corners, "the 4 corners"))

        for i, c1 in enumerate(all_cells):
            for c2 in all_cells[i + 1:]:
                cnbrs = get_common_neighbors(size, c1, c2)
                if len(cnbrs) >= 2:
                    n1 = char_map[c1].name
                    n2 = char_map[c2].name
                    regions.append((
                        "COMMON_NEIGHBORS",
                        cnbrs,
                        f"common neighbors of {n1} ({c1}) and {n2} ({c2})"
                    ))

    return regions


def generate_single_level(
    level_id: str,
    name: str,
    chapter: int,
    size: int,
    seed: int
) -> Optional[Dict[str, Any]]:
    rng = random.Random(seed)
    all_cells = get_all_cells(size)
    char_map = create_character_map(size)
    total_cells = size * size
    true_regions = build_all_true_regions(size, char_map, chapter)

    for attempt in range(40):
        # 1. Ground truth
        num_crims = rng.randint(max(2, int(total_cells * 0.38)), min(total_cells - 2, int(total_cells * 0.62)))
        crim_cells = set(rng.sample(all_cells, num_crims))
        solution_bool = {cid: (cid in crim_cells) for cid in all_cells}
        solution_roles = {cid: (Role.CRIMINAL if b else Role.INNOCENT) for cid, b in solution_bool.items()}

        def count_in(cells_list: List[str], target_role: Role) -> int:
            target_b = (target_role == Role.CRIMINAL)
            return sum(1 for c in cells_list if solution_bool[c] == target_b)

        # 2. Initial revealed cells (1 for 3x3/4x4, 2 for 5x5)
        num_init = 1 if size <= 4 else 2
        init_cells = rng.sample(all_cells, num_init)

        assigned_clues: Dict[str, Clue] = {}
        revealed_cells: Dict[str, Role] = {cid: solution_roles[cid] for cid in init_cells}
        clue_counter = 0

        # Helper to build candidate forcing clues from true regions
        def pick_forcing_clue(source_cell: str) -> Clue:
            nonlocal clue_counter
            clue_counter += 1
            unrev_set = set(all_cells) - set(revealed_cells.keys())

            # Find true regions that can immediately force >= 1 unrevealed cell:
            # (a) Regions with exactly 1 unrevealed cell
            # (b) Regions with 1..3 unrevealed cells where all unrevealed cells share the same role
            forcing_regions: List[Tuple[str, List[str], str, List[str], Optional[Role]]] = []
            for r_kind, r_cells, r_desc in true_regions:
                u_cells = [c for c in r_cells if c in unrev_set]
                if not u_cells:
                    continue
                if len(u_cells) == 1:
                    forcing_regions.append((r_kind, r_cells, r_desc, u_cells, None))
                elif 2 <= len(u_cells) <= 3:
                    roles_in_u = {solution_roles[c] for c in u_cells}
                    if len(roles_in_u) == 1:
                        only_role = next(iter(roles_in_u))
                        forcing_regions.append((r_kind, r_cells, r_desc, u_cells, only_role))

            rng.shuffle(forcing_regions)

            # Decide what kind of clue to emit based on chapter and availability
            can_use_region = len(forcing_regions) > 0
            single_u_regions = [fr for fr in forcing_regions if len(fr[3]) == 1]
            fully_revealed_regions = [
                (rk, rc, rd) for rk, rc, rd in true_regions
                if all(c not in unrev_set for c in rc) and len(rc) <= 5
            ]

            choices = ["SAME_DIFF", "NAMED_GROUP"]
            if can_use_region:
                choices.extend(["TRUE_REGION", "TRUE_REGION", "TRUE_REGION"])
            if chapter >= 3 and single_u_regions:
                choices.extend(["PARITY_REGION", "PARITY_REGION"])
            if chapter >= 3 and single_u_regions and fully_revealed_regions:
                choices.append("COMPARE_REGION")

            chosen_mode = rng.choice(choices)

            if chosen_mode == "COMPARE_REGION" and single_u_regions and fully_revealed_regions:
                _, rA_cells, rA_desc, u_list, _ = rng.choice(single_u_regions)
                target_u = u_list[0]
                target_role = Role.CRIMINAL if rng.random() < 0.6 else Role.INNOCENT
                cntA = count_in(rA_cells, target_role)
                # Look for a fully revealed region with same count (so op="=" forces target_u)
                matching_B = [
                    (rk, rc, rd) for rk, rc, rd in fully_revealed_regions
                    if count_in(rc, target_role) == cntA and set(rc) != set(rA_cells) and len(set(rc) ^ set(rA_cells)) <= 7
                ]
                if matching_B:
                    _, rB_cells, rB_desc = rng.choice(matching_B)
                    c = Clue(
                        id=f"{source_cell}_cmp_{clue_counter}",
                        source_cell=source_cell,
                        clue_type=ClueType.COMPARE_COUNT,
                        params={
                            "region_A_cells": rA_cells,
                            "region_B_cells": rB_cells,
                            "region_A_desc": rA_desc,
                            "region_B_desc": rB_desc,
                            "op": "=",
                        },
                        target_role=target_role,
                        referenced_cells=sorted(list(set(rA_cells + rB_cells))),
                    )
                    c.text = render_clue_text(c, char_map)
                    return c

            if chosen_mode == "PARITY_REGION" and single_u_regions:
                # Pick a single-unrevealed region with <= 5 cells
                small_single = [fr for fr in single_u_regions if len(fr[1]) <= 5]
                if small_single:
                    _, r_cells, r_desc, _, _ = rng.choice(small_single)
                    target_role = Role.CRIMINAL if rng.random() < 0.6 else Role.INNOCENT
                    cnt = count_in(r_cells, target_role)
                    c = Clue(
                        id=f"{source_cell}_par_{clue_counter}",
                        source_cell=source_cell,
                        clue_type=ClueType.PARITY,
                        params={"is_odd": (cnt % 2 == 1), "region_cells": r_cells, "region_desc": r_desc},
                        target_role=target_role,
                        referenced_cells=r_cells,
                    )
                    c.text = render_clue_text(c, char_map)
                    return c

            if chosen_mode == "TRUE_REGION" and can_use_region:
                # Prefer advanced regions in Chapter >= 2 when available
                adv_forcing = [fr for fr in forcing_regions if fr[0] in ("CORNERS", "COMMON_NEIGHBORS")]
                if chapter >= 2 and adv_forcing and rng.random() < 0.55:
                    r_kind, r_cells, r_desc, u_cells, uniform_role = rng.choice(adv_forcing)
                else:
                    r_kind, r_cells, r_desc, u_cells, uniform_role = rng.choice(forcing_regions)

                target_role = Role.CRIMINAL if rng.random() < 0.6 else Role.INNOCENT
                cnt = count_in(r_cells, target_role)

                # Determine whether we can use AT_LEAST / AT_MOST (in Chapter >= 2) or EXACTLY
                u_all_match_target = all(solution_roles[u] == target_role for u in u_cells)
                u_none_match_target = all(solution_roles[u] != target_role for u in u_cells)

                ctype = ClueType.EXACTLY
                if chapter >= 2 and rng.random() < 0.45:
                    if u_all_match_target and cnt > 0:
                        ctype = ClueType.AT_LEAST
                    elif u_none_match_target and cnt < len(r_cells):
                        ctype = ClueType.AT_MOST

                c = Clue(
                    id=f"{source_cell}_{ctype.value.lower()}_{clue_counter}",
                    source_cell=source_cell,
                    clue_type=ctype,
                    params={"k": cnt, "region_cells": r_cells, "region_desc": r_desc},
                    target_role=target_role,
                    referenced_cells=r_cells,
                )
                c.text = render_clue_text(c, char_map)
                return c

            if chosen_mode == "NAMED_GROUP" and len(revealed_cells) >= 2:
                target_u = rng.choice(list(unrev_set))
                rev_sample = rng.sample(list(revealed_cells.keys()), 2)
                group_cells = sorted([target_u] + rev_sample)
                names_str = ", ".join(f"{char_map[cid].name} ({cid})" for cid in group_cells)
                r_desc = f"suspects [{names_str}]"
                target_role = Role.CRIMINAL if rng.random() < 0.6 else Role.INNOCENT
                cnt = count_in(group_cells, target_role)

                if chapter >= 3 and rng.random() < 0.4:
                    c = Clue(
                        id=f"{source_cell}_par_{clue_counter}",
                        source_cell=source_cell,
                        clue_type=ClueType.PARITY,
                        params={"is_odd": (cnt % 2 == 1), "region_cells": group_cells, "region_desc": r_desc},
                        target_role=target_role,
                        referenced_cells=group_cells,
                    )
                else:
                    c = Clue(
                        id=f"{source_cell}_ex_{clue_counter}",
                        source_cell=source_cell,
                        clue_type=ClueType.EXACTLY,
                        params={"k": cnt, "region_cells": group_cells, "region_desc": r_desc},
                        target_role=target_role,
                        referenced_cells=group_cells,
                    )
                c.text = render_clue_text(c, char_map)
                return c

            # Default: SAME or DIFFERENT between a revealed cell and an unrevealed cell
            target_u = rng.choice(list(unrev_set))
            ref_cell = rng.choice(list(revealed_cells.keys()))
            if solution_bool[ref_cell] == solution_bool[target_u]:
                c = Clue(
                    id=f"{source_cell}_same_{target_u}_{clue_counter}",
                    source_cell=source_cell,
                    clue_type=ClueType.SAME,
                    params={"cell_1": ref_cell, "cell_2": target_u},
                    referenced_cells=sorted([ref_cell, target_u]),
                )
            else:
                c = Clue(
                    id=f"{source_cell}_diff_{target_u}_{clue_counter}",
                    source_cell=source_cell,
                    clue_type=ClueType.DIFFERENT,
                    params={"cell_1": ref_cell, "cell_2": target_u},
                    referenced_cells=sorted([ref_cell, target_u]),
                )
            c.text = render_clue_text(c, char_map)
            return c

        # 3. Forward-chaining wave construction
        # Never overwrite an already assigned clue!
        while len(revealed_cells) < total_cells:
            sources_without_clue = [c for c in revealed_cells if c not in assigned_clues]
            if not sources_without_clue:
                break
            src = sources_without_clue[0]
            new_clue = pick_forcing_clue(src)
            assigned_clues[src] = new_clue

            # Check which cells are newly forced by the updated public knowledge
            agent_sim = DeductiveLogicAgent()
            while len(revealed_cells) < total_cells:
                pub_state = PublicKnowledgeState(
                    size=size,
                    characters=char_map,
                    revealed_cells=dict(revealed_cells),
                    revealed_clues={cid: assigned_clues[cid] for cid in revealed_cells if cid in assigned_clues},
                )
                forced = agent_sim.find_next_forced_cell(pub_state)
                if forced is None:
                    break
                fcid, frole, _, _ = forced
                revealed_cells[fcid] = frole

        if len(revealed_cells) < total_cells:
            continue

        # 4. Assign meaningful, non-trivial closing clues to any remaining cells without clues
        for cid in all_cells:
            if cid not in assigned_clues:
                clue_counter += 1
                nbrs = get_neighbors(size, cid)
                cname = char_map[cid].name
                r_desc = f"neighbors of {cname} ({cid})"
                cnt = count_in(nbrs, Role.CRIMINAL)
                c = Clue(
                    id=f"{cid}_closing_{clue_counter}",
                    source_cell=cid,
                    clue_type=ClueType.EXACTLY,
                    params={"k": cnt, "region_cells": nbrs, "region_desc": r_desc},
                    target_role=Role.CRIMINAL,
                    referenced_cells=nbrs,
                )
                c.text = render_clue_text(c, char_map)
                assigned_clues[cid] = c

        # 5. Verification Gate
        # Ensure all clues are true under Direct Semantic Evaluator
        if not all(evaluate_clue_directly(c, solution_bool) for c in assigned_clues.values()):
            continue

        engine = GameEngine(size)
        level_dict = {
            "id": level_id,
            "name": name,
            "chapter": chapter,
            "size": size,
            "characters": [char_map[cid].to_dict() for cid in all_cells],
            "solution": {cid: r.value for cid, r in solution_roles.items()},
            "clues": [assigned_clues[cid].to_dict() for cid in all_cells],
            "initial_revealed": init_cells,
        }
        engine.load_level(level_dict)
        test_agent = DeductiveLogicAgent()
        solved = test_agent.auto_solve(engine)

        if not solved or not engine.is_solved():
            continue

        # Uniqueness check (including initial revealed facts as part of the level specification)
        init_fact_clues = [
            Clue(
                id=f"init_{cid}",
                source_cell=cid,
                clue_type=ClueType.FACT,
                params={"cell_id": cid, "role": solution_roles[cid].value},
                target_role=solution_roles[cid],
                referenced_cells=[cid],
            )
            for cid in init_cells
        ]
        is_unique, num_models = test_agent.check_uniqueness(
            list(assigned_clues.values()) + init_fact_clues, size
        )
        if not is_unique or num_models != 1:
            continue

        return level_dict

    return None


def generate_all_55_levels(output_file: Optional[str] = None) -> List[Dict[str, Any]]:
    if output_file is None:
        output_file = os.path.join(PROJECT_ROOT, "levels", "levels_manifest.json")
    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    levels = []

    print("Generating 55 standard Griductive levels...", flush=True)
    start_time = time.perf_counter()

    for i in range(1, 56):
        if 1 <= i <= 15:
            chapter = 1
            size = 3
            ch_name = "Rookie Detective"
        elif 16 <= i <= 35:
            chapter = 2
            size = 4
            ch_name = "Senior Inspector"
        elif 36 <= i <= 43:
            chapter = 3
            size = 4
            ch_name = "Mastermind"
        elif 44 <= i <= 50:
            chapter = 3
            size = 5
            ch_name = "Mastermind"
        else:
            chapter = 4
            size = 5
            ch_name = "Stress Test Suite"

        level_id = f"level_{i:02d}"
        name = f"Case #{i:02d}: {ch_name} ({size}x{size})"
        seed = 3000 + i * 53

        lvl_dict = generate_single_level(level_id, name, chapter, size, seed)
        if lvl_dict is None:
            lvl_dict = generate_single_level(level_id, name, chapter, size, seed + 7777)

        if lvl_dict is None:
            raise RuntimeError(f"Failed to generate level {i}")

        levels.append(lvl_dict)
        print(f"[{i:02d}/55] Generated {name} - Size {size}x{size} - Clues: {len(lvl_dict['clues'])} OK", flush=True)

    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(levels, f, indent=2, ensure_ascii=False)

    elapsed = time.perf_counter() - start_time
    print(f"Successfully generated and verified all {len(levels)} levels in {elapsed:.2f}s!", flush=True)
    print(f"Saved to: {output_file}", flush=True)
    return levels


if __name__ == "__main__":
    generate_all_55_levels()
