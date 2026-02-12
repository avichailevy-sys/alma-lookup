# ALMA Hierarchy Lookup (Ktiv / Midrash Project)

This application allows users to explore parent–child relationships between ALMA records.

The tool was created for the Midrash project to analyze manuscript hierarchies in the Ktiv catalog.

## What the app does

Given an ALMA ID, the app shows:

1. If the record appears as a **child** – its parent ALMA record(s)
2. If the record appears as a **parent** – its child ALMA record(s)

A record may be both a child and a parent.

## Data

The relationships are based on:

`CHILD PARENT ALMA.xlsx`

Parent fields may contain multiple ALMA IDs separated by `|||`.

## How to run locally

Install requirements:
pip install streamlit pandas openpyxl

Run:
streamlit run alma_lookup_app.py


The app will open in your browser.

## Web version

The application is deployed via Streamlit Cloud.

## Author

Avichai Levy  
Midrash Project

