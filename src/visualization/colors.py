"""공유 컬러 팔레트 - Instagram 브랜드 + 등급/카테고리별 색상"""

# ── Instagram 그라디언트 팔레트 ──────────────────────────────────
INSTAGRAM_COLORS = {
    "pink": "#E1306C",
    "orange": "#F77737",
    "yellow": "#FCAF45",
    "purple": "#833AB4",
    "blue": "#405DE6",
    "gradient": ["#E1306C", "#F77737", "#FCAF45"],
}

# ── 등급(Grade)별 색상 ──────────────────────────────────────────
GRADE_COLORS = {
    "hot": {"hex": "#E1306C", "rgb": (0.88, 0.19, 0.42), "bg_hex": "#FCE4EC"},
    "rising": {"hex": "#F77737", "rgb": (0.97, 0.47, 0.22), "bg_hex": "#FFF3E0"},
    "stable": {"hex": "#9E9E9E", "rgb": (0.62, 0.62, 0.62), "bg_hex": "#F5F5F5"},
}

# ── 카테고리별 색상 ─────────────────────────────────────────────
CATEGORY_COLORS = {
    "celeb":     {"hex": "#833AB4", "rgb": (0.51, 0.23, 0.71), "name": "셀럽/인플루언서"},
    "brand":     {"hex": "#405DE6", "rgb": (0.25, 0.36, 0.90), "name": "브랜드"},
    "item":      {"hex": "#2ECC71", "rgb": (0.18, 0.80, 0.44), "name": "패션 아이템"},
    "style":     {"hex": "#E1306C", "rgb": (0.88, 0.19, 0.42), "name": "스타일/무드"},
    "beauty":    {"hex": "#FF6B9D", "rgb": (1.00, 0.42, 0.62), "name": "뷰티"},
    "lifestyle": {"hex": "#F39C12", "rgb": (0.95, 0.61, 0.07), "name": "라이프스타일"},
    "event":     {"hex": "#1ABC9C", "rgb": (0.10, 0.74, 0.61), "name": "이벤트/시즌"},
    "general":   {"hex": "#9E9E9E", "rgb": (0.62, 0.62, 0.62), "name": "일반"},
}

# ── Google Sheets용 RGB 딕셔너리 (0~1 범위) ─────────────────────
SHEETS_HEADER_BG = {"red": 0.88, "green": 0.19, "blue": 0.42}  # Instagram 핑크
SHEETS_HEADER_FG = {"red": 1.0, "green": 1.0, "blue": 1.0}  # 흰색
SHEETS_BORDER_COLOR = {"red": 0.85, "green": 0.85, "blue": 0.85}  # 연한 회색

SHEETS_GRADE_BG = {
    "hot": {"red": 0.99, "green": 0.89, "blue": 0.93},      # 연핑크
    "rising": {"red": 1.0, "green": 0.95, "blue": 0.88},     # 연오렌지
    "stable": {"red": 0.96, "green": 0.96, "blue": 0.96},    # 연회색
}

SHEETS_GRADIENT = {
    "min": {"red": 1.0, "green": 1.0, "blue": 1.0},         # 흰색
    "max": {"red": 0.88, "green": 0.19, "blue": 0.42},      # Instagram 핑크
}

SHEETS_TAB_COLORS = {
    "hashtag": {"red": 0.88, "green": 0.19, "blue": 0.42},   # 핑크
    "viral": {"red": 0.97, "green": 0.47, "blue": 0.22},     # 오렌지
    "insight": {"red": 0.99, "green": 0.69, "blue": 0.27},   # 노랑
    "glossary": {"red": 0.51, "green": 0.23, "blue": 0.71},  # 보라
    "info": {"red": 0.25, "green": 0.36, "blue": 0.90},      # 파랑
}

# ── Plotly용 색상 시퀀스 ────────────────────────────────────────
PLOTLY_GRADE_COLORS = {
    "🔥 Hot": "#E1306C",
    "📈 Rising": "#F77737",
    "⚪ Stable": "#9E9E9E",
}

PLOTLY_CATEGORY_SEQUENCE = [
    CATEGORY_COLORS["celeb"]["hex"],
    CATEGORY_COLORS["brand"]["hex"],
    CATEGORY_COLORS["item"]["hex"],
    CATEGORY_COLORS["style"]["hex"],
    CATEGORY_COLORS["beauty"]["hex"],
    CATEGORY_COLORS["lifestyle"]["hex"],
    CATEGORY_COLORS["event"]["hex"],
    CATEGORY_COLORS["general"]["hex"],
]
