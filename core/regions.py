"""
Region and coordinate utilities for Griductive Solver.
Handles coordinate translation, region definitions, and resolution for NxN grids.
"""
from typing import List, Set, Tuple
from core.models import Region, RegionType


def cell_id_from_rc(r: int, c: int) -> str:
    """
    Convert 0-indexed row and col to cell_id.
    r: row (0 to N-1)
    c: col (0 to N-1)
    e.g. (0, 0) -> 'A1', (1, 2) -> 'C2'
    """
    col_letter = chr(ord('A') + c)
    row_num = r + 1
    return f"{col_letter}{row_num}"


def rc_from_cell_id(cell_id: str) -> Tuple[int, int]:
    """
    Convert cell_id to 0-indexed (row, col).
    e.g. 'A1' -> (0, 0), 'C2' -> (1, 2)
    """
    cell_id = cell_id.strip().upper()
    col = ord(cell_id[0]) - ord('A')
    row = int(cell_id[1:]) - 1
    return (row, col)


def get_all_cells(size: int) -> List[str]:
    """Get all cell IDs in row-major order."""
    cells = []
    for r in range(size):
        for c in range(size):
            cells.append(cell_id_from_rc(r, c))
    return cells


def get_row_cells(size: int, row_1indexed: int) -> List[str]:
    """Get all cells in a given 1-indexed row."""
    r = row_1indexed - 1
    if not (0 <= r < size):
        return []
    return [cell_id_from_rc(r, c) for c in range(size)]


def get_col_cells(size: int, col_letter: str) -> List[str]:
    """Get all cells in a given column letter ('A', 'B', etc.)."""
    c = ord(col_letter.strip().upper()) - ord('A')
    if not (0 <= c < size):
        return []
    return [cell_id_from_rc(r, c) for r in range(size)]


def get_neighbors(size: int, cell_id: str) -> List[str]:
    """
    Get all adjacent cells (horizontal, vertical, diagonal) up to 8 neighbors.
    Excludes the center cell itself. Returned in row-major sorted order.
    """
    r, c = rc_from_cell_id(cell_id)
    neighbors = []
    for dr in (-1, 0, 1):
        for dc in (-1, 0, 1):
            if dr == 0 and dc == 0:
                continue
            nr, nc = r + dr, c + dc
            if 0 <= nr < size and 0 <= nc < size:
                neighbors.append(cell_id_from_rc(nr, nc))
    neighbors.sort()
    return neighbors


def get_common_neighbors(size: int, cell_1: str, cell_2: str) -> List[str]:
    """
    Advanced Region: Intersection of neighbors of cell_1 and cell_2.
    """
    n1 = set(get_neighbors(size, cell_1))
    n2 = set(get_neighbors(size, cell_2))
    common = sorted(list(n1.intersection(n2)))
    return common


def get_corners(size: int) -> List[str]:
    """
    Advanced Region: The 4 corner cells of an NxN grid.
    """
    corners = [
        cell_id_from_rc(0, 0),                 # Top-Left (A1)
        cell_id_from_rc(0, size - 1),          # Top-Right
        cell_id_from_rc(size - 1, 0),          # Bottom-Left
        cell_id_from_rc(size - 1, size - 1),   # Bottom-Right
    ]
    corners.sort()
    return corners


def get_boundary(size: int) -> List[str]:
    """
    Advanced Region: All perimeter/boundary cells of an NxN grid.
    """
    boundary_cells = set()
    for r in range(size):
        for c in range(size):
            if r == 0 or r == size - 1 or c == 0 or c == size - 1:
                boundary_cells.add(cell_id_from_rc(r, c))
    return sorted(list(boundary_cells))


def resolve_region(size: int, region: Region) -> List[str]:
    """
    Resolves any Region object to its concrete list of cell IDs.
    Updates region.resolved_cells and returns the list.
    """
    rtype = region.region_type
    params = region.params

    if rtype == RegionType.ROW:
        row_num = int(params.get("row", 1))
        cells = get_row_cells(size, row_num)
    elif rtype == RegionType.COL:
        col_letter = str(params.get("col", "A")).upper()
        cells = get_col_cells(size, col_letter)
    elif rtype == RegionType.NEIGHBORS:
        cid = params.get("cell_id", "A1")
        cells = get_neighbors(size, cid)
    elif rtype == RegionType.CELLS:
        raw_cells = params.get("cells", [])
        valid_cells = set(get_all_cells(size))
        cells = sorted([c for c in raw_cells if c in valid_cells])
    elif rtype == RegionType.COMMON_NEIGHBORS:
        c1 = params.get("cell_1", "A1")
        c2 = params.get("cell_2", "A2")
        cells = get_common_neighbors(size, c1, c2)
    elif rtype == RegionType.CORNERS:
        cells = get_corners(size)
    elif rtype == RegionType.BOUNDARY:
        cells = get_boundary(size)
    else:
        cells = []

    region.resolved_cells = cells
    return cells
