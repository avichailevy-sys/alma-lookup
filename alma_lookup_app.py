from pathlib import Path
import pandas as pd
import streamlit as st

# -----------------------------
# Config
# -----------------------------
DEFAULT_CHILD_PARENT_XLSX = Path("CHILD PARENT ALMA.xlsx")
PARENT_SEPARATOR = "|||"

GENIZA_LIST_FILE = Path("NLI_GNIZA_ALMAs.list")
MANUSCRIPTS_LIST_FILE = Path("NLI_MANUSCRIPTS_JPGS_ALMAs_only.list")


def clean_id(x) -> str:
    """Normalize ALMA IDs read from Excel/text."""
    if x is None:
        return ""
    s = str(x).strip()

    # Remove Excel "force-text" apostrophe if present
    if s.startswith("'"):
        s = s[1:].strip()

    # Remove internal whitespace (copy/paste artifacts)
    s = s.replace(" ", "").replace("\t", "")

    # Remove RTL marks if present
    s = s.replace("\u200f", "").replace("\u200e", "")

    return s


@st.cache_data(show_spinner=True)
def load_graph(xlsx_path: str):
    """
    Load child-parent table, normalize parent lists (split by '|||'),
    and build adjacency maps:
      - child_to_parents: child -> set(parents)
      - parent_to_children: parent -> set(children)
    """
    df = pd.read_excel(xlsx_path, dtype=str, engine="openpyxl").fillna("")

    # Find columns robustly
    child_col_candidates = [c for c in df.columns if "child" in c.lower()]
    parent_col_candidates = [c for c in df.columns if "parent" in c.lower()]

    if not child_col_candidates or not parent_col_candidates:
        raise ValueError(
            "Couldn't find columns containing 'child' and 'parent' in the Excel file."
        )

    child_col = child_col_candidates[0]
    parent_col = parent_col_candidates[0]

    child_to_parents: dict[str, set[str]] = {}
    parent_to_children: dict[str, set[str]] = {}

    for _, row in df.iterrows():
        child = clean_id(row[child_col])
        parent_field = str(row[parent_col] or "").strip()

        if not child:
            continue

        # Split multiple parents in one cell
        parents = []
        if parent_field:
            parts = [p.strip() for p in parent_field.split(PARENT_SEPARATOR)]
            parents = [clean_id(p) for p in parts if clean_id(p)]

        if child not in child_to_parents:
            child_to_parents[child] = set()

        for p in parents:
            child_to_parents[child].add(p)
            parent_to_children.setdefault(p, set()).add(child)

    return child_to_parents, parent_to_children


@st.cache_data(show_spinner=False)
def load_alma_list(path: str) -> set[str]:
    """
    Load a .list file (one ALMA per line) into a set.
    Ignores empty lines and comment lines starting with #.
    """
    p = Path(path)
    if not p.exists():
        return set()

    ids: set[str] = set()
    with open(p, "r", encoding="utf-8", errors="ignore") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            s = clean_id(line)
            if s:
                ids.add(s)
    return ids


# -----------------------------
# UI
# -----------------------------
st.set_page_config(page_title="ALMA Parent/Child Lookup", layout="wide")
st.title("ALMA Parent/Child Lookup")

st.write(
    "Enter an **ALMA ID** and get:\n"
    "1) If it is a **child** → its **parent(s)**\n"
    "2) If it is a **parent** → its **children**\n"
    "3) Whether it belongs to the **GENIZA** list and/or **MANUSCRIPTS** list\n"
    "\n*(A record may be both a child and a parent.)*"
)

with st.sidebar:
    st.header("Data file")
    uploaded = st.file_uploader("Upload CHILD PARENT ALMA.xlsx (optional)", type=["xlsx"])

    if uploaded is None:
        xlsx_path = str(DEFAULT_CHILD_PARENT_XLSX)
    else:
        tmp_path = Path("uploaded_CHILD_PARENT_ALMA.xlsx")
        tmp_path.write_bytes(uploaded.read())
        xlsx_path = str(tmp_path)

# Load mappings (silently; spinner is fine)
try:
    child_to_parents, parent_to_children = load_graph(xlsx_path)
except Exception as e:
    st.error(f"Failed to load child/parent Excel: {e}")
    st.stop()

# Load list files (silently)
geniza_ids = load_alma_list(str(GENIZA_LIST_FILE))
manuscripts_ids = load_alma_list(str(MANUSCRIPTS_LIST_FILE))

alma_in = st.text_input("Enter ALMA ID", placeholder="e.g. 990000907150205000")
alma = clean_id(alma_in)

if not alma:
    st.caption("Enter an ALMA ID above to see results.")
    st.stop()

# Membership
in_geniza = alma in geniza_ids
in_manuscripts = alma in manuscripts_ids

st.subheader("List membership")
if in_geniza and in_manuscripts:
    st.write("✅ GENIZA: **YES**  |  ✅ MANUSCRIPTS: **YES**")
elif in_geniza:
    st.write("✅ GENIZA: **YES**  |  ❌ MANUSCRIPTS: **NO**")
elif in_manuscripts:
    st.write("❌ GENIZA: **NO**  |  ✅ MANUSCRIPTS: **YES**")
else:
    st.write("❌ GENIZA: **NO**  |  ❌ MANUSCRIPTS: **NO**")

col1, col2 = st.columns(2)

# As CHILD → parents
with col1:
    st.subheader("As CHILD → Parents")
    parents = sorted(child_to_parents.get(alma, set()))
    if parents:
        st.write(f"Parents found: **{len(parents)}**")
        st.code("\n".join(parents))
        st.download_button(
            "Download parents as TXT",
            data=("\n".join(parents) + "\n").encode("utf-8"),
            file_name=f"{alma}_parents.txt",
            mime="text/plain",
        )
    else:
        st.info("This ALMA does not appear as a child (no parents listed in this table).")

# As PARENT → children
with col2:
    st.subheader("As PARENT → Children")
    children = sorted(parent_to_children.get(alma, set()))
    if children:
        st.write(f"Children found: **{len(children)}**")
        st.code("\n".join(children))
        st.download_button(
            "Download children as TXT",
            data=("\n".join(children) + "\n").encode("utf-8"),
            file_name=f"{alma}_children.txt",
            mime="text/plain",
        )
    else:
        st.info("This ALMA does not appear as a parent (no children listed in this table).")

st.markdown("---")
st.subheader("Summary")
is_child = alma in child_to_parents and len(child_to_parents[alma]) > 0
is_parent = alma in parent_to_children and len(parent_to_children[alma]) > 0

st.write(
    f"- Appears as **child**: {'✅' if is_child else '❌'}\n"
    f"- Appears as **parent**: {'✅' if is_parent else '❌'}"
)


