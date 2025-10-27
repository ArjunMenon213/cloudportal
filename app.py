import os
import re
import base64
from io import StringIO
from datetime import datetime, timedelta

import pandas as pd
import requests
import streamlit as st
import streamlit.components.v1 as components

st.set_page_config(page_title="TRACKER", layout="wide")

TITLE = "TRACKER : Automated tool inventory management online inventory management portal"

# -------------------------
# Demo data initializer
# -------------------------
def init_data():
    inventory = pd.DataFrame([
        {"id": 1, "name": "Cordless Drill", "category": "Power Tools", "quantity": 5, "location": "Shelf A1", "status": "available", "last_updated": datetime.now().isoformat()},
        {"id": 2, "name": "Hammer", "category": "Hand Tools", "quantity": 10, "location": "Shelf B3", "status": "available", "last_updated": (datetime.now()-timedelta(days=1)).isoformat()},
        {"id": 3, "name": "Multimeter", "category": "Electronics", "quantity": 2, "location": "Shelf C2", "status": "checked_out", "last_updated": (datetime.now()-timedelta(days=2)).isoformat()},
        {"id": 4, "name": "Safety Glasses", "category": "PPE", "quantity": 0, "location": "Shelf D1", "status": "missing", "last_updated": (datetime.now()-timedelta(days=5)).isoformat()},
        {"id": 5, "name": "Screwdriver Set", "category": "Hand Tools", "quantity": 3, "location": "Shelf B1", "status": "available", "last_updated": datetime.now().isoformat()},
    ])
    usage = pd.DataFrame([
        {"event_id": 101, "item_id": 3, "item_name": "Multimeter", "user": "alice", "action": "checked_out", "timestamp": (datetime.now()-timedelta(days=2)).isoformat()},
        {"event_id": 102, "item_id": 1, "item_name": "Cordless Drill", "user": "bob", "action": "checked_out", "timestamp": (datetime.now()-timedelta(hours=5)).isoformat()},
        {"event_id": 103, "item_id": 1, "item_name": "Cordless Drill", "user": "bob", "action": "returned", "timestamp": (datetime.now()-timedelta(hours=2)).isoformat()},
        {"event_id": 104, "item_id": 4, "item_name": "Safety Glasses", "user": "charlie", "action": "reported_missing", "timestamp": (datetime.now()-timedelta(days=5)).isoformat()},
    ])
    users = ["alice", "bob", "charlie", "admin"]
    return inventory, usage, users

# -------------------------
# Configs: sheet URLs & images
# -------------------------
DRAWER_URLS = {
    1: "https://docs.google.com/spreadsheets/d/1tbGORyBH36yx2R_iR1IYcHu4MwbSKrfE/edit?usp=drive_link&ouid=115545081311750015459&rtpof=true&sd=true",
    2: "https://docs.google.com/spreadsheets/d/1JOYSm855CuvnA6d-QXZC82Vpe0BrlrWi/edit?usp=sharing&ouid=115545081311750015459&rtpof=true&sd=true",
    3: "https://docs.google.com/spreadsheets/d/10Y_HRew2IdvVlXMe8Kf5RFJGAieZtllC/edit?usp=drive_link&ouid=115545081311750015459&rtpof=true&sd=true",
    4: "https://docs.google.com/spreadsheets/d/1Zsv2g7p_kb_Vmt2R5iD5G9GBbhmwLZSF/edit?usp=drive_link&ouid=115545081311750015459&rtpof=true&sd=true",
    5: "https://docs.google.com/spreadsheets/d/1m06qyNzwYF_0fZnFpZA0QSpiumqdsHtr/edit?usp=drive_link&ouid=115545081311750015459&rtpof=true&sd=true",
    6: "https://docs.google.com/spreadsheets/d/1wJU5SC9VL5yeewjZivBRbyO3LtiXrVA9/edit?usp=sharing&ouid=115545081311750015459&rtpof=true&sd=true",
    7: "https://docs.google.com/spreadsheets/d/1Dc0myxSLB_dTSR-eFE4BZ8ZjqnSpDBkA/edit?usp=sharing&ouid=115545081311750015459&rtpof=true&sd=true",
}

DRAWER_IMAGES = {i: f"tools-drawer{i}.jpg" for i in range(1, 8)}

CUSTOMER_SHEET_URL = "https://docs.google.com/spreadsheets/d/1zpeOkT6cBPOMlVWeqHG9YLpEaT8YTIse/edit?usp=sharing&ouid=115545081311750015459&rtpof=true&sd=true"

