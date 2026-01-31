import streamlit as st
import pandas as pd
import requests
import re
import io

# --- PAGE CONFIG ---
st.set_page_config(
    page_title="QFPL Hub",
    page_icon="⚽",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ==========================================
# 1. LIVE DATA LINKS
# ==========================================
SHEET_URLS = {
    "lineups": "https://docs.google.com/spreadsheets/d/e/2PACX-1vSW-bUC-2pv_0v0zVGMEkvecItvGWF1tCiOdy-abcLT8i0Ea7YCAofFzZ6cvUQfvbb1HGNyu1YV3hrM/pub?gid=1076160662&single=true&output=csv",
    "registrations": "https://docs.google.com/spreadsheets/d/e/2PACX-1vTUnKgVpZJYBQMbcC0L1sQgRkf5osqet6w41iknV_YfJmocVqaiwcX0PfPkDHd4JNqj77Ki1-p1l6jJ/pub?gid=950411350&single=true&output=csv",
    "scoring": "https://docs.google.com/spreadsheets/d/e/2PACX-1vRVV6_32cFdtqjEMj59Z-7UNjtFpJCu_dETfIvyP56IREQM7vr6hV9qUMBAE3CbJNUqm6Wb8PM8eWRH/pub?gid=0&single=true&output=csv",
    "fixtures": "https://docs.google.com/spreadsheets/d/e/2PACX-1vTpIC9NUmE1uXx7_s_xr2to81xNi5UYNOq_fPNY7N5WEdUmbfZYwRvxtsw7zbeQlE_q05qYgwQ50ua_/pub?gid=0&single=true&output=csv",
    "chips": "https://docs.google.com/spreadsheets/d/e/2PACX-1vS7LIgpfq7K-bb_1I7ZTf8XaKlaFclQq49IVHiBMqIpfwiQfiS5bk0B6lQcRwAijf6ZyvLOC1Vp3VfH/pub?gid=805641470&single=true&output=csv"
}

# --- DATA LOADING FUNCTIONS ---

@st.cache_data(ttl=600)
def fetch_csv(url, key_col=None):
    """Fetches CSV data and automatically finds the header row."""
    try:
        response = requests.get(url)
        response.raise_for_status()
        content = response.content.decode('utf-8')
        
        # 1. Try reading normally
        df = pd.read_csv(io.StringIO(content))
        
        # 2. Smart Header Search
        if key_col:
            # Normalize cols to lowercase for search
            cols_lower = [str(c).lower() for c in df.columns]
            if key_col.lower() not in cols_lower:
                lines = content.splitlines()
                # Check first 50 lines for the key column
                for i, line in enumerate(lines[:50]): 
                    if key_col.lower() in line.lower():
                        df = pd.read_csv(io.StringIO(content), header=i)
                        break
        return df
    except Exception as e:
        st.error(f"Error reading sheet: {e}")
        return pd.DataFrame()

@st.cache_data(ttl=600)
def load_data_bundle():
    # 1. Lineups
    df_l = fetch_csv(SHEET_URLS["lineups"], "PLAYER")
    if not df_l.empty:
        # Parse Lineups Columns
        p_idx = -1
        for i, c in enumerate(df_l.columns):
            if str(c).strip().upper() == "PLAYER":
                p_idx = i; break
        
        if p_idx != -1:
            try:
                indices = [p_idx-1, p_idx] + list(range(p_idx+2, p_idx+9))
                df_l = df_l.iloc[:, indices]
                df_l.columns = ['Team', 'Player', '1', '2', '3', '4', '5', '6', '7']
            except: pass

    # 2. Registrations
    df_r = fetch_csv(SHEET_URLS["registrations"], "Profile")
    if 'Profile' in df_r.columns:
        df_r['FPL_ID'] = df_r['Profile'].apply(lambda x: int(re.search(r'entry/(\d+)', str(x)).group(1)) if re.search(r'entry/(\d+)', str(x)) else None)

    df_main = pd.DataFrame()
    if not df_l.empty and not df_r.empty:
        df_main = pd.merge(df_l, df_r[['Player', 'FPL_ID']], on='Player', how='left')

    # 3. Chips & Fixtures
    df_fix = fetch_csv(SHEET_URLS["fixtures"], "ShortName")
    
    df_chips = fetch_csv(SHEET_URLS["chips"], "Chip Played")
    if not df_chips.empty:
        # Standardize Chip Columns
        df_chips.columns = [c.strip().replace(':', '') for c in df_chips.columns]
        
        cols = df_chips.columns
        c_team = next((c for c in cols if "QFC" in c or "Team" in c), None)
        c_gw = next((c for c in cols if "GW" in c or "Gameweek" in c), None)
        
        if c_team:
            # Clean Team Name: "Fulham QFC" -> "Fulham"
            df_chips['CleanTeam'] = df_chips[c_team].astype(str).str.replace(' QFC', '', regex=False).str.strip()
        
        if c_gw:
            # Clean GW: "GW06" -> 6
            df_chips['GW_Int'] = df_chips[c_gw].astype(str).str.extract(r'(\d+)').astype(float)

    # 4. Form (ROBUST LOADING)
    # The 'FORM' table is tricky. We read the raw text and find the exact row 
    # that has "Team", "1", and "2" to identify the real header.
    df_form = pd.DataFrame(columns=['Team']) # Init with Team column to prevent KeyError
    try:
        response = requests.get(SHEET_URLS["scoring"])
        response.raise_for_status()
        content = response.content.decode('utf-8')
        
        lines = content.splitlines()
        header_row = None
        for i, line in enumerate(lines):
            # Look for the row containing "Team" and Gameweek numbers
            if "Team" in line and ",1," in line and ",2," in line:
                header_row = i
                break
        
        if header_row is not None:
            df_score = pd.read_csv(io.StringIO(content), header=header_row)
            if 'Team' in df_score.columns:
                cols = ['Team'] + [str(i) for i in range(1, 39) if str(i) in df_score.columns]
                df_form = df_score[cols].copy()
    except:
        pass

    return df_main, df_form, df_fix, df_chips

# API Helpers
@st.cache_data(ttl=300)
def get_fpl_metadata():
    try:
        r = requests.get("https://fantasy.premierleague.com/api/bootstrap-static/", timeout=3)
        if r.status_code != 200: return {}, {}, 20
        data = r.json()
        elements = {p['id']: {'name': p['web_name'], 'team_id': p['team']} for p in data['elements']}
        teams = {t['id']: t['short_name'] for t in data['teams']}
        curr_gw = 38
        for e in data['events']:
            if e['is_current']: curr_gw = e['id']; break
            elif e['is_next']: curr_gw = max(1, e['id'] - 1); break
        return elements, teams, curr_gw
    except: return {}, {}, 20

def get_picks(fpl_id, gw):
    if not fpl_id: return []
    try:
        r = requests.get(f"https://fantasy.premierleague.com/api/entry/{int(fpl_id)}/event/{gw}/picks/", timeout=3)
        return [p['element'] for p in r.json()['picks']] if r.status_code == 200 else []
    except: return []

# Logic Helpers
def get_phase(gw):
    if 1 <= gw <= 5: return '1'
    if 6 <= gw <= 10: return '2'
    if 12 <= gw <= 16: return '3'
    if 17 <= gw <= 21: return '4'
    if 23 <= gw <= 27: return '5'
    if 28 <= gw <= 32: return '6'
    if 34 <= gw <= 38: return '7'
    return None

def get_fixture_raw(team_code, gw, df_fix):
    if df_fix.empty: return None
    row = df_fix[df_fix['ShortName'] == team_code]
    if row.empty: return None
    col = f"GW{gw}"
    if col not in row.columns: return None
    return str(row[col].values[0]) # Returns raw string (e.g. 'che' or 'CHE')

# --- APP START ---

with st.spinner("Connecting to live QFPL data..."):
    df, df_form, df_fix, df_used_chips = load_data_bundle()
    fpl_elements, fpl_teams, current_gw = get_fpl_metadata()

if df.empty:
    st.error("Data load failed. Please check the Google Sheet Links.")
    st.stop()

teams_list = sorted([t for t in df['Team'].dropna().unique().tolist() if len(str(t)) > 1])

if 'page' not in st.session_state: st.session_state.page = 'home'
def go(p): st.session_state.page = p

# ==========================================
# PAGE: HOME
# ==========================================
if st.session_state.page == 'home':
    st.title("🏆 QFPL Hub")
    st.caption(f"Live Data Connected | Current Real FPL GW: {current_gw}")
    st.divider()
    
    c1, c2, c3 = st.columns(3)
    with c1:
        st.info("📊 **Differentials**")
        st.button("Calculator", on_click=go, args=('diff',), use_container_width=True)
    with c2:
        st.info("📋 **Lineups**")
        st.button("Lineup Helper", on_click=go, args=('help',), use_container_width=True)
    with c3:
        st.info("🍟 **Chips**")
        st.button("Chip Helper", on_click=go, args=('chip',), use_container_width=True)

# ==========================================
# PAGE: DIFFERENTIALS
# ==========================================
elif st.session_state.page == 'diff':
    st.button("← Back", on_click=go, args=('home',))
    st.header("📊 Differential Calculator")
    
    c1, c2 = st.columns(2)
    with c1: t_a = st.selectbox("Your Team", teams_list)
    with c2: gw = st.number_input("Gameweek", 1, 38, current_gw)

    if st.button("Calculate", type="primary"):
        phase = get_phase(gw)
        if not phase:
            st.error(f"GW{gw} is not in a QFPL Phase.")
        else:
            raw_opp = get_fixture_raw(t_a, gw, df_fix)
            if not raw_opp:
                st.error("Opponent not found in fixtures.")
            else:
                t_b = raw_opp.upper()
                fetch_gw = min(gw, current_gw)
                
                st.markdown(f"**Matchup:** {t_a} vs {t_b} (Phase {phase})")
                if gw > current_gw: st.caption(f"Using squads from GW{fetch_gw}")

                if phase not in df.columns or df[phase].isnull().all():
                    st.error(f"Lineups for Phase {phase} unavailable.")
                else:
                    prog = st.progress(0, "Fetching...")
                    def get_h(tm, s, e):
                        h = {}
                        team_rows = df[df['Team'] == tm]
                        active = team_rows[team_rows[phase].astype(str).str.upper().isin(['S','C'])]
                        total = len(active)
                        count = 0
                        for i, (_, r) in enumerate(active.iterrows()):
                            count+=1
                            if total > 0: prog.progress(int(s + ((count)/total * (e-s))), f"Loading {tm}...")
                            mul = 2 if str(r[phase]).upper() == 'C' else 1
                            for p in get_picks(r['FPL_ID'], fetch_gw): h[p] = h.get(p, 0) + mul
                        return h

                    ha = get_h(t_a, 0, 50)
                    hb = get_h(t_b, 50, 100)
                    prog.empty()

                    res = []
                    for pid in set(ha) | set(hb):
                        net = ha.get(pid,0) - hb.get(pid,0)
                        if net != 0:
                            p = fpl_elements.get(pid, {'name': 'Unknown'})
                            p_tm = fpl_teams.get(p.get('team_id'), '-')
                            res.append({'Player': p['name'], 'Team': p_tm, f'{t_a}': ha.get(pid,0), f'{t_b}': hb.get(pid,0), 'Net': net})
                    
                    if not res: st.success("Teams are flat!")
                    else:
                        rdf = pd.DataFrame(res).sort_values(by='Net', key=abs, ascending=False)
                        st.dataframe(rdf.style.map(lambda v: f'background-color: {"#d1e7dd" if v>0 else "#f8d7da" if v<0 else ""}; color: black', subset=['Net']), use_container_width=True, hide_index=True)

# ==========================================
# PAGE: LINEUP HELPER
# ==========================================
elif st.session_state.page == 'help':
    st.button("← Back", on_click=go, args=('home',))
    st.header("📋 Lineup Helper")
    
    c1, c2 = st.columns(2)
    with c1: my_team = st.selectbox("Team", teams_list)
    with c2: n_ph = st.selectbox("Submission Phase", [4, 5, 6, 7])

    data = []
    team_rows = df[df['Team'] == my_team]
    
    for _, r in team_rows.iterrows():
        p1, p2 = str(n_ph - 1), str(n_ph - 2)
        must = False
        if p1 in df.columns and p2 in df.columns:
            if str(r[p1]).upper() == 'B' and str(r[p2]).upper() == 'B': must = True
        
        used_cap = False
        for i in range(1, n_ph):
            if str(i) in df.columns and str(r[str(i)]).upper() == 'C': used_cap = True
        
        data.append({
            "Player": r['Player'],
            "Bench Status": "MUST START" if must else "OK",
            "Captaincy": "Used" if used_cap else "Available",
            "_sort": 0 if must else 1
        })
    
    if data:
        df_out = pd.DataFrame(data).sort_values(by=['_sort', 'Player'])
        if any(df_out['_sort']==0): st.error("🚨 Must Start violations found!")
        
        st.dataframe(
            df_out.style.apply(lambda x: ['background-color: #f8d7da; font-weight: bold']*len(x) if x['_sort']==0 else ['background-color: #fff3cd']*len(x) if x['Captaincy']=="Used" else ['']*len(x), axis=1).hide(subset=['_sort'], axis='columns'),
            use_container_width=True, hide_index=True
        )
    st.link_button("🚀 Submit", "https://docs.google.com/forms/d/e/1FAIpQLSfIPWcBe5LpLmI8dq5Jqxvw2ug9_9d2Ha9RIyREMEiBbNmyzQ/viewform", type="primary")

# ==========================================
# PAGE: CHIP HELPER
# ==========================================
elif st.session_state.page == 'chip':
    st.button("← Back", on_click=go, args=('home',))
    st.header("🍟 Chip Helper")
    
    c1, c2 = st.columns(2)
    with c1: team = st.selectbox("Team", teams_list)
    with c2: next_gw = st.number_input("Upcoming Gameweek", 1, 38, current_gw+1)

    # 1. Identify Columns
    cols = df_used_chips.columns
    c_chip = next((c for c in cols if "Chip" in c), None)
    c_status = next((c for c in cols if "Status" in c), None)
    
    # 2. Phase Limits
    curr_phase = get_phase(next_gw)
    chips_used_in_phase = 0
    if curr_phase and not df_used_chips.empty:
        ranges = {'1':(1,5), '2':(6,10), '3':(12,16), '4':(17,21), '5':(23,27), '6':(28,32), '7':(34,38)}
        s, e = ranges[curr_phase]
        try:
            team_chips = df_used_chips[
                (df_used_chips['CleanTeam'].str.contains(team, case=False)) & 
                (df_used_chips[c_status] == 'Valid') & 
                (df_used_chips[c_chip] != 'Red Hot Form')
            ].copy()
            phase_count = len(team_chips[(team_chips['GW_Int'] >= s) & (team_chips['GW_Int'] <= e)])
            chips_used_in_phase = phase_count
        except: pass

    phase_limit_reached = (chips_used_in_phase >= 2)
    
    # 3. Full Team Name Logic
    full_team = team
    if not df_fix.empty:
        mapper = dict(zip(df_fix['ShortName'], df_fix['Team']))
        full_team = mapper.get(team, team)

    # 4. Chip Analysis
    chips_list = ["Red Hot Form", "Stay Humble", "Travelling Support", "Fox in the Box", "Bought the Ref", "Man Mark", "Park the Bus"]
    res = []
    
    for c_name in chips_list:
        is_rhf = (c_name == "Red Hot Form")
        
        # A. Check Usage
        used = False
        last_rhf_gw = 0
        try:
            matches = df_used_chips[
                (df_used_chips['CleanTeam'].str.contains(team, case=False)) & 
                (df_used_chips[c_chip] == c_name) & 
                (df_used_chips[c_status] == 'Valid')
            ]
            if not matches.empty:
                used = True
                if is_rhf: last_rhf_gw = matches['GW_Int'].max()
        except: pass

        avail = "Yes"
        can_play = "Yes"
        comment = "Ready to play."
        color = "green"

        # Rule 1: Lifetime (Except RHF)
        if not is_rhf and used:
            res.append({"Chip Name": c_name, "Availability": "No", "Can be Played?": "No", "Comments": "Already played.", "_c": "grey"})
            continue
        
        # Rule 2: Phase Limit (Except RHF)
        elif not is_rhf and phase_limit_reached:
            res.append({"Chip Name": c_name, "Availability": "Yes", "Can be Played?": "No", "Comments": f"Phase limit ({chips_used_in_phase}/2 used).", "_c": "red"})
            continue

        # Rule 3: Specific Logic
        if is_rhf:
            gap = next_gw - last_rhf_gw
            if gap <= 4:
                avail = "No"; can_play = "No"; comment = f"Played in GW{int(last_rhf_gw)}. Reset gap {gap}/5."; color = "red"
            else:
                try:
                    if df_form.empty: raise ValueError("Empty")
                    t_row = df_form[df_form['Team'] == full_team]
                    if not t_row.empty:
                        last_4 = []
                        for g in range(next_gw-4, next_gw):
                            if str(g) in t_row.columns:
                                val = str(t_row[str(g)].values[0]).upper()
                                if val in ['W','L','D']: last_4.append(val)
                        if last_4 != ['W']*4:
                            can_play = "No"; comment = f"Need 4 Wins. Form: {last_4}"; color = "red"
                    else:
                        can_play = "No"; comment = "Form data missing."; color = "red"
                except:
                    can_play = "No"; comment = "Form data unavailable."; color = "red"

        elif c_name == "Stay Humble":
            try:
                raw_opp = get_fixture_raw(team, next_gw, df_fix)
                if not raw_opp:
                    can_play = "No"; comment = "No fixture."; color = "red"
                else:
                    opp_code = raw_opp.upper()
                    found_loss = False
                    for g in range(1, next_gw):
                        hist_raw = get_fixture_raw(team, g, df_fix)
                        if hist_raw and hist_raw.upper() == opp_code:
                            t_row = df_form[df_form['Team'] == full_team]
                            if not t_row.empty and str(t_row[str(g)].values[0]).upper() == 'L':
                                found_loss = True; break
                    if not found_loss:
                        can_play = "No"; comment = f"Must play vs team you lost to (vs {opp_code})."; color = "red"
            except: pass
        
        elif c_name == "Travelling Support":
            # Must be Away (lowercase in fixtures)
            raw_fix = get_fixture_raw(team, next_gw, df_fix)
            if raw_fix and raw_fix.isupper():
                can_play = "No"; comment = f"Home game vs {raw_fix}. Must be Away."; color = "red"

        res.append({"Chip Name": c_name, "Availability": avail, "Can be Played?": can_play, "Comments": comment, "_c": color})

    rdf = pd.DataFrame(res)
    st.dataframe(
        rdf.style.apply(lambda x: [f'background-color: {"#d1e7dd" if x["_c"]=="green" else "#f8d7da" if x["_c"]=="red" else "#e2e3e5"}; color: black']*len(x), axis=1)
        .hide(subset=['_c'], axis='columns'),
        use_container_width=True, hide_index=True
    )
    
    st.divider()
    st.link_button("🍟 Submit Chip", "https://docs.google.com/forms/d/e/1FAIpQLSeCOyvw4b7Ka2S19oBrhJd9SBnfCZM0Ycap-9Q8ng50hvKgcQ/viewform", type="primary")
