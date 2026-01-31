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
    # 1. Lineups (Look for 'PLAYER' column)
    df_l = fetch_csv(SHEET_URLS["lineups"], "PLAYER")
    
    # --- FIX FOR "x" IN DROPDOWN ---
    if not df_l.empty:
        # Find the column index of "PLAYER"
        # We assume the structure is: [Empty?, TEAM, PLAYER, TEAM, 1, 2, 3...]
        player_col_idx = -1
        for i, col in enumerate(df_l.columns):
            if str(col).strip().upper() == "PLAYER":
                player_col_idx = i
                break
        
        if player_col_idx != -1:
            # Team is 1 left of Player
            # Phases start 2 right of Player (skipping the duplicate Team col)
            idx_team = player_col_idx - 1
            idx_player = player_col_idx
            idx_phases = list(range(player_col_idx + 2, player_col_idx + 9)) # 7 phases
            
            target_indices = [idx_team, idx_player] + idx_phases
            
            # Safe slice
            try:
                df_l = df_l.iloc[:, target_indices]
                df_l.columns = ['Team', 'Player', '1', '2', '3', '4', '5', '6', '7']
            except:
                st.error("Could not parse Lineups columns automatically. Check sheet structure.")
        else:
            # Fallback if we can't find "PLAYER" header logic
            pass

    # 2. Registrations (Look for 'Profile')
    df_r = fetch_csv(SHEET_URLS["registrations"], "Profile")
    if 'Profile' in df_r.columns:
        df_r['FPL_ID'] = df_r['Profile'].apply(lambda x: int(re.search(r'entry/(\d+)', str(x)).group(1)) if re.search(r'entry/(\d+)', str(x)) else None)

    # Merge Main Data
    df_main = pd.DataFrame()
    if not df_l.empty and not df_r.empty:
        df_main = pd.merge(df_l, df_r[['Player', 'FPL_ID']], on='Player', how='left')

    # 3. Fixtures (Look for 'ShortName')
    df_fix = fetch_csv(SHEET_URLS["fixtures"], "ShortName")
    
    # 4. Chips (Look for 'Chip Played')
    df_chips = fetch_csv(SHEET_URLS["chips"], "Chip Played")
    if not df_chips.empty:
        # Normalize columns (strip spaces, remove colons)
        df_chips.columns = [c.strip().replace(':', '') for c in df_chips.columns]

    # 5. Form/Scoring (Look for 'FORM')
    df_score_raw = fetch_csv(SHEET_URLS["scoring"], "FORM")
    df_form = pd.DataFrame()
    if not df_score_raw.empty:
        cols_to_keep = ['Team'] + [str(i) for i in range(1, 39) if str(i) in df_score_raw.columns]
        if 'Team' in df_score_raw.columns:
            df_form = df_score_raw[cols_to_keep].copy()

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
    except:
        return {}, {}, 20

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

def get_opponent(team_code, gw, df_fix):
    if df_fix.empty: return None
    row = df_fix[df_fix['ShortName'] == team_code]
    if row.empty: return None
    col = f"GW{gw}"
    if col not in row.columns: return None
    return str(row[col].values[0]).upper()

# --- APP START ---

with st.spinner("Connecting to live QFPL data..."):
    df, df_form, df_fix, df_used_chips = load_data_bundle()
    fpl_elements, fpl_teams, current_gw = get_fpl_metadata()

if df.empty:
    st.error("Could not load data. Please check if the Google Sheets are published as CSV.")
    st.stop()

# Ensure we don't have empty team names or 'x'
teams_list = sorted([t for t in df['Team'].dropna().unique().tolist() if len(str(t)) > 1])

