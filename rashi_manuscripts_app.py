"""
MiDRASH — Rashi Manuscripts Website
=====================================
A scholarly web application for browsing, viewing, and comparing
transcriptions of Rashi manuscript witnesses.

Part of the MiDRASH Project (Manuscript Indexing, Documentation,
Research, and Analysis of Scholarly Hebrew texts).
"""

import streamlit as st
import pandas as pd
from difflib import SequenceMatcher

# ─────────────────────────────────────────────────────────────────────────────
# PAGE CONFIG
# ─────────────────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="MiDRASH | Rashi Manuscripts",
    page_icon="📜",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─────────────────────────────────────────────────────────────────────────────
# STYLES
# ─────────────────────────────────────────────────────────────────────────────
STYLES = """
<style>
@import url('https://fonts.googleapis.com/css2?family=EB+Garamond:ital,wght@0,400;0,600;1,400&family=Source+Sans+3:wght@300;400;600&display=swap');

/* ── Background ────────────────────────────── */
[data-testid="stAppViewContainer"] {
    background-color: #faf8f3;
}
[data-testid="stMain"] > div {
    padding-top: 1.5rem;
}

/* ── Sidebar ────────────────────────────────── */
[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #1a1a2e 0%, #16213e 60%, #0f3460 100%);
}
[data-testid="stSidebar"] * {
    color: #d8d0c0 !important;
}
[data-testid="stSidebar"] .stRadio label {
    font-size: 0.95rem !important;
}

/* ── Typography ─────────────────────────────── */
h1 { font-family: 'EB Garamond', serif; color: #1a1005; font-size: 2.4rem !important; }
h2 { font-family: 'EB Garamond', serif; color: #2c1810; font-size: 1.8rem !important; }
h3 { font-family: 'EB Garamond', serif; color: #3d2415; font-size: 1.35rem !important; }
p, li { font-family: 'Source Sans 3', sans-serif; color: #2a2018; line-height: 1.7; }

/* ── Hero banner ────────────────────────────── */
.hero-banner {
    background: linear-gradient(135deg, #1a1a2e 0%, #16213e 50%, #0f3460 100%);
    color: #ede8d5;
    padding: 2.5rem 3rem;
    border-radius: 12px;
    margin-bottom: 2rem;
    border-left: 6px solid #c9a84c;
}
.hero-banner h1 { color: #f5e8c0 !important; margin: 0 0 0.3rem 0; font-size: 2.6rem !important; }
.hero-banner .subtitle { color: #a8b8c8; font-size: 1.05rem; margin-top: 0.5rem; }
.hero-banner .hebrew-title {
    font-family: 'SBL Hebrew','Ezra SIL','David','FrankRuehl','Times New Roman', serif;
    font-size: 1.6rem;
    color: #c9a84c;
    direction: rtl;
    display: block;
    margin-bottom: 0.4rem;
}

/* ── Stat boxes ─────────────────────────────── */
.stat-grid { display: flex; gap: 1rem; flex-wrap: wrap; margin: 1.5rem 0; }
.stat-box {
    flex: 1 1 140px;
    background: linear-gradient(135deg, #1a1a2e, #16213e);
    color: white;
    padding: 1.2rem 1rem;
    border-radius: 10px;
    text-align: center;
    border-bottom: 3px solid #c9a84c;
}
.stat-number { font-size: 2.2rem; font-weight: 700; color: #f0d090; display: block; }
.stat-label { font-size: 0.8rem; color: #8a9ab0; text-transform: uppercase; letter-spacing: 0.05em; }

/* ── Manuscript cards ───────────────────────── */
.ms-card {
    background: #ffffff;
    border: 1px solid #e0d5c0;
    border-radius: 10px;
    padding: 1.2rem 1.4rem;
    margin: 0.6rem 0;
    box-shadow: 0 2px 6px rgba(0,0,0,0.06);
    border-left: 4px solid #c9a84c;
}
.ms-card h4 {
    font-family: 'EB Garamond', serif;
    color: #2c1810;
    margin: 0 0 0.3rem 0;
    font-size: 1.1rem;
}
.ms-card .meta { font-size: 0.82rem; color: #6b5a48; margin: 0.15rem 0; }
.ms-card .hebrew-ms {
    font-family: 'SBL Hebrew','David','Times New Roman', serif;
    font-size: 1.05rem;
    color: #444;
    direction: rtl;
    display: block;
    margin-bottom: 0.3rem;
}

/* ── Status badges ──────────────────────────── */
.badge {
    display: inline-block;
    padding: 0.15rem 0.55rem;
    border-radius: 20px;
    font-size: 0.72rem;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.04em;
    margin: 0 0.2rem;
}
.badge-complete { background: #d4edda; color: #155724; }
.badge-partial  { background: #fff3cd; color: #856404; }
.badge-pending  { background: #f8d7da; color: #721c24; }
.badge-ashkenazi { background: #d1ecf1; color: #0c5460; }
.badge-sephardic { background: #e2d9f3; color: #432874; }
.badge-italian   { background: #fde8d0; color: #7a3b0c; }
.badge-french    { background: #d0e8f5; color: #0a3d5f; }

/* ── Hebrew transcription block ─────────────── */
.heb-block {
    direction: rtl;
    font-family: 'SBL Hebrew','Ezra SIL','David','FrankRuehl','Times New Roman', serif;
    font-size: 1.3rem;
    line-height: 2.1;
    text-align: right;
    background: #fffef9;
    border-right: 5px solid #c9a84c;
    border-radius: 0 8px 8px 0;
    padding: 1.1rem 1.5rem;
    margin: 0.8rem 0;
    color: #1a1010;
    box-shadow: inset 0 0 0 1px #e8dfc8;
}

/* ── Diff highlighting ──────────────────────── */
.diff-changed { background: #ffe082; padding: 0 2px; border-radius: 3px; }
.diff-removed { background: #ffcdd2; padding: 0 2px; border-radius: 3px; text-decoration: line-through; opacity: 0.7; }
.diff-added   { background: #c8e6c9; padding: 0 2px; border-radius: 3px; }

/* ── Compare panel ──────────────────────────── */
.compare-panel {
    background: #fffef9;
    border: 1px solid #d5c5a0;
    border-radius: 10px;
    padding: 1rem 1.2rem;
}
.compare-header {
    font-family: 'EB Garamond', serif;
    font-size: 1.05rem;
    font-weight: 600;
    color: #1a1a2e;
    border-bottom: 2px solid #c9a84c;
    padding-bottom: 0.4rem;
    margin-bottom: 0.8rem;
}

/* ── Section divider ────────────────────────── */
.section-head {
    font-family: 'EB Garamond', serif;
    font-size: 1.5rem;
    color: #2c1810;
    border-bottom: 2px solid #c9a84c;
    padding-bottom: 0.4rem;
    margin: 1.8rem 0 1rem 0;
}

/* ── Passage label ──────────────────────────── */
.passage-label {
    font-family: 'EB Garamond', serif;
    font-size: 1.0rem;
    color: #5a4030;
    background: #f5f0e8;
    display: inline-block;
    padding: 0.25rem 0.8rem;
    border-radius: 4px;
    margin-bottom: 0.5rem;
    border: 1px solid #d5c5a0;
}

/* ── Metadata table ─────────────────────────── */
.meta-table { width: 100%; border-collapse: collapse; }
.meta-table td { padding: 0.45rem 0.6rem; border-bottom: 1px solid #ede8d8; font-size: 0.9rem; }
.meta-table td:first-child { font-weight: 600; color: #5a4030; width: 40%; }
.meta-table td:last-child { color: #2a2018; }

/* ── Logo / project name ────────────────────── */
.sidebar-logo {
    text-align: center;
    padding: 1.5rem 0.5rem 1rem;
    border-bottom: 1px solid rgba(200,168,76,0.35);
    margin-bottom: 1rem;
}
.sidebar-logo .logo-heb {
    font-family: 'SBL Hebrew','David','Times New Roman', serif;
    font-size: 1.6rem;
    color: #c9a84c !important;
    display: block;
    direction: rtl;
}
.sidebar-logo .logo-en {
    font-family: 'EB Garamond', serif;
    font-size: 1.3rem;
    color: #e8dfc8 !important;
    font-weight: 600;
    display: block;
}
.sidebar-logo .logo-sub {
    font-size: 0.72rem;
    color: #7a8a9a !important;
    text-transform: uppercase;
    letter-spacing: 0.08em;
    display: block;
    margin-top: 0.3rem;
}

/* ── About section ──────────────────────────── */
.about-box {
    background: white;
    border: 1px solid #e0d5c0;
    border-radius: 10px;
    padding: 1.5rem 2rem;
    margin: 0.8rem 0;
    border-left: 5px solid #c9a84c;
}

/* ── Search highlight ───────────────────────── */
.search-hit { background: #fff9c4; font-weight: 600; }

/* ── Timeline ───────────────────────────────── */
.timeline { border-left: 3px solid #c9a84c; padding-left: 1.2rem; margin: 1rem 0; }
.timeline-item { margin-bottom: 1.2rem; position: relative; }
.timeline-item::before {
    content: '';
    width: 11px; height: 11px;
    background: #c9a84c; border-radius: 50%;
    position: absolute; left: -1.72rem; top: 0.35rem;
}
.timeline-date { font-size: 0.8rem; color: #7a6848; font-weight: 600; }
.timeline-title { font-family: 'EB Garamond', serif; font-size: 1.0rem; color: #1a1010; }
</style>
"""

