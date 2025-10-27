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

# Drawer Google Sheet URLs (as provided)
DRAWER_URLS = {
    1: "https://docs.google.com/spreadsheets/d/1tbGORyBH36yx2R_iR1IYcHu4MwbSKrfE/edit?usp=drive_link&ouid=115545081311750015459&rtpof=true&sd=true",
    2: "https://docs.google.com/spreadsheets/d/1JOYSm855CuvnA6d-QXZC82Vpe0BrlrWi/edit?usp=sharing&ouid=115545081311750015459&rtpof=true&sd=true",
    3: "https://docs.google.com/spreadsheets/d/10Y_HRew2IdvVlXMe8Kf5RFJGAieZtllC/edit?usp=drive_link&ouid=115545081311750015459&rtpof=true&sd=true",
    4: "https://docs.google.com/spreadsheets/d/1Zsv2g7p_kb_Vmt2R5iD5G9GBbhmwLZSF/edit?usp=drive_link&ouid=115545081311750015459&rtpof=true&sd=true",
    5: "https://docs.google.com/spreadsheets/d/1m06qyNzwYF_0fZnFpZA0QSpiumqdsHtr/edit?usp=drive_link&ouid=115545081311750015459&rtpof=true&sd=true",
    6: "https://docs.google.com/spreadsheets/d/1wJU5SC9VL5yeewjZivBRbyO3LtiXrVA9/edit?usp=sharing&ouid=115545081311750015459&rtpof=true&sd=true",
    7: "https://docs.google.com/spreadsheets/d/1Dc0myxSLB_dTSR-eFE4BZ8ZjqnSpDBkA/edit?usp=sharing&ouid=115545081311750015459&rtpof=true&sd=true",
}

# Local images in repo: tools-drawer1.jpg ... tools-drawer7.jpg
DRAWER_IMAGES = {i: f"tools-drawer{i}.jpg" for i in range(1, 8)}

# Customer sheet URL for Admin panel (as requested)
CUSTOMER_SHEET_URL = "https://docs.google.com/spreadsheets/d/1zpeOkT6cBPOMlVWeqHG9YLpEaT8YTIse/edit?usp=sharing&ouid=115545081311750015459&rtpof=true&sd=true"

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
    """
    Read local image file and return HTML <img> with data URI and fixed dimensions.
    This avoids use_column_width deprecation and forces the desired width/height.
    """
    if not os.path.exists(path):
        return None
    try:
        with open(path, "rb") as f:
            data = f.read()
        b64 = base64.b64encode(data).decode("utf-8")
        ext = os.path.splitext(path)[1].lower().lstrip(".")
        mime = f"image/{'jpeg' if ext in ['jpg','jpeg'] else ext}"
        html = f"""
        <div style="text-align:center;">
          <img src="data:{mime};base64,{b64}" width="{width}" height="{height}" style="object-fit:cover; border-radius:6px; display:block; margin-left:auto; margin-right:auto;" />
        </div>
        """
        return html
    except Exception as e:
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

# Initialize demo data and session state
if "inventory_df" not in st.session_state:
    inv, usage, users = init_data()
    st.session_state.inventory_df = inv
    st.session_state.usage_df = usage
    st.session_state.users = users
    st.session_state.selected = "Status"
    st.session_state.master_control = True
    st.session_state.selected_drawer = None

# Minimal styling
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

st.title(TITLE)

# Top nav bar (buttons)
options = ["Status", "Usage History", "Inventory Data", "Missing Items", "Admin Panel"]
cols = st.columns([1,1,1,1,1], gap="small")
for i, opt in enumerate(options):
    with cols[i]:
        if st.button(opt, key=f"btn_{opt}"):
            st.session_state.selected = opt

pane = st.container()

