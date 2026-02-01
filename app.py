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
    "chips": "https://docs.google.com/spreadsheets/d/e/2PACX-1vS7LIgpfq7K-bb_1I7ZTf8XaKlaFclQq49IVHiBMqIpfwiQfiS5bk0B6lQcRwAijf6ZyvLOC1Vp3VfH/pub?gid=805641470&single=true&output=csv",
    "dashboard": "https://docs.google.com/spreadsheets/d/e/2PACX-1vQMx7WNVySFfJuAjKyc5PvPnL5XAz9FzLbIXFL5qjqwt4_YCJmuNax_jMsfxnRXoekHKQzFmYUu5YEM/pub?gid=0&single=true&output=csv"
}

# --- DATA LOADING FUNCTIONS ---

@st.cache_data(ttl=600)
def fetch_csv(url, key_col=None):
    try:
        response = requests.get(url)
        response.raise_for_status()
        content = response.content.decode('utf-8')
        df = pd.read_csv(io.StringIO(content))
        
        if key_col:
            cols_lower = [str(c).lower() for c in df.columns]
            if key_col.lower() not in cols_lower:
                lines = content.splitlines()
                for i, line in enumerate(lines[:50]): 
                    if key_col.lower() in line.lower():
                        df = pd.read_csv(io.StringIO(content), header=i)
                        break
        return df
    except Exception as e:
        return pd.DataFrame()

@st.cache_data(ttl=600)
def load_data_bundle():
    # 1. Lineups
    df_l = fetch_csv(SHEET_URLS["lineups"], "PLAYER")
    if not df_l.empty:
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

    # 3. Chips Data
    df_fix = fetch_csv(SHEET_URLS["fixtures"], "ShortName")
    df_chips = fetch_csv(SHEET_URLS["chips"], "Chip Played")
    if not df_chips.empty:
        df_chips.columns = [c.strip().replace(':', '') for c in df_chips.columns]
        
        cols = df_chips.columns
        c_team = next((c for c in cols if "QFC" in c or "Team" in c), None)
        c_gw = next((c for c in cols if "GW" in c or "Gameweek" in c), None)
        c_stat = next((c for c in cols if "Status" in c), None)
        
        if c_team:
            df_chips['CleanTeam'] = df_chips[c_team].astype(str).str.replace(' QFC', '', regex=False).str.strip()
        if c_gw:
            df_chips['GW_Int'] = df_chips[c_gw].astype(str).str.extract(r'(\d+)').astype(float)

    # 4. Form (Scoring)
    # The 'FORM' table is tricky. We search for the specific header row.
    df_form = pd.DataFrame()
    try:
        response = requests.get(SHEET_URLS["scoring"])
        content = response.content.decode('utf-8')
        lines = content.splitlines()
        header_row = None
        for i, line in enumerate(lines):
            # Look for row with "Team", "1", "2"
            if "Team" in line and ",1," in line and ",2," in line:
                header_row = i; break
        
        if header_row is not None:
            df_score = pd.read_csv(io.StringIO(content), header=header_row)
            cols = ['Team'] + [str(i) for i in range(1, 39) if str(i) in df_score.columns]
            if 'Team' in df_score.columns:
                df_form = df_score[cols].copy()
    except: pass

    # 5. Dashboard
    df_dash = fetch_csv(SHEET_URLS["dashboard"], "Team")

    return df_main, df_form, df_fix, df_chips, df_dash

# API Helpers
@st.cache_data(ttl=300)
def get_fpl_metadata():
    try:
        r = requests.get("https://fantasy.premierleague.com/api/bootstrap-static/", timeout=3)
        if r.status_code != 200: return {}, {}, 20
        d = r.json()
        elements = {p['id']: {'name': p['web_name'], 'team_id': p['team']} for p in d['elements']}
        teams = {t['id']: t['short_name'] for t in d['teams']}
        curr = 38
        for e in d['events']:
            if e['is_current']: curr = e['id']; break
            elif e['is_next']: curr = max(1, e['id'] - 1); break
        return elements, teams, curr
    except: return {}, {}, 20