# ─────────────────────────────────────────────────────────────────────────────
# DATA — PASSAGES (verses Rashi commented on, used for comparison)
# ─────────────────────────────────────────────────────────────────────────────
PASSAGES = {
    "gen_1_1":  "Genesis 1:1 — בְּרֵאשִׁית",
    "gen_1_2":  "Genesis 1:2 — תֹהוּ וָבֹהוּ",
    "gen_2_7":  "Genesis 2:7 — וַיִּיצֶר ה׳",
    "exod_3_14":"Exodus 3:14 — אֶהְיֶה אֲשֶׁר אֶהְיֶה",
    "exod_20_2":"Exodus 20:2 — עֲשֶׂרֶת הַדִּבְּרוֹת",
    "lev_1_1":  "Leviticus 1:1 — וַיִּקְרָא",
    "deut_6_4": "Deuteronomy 6:4 — שְׁמַע יִשְׂרָאֵל",
}

# Rashi commentary texts — each passage has a base text and named variants
# representing different manuscript traditions (all public domain / demo)
RASHI_TEXTS = {
    "gen_1_1": {
        "base": (
            "בְּרֵאשִׁית. אָמַר רַבִּי יִצְחָק, לֹא הָיָה צָרִיךְ לְהַתְחִיל אֶת הַתּוֹרָה "
            "אֶלָּא מֵהַחֹדֶשׁ הַזֶּה לָכֶם, שֶׁהִיא מִצְוָה רִאשׁוֹנָה שֶׁנִּצְטַוּוּ בָּהּ "
            "יִשְׂרָאֵל. וּמַה טַּעַם פָּתַח בִּבְרֵאשִׁית, מִשּׁוּם כֹּחַ מַעֲשָׂיו הִגִּיד "
            "לְעַמּוֹ לָתֵת לָהֶם נַחֲלַת גּוֹיִם."
        ),
        "v1": (
            "בְּרֵאשִׁית. אָמַר רַבִּי יִצְחָק, לֹא הָיָה צָרִיךְ לְהַתְחִיל הַתּוֹרָה "
            "אֶלָּא מֵהַחֹדֶשׁ הַזֶּה לָכֶם, שֶׁהִיא מִצְוָה רִאשׁוֹנָה שֶׁנִּצְטַוּוּ "
            "יִשְׂרָאֵל. וּמַה טַּעַם פָּתַח בִּבְרֵאשִׁית, מִשּׁוּם כֹּחַ מַעֲשָׂיו הִגִּיד "
            "לְעַמּוֹ לָתֵת לָהֶם נַחֲלַת גּוֹיִם."
        ),
        "v2": (
            "בְּרֵאשִׁית. אָמַר ר' יִצְחָק, לֹא הָיָה צָרִיךְ לְהַתְחִיל אֶת הַתּוֹרָה "
            "אֶלָּא מֵ'הַחֹדֶשׁ הַזֶּה לָכֶם', שֶׁהִיא מִצְוָה רִאשׁוֹנָה שֶׁנִּצְטַוּוּ בָּהּ "
            "בְּנֵי יִשְׂרָאֵל. וּמַה טַּעַם פָּתַח בִּבְרֵאשִׁית, מִפְּנֵי 'כֹּחַ מַעֲשָׂיו "
            "הִגִּיד לְעַמּוֹ לָתֵת לָהֶם נַחֲלַת גּוֹיִם'."
        ),
        "v3": (
            "בְּרֵאשִׁית בָּרָא. דָּרַשׁ רַבִּי יִצְחָק, לֹא הָיָה צָרִיךְ לְהַתְחִיל אֶת "
            "הַתּוֹרָה אֶלָּא מֵהַחֹדֶשׁ הַזֶּה לָכֶם, שֶׁהִיא מִצְוָה רִאשׁוֹנָה שֶׁנִּצְטַוּוּ "
            "בָּהּ יִשְׂרָאֵל. וּמַה טַּעַם פָּתַח בִּבְרֵאשִׁית, מִשּׁוּם שֶׁנֶּאֱמַר כֹּחַ "
            "מַעֲשָׂיו הִגִּיד לְעַמּוֹ לָתֵת לָהֶם נַחֲלַת גּוֹיִם."
        ),
    },
    "gen_1_2": {
        "base": (
            "וְהָאָרֶץ הָיְתָה תֹהוּ וָבֹהוּ. תֹּהוּ לְשׁוֹן שְׁמָמָה וְתֵהֶא. בֹּהוּ לְשׁוֹן "
            "עֲרֵבוּת וְרֵיקָנוּת. שְׁמֵי הַשָּׁמַיִם וְהַמַּיִם וְהַחֹשֶׁךְ הָיוּ בַּתְּחִלָּה, "
            "שֶׁהֲרֵי לֹא נֶאֱמַר בּוֹ בָּרָא."
        ),
        "v1": (
            "וְהָאָרֶץ הָיְתָה תֹהוּ וָבֹהוּ. תֹּהוּ — לְשׁוֹן שְׁמָמָה וְתֵהֶא. בֹּהוּ — "
            "לְשׁוֹן עֲרֵבוּת וְרֵיקָנוּת. שְׁמֵי הַשָּׁמַיִם וְהַמַּיִם וְהַחֹשֶׁךְ קָדְמוּ "
            "לַתְּחִלָּה."
        ),
        "v2": (
            "תֹהוּ וָבֹהוּ. תֹּהוּ לְשׁוֹן שְׁמָמָה, בֹּהוּ לְשׁוֹן רֵיקָנוּת וַחֲלָלִיּוּת. "
            "שְׁמֵי הַשָּׁמַיִם וְהַמַּיִם וְהַחֹשֶׁךְ הָיוּ בַּתְּחִלָּה כְּבָר."
        ),
        "v3": (
            "וְהָאָרֶץ הָיְתָה תֹהוּ וָבֹהוּ. פֵּרוּשׁ תֹּהוּ לְשׁוֹן שְׁמָמָה, וּבֹהוּ לְשׁוֹן "
            "עֲרֵבוּת וְרֵיקָנוּת. וּשְׁמֵי הַשָּׁמַיִם וְהַמַּיִם וְהַחֹשֶׁךְ הָיוּ בַּתְּחִלָּה."
        ),
    },
    "gen_2_7": {
        "base": (
            "וַיִּיצֶר ה' אֱלֹהִים. יוּ\"ד כְּפוּלָה, לְפִי שֶׁנִּבְרָא בִּשְׁתֵּי יְצִירוֹת, "
            "יְצִירַת עוֹלָם הַזֶּה וִיצִירַת עוֹלָם הַבָּא."
        ),
        "v1": (
            "וַיִּיצֶר. שְׁתֵּי יוּ\"דִין, לְפִי שֶׁהָאָדָם נִבְרָא בִּשְׁתֵּי יְצִירוֹת, "
            "יְצִירָה לְעוֹלָם הַזֶּה וִיצִירָה לְעוֹלָם הַבָּא."
        ),
        "v2": (
            "וַיִּיצֶר ה' אֱלֹהִים אֶת הָאָדָם. יו\"ד כְּפוּלָה, מְלַמֵּד שֶׁנִּבְרָא בִּשְׁתֵּי "
            "יְצִירוֹת, אַחַת לְחַיֵּי עוֹלָם הַזֶּה וְאַחַת לְחַיֵּי עוֹלָם הַבָּא."
        ),
        "v3": (
            "וַיִּיצֶר. נִכְתַּב בְּשְׁתֵּי יוּ\"דִין, כְּנֶגֶד שְׁתֵּי יְצִירוֹת שֶׁל הָאָדָם, "
            "יְצִירָה בָּעוֹלָם הַזֶּה וִיצִירָה בָּעוֹלָם הַבָּא."
        ),
    },
    "exod_3_14": {
        "base": (
            "אֶהְיֶה אֲשֶׁר אֶהְיֶה. אֶהְיֶה עִמָּהֶם בְּצָרָה זוֹ, אֲשֶׁר אֶהְיֶה עִמָּהֶם "
            "בַּשִּׁעְבּוּד שֶׁל מַלְכֻיּוֹת. אָמַר לוֹ מֹשֶׁה, רִבּוֹנוֹ שֶׁל עוֹלָם, לָמָּה "
            "לִי לְהַזְכִּיר לָהֶם צָרָה אַחֶרֶת."
        ),
        "v1": (
            "אֶהְיֶה אֲשֶׁר אֶהְיֶה. אֶהְיֶה עִמָּהֶם בְּצָרָה זוֹ, כַּאֲשֶׁר אֶהְיֶה עִמָּהֶם "
            "בַּשִּׁעְבּוּד שֶׁל מַלְכֻיּוֹת. אָמַר לוֹ מֹשֶׁה, רִבּוֹנוֹ שֶׁל עוֹלָם, מַה "
            "לִּי לְהַזְכִּיר לָהֶם צָרָה אַחֶרֶת."
        ),
        "v2": (
            "אֶהְיֶה אֲשֶׁר אֶהְיֶה. אֶהְיֶה עִמָּהֶם בְּצָרָה זוֹ, אֲשֶׁר אֶהְיֶה עִמָּהֶם "
            "בִּשְׁאָר שִׁעְבּוּדֵי הַמַּלְכֻיּוֹת. אָמַר לוֹ, רִבּוֹנוֹ שֶׁל עוֹלָם, לָמָּה "
            "לִי לְהַזְכִּיר לָהֶם צָרוֹת אֲחֵרוֹת."
        ),
        "v3": (
            "אֶהְיֶה אֲשֶׁר אֶהְיֶה. אֶהְיֶה עִמָּהֶם בְּצָרָה זוֹ, כֵּן אֶהְיֶה עִמָּהֶם "
            "בְּשִׁעְבּוּד הַמַּלְכֻיּוֹת. אָמַר מֹשֶׁה לִפְנֵי הַקָּדוֹשׁ בָּרוּךְ הוּא, "
            "רִבּוֹנוֹ שֶׁל עוֹלָם, לָמָּה לִי לְהַזְכִּיר לָהֶם צָרָה אַחֶרֶת."
        ),
    },
    "exod_20_2": {
        "base": (
            "אָנֹכִי ה' אֱלֹהֶיךָ. לָמָּה לֹא נֶאֱמַר בְּרֵאשִׁית הַדִּבְּרוֹת 'צַוֵּה' אוֹ "
            "'דַּבֵּר'? אֶלָּא שֶׁיִּהְיוּ יִשְׂרָאֵל מַכִּירִים אוֹתִי שֶׁהוֹצֵאתִי אוֹתָם "
            "מִמִּצְרַיִם."
        ),
        "v1": (
            "אָנֹכִי ה' אֱלֹהֶיךָ. לָמָּה לֹא נֶאֱמַר 'צַוֵּה' אוֹ 'דַּבֵּר'? אֶלָּא כְּדֵי "
            "שֶׁיִּהְיוּ יִשְׂרָאֵל מַכִּירִים אוֹתִי שֶׁהוֹצֵאתִי אוֹתָם מֵאֶרֶץ מִצְרַיִם."
        ),
        "v2": (
            "אָנֹכִי. מִדּוּעַ פָּתַח בְּלָשׁוֹן אָנֹכִי וְלֹא אָמַר 'אֲנִי'? אֶלָּא לְשׁוֹן "
            "מִצְרַיִם הָיָה בְּפִיהֶם. ה' אֱלֹהֶיךָ — שֶׁהוֹצֵאתִי אוֹתְךָ מֵאֶרֶץ מִצְרַיִם."
        ),
        "v3": (
            "אָנֹכִי ה' אֱלֹהֶיךָ. אָמַר לָהֶם, אֲנִי הוּא שֶׁיִּחַדְתֶּם לִי בְּמִצְרַיִם, "
            "קִבַּלְתֶּם מַלְכוּתִי אָז עֲלֵיכֶם. אֱלֹהֶיךָ — שֶׁהוֹצֵאתִי אֶתְכֶם מֵאֶרֶץ "
            "מִצְרַיִם."
        ),
    },
    "lev_1_1": {
        "base": (
            "וַיִּקְרָא אֶל מֹשֶׁה. לְכָל דִּבְּרוֹת וּלְכָל אֲמִירוֹת וּלְכָל צִוּוּיִים "
            "קָדְמָה קְרִיאָה, לְשׁוֹן חִבָּה, לְשׁוֹן שֶׁמַּלְאֲכֵי הַשָּׁרֵת מִשְׁתַּמְּשִׁין בּוֹ."
        ),
        "v1": (
            "וַיִּקְרָא אֶל מֹשֶׁה. לְכָל דִּבְּרוֹת וְאֲמִירוֹת וְצִוּוּיִים קָדְמָה קְרִיאָה, "
            "לְשׁוֹן שֶׁל חִבָּה, כְּלָשׁוֹן שֶׁמַּלְאֲכֵי הַשָּׁרֵת מִשְׁתַּמְּשִׁין בּוֹ."
        ),
        "v2": (
            "וַיִּקְרָא. בְּכָל אֲמִירָה וְדִבּוּר שֶׁדִּבֶּר הַקָּדוֹשׁ בָּרוּךְ הוּא אֶל מֹשֶׁה, "
            "קָדְמָה לָהֶם קְרִיאָה, לְשׁוֹן חִבָּה כְּדֶרֶךְ שֶׁהַמַּלְאָכִים קוֹרִים זֶה לָזֶה."
        ),
        "v3": (
            "וַיִּקְרָא אֶל מֹשֶׁה. לְכָל דִּבְּרוֹת ה' קָדְמָה הַקְּרִיאָה, שֶׁהִיא לְשׁוֹן "
            "חִבָּה וְחֶמְלָה, וְהִיא הַלָּשׁוֹן שֶׁבָּהּ מִשְׁתַּמְּשִׁים מַלְאֲכֵי הַשָּׁרֵת."
        ),
    },
    "deut_6_4": {
        "base": (
            "שְׁמַע יִשְׂרָאֵל. צִוָּה אוֹתָם שֶׁיִּקְרְאוּ אֶת שְׁמַע פַּעֲמַיִם בַּיּוֹם, "
            "שַׁחֲרִית וְעַרְבִית. שְׁמַע — שְׁמַע וְהַאֲמֵן כִּי ה' אֱלֹהֵינוּ, הוּא ה' אֶחָד."
        ),
        "v1": (
            "שְׁמַע יִשְׂרָאֵל. צִוָּה אוֹתָם שֶׁיִּקְרְאוּ אֶת שְׁמַע פַּעֲמַיִם בַּיּוֹם, "
            "שַׁחֲרִית וָעֶרֶב. שְׁמַע וְהַאֲמֵן כִּי ה' הוּא אֱלֹהֵינוּ וְהוּא אֶחָד."
        ),
        "v2": (
            "שְׁמַע יִשְׂרָאֵל ה' אֱלֹהֵינוּ. שְׁמַע — הֶאֱמֵן וְקַבֵּל עָלֶיךָ, כִּי ה' "
            "אֱלֹהֵינוּ הוּא לְבַדּוֹ. ה' אֶחָד — שֵׁם מְיֻחָד לוֹ בִּלְבַד."
        ),
        "v3": (
            "שְׁמַע יִשְׂרָאֵל. הַקְשֵׁב לְמַה שֶּׁאֲנִי מְצַוֶּה אוֹתְךָ, כִּי ה' אֱלֹהֵינוּ "
            "הוּא לְבַדּוֹ ה' הָאֶחָד. וְצִוָּה אוֹתָם לִקְרוֹא שְׁמַע שַׁחֲרִית וְעַרְבִית."
        ),
    },
}

