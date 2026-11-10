"""
Reusable UI Components for Griductive Solver NiceGUI interface.
Implements in-place DOM updates (BoardCardView) and full bilingual (VI | EN) synchronization
so flipping a card, highlighting regions, or switching language NEVER causes layout shifts.
"""
from typing import Any, Callable, Dict, List, Optional
from nicegui import ui
from core.models import Character, Clue, PublicKnowledgeState, Role
from ui.i18n import (
    t,
    translate_clue_text,
    translate_occupation,
    translate_role_str,
)
from ui.theme import format_clue_html, generate_pixel_avatar_svg


class BoardCardView:
    """
    Holds a persistent reference to a single character card's DOM elements.
    Allows in-place 3D card flip, highlight toggling, and language switching
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
        lang: str = "VI",
    ):
        self.cell_id = cell_id
        self.character = character
        self.is_revealed = is_revealed
        self.role = role
        self.clue = clue
        self.on_verdict_click = on_verdict_click
        self.on_card_click = on_card_click
        self.lang = lang
        self.card_dom_id = f"card_{cell_id}"

        with ui.card().classes("grid-card").style("gap: 2px; padding: 5px 6px;").props(
            f"id={self.card_dom_id}"
        ) as self.card:
            # Header: Coordinate & Occupation
            with ui.row().classes("w-full justify-between items-center").style("margin-bottom: 1px; flex-shrink: 0;"):
                ui.label(cell_id).classes("badge-tag badge-coord")
                self.occ_label = ui.label(translate_occupation(character.occupation, self.lang)).style(
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

            # Bottom container (swapped in-place when revealed or language changed)
            self.bottom_container = ui.column().classes("w-full items-center").style("gap: 2px; flex-shrink: 0;")

        self._render_state_content()

    def _render_state_content(self) -> None:
        """Updates only the card's styling and bottom section in-place."""
        self.occ_label.text = translate_occupation(self.character.occupation, self.lang)
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
                ui.label(t("suspect_question", self.lang)).style(
                    "font-size: 14px; color: #94a3b8; margin: 6px 0 4px 0;"
                )
                btn_pad = "3px 4px" if self.lang == "VI" else "4px 6px"
                btn_font = "7.5px" if self.lang == "VI" else "8px"
                with ui.row().classes("w-full justify-around items-center").style("margin-top: 2px; gap: 3px;"):
                    ui.button(
                        t("btn_inno", self.lang),
                        on_click=lambda: self.on_verdict_click(self.cell_id, Role.INNOCENT),
                    ).classes("pixel-btn pixel-btn-innocent verdict-btn-inno").style(
                        f"font-size: {btn_font} !important; padding: {btn_pad} !important;"
                    )
                    ui.button(
                        t("btn_crim", self.lang),
                        on_click=lambda: self.on_verdict_click(self.cell_id, Role.CRIMINAL),
                    ).classes("pixel-btn pixel-btn-criminal verdict-btn-crim").style(
                        f"font-size: {btn_font} !important; padding: {btn_pad} !important;"
                    )
            else:
                badge_class = "badge-innocent" if self.role == Role.INNOCENT else "badge-criminal"
                role_raw = self.role.value if self.role else "UNKNOWN"
                role_text = translate_role_str(role_raw, self.lang)
                ui.label(role_text).classes(f"badge-tag {badge_class}").style("margin-top: 1px; flex-shrink: 0;")

                if self.clue and self.clue.text:
                    formatted_html = format_clue_html(self.clue.text, dark_bg=False, lang=self.lang)
                    localized_tip = translate_clue_text(self.clue.text, self.lang)
                    with ui.element("div").classes("card-clue-box cursor-pointer").on(
                        "click", lambda: self.on_card_click(self.cell_id)
                    ).tooltip(f"[{self.cell_id}] {localized_tip}"):
                        ui.html(f'<div style="width:100%; margin:0; padding:0;">💬 {formatted_html}</div>')
                else:
                    ui.label(t("no_clue", self.lang)).classes("card-clue-box").style("color: #777; font-style: italic;")

    def reveal_in_place(self, role: Role, clue: Optional[Clue]) -> None:
        """Flips this card to revealed state in-place without rebuilding the grid."""
        self.is_revealed = True
        self.role = role
        self.clue = clue
        self._render_state_content()

    def set_language(self, lang: str) -> None:
        """Updates card language in-place without rebuilding the board."""
        self.lang = lang
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
    lang: str = "VI",
) -> None:
    """
    Renders a list of all currently revealed clues in the Detective Notebook.
    Clicking any clue highlights its referenced cells on the board.
    """
    with ui.column().classes("clue-list-box"):
        if not public_state.revealed_clues:
            ui.label(t("no_clues_yet", lang)).style("color: #777;")
            return

        for cid, clue in public_state.revealed_clues.items():
            char = public_state.characters.get(cid)
            cname = char.name if char else cid
            role = public_state.revealed_cells.get(cid, Role.UNKNOWN)
            role_color = "#38b764" if role == Role.INNOCENT else "#e43b44"
            role_disp = translate_role_str(role.value, lang)
            item_cls = "clue-list-item active-clue-item" if selected_clue_cell == cid else "clue-list-item"
            formatted_clue = format_clue_html(clue.text, dark_bg=True, lang=lang)

            with ui.element("div").classes(f"{item_cls} w-full").on("click", lambda c=cid: on_clue_click(c)):
                ui.html(
                    f'<span style="color:#ffcd75; font-weight:bold;">[{cid}] {cname}</span> '
                    f'<span style="color:{role_color}; font-size:15px;">({role_disp})</span>: '
                    f'{formatted_clue}'
                )