def get_picks(fpl_id, gw):
    if not fpl_id: return []
    try:
        r = requests.get(f"https://fantasy.premierleague.com/api/entry/{int(fpl_id)}/event/{gw}/picks/", timeout=3)
        return [p['element'] for p in r.json()['picks']] if r.status_code == 200 else []
    except: return []

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
    return str(row[col].values[0])

# --- APP START ---

with st.spinner("Loading QFPL data..."):
    df, df_form, df_fix, df_used_chips, df_dashboard = load_data_bundle()
    fpl_elements, fpl_teams, current_gw = get_fpl_metadata()

if df.empty:
    st.error("Critical Data Missing. Check 'lineups' link.")
    st.stop()

teams_list = sorted([t for t in df['Team'].dropna().unique().tolist() if len(str(t)) > 1])

# Navigation
if 'page' not in st.session_state: st.session_state.page = 'home'
def go(p): st.session_state.page = p

# ==========================================
# PAGE: HOME
# ==========================================
if st.session_state.page == 'home':
    st.title("🏆 QFPL Hub")
    st.caption(f"Current FPL Gameweek: {current_gw}")
    st.divider()
    
    c1, c2, c3 = st.columns(3)
    with c1:
        st.info("📊 **Live Scores**")
        st.button("Dashboard", on_click=go, args=('scores',), use_container_width=True)
        st.write("")
        st.info("⚡ **Differentials**")
        st.button("Diff Calculator", on_click=go, args=('diff',), use_container_width=True)
    with c2:
        st.info("📋 **Lineups**")
        st.button("Lineup Helper", on_click=go, args=('help',), use_container_width=True)
    with c3:
        st.info("🍟 **Chips**")
        st.button("Chip Helper", on_click=go, args=('chip',), use_container_width=True)

# ==========================================
# PAGE: LIVE SCORES
# ==========================================
elif st.session_state.page == 'scores':
    st.button("← Back", on_click=go, args=('home',))
    st.header("📊 Live Scores")
    
    if df_dashboard.empty:
        st.warning("Dashboard data unavailable.")
    else:
        df_dash = df_dashboard.dropna(axis=1, how='all').dropna(axis=0, how='all')
        hl_team = st.selectbox("Highlight Team", ["None"] + teams_list)
        
        def highlight_team(row):
            if hl_team != "None" and row.astype(str).str.contains(hl_team, case=False).any():
                return ['color: #09AB3B; font-weight: bold'] * len(row)
            return [''] * len(row)
        
        st.dataframe(df_dash.style.apply(highlight_team, axis=1), use_container_width=True, hide_index=True)

# ==========================================
# PAGE: DIFFERENTIALS
# ==========================================
elif st.session_state.page == 'diff':
    st.button("← Back", on_click=go, args=('home',))
    st.header("⚡ Differential Calculator")
    
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
                st.markdown(f"**{t_a} vs {t_b}** (Phase {phase})")
                
                if phase not in df.columns or df[phase].isnull().all():
                    st.error(f"Lineups for Phase {phase} unavailable.")
                else:
                    prog = st.progress(0, "Fetching...")
                    def get_h(tm):
                        h = {}
                        active = df[(df['Team'] == tm) & (df[phase].astype(str).str.upper().isin(['S','C']))]
                        total = len(active)
                        count = 0
                        for i, (_, r) in enumerate(active.iterrows()):
                            count+=1
                            if total > 0: prog.progress(int((count)/total * 50), f"Loading {tm}...")
                            mul = 2 if str(r[phase]).upper() == 'C' else 1
                            for p in get_picks(r['FPL_ID'], fetch_gw): h[p] = h.get(p, 0) + mul
                        return h

                    ha = get_h(t_a)
                    hb = get_h(t_b)
                    prog.empty()

                    res = []
                    for pid in set(ha) | set(hb):
                        net = ha.get(pid,0) - hb.get(pid,0)
                        if net != 0:
                            p = fpl_elements.get(pid, {'name': 'Unknown'})
                            pt = fpl_teams.get(p.get('team_id'), '-')
                            res.append({'Player': p['name'], 'Team': pt, f'{t_a}': ha.get(pid,0), f'{t_b}': hb.get(pid,0), 'Net': net})
                    
                    if not res: st.success("Teams are flat!")
                    else:
                        rdf = pd.DataFrame(res).sort_values(by='Net', key=abs, ascending=False)
                        def style_net(val):
                            if val > 0: return 'color: #09AB3B; font-weight: bold'
                            if val < 0: return 'color: #FF4B4B; font-weight: bold'
                            return ''
                        st.dataframe(rdf.style.map(style_net, subset=['Net']).hide(axis='index'), use_container_width=True)