# ─────────────────────────────────────────────────────────────────────────────
# DATA — MANUSCRIPTS
# ─────────────────────────────────────────────────────────────────────────────
MANUSCRIPTS = [
    {
        "id": "MS-MUN-001",
        "title": 'פירוש רש"י על התורה',
        "title_en": "Rashi's Commentary on the Torah",
        "short_name": "Munich 5",
        "date_display": "13th century",
        "date_approx": 1250,
        "repository": "Bavarian State Library",
        "shelfmark": "Cod.hebr. 5",
        "city": "Munich",
        "country": "Germany",
        "script": "Ashkenazi semi-cursive",
        "material": "Parchment",
        "folios": 234,
        "condition": "Good",
        "transcription_status": "Complete",
        "text_tradition": "Ashkenazi",
        "passage_variant": "base",
        "description": (
            "One of the earliest and most complete manuscripts of Rashi's Torah commentary, "
            "copied in Ashkenaz during the 13th century. Contains important textual variants "
            "not found in printed editions. The manuscript was acquired by the Bavarian State "
            "Library in the 19th century and is considered a primary witness for establishing "
            "the text of Rashi's commentary. Marginal corrections appear throughout in a "
            "later hand."
        ),
        "notes": "Contains marginal corrections in a later hand. Several passages show unique readings.",
    },
    {
        "id": "MS-VTK-002",
        "title": 'פירוש רש"י על התורה',
        "title_en": "Rashi's Commentary on the Torah",
        "short_name": "Vatican 38",
        "date_display": "Late 12th century",
        "date_approx": 1190,
        "repository": "Biblioteca Apostolica Vaticana",
        "shelfmark": "Vat.ebr. 38",
        "city": "Vatican City",
        "country": "Vatican",
        "script": "Italian semi-cursive",
        "material": "Parchment",
        "folios": 189,
        "condition": "Fair",
        "transcription_status": "Complete",
        "text_tradition": "Italian",
        "passage_variant": "v1",
        "description": (
            "An early Italian manuscript of Rashi's commentary, showing characteristics of "
            "the Italian scribal tradition. Provides important evidence for the southern "
            "European transmission of Rashi's text, distinct from the Ashkenazi tradition. "
            "The manuscript was part of the papal collection since at least the 15th century. "
            "Some water damage affects the lower margins of several folios."
        ),
        "notes": "Some water damage to lower margins. A few lacunae filled by a later hand.",
    },
    {
        "id": "MS-PAR-003",
        "title": 'פירוש רש"י על התורה',
        "title_en": "Rashi's Commentary on the Torah",
        "short_name": "Paris 155",
        "date_display": "Early 13th century",
        "date_approx": 1220,
        "repository": "Bibliothèque nationale de France",
        "shelfmark": "Hébreu 155",
        "city": "Paris",
        "country": "France",
        "script": "French semi-cursive",
        "material": "Parchment",
        "folios": 211,
        "condition": "Good",
        "transcription_status": "Complete",
        "text_tradition": "French",
        "passage_variant": "v2",
        "description": (
            "A French manuscript close in tradition to Rashi's original milieu in Troyes. "
            "The French semi-cursive script and northern French provenance make this manuscript "
            "a key witness for the earliest transmission of the text. Likely copied within a "
            "generation of Rashi's death (1105). Beautifully preserved with chapter headers "
            "in red ink."
        ),
        "notes": "Beautifully preserved. Contains rubrics and chapter headers in red ink.",
    },
    {
        "id": "MS-OXF-004",
        "title": 'פירוש רש"י על התורה',
        "title_en": "Rashi's Commentary on the Torah",
        "short_name": "Bodleian Opp. 34",
        "date_display": "Mid-13th century",
        "date_approx": 1260,
        "repository": "Bodleian Library",
        "shelfmark": "MS Opp. 34",
        "city": "Oxford",
        "country": "United Kingdom",
        "script": "Ashkenazi semi-cursive",
        "material": "Parchment",
        "folios": 220,
        "condition": "Good",
        "transcription_status": "Complete",
        "text_tradition": "Ashkenazi",
        "passage_variant": "v3",
        "description": (
            "Part of the Oppenheimer Collection at Oxford, one of the largest collections of "
            "Hebrew manuscripts in the world. This manuscript shows Ashkenazi characteristics "
            "and was likely produced in the Rhine valley. Contains numerous interlinear glosses "
            "and marginal comments by later scholars. Acquired by the Bodleian Library in 1829 "
            "as part of the Oppenheimer bequest."
        ),
        "notes": "Acquired by the Bodleian Library in 1829 as part of the Oppenheimer bequest.",
    },
    {
        "id": "MS-NLI-005",
        "title": 'פירוש רש"י על התורה',
        "title_en": "Rashi's Commentary on the Torah",
        "short_name": "NLI Heb. 4° 3614",
        "date_display": "Late 13th century",
        "date_approx": 1285,
        "repository": "National Library of Israel",
        "shelfmark": "Heb. 4° 3614",
        "city": "Jerusalem",
        "country": "Israel",
        "script": "Sephardic semi-cursive",
        "material": "Parchment",
        "folios": 198,
        "condition": "Very Good",
        "transcription_status": "Partial",
        "text_tradition": "Sephardic",
        "passage_variant": "v1",
        "description": (
            "A Sephardic manuscript from the NLI collection, representing the Iberian "
            "transmission of Rashi's text. The Sephardic scribal tradition is distinct from "
            "the Ashkenazi, and this manuscript shows several unique readings. It is currently "
            "being transcribed as part of the MiDRASH project. Genesis and Exodus have been "
            "completed; work on the remaining books is ongoing."
        ),
        "notes": "Transcription in progress. Genesis and Exodus completed.",
    },
    {
        "id": "MS-HAM-006",
        "title": 'פירוש רש"י על התורה',
        "title_en": "Rashi's Commentary on the Torah",
        "short_name": "Hamburg 45",
        "date_display": "Early 14th century",
        "date_approx": 1320,
        "repository": "Staats- und Universitätsbibliothek Hamburg",
        "shelfmark": "Cod. hebr. 45",
        "city": "Hamburg",
        "country": "Germany",
        "script": "Ashkenazi square with semi-cursive additions",
        "material": "Paper",
        "folios": 167,
        "condition": "Good",
        "transcription_status": "Partial",
        "text_tradition": "Ashkenazi",
        "passage_variant": "v2",
        "description": (
            "A later Ashkenazi manuscript written on paper, indicating the transitional period "
            "in manuscript production during the 14th century. The text shows influence from "
            "both earlier Ashkenazi and continental traditions. Contains extensive marginalia "
            "from multiple hands. Genesis and Leviticus have been transcribed."
        ),
        "notes": "Transcription of Genesis and Leviticus completed.",
    },
    {
        "id": "MS-CAM-007",
        "title": 'פירוש רש"י על התורה',
        "title_en": "Rashi's Commentary on the Torah",
        "short_name": "Cambridge Add. 377",
        "date_display": "Late 13th century",
        "date_approx": 1290,
        "repository": "Cambridge University Library",
        "shelfmark": "Add. MS 377",
        "city": "Cambridge",
        "country": "United Kingdom",
        "script": "English semi-cursive",
        "material": "Parchment",
        "folios": 203,
        "condition": "Fair",
        "transcription_status": "Pending",
        "text_tradition": "Ashkenazi",
        "passage_variant": "v3",
        "description": (
            "An English manuscript of Rashi's commentary, one of the few surviving Hebrew "
            "manuscripts of English provenance predating the expulsion of Jews from England "
            "in 1290. The manuscript's English scribal characteristics make it a unique witness "
            "to the Anglo-Jewish textual tradition. Currently awaiting transcription by the "
            "MiDRASH project team."
        ),
        "notes": "Awaiting transcription. Some damage from past damp storage conditions.",
    },
    {
        "id": "MS-FLR-008",
        "title": 'פירוש רש"י על התורה',
        "title_en": "Rashi's Commentary on the Torah",
        "short_name": "Laurenziana Plut. 1",
        "date_display": "Early 14th century",
        "date_approx": 1310,
        "repository": "Biblioteca Medicea Laurenziana",
        "shelfmark": "Plut. I.1",
        "city": "Florence",
        "country": "Italy",
        "script": "Italian square",
        "material": "Parchment",
        "folios": 245,
        "condition": "Excellent",
        "transcription_status": "Complete",
        "text_tradition": "Italian",
        "passage_variant": "base",
        "description": (
            "A beautifully illuminated Italian manuscript from the Medici collection, "
            "featuring decorated initials and marginal illustrations. The text belongs to "
            "the Italian tradition and is notable for its exceptional artistic quality. "
            "Considered one of the most aesthetically significant manuscripts of Rashi's "
            "commentary in existence. Transcription is complete."
        ),
        "notes": "Exceptional preservation. Contains illuminated decorations throughout.",
    },
]

