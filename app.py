import streamlit as st
import pandas as pd
import altair as alt
from datetime import datetime, timedelta
import streamlit.components.v1 as components
import re

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

# Google Sheets links for drawers (as provided)
DRAWER_URLS = {
    1: "https://docs.google.com/spreadsheets/d/1tbGORyBH36yx2R_iR1IYcHu4MwbSKrfE/edit?usp=drive_link&ouid=115545081311750015459&rtpof=true&sd=true",
    2: "https://docs.google.com/spreadsheets/d/1JOYSm855CuvnA6d-QXZC82Vpe0BrlrWi/edit?usp=sharing&ouid=115545081311750015459&rtpof=true&sd=true",
    3: "https://docs.google.com/spreadsheets/d/10Y_HRew2IdvVlXMe8Kf5RFJGAieZtllC/edit?usp=drive_link&ouid=115545081311750015459&rtpof=true&sd=true",
    4: "https://docs.google.com/spreadsheets/d/1Zsv2g7p_kb_Vmt2R5iD5G9GBbhmwLZSF/edit?usp=drive_link&ouid=115545081311750015459&rtpof=true&sd=true",
    5: "https://docs.google.com/spreadsheets/d/1m06qyNzwYF_0fZnFpZA0QSpiumqdsHtr/edit?usp=drive_link&ouid=115545081311750015459&rtpof=true&sd=true",
    6: "https://docs.google.com/spreadsheets/d/1wJU5SC9VL5yeewjZivBRbyO3LtiXrVA9/edit?usp=sharing&ouid=115545081311750015459&rtpof=true&sd=true",
    7: "https://docs.google.com/spreadsheets/d/1Dc0myxSLB_dTSR-eFE4BZ8ZjqnSpDBkA/edit?usp=sharing&ouid=115545081311750015459&rtpof=true&sd=true",
}

def extract_sheet_embed_url(sheet_url: str) -> str:
    """
    Try to build an embeddable URL for a Google Sheet.
    Best-effort: extract the doc id and use the /preview path which usually works for public/shareable sheets.
    """
    # extract id from /d/<id>/
    m = re.search(r"/d/([a-zA-Z0-9-_]+)", sheet_url)
    if not m:
        return sheet_url  # fallback to original
    _id = m.group(1)
    # Use preview path which is commonly embeddable:
    return f"https://docs.google.com/spreadsheets/d/{_id}/preview"

# Initialize demo data and state
if "inventory_df" not in st.session_state:
    inv, usage, users = init_data()
    st.session_state.inventory_df = inv
    st.session_state.usage_df = usage
    st.session_state.users = users
    st.session_state.selected = "Status"
    st.session_state.master_control = True
    # default no drawer selected
    st.session_state.selected_drawer = None

# Minimal styling: keep Streamlit defaults for typography; only style ONLINE pill slightly.
st.markdown(
    """
    <style>
    .tab-button { padding:6px 8px; border-radius:6px; }
    .status-pill { display:inline-block; padding:6px 12px; border-radius:14px; color:#ffffff; font-weight:700; background:#16a34a; }
    .drawer-btn { width:100%; }
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
    """
    Render 7 horizontal drawer buttons (Drawer 1 .. Drawer 7).
    When a drawer button is pressed, set session_state.selected_drawer to that number.
    Below the buttons, embed the corresponding Google Sheet (using a best-effort preview/embed URL).
    """
    st.subheader("Usage History")

    st.write("Select a drawer to view its sheet:")

    # Horizontal row of 7 buttons
    cols = st.columns(7, gap="small")
    for i in range(1, 8):
        with cols[i-1]:
            if st.button(f"Drawer {i}", key=f"drawer_btn_{i}"):
                st.session_state.selected_drawer = i

    # Panel: embed selected sheet (or show informational message)
    st.markdown("---")
    if st.session_state.selected_drawer is None:
        st.info("No drawer selected. Click a drawer button above to load its sheet.")
        return

    selected = st.session_state.selected_drawer
    st.write(f"Displaying: Drawer {selected}")

    sheet_url = DRAWER_URLS.get(selected)
    if not sheet_url:
        st.error("URL for selected drawer not found.")
        return

    embed_url = extract_sheet_embed_url(sheet_url)

    # Embed the Google Sheet in an iframe. Height can be adjusted as needed.
    iframe_html = f"""
    <div style="width:100%;">
      <iframe src="{embed_url}" style="width:100%; height:720px; border:0;" allowfullscreen></iframe>
    </div>
    """
    components.html(iframe_html, height=740)

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
    st.subheader("Missing Items")
    inv = st.session_state.inventory_df
    missing_df = inv[inv["status"] == "missing"].copy()
    if missing_df.empty:
        st.success("No missing items! Great job.")
        return
    st.dataframe(missing_df.reset_index(drop=True))
    st.write("Actions")
    rows = missing_df.to_dict("records")
    for item in rows:
        cols = st.columns([3,1])
        cols[0].write(f"ID {item['id']} — {item['name']} ({item['category']}) — Location: {item['location']} — Qty: {item['quantity']}")
        if cols[1].button("Mark Found", key=f"found_{item['id']}"):
            idx = st.session_state.inventory_df.index[st.session_state.inventory_df["id"] == item["id"]].tolist()
            if idx:
                st.session_state.inventory_df.at[idx[0], "status"] = "available"
                st.session_state.inventory_df.at[idx[0], "last_updated"] = datetime.now().isoformat()
                new_event = {"event_id": int(st.session_state.usage_df["event_id"].max() + 1) if not st.session_state.usage_df.empty else 1,
                             "item_id": item["id"], "item_name": item["name"], "user": "system", "action": "marked_found", "timestamp": datetime.now().isoformat()}
                st.session_state.usage_df = pd.concat([st.session_state.usage_df, pd.DataFrame([new_event])], ignore_index=True)
                st.experimental_rerun()

def show_admin_panel():
    st.subheader("Admin Panel")
    st.write("Manage users and global settings. This is a simplified admin view for the demo.")
    st.write("Registered users")
    st.dataframe(pd.DataFrame({"user": st.session_state.users}))

    with st.form("add_user"):
        new_user = st.text_input("Add user (username)")
        add_submitted = st.form_submit_button("Add user")
        if add_submitted and new_user:
            if new_user in st.session_state.users:
                st.warning("User already exists.")
            else:
                st.session_state.users.append(new_user)
                st.success(f"User '{new_user}' added.")

    with st.form("remove_user"):
        remove_user = st.selectbox("Remove user", options=[""] + st.session_state.users)
        remove_submitted = st.form_submit_button("Remove user")
        if remove_submitted and remove_user:
            st.session_state.users = [u for u in st.session_state.users if u != remove_user]
            st.success(f"User '{remove_user}' removed.")

    st.markdown("---")
    st.write("Danger zone")
    if st.button("Reset demo data (in-session only)"):
        inv, usage, users = init_data()
        st.session_state.inventory_df = inv
        st.session_state.usage_df = usage
        st.session_state.users = users
        st.session_state.master_control = True
        st.session_state.selected_drawer = None
        st.success("Demo data reset.")
        st.experimental_rerun()

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