def show_status():
    st.subheader("Status Panel")

    # Row 1: Current Status - green pill
    c1, c2 = st.columns([2, 4])
    with c1:
        st.write("1. Current Status")
    with c2:
        st.markdown('<span class="status-pill">ONLINE</span>', unsafe_allow_html=True)

    # Row 2: Master Control - checkbox that toggles visually only
    c1, c2 = st.columns([2, 4])
    with c1:
        st.write("2. Master Control")
    with c2:
        master = st.checkbox("", value=st.session_state.master_control, key="master_control_checkbox")
        st.write("ON" if master else "OFF")
        st.session_state.master_control = master

    # Row 3: Current Time - show browser time via client-side JS
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

    # Row 4: Current Location (static)
    c1, c2 = st.columns([2, 4])
    with c1:
        st.write("4. Current Location")
    with c2:
        st.write("Lehman Building of engineering")

    # Row 5: Current Room (static)
    c1, c2 = st.columns([2, 4])
    with c1:
        st.write("5. Current Room")
    with c2:
        st.write("LB 172 - Robotics Research Lab")

def show_usage_history():
    st.subheader("Usage History")
    st.write("Select a drawer to view its image and sheet:")

    # Horizontal row of 7 buttons
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

    # Show local repository image first with fixed dimensions 400x306
    local_img = DRAWER_IMAGES.get(selected)
    if local_img and os.path.exists(local_img):
        img_html = embed_local_image_html(local_img, width=400, height=306)
        if img_html:
            components.html(img_html, height=330)  # a bit taller to accommodate padding
        else:
            st.image(local_img, width=400)  # fallback, may preserve aspect ratio
    else:
        # fallback placeholder as embedded image
        placeholder = f"https://via.placeholder.com/400x306.png?text=Drawer+{selected}+Image+not+found"
        components.html(f'<div style="text-align:center;"><img src="{placeholder}" width="400" height="306" style="object-fit:cover; border-radius:6px;" /></div>', height=330)

    # Fetch and show CSV
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

    # Sort by first column ascending (convert to numeric if possible)
    first_col = df.columns[0]
    df[first_col] = pd.to_numeric(df[first_col], errors='coerce')
    df_sorted = df.sort_values(by=first_col, ascending=True, na_position='last').reset_index(drop=True)

    # --- Display only up to 6 columns in the UI, but keep the full dataframe for download/logic ---
    if df_sorted.shape[1] > 6:
        df_display = df_sorted.iloc[:, :6].copy()
    else:
        df_display = df_sorted.copy()

    st.success(f"Loaded sheet from: {used_url}  (rows: {len(df_sorted)}, cols: {len(df_sorted.columns)})")
    # Show only the first 6 columns (or fewer if sheet has <6 cols)
    st.dataframe(df_display)
    # Keep download as full CSV to avoid changing sheet export logic
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

    st.download_button("Download inventory CSV", data=st.session_state.inventory_df.to_csv(index=False), file_name="inventory_export.csv", mime="text/csv")
    st.subheader("Inventory Table")
    st.dataframe(st.session_state.inventory_df.sort_values(["category", "name"]).reset_index(drop=True))