# Index by ID for fast lookup
MS_BY_ID = {m["id"]: m for m in MANUSCRIPTS}

# ─────────────────────────────────────────────────────────────────────────────
# HELPER FUNCTIONS
# ─────────────────────────────────────────────────────────────────────────────

def get_transcript(ms: dict, passage_key: str) -> str:
    """Return the transcription text for a manuscript and passage."""
    variant = ms.get("passage_variant", "base")
    texts = RASHI_TEXTS.get(passage_key, {})
    return texts.get(variant, texts.get("base", "— transcription not yet available —"))


def badge_html(status: str) -> str:
    cls_map = {
        "Complete": "badge-complete",
        "Partial":  "badge-partial",
        "Pending":  "badge-pending",
    }
    cls = cls_map.get(status, "badge-pending")
    return f'<span class="badge {cls}">{status}</span>'


def tradition_badge(tradition: str) -> str:
    cls_map = {
        "Ashkenazi": "badge-ashkenazi",
        "Sephardic":  "badge-sephardic",
        "Italian":    "badge-italian",
        "French":     "badge-french",
    }
    key = tradition.split()[0]  # handle "Ashkenazi (English)"
    cls = cls_map.get(key, "badge-ashkenazi")
    return f'<span class="badge {cls}">{tradition}</span>'