# -------------------------
# Helpers
# -------------------------
def extract_doc_id(sheet_url: str) -> str:
    m = re.search(r"/d/([a-zA-Z0-9-_]+)", sheet_url)
    return m.group(1) if m else ""

def extract_gid(sheet_url: str) -> str:
    m = re.search(r"[#&]gid=([0-9]+)", sheet_url)
    if m:
        return m.group(1)
    m = re.search(r"[?&]gid=([0-9]+)", sheet_url)
    if m:
        return m.group(1)
    return "0"

def build_export_urls(doc_id: str, gid: str):
    urls = []
    urls.append(f"https://docs.google.com/spreadsheets/d/{doc_id}/export?format=csv&gid={gid}")
    urls.append(f"https://docs.google.com/spreadsheets/d/{doc_id}/gviz/tq?tqx=out:csv&gid={gid}")
    return urls

def embed_local_image_html(path: str, width: int = 400, height: int = 306):
    if not os.path.exists(path):
        return None
    try:
        with open(path, "rb") as f:
            data = f.read()
        b64 = base64.b64encode(data).decode("utf-8")
        ext = os.path.splitext(path)[1].lower().lstrip(".")
        mime = f"image/{'jpeg' if ext in ['jpg','jpeg'] else ext}"
        html = f"""
        <div style="text-align:left;">
          <img src="data:{mime};base64,{b64}" width="{width}" height="{height}" style="object-fit:cover; border-radius:6px; display:block;" />
        </div>
        """
        return html
    except Exception:
        return None

def embed_local_image_responsive_html(path: str, max_width_px: int = 900, display_height_px: int = None):
    """
    Render a local file as a responsive image: width constrained by container,
    preserving aspect ratio. If display_height_px provided, set component height (for Streamlit).
    """
    if not os.path.exists(path):
        return None
    try:
        with open(path, "rb") as f:
            data = f.read()
        b64 = base64.b64encode(data).decode("utf-8")
        ext = os.path.splitext(path)[1].lower().lstrip(".")
        mime = f"image/{'jpeg' if ext in ['jpg','jpeg'] else ext}"
        # Use max-width to make image responsive and avoid clipping; height:auto preserves aspect ratio.
        html = f"""
        <div style="display:flex; justify-content:flex-start; align-items:center;">
          <img src="data:{mime};base64,{b64}" style="max-width:{max_width_px}px; width:100%; height:auto; border-radius:6px; display:block;" />
        </div>
        """
        return html
    except Exception:
        return None

def fetch_sheet_csv(sheet_url: str):
    doc_id = extract_doc_id(sheet_url)
    if not doc_id:
        return None, None, None, "Could not extract document id from URL."

    gid = extract_gid(sheet_url)
    candidate_urls = build_export_urls(doc_id, gid)

    last_status = None
    last_snippet = ""
    for url in candidate_urls:
        try:
            resp = requests.get(url, timeout=20)
        except Exception as e:
            last_status = None
            last_snippet = str(e)
            continue

        last_status = resp.status_code
        if resp.status_code == 200:
            try:
                df = pd.read_csv(StringIO(resp.text))
                return df, url, resp.status_code, resp.text[:800]
            except Exception as e:
                return None, url, resp.status_code, f"Fetched content but failed to parse CSV: {e}\nSnippet: {resp.text[:800]}"
        else:
            last_snippet = resp.text[:800]

    return None, candidate_urls[-1] if candidate_urls else None, last_status, last_snippet

# -------------------------
# Initialize session state
# -------------------------
if "inventory_df" not in st.session_state:
    inv, usage, users = init_data()
    st.session_state.inventory_df = inv
    st.session_state.usage_df = usage
    st.session_state.users = users
    st.session_state.selected = "Status"
    st.session_state.master_control = True
    st.session_state.selected_drawer = None
    st.session_state.admin_unlocked = False

