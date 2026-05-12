"""
MLB Teams Frontend — Streamlit
Consumes the FastAPI backend at BASE_URL.
Provides full SCRUD: Search, Create, Retrieve, Update, Delete
"""

import streamlit as st
import requests
import logging

# ── Logging ───────────────────────────────────────────────────────────────────
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ── Config ────────────────────────────────────────────────────────────────────
BASE_URL = "https://mlb-api-49k1.onrender.com"

DIVISIONS = ["AL East", "AL Central", "AL West", "NL East", "NL Central", "NL West"]
LEAGUES   = ["AL", "NL"]

# ── Page setup ────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="MLB Teams Manager",
    page_icon="⚾",
    layout="wide",
)

st.title("⚾ MLB Teams Manager")
st.caption(f"Backend: `{BASE_URL}`")

# ── Helper ────────────────────────────────────────────────────────────────────
def api(method: str, path: str, **kwargs):
    """Generic API caller with error display."""
    url = BASE_URL + path
    try:
        resp = getattr(requests, method)(url, timeout=10, **kwargs)
        logger.info("%s %s → %d", method.upper(), url, resp.status_code)
        if resp.ok:
            return resp.json(), None
        return None, f"{resp.status_code}: {resp.text}"
    except requests.exceptions.ConnectionError:
        return None, "Cannot connect to backend. Is it running?"
    except Exception as exc:
        return None, str(exc)

# ── Sidebar navigation ────────────────────────────────────────────────────────
page = st.sidebar.radio(
    "Function",
    ["🔍 Search", "➕ Create", "📋 Retrieve All", "🔎 Retrieve One", "✏️ Update", "🗑️ Delete"],
)

# ══════════════════════════════════════════════════════════════════════════════
# SEARCH
# ══════════════════════════════════════════════════════════════════════════════
if page == "🔍 Search":
    st.header("Search Teams")
    st.markdown("Filter by any combination of name, division, or league.")

    col1, col2, col3 = st.columns(3)
    with col1:
        name_q = st.text_input("Team name (partial OK)", "")
    with col2:
        div_q = st.selectbox("Division", ["(any)"] + DIVISIONS)
    with col3:
        league_q = st.selectbox("League", ["(any)"] + LEAGUES)

    if st.button("Search ⚾"):
        params = {}
        if name_q:
            params["name"] = name_q
        if div_q != "(any)":
            params["division"] = div_q
        if league_q != "(any)":
            params["league"] = league_q

        data, err = api("get", "/teams/search", params=params)
        if err:
            st.error(err)
        elif not data:
            st.warning("No teams matched your search.")
        else:
            st.success(f"{len(data)} team(s) found")
            st.dataframe(data, use_container_width=True)

# ══════════════════════════════════════════════════════════════════════════════
# CREATE
# ══════════════════════════════════════════════════════════════════════════════
elif page == "➕ Create":
    st.header("Create a New Team")

    with st.form("create_form"):
        c1, c2 = st.columns(2)
        with c1:
            new_id    = st.number_input("ID (unique integer)", min_value=1, step=1, value=100)
            new_name  = st.text_input("Team name", "Monarchs")
            new_city  = st.text_input("City", "Kansas City")
            new_found = st.number_input("Founded (year)", min_value=1850, max_value=2030, value=1969)
        with c2:
            new_div   = st.selectbox("Division", DIVISIONS)
            new_lg    = st.selectbox("League", LEAGUES)
            new_champ = st.number_input("Championships", min_value=0, step=1, value=0)

        submitted = st.form_submit_button("Create Team ➕")

    if submitted:
        payload = {
            "id": int(new_id),
            "name": new_name,
            "city": new_city,
            "division": new_div,
            "league": new_lg,
            "founded": int(new_found),
            "championships": int(new_champ),
        }
        data, err = api("post", "/teams", json=payload)
        if err:
            st.error(err)
        else:
            st.success(f"✅ Created: {data['city']} {data['name']} (id={data['id']})")
            st.json(data)