def render_metrics_panel(metrics_data: Dict[str, Any], lang: str = "VI") -> None:
    """
    Renders real-time SAT and DPLL metrics in the active language.
    """
    with ui.row().classes("w-full flex-wrap gap-2 justify-between"):
        ui.html(f'<div class="metric-box">{t("m_vars", lang)}: <span>{metrics_data.get("primary_vars", 0)}</span></div>')
        ui.html(f'<div class="metric-box">{t("m_clauses", lang)}: <span>{metrics_data.get("cnf_clauses", 0)}</span></div>')
        ui.html(f'<div class="metric-box">SAT: <span>{metrics_data.get("sat_calls", 0)}</span></div>')
        ui.html(f'<div class="metric-box">{t("m_decisions", lang)}: <span>{metrics_data.get("decisions", 0)}</span></div>')
        ui.html(f'<div class="metric-box">{t("m_unit_prop", lang)}: <span>{metrics_data.get("propagations", 0)}</span></div>')
        ui.html(f'<div class="metric-box">{t("m_backtracks", lang)}: <span>{metrics_data.get("backtracks", 0)}</span></div>')
        ui.html(f'<div class="metric-box">{t("m_time", lang)}: <span>{metrics_data.get("runtime_ms", 0.0):.1f}ms</span></div>')


def render_deduction_trace(trace_steps: List[Dict[str, Any]], lang: str = "VI") -> None:
    """
    Renders the step-by-step detective deduction log in the active language.
    """
    with ui.column().classes("trace-log w-full"):
        if not trace_steps:
            ui.label(t("no_trace_yet", lang)).style("color: #777;")
        for step in reversed(trace_steps):
            s_num = step.get("step_number", 1)
            target = step.get("target_cell", "")
            verdict = step.get("verdict", "")
            queries = step.get("sat_queries_count", 0)
            new_clue = step.get("newly_revealed_clue", "")
            dec = step.get("decisions", 0)
            ms = step.get("runtime_ms", 0)

            v_class = "verdict-crim" if verdict == "CRIMINAL" else "verdict-inno"
            v_disp = translate_role_str(verdict, lang)

            if lang == "VI":
                step_tag = f"[BƯỚC {s_num:02d}]"
                forced_lbl = "Suy ra"
                clue_lbl = "Manh mối"
                meta_lbl = f"(SAT: {queries}, nhánh: {dec}, {ms}ms)"
            else:
                step_tag = f"[STEP {s_num:02d}]"
                forced_lbl = "Forced"
                clue_lbl = "Clue"
                meta_lbl = f"(SAT: {queries}, dec: {dec}, {ms}ms)"

            content = (
                f'<div class="trace-entry">'
                f'<span class="step-tag">{step_tag}</span> {forced_lbl} '
                f'<b>{target}</b> &#8594; <span class="{v_class}">{v_disp}</span> '
                f'<span style="color:#29adff;">{meta_lbl}</span>'
            )
            if new_clue:
                clue_disp = translate_clue_text(new_clue, lang)
                content += f'<br/><span style="color:#ffcd75; padding-left: 12px;">&#10148; {clue_lbl}: "{clue_disp}"</span>'
            content += '</div>'
            ui.html(content)