# -------------------------
# Styles
# -------------------------
st.markdown(
    """
    <style>
    .tab-button { padding:6px 8px; border-radius:6px; }
    .status-pill { display:inline-block; padding:6px 12px; border-radius:14px; color:#ffffff; font-weight:700; background:#16a34a; }
    .passcode-box {
      display:block;
      width:100%;
      background-color:#16a34a;
      color:#ffffff;
      padding:18px;
      border-radius:8px;
      text-align:center;
      font-weight:800;
      font-size:36px;
      box-shadow: 0 4px 8px rgba(0,0,0,0.08);
    }
    .edit-link-btn {
      display:inline-block;
      padding:10px 16px;
      background:#2563eb;
      color:#fff;
      border-radius:6px;
      text-decoration:none;
      font-weight:700;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# -------------------------
# Top banner + title row
# -------------------------
# Show topbanner.png full width (responsive) and put the TITLE underneath it so the banner
# is fully visible and the title appears below.
banner_path = "topbanner.png"
if os.path.exists(banner_path):
    banner_html = embed_local_image_responsive_html(banner_path, max_width_px=900)
    if banner_html:
        # set height a bit larger to ensure the component isn't clipped; height is advisory
        components.html(banner_html, height=160)
    else:
        # fallback to st.image if embedding as HTML failed
        st.image(banner_path, use_column_width=True)
else:
    # placeholder if banner not found
    components.html(
        '<div style="display:flex; justify-content:flex-start; align-items:center;"><img src="https://via.placeholder.com/900x160.png?text=Banner" style="max-width:900px; width:100%; height:auto; border-radius:6px;" /></div>',
        height=160,
    )

# Title placed under the banner (left aligned)
st.markdown(f"<h1 style='margin:12px 0 12px 0; text-align:left;'>{TITLE}</h1>", unsafe_allow_html=True)

# Top nav bar
options = ["Status", "Usage History", "Inventory Data", "Missing Items", "Admin Panel"]
cols = st.columns([1,1,1,1,1], gap="small")
for i, opt in enumerate(options):
    with cols[i]:
        if st.button(opt, key=f"btn_{opt}"):
            st.session_state.selected = opt

# Auto-lock admin when navigating away from Admin Panel
if st.session_state.get("selected") != "Admin Panel" and st.session_state.get("admin_unlocked", False):
    st.session_state.admin_unlocked = False

pane = st.container()

# -------------------------
# Page panes
# -------------------------
def show_status():
    st.subheader("Status Panel")

    c1, c2 = st.columns([2, 4])
    with c1:
        st.write("1. Current Status")
    with c2:
        st.markdown('<span class="status-pill">ONLINE</span>', unsafe_allow_html=True)

    c1, c2 = st.columns([2, 4])
    with c1:
        st.write("2. Master Control")
    with c2:
        master = st.checkbox("", value=st.session_state.master_control, key="master_control_checkbox")
        st.write("ON" if master else "OFF")
        st.session_state.master_control = master

    c1, c2 = st.columns([2, 4])
    with c1:
        st.write("3. Current Time")
    with c2:
        clock_html = """
        <div>
          <span id="client-clock">--</span>
        </div>
        <script>
          function pad(n){ return n.toString().padStart(2,'0'); }
          function updateClock(){
            const now = new Date();
            const s = now.getFullYear() + '-' + pad(now.getMonth()+1) + '-' + pad(now.getDate())
                      + ' ' + pad(now.getHours()) + ':' + pad(now.getMinutes()) + ':' + pad(now.getSeconds());
            document.getElementById('client-clock').textContent = s;
          }
          updateClock();
          setInterval(updateClock, 1000);
        </script>
        """
        components.html(clock_html, height=40)

    c1, c2 = st.columns([2, 4])
    with c1:
        st.write("4. Current Location")
    with c2:
        st.write("Lehman Building of engineering")

    c1, c2 = st.columns([2, 4])
    with c1:
        st.write("5. Current Room")
    with c2:
        st.write("LB 172 - Robotics Research Lab")

def show_usage_history():
    st.subheader("Usage History")
    st.write("Select a drawer to view its image and sheet:")

    btn_cols = st.columns(7, gap="small")
    for i in range(1, 8):
        with btn_cols[i-1]:
            if st.button(f"Drawer {i}", key=f"drawer_btn_{i}"):
                st.session_state.selected_drawer = i

    st.markdown("---")
    selected = st.session_state.selected_drawer
    if selected is None:
        st.info("No drawer selected. Click a Drawer button above.")
        return

    st.write(f"Displaying: Drawer {selected}")

    local_img = DRAWER_IMAGES.get(selected)
    if local_img and os.path.exists(local_img):
        img_html = embed_local_image_html(local_img, width=400, height=306)
        if img_html:
            components.html(img_html, height=330)
        else:
            st.image(local_img, width=400)
    else:
        placeholder = f"https://via.placeholder.com/400x306.png?text=Drawer+{selected}+Image+not+found"
        components.html(f'<div style="text-align:center;"><img src="{placeholder}" width="400" height="306" style="object-fit:cover; border-radius:6px;" /></div>', height=330)

    sheet_url = DRAWER_URLS.get(selected)
    if not sheet_url:
        st.error("No sheet URL configured for this drawer.")
        return

    st.write("Loading sheet as CSV... (attempting multiple export endpoints)")
    df, used_url, status, snippet = fetch_sheet_csv(sheet_url)

    if df is None:
        st.error("Failed to load CSV.")
        if status:
            st.write(f"Last HTTP status: {status}")
        if used_url:
            st.write(f"Last tried URL: {used_url}")
        if snippet:
            st.write("Response / error snippet (truncated):")
            st.code(snippet)
        st.info("Common fixes: set the sheet's Share → 'Anyone with the link' → Viewer, or Publish → 'Publish to web' for that sheet/tab. If sheets are private, use a service account (gspread).")
        return

    first_col = df.columns[0]
    df[first_col] = pd.to_numeric(df[first_col], errors='coerce')
    df_sorted = df.sort_values(by=first_col, ascending=True, na_position='last').reset_index(drop=True)

    if df_sorted.shape[1] > 6:
        df_display = df_sorted.iloc[:, :6].copy()
    else:
        df_display = df_sorted.copy()

    st.success(f"Loaded sheet from: {used_url}  (rows: {len(df_sorted)}, cols: {len(df_sorted.columns)})")
    st.dataframe(df_display)
    st.download_button("Download sheet CSV", data=df_sorted.to_csv(index=False).encode("utf-8"), file_name=f"drawer_{selected}.csv", mime="text/csv")

def show_inventory_data():
    st.subheader("Inventory Data")
    inv = st.session_state.inventory_df.copy()
    st.write("You can add new items using the form below. Use the table to review current inventory. (This demo stores data in memory for this session.)")

    with st.expander("Add new inventory item"):
        with st.form("add_item_form", clear_on_submit=True):
            name = st.text_input("Item name")
            category = st.text_input("Category")
            quantity = st.number_input("Quantity", min_value=0, step=1, value=1)
            location = st.text_input("Location")
            submitted = st.form_submit_button("Add item")
            if submitted:
                new_id = int(inv["id"].max() + 1) if not inv.empty else 1
                new_item = {"id": new_id, "name": name, "category": category or "Uncategorized",
                            "quantity": int(quantity), "location": location or "Unspecified",
                            "status": "available" if quantity > 0 else "missing",
                            "last_updated": datetime.now().isoformat()}
                st.session_state.inventory_df = pd.concat([st.session_state.inventory_df, pd.DataFrame([new_item])], ignore_index=True)
                st.success(f"Added item '{name}' (id: {new_id})")

    st.download_button("Download inventory CSV", data=st.session_state.inventory_df.to_csv(index=False).encode("utf-8"), file_name="inventory_export.csv", mime="text/csv")
    st.subheader("Inventory Table")
    st.dataframe(st.session_state.inventory_df.sort_values(["category", "name"]).reset_index(drop=True))

def show_missing_items():
    """
    For each drawer (1..7) render one row: left=currently removed items (by grouping on col1 and
    taking group's last entry and checking col2 for 'removed'), right=image (250x191).
    Each row has a fixed height so image and table align.
    """
    st.subheader("Missing Items — Currently Removed (based on last history entry)")

    row_table_height = 200

    for i in range(1, 8):
        st.markdown(f"### Drawer {i}")
        left_col, right_col = st.columns([3, 1])

        # LEFT: compute currently removed items
        with left_col:
            sheet_url = DRAWER_URLS.get(i)
            if not sheet_url:
                st.info(f"Drawer {i}: no sheet URL configured.")
                components.html(f'<div style="height:{row_table_height}px;"></div>', height=8)
            else:
                df, used_url, status, snippet = fetch_sheet_csv(sheet_url)
                if df is None:
                    st.warning(f"Drawer {i}: failed to load sheet. Last status: {status}")
                    if used_url:
                        st.write(f"Last tried URL: {used_url}")
                    if snippet:
                        st.code(snippet)
                    components.html(f'<div style="height:{row_table_height}px;"></div>', height=8)
                else:
                    if df.shape[1] < 2:
                        st.info(f"Drawer {i}: sheet has fewer than 2 columns; cannot determine last action.")
                        components.html(f'<div style="height:{row_table_height}px;"></div>', height=8)
                    else:
                        first_col = df.columns[0]
                        second_col = df.columns[1]
                        # group and get last row per key (preserve file order)
                        try:
                            last_indices = df.groupby(df[first_col], sort=False).apply(lambda g: g.index[-1])
                            last_idx_list = list(last_indices.values)
                            last_rows = df.loc[last_idx_list].reset_index(drop=True)
                        except Exception:
                            grouped = {}
                            for idx, row in df.iterrows():
                                key = row[first_col]
                                grouped[key] = idx
                            last_idx_list = list(grouped.values())
                            last_rows = df.loc[last_idx_list].reset_index(drop=True)

                        mask = last_rows[second_col].astype(str).str.lower().str.contains("removed", na=False)
                        currently_removed = last_rows[mask].reset_index(drop=True)

                        if currently_removed.empty:
                            st.write("No currently removed items found in this drawer (based on the last history entry).")
                            components.html(f'<div style="height:{row_table_height}px;"></div>', height=8)
                        else:
                            if currently_removed.shape[1] > 6:
                                display_df = currently_removed.iloc[:, :6].copy()
                            else:
                                display_df = currently_removed.copy()
                            st.dataframe(display_df, height=row_table_height)

        # RIGHT: image
        with right_col:
            img_path = DRAWER_IMAGES.get(i)
            if img_path and os.path.exists(img_path):
                img_html = embed_local_image_html(img_path, width=250, height=191)
                if img_html:
                    components.html(img_html, height=row_table_height)
                else:
                    st.image(img_path, width=250, caption=f"Drawer {i}")
                    components.html(f'<div style="height:{row_table_height - 24}px;"></div>', height=8)
            else:
                placeholder = f"https://via.placeholder.com/250x191.png?text=Drawer+{i}"
                components.html(f'<div style="text-align:center;"><img src="{placeholder}" width="250" height="191" style="object-fit:cover; border-radius:6px;" /></div>', height=row_table_height)

def show_admin_panel():
    """
    Admin panel locked behind passcode "3721".
    Auto-locks when the user navigates away from Admin Panel.
    """
    st.subheader("Admin Panel")

    unlocked = st.session_state.get("admin_unlocked", False)

    if not unlocked:
        st.write("Admin access requires passcode.")
        entered = st.text_input("Enter passcode to unlock admin panel", type="password", key="admin_pass_input")
        if st.button("Unlock Admin Panel"):
            if entered == "3721":
                st.session_state.admin_unlocked = True
                st.success("Admin panel unlocked.")
                return
            else:
                st.error("Incorrect passcode.")
                return
        return

    # Unlocked view
    st.markdown('<div class="passcode-box">"Current access passcode for all utilities: 3721</div>', unsafe_allow_html=True)

    st.markdown("---")
    st.markdown("### current customers with access")

    st.write("Loading customers sheet... (attempting multiple export endpoints)")
    df, used_url, status, snippet = fetch_sheet_csv(CUSTOMER_SHEET_URL)

    if df is None:
        st.error("Failed to load customers sheet.")
        if status:
            st.write(f"Last HTTP status: {status}")
        if used_url:
            st.write(f"Last tried URL: {used_url}")
        if snippet:
            st.write("Response / error snippet (truncated):")
            st.code(snippet)
        st.info("Common fixes: set the sheet's Share → 'Anyone with the link' → Viewer, or Publish → 'Publish to web' for that sheet/tab.")
        return

    if df.shape[1] > 6:
        df_display = df.iloc[:, :6].copy()
    else:
        df_display = df.copy()

    st.success(f"Loaded sheet from: {used_url}  (rows: {len(df)}, cols: {len(df.columns)})")
    st.dataframe(df_display)
    st.download_button("Download customers CSV", data=df.to_csv(index=False).encode("utf-8"), file_name="current_customers.csv", mime="text/csv")

    edit_button_html = f'''
      <div style="margin-top:12px;">
        <a class="edit-link-btn" href="{CUSTOMER_SHEET_URL}" target="_blank" rel="noopener noreferrer">Edit Customer access Credentials</a>
      </div>
    '''
    st.markdown(edit_button_html, unsafe_allow_html=True)

# -------------------------
# Render selected pane
# -------------------------
with pane:
    selected = st.session_state.selected
    if selected == "Status":
        show_status()
    elif selected == "Usage History":
        show_usage_history()
    elif selected == "Inventory Data":
        show_inventory_data()
    elif selected == "Missing Items":
        show_missing_items()
    elif selected == "Admin Panel":
        show_admin_panel()
    else:
        st.write("Select a section from the bar above.")

st.markdown("----")
st.caption("This is a demo Streamlit app. Data is stored only for the current session. For production use, connect to a database and add authentication.")