# ══════════════════════════════════════════════════════════════════════════════
# RETRIEVE ALL
# ══════════════════════════════════════════════════════════════════════════════
elif page == "📋 Retrieve All":
    st.header("All Teams")
    if st.button("Load all teams"):
        data, err = api("get", "/teams")
        if err:
            st.error(err)
        else:
            st.success(f"{len(data)} teams in database")
            st.dataframe(data, use_container_width=True)

# ══════════════════════════════════════════════════════════════════════════════
# RETRIEVE ONE
# ══════════════════════════════════════════════════════════════════════════════
elif page == "🔎 Retrieve One":
    st.header("Retrieve a Single Team")
    team_id = st.number_input("Team ID", min_value=1, step=1, value=1)
    if st.button("Get Team"):
        data, err = api("get", f"/teams/{int(team_id)}")
        if err:
            st.error(err)
        else:
            st.success(f"Found: {data['city']} {data['name']}")
            col1, col2, col3 = st.columns(3)
            col1.metric("League",   data["league"])
            col2.metric("Division", data["division"])
            col3.metric("Championships", data["championships"])
            st.json(data)

# ══════════════════════════════════════════════════════════════════════════════
# UPDATE
# ══════════════════════════════════════════════════════════════════════════════
elif page == "✏️ Update":
    st.header("Update a Team")
    st.markdown("Fill in only the fields you want to change.")

    upd_id = st.number_input("Team ID to update", min_value=1, step=1, value=1)

    if st.button("Load current data"):
        data, err = api("get", f"/teams/{int(upd_id)}")
        if err:
            st.error(err)
        else:
            st.session_state["loaded"] = data

    loaded = st.session_state.get("loaded", {})

    with st.form("update_form"):
        c1, c2 = st.columns(2)
        with c1:
            u_name  = st.text_input("Name",  value=loaded.get("name", ""))
            u_city  = st.text_input("City",  value=loaded.get("city", ""))
            u_found = st.text_input("Founded (leave blank to keep)", value="")
        with c2:
            u_div = st.selectbox(
                "Division",
                ["(keep)"] + DIVISIONS,
                index=0 if not loaded else
                      (["(keep)"] + DIVISIONS).index(loaded.get("division", "(keep)"))
                      if loaded.get("division") in DIVISIONS else 0,
            )
            u_lg = st.selectbox(
                "League",
                ["(keep)"] + LEAGUES,
                index=0 if not loaded else
                      (["(keep)"] + LEAGUES).index(loaded.get("league", "(keep)"))
                      if loaded.get("league") in LEAGUES else 0,
            )
            u_champ = st.text_input("Championships (leave blank to keep)", value="")

        save = st.form_submit_button("Save Changes ✏️")

    if save:
        payload = {}
        if u_name:  payload["name"]  = u_name
        if u_city:  payload["city"]  = u_city
        if u_div  != "(keep)": payload["division"] = u_div
        if u_lg   != "(keep)": payload["league"]   = u_lg
        if u_found.strip(): payload["founded"]        = int(u_found)
        if u_champ.strip(): payload["championships"]  = int(u_champ)

        if not payload:
            st.warning("No fields to update.")
        else:
            data, err = api("put", f"/teams/{int(upd_id)}", json=payload)
            if err:
                st.error(err)
            else:
                st.success("✅ Updated successfully")
                st.json(data)

# ══════════════════════════════════════════════════════════════════════════════
# DELETE
# ══════════════════════════════════════════════════════════════════════════════
elif page == "🗑️ Delete":
    st.header("Delete a Team")
    del_id = st.number_input("Team ID to delete", min_value=1, step=1, value=1)

    if st.button("Preview team"):
        data, err = api("get", f"/teams/{int(del_id)}")
        if err:
            st.error(err)
        else:
            st.info(f"You are about to delete: **{data['city']} {data['name']}**")
            st.session_state["del_preview"] = data

    if st.session_state.get("del_preview"):
        st.warning(f"⚠️ This cannot be undone!")
        if st.button("Confirm Delete 🗑️", type="primary"):
            data, err = api("delete", f"/teams/{int(del_id)}")
            if err:
                st.error(err)
            else:
                st.success(data["message"])
                st.session_state.pop("del_preview", None)
