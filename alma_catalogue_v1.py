# alma_catalogue_v1.py
# V1 + DEBUG: ALMA lookup from catalog_index.parquet + two flags:
#   - Genizah (from NLI_GNIZA_ALMAs.list)
#   - Role: Parent / Child / Both (from CHILD PARENT ALMA.xlsx)
#
# DEBUG additions:
#   - Prints CWD and file list
#   - Prints progress markers before/after each load
#
# Notes:
# - We normalize ALMA IDs everywhere by extracting the long digit sequence.
# - We DO NOT show "Neither"; if not found in the role map we show "—".

import os
import re
import pandas as pd
import streamlit as st

# Files are in the SAME folder as this script (alma-lookup/)
CATALOG_PARQUET = "catalog_index.parquet"
GENIZA_LIST = "NLI_GNIZA_ALMAs.list"
CHILD_PARENT_XLSX = "CHILD PARENT ALMA.xlsx"


# ---------- Normalization ----------
def extract_alma(x) -> str | None:
    """Extract the first long digit sequence (ALMA-style) from any input."""
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
    out: set[str] = set()
    try:
        with open(GENIZA_LIST, "r", encoding="utf-8") as f:
            for line in f:
                alma = extract_alma(line)
                if alma:
                    out.add(alma)
    except FileNotFoundError:
        return set()
    return out


@st.cache_data
def load_role_map() -> dict[str, str]:
    """
    Build dict: ALMA -> 'Parent' / 'Child' / 'Both' from CHILD PARENT ALMA.xlsx
    Expected columns: 'child', 'parent'
    Parent field may contain multiple parents separated by '|||'.
    """
    try:
        hp = pd.read_excel(CHILD_PARENT_XLSX, dtype=str)
    except FileNotFoundError:
        return {}

    # We intentionally fail loudly if schema is unexpected (helps debugging)
    if "child" not in hp.columns or "parent" not in hp.columns:
        raise ValueError(
            "CHILD PARENT ALMA.xlsx must contain columns named exactly: 'child' and 'parent'. "
            f"Found columns: {hp.columns.tolist()}"
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
    if (
        "no restrictions" in t
        or "public domain" in t
        or "נחלת הכלל" in (text or "")
        or "ללא מגבלות" in (text or "")
    ):
        return "🟢"
    if "contract" in t or "attribution" in t:
        return "🟡"
    if "restricted" in t or "permission" in t or "אסור" in (text or ""):
        return "🔴"
    return "⚪"


# ---------- App ----------
st.set_page_config(page_title="ALMA Catalog Viewer — V1", layout="wide")
st.title("ALMA Catalog Viewer — V1")

# ---- DEBUG: environment visibility ----
st.subheader("DEBUG (temporary)")
st.write("DEBUG cwd:", os.getcwd())
try:
    st.write("DEBUG files in cwd:", sorted(os.listdir(".")))
except Exception as e:
    st.write("DEBUG could not list cwd files:", repr(e))

# ---- DEBUG: load steps ----
st.write("DEBUG: before load_catalog()")
catalog = load_catalog()
st.write("DEBUG: after load_catalog() — rows:", int(catalog.shape[0]), "cols:", int(catalog.shape[1]))

st.write("DEBUG: before load_geniza_set()")
geniza = load_geniza_set()
st.write("DEBUG: after load_geniza_set() — size:", len(geniza))

st.write("DEBUG: before load_role_map()")
role_map = load_role_map()
st.write("DEBUG: after load_role_map() — size:", len(role_map))

st.markdown("---")  # end debug section


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
    title_rem = rec.get("title_remainder", "") or ""
    library = rec.get("library", "") or ""
    shelfmark = rec.get("shelfmark", "") or ""
    city = rec.get("city", "") or ""
    country = rec.get("country", "") or ""
    rights_note = rec.get("rights_note", "") or ""
    access_level = rec.get("access_level", "") or ""
    terms_name = rec.get("terms_name", "") or ""
    terms_url = rec.get("terms_url", "") or ""

    # Flags
    is_geniza = alma in geniza
    role = role_map.get(alma, "—")  # do not show "Neither"

    c1, c2 = st.columns([2, 1], gap="large")

    with c1:
        st.subheader("Description")
        if title_rem.strip():
            st.write(f"**{title}** — {title_rem}")
        else:
            st.write(f"**{title}**" if title.strip() else "—")

        st.subheader("Holding")
        st.write(f"**Library:** {library or '—'}")
        st.write(f"**Shelfmark:** {shelfmark or '—'}")
        loc = ", ".join([x for x in [city, country] if isinstance(x, str) and x.strip()])
        st.write(f"**Location:** {loc or '—'}")

    with c2:
        st.subheader("Rights")
        rights_text = " ".join(
            [x for x in [access_level, rights_note] if isinstance(x, str) and x.strip()]
        )
        st.write(f"{rights_icon(rights_text)} **{terms_name or '—'}**")
        if terms_url and isinstance(terms_url, str) and terms_url.strip():
            st.write(terms_url)
        if rights_text:
            st.caption(rights_text)

        st.subheader("Flags")
        st.write(f"**Genizah:** {'Yes' if is_geniza else 'No'}")
        st.write(f"**Role:** {role}")