def word_diff_html(text_a: str, text_b: str) -> tuple[str, str]:
    """
    Return (html_a, html_b) where differing words are highlighted.
    Uses SequenceMatcher on word tokens.
    """
    words_a = text_a.split()
    words_b = text_b.split()
    matcher = SequenceMatcher(None, words_a, words_b, autojunk=False)
    out_a, out_b = [], []
    for tag, i1, i2, j1, j2 in matcher.get_opcodes():
        if tag == "equal":
            out_a.extend(words_a[i1:i2])
            out_b.extend(words_b[j1:j2])
        elif tag == "replace":
            for w in words_a[i1:i2]:
                out_a.append(f'<span class="diff-changed">{w}</span>')
            for w in words_b[j1:j2]:
                out_b.append(f'<span class="diff-changed">{w}</span>')
        elif tag == "delete":
            for w in words_a[i1:i2]:
                out_a.append(f'<span class="diff-removed">{w}</span>')
        elif tag == "insert":
            for w in words_b[j1:j2]:
                out_b.append(f'<span class="diff-added">{w}</span>')
    return " ".join(out_a), " ".join(out_b)


def count_diff_words(text_a: str, text_b: str) -> int:
    """Count number of differing word positions between two texts."""
    words_a = text_a.split()
    words_b = text_b.split()
    matcher = SequenceMatcher(None, words_a, words_b, autojunk=False)
    return sum(max(i2 - i1, j2 - j1) for tag, i1, i2, j1, j2 in matcher.get_opcodes() if tag != "equal")


# ─────────────────────────────────────────────────────────────────────────────
# PAGE — HOME
# ─────────────────────────────────────────────────────────────────────────────

def page_home():
    st.markdown("""
    <div class="hero-banner">
      <span class="hebrew-title">פירוש רש"י על התורה — עדי כתב יד</span>
      <h1>MiDRASH — Rashi Manuscript Collection</h1>
      <p class="subtitle">
        A digital scholarly edition of Rashi's Torah commentary across manuscript witnesses —
        transcriptions, comparisons, and variant analysis.
      </p>
    </div>
    """, unsafe_allow_html=True)

    # ── Stats ──────────────────────────────────────────────────────────────
    total_ms   = len(MANUSCRIPTS)
    complete   = sum(1 for m in MANUSCRIPTS if m["transcription_status"] == "Complete")
    partial    = sum(1 for m in MANUSCRIPTS if m["transcription_status"] == "Partial")
    passages   = len(PASSAGES)
    traditions = len({m["text_tradition"].split()[0] for m in MANUSCRIPTS})

    st.markdown(f"""
    <div class="stat-grid">
      <div class="stat-box">
        <span class="stat-number">{total_ms}</span>
        <span class="stat-label">Manuscripts</span>
      </div>
      <div class="stat-box">
        <span class="stat-number">{complete}</span>
        <span class="stat-label">Fully Transcribed</span>
      </div>
      <div class="stat-box">
        <span class="stat-number">{partial}</span>
        <span class="stat-label">In Progress</span>
      </div>
      <div class="stat-box">
        <span class="stat-number">{passages}</span>
        <span class="stat-label">Comparable Passages</span>
      </div>
      <div class="stat-box">
        <span class="stat-number">{traditions}</span>
        <span class="stat-label">Text Traditions</span>
      </div>
    </div>
    """, unsafe_allow_html=True)

    # ── About ──────────────────────────────────────────────────────────────
    col_left, col_right = st.columns([3, 2])

    with col_left:
        st.markdown('<div class="section-head">About this Collection</div>', unsafe_allow_html=True)
        st.markdown("""
        **Rashi** (Rabbi Shlomo Yitzhaki, 1040–1105) was one of the most influential Jewish
        scholars of the medieval period. His commentary on the Torah, written in Troyes (northern
        France), became the standard reference for the study of the Hebrew Bible in Jewish
        tradition. The commentary survives in hundreds of manuscripts, each reflecting the
        scribal conventions and textual traditions of its region and period.

        The **MiDRASH Project** is producing critical transcriptions of key manuscript witnesses,
        enabling systematic comparison across the Ashkenazi, Sephardic, French, and Italian
        text traditions. This website presents the project's transcriptions alongside tools for
        scholarly analysis.

        **Key features:**
        - Browse all manuscript witnesses with full metadata
        - Read transcriptions passage by passage
        - Compare any two manuscripts side by side with highlighted variants
        - Download transcriptions for offline study
        """)

    with col_right:
        st.markdown('<div class="section-head">Featured Manuscripts</div>', unsafe_allow_html=True)
        featured = ["MS-PAR-003", "MS-VTK-002", "MS-FLR-008"]
        for ms_id in featured:
            ms = MS_BY_ID[ms_id]
            st.markdown(f"""
            <div class="ms-card">
              <span class="hebrew-ms">{ms['title']}</span>
              <h4>{ms['short_name']}</h4>
              <div class="meta">📍 {ms['repository']}, {ms['city']}</div>
              <div class="meta">📅 {ms['date_display']} &nbsp;·&nbsp; {ms['material']}, {ms['folios']} ff.</div>
              <div style="margin-top:0.5rem">
                {badge_html(ms['transcription_status'])}
                {tradition_badge(ms['text_tradition'])}
              </div>
            </div>
            """, unsafe_allow_html=True)

    # ── Quick sample ───────────────────────────────────────────────────────
    st.markdown('<div class="section-head">Sample Passage — Genesis 1:1</div>', unsafe_allow_html=True)
    st.markdown("""
    The opening words of Rashi's commentary on the Torah are perhaps the most famous in all
    of rabbinic literature. They demonstrate the range of scribal variation preserved across
    the manuscript tradition:
    """)
    sample_ms = MS_BY_ID["MS-PAR-003"]
    text = get_transcript(sample_ms, "gen_1_1")
    st.markdown(f"""
    <div class="passage-label">Genesis 1:1 · {sample_ms['short_name']} ({sample_ms['date_display']})</div>
    <div class="heb-block">{text}</div>
    """, unsafe_allow_html=True)
    st.caption(
        "Navigate to **Compare Manuscripts** to see how this passage differs across witnesses."
    )

    # ── Collection timeline ────────────────────────────────────────────────
    st.markdown('<div class="section-head">Manuscript Timeline</div>', unsafe_allow_html=True)
    sorted_ms = sorted(MANUSCRIPTS, key=lambda m: m["date_approx"])
    timeline_html = '<div class="timeline">'
    for ms in sorted_ms:
        timeline_html += f"""
        <div class="timeline-item">
          <span class="timeline-date">{ms['date_display']}</span><br>
          <span class="timeline-title">{ms['short_name']}</span>
          — {ms['repository']}, {ms['city']}
          &nbsp;{tradition_badge(ms['text_tradition'])}
        </div>"""
    timeline_html += "</div>"
    st.markdown(timeline_html, unsafe_allow_html=True)


