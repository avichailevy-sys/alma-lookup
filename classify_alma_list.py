from pathlib import Path
import pandas as pd
import streamlit as st

# -----------------------------
# Config (repo files)
# -----------------------------
CHILD_PARENT_XLSX = Path("CHILD PARENT ALMA.xlsx")
GENIZA_LIST_FILE = Path("NLI_GNIZA_ALMAs.list")
PARENT_SEPARATOR = "|||"


def clean_id(x) -> str:
    if x is None:
        return ""
    s = str(x).strip()
    if s.startswith("'"):
        s = s[1:].strip()
    s = s.replace(" ", "").replace("\t", "")
    s = s.replace("\u200f", "").replace("\u200e", "")  # RTL marks
    return s


def parse_txt_ids(file_bytes: bytes) -> list[str]:
    """
    Parse uploaded TXT: one ALMA per line.
    - Ignores empty lines and lines starting with '#'
    - Deduplicates while preserving order
    """
    text = file_bytes.decode("utf-8", errors="ignore")
    seen = set()
    ordered = []
    for line in text.splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        alma = clean_id(line)
        if alma and alma not in seen:
            seen.add(alma)
            ordered.append(alma)
    return ordered


@st.cache_data(show_spinner=True)
def load_geniza_set() -> set[str]:
    if not GENIZA_LIST_FILE.exists():
        raise FileNotFoundError(f"Missing file in repo: {GENIZA_LIST_FILE}")
    ids = set()
    with open(GENIZA_LIST_FILE, "r", encoding="utf-8", errors="ignore") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            s = clean_id(line)
            if s:
                ids.add(s)
    return ids


@st.cache_data(show_spinner=True)
def load_graph() -> tuple[dict[str, set[str]], dict[str, set[str]]]:
    """
    Build:
      child_to_parents: child -> set(parents)
      parent_to_children: parent -> set(children)
    """
    if not CHILD_PARENT_XLSX.exists():
        raise FileNotFoundError(f"Missing file in repo: {CHILD_PARENT_XLSX}")

    df = pd.read_excel(CHILD_PARENT_XLSX, dtype=str, engine="openpyxl").fillna("")

    child_cols = [c for c in df.columns if "child" in c.lower()]
    parent_cols = [c for c in df.columns if "parent" in c.lower()]
    if not child_cols or not parent_cols:
        raise ValueError(f"Could not find 'child'/'parent' columns. Columns: {list(df.columns)}")

    child_col = child_cols[0]
    parent_col = parent_cols[0]

    child_to_parents: dict[str, set[str]] = {}
    parent_to_children: dict[str, set[str]] = {}

    for _, row in df.iterrows():
        child = clean_id(row[child_col])
        parent_field = str(row[parent_col] or "").strip()
        if not child:
            continue

        parents = []
        if parent_field:
            parts = [p.strip() for p in parent_field.split(PARENT_SEPARATOR)]
            parents = [clean_id(p) for p in parts if clean_id(p)]

        child_to_parents.setdefault(child, set())
        for p in parents:
            child_to_parents[child].add(p)
            parent_to_children.setdefault(p, set()).add(child)

    return child_to_parents, parent_to_children


def to_txt(ids: list[str]) -> bytes:
    return ("\n".join(ids) + ("\n" if ids else "")).encode("utf-8")


# -----------------------------
# UI
# -----------------------------
st.set_page_config(page_title="ALMA Batch Classifier", layout="wide")
st.title("ALMA Batch Classifier")

st.write(
    "Upload a TXT file with **one ALMA ID per line**.\n\n"
    "The app will return:\n"
    "- **GENIZAH** vs **NOT GENIZAH**\n"
    "- Role lists: **parents only**, **children & parents**, **children only**"
)

# Hard requirement: repo files must exist
missing = []
if not GENIZA_LIST_FILE.exists():
    missing.append(str(GENIZA_LIST_FILE))
if not CHILD_PARENT_XLSX.exists():
    missing.append(str(CHILD_PARENT_XLSX))

if missing:
    st.error(
        "Missing required file(s) in the repository:\n\n- "
        + "\n- ".join(missing)
        + "\n\nUpload them to the repo (same folder as this app) and redeploy."
    )
    st.stop()

# Load background data (silent aside from the spinner)
try:
    geniza_set = load_geniza_set()
    child_to_parents, parent_to_children = load_graph()
except Exception as e:
    st.error(str(e))
    st.stop()

uploaded = st.file_uploader("Upload ALMA list (TXT)", type=["txt"])
if uploaded is None:
    st.caption("Upload a .txt file to continue.")
    st.stop()

ids = parse_txt_ids(uploaded.getvalue())
if not ids:
    st.error("No valid ALMA IDs found in the uploaded file.")
    st.stop()

# -----------------------------
# A) GENIZAH vs NOT GENIZAH
# -----------------------------
genizah = [a for a in ids if a in geniza_set]
not_genizah = [a for a in ids if a not in geniza_set]

st.subheader("GENIZAH vs NOT GENIZAH")
c1, c2 = st.columns(2)

with c1:
    st.markdown(f"**GENIZAH** ({len(genizah)})")
    st.code("\n".join(genizah) if genizah else "(none)")
    st.download_button(
        "Download GENIZAH.txt",
        data=to_txt(genizah),
        file_name="GENIZAH.txt",
        mime="text/plain",
    )

with c2:
    st.markdown(f"**NOT GENIZAH** ({len(not_genizah)})")
    st.code("\n".join(not_genizah) if not_genizah else "(none)")
    st.download_button(
        "Download NOT_GENIZAH.txt",
        data=to_txt(not_genizah),
        file_name="NOT_GENIZAH.txt",
        mime="text/plain",
    )

# -----------------------------
# B) Roles: parent/child
# -----------------------------
parents_only = []
children_and_parents = []
children_only = []

for a in ids:
    is_child = a in child_to_parents and len(child_to_parents[a]) > 0
    is_parent = a in parent_to_children and len(parent_to_children[a]) > 0

    if is_parent and not is_child:
        parents_only.append(a)
    elif is_parent and is_child:
        children_and_parents.append(a)
    elif (not is_parent) and is_child:
        children_only.append(a)
    # If neither, we intentionally ignore (per your request)

st.subheader("Hierarchy roles")

r1, r2, r3 = st.columns(3)

with r1:
    st.markdown(f"**PARENTS ONLY** ({len(parents_only)})")
    st.code("\n".join(parents_only) if parents_only else "(none)")
    st.download_button(
        "Download PARENTS_ONLY.txt",
        data=to_txt(parents_only),
        file_name="PARENTS_ONLY.txt",
        mime="text/plain",
    )

with r2:
    st.markdown(f"**CHILDREN AND PARENTS** ({len(children_and_parents)})")
    st.code("\n".join(children_and_parents) if children_and_parents else "(none)")
    st.download_button(
        "Download CHILDREN_AND_PARENTS.txt",
        data=to_txt(children_and_parents),
        file_name="CHILDREN_AND_PARENTS.txt",
        mime="text/plain",
    )

with r3:
    st.markdown(f"**CHILDREN ONLY** ({len(children_only)})")
    st.code("\n".join(children_only) if children_only else "(none)")
    st.download_button(
        "Download CHILDREN_ONLY.txt",
        data=to_txt(children_only),
        file_name="CHILDREN_ONLY.txt",
        mime="text/plain",
    )