# --- NAVIGATION ---
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
            t_b = get_opponent(t_a, gw, df_fix)
            if not t_b:
                st.error("Opponent not found in fixtures.")
            else:
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
                        
                        count=0
                        total=len(active)
                        for _, r in active.iterrows():
                            count+=1
                            prog.progress(int(s + (count/total * (e-s))), f"Loading {tm}...")
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

    curr_phase = get_phase(next_gw)
    chips_used_in_phase = 0
    
    if curr_phase and not df_used_chips.empty:
        ranges = {'1':(1,5), '2':(6,10), '3':(12,16), '4':(17,21), '5':(23,27), '6':(28,32), '7':(34,38)}
        s, e = ranges[curr_phase]
        try:
            # Use 'Your QFC' or similar column for team name
            # We look for the first column
            col_team = df_used_chips.columns[0]
            col_chip = df_used_chips.columns[1]
            col_status = df_used_chips.columns[2]
            col_gw = df_used_chips.columns[3]

            t_mask = df_used_chips[col_team].astype(str).str.contains(team, case=False)
            s_mask = df_used_chips[col_status].astype(str) == 'Valid'
            c_mask = df_used_chips[col_chip] != 'Red Hot Form'
            
            sub = df_used_chips[t_mask & s_mask & c_mask].copy()
            sub['G'] = sub[col_gw].astype(str).str.extract(r'(\d+)').astype(float)
            chips_used_in_phase = len(sub[(sub['G'] >= s) & (sub['G'] <= e)])
        except: pass

    limit_hit = (chips_used_in_phase >= 2)
    
    full_team = team
    if not df_fix.empty:
        mapper = dict(zip(df_fix['ShortName'], df_fix['Team']))
        full_team = mapper.get(team, team)

    chips = [
        {"name": "Red Hot Form", "type": "form", "desc": "4 Wins in a row"},
        {"name": "Stay Humble", "type": "humble", "desc": "Play vs team you lost to"},
        {"name": "Travelling Support", "type": "std", "desc": "Standard"},
        {"name": "Fox in the Box", "type": "std", "desc": "Standard"},
        {"name": "Bought the Ref", "type": "std", "desc": "Standard"},
        {"name": "Man Mark", "type": "std", "desc": "Standard"},
        {"name": "Park the Bus", "type": "std", "desc": "Standard"}
    ]
    
    res = []
    for c in chips:
        # Check Usage
        used = False
        try:
            if not df_used_chips.empty:
                col_team = df_used_chips.columns[0]
                col_chip = df_used_chips.columns[1]
                col_status = df_used_chips.columns[2]
                
                t_mask = df_used_chips[col_team].astype(str).str.contains(team, case=False)
                c_mask = df_used_chips[col_chip] == c['name']
                s_mask = df_used_chips[col_status] == 'Valid'
                
                if not df_used_chips[t_mask & c_mask & s_mask].empty: used = True
        except: pass

        if c['name'] != "Red Hot Form" and used:
            res.append({"Chip": c['name'], "Status": "Played", "Reason": "Used once per season", "_c": "grey"})
            continue
        
        if c['name'] != "Red Hot Form" and limit_hit:
            res.append({"Chip": c['name'], "Status": "Unavailable", "Reason": f"Phase limit ({chips_used_in_phase}/2)", "_c": "red"})
            continue
            
        # Logic Checks
        stat, reason, col = "Available", "Ready", "green"
        
        if c['type'] == 'form':
            try:
                t_row = df_form[df_form['Team'] == full_team]
                if not t_row.empty:
                    last_4 = []
                    for g in range(next_gw-4, next_gw):
                        if str(g) in t_row.columns: 
                            val = str(t_row[str(g)].values[0]).upper()
                            if val in ['W','L','D']: last_4.append(val)
                    
                    if last_4 != ['W']*4:
                        stat, reason, col = "Unavailable", f"Form: {last_4}", "red"
                else:
                    stat, reason, col = "Unavailable", "Form data missing", "red"
            except: pass
            
        elif c['type'] == 'humble':
            try:
                opp = get_opponent(team, next_gw, df_fix)
                if not opp:
                    stat, reason, col = "Unavailable", "No fixture found", "red"
                else:
                    found_loss = False
                    for g in range(1, next_gw):
                        hist_opp = get_opponent(team, g, df_fix)
                        if hist_opp == opp:
                            t_row = df_form[df_form['Team'] == full_team]
                            if not t_row.empty and str(t_row[str(g)].values[0]).upper() == 'L':
                                found_loss = True; break
                    if not found_loss:
                        stat, reason, col = "Unavailable", f"Haven't lost to {opp}", "red"
            except: pass

        res.append({"Chip": c['name'], "Status": stat, "Reason": reason, "_c": col})

    rdf = pd.DataFrame(res)
    if not rdf.empty:
        st.dataframe(rdf.style.apply(lambda x: [f'background-color: {"#d1e7dd" if x["_c"]=="green" else "#f8d7da" if x["_c"]=="red" else "#e2e3e5"}; color: black']*len(x), axis=1).hide(subset=['_c'], axis='columns'), use_container_width=True, hide_index=True)
    st.link_button("🍟 Submit Chip", "https://docs.google.com/forms/d/e/1FAIpQLSeCOyvw4b7Ka2S19oBrhJd9SBnfCZM0Ycap-9Q8ng50hvKgcQ/viewform", type="primary")