# ==========================================
# PAGE: LINEUP HELPER
# ==========================================
elif st.session_state.page == 'help':
    st.button("← Back", on_click=go, args=('home',))
    st.header("📋 Lineup Helper")
    
    c1, c2 = st.columns(2)
    with c1: my_team = st.selectbox("Team", teams_list)
    with c2: n_ph = st.selectbox("Submission Phase", [4, 5, 6, 7])

    if st.button("Analyze", type="primary"):
        data = []
        team_rows = df[df['Team'] == my_team]
        
        # Calculate Remaining Phases (Current Submission + Future)
        # Total Phases = 7. 
        # If submitting for Phase 5, phases 5, 6, 7 are available (3 left).
        phases_remaining = 8 - n_ph
        
        for _, r in team_rows.iterrows():
            # 1. Bench Streak
            p1, p2 = str(n_ph - 1), str(n_ph - 2)
            must = False
            if p1 in df.columns and p2 in df.columns:
                if str(r[p1]).upper() == 'B' and str(r[p2]).upper() == 'B': must = True
            
            # 2. Captaincy Check
            used_cap = False
            for i in range(1, n_ph):
                if str(i) in df.columns and str(r[str(i)]).upper() == 'C': used_cap = True
            
            # 3. Mandatory Selections (Quota of 3 starts total)
            past_starts = 0
            for i in range(1, n_ph):
                if str(i) in df.columns and str(r[str(i)]).upper() in ['S', 'C']:
                    past_starts += 1
            
            starts_needed = max(0, 3 - past_starts)
            
            # Status Logic
            quota_status = f"Need {starts_needed} more"
            is_critical_quota = False
            
            if starts_needed == 0:
                quota_status = "Quota Met ✅"
            elif starts_needed > phases_remaining:
                quota_status = f"IMPOSSIBLE 🚨 ({starts_needed} needed in {phases_remaining} left)"
                is_critical_quota = True
            elif starts_needed == phases_remaining:
                quota_status = f"MUST SELECT ⚠️ (Need {starts_needed}/{phases_remaining})"
                is_critical_quota = True
                
            data.append({
                "Player": r['Player'],
                "Bench Status": "MUST START" if must else "OK",
                "Captaincy": "Used" if used_cap else "Available",
                "Min Selections": quota_status,
                "_sort": 0 if must or is_critical_quota else 1
            })
        
        df_out = pd.DataFrame(data).sort_values(by=['_sort', 'Player'])
        if any(df_out['_sort']==0): st.error("🚨 Must Start violations found!")
        
        def style_lineup(row):
            styles = []
            for col in row.index:
                txt = str(row[col])
                if "MUST" in txt or "IMPOSSIBLE" in txt:
                    styles.append('color: #FF4B4B; font-weight: bold')
                elif "Used" in txt:
                    styles.append('color: #FFA500; font-weight: bold')
                elif "Quota Met" in txt:
                    styles.append('color: #09AB3B')
                else:
                    styles.append('')
            return styles

        st.dataframe(
            df_out.style.apply(style_lineup, axis=1).hide(subset=['_sort'], axis='columns'),
            use_container_width=True, hide_index=True
        )
        st.link_button("🚀 Submit", "https://docs.google.com/forms/d/e/1FAIpQLSfIPWcBe5LpLmI8dq5Jqxvw2ug9_9d2Ha9RIyREMEiBbNmyzQ/viewform")

