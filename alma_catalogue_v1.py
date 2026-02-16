import re
import pandas as pd
import streamlit as st

# Paths (app runs from alma-lookup/main/)
CATALOG_PARQUET = "catalog_index.parquet"
GENIZA_LIST = "NLI_GNIZA_ALMAs.list"
CHILD_PARENT_XLSX = "CHILD PARENT ALMA.xlsx"


# ---------- Utilities ----------
def extract_alma(x):
    """Extract numeric ALMA from any text."""
    if x is None:
        return None
    m = re.search(r"\d{6,}", str(x))
    return m.group(0) if m else None


# ---------- Loaders ----------
@st.cache_data
def load_catalog():
    df = pd.read_parquet(CATALOG_PARQUET)
    df["ALMA"] = df["ALMA"].astype(str).str.strip()
    return df.drop_duplicates("ALMA").set_index("ALMA")


@st.cache_data
def load_geniza_set():
    out = set()
    try:
        with open(GENIZA_LIST, "r", encoding="utf-8") as f:
            for line in f:
                alma = extract_alma(line)
                if alma:
                    out.add(alma)
    except FileNotFoundError:
        pass
    return out


@st.cache_data
def load_role_map():
    role = {}
    try:
        hp = pd.read_excel(CHILD_PARENT_XLSX, dtype=str)
    except FileNotFoundError:
        return role

    parents = set()
    children = set()

    for _, row in hp.iterrows():
        child = extract_alma(row.get("child"))
        if child:
            children.add(child)

        parents_raw = row.get("parent")
        if isinstance(parents_raw, str) and parents_raw.strip():
            for p in parents_raw.split("|||"):
                p2 = extract_alma(p)
                if p2:
                    parents.add(p2)

    for a in parents:
        role[a] = "Parent"
    for a in children:
        role[a] = "Both" if a in role else "Child"

    return role


# ---------- Rights logic (simplified V1) ----------
def rights_status(access_level, rights_note):
    summary = (access_level or "").strip()
    details = (rights_note or "").strip()
    txt = (summary + " " + details).lower()

    if (
        "no restrictions" in txt
        or "public domain" in txt
        or "נחלת הכלל" in txt
        or "ללא מגבלות" in txt
    ):
        badge = "🟢"
        label = summary or "No restrictions"

    elif (
        "restricted" in txt
        or "permission" in txt
        or "all rights reserved" in txt
        or "אסור" in txt
    ):
        badge = "🔴"
        label = summary or "Restricted"

    elif (
        "contract" in txt
        or "attribution" in txt
        or "credit" in txt
    ):
        badge = "🟡"
        label = summary or "Limited terms"

    else:
        badge = "⚪"
        label = summary or "Unknown"

    return badge, label, details


# ---------- App ----------
st.set_page_config(page_title="ALMA Catalog Viewer", layout="wide")
st.title("ALMA Catalog Viewer — V1")

catalog = load_catalog()
geniza = load_geniza_set()
role_map = load_role_map()

raw = st.text_input("ALMA ID").strip()
alma = extract_alma(raw)

if raw and not alma:
    st.error("Please enter a valid numeric ALMA ID.")
    st.stop()

if alma:
    if alma not in catalog.index:
        st.error("Not found in catalog_index.parquet")
        st.stop()

    rec = catalog.loc[alma]

    # Catalog fields
    title = rec.get("title", "")
    title_rem = rec.get("title_remainder", "")
    library = rec.get("library", "")
    shelfmark = rec.get("shelfmark", "")
    city = rec.get("city", "")
    country = rec.get("country", "")
    rights_note = rec.get("rights_note", "")
    access_level = rec.get("access_level", "")

    # Flags
    is_geniza = alma in geniza
    role = role_map.get(alma, "—")

    col1, col2 = st.columns([2, 1])

    # ---------- Left column ----------
    with col1:
        st.subheader("Description")
        if title_rem:
            st.write(f"**{title}** — {title_rem}")
        else:
            st.write(title or "—")

        st.subheader("Holding")
        st.write(f"Library: {library or '—'}")
        st.write(f"Shelfmark: {shelfmark or '—'}")
        location = ", ".join([x for x in [city, country] if x])
        st.write(f"Location: {location or '—'}")

    # ---------- Right column ----------
    with col2:
        st.subheader("Rights")

        badge, label, details = rights_status(access_level, rights_note)
        st.write(f"{badge} **{label}**")

        # Optional detailed text
        if details:
            with st.expander("Show rights details"):
                st.write(details)

        st.subheader("Flags")
        st.write(f"Genizah: {'Yes' if is_geniza else 'No'}")
        st.write(f"Role: {role}")


