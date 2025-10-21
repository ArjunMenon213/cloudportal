
import streamlit as st
import pandas as pd
import glob
import os
from pathlib import Path
from io import BytesIO
from datetime import datetime

st.set_page_config(page_title="Tool Drawer Tracker", layout="wide")

# --- Helpers -----------------------------------------------------------------
@st.cache_data
def read_excel_bytesio(bio, filename=""):
    """
    Read a BytesIO uploaded file (or local path) and try to return a dataframe.
    Supports .xlsx, .xls, .csv
    """
    try:
        if filename.lower().endswith(".csv"):
            return pd.read_csv(bio)
        else:
            return pd.read_excel(bio, engine="openpyxl")
    except Exception as e:
        # fallback: try pandas autodetect
        try:
            return pd.read_excel(bio)
        except Exception:
            st.warning(f"Could not read file {filename}: {e}")
            return pd.DataFrame()


def normalize_columns(df: pd.DataFrame) -> pd.DataFrame:
    """
    Map common column name variants to canonical columns:
    'Tool #', 'Status', 'Drawer', 'Name', 'Timestamp'
    """
    if df.empty:
        return df
    col_map = {}
    for c in df.columns:
        lc = c.lower().strip()
        if "tool" in lc and ("#" in lc or "number" in lc or "no" in lc or "id" in lc):
            col_map[c] = "Tool #"
        elif "tool" in lc and "name" not in lc:
            col_map[c] = "Tool #"
        elif "status" in lc:
            col_map[c] = "Status"
        elif "drawer" in lc:
            col_map[c] = "Drawer"
        elif "name" in lc and "person" in lc or lc == "name":
            col_map[c] = "Name"
        elif "timestamp" in lc or "time" in lc or "date" in lc:
            col_map[c] = "Timestamp"
        elif lc in ("user", "person", "taken by", "checked out by"):
            col_map[c] = "Name"
    df = df.rename(columns=col_map)
    # If Tool # still not present, try to infer from first column
    if "Tool #" not in df.columns and len(df.columns) > 0:
        possible = df.columns[0]
        if df[possible].dtype != "O" or df[possible].astype(str).str.isnumeric().any():
            df = df.rename(columns={possible: "Tool #"})
    return df


@st.cache_data
def load_from_folder(folder: str):
    """
    Read all .xlsx/.xls/.csv from folder and return combined dataframe and list of sources.
    """
    files = sorted(glob.glob(os.path.join(folder, "*.*")))
    dfs = []
    sources = []
    for f in files:
        if not f.lower().endswith((".xlsx", ".xls", ".csv")):
            continue
        try:
            df = pd.read_excel(f, engine="openpyxl") if f.lower().endswith((".xlsx", ".xls")) else pd.read_csv(f)
        except Exception:
            try:
                df = pd.read_excel(f)
            except Exception as e:
                st.warning(f"Could not read {f}: {e}")
                continue
        df = normalize_columns(df)
        if df.empty:
            continue
        df["__source_file"] = Path(f).name
        dfs.append(df)
        sources.append(f)
    if dfs:
        combined = pd.concat(dfs, ignore_index=True, sort=False)
    else:
        combined = pd.DataFrame()
    return combined, files


@st.cache_data
def load_from_uploaded(uploaded_files):
    dfs = []
    for up in uploaded_files:
        bio = up
        try:
            df = read_excel_bytesio(bio, up.name)
        except Exception:
            st.warning(f"Could not read {up.name}")
            continue
        df = normalize_columns(df)
        if df.empty:
            continue
        df["__source_file"] = up.name
        dfs.append(df)
    if dfs:
        combined = pd.concat(dfs, ignore_index=True, sort=False)
    else:
        combined = pd.DataFrame()
    return combined


def canonicalize(df: pd.DataFrame) -> pd.DataFrame:
    """
    Ensure canonical columns exist and parse Timestamp column.
    """
    if df.empty:
        return df
    # Ensure canonical names exist even if missing
    for c in ("Tool #", "Status", "Drawer", "Name", "Timestamp"):
        if c not in df.columns:
            df[c] = pd.NA
    # parse Timestamp
    df["Timestamp_parsed"] = pd.to_datetime(df["Timestamp"], errors="coerce")
    # If Timestamp_parsed empty but there is a column that looks like datetime, try to infer
    if df["Timestamp_parsed"].isna().all():
        for col in df.columns:
            if col.lower().startswith("date") or "time" in col.lower():
                df["Timestamp_parsed"] = pd.to_datetime(df[col], errors="coerce")
                if not df["Timestamp_parsed"].isna().all():
                    break
    # Keep consistent column order
    cols = ["Tool #", "Status", "Drawer", "Name", "Timestamp", "Timestamp_parsed", "__source_file"]
    for c in cols:
        if c not in df.columns:
            df[c] = pd.NA
    return df[cols + [c for c in df.columns if c not in cols]]


# --- UI ----------------------------------------------------------------------
st.title("Tool Drawer Tracker")
st.markdown("Upload the Excel files for your drawers, or (when running locally) place them in a `data/` folder. The app will combine and visualize check-outs / removals.")