# ==========================================
# PAGE: CHIP HELPER
# ==========================================
elif st.session_state.page == 'chip':
    st.button("← Back", on_click=go, args=('home',))
    st.header("🍟 Chip Helper")
    
    c1, c2 = st.columns(2)
    with c1: team = st.selectbox("Team", teams_list)
    with c2: next_gw = st.number_input("Upcoming Gameweek", 1, 38, current_gw+1)

    if st.button("Check Eligibility", type="primary"):
        cols = df_used_chips.columns
        c_chip = next((c for c in cols if "Chip" in c), None)
        c_status = next((c for c in cols if "Status" in c), None)
        
        # Phase Limits
        curr_phase = get_phase(next_gw)
        chips_used_in_phase = 0
        if curr_phase and not df_used_chips.empty:
            ranges = {'1':(1,5), '2':(6,10), '3':(12,16), '4':(17,21), '5':(23,27), '6':(28,32), '7':(34,38)}
            s, e = ranges[curr_phase]
            try:
                t_mask = df_used_chips['CleanTeam'].str.contains(team, case=False)
                s_mask = df_used_chips[c_status] == 'Valid'
                c_mask = df_used_chips[c_chip] != 'Red Hot Form'
                
                sub = df_used_chips[t_mask & s_mask & c_mask].copy()
                chips_used_in_phase = len(sub[(sub['GW_Int'] >= s) & (sub['GW_Int'] <= e)])
            except: pass

        phase_limit_reached = (chips_used_in_phase >= 2)
        
        full_team = team
        if not df_fix.empty:
            mapper = dict(zip(df_fix['ShortName'], df_fix['Team']))
            full_team = mapper.get(team, team)

        chips_list = ["Red Hot Form", "Stay Humble", "Travelling Support", "Fox in the Box", "Bought the Ref", "Man Mark", "Park the Bus"]
        res = []
        
        for c_name in chips_list:
            is_rhf = (c_name == "Red Hot Form")
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
            comment = "Ready."
            color = "green"

            # 1. Usage
            if not is_rhf and used:
                res.append({"Chip Name": c_name, "Availability": "No", "Can be Played?": "No", "Comments": "Already played.", "_c": "grey"})
                continue
            
            if not is_rhf and phase_limit_reached:
                res.append({"Chip Name": c_name, "Availability": "Yes", "Can be Played?": "No", "Comments": f"Phase limit ({chips_used_in_phase}/2 used).", "_c": "red"})
                continue

            # 2. RHF Logic
            if is_rhf:
                gap = next_gw - last_rhf_gw
                if gap <= 4:
                    avail = "No"; can_play = "No"; comment = f"Played in GW{int(last_rhf_gw)}. Reset gap {gap}/5."; color = "red"
                else:
                    try:
                        t_row = df_form[df_form['Team'] == full_team]
                        if not t_row.empty:
                            last_4 = []
                            for g in range(next_gw-4, next_gw):
                                if str(g) in t_row.columns:
                                    val = str(t_row[str(g)].values[0]).upper()
                                    if val in ['W','L','D']: last_4.append(val)
                            
                            # Streak Check
                            if last_4 != ['W']*4:
                                can_play = "No"; comment = f"Form: {last_4} (Need 4 Wins)"; color = "red"
                        else:
                            can_play = "No"; comment = "Form unavailable."; color = "red"
                    except: pass

            # 3. Stay Humble
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
            
            # 4. Travelling Support
            elif c_name == "Travelling Support":
                raw_fix = get_fixture_raw(team, next_gw, df_fix)
                if raw_fix and raw_fix.isupper():
                    can_play = "No"; comment = f"Home game vs {raw_fix}. Must be Away."; color = "red"

            res.append({"Chip Name": c_name, "Availability": avail, "Can be Played?": can_play, "Comments": comment, "_c": color})

        rdf = pd.DataFrame(res)
        
        def style_chip_row(row):
            c = row['_c']
            color_css = ''
            if c == 'green': color_css = 'color: #09AB3B; font-weight: bold'
            elif c == 'red': color_css = 'color: #FF4B4B; font-weight: bold'
            elif c == 'grey': color_css = 'color: #808495'
            return [color_css] * len(row)

        st.dataframe(
            rdf.style.apply(style_chip_row, axis=1).hide(subset=['_c'], axis='columns'),
            use_container_width=True, hide_index=True
        )
    st.divider()
    st.link_button("🍟 Submit Chip", "https://docs.google.com/forms/d/e/1FAIpQLSeCOyvw4b7Ka2S19oBrhJd9SBnfCZM0Ycap-9Q8ng50hvKgcQ/viewform")
