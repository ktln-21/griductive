"""
Bilingual Localization (VI | EN) for Griductive Solver UI.
Synchronizes all UI labels, chapter/stage names, occupations, roles,
clue texts, metrics, and deduction logs into either Vietnamese (VI) or English (EN).
"""
import re
from typing import Dict
from core.models import Role


OCCUPATION_VI: Dict[str, str] = {
    "Guard": "Bảo vệ",
    "Detective": "Thám tử",
    "Cook": "Đầu bếp",
    "Clerk": "Thư ký",
    "Doctor": "Bác sĩ",
    "Judge": "Thẩm phán",
    "Pilot": "Phi công",
    "Farmer": "Nông dân",
    "Florist": "Chủ tiệm hoa",
    "Sailor": "Thủy thủ",
    "Artist": "Họa sĩ",
    "Tailor": "Thợ may",
    "Miner": "Thợ mỏ",
    "Baker": "Thợ bánh",
    "Smith": "Thợ rèn",
    "Potter": "Thợ gốm",
    "Barber": "Thợ cắt tóc",
    "Butler": "Quản gia",
    "Waiter": "Phục vụ",
    "Nurse": "Y tá",
    "Banker": "Ngân hàng",
    "Lawyer": "Luật sư",
    "Writer": "Nhà văn",
    "Chemist": "Dược sĩ",
    "Miller": "Thợ xay",
    "Suspect": "Nghi phạm",
}


UI_TEXT: Dict[str, Dict[str, str]] = {
    "EN": {
        "chap_1": "Chap 1 (3x3)",
        "chap_2": "Chap 2 (4x4)",
        "chap_3": "Chap 3 (4x4/5x5)",
        "chap_4": "Chap 4 (5x5 Stress)",
        "prev_btn": "◀ PREV",
        "next_btn": "NEXT ▶",
        "next_stage_btn": "NEXT STAGE ▶",
        "restart_btn": "🔄 RESTART",
        "hint_btn": "💡 HINT",
        "step_ai_btn": "🤖 STEP AI",
        "auto_solve_btn": "⚡ AUTO SOLVE",
        "stop_ai_btn": "⏹ STOP AI",
        "sound_config_title": "🎛️ SOUND & SPEED CONFIG",
        "bgm_on": "🎵 BGM: ON",
        "bgm_off": "🎵 BGM: OFF",
        "track_label": "Track:",
        "bgm_vol_label": "BGM Vol",
        "sfx_vol_label": "SFX Vol",
        "ai_speed_label": "AI Speed",
        "active_clues_title": "📋 ACTIVE CLUES",
        "active_clues_sub": "Click clue to highlight region",
        "no_clues_yet": "No clues revealed yet.",
        "metrics_title": "⚙️ CNF & DPLL METRICS",
        "metrics_sub": "Pure Python SAT",
        "m_vars": "VARS",
        "m_clauses": "CLAUSES",
        "m_decisions": "DECISIONS",
        "m_unit_prop": "UNIT PROP",
        "m_backtracks": "BACKTRACKS",
        "m_time": "TIME (ms)",
        "trace_title": "📓 DEDUCTION TRACE LOG",
        "no_trace_yet": "No deductions recorded yet. Start investigating!",
        "suspect_question": "? SUSPECT ?",
        "btn_inno": "INNO",
        "btn_crim": "CRIM",
        "role_inno": "INNOCENT",
        "role_crim": "CRIMINAL",
        "no_clue": "No clue.",
        "highlight_cleared": "Highlight cleared.",
    },
    "VI": {
        "chap_1": "Chương 1 (3x3)",
        "chap_2": "Chương 2 (4x4)",
        "chap_3": "Chương 3 (4x4/5x5)",
        "chap_4": "Chương 4 (5x5 Cực Khó)",
        "prev_btn": "◀ TRƯỚC",
        "next_btn": "SAU ▶",
        "next_stage_btn": "MÀN TIẾP ▶",
        "restart_btn": "🔄 CHƠI LẠI",
        "hint_btn": "💡 GỢI Ý",
        "step_ai_btn": "🤖 AI 1 BƯỚC",
        "auto_solve_btn": "⚡ TỰ ĐỘNG GIẢI",
        "stop_ai_btn": "⏹ DỪNG AI",
        "sound_config_title": "🎛️ ÂM THANH & TỐC ĐỘ",
        "bgm_on": "🎵 NHẠC: BẬT",
        "bgm_off": "🎵 NHẠC: TẮT",
        "track_label": "Nhạc nền:",
        "bgm_vol_label": "Âm lượng nhạc",
        "sfx_vol_label": "Hiệu ứng (SFX)",
        "ai_speed_label": "Tốc độ AI",
        "active_clues_title": "📋 MANH MỐI ĐÃ MỞ",
        "active_clues_sub": "Nhấn manh mối để soi vùng ô",
        "no_clues_yet": "Chưa có manh mối nào được mở.",
        "metrics_title": "⚙️ THỐNG KÊ CNF & DPLL",
        "metrics_sub": "SAT Thuần Python",
        "m_vars": "BIẾN (VARS)",
        "m_clauses": "MỆNH ĐỀ",
        "m_decisions": "NHÁNH (DEC)",
        "m_unit_prop": "LAN TRUYỀN",
        "m_backtracks": "QUAY LUI",
        "m_time": "THỜI GIAN",
        "trace_title": "📓 NHẬT KÝ SUY LUẬN",
        "no_trace_yet": "Chưa có bước suy luận nào. Hãy bắt đầu điều tra!",
        "suspect_question": "? NGHI PHẠM ?",
        "btn_inno": "VÔ TỘI",
        "btn_crim": "TỘI PHẠM",
        "role_inno": "VÔ TỘI",
        "role_crim": "TỘI PHẠM",
        "no_clue": "Không có manh mối.",
        "highlight_cleared": "Đã tắt vùng đánh dấu.",
    },
}