# ─────────────────────────────────────────────────────────────────────────────
# PAGE — BROWSE MANUSCRIPTS
# ─────────────────────────────────────────────────────────────────────────────

def page_browse():
    st.markdown("## Browse Manuscripts")
    st.markdown(
        "Filter the manuscript collection and click **View** to open full details and transcription."
    )

    # ── Filters ────────────────────────────────────────────────────────────
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        status_filter = st.multiselect(
            "Transcription status",
            ["Complete", "Partial", "Pending"],
            default=["Complete", "Partial", "Pending"],
        )
    with col2:
        all_traditions = sorted({m["text_tradition"].split()[0] for m in MANUSCRIPTS})
        tradition_filter = st.multiselect(
            "Text tradition",
            all_traditions,
            default=all_traditions,
        )
    with col3:
        all_countries = sorted({m["country"] for m in MANUSCRIPTS})
        country_filter = st.multiselect(
            "Country",
            all_countries,
            default=all_countries,
        )
    with col4:
        search_q = st.text_input("Search", placeholder="shelfmark, city, notes…")

    # ── Apply filters ──────────────────────────────────────────────────────
    results = [
        m for m in MANUSCRIPTS
        if m["transcription_status"] in status_filter
        and m["text_tradition"].split()[0] in tradition_filter
        and m["country"] in country_filter
        and (
            not search_q
            or search_q.lower() in m["short_name"].lower()
            or search_q.lower() in m["shelfmark"].lower()
            or search_q.lower() in m["city"].lower()
            or search_q.lower() in m["notes"].lower()
            or search_q.lower() in m["repository"].lower()
        )
    ]

    st.markdown(f"**{len(results)}** manuscript(s) found")
    st.divider()

    if not results:
        st.info("No manuscripts match the current filters.")
        return

    # ── Results ────────────────────────────────────────────────────────────
    for ms in results:
        col_info, col_btn = st.columns([5, 1])
        with col_info:
            st.markdown(f"""
            <div class="ms-card">
              <span class="hebrew-ms">{ms['title']}</span>
              <h4>{ms['short_name']}</h4>
              <div class="meta">📍 {ms['repository']} · {ms['shelfmark']} · {ms['city']}, {ms['country']}</div>
              <div class="meta">📅 {ms['date_display']} &nbsp;·&nbsp; ✍️ {ms['script']} &nbsp;·&nbsp; 📖 {ms['material']}, {ms['folios']} ff.</div>
              <div style="margin-top:0.5rem">
                {badge_html(ms['transcription_status'])}
                {tradition_badge(ms['text_tradition'])}
              </div>
            </div>
            """, unsafe_allow_html=True)
        with col_btn:
            st.write("")
            st.write("")
            st.write("")
            if st.button("View →", key=f"view_{ms['id']}"):
                st.session_state["viewer_ms_id"] = ms["id"]
                st.session_state["page"] = "📄 Manuscript Viewer"
                st.rerun()


# ─────────────────────────────────────────────────────────────────────────────
# PAGE — MANUSCRIPT VIEWER
# ─────────────────────────────────────────────────────────────────────────────

def page_viewer():
    st.markdown("## Manuscript Viewer")

    # Manuscript selector
    ms_options = {m["short_name"]: m["id"] for m in MANUSCRIPTS}
    default_name = next(
        (m["short_name"] for m in MANUSCRIPTS if m["id"] == st.session_state.get("viewer_ms_id")),
        MANUSCRIPTS[0]["short_name"],
    )
    selected_name = st.selectbox(
        "Select manuscript",
        list(ms_options.keys()),
        index=list(ms_options.keys()).index(default_name),
    )
    ms = MS_BY_ID[ms_options[selected_name]]

    st.divider()

    col_meta, col_trans = st.columns([2, 3])

    # ── Metadata panel ──────────────────────────────────────────────────────
    with col_meta:
        st.markdown(f"""
        <h3 style="font-family:'EB Garamond',serif; color:#1a1005;">{ms['short_name']}</h3>
        <span class="hebrew-ms" style="font-family:'SBL Hebrew','David',serif; font-size:1.2rem;
              direction:rtl; display:block; color:#444; margin-bottom:0.5rem;">{ms['title']}</span>
        <div style="margin-bottom:0.8rem">
            {badge_html(ms['transcription_status'])}
            {tradition_badge(ms['text_tradition'])}
        </div>
        """, unsafe_allow_html=True)

        st.markdown(f"""
        <table class="meta-table">
          <tr><td>Repository</td><td>{ms['repository']}</td></tr>
          <tr><td>Shelfmark</td><td>{ms['shelfmark']}</td></tr>
          <tr><td>City</td><td>{ms['city']}, {ms['country']}</td></tr>
          <tr><td>Date</td><td>{ms['date_display']}</td></tr>
          <tr><td>Script</td><td>{ms['script']}</td></tr>
          <tr><td>Material</td><td>{ms['material']}</td></tr>
          <tr><td>Folios</td><td>{ms['folios']}</td></tr>
          <tr><td>Condition</td><td>{ms['condition']}</td></tr>
          <tr><td>Tradition</td><td>{ms['text_tradition']}</td></tr>
        </table>
        """, unsafe_allow_html=True)

        st.markdown("#### Description")
        st.markdown(ms["description"])

        if ms["notes"]:
            st.markdown("#### Notes")
            st.info(ms["notes"])

        # Compare shortcut
        st.markdown("---")
        if st.button("Compare this manuscript →", use_container_width=True):
            st.session_state["compare_ms_a"] = ms["id"]
            st.session_state["page"] = "⚖️ Compare Manuscripts"
            st.rerun()

    # ── Transcription panel ─────────────────────────────────────────────────
    with col_trans:
        if ms["transcription_status"] == "Pending":
            st.warning(
                "Transcription has not yet begun for this manuscript. "
                "Check back later for updates."
            )
            return

        st.markdown("#### Transcriptions by Passage")
        passage_key = st.selectbox(
            "Select passage",
            list(PASSAGES.keys()),
            format_func=lambda k: PASSAGES[k],
            key="viewer_passage",
        )

        text = get_transcript(ms, passage_key)

        # Check if passage is available for this partially-transcribed manuscript
        # (For demo: Partial manuscripts have Genesis/Exodus only)
        is_partial_and_missing = (
            ms["transcription_status"] == "Partial"
            and passage_key.startswith(("lev", "deut"))
        )

        if is_partial_and_missing:
            st.warning(
                f"Transcription for {PASSAGES[passage_key]} is not yet available "
                f"for {ms['short_name']}. Work is ongoing."
            )
        else:
            st.markdown(
                f'<div class="passage-label">{PASSAGES[passage_key]}</div>',
                unsafe_allow_html=True,
            )
            st.markdown(f'<div class="heb-block">{text}</div>', unsafe_allow_html=True)

            # Download
            dl_text = f"Manuscript: {ms['short_name']}\n"
            dl_text += f"Repository: {ms['repository']} — {ms['shelfmark']}\n"
            dl_text += f"Passage: {PASSAGES[passage_key]}\n"
            dl_text += f"Tradition: {ms['text_tradition']}\n\n"
            dl_text += text + "\n"

            st.download_button(
                "Download transcription (.txt)",
                data=dl_text,
                file_name=f"rashi_{ms['id']}_{passage_key}.txt",
                mime="text/plain",
            )

        # ── All passages summary ───────────────────────────────────────────
        st.markdown("---")
        st.markdown("#### All Available Passages")
        for pk, plabel in PASSAGES.items():
            is_missing = (
                ms["transcription_status"] == "Partial"
                and pk.startswith(("lev", "deut"))
            )
            icon = "✅" if not is_missing and ms["transcription_status"] != "Pending" else "⏳"
            st.markdown(f"{icon} {plabel}")


