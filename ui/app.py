"""
Main Application UI for Griductive Solver using NiceGUI.
Implements:
- Zero-jank in-place card updates (BoardCardView) — no full-board reload on moves!
- 3D Card Flip animations & 8-bit pixel particle bursts
- Built-in Web Audio Chiptune Synthesizer (4 BGM tracks + full SFX suite)
- Audio & Auto-Solve Speed Config Panel (BGM toggle, track switch, BGM/SFX volume sliders, Auto-Solve speed slider)
- Fixed-height inline Detective Status Bar (no disruptive toast popups)
"""
import asyncio
import json
import os
import sys
from typing import Any, Callable, Dict, List, Optional, Set

from nicegui import ui

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

DEFAULT_MANIFEST_PATH = os.path.join(PROJECT_ROOT, "levels", "levels_manifest.json")

from core.engine import GameEngine
from core.models import Role, VerdictResult
from solver.agent import DeductiveLogicAgent
from solver.cnf_encoder import CNFEncoder
from ui.components import (
    BoardCardView,
    render_active_clues_panel,
    render_deduction_trace,
    render_metrics_panel,
)
from ui.theme import AUDIO_AND_FX_JS, PIXEL_CSS


CHAPTER_INFO = {
    1: ("CHAP 1: ROOKIE (3x3)", 0),
    2: ("CHAP 2: INSPECTOR (4x4)", 15),
    3: ("CHAP 3: MASTERMIND (4x4/5x5)", 35),
    4: ("CHAP 4: STRESS TEST (5x5)", 50),
}

BGM_TRACK_OPTIONS = {
    "noir": "🎵 1. Noir Detective Mystery",
    "cyber": "🎵 2. Cyber Logic Synth",
    "trial": "🎵 3. Tense Courtroom Trial",
    "chill": "🎵 4. Chill Lo-Fi Pixel Cafe",
}


class GriductiveApp:
    def __init__(self, manifest_path: str = DEFAULT_MANIFEST_PATH):
        self.manifest_path = manifest_path
        self.levels: List[Dict[str, Any]] = []
        self.current_level_idx: int = 0
        self.solved_level_indices: Set[int] = set()
        self.engine = GameEngine()
        self.agent = DeductiveLogicAgent()

        # UI State
        self.highlighted_cells: Set[str] = set()
        self.selected_clue_cell: Optional[str] = None
        self.hint_target_cell: Optional[str] = None
        self.is_auto_solving: bool = False
        self.metrics_state: Dict[str, Any] = {}
        self.deduction_steps: List[Dict[str, Any]] = []

        # Audio & Speed Config State
        self.bgm_enabled: bool = False
        self.bgm_track: str = "noir"
        self.bgm_volume: int = 35       # 0..100
        self.sfx_volume: int = 70       # 0..100
        self.auto_solve_delay: float = 0.35  # seconds per step (0.10s .. 1.20s)

        # Status bar message
        self.status_text: str = "Ready! Click a revealed clue to highlight its region, or deduce a suspect."
        self.status_kind: str = "info"  # info, accepted, warning, error

        self.load_manifest()

    def load_manifest(self) -> None:
        """Loads all 55 levels from levels_manifest.json (auto-generates if missing)."""
        if not os.path.exists(self.manifest_path):
            from generator.level_gen import generate_all_55_levels
            generate_all_55_levels(self.manifest_path)

        with open(self.manifest_path, "r", encoding="utf-8") as f:
            self.levels = json.load(f)

    def set_level(self, idx: int) -> None:
        """Sets the current level and resets state."""
        if 0 <= idx < len(self.levels):
            self.current_level_idx = idx
            level_dict = self.levels[idx]
            self.engine.load_level(level_dict)
            self.agent.reset()
            self.highlighted_cells.clear()
            self.selected_clue_cell = None
            self.hint_target_cell = None
            self.is_auto_solving = False
            self.deduction_steps.clear()

            init_rev = level_dict.get("initial_revealed", [])
            if init_rev:
                first_cid = init_rev[0]
                if first_cid in self.engine.revealed_clues:
                    self.selected_clue_cell = first_cid
                    self.highlighted_cells = set(
                        self.engine.revealed_clues[first_cid].referenced_cells
                    )
                    clue_txt = self.engine.revealed_clues[first_cid].text
                    self.status_text = f'Starting Clue [{first_cid}]: "{clue_txt}"'
                    self.status_kind = "info"

            self.update_metrics()

    def update_metrics(self) -> None:
        """Updates CNF and DPLL metrics."""
        pub_state = self.engine.get_public_state()
        encoder = CNFEncoder(pub_state.size)
        kb_clauses = encoder.build_kb(pub_state)

        if self.engine.is_solved():
            self.solved_level_indices.add(self.current_level_idx)

        self.metrics_state = {
            "primary_vars": pub_state.size * pub_state.size,
            "aux_vars": encoder.aux_var_count,
            "cnf_clauses": len(kb_clauses),
            "sat_calls": self.agent.total_sat_calls,
            "decisions": self.agent.cumulative_metrics.decisions,
            "propagations": self.agent.cumulative_metrics.propagations,
            "backtracks": self.agent.cumulative_metrics.backtracks,
            "runtime_ms": self.agent.cumulative_metrics.runtime_ms,
        }