def show_missing_items():
    """
    For each drawer (1..7) render a single row containing:
      - left: the "currently removed" items computed by grouping on the first column and
              checking the last entry (chronological) of each group for the word 'removed'
              (searching the second column for the action).
      - right: the drawer image sized width=250 height=191.

    The logic:
      - keep sheet-fetching/export logic unchanged (fetch_sheet_csv).
      - assume CSV rows are chronological in file order (first row = earliest).
      - group rows by the first column's value, determine each group's last row (by order),
        and consider the item "missing" if that last row's second-column value contains 'removed'
        (case-insensitive).
      - display the last-row entries for items that are currently removed.
    """
    st.subheader("Missing Items — Currently Removed (based on last history entry)")

    # Per-drawer rows: each drawer gets its own two-column row so table and image stay aligned
    row_table_height = 200  # px; dataframe will be shown with this height so images align

    for i in range(1, 8):
        st.markdown(f"### Drawer {i}")
        left_col, right_col = st.columns([3, 1])

        # LEFT: compute "currently removed" entries using last-entry-per-group logic
        with left_col:
            sheet_url = DRAWER_URLS.get(i)
            if not sheet_url:
                st.info(f"Drawer {i}: no sheet URL configured.")
                # spacer so heights remain consistent
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
                    # Need at least 2 columns: first column is grouping key, second column contains the action text
                    if df.shape[1] < 2:
                        st.info(f"Drawer {i}: sheet has fewer than 2 columns; cannot determine last action.")
                        components.html(f'<div style="height:{row_table_height}px;"></div>', height=8)
                    else:
                        first_col = df.columns[0]
                        second_col = df.columns[1]

                        # Keep original row order (assume file order is chronological). Use groupby to get last row index per group.
                        try:
                            # groupby preserves the order of appearance when sort=False
                            last_indices = df.groupby(df[first_col], sort=False).apply(lambda g: g.index[-1])
                            # last_indices is a Series with group keys -> index; get the indices as list
                            last_idx_list = list(last_indices.values)
                            last_rows = df.loc[last_idx_list].reset_index(drop=True)
                        except Exception:
                            # fallback: for safety, compute by iterating groups
                            grouped = {}
                            for idx, row in df.iterrows():
                                key = row[first_col]
                                grouped[key] = idx
                            last_idx_list = list(grouped.values())
                            last_rows = df.loc[last_idx_list].reset_index(drop=True)

                        # Now filter last_rows where second_col contains 'removed' (case-insensitive)
                        mask = last_rows[second_col].astype(str).str.lower().str.contains("removed", na=False)
                        currently_removed = last_rows[mask].reset_index(drop=True)

                        if currently_removed.empty:
                            st.write("No currently removed items found in this drawer (based on the last history entry).")
                            components.html(f'<div style="height:{row_table_height}px;"></div>', height=8)
                        else:
                            # Show only up to 6 columns for visual consistency
                            if currently_removed.shape[1] > 6:
                                display_df = currently_removed.iloc[:, :6].copy()
                            else:
                                display_df = currently_removed.copy()
                            st.dataframe(display_df, height=row_table_height)

        # RIGHT: image sized 250x191
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
    Admin panel redesigned per request:
      - Large green highlighted passcode "Current access passcode for all utilities: 3721"
      - Horizontal separator
      - "current customers with access" sheet loaded using the same fetch logic
      - After the sheet, an "Edit Customer access Credentials" button that links to the Google Sheet URL
    """
    st.subheader("Admin Panel")

    # Large green highlighted passcode
    # using the CSS class defined earlier .passcode-box
    st.markdown('<div class="passcode-box">Current access passcode for all utilities: 3721</div>', unsafe_allow_html=True)

    # horizontal separator
    st.markdown("---")

    # Title
    st.markdown("### current customers with access")

    # Load and display the provided Google Sheet using existing fetch logic
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

    # Display only first 6 columns in the UI for consistency (full CSV available for download)
    if df.shape[1] > 6:
        df_display = df.iloc[:, :6].copy()
    else:
        df_display = df.copy()

    st.success(f"Loaded sheet from: {used_url}  (rows: {len(df)}, cols: {len(df.columns)})")
    st.dataframe(df_display)
    st.download_button("Download customers CSV", data=df.to_csv(index=False).encode("utf-8"), file_name="current_customers.csv", mime="text/csv")

    # "Edit Customer access Credentials" button linking to the sheet
    # Use an HTML anchor styled as a button to open the sheet in a new tab
    edit_button_html = f'''
      <div style="margin-top:12px;">
        <a class="edit-link-btn" href="{CUSTOMER_SHEET_URL}" target="_blank" rel="noopener noreferrer">Edit Customer access Credentials</a>
      </div>
    '''
    st.markdown(edit_button_html, unsafe_allow_html=True)

# Render selected pane
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