# ─────────────────────────────────────────────────────────────────────────────
# PAGE — COMPARE MANUSCRIPTS
# ─────────────────────────────────────────────────────────────────────────────

def page_compare():
    st.markdown("## Compare Manuscripts")
    st.markdown(
        "Select two manuscript witnesses and a passage to view a side-by-side comparison "
        "with word-level variant highlighting."
    )

    available = [m for m in MANUSCRIPTS if m["transcription_status"] != "Pending"]
    ms_labels = {m["short_name"]: m["id"] for m in available}
    ms_names  = list(ms_labels.keys())

    col_a, col_b, col_p = st.columns([2, 2, 3])

    # Pre-fill from session if navigated from viewer
    default_a = st.session_state.get("compare_ms_a", available[0]["id"])
    default_a_name = next((m["short_name"] for m in available if m["id"] == default_a), ms_names[0])
    default_b_name = ms_names[1] if ms_names[1] != default_a_name else ms_names[0]

    with col_a:
        sel_a = st.selectbox(
            "Manuscript A",
            ms_names,
            index=ms_names.index(default_a_name),
        )
    with col_b:
        sel_b = st.selectbox(
            "Manuscript B",
            ms_names,
            index=ms_names.index(default_b_name) if default_b_name in ms_names else 1,
        )
    with col_p:
        passage_key = st.selectbox(
            "Passage",
            list(PASSAGES.keys()),
            format_func=lambda k: PASSAGES[k],
            key="compare_passage",
        )

    ms_a = MS_BY_ID[ms_labels[sel_a]]
    ms_b = MS_BY_ID[ms_labels[sel_b]]

    if sel_a == sel_b:
        st.warning("Please select two different manuscripts to compare.")
        return

    text_a = get_transcript(ms_a, passage_key)
    text_b = get_transcript(ms_b, passage_key)

    html_a, html_b = word_diff_html(text_a, text_b)
    n_diffs = count_diff_words(text_a, text_b)

    st.divider()

    # ── Diff legend ─────────────────────────────────────────────────────────
    st.markdown(
        '<span class="badge diff-changed" style="background:#ffe082;color:#333">Variant word</span>'
        '&nbsp;&nbsp;'
        '<span class="badge diff-added" style="background:#c8e6c9;color:#155724">Word present in B only</span>'
        '&nbsp;&nbsp;'
        '<span class="badge diff-removed" style="background:#ffcdd2;color:#721c24">Word present in A only</span>',
        unsafe_allow_html=True,
    )
    st.markdown(f"**{n_diffs} differing word position(s)** detected in this passage.")
    st.divider()

    col_left, col_right = st.columns(2)

    with col_left:
        st.markdown(f"""
        <div class="compare-panel">
          <div class="compare-header">
            {ms_a['short_name']}
            &nbsp;{tradition_badge(ms_a['text_tradition'])}
          </div>
          <div style="font-size:0.82rem; color:#6b5a48; margin-bottom:0.7rem">
            {ms_a['repository']}<br>
            {ms_a['shelfmark']} · {ms_a['date_display']}
          </div>
          <div class="passage-label">{PASSAGES[passage_key]}</div>
          <div class="heb-block">{html_a}</div>
        </div>
        """, unsafe_allow_html=True)

    with col_right:
        st.markdown(f"""
        <div class="compare-panel">
          <div class="compare-header">
            {ms_b['short_name']}
            &nbsp;{tradition_badge(ms_b['text_tradition'])}
          </div>
          <div style="font-size:0.82rem; color:#6b5a48; margin-bottom:0.7rem">
            {ms_b['repository']}<br>
            {ms_b['shelfmark']} · {ms_b['date_display']}
          </div>
          <div class="passage-label">{PASSAGES[passage_key]}</div>
          <div class="heb-block">{html_b}</div>
        </div>
        """, unsafe_allow_html=True)

    # ── Variant summary table ────────────────────────────────────────────────
    if n_diffs > 0:
        st.divider()
        st.markdown("#### Variant Summary")

        words_a = text_a.split()
        words_b = text_b.split()
        matcher = SequenceMatcher(None, words_a, words_b, autojunk=False)
        rows = []
        for tag, i1, i2, j1, j2 in matcher.get_opcodes():
            if tag == "equal":
                continue
            rows.append({
                "Type":  tag.capitalize(),
                f"{ms_a['short_name']} (A)": " ".join(words_a[i1:i2]) or "—",
                f"{ms_b['short_name']} (B)": " ".join(words_b[j1:j2]) or "—",
            })

        if rows:
            df = pd.DataFrame(rows)
            st.dataframe(df, use_container_width=True, hide_index=True)

        # Download comparison
        dl_lines = [
            f"Comparison: {ms_a['short_name']} vs {ms_b['short_name']}",
            f"Passage: {PASSAGES[passage_key]}",
            f"Differences: {n_diffs}",
            "",
            f"--- {ms_a['short_name']} ---",
            text_a,
            "",
            f"--- {ms_b['short_name']} ---",
            text_b,
        ]
        st.download_button(
            "Download comparison (.txt)",
            data="\n".join(dl_lines),
            file_name=f"compare_{ms_a['id']}_{ms_b['id']}_{passage_key}.txt",
            mime="text/plain",
        )

    # ── All passages overview ────────────────────────────────────────────────
    st.divider()
    st.markdown("#### Variant Count Across All Passages")
    passage_diffs = []
    for pk, plabel in PASSAGES.items():
        ta = get_transcript(ms_a, pk)
        tb = get_transcript(ms_b, pk)
        nd = count_diff_words(ta, tb)
        passage_diffs.append({"Passage": plabel, "Differing words": nd})

    df_all = pd.DataFrame(passage_diffs)
    st.bar_chart(df_all.set_index("Passage")["Differing words"])


# ─────────────────────────────────────────────────────────────────────────────
# PAGE — TEXT SEARCH
# ─────────────────────────────────────────────────────────────────────────────

