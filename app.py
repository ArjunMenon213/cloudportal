import streamlit as st
import pandas as pd
import altair as alt
from datetime import datetime, timedelta

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
    # status panel controls
    st.session_state.master_control = True  # Master control ON/OFF
    st.session_state.current_location = "Lehman Building of engineering"
    st.session_state.current_room = "LB 172 - Robotics Research Lab"

# Small styling to make the bar compact and status indicator
st.markdown(
    """
    <style>
    .small-bar {margin-top: -10px;}
    .tab-button {width:100%; padding:6px 8px; border-radius:6px;}
    .tab-active {background-color:#0f62fe;color:white;}
    .status-pill {
        display:inline-block;
        padding:6px 12px;
        border-radius:12px;
        color:white;
        font-weight:600;
    }
    .status-online { background-color: #16a34a; } /* green */
    .status-offline { background-color: #ef4444; } /* red */
    .panel-label {font-weight:600; color:#333; margin-bottom:4px;}
    .panel-row {margin-bottom:12px;}
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

# carousel-like pane (single place where content swaps)
pane = st.container()

def show_status():
    # This function renders the vertical status panel requested by the user.
    st.subheader("Status Panel")

    # Container for vertical list
    container = st.container()

    # 1. Currently Online — always show ONLINE (static, no toggles)
    with container:
        st.markdown('<div class="panel-row">', unsafe_allow_html=True)
        st.markdown('<div class="panel-label">1. Currently Online</div>', unsafe_allow_html=True)
        # Static ONLINE pill (always online)
        st.markdown(f'<div class="status-pill status-online">ONLINE</div>', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

    # 2. Master Control: ON/OFF switch (checkbox)
    with container:
        st.markdown('<div class="panel-row">', unsafe_allow_html=True)
        st.markdown('<div class="panel-label">2. Master Control</div>', unsafe_allow_html=True)
        master = st.checkbox("Master Control (ON / OFF)", value=st.session_state.master_control, key="master_control_checkbox")
        st.session_state.master_control = master
        mc_text = "ON" if st.session_state.master_control else "OFF"
        mc_class = "status-online" if st.session_state.master_control else "status-offline"
        st.markdown(f'<div style="margin-top:6px;"><span class="status-pill {mc_class}">{mc_text}</span></div>', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

    # 3. Current Time
    with container:
        st.markdown('<div class="panel-row">', unsafe_allow_html=True)
        st.markdown('<div class="panel-label">3. Current Time</div>', unsafe_allow_html=True)
        now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        st.write(now_str)
        if st.button("Refresh Time", key="refresh_time"):
            st.experimental_rerun()
        st.markdown('</div>', unsafe_allow_html=True)

    # 4. Current Location
    with container:
        st.markdown('<div class="panel-row">', unsafe_allow_html=True)
        st.markdown('<div class="panel-label">4. Current Location</div>', unsafe_allow_html=True)
        loc = st.text_input("Location", value=st.session_state.current_location, key="location_input")
        st.session_state.current_location = loc
        st.markdown('</div>', unsafe_allow_html=True)

    # 5. Current Room
    with container:
        st.markdown('<div class="panel-row">', unsafe_allow_html=True)
        st.markdown('<div class="panel-label">5. Current Room</div>', unsafe_allow_html=True)
        room = st.text_input("Room", value=st.session_state.current_room, key="room_input")
        st.session_state.current_room = room
        st.markdown('</div>', unsafe_allow_html=True)

    st.markdown("---")
    st.write("Notes:")
    st.write("- 'Currently Online' always displays ONLINE as requested.")
    st.write("- 'Master Control' checkbox acts as a global ON/OFF switch and is stored in session_state for this session.")
    st.write("- Edit Location and Room inline; values are kept in session_state for the session.")

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
            # mark as available
            idx = st.session_state.inventory_df.index[st.session_state.inventory_df["id"] == item["id"]].tolist()
            if idx:
                st.session_state.inventory_df.at[idx[0], "status"] = "available"
                st.session_state.inventory_df.at[idx[0], "last_updated"] = datetime.now().isoformat()
                # add usage event
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
        # reset status panel controls
        st.session_state.master_control = True
        st.session_state.current_location = "Lehman Building of engineering"
        st.session_state.current_room = "LB 172 - Robotics Research Lab"
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
st.caption("This is a demo streamer app. Data is stored only for the current session. For production use, connect to a database and add authentication.")
