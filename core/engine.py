"""
Game Engine for Griductive Solver.
Maintains hidden solution and unrevealed clues with strict data isolation.
Validates player and agent verdicts using Deductive Logic Agent entailment.
"""
from typing import Any, Dict, List, Optional
from core.models import Character, Clue, PublicKnowledgeState, Role, VerdictResult


class GameEngine:
    def __init__(self, size: int = 3):
        self.size: int = size
        self.characters: Dict[str, Character] = {}
        # Hidden game state (NEVER shared directly with LogicAgent)
        self._hidden_solution: Dict[str, Role] = {}
        self._unrevealed_clues: Dict[str, Clue] = {}
        
        # Public knowledge state
        self.revealed_cells: Dict[str, Role] = {}
        self.revealed_clues: Dict[str, Clue] = {}

        # Initial revealed cells for restart
        self._initial_revealed_cells: Dict[str, Role] = {}
        self._initial_revealed_clues: Dict[str, Clue] = {}
        self.level_metadata: Dict[str, Any] = {}

    def load_level(self, level_dict: Dict[str, Any]) -> None:
        """
        Load a level configuration from a dictionary.
        """
        self.size = int(level_dict["size"])
        self.level_metadata = {
            "id": level_dict.get("id", "level_unknown"),
            "name": level_dict.get("name", "Untitled"),
            "chapter": level_dict.get("chapter", 1),
            "description": level_dict.get("description", ""),
        }

        # Characters
        self.characters = {}
        for char_data in level_dict.get("characters", []):
            char = Character.from_dict(char_data)
            self.characters[char.cell_id] = char

        # Hidden solution
        self._hidden_solution = {}
        for cid, role_str in level_dict.get("solution", {}).items():
            self._hidden_solution[cid] = Role(role_str)

        # Clues
        self._unrevealed_clues = {}
        for clue_data in level_dict.get("clues", []):
            clue = Clue.from_dict(clue_data)
            self._unrevealed_clues[clue.source_cell] = clue

        # Initial state setup
        self.revealed_cells = {}
        self.revealed_clues = {}

        initial_revealed = level_dict.get("initial_revealed", [])
        for cid in initial_revealed:
            if cid in self._hidden_solution:
                self.revealed_cells[cid] = self._hidden_solution[cid]
                if cid in self._unrevealed_clues:
                    self.revealed_clues[cid] = self._unrevealed_clues[cid]

        # Save snapshot for reset
        self._initial_revealed_cells = dict(self.revealed_cells)
        self._initial_revealed_clues = dict(self.revealed_clues)

    def reset(self) -> None:
        """Reset the game to the initial level state."""
        self.revealed_cells = dict(self._initial_revealed_cells)
        self.revealed_clues = dict(self._initial_revealed_clues)

    def get_public_state(self) -> PublicKnowledgeState:
        """
        Produce a strictly isolated PublicKnowledgeState.
        LogicAgent only sees this snapshot.
        """
        return PublicKnowledgeState(
            size=self.size,
            characters={cid: Character(
                cell_id=c.cell_id,
                name=c.name,
                occupation=c.occupation,
                avatar_svg=c.avatar_svg
            ) for cid, c in self.characters.items()},
            revealed_cells=dict(self.revealed_cells),
            revealed_clues=dict(self.revealed_clues),
        )

    def is_solved(self) -> bool:
        """Check if all cells have been revealed."""
        total_cells = self.size * self.size
        return len(self.revealed_cells) == total_cells

    def submit_verdict(self, cell_id: str, verdict: Role, agent: Any) -> VerdictResult:
        """
        Verify a player or agent's verdict for a cell against current public knowledge.
        Rule:
        - If already revealed: return ALREADY_REVEALED.
        - Query agent.check_entailment(public_state, cell_id):
          - If forced role == verdict: ACCEPTED (reveal card & clue).
          - If forced role is None (UNKNOWN): NOT_PROVABLE (Do not guess!).
          - If forced role is opposite: CONTRADICTED.
        """
        if cell_id in self.revealed_cells:
            return VerdictResult.ALREADY_REVEALED

        public_state = self.get_public_state()
        forced_role = agent.check_entailment(public_state, cell_id)

        if forced_role == verdict:
            # Correct and proved! Reveal card and clue
            self.revealed_cells[cell_id] = verdict
            if cell_id in self._unrevealed_clues:
                self.revealed_clues[cell_id] = self._unrevealed_clues[cell_id]
            return VerdictResult.ACCEPTED
        elif forced_role is None or forced_role == Role.UNKNOWN:
            # Both SAT branches possible -> not logically entailed yet
            return VerdictResult.NOT_PROVABLE
        else:
            # The opposite role is forced!
            return VerdictResult.CONTRADICTED

    def direct_reveal(self, cell_id: str) -> None:
        """
        Force-reveal a cell directly using hidden solution (used by level generator).
        """
        if cell_id in self._hidden_solution:
            role = self._hidden_solution[cell_id]
            self.revealed_cells[cell_id] = role
            if cell_id in self._unrevealed_clues:
                self.revealed_clues[cell_id] = self._unrevealed_clues[cell_id]
