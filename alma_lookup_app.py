from pathlib import Path
import pandas as pd
import streamlit as st

# -----------------------------
# Config
# -----------------------------
DEFAULT_CHILD_PARENT_XLSX = Path("CHILD PARENT ALMA.xlsx")
PARENT_SEPARATOR = "|||"

def clean_id(x: str) -> str:
    """Normalize ALMA IDs read from Excel/text."""
    if x is None:
        return ""
    s = str(x).strip()
    # Remove Excel "force-text" apostrophe if present
    if s.startswith("'"):
        s = s[1:].strip()
    # Remove spaces inside (sometimes copy/paste inserts them)
    s = s.replace(" ", "")
    return s

@st.cache_data(show_spinner=True)
def load_graph(xlsx_path: str):
    """Load child-parent table, normalize parent lists, and build adjacency maps."""
    df = pd.read_excel(xlsx_path, dtype=str, engine="openpyxl").fillna("")

    # Find columns (robust if headers are slightly different)
    child_col_candidates = [c for c in df.columns if "child" in c.lower()]
    parent_col_candidates = [c for c in df.columns if "parent" in c.lower()]

    if not child_col_candidates or not parent_col_candidates:
        raise ValueError(
            f"Couldn't find columns containing 'child' and 'parent'. Found columns: {list(df.columns)}"
        )

    child_col = child_col_candidates[0]
    parent_col = parent_col_candidates[0]

    # Build maps
    child_to_parents = {}  # child -> set(parents)
    parent_to_children = {}  # parent -> set(children)

    for _, row in df.iterrows():
        child = clean_id(row[child_col])
        parent_field = str(row[parent_col] or "").strip()

        if not child:
            continue

        # Split parent field by the delimiter you showed (|||).
        # Also tolerate cases where it might be empty.
        parents = []
        if parent_field:
            parts = [p.strip() for p in parent_field.split(PARENT_SEPARATOR)]
            parents = [clean_id(p) for p in parts if clean_id(p)]

        # Update child -> parents
        if child not in child_to_parents:
            child_to_parents[child] = set()
        for p in parents:
            child_to_parents[child].add(p)

            # Update parent -> children
            if p not in parent_to_children:
                parent_to_children[p] = set()
            parent_to_children[p].add(child)

    return child_col, parent_col, child_to_parents, parent_to_children


# -----------------------------
# UI
# -----------------------------
st.set_page_config(page_title="ALMA Parent/Child Lookup", layout="wide")
st.title("ALMA Parent/Child Lookup")

st.write(
    "Enter an **ALMA ID** and get:\n"
    "1) If it is a **child** → its **parents**\n"
    "2) If it is a **parent** → its **children**\n"
    "(It can be both.)"
)

with st.sidebar:
    st.header("Data file")
    uploaded = st.file_uploader("Upload CHILD PARENT ALMA.xlsx", type=["xlsx"])
    if uploaded is None:
        st.caption(f"Using default path: `{DEFAULT_CHILD_PARENT_XLSX}`")
        xlsx_path = str(DEFAULT_CHILD_PARENT_XLSX)
    else:
        # Streamlit gives a file-like object; save to a temp path in app folder
        tmp_path = Path("uploaded_CHILD_PARENT_ALMA.xlsx")
        tmp_path.write_bytes(uploaded.read())
        xlsx_path = str(tmp_path)

try:
    child_col, parent_col, child_to_parents, parent_to_children = load_graph(xlsx_path)
except Exception as e:
    st.error(f"Failed to load file: {e}")
    st.stop()

st.success(
    f"Loaded mapping. Columns detected: child=`{child_col}` | parent=`{parent_col}` | "
    f"unique children={len(child_to_parents):,} | unique parents={len(parent_to_children):,}"
)

alma_in = st.text_input("Enter ALMA ID", placeholder="e.g. 990000907150205000")
alma = clean_id(alma_in)

col1, col2 = st.columns(2)

if alma:
    # CHILD SIDE
    with col1:
        st.subheader("As CHILD → Parents")
        parents = sorted(child_to_parents.get(alma, set()))
        if parents:
            st.write(f"**This ALMA appears as a child.** Parents found: **{len(parents)}**")
            st.code("\n".join(parents))
            st.download_button(
                "Download parents as TXT",
                data=("\n".join(parents) + "\n").encode("utf-8"),
                file_name=f"{alma}_parents.txt",
                mime="text/plain",
            )
        else:
            st.info("This ALMA does **not** appear as a child (no parents listed in this table).")

    # PARENT SIDE
    with col2:
        st.subheader("As PARENT → Children")
        children = sorted(parent_to_children.get(alma, set()))
        if children:
            st.write(f"**This ALMA appears as a parent.** Children found: **{len(children)}**")
            st.code("\n".join(children))
            st.download_button(
                "Download children as TXT",
                data=("\n".join(children) + "\n").encode("utf-8"),
                file_name=f"{alma}_children.txt",
                mime="text/plain",
            )
        else:
            st.info("This ALMA does **not** appear as a parent (no children listed in this table).")

    # BOTH?
    is_child = alma in child_to_parents and len(child_to_parents[alma]) > 0
    is_parent = alma in parent_to_children and len(parent_to_children[alma]) > 0
    st.markdown("---")
    st.subheader("Summary")
    st.write(
        f"- Appears as **child**: {'✅' if is_child else '❌'}\n"
        f"- Appears as **parent**: {'✅' if is_parent else '❌'}"
    )

else:
    st.caption("Enter an ALMA ID above to see results.")
