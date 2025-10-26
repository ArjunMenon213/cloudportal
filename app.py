import streamlit as st
import pandas as pd
import altair as alt
from datetime import datetime, timedelta
import streamlit.components.v1 as components

st.set_page_config(page_title="TRACKER", layout="wide")

TITLE = "TRACKER : Automated tool inventory management online inventory management portal"

def init_data():
    # sample inventory
    inventory = pd.DataFrame([
        {"id": 1, "name": "Cordless Drill", "category": "Power Tools", "quantity": 5, "location": "Shelf A1", "status": "available", "last_updated": datetime.now().isoformat()},
        {"id": 2, "name": "Hammer", "category": "Hand Tools", "quantity": 10, "location": "Shelf B3", "status": "available", "last_updated": (datetime.now()-timedelta(days=1)).isoformat()},
        {"id": 3, "name": "Multimeter", "category": "Electronics", "quantity": 2, "location": "Shelf C2", "status": "checked_out", "last_updated": (datetime.now()-timedelta(days=2)).isoformat()},
        {"id": 4, "name": "Safety Glasses", "category": "PPE", "quantity": 0, "location": "Shelf D1", "status": "missing", "last_updated": (datetime.now()-timedelta(days=5)).isoformat()},
        {"id": 5, "name": "Screwdriver Set", "category": "Hand Tools", "quantity": 3, "location": "Shelf B1", "status": "available", "last_updated": datetime.now().isoformat()},
    ])
    # sample usage history
    usage = pd.DataFrame([
        {"event_id": 101, "item_id": 3, "item_name": "Multimeter", "user": "alice", "action": "checked_out", "timestamp": (datetime.now()-timedelta(days=2)).isoformat()},
        {"event_id": 102, "item_id": 1, "item_name": "Cordless Drill", "user": "bob", "action": "checked_out", "timestamp": (datetime.now()-timedelta(hours=5)).isoformat()},
        {"event_id": 103, "item_id": 1, "item_name": "Cordless Drill", "user": "bob", "action": "returned", "timestamp": (datetime.now()-timedelta(hours=2)).isoformat()},
        {"event_id": 104, "item_id": 4, "item_name": "Safety Glasses", "user": "charlie", "action": "reported_missing", "timestamp": (datetime.now()-timedelta(days=5)).isoformat()},
    ])
    users = ["alice", "bob", "charlie", "admin"]
    return inventory, usage, users

# Initialize session state and demo data
if "inventory_df" not in st.session_state:
    inv, usage, users = init_data()
    st.session_state.inventory_df = inv
    st.session_state.usage_df = usage
    st.session_state.users = users
    st.session_state.selected = "Status"
    st.session_state.master_control = True  # default state for the visible switch

# Styling for improved contrast and visible clock
st.markdown(
    """
    <style>
    /* tab bar */
    .tab-button {width:100%; padding:6px 8px; border-radius:6px;}
    .tab-active {background-color:#0f62fe;color:white;}
    /* status row layout */
    .status-row {display:flex; align-items:center; gap:12px; padding:10px 0; border-bottom: 1px solid #f3f4f6;}
    .status-label {min-width:260px; color:#0b3b6e; font-weight:700; font-size:14px;} /* darker blue for labels */
    .status-value {font-weight:700; color:#0b4a6f; font-size:14px;} /* readable blue for values */
    .status-pill {display:inline-block; padding:6px 14px; border-radius:16px; color:white; font-weight:800; background:#16a34a;}
    .clock {font-family:monospace; font-weight:800; color:#b45309; background:#fff7ed; padding:6px 10px; border-radius:8px; border:1px solid #f6ad55;}
    .panel {padding:6px 4px;}
    .switch-checkbox > label {vertical-align: middle;}
    </style>
    """,
    unsafe_allow_html=True,
)

st.title(TITLE)

# horizontal option bar implemented with columns + buttons
options = ["Status", "Usage History", "Inventory Data", "Missing Items", "Admin Panel"]
cols = st.columns([1,1,1,1,1], gap="small")
for i, opt in enumerate(options):
    with cols[i]:
        if st.button(opt, key=f"btn_{opt}"):
            st.session_state.selected = opt