def page_search():
    st.markdown("## Full-Text Search")
    st.markdown(
        "Search across all transcribed passages. Results are shown in context with the "
        "matching portion highlighted."
    )

    query = st.text_input(
        "Search transcriptions (Hebrew or transliteration)",
        placeholder="e.g. אמר רבי יצחק",
    )
    if not query:
        st.info("Enter a search term above to begin.")
        return

    hits = []
    for ms in MANUSCRIPTS:
        if ms["transcription_status"] == "Pending":
            continue
        for pk, plabel in PASSAGES.items():
            text = get_transcript(ms, pk)
            if query in text:
                # Find snippet around the match
                idx = text.find(query)
                start = max(0, idx - 30)
                end   = min(len(text), idx + len(query) + 30)
                snippet = text[start:end].replace(
                    query, f'<span class="search-hit">{query}</span>'
                )
                if start > 0:
                    snippet = "…" + snippet
                if end < len(text):
                    snippet = snippet + "…"
                hits.append({
                    "ms":      ms,
                    "passage": plabel,
                    "snippet": snippet,
                })

    if not hits:
        st.warning(f'No transcriptions contain "{query}".')
        return

    st.success(f"Found **{len(hits)}** result(s) for **{query}**")

    for h in hits:
        ms = h["ms"]
        st.markdown(f"""
        <div class="ms-card">
          <h4>{ms['short_name']} — {h['passage']}</h4>
          <div class="meta">
            {ms['repository']} · {ms['shelfmark']} · {ms['date_display']}
            &nbsp;{tradition_badge(ms['text_tradition'])}
          </div>
          <div class="heb-block" style="font-size:1.1rem; padding:0.7rem 1rem;">{h['snippet']}</div>
        </div>
        """, unsafe_allow_html=True)
        if st.button("Open manuscript →", key=f"search_open_{ms['id']}_{h['passage']}"):
            st.session_state["viewer_ms_id"] = ms["id"]
            st.session_state["page"] = "📄 Manuscript Viewer"
            st.rerun()


# ─────────────────────────────────────────────────────────────────────────────
# PAGE — ABOUT
# ─────────────────────────────────────────────────────────────────────────────

def page_about():
    st.markdown("## About the MiDRASH Project")

    col1, col2 = st.columns([3, 2])

    with col1:
        st.markdown("""
        <div class="about-box">
        <h3>Project Overview</h3>

        The <strong>MiDRASH Project</strong> (Manuscript Indexing, Documentation, Research,
        and Analysis of Scholarly Hebrew texts) is a research initiative dedicated to the
        systematic study of Hebrew manuscript traditions. The project is hosted at the
        <strong>National Library of Israel</strong>.

        <br><br>

        This website focuses specifically on the manuscript transmission of
        <strong>Rashi's Commentary on the Torah</strong> (פירוש רש"י על התורה).
        Rashi (Rabbi Shlomo Yitzhaki, 1040–1105) composed his commentary in Troyes, France,
        and it rapidly became the standard reference work for the study of the Hebrew Bible in
        Jewish communities across Europe and beyond.

        <br><br>

        Despite its canonical status, Rashi's commentary exists in hundreds of manuscript
        copies that differ from one another — and from the printed editions — in thousands
        of small but significant details. The MiDRASH project aims to document these
        differences systematically by producing critical transcriptions of key manuscript
        witnesses.
        </div>
        """, unsafe_allow_html=True)

        st.markdown("""
        <div class="about-box" style="margin-top:1rem">
        <h3>Methodology</h3>

        Each manuscript is transcribed diplomatically — that is, the text is reproduced
        as written, preserving spelling variants, abbreviations, and scribal corrections.
        Transcriptions are then aligned to a reference text to facilitate comparison.

        <br><br>

        The word-level diff tool on this site uses a sequence-matching algorithm
        (based on the Ratcliff/Obershelp method) to identify substitutions, insertions,
        and deletions between any two manuscripts at any given passage.

        <br><br>

        <strong>Manuscript selection criteria:</strong>
        <ul>
          <li>Date of copying (preference for pre-1350 witnesses)</li>
          <li>Geographic origin (representatives of all main traditions)</li>
          <li>Physical condition and legibility</li>
          <li>Known importance in prior scholarship</li>
        </ul>
        </div>
        """, unsafe_allow_html=True)

    with col2:
        st.markdown("""
        <div class="about-box">
        <h3>Rashi — A Brief Biography</h3>
        <span class="hebrew-ms" style="font-family:'SBL Hebrew','David',serif; font-size:1.1rem;
              direction:rtl; display:block; color:#2c1810; margin-bottom:0.5rem;">
          רבי שלמה יצחקי (רש"י)<br>תת"ם – תתס"ה
        </span>

        Born in Troyes, Champagne (France) in 1040, Rashi studied in the great academies
        of the Rhine valley (Worms and Mainz) before returning to Troyes, where he founded
        his own academy and composed his monumental commentaries.

        <br><br>

        His Torah commentary, completed around 1080–1105, integrates close reading of
        the Hebrew text with selections from midrashic literature, presented in remarkably
        clear and concise prose. It was the first Hebrew book to be printed (Reggio di
        Calabria, 1475) and has been reprinted continuously ever since.

        <br><br>

        Rashi died in 1105, leaving behind two daughters whose husbands and sons
        (the <em>Tosafists</em>) continued and debated his interpretive legacy.
        </div>
        """, unsafe_allow_html=True)

        st.markdown("""
        <div class="about-box" style="margin-top:1rem">
        <h3>Text Traditions in this Collection</h3>

        <strong>Ashkenazi</strong> — manuscripts produced in the Rhine valley and surrounding
        German-speaking lands, closest to Rashi's own region. <br><br>

        <strong>French</strong> — manuscripts from northern France, often preserving
        early readings close to Rashi's original. <br><br>

        <strong>Italian</strong> — manuscripts from Italian Jewish communities, showing
        a distinctive scribal tradition with some unique readings. <br><br>

        <strong>Sephardic</strong> — manuscripts from the Iberian peninsula, representing
        the southernmost branch of the manuscript tradition.
        </div>
        """, unsafe_allow_html=True)

        st.markdown("""
        <div class="about-box" style="margin-top:1rem">
        <h3>Citation</h3>

        When citing transcriptions from this site, please use:

        <em>MiDRASH Project, Rashi Manuscripts Collection, National Library of Israel
        (accessed [date]).</em>
        </div>
        """, unsafe_allow_html=True)


# ─────────────────────────────────────────────────────────────────────────────
# MAIN — SIDEBAR + ROUTING
# ─────────────────────────────────────────────────────────────────────────────

def main():
    st.markdown(f"<style>{STYLES}</style>", unsafe_allow_html=True)

    # ── Sidebar ─────────────────────────────────────────────────────────────
    with st.sidebar:
        st.markdown("""
        <div class="sidebar-logo">
          <span class="logo-heb">מִדְרָשׁ</span>
          <span class="logo-en">MiDRASH</span>
          <span class="logo-sub">Rashi Manuscripts</span>
        </div>
        """, unsafe_allow_html=True)

        PAGES = {
            "🏠 Home":                 page_home,
            "📚 Browse Manuscripts":   page_browse,
            "📄 Manuscript Viewer":    page_viewer,
            "⚖️ Compare Manuscripts":  page_compare,
            "🔍 Search Transcriptions":page_search,
            "ℹ️ About MiDRASH":        page_about,
        }

        # Honour session-state navigation (e.g. from "View →" buttons)
        if "page" in st.session_state and st.session_state["page"] in PAGES:
            default_page = list(PAGES.keys()).index(st.session_state["page"])
        else:
            default_page = 0

        selected = st.radio(
            "Navigation",
            list(PAGES.keys()),
            index=default_page,
            label_visibility="collapsed",
        )

        # Clear the stored page so the radio takes over from next rerun
        if "page" in st.session_state:
            del st.session_state["page"]

        # ── Sidebar stats ──────────────────────────────────────────────────
        st.markdown("---")
        complete = sum(1 for m in MANUSCRIPTS if m["transcription_status"] == "Complete")
        st.markdown(
            f"<div style='font-size:0.78rem; color:#7a8a9a; text-align:center'>"
            f"<b style='color:#c9a84c'>{complete}</b> of <b style='color:#c9a84c'>{len(MANUSCRIPTS)}</b>"
            f" manuscripts fully transcribed<br>"
            f"<b style='color:#c9a84c'>{len(PASSAGES)}</b> comparable passages</div>",
            unsafe_allow_html=True,
        )
        st.markdown("---")
        st.markdown(
            "<div style='font-size:0.72rem; color:#5a6a7a; text-align:center'>"
            "National Library of Israel<br>MiDRASH Project<br><br>"
            "Data for demo purposes.<br>Contact project for full access."
            "</div>",
            unsafe_allow_html=True,
        )

    # ── Route ────────────────────────────────────────────────────────────────
    PAGES[selected]()


if __name__ == "__main__":
    main()
