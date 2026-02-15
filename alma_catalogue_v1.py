import pandas as pd
import streamlit as st

CATALOG_PARQUET = "catalog_index.parquet"
GENIZA_LIST = "NLI_GNIZA_ALMAs.list"
CHILD_PARENT_XLSX = "CHILD PARENT ALMA.xlsx"

@st.cache_data
def load_catalog():
    df = pd.read_parquet(CATALOG_PARQUET)
    df["ALMA"] = df["ALMA"].astype(str).str.strip()
    return df.drop_duplicates("ALMA").set_index("ALMA")

@st.cache_data
def load_geniza_set():
    try:
        with open(GENIZA_LIST, "r", encoding="utf-8") as f:
            return set(line.strip() for line in f if line.strip())
    except FileNotFoundError:
        return set()

@st.cache_data
def load_role_map():
    try:
        hp = pd.read_excel(CHILD_PARENT_XLSX, dtype=str)
    except FileNotFoundError:
        return {}

    # Use first column as child, second as parent by default (simple V1)
    child_col = hp.columns[0]
    parent_col = hp.columns[1] if len(hp.columns) > 1 else hp.columns[0]

    parents_set, children_set = set(), set()

    for _, row in hp.iterrows():
        child = str(row.get(child_col, "")).strip()
        if child:
            children_set.add(child)

        parents_raw = str(row.get(parent_col, "")).strip()
        if parents_raw:
            for p in parents_raw.split("|||"):
                p = p.strip()
                if p:
                    parents_set.add(p)

    role = {}
    for a in parents_set:
        role[a] = "Parent"
    for a in children_set:
        role[a] = "Both" if a in role else "Child"
    return role

def rights_color(text: str) -> str:
    t = (text or "").lower()
    if "no restrictions" in t or "public domain" in t:
        return "🟢"
    if "contract" in t:
        return "🟡"
    if "restricted" in t or "permission" in t:
        return "🔴"
    return "⚪"

st.set_page_config(page_title="ALMA Catalog V1", layout="wide")
st.title("ALMA Catalog Viewer — V1")

catalog = load_catalog()
geniza = load_geniza_set()
role_map = load_role_map()

alma = st.text_input("ALMA ID").strip()

if alma:
    if alma not in catalog.index:
        st.error("Not found in catalog_index.parquet")
    else:
        rec = catalog.loc[alma]

        title = rec.get("title", "")
        title_rem = rec.get("title_remainder", "")
        library = rec.get("library", "")
        shelfmark = rec.get("shelfmark", "")
        city = rec.get("city", "")
        country = rec.get("country", "")
        rights_note = rec.get("rights_note", "")
        access_level = rec.get("access_level", "")
        terms_name = rec.get("terms_name", "")
        terms_url = rec.get("terms_url", "")

        is_geniza = alma in geniza
        role = role_map.get(alma, "Neither")

        c1, c2 = st.columns([2, 1])

        with c1:
            st.subheader("Description")
            if title_rem:
                st.write(f"{title} — {title_rem}")
            else:
                st.write(title)

            st.subheader("Holding")
            st.write(f"Library: {library}")
            st.write(f"Shelfmark: {shelfmark}")
            st.write(f"Location: {', '.join([x for x in [city, country] if x])}")

        with c2:
            st.subheader("Rights")
            rights_text = " ".join([x for x in [access_level, rights_note] if x])
            st.write(f"{rights_color(rights_text)} {terms_name or ''}")
            if terms_url:
                st.write(terms_url)
            st.caption(rights_text)

            st.subheader("Flags")
            st.write(f"Genizah: {'Yes' if is_geniza else 'No'}")
            st.write(f"Role: {role}")