BGM_TRACKS_I18N: Dict[str, Dict[str, str]] = {
    "EN": {
        "noir": "🕵️ Noir Detective",
        "cyber": "⚡ Cyber Logic",
        "trial": "⚖️ Logic Trial",
        "chill": "☕ Midnight Study",
    },
    "VI": {
        "noir": "🕵️ Thám Tử Noir",
        "cyber": "⚡ Logic Điện Tử",
        "trial": "⚖️ Phiên Tòa Logic",
        "chill": "☕ Đêm Suy Luận",
    },
}


def t(key: str, lang: str = "VI") -> str:
    """Lookup a UI key in the active language ('VI' or 'EN')."""
    d = UI_TEXT.get(lang, UI_TEXT["EN"])
    return d.get(key, UI_TEXT["EN"].get(key, key))


def translate_occupation(occupation: str, lang: str = "VI") -> str:
    if lang != "VI":
        return occupation
    return OCCUPATION_VI.get(occupation, occupation)


def translate_role_str(role_val: str, lang: str = "VI") -> str:
    if lang != "VI":
        return role_val
    if role_val.upper() == "INNOCENT":
        return "VÔ TỘI"
    if role_val.upper() == "CRIMINAL":
        return "TỘI PHẠM"
    return "CHƯA RÕ"


def translate_stage_name(name: str, lang: str = "VI") -> str:
    if lang != "VI":
        return name
    out = name
    out = out.replace("Case #", "Vụ án #")
    out = out.replace("Rookie Detective", "Thám Tử Tập Sự")
    out = out.replace("Senior Inspector", "Thanh Tra Cao Cấp")
    out = out.replace("Mastermind", "Bậc Thầy Suy Luận")
    out = out.replace("Stress Test Suite", "Thử Thách Cực Hạn")
    out = out.replace("Tutorial: First Deduction", "Hướng Dẫn: Suy Luận Đầu Tiên")
    return out


def _translate_region_vi(reg_en: str) -> str:
    reg = reg_en.strip()
    m = re.match(r"^Row\s+(\d+)$", reg, re.IGNORECASE)
    if m:
        return f"Hàng {m.group(1)}"
    m = re.match(r"^Column\s+([A-Z])$", reg, re.IGNORECASE)
    if m:
        return f"Cột {m.group(1)}"
    if reg.lower() == "the 4 corners":
        return "4 ô góc"
    m = re.match(r"^common neighbors of\s+(.+?)\s+and\s+(.+)$", reg, re.IGNORECASE)
    if m:
        return f"các ô kề chung của {m.group(1)} và {m.group(2)}"
    m = re.match(r"^neighbors of\s+(.+)$", reg, re.IGNORECASE)
    if m:
        return f"các ô kề của {m.group(1)}"
    return reg


def _translate_target_vi(target_en: str) -> str:
    low = target_en.strip().lower()
    if "criminal" in low:
        return "Tội phạm"
    return "Người vô tội"


