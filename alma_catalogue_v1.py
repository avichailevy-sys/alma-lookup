# alma_catalogue_v1.py
# V1: ALMA lookup from catalog_index.parquet + two flags:
#   - Genizah (from NLI_GNIZA_ALMAs.list)
#   - Role: Parent / Child / Both (from CHILD PARENT ALMA.xlsx)
#
# Notes:
# - We normalize ALMA IDs everywhere by extracting the long digit sequence.
# - We DO NOT show "Neither"; if not found in the role map we show "—".

import re
import pandas as pd
import streamlit as st

CATALOG_PARQUET = "../catalog_index.parquet"
GENIZA_LIST = "../NLI_GNIZA_ALMAs.list"
CHILD_PARENT_XLSX = "../CHILD PARENT ALMA.xlsx"


# ---------- Normalization ----------
def extract_alma(x) -> str | None:
    """
    Extract the first long digit sequence (ALMA-style) from any input.
    Returns None if no such sequence is found.
    """
    if x is None:
        return None
    m = re.search(r"\d{6,}", str(x))
    return m.group(0) if m else None


# ---------- Loaders ----------
@st.cache_data
def load_catalog() -> pd.DataFrame:
    df = pd.read_parquet(CATALOG_PARQUET)
    if "ALMA" not in df.columns:
        raise ValueError("catalog_index.parquet must contain a column named 'ALMA'")
    df["ALMA"] = df["ALMA"].astype(str).str.strip()
    df = df.dropna(subset=["ALMA"]).drop_duplicates(subset=["ALMA"]).set_index("ALMA")
    return df


@st.cache_data
def load_geniza_set() -> set[str]:
    try:
        out: set[str] = set()
        with open(GENIZA_LIST, "r", encoding="utf-8") as f:
            for line in f:
                alma = extract_alma(line)
                if alma:
                    out.add(alma)
        return out
    except FileNotFoundError:
        return set()


@st.cache_data
def load_role_map() -> dict[str, str]:
    """
    Build dict: ALMA -> 'Parent' / 'Child' / 'Both' from CHILD PARENT ALMA.xlsx
    Expected columns (confirmed by user): 'child', 'parent'
    Parent field may contain multiple parents separated by '|||'.
    """
    try:
        hp = pd.read_excel(CHILD_PARENT_XLSX, dtype=str)
    except FileNotFoundError:
        return {}

    if "child" not in hp.columns or "parent" not in hp.columns:
        # Keep V1 simple: fail loudly so you know the file schema isn't what we expect.
        raise ValueError(
            "CHILD PARENT ALMA.xlsx must contain columns named exactly: 'child' and 'parent'"
        )

    parents_set: set[str] = set()
    children_set: set[str] = set()

    for _, row in hp.iterrows():
        child = extract_alma(row.get("child"))
        if child:
            children_set.add(child)

        parents_raw = row.get("parent")
        if isinstance(parents_raw, str) and parents_raw.strip():
            for p in parents_raw.split("|||"):
                p2 = extract_alma(p)
                if p2:
                    parents_set.add(p2)

    role: dict[str, str] = {}
    for a in parents_set:
        role[a] = "Parent"
    for a in children_set:
        role[a] = "Both" if a in role else "Child"
    return role


# ---------- Rights indicator (simple V1) ----------
def rights_icon(text: str) -> str:
    t = (text or "").lower()
    if "no restrictions" in t or "public domain" in t or "נחלת הכלל" in (text or "") or "ללא מגבלות" in (text or ""):
        return "🟢"
    if "contract" in t or "attribution" in t:
        return "🟡"
    if "restricted" in t or "permission" in t or "אסור" in (text or ""):
        return "🔴"
    return "⚪"


# ---------- App ----------
st.set_page_config(page_title="ALMA Catalog Viewer — V1", layout="wide")
st.title("ALMA Catalog Viewer — V1")

# Load data
catalog = load_catalog()
geniza = load_geniza_set()
role_map = load_role_map()

raw = st.text_input("ALMA ID", placeholder="Paste the numeric ALMA ID").strip()
alma = extract_alma(raw)

if raw and not alma:
    st.error("No valid numeric ALMA ID detected.")
    st.stop()

if alma:
    if alma not in catalog.index:
        st.error("Not found in catalog_index.parquet")
        st.stop()

    rec = catalog.loc[alma]

    # Columns produced by your parquet build script
    title = rec.get("title", "") or ""
    title

