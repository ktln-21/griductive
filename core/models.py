"""
Core data models for Griductive Solver.
Defines Character, Region, Clue, PublicKnowledgeState, and Game Enums.
"""
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Set


class Role(str, Enum):
    CRIMINAL = "CRIMINAL"
    INNOCENT = "INNOCENT"
    UNKNOWN = "UNKNOWN"


class VerdictResult(str, Enum):
    ACCEPTED = "ACCEPTED"
    NOT_PROVABLE = "NOT_PROVABLE"
    CONTRADICTED = "CONTRADICTED"
    ALREADY_REVEALED = "ALREADY_REVEALED"


class ClueType(str, Enum):
    # 6 basic clues
    FACT = "FACT"
    SAME = "SAME"
    DIFFERENT = "DIFFERENT"
    AT_LEAST = "AT_LEAST"
    AT_MOST = "AT_MOST"
    EXACTLY = "EXACTLY"
    # 2 extensions
    PARITY = "PARITY"
    COMPARE_COUNT = "COMPARE_COUNT"


class RegionType(str, Enum):
    ROW = "ROW"
    COL = "COL"
    NEIGHBORS = "NEIGHBORS"
    CELLS = "CELLS"
    # 2 advanced regions (extensions)
    COMMON_NEIGHBORS = "COMMON_NEIGHBORS"
    CORNERS = "CORNERS"
    BOUNDARY = "BOUNDARY"


@dataclass
class Character:
    cell_id: str
    name: str
    occupation: str
    avatar_svg: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "cell_id": self.cell_id,
            "name": self.name,
            "occupation": self.occupation,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Character":
        return cls(
            cell_id=data["cell_id"],
            name=data["name"],
            occupation=data["occupation"],
            avatar_svg=data.get("avatar_svg"),
        )


@dataclass
class Region:
    region_type: RegionType
    params: Dict[str, Any] = field(default_factory=dict)
    resolved_cells: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "region_type": self.region_type.value,
            "params": self.params,
            "resolved_cells": self.resolved_cells,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Region":
        return cls(
            region_type=RegionType(data["region_type"]),
            params=data.get("params", {}),
            resolved_cells=data.get("resolved_cells", []),
        )


@dataclass
class Clue:
    id: str
    source_cell: str
    clue_type: ClueType
    params: Dict[str, Any] = field(default_factory=dict)
    text: str = ""
    target_role: Role = Role.CRIMINAL
    referenced_cells: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "source_cell": self.source_cell,
            "clue_type": self.clue_type.value,
            "params": self.params,
            "text": self.text,
            "target_role": self.target_role.value,
            "referenced_cells": self.referenced_cells,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Clue":
        return cls(
            id=data["id"],
            source_cell=data["source_cell"],
            clue_type=ClueType(data["clue_type"]),
            params=data.get("params", {}),
            text=data.get("text", ""),
            target_role=Role(data.get("target_role", Role.CRIMINAL.value)),
            referenced_cells=data.get("referenced_cells", []),
        )


@dataclass
class PublicKnowledgeState:
    """
    Public knowledge visible to the Deductive Logic Agent and the Player.
    Strictly isolated from hidden game state.
    """
    size: int
    characters: Dict[str, Character]
    revealed_cells: Dict[str, Role]
    revealed_clues: Dict[str, Clue]

    @property
    def unrevealed_cell_ids(self) -> List[str]:
        all_cells = sorted(list(self.characters.keys()))
        return [cid for cid in all_cells if cid not in self.revealed_cells]