def translate_clue_text(text: str, lang: str = "VI") -> str:
    """
    Translates any English clue string into fluent Vietnamese when lang == 'VI',
    or returns the original English clue string when lang == 'EN'.
    """
    if not text or lang != "VI":
        return text

    s = text.strip()

    # 1. SAME status: "{n1} ({c1}) and {n2} ({c2}) have the SAME status."
    m = re.match(r"^(.+?)\s+and\s+(.+?)\s+have the SAME status\.$", s)
    if m:
        return f"{m.group(1)} và {m.group(2)} CÙNG PHE."

    # 2. DIFFERENT statuses: "{n1} ({c1}) and {n2} ({c2}) have DIFFERENT statuses."
    m = re.match(r"^(.+?)\s+and\s+(.+?)\s+have DIFFERENT statuses\.$", s)
    if m:
        return f"{m.group(1)} và {m.group(2)} KHÁC PHE."

    # 3. FACT: "{name} ({cid}) is a/an Criminal/Innocent."
    m = re.match(r"^(.+?)\s+is\s+(?:a|an)\s+(Criminal|Innocent)\.$", s, re.IGNORECASE)
    if m:
        role_vi = _translate_target_vi(m.group(2))
        return f"{m.group(1)} là {role_vi}."

    # 4. NO {target} in {reg}: "NO Criminals in Row 1."
    m = re.match(r"^NO\s+(Criminals?|Innocents?)\s+in\s+(.+)\.$", s, re.IGNORECASE)
    if m:
        role_vi = _translate_target_vi(m.group(1))
        reg_vi = _translate_region_vi(m.group(2))
        return f"KHÔNG CÓ {role_vi} nào ở {reg_vi}."

    # 5. Exactly {k} {target} in {reg}: "Exactly 2 Criminals in Row 1."
    m = re.match(r"^Exactly\s+(\d+)\s+(Criminals?|Innocents?)\s+in\s+(.+)\.$", s, re.IGNORECASE)
    if m:
        k = m.group(1)
        role_vi = _translate_target_vi(m.group(2))
        reg_vi = _translate_region_vi(m.group(3))
        return f"Có ĐÚNG {k} {role_vi} ở {reg_vi}."

    # 6. At least {k} {target} in {reg}
    m = re.match(r"^At least\s+(\d+)\s+(Criminals?|Innocents?)\s+in\s+(.+)\.$", s, re.IGNORECASE)
    if m:
        k = m.group(1)
        role_vi = _translate_target_vi(m.group(2))
        reg_vi = _translate_region_vi(m.group(3))
        return f"Có ÍT NHẤT {k} {role_vi} ở {reg_vi}."

    # 7. At most {k} {target} in {reg}
    m = re.match(r"^At most\s+(\d+)\s+(Criminals?|Innocents?)\s+in\s+(.+)\.$", s, re.IGNORECASE)
    if m:
        k = m.group(1)
        role_vi = _translate_target_vi(m.group(2))
        reg_vi = _translate_region_vi(m.group(3))
        return f"Có NHIỀU NHẤT {k} {role_vi} ở {reg_vi}."

    # 8. PARITY: "An ODD/EVEN number of {target} in {reg}."
    m = re.match(r"^An\s+(ODD|EVEN)\s+number of\s+(Criminals?|Innocents?)\s+in\s+(.+)\.$", s, re.IGNORECASE)
    if m:
        parity_vi = "số LẺ" if m.group(1).upper() == "ODD" else "số CHẴN"
        role_vi = _translate_target_vi(m.group(2))
        reg_vi = _translate_region_vi(m.group(3))
        return f"Số {role_vi} ở {reg_vi} là {parity_vi}."

    # 9. COMPARE_COUNT Equal: "Equal number of {target} in {desc_a} and {desc_b}."
    m = re.match(r"^Equal number of\s+(Criminals?|Innocents?)\s+in\s+(.+?)\s+and\s+(.+)\.$", s, re.IGNORECASE)
    if m:
        role_vi = _translate_target_vi(m.group(1))
        ra = _translate_region_vi(m.group(2))
        rb = _translate_region_vi(m.group(3))
        return f"Số {role_vi} ở {ra} BẰNG ở {rb}."

    # 10. COMPARE_COUNT MORE/FEWER: "MORE/FEWER {target} in {desc_a} than in {desc_b}."
    m = re.match(r"^(MORE|FEWER)\s+(Criminals?|Innocents?)\s+in\s+(.+?)\s+than in\s+(.+)\.$", s, re.IGNORECASE)
    if m:
        cmp_vi = "NHIỀU HƠN" if m.group(1).upper() == "MORE" else "ÍT HƠN"
        role_vi = _translate_target_vi(m.group(2))
        ra = _translate_region_vi(m.group(3))
        rb = _translate_region_vi(m.group(4))
        return f"Số {role_vi} ở {ra} {cmp_vi} ở {rb}."

    return s