def create_ui():
    """Main UI builder with zero-jank in-place card updates."""
    app_instance = GriductiveApp()
    app_instance.set_level(0)

    ui.add_head_html(f"<style>{PIXEL_CSS}</style>{AUDIO_AND_FX_JS}")

    # Persistent references to current board's card views
    card_views: Dict[str, BoardCardView] = {}

    # Top Header Bar
    with ui.header().classes("pixel-panel w-full justify-between items-center").style(
        "margin-bottom: 4px; padding: 6px 14px;"
    ):
        with ui.row().classes("items-center gap-3"):
            ui.html('<span style="font-size: 26px;">🕵️</span>')
            with ui.column().style("gap: 2px;"):
                ui.label("GRIDUCTIVE SOLVER").classes("pixel-title")
                ui.label(
                    f"CSC14003 - Project 2 | {len(app_instance.levels)} No-Guess Stages"
                ).classes("pixel-subtitle")

        # Chapter Quick-Jump Buttons
        chapter_bar = ui.row().classes("items-center gap-2")

    # Main Content Area
    with ui.row().classes("w-full justify-center items-start").style("padding: 4px 12px; gap: 14px;"):
        # LEFT COLUMN: Stage Navigation, Controls, Status Bar & Board
        with ui.column().classes("items-center").style("min-width: 550px; max-width: 870px; gap: 6px;"):
            # Stage Selector & Prev/Next Bar
            nav_container = ui.row().classes("pixel-panel w-full justify-between items-center").style(
                "gap: 8px; padding: 6px 10px;"
            )

            # Action Controls Bar
            with ui.row().classes("pixel-panel w-full justify-around items-center").style(
                "padding: 6px 10px;"
            ):
                ui.button(
                    "🔄 RESTART",
                    on_click=lambda: on_restart_click(),
                ).classes("pixel-btn pixel-btn-restart")
                ui.button(
                    "💡 HINT",
                    on_click=lambda: on_hint_click(),
                ).classes("pixel-btn pixel-btn-hint")
                ui.button(
                    "🤖 STEP AI",
                    on_click=lambda: on_step_ai_click(),
                ).classes("pixel-btn pixel-btn-solve")
                auto_btn = ui.button(
                    "⚡ AUTO SOLVE",
                    on_click=lambda: on_auto_solve_click(),
                ).classes("pixel-btn pixel-btn-solve")

            # FIXED-HEIGHT INLINE STATUS BAR (Never changes height -> 0 screen jump!)
            with ui.element("div").classes("detective-status-bar status-bar-info") as status_bar_el:
                status_msg_label = ui.label(app_instance.status_text).style(
                    "font-family: 'VT323', monospace; font-size: 17.5px; line-height: 1.15; color: #f4f4f4; "
                    "display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical; overflow: hidden;"
                )
                next_stage_btn = ui.button(
                    "NEXT STAGE ▶",
                    on_click=lambda: go_to_level(app_instance.current_level_idx + 1),
                ).classes("pixel-btn pixel-btn-hint").style("font-size: 8px; padding: 4px 8px; display: none;")

            # Grid Board Container
            with ui.column().classes("pixel-panel items-center justify-center w-full").style(
                "padding: 10px 14px;"
            ):
                with ui.row().classes("w-full justify-between items-center").style("margin-bottom: 6px;"):
                    board_title_label = ui.label("").style(
                        "font-family: 'Press Start 2P'; font-size: 10px; color: #ffcd75;"
                    )
                    board_progress_label = ui.label("").style(
                        "font-family: 'Press Start 2P'; font-size: 9px; color: #a7f070;"
                    )
                board_grid_holder = ui.column().classes("items-center justify-center w-full")

        # RIGHT COLUMN: Sound & Speed Config, Active Clues, Metrics & Detective Log
        with ui.column().classes("pixel-panel").style("width: 470px; min-width: 400px; gap: 8px;"):
            # 1. SOUND & AUTO-SOLVE SPEED CONFIG PANEL
            with ui.column().classes("w-full").style(
                "background-color: #161a2c; border: 3px solid #000; padding: 8px 10px; gap: 6px;"
            ):
                with ui.row().classes("w-full justify-between items-center"):
                    ui.label("🎛️ SOUND & SPEED CONFIG").classes("pixel-title").style("font-size: 11px;")
                    bgm_toggle_btn = ui.button(
                        "🎵 BGM: OFF",
                        on_click=lambda: toggle_bgm(),
                    ).classes("pixel-btn").style("font-size: 8px; padding: 4px 8px;")

                # Track selector row
                with ui.row().classes("w-full items-center justify-between").style("gap: 8px;"):
                    ui.label("Track:").style("font-size: 16px; color: #ffcd75; min-width: 48px;")
                    ui.select(
                        options=BGM_TRACK_OPTIONS,
                        value=app_instance.bgm_track,
                        on_change=lambda e: change_bgm_track(e.value),
                    ).props("dark outlined dense").style(
                        "flex: 1; font-family: 'VT323'; font-size: 17px;"
                    )

                # Sliders for BGM Volume, SFX Volume, Auto-Solve Speed
                with ui.row().classes("w-full items-center justify-between").style("gap: 6px;"):
                    bgm_vol_label = ui.label(f"BGM Vol: {app_instance.bgm_volume}%").style(
                        "font-size: 16px; color: #a7f070; min-width: 95px;"
                    )
                    ui.slider(
                        min=0, max=100, step=5, value=app_instance.bgm_volume,
                        on_change=lambda e: change_bgm_vol(int(e.value)),
                    ).props("dark dense color=green").style("flex: 1;")

                with ui.row().classes("w-full items-center justify-between").style("gap: 6px;"):
                    sfx_vol_label = ui.label(f"SFX Vol: {app_instance.sfx_volume}%").style(
                        "font-size: 16px; color: #29adff; min-width: 95px;"
                    )
                    ui.slider(
                        min=0, max=100, step=5, value=app_instance.sfx_volume,
                        on_change=lambda e: change_sfx_vol(int(e.value)),
                    ).props("dark dense color=cyan").style("flex: 1;")

                with ui.row().classes("w-full items-center justify-between").style("gap: 6px;"):
                    speed_label = ui.label(f"AI Speed: {app_instance.auto_solve_delay:.2f}s").style(
                        "font-size: 16px; color: #ef7d57; min-width: 95px;"
                    )
                    ui.slider(
                        min=0.10, max=1.20, step=0.05, value=app_instance.auto_solve_delay,
                        on_change=lambda e: change_ai_speed(float(e.value)),
                    ).props("dark dense color=orange").style("flex: 1;")

            # 2. ACTIVE CLUES PANEL
            with ui.row().classes("w-full justify-between items-center"):
                ui.label("📋 ACTIVE CLUES (GỢI Ý)").classes("pixel-title").style("font-size: 11px;")
                ui.label("Click clue to highlight region").style("font-size: 15px; color: #a7f070;")

            clues_container = ui.column().classes("w-full")

            # 3. CNF & DPLL METRICS
            with ui.row().classes("w-full justify-between items-center"):
                ui.label("⚙️ CNF & DPLL METRICS").classes("pixel-title").style("font-size: 11px;")
                ui.label("Pure Python SAT").style("font-size: 15px; color: #29adff;")

            metrics_container = ui.column().classes("w-full")

            # 4. DEDUCTION TRACE LOG
            with ui.row().classes("w-full justify-between items-center"):
                ui.label("📓 DEDUCTION TRACE LOG").classes("pixel-title").style("font-size: 11px;")

            trace_container = ui.column().classes("w-full")

    # ---------------------------------------------------------
    # Audio & Speed Config Handlers
    # ---------------------------------------------------------
    def toggle_bgm() -> None:
        app_instance.bgm_enabled = not app_instance.bgm_enabled
        if app_instance.bgm_enabled:
            bgm_toggle_btn.text = "🎵 BGM: ON"
            bgm_toggle_btn.classes(add="pixel-btn-innocent")
            ui.run_javascript(
                f"window.GriductiveFX?.setBGMVolume({app_instance.bgm_volume / 100.0}); "
                f"window.GriductiveFX?.setBGMTrack('{app_instance.bgm_track}'); "
                f"window.GriductiveFX?.toggleBGM(true);"
            )
        else:
            bgm_toggle_btn.text = "🎵 BGM: OFF"
            bgm_toggle_btn.classes(remove="pixel-btn-innocent")
            ui.run_javascript("window.GriductiveFX?.toggleBGM(false);")

    def change_bgm_track(track_key: str) -> None:
        app_instance.bgm_track = track_key
        if not app_instance.bgm_enabled:
            toggle_bgm()
        else:
            ui.run_javascript(f"window.GriductiveFX?.setBGMTrack('{track_key}');")

    def change_bgm_vol(vol_pct: int) -> None:
        app_instance.bgm_volume = vol_pct
        bgm_vol_label.text = f"BGM Vol: {vol_pct}%"
        ui.run_javascript(f"window.GriductiveFX?.setBGMVolume({vol_pct / 100.0});")

    def change_sfx_vol(vol_pct: int) -> None:
        app_instance.sfx_volume = vol_pct
        sfx_vol_label.text = f"SFX Vol: {vol_pct}%"
        ui.run_javascript(
            f"window.GriductiveFX?.setSFXVolume({vol_pct / 100.0}); "
            f"window.GriductiveFX?.playSFX('button');"
        )

    def change_ai_speed(delay_sec: float) -> None:
        app_instance.auto_solve_delay = round(delay_sec, 2)
        speed_label.text = f"AI Speed: {app_instance.auto_solve_delay:.2f}s"

    # ---------------------------------------------------------
    # Status Bar & Header In-Place Updaters (Zero Layout Shift!)
    # ---------------------------------------------------------
    def set_status_bar(text: str, kind: str = "info") -> None:
        app_instance.status_text = text
        app_instance.status_kind = kind
        status_msg_label.text = text
        status_bar_el.classes(
            remove="status-bar-info status-bar-accepted status-bar-warning status-bar-error"
        )
        status_bar_el.classes(add=f"status-bar-{kind}")

        if app_instance.engine.is_solved() and app_instance.current_level_idx + 1 < len(app_instance.levels):
            next_stage_btn.style("font-size: 8px; padding: 4px 8px; display: inline-block;")
        else:
            next_stage_btn.style("display: none;")

    def update_board_header_labels() -> None:
        pub_state = app_instance.engine.get_public_state()
        size = pub_state.size
        lvl_meta = app_instance.engine.level_metadata
        rev_cnt = len(pub_state.revealed_cells)
        tot_cnt = size * size
        board_title_label.text = f"Chapter {lvl_meta.get('chapter', 1)} — {lvl_meta.get('name', 'Case')}"
        board_progress_label.text = f"Revealed: {rev_cnt}/{tot_cnt} | Clues: {len(pub_state.revealed_clues)}"

    def sync_card_highlights() -> None:
        """Updates card highlights in-place without touching card contents or rebuilding DOM."""
        for cid, cv in card_views.items():
            cv.update_highlights(
                is_highlighted=(cid in app_instance.highlighted_cells),
                is_selected_clue=(cid == app_instance.selected_clue_cell),
                is_hint_target=(cid == app_instance.hint_target_cell),
            )

    def refresh_side_panels() -> None:
        """Refreshes only the right-side fixed-height panels."""
        pub_state = app_instance.engine.get_public_state()
        clues_container.clear()
        with clues_container:
            render_active_clues_panel(
                public_state=pub_state,
                selected_clue_cell=app_instance.selected_clue_cell,
                on_clue_click=on_card_or_clue_click,
            )

        metrics_container.clear()
        with metrics_container:
            render_metrics_panel(app_instance.metrics_state)

        trace_container.clear()
        with trace_container:
            render_deduction_trace(app_instance.deduction_steps)

    # ---------------------------------------------------------
    # Full Board Builder (ONLY called when changing/restarting a level!)
    # ---------------------------------------------------------
    def build_board_once() -> None:
        card_views.clear()
        board_grid_holder.clear()
        pub_state = app_instance.engine.get_public_state()
        size = pub_state.size
        update_board_header_labels()

        grid_style = (
            f"display: grid; grid-template-columns: repeat({size}, 1fr); "
            f"gap: 8px; justify-items: center;"
        )
        with board_grid_holder:
            with ui.element("div").style(grid_style):
                for r in range(size):
                    for c in range(size):
                        col_letter = chr(ord("A") + c)
                        cid = f"{col_letter}{r + 1}"
                        char = pub_state.characters[cid]
                        is_rev = cid in pub_state.revealed_cells
                        role = pub_state.revealed_cells.get(cid)
                        clue = pub_state.revealed_clues.get(cid)

                        cv = BoardCardView(
                            cell_id=cid,
                            character=char,
                            is_revealed=is_rev,
                            role=role,
                            clue=clue,
                            on_verdict_click=on_verdict_click,
                            on_card_click=on_card_or_clue_click,
                        )
                        card_views[cid] = cv

        sync_card_highlights()

    def refresh_navigation() -> None:
        chapter_bar.clear()
        curr_chap = app_instance.levels[app_instance.current_level_idx].get("chapter", 1)
        with chapter_bar:
            for ch_num, (ch_label, start_idx) in CHAPTER_INFO.items():
                btn_cls = (
                    "pixel-btn pixel-btn-chap-active"
                    if curr_chap == ch_num
                    else "pixel-btn"
                )
                ui.button(
                    ch_label,
                    on_click=lambda idx=start_idx: go_to_level(idx),
                ).classes(btn_cls)

        nav_container.clear()
        with nav_container:
            prev_idx = max(0, app_instance.current_level_idx - 1)
            next_idx = min(len(app_instance.levels) - 1, app_instance.current_level_idx + 1)

            ui.button(
                "◀ PREV",
                on_click=lambda: go_to_level(prev_idx),
            ).classes("pixel-btn")

            level_options = {
                i: (
                    f"{'✓ ' if i in app_instance.solved_level_indices else ''}"
                    f"[Chap {lvl['chapter']} | {lvl['size']}x{lvl['size']}] {lvl['name']}"
                )
                for i, lvl in enumerate(app_instance.levels)
            }
            ui.select(
                options=level_options,
                value=app_instance.current_level_idx,
                on_change=lambda e: go_to_level(int(e.value)),
            ).props("dark outlined dense").style("min-width: 330px; font-family: 'VT323'; font-size: 18px;")

            ui.button(
                "NEXT ▶",
                on_click=lambda: go_to_level(next_idx),
            ).classes("pixel-btn")

    # ---------------------------------------------------------
    # Interactive Event Handlers (In-Place, Smooth, With SFX & FX)
    # ---------------------------------------------------------
    def go_to_level(new_idx: int) -> None:
        if 0 <= new_idx < len(app_instance.levels) and new_idx != app_instance.current_level_idx:
            ui.run_javascript("window.GriductiveFX?.playSFX('button');")
            app_instance.set_level(new_idx)
            refresh_navigation()
            build_board_once()
            refresh_side_panels()
            set_status_bar(app_instance.status_text, app_instance.status_kind)

    def on_restart_click() -> None:
        ui.run_javascript("window.GriductiveFX?.playSFX('button');")
        app_instance.set_level(app_instance.current_level_idx)
        build_board_once()
        refresh_side_panels()
        set_status_bar(app_instance.status_text, "info")

    def on_card_or_clue_click(cell_id: str) -> None:
        app_instance.hint_target_cell = None
        if cell_id in app_instance.engine.revealed_clues:
            clue = app_instance.engine.revealed_clues[cell_id]
            if app_instance.selected_clue_cell == cell_id:
                app_instance.selected_clue_cell = None
                app_instance.highlighted_cells.clear()
                set_status_bar("Highlight cleared.", "info")
            else:
                app_instance.selected_clue_cell = cell_id
                app_instance.highlighted_cells = set(clue.referenced_cells)
                set_status_bar(f'Clue [{cell_id}]: "{clue.text}"', "info")
            ui.run_javascript("window.GriductiveFX?.playSFX('select');")
        else:
            app_instance.selected_clue_cell = None
            app_instance.highlighted_cells.clear()

        sync_card_highlights()
        refresh_side_panels()

    def apply_accepted_reveal(
        cell_id: str,
        role: Role,
        step_dict: Dict[str, Any],
        from_user_click: bool = False,
    ) -> None:
        """Flips a single card in-place with 3D animation, particles, and sound."""
        new_clue = app_instance.engine.revealed_clues.get(cell_id)
        app_instance.hint_target_cell = None
        if new_clue:
            app_instance.selected_clue_cell = cell_id
            app_instance.highlighted_cells = set(new_clue.referenced_cells)

        app_instance.deduction_steps.append(step_dict)
        app_instance.update_metrics()

        # In-place flip on the single target card ONLY!
        if cell_id in card_views:
            card_views[cell_id].reveal_in_place(role, new_clue)

        sync_card_highlights()
        update_board_header_labels()
        refresh_side_panels()

        press_sfx = "press_inno" if role == Role.INNOCENT else "press_crim"
        sfx_kind = "flip_inno" if role == Role.INNOCENT else "flip_crim"
        # If triggered by AI step, also play the press_inno/press_crim tactile sound first
        pre_js = "" if from_user_click else f"window.GriductiveFX?.playSFX('{press_sfx}', 0); "

        if app_instance.engine.is_solved():
            set_status_bar(
                "★ CASE SOLVED! All suspects identified 100% via pure deductive logic!",
                "accepted",
            )
            refresh_navigation()
            ui.run_javascript(
                f"{pre_js}"
                f"window.GriductiveFX?.celebrateCard('card_{cell_id}', '{role.value}'); "
                f"window.GriductiveFX?.playSFX('victory', 95);"
            )
        else:
            clue_txt = f' — Clue: "{new_clue.text}"' if new_clue else ""
            set_status_bar(
                f"✓ ACCEPTED! {cell_id} is {role.value}{clue_txt}",
                "accepted",
            )
            ui.run_javascript(
                f"{pre_js}"
                f"window.GriductiveFX?.celebrateCard('card_{cell_id}', '{role.value}'); "
                f"window.GriductiveFX?.playSFX('{sfx_kind}', 95);"
            )

    def on_verdict_click(cell_id: str, verdict: Role) -> None:
        res = app_instance.engine.submit_verdict(cell_id, verdict, app_instance.agent)

        if res == VerdictResult.ACCEPTED:
            new_clue = app_instance.engine.revealed_clues.get(cell_id)
            step_data = {
                "step_number": len(app_instance.deduction_steps) + 1,
                "target_cell": cell_id,
                "verdict": verdict.value,
                "sat_queries_count": 2,
                "newly_revealed_clue": new_clue.text if new_clue else None,
                "decisions": app_instance.agent.cumulative_metrics.decisions,
                "runtime_ms": round(app_instance.agent.cumulative_metrics.runtime_ms, 2),
            }
            apply_accepted_reveal(cell_id, verdict, step_data, from_user_click=True)

        elif res == VerdictResult.NOT_PROVABLE:
            app_instance.update_metrics()
            set_status_bar(
                f"⚠️ NOT PROVABLE! {cell_id} is not logically forced yet — Do not guess!",
                "warning",
            )
            refresh_side_panels()
            ui.run_javascript(
                f"window.GriductiveFX?.shakeCard('card_{cell_id}'); "
                f"window.GriductiveFX?.playSFX('not_provable', 95);"
            )

        elif res == VerdictResult.CONTRADICTED:
            app_instance.update_metrics()
            set_status_bar(
                f"❌ CONTRADICTED! The opposite verdict for {cell_id} is logically forced by current clues!",
                "error",
            )
            refresh_side_panels()
            ui.run_javascript(
                f"window.GriductiveFX?.shakeCard('card_{cell_id}'); "
                f"window.GriductiveFX?.playSFX('contradicted', 95);"
            )

    def on_hint_click() -> None:
        pub_state = app_instance.engine.get_public_state()
        hint = app_instance.agent.get_hint(pub_state)
        if hint is None:
            set_status_bar("Board is already solved! Click NEXT STAGE ▶ to continue.", "info")
            return

        cid = hint["cell_id"]
        role = hint["verdict"]
        name = hint["character_name"]
        app_instance.hint_target_cell = cid
        app_instance.highlighted_cells = {cid}
        app_instance.update_metrics()

        sync_card_highlights()
        refresh_side_panels()
        set_status_bar(
            f"💡 HINT: {name} ({cid}) is logically forced to be {role.value}!",
            "warning",
        )
        ui.run_javascript("window.GriductiveFX?.playSFX('hint');")

    def on_step_ai_click() -> None:
        step = app_instance.agent.step_solve(app_instance.engine)
        if step:
            apply_accepted_reveal(step.target_cell, step.verdict, step.to_dict())
        else:
            set_status_bar("Board is already completely solved!", "info")

    async def on_auto_solve_click() -> None:
        if app_instance.is_auto_solving:
            app_instance.is_auto_solving = False
            auto_btn.text = "⚡ AUTO SOLVE"
            set_status_bar("Auto-Solve paused.", "info")
            return

        if app_instance.engine.is_solved():
            set_status_bar("Case is already solved!", "accepted")
            return

        app_instance.is_auto_solving = True
        auto_btn.text = "⏹ STOP AI"
        set_status_bar("🤖 AI Detective running step-by-step deduction...", "info")

        while not app_instance.engine.is_solved() and app_instance.is_auto_solving:
            step = app_instance.agent.step_solve(app_instance.engine)
            if step is None:
                break
            apply_accepted_reveal(step.target_cell, step.verdict, step.to_dict())
            await asyncio.sleep(app_instance.auto_solve_delay)

        app_instance.is_auto_solving = False
        auto_btn.text = "⚡ AUTO SOLVE"

    # Initial Render
    refresh_navigation()
    build_board_once()
    refresh_side_panels()
    set_status_bar(app_instance.status_text, app_instance.status_kind)


if __name__ in {"__main__", "__mp_main__"}:
    create_ui()
    ui.run(title="Griductive Solver - CSC14003", port=8080, reload=False)
