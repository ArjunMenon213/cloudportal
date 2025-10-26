import os
import time
import pandas as pd
import streamlit as st
import streamlit.components.v1 as components

st.set_page_config(page_title="Local Excel Live Viewer", layout="wide")

# CONFIG: set these via environment variables or edit here
LOCAL_PATH = os.getenv("LOCAL_PATH", "/path/to/file.xlsx")  # <-- set absolute path
POLL_SECONDS = int(os.getenv("POLL_SECONDS", "300"))  # JS page-reload interval for viewers

st.title("Local Excel Live Viewer")
st.markdown("Displays a local Excel file and reloads automatically when the file is updated.")

# Sanity checks
if not os.path.isabs(LOCAL_PATH):
    st.warning("LOCAL_PATH is not absolute — consider using an absolute path to avoid surprises.")
if not os.path.exists(LOCAL_PATH):
    st.error(f"Local file not found: {LOCAL_PATH}")
    st.stop()

# Use file mtime as cache key: when mtime changes, cached loader will re-run
def file_mtime(path):
    try:
        return os.path.getmtime(path)
    except Exception:
        return None

@st.cache_data(show_spinner=False)
def load_local_excel(path, mtime):
    """
    Cache by (path, mtime). When mtime changes, Streamlit will call this again.
    Try to read as Excel first, fall back to CSV.
    """
    try:
        return pd.read_excel(path)
    except Exception:
        try:
            return pd.read_csv(path)
        except Exception as e:
            raise RuntimeError(f"Could not read file as Excel or CSV: {e}")

# Sidebar controls & info
with st.sidebar:
    st.header("Config")
    st.write("LOCAL_PATH")
    st.code(LOCAL_PATH, language="bash")
    st.write("Polling / viewer reload (seconds):", POLL_SECONDS)
    st.markdown("---")
    if st.button("Force reload now"):
        # Clear cache for this path so next read is fresh
        load_local_excel.clear()
        st.experimental_rerun()
    st.write("Last read attempt (UTC):")
    st.write(st.session_state.get("_last_read", "never"))

# Inject JS to refresh the page for passive viewers
reload_js = f"""
<script>
setTimeout(function() {{
  window.location.reload(true);
}}, {POLL_SECONDS * 1000});
</script>
"""
components.html(reload_js, height=0)

# Read file (cache keyed by mtime)
mtime = file_mtime(LOCAL_PATH)
try:
    df = load_local_excel(LOCAL_PATH, mtime)
    st.session_state["_last_read"] = time.strftime("%Y-%m-%d %H:%M:%S (UTC)", time.gmtime())
except Exception as e:
    st.error(f"Error loading file: {e}")
    st.stop()

st.subheader("Preview")
st.write(f"Rows: {len(df):,}  Columns: {len(df.columns):,}")
st.dataframe(df, use_container_width=True, height=600)

csv_bytes = df.to_csv(index=False).encode("utf-8")
st.download_button("Download current snapshot (CSV)", data=csv_bytes, file_name="snapshot.csv", mime="text/csv")

with st.expander("Debug / metadata"):
    st.write("File mtime (seconds since epoch):", mtime)
    st.write("File size (bytes):", os.path.getsize(LOCAL_PATH))
    st.write(df.head(20))