pane = st.container()

def show_status():
    """
    Render the status panel exactly as requested:
    - Current Status: ONLINE (green pill)
    - Master Control: an on/off switch (checkbox) that toggles visually
    - Current Time: browser clock (client-side) displayed live
    - Current Location: static text
    - Current Room: static text
    Each item is shown on one horizontal line with improved color contrast.
    """
    st.subheader("Status Panel")
    with st.container():
        # Row 1: Current Status (static green pill)
        r1_col = st.columns([2,4])
        with r1_col[0]:
            st.markdown('<div class="status-label">1. Current Status</div>', unsafe_allow_html=True)
        with r1_col[1]:
            st.markdown('<div class="status-value"><span class="status-pill">ONLINE</span></div>', unsafe_allow_html=True)

        # Row 2: Master Control (switch/checkbox)
        r2_col = st.columns([2,4])
        with r2_col[0]:
            st.markdown('<div class="status-label">2. Master Control</div>', unsafe_allow_html=True)
        with r2_col[1]:
            # render a checkbox as an on/off switch; it does not change other app behavior
            master = st.checkbox(label=" ", value=st.session_state.master_control, key="master_control_checkbox")
            mc_text = "ON" if master else "OFF"
            mc_color = "#16a34a" if master else "#ef4444"
            st.markdown(
                f'<div class="status-value" style="display:inline-block;padding-left:8px;"><span style="display:inline-block;padding:6px 12px;border-radius:10px;background:{mc_color};color:#fff;font-weight:800;">{mc_text}</span></div>',
                unsafe_allow_html=True
            )
            st.session_state.master_control = master

        # Row 3: Current Time (client-side/browser) - label simplified and clock shown
        r3_col = st.columns([2,4])
        with r3_col[0]:
            st.markdown('<div class="status-label">3. Current Time</div>', unsafe_allow_html=True)
        with r3_col[1]:
            # client-side clock using JS so it shows browser time and updates every second
            clock_html = """
            <div style="display:flex; align-items:center;">
              <div id="client-clock" class="clock">--</div>
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
            components.html(clock_html, height=48)

        # Row 4: Current Location (static)
        r4_col = st.columns([2,4])
        with r4_col[0]:
            st.markdown('<div class="status-label">4. Current Location</div>', unsafe_allow_html=True)
        with r4_col[1]:
            st.markdown('<div class="status-value">Lehman Building of engineering</div>', unsafe_allow_html=True)

        # Row 5: Current Room (static)
        r5_col = st.columns([2,4])
        with r5_col[0]:
            st.markdown('<div class="status-label">5. Current Room</div>', unsafe_allow_html=True)
        with r5_col[1]:
            st.markdown('<div class="status-value">LB 172 - Robotics Research Lab</div>', unsafe_allow_html=True)

def show_usage_history():
    usage_df = st.session_state.usage_df
    st.subheader("Usage History")
    col1, col2 = st.columns([2,1])
    with col1:
        user_filter = st.selectbox("Filter by user (optional)", options=["All"] + sorted(st.session_state.users))
    with col2:
        days = st.selectbox("Last N days", options=[7, 30, 90, 365], index=0)
    cutoff = datetime.now() - timedelta(days=int(days))
    df = usage_df.copy()
    df["timestamp_dt"] = pd.to_datetime(df["timestamp"])
    df = df[df["timestamp_dt"] >= cutoff]
    if user_filter != "All":
        df = df[df["user"] == user_filter]
    st.dataframe(df.sort_values("timestamp_dt", ascending=False).reset_index(drop=True))

    st.subheader("Usage over time")
    if not df.empty:
        df_count = df.groupby([pd.Grouper(key="timestamp_dt", freq="D"), "action"]).size().reset_index(name="count")
        chart = alt.Chart(df_count).mark_line(point=True).encode(
            x="timestamp_dt:T",
            y="count:Q",
            color="action:N",
            tooltip=["timestamp_dt", "action", "count"]
        ).properties(height=300)
        st.altair_chart(chart, use_container_width=True)
    else:
        st.write("No usage events for the selected filters.")

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