st.sidebar.header("Data source")
data_source = st.sidebar.radio("How do you want to provide files?", ("Upload files now", "Read from repository / data folder (server)"))

combined_df = pd.DataFrame()
if data_source == "Upload files now":
    uploaded = st.sidebar.file_uploader("Select one or more Excel / CSV files", type=["xlsx", "xls", "csv"], accept_multiple_files=True)
    if uploaded:
        combined_df = load_from_uploaded(uploaded)
    else:
        st.sidebar.info("Upload the Excel files exported from each drawer. You can select multiple files at once.")
else:
    default_folder = "data"
    st.sidebar.write("This will scan the repository's ./data folder for .xlsx/.xls/.csv files.")
    folder = st.sidebar.text_input("Folder to scan", value=default_folder)
    if st.sidebar.button("Scan folder"):
        combined_df, file_list = load_from_folder(folder)
        if combined_df.empty:
            st.sidebar.warning(f"No readable files found in {folder}. Place your drawer files there and re-scan.")
        else:
            st.sidebar.success(f"Read {len(file_list)} files from {folder}.")

# If still empty, show help and exit
if combined_df.empty:
    st.info("No data loaded yet. Upload files via the left sidebar or put Excel files into a `data/` folder and click 'Scan folder'. See the README for more details.")
    st.stop()

# canonicalize and cleanup
df = canonicalize(combined_df)
# Basic cleaning: strip strings
for c in ["Status", "Drawer", "Name"]:
    if c in df.columns:
        df[c] = df[c].astype(str).str.strip().replace({"nan": ""})

# Sidebar filters
st.sidebar.header("Filters")
all_drawers = sorted(df["Drawer"].dropna().unique().astype(str))
selected_drawers = st.sidebar.multiselect("Drawer", options=all_drawers, default=all_drawers if len(all_drawers) <= 7 else all_drawers[:7])
all_status = sorted(df["Status"].dropna().unique().astype(str))
selected_status = st.sidebar.multiselect("Status", options=all_status, default=all_status)
all_names = sorted(df["Name"].dropna().unique().astype(str))
selected_names = st.sidebar.multiselect("Person / Name (optional)", options=all_names, default=all_names)

min_date = df["Timestamp_parsed"].min()
max_date = df["Timestamp_parsed"].max()
if pd.isna(min_date):
    min_date = datetime(2000, 1, 1)
if pd.isna(max_date):
    max_date = datetime.now()
start_date, end_date = st.sidebar.date_input("Date range", value=(min_date.date(), max_date.date()))

# Apply filters
mask = pd.Series(True, index=df.index)
if selected_drawers:
    mask &= df["Drawer"].astype(str).isin(selected_drawers)
if selected_status:
    mask &= df["Status"].astype(str).isin(selected_status)
if selected_names:
    mask &= df["Name"].astype(str).isin(selected_names)
mask &= df["Timestamp_parsed"].dt.date.between(start_date, end_date)
filtered = df[mask].copy()

st.subheader(f"Combined tool events — {len(filtered):,} rows (showing filtered results)")
st.write("You can sort columns by clicking on the table headers. Timestamp_parsed is the parsed datetime column.")

# Show table
st.dataframe(filtered.sort_values(by="Timestamp_parsed", ascending=False), use_container_width=True)

# Quick stats
st.markdown("### Quick summary")
col1, col2, col3 = st.columns(3)
with col1:
    st.metric("Total events (filtered)", f"{len(filtered):,}")
with col2:
    counts = filtered["Status"].value_counts().to_dict()
    st.write("Status counts")
    st.json(counts)
with col3:
    top_people = filtered["Name"].value_counts().head(5)
    st.write("Top people (filtered)")
    st.table(top_people)

# Time series: events per day
st.markdown("### Events over time")
time_group = filtered.dropna(subset=["Timestamp_parsed"]).groupby(pd.Grouper(key="Timestamp_parsed", freq="D")).size()
if not time_group.empty:
    st.line_chart(time_group)
else:
    st.write("No parsable timestamps in the filtered data to plot.")

# Drawer breakdown
st.markdown("### Events by drawer")
drawer_counts = filtered["Drawer"].value_counts()
st.bar_chart(drawer_counts)

# Download combined CSV
st.markdown("### Download")
csv_bytes = filtered.drop(columns=[c for c in filtered.columns if c.startswith("Unnamed:")], errors="ignore").to_csv(index=False).encode("utf-8")
st.download_button("Download filtered CSV", data=csv_bytes, file_name="tool_drawer_filtered.csv", mime="text/csv")

st.markdown("---")
st.markdown("Notes:")
st.markdown(
    "- The app accepts Excel (.xlsx, .xls) and CSV files. Column names are matched heuristically (common variants like 'Timestamp', 'Time', 'Date' will be parsed)."
)
st.markdown("- If your timestamps aren't parsed correctly, check the column naming or formats in the source files.")
st.markdown("- To host publicly: push this repo to GitHub and deploy on Streamlit Community Cloud (see README).")
