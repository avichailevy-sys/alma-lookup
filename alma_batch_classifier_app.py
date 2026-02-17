from pathlib import Path
import re
import pandas as pd
import streamlit as st

# -----------------------------
# Config (repo files)
# -----------------------------
CHILD_PARENT_XLSX = Path("CHILD PARENT ALMA.xlsx")
GENIZA_LIST_FILE = Path("NLI_GNIZA_ALMAs.list")
PARENT_SEPARATOR = "|||"

# Extract long digit sequences as ALMA IDs (robust for messy lines)
ALMA_RE = re.compile(r"\d{8,}")


def clean_line(s: str) -> str:
    """Light cleanup for weird invisible chars; keep it simple."""
    if s is None:
        return ""
    s = str(s)
    s = s.replace("\u200f", "").replace("\u200e", "")  # RTL marks
    s = s.replace("\ufeff", "")  # BOM
    return s.strip()


def extract_almas_from_text(text: str) -> list[str]:
    """Extract ALMA-like digit sequences from a text blob, preserving order and deduping."""
    seen = set()
    ordered = []
    for line in text.splitlines():
        line = clean_line(line)
        if not line or line.startswith("#"):
            continue
        for m in ALMA_RE.findall(line):
            if m not in seen:
                seen.add(m)
                ordered.append(m)
    return ordered


def parse_uploaded_txt(file_bytes: bytes) -> list[str]:
    """Parse uploaded TXT and extract ALMA IDs robustly."""
    text = file_bytes.decode("utf-8", errors="ignore")
    return extract_almas_from_text(text)


@st.cache_data(show_spinner=True)
def load_geniza_set() -> set[str]:
    """Load GENIZA list and extract ALMA IDs robustly."""
    if not GENIZA_LIST_FILE.exists():
        raise FileNotFoundError(f"Missing file in repo: {GENIZA_LIST_FILE}")

    text = GENIZA_LIST_FILE.read_text(encoding="utf-8", errors="ignore")
    almas = extract_almas_from_text(text)
    return set(almas)


@st.cache_data(show_spinner=True)
def load_graph() -> tuple[dict[str, set[str]], dict[str, set[str]]]:
    """
    Build:
      child_to_parents: child -> set(parents)
      parent_to_children: parent -> set(children)
    Parent field may contain multiple parents separated by '|||'.
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
        child_raw = clean_line(row[child_col])
        if not child_raw:
            continue

        # Extract a child ALMA (first long digit sequence)
        child_ids = ALMA_RE.findall(child_raw)
        if not child_ids:
            continue
        child = child_ids[0]

        parent_field = clean_line(row[parent_col])
        parents: list[str] = []

        if parent_field:
            # Split by delimiter, then extract ALMA digits from each part (robust)
            parts = [clean_line(p) for p in parent_field.split(PARENT_SEPARATOR)]
            for part in parts:
                for pid in ALMA_RE.findall(part):
                    parents.append(pid)

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
st.set_page_config(page_title="Batch ALMA Classifier", layout="wide")
st.title("Batch ALMA Classifier")

st.write(
    "Upload a TXT file with ALMA IDs (one per line). The app will return:\n"
    "- **GENIZAH** vs **NOT GENIZAH**\n"
    "- Hierarchy roles: **parents only**, **children & parents**, **children only**\n"
)

# Check required repo files exist
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

# Load background data
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

ids = parse_uploaded_txt(uploaded.getvalue())
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

# -----------------------------
# C) Unique parents derived from submitted children (Daniel’s request)
# -----------------------------
st.subheader("Unique parents derived from submitted children")

# All submitted IDs that are children (children_only + children_and_parents)
submitted_children = children_only + children_and_parents

unique_parents = set()
parent_to_childcount: dict[str, int] = {}
mapping_rows = []

for child in submitted_children:
    parents = sorted(child_to_parents.get(child, set()))
    if not parents:
        continue

    unique_parents.update(parents)

    for p in parents:
        parent_to_childcount[p] = parent_to_childcount.get(p, 0) + 1

    mapping_rows.append({"Child": child, "Parents": f" {PARENT_SEPARATOR} ".join(parents)})

parents_list = sorted(unique_parents)

st.write(
    f"From **{len(submitted_children)}** submitted child ALMAs, found **{len(parents_list)}** unique parent ALMAs."
)

st.code("\n".join(parents_list) if parents_list else "(none)")

st.download_button(
    "Download UNIQUE_PARENTS.txt",
    data=to_txt(parents_list),
    file_name="UNIQUE_PARENTS.txt",
    mime="text/plain",
)

if parent_to_childcount:
    st.markdown("**Parents ranked by number of submitted children**")
    summary_df = (
        pd.DataFrame([{"Parent": p, "Children_in_upload": c} for p, c in parent_to_childcount.items()])
        .sort_values("Children_in_upload", ascending=False)
        .reset_index(drop=True)
    )
    st.dataframe(summary_df, use_container_width=True, hide_index=True)

if mapping_rows:
    with st.expander("Show child → parents mapping"):
        mapping_df = pd.DataFrame(mapping_rows)
        st.dataframe(mapping_df, use_container_width=True, hide_index=True)

        st.download_button(
            "Download CHILD_TO_PARENTS.csv",
            data=mapping_df.to_csv(index=False),
            file_name="CHILD_TO_PARENTS.csv",
            mime="text/csv",
        )

# -----------------------------
# D) Top-level parents & standalone (no parents)
# -----------------------------
st.subheader("Top-level parents and standalone (no parents)")

top_level_parents = []
standalone = []

for a in ids:
    has_parents = a in child_to_parents and len(child_to_parents[a]) > 0
    has_children = a in parent_to_children and len(parent_to_children[a]) > 0

    if not has_parents and has_children:
        top_level_parents.append(a)
    elif not has_parents and not has_children:
        standalone.append(a)

c1, c2 = st.columns(2)

with c1:
    st.markdown(f"**TOP-LEVEL PARENTS (has children)** ({len(top_level_parents)})")
    st.code("\n".join(top_level_parents) if top_level_parents else "(none)")
    st.download_button(
        "Download TOP_LEVEL_PARENTS.txt",
        data=to_txt(top_level_parents),
        file_name="TOP_LEVEL_PARENTS.txt",
        mime="text/plain",
    )

with c2:
    st.markdown(f"**STANDALONE (no children)** ({len(standalone)})")
    st.code("\n".join(standalone) if standalone else "(none)")
    st.download_button(
        "Download STANDALONE.txt",
        data=to_txt(standalone),
        file_name="STANDALONE.txt",
        mime="text/plain",
    )
