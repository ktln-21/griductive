"""
Reusable UI Components for Griductive Solver NiceGUI interface.
Implements in-place DOM updates (BoardCardView) so flipping a card or highlighting
regions NEVER rebuilds the board or causes screen jumping/flicker.
"""
from typing import Any, Callable, Dict, List, Optional, Set
from nicegui import ui
from core.models import Character, Clue, PublicKnowledgeState, Role
from ui.theme import format_clue_html, generate_pixel_avatar_svg


class BoardCardView:
    """
    Holds a persistent reference to a single character card's DOM elements.
    Allows in-place 3D card flip, highlight toggling, and status updates
    without ever clearing or recreating the board grid.
    """
    def __init__(
        self,
        cell_id: str,
        character: Character,
        is_revealed: bool,
        role: Optional[Role],
        clue: Optional[Clue],
        on_verdict_click: Callable[[str, Role], Any],
        on_card_click: Callable[[str], Any],
    ):
        self.cell_id = cell_id
        self.character = character
        self.is_revealed = is_revealed
        self.role = role
        self.clue = clue
        self.on_verdict_click = on_verdict_click
        self.on_card_click = on_card_click
        self.card_dom_id = f"card_{cell_id}"

        with ui.card().classes("grid-card").style("gap: 2px; padding: 5px 6px;").props(
            f"id={self.card_dom_id}"
        ) as self.card:
            # Header: Coordinate & Occupation
            with ui.row().classes("w-full justify-between items-center").style("margin-bottom: 1px; flex-shrink: 0;"):
                ui.label(cell_id).classes("badge-tag badge-coord")
                self.occ_label = ui.label(character.occupation).style(
                    "font-size: 14px; font-weight: bold; color: #a0aec0;"
                )

            # Center: Pixel Avatar + Character Name
            svg_html = generate_pixel_avatar_svg(character.name, character.occupation, size=40)
            ui.html(svg_html).classes("cursor-pointer").style("flex-shrink: 0;").on(
                "click", lambda: self.on_card_click(self.cell_id)
            )

            self.name_label = ui.label(character.name).style(
                "font-family: 'Press Start 2P'; font-size: 9px; color: #ffcd75; text-align: center; "
                "margin-top: 1px; width: 100%; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; flex-shrink: 0;"
            )

            # Bottom container (swapped in-place when revealed)
            self.bottom_container = ui.column().classes("w-full items-center").style("gap: 2px; flex-shrink: 0;")

        self._render_state_content()

    def _render_state_content(self) -> None:
        """Updates only the card's styling and bottom section in-place."""
        self.card.classes(remove="card-revealed-innocent card-revealed-criminal")
        if self.is_revealed:
            if self.role == Role.INNOCENT:
                self.card.classes(add="card-revealed-innocent")
            elif self.role == Role.CRIMINAL:
                self.card.classes(add="card-revealed-criminal")
            self.name_label.style(
                "font-family: 'Press Start 2P'; font-size: 9px; color: #1a1c2c; text-align: center; "
                "margin-top: 1px; width: 100%; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; flex-shrink: 0;"
            )
            self.occ_label.style("font-size: 14px; font-weight: bold; color: #4a5568;")
        else:
            self.name_label.style(
                "font-family: 'Press Start 2P'; font-size: 9px; color: #ffcd75; text-align: center; "
                "margin-top: 1px; width: 100%; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; flex-shrink: 0;"
            )
            self.occ_label.style("font-size: 14px; font-weight: bold; color: #a0aec0;")

        self.bottom_container.clear()
        with self.bottom_container:
            if not self.is_revealed:
                ui.label("? SUSPECT ?").style("font-size: 14px; color: #94a3b8; margin: 6px 0 4px 0;")
                with ui.row().classes("w-full justify-around items-center").style("margin-top: 2px; gap: 4px;"):
                    ui.button(
                        "INNO",
                        on_click=lambda: self.on_verdict_click(self.cell_id, Role.INNOCENT),
                    ).classes("pixel-btn pixel-btn-innocent verdict-btn-inno").style("font-size: 8px; padding: 4px 6px;")
                    ui.button(
                        "CRIM",
                        on_click=lambda: self.on_verdict_click(self.cell_id, Role.CRIMINAL),
                    ).classes("pixel-btn pixel-btn-criminal verdict-btn-crim").style("font-size: 8px; padding: 4px 6px;")
            else:
                badge_class = "badge-innocent" if self.role == Role.INNOCENT else "badge-criminal"
                role_text = self.role.value if self.role else "UNKNOWN"
                ui.label(role_text).classes(f"badge-tag {badge_class}").style("margin-top: 1px; flex-shrink: 0;")

                if self.clue and self.clue.text:
                    formatted_html = format_clue_html(self.clue.text, dark_bg=False)
                    with ui.element("div").classes("card-clue-box cursor-pointer").on(
                        "click", lambda: self.on_card_click(self.cell_id)
                    ).tooltip(f"[{self.cell_id}] {self.clue.text}"):
                        ui.html(f'<div style="width:100%; margin:0; padding:0;">💬 {formatted_html}</div>')
                else:
                    ui.label("No clue.").classes("card-clue-box").style("color: #777; font-style: italic;")

    def reveal_in_place(self, role: Role, clue: Optional[Clue]) -> None:
        """Flips this card to revealed state in-place without rebuilding the grid."""
        self.is_revealed = True
        self.role = role
        self.clue = clue
        self._render_state_content()

    def update_highlights(
        self,
        is_highlighted: bool,
        is_selected_clue: bool,
        is_hint_target: bool = False,
    ) -> None:
        """Toggles highlight and hint classes in-place with zero DOM rebuild."""
        if is_highlighted:
            self.card.classes(add="card-highlighted")
        else:
            self.card.classes(remove="card-highlighted")

        if is_selected_clue:
            self.card.classes(add="card-active-clue")
        else:
            self.card.classes(remove="card-active-clue")

        if is_hint_target:
            self.card.classes(add="card-hint-target")
        else:
            self.card.classes(remove="card-hint-target")


def render_active_clues_panel(
    public_state: PublicKnowledgeState,
    selected_clue_cell: Optional[str],
    on_clue_click: Callable[[str], Any],
) -> None:
    """
    Renders a list of all currently revealed clues in the Detective Notebook.
    Clicking any clue highlights its referenced cells on the board.
    """
    with ui.column().classes("clue-list-box"):
        if not public_state.revealed_clues:
            ui.label("No clues revealed yet.").style("color: #777;")
            return

        for cid, clue in public_state.revealed_clues.items():
            char = public_state.characters.get(cid)
            cname = char.name if char else cid
            role = public_state.revealed_cells.get(cid, Role.UNKNOWN)
            role_color = "#38b764" if role == Role.INNOCENT else "#e43b44"
            item_cls = "clue-list-item active-clue-item" if selected_clue_cell == cid else "clue-list-item"
            formatted_clue = format_clue_html(clue.text, dark_bg=True)

            with ui.element("div").classes(f"{item_cls} w-full").on("click", lambda c=cid: on_clue_click(c)):
                ui.html(
                    f'<span style="color:#ffcd75; font-weight:bold;">[{cid}] {cname}</span> '
                    f'<span style="color:{role_color}; font-size:15px;">({role.value})</span>: '
                    f'{formatted_clue}'
                )


def render_metrics_panel(metrics_data: Dict[str, Any]) -> None:
    """
    Renders real-time SAT and DPLL metrics.
    """
    with ui.row().classes("w-full flex-wrap gap-2 justify-between"):
        ui.html(f'<div class="metric-box">VARS: <span>{metrics_data.get("primary_vars", 0)}</span></div>')
        ui.html(f'<div class="metric-box">CLAUSES: <span>{metrics_data.get("cnf_clauses", 0)}</span></div>')
        ui.html(f'<div class="metric-box">SAT CALLS: <span>{metrics_data.get("sat_calls", 0)}</span></div>')
        ui.html(f'<div class="metric-box">DECISIONS: <span>{metrics_data.get("decisions", 0)}</span></div>')
        ui.html(f'<div class="metric-box">PROPS: <span>{metrics_data.get("propagations", 0)}</span></div>')
        ui.html(f'<div class="metric-box">BACKTRACKS: <span>{metrics_data.get("backtracks", 0)}</span></div>')
        ui.html(f'<div class="metric-box">TIME: <span>{metrics_data.get("runtime_ms", 0.0):.1f}ms</span></div>')


def render_deduction_trace(trace_steps: List[Dict[str, Any]]) -> None:
    """
    Renders the step-by-step detective deduction log.
    """
    with ui.column().classes("trace-log w-full"):
        if not trace_steps:
            ui.label("Detective Log is empty. Make a deduction or click HINT / STEP AI!").style("color: #777;")
        for step in reversed(trace_steps):
            s_num = step.get("step_number", 1)
            target = step.get("target_cell", "")
            verdict = step.get("verdict", "")
            queries = step.get("sat_queries_count", 0)
            new_clue = step.get("newly_revealed_clue", "")
            dec = step.get("decisions", 0)
            ms = step.get("runtime_ms", 0)

            v_class = "verdict-crim" if verdict == "CRIMINAL" else "verdict-inno"

            content = (
                f'<div class="trace-entry">'
                f'<span class="step-tag">[STEP {s_num:02d}]</span> Forced '
                f'<b>{target}</b> &#8594; <span class="{v_class}">{verdict}</span> '
                f'<span style="color:#29adff;">(SAT: {queries}, dec: {dec}, {ms}ms)</span>'
            )
            if new_clue:
                content += f'<br/><span style="color:#ffcd75; padding-left: 12px;">&#10148; Clue: "{new_clue}"</span>'
            content += '</div>'
            ui.html(content)
