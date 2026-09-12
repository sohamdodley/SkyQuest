"""SkyQuest — 10-stage cadet game. South Asia + Europe. Dual-view flights."""

from __future__ import annotations

import json
from pathlib import Path

import plotly.graph_objects as go
from plotly.subplots import make_subplots
import streamlit as st

ROOT = Path(__file__).parent
DATA = ROOT / "data"

st.set_page_config(
    page_title="SkyQuest",
    page_icon="✈",
    layout="wide",
    initial_sidebar_state="expanded",
)


def load_json(name: str):
    with open(DATA / name, encoding="utf-8") as f:
        return json.load(f)


CITIES = load_json("cities.json")
STAGES = load_json("stages.json")
AIRCRAFT = load_json("aircraft.json")


def stage_by_id(n: int) -> dict:
    return next(s for s in STAGES if s["id"] == n)


def total_nm(stage: dict) -> float:
    return float(sum(stage["legs_nm"]))


def true_plan(stage: dict) -> dict:
    ac = AIRCRAFT[stage["aircraft"]]
    tas = ac["cruise_kt"]
    wind = stage["wind_kt"]
    # planning assumption: wind is a headwind unless stage says otherwise
    gs = max(40.0, tas - 0.7 * wind)
    dist = total_nm(stage)
    hours = dist / gs
    if stage["id"] == 9:
        hours += stage.get("hold_min", 0) / 60.0
    fuel = ac["burn_gph"] * hours + ac["reserve_gal"]
    return {
        "gs_kt": round(gs, 1),
        "ete_min": round(hours * 60, 1),
        "fuel_gal": round(fuel, 1),
        "dist_nm": round(dist, 1),
        "endurance_h": round((ac["fuel_cap_gal"] - ac["reserve_gal"]) / ac["burn_gph"], 2),
    }


RANKS = [
    (1, "Cadet"),
    (3, "Student Pilot"),
    (5, "Private"),
    (7, "Cross-Country"),
    (9, "Airline Cadet"),
    (10, "Explorer"),
]


def rank_for(unlocked: int) -> str:
    name = "Cadet"
    for n, r in RANKS:
        if unlocked >= n:
            name = r
    return name


def init_state():
    ss = st.session_state
    ss.setdefault("page", "hub")
    ss.setdefault("unlocked", 1)
    ss.setdefault("active", 1)
    ss.setdefault("logbook", [])
    ss.setdefault("pins", ["VECC"])
    ss.setdefault("hours", 0.0)
    ss.setdefault("player_plan", {})
    ss.setdefault("flight", None)
    ss.setdefault("last_result", None)
    ss.setdefault("lab", {"thrust": 60, "mass": 50, "flaps": 0, "wind": 0})


def css():
    st.markdown(
        """
<style>
@import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Sans:wght@400;600;700&family=IBM+Plex+Mono:wght@400;600&display=swap');
html, body, [class*="css"]  { font-family: 'IBM Plex Sans', sans-serif; }
.block-container { padding-top: 1.1rem; max-width: 1400px; }
h1, h2, h3 { letter-spacing: 0.02em; }
.sq-hero { background: linear-gradient(120deg,#0b1220 0%,#15233d 55%,#1c2b22 100%);
  border: 1px solid #2a3b5a; border-radius: 18px; padding: 1.4rem 1.6rem; margin-bottom: 1rem; }
.sq-kicker { color:#E8B84A; font-family:'IBM Plex Mono',monospace; font-size:0.78rem; letter-spacing:0.16em; }
.sq-card { background:#151D2E; border:1px solid #2a3b5a; border-radius:14px; padding:0.9rem 1rem; margin-bottom:0.7rem; }
.sq-lock { opacity:0.45; }
.badge { display:inline-block; background:#E8B84A22; color:#E8B84A; border:1px solid #E8B84A55;
  border-radius:999px; padding:0.1rem 0.55rem; font-size:0.75rem; margin-right:0.3rem; }
.hud { font-family:'IBM Plex Mono',monospace; background:#070b14; border:1px solid #E8B84A33;
  border-radius:12px; padding:0.7rem 0.9rem; color:#E8B84A; }
.callout { background:#1d2a18; border-left:4px solid #E8B84A; padding:0.8rem 1rem; border-radius:8px; }
.warn { background:#2a1818; border-left:4px solid #e07a5f; padding:0.8rem 1rem; border-radius:8px; }
.ok { background:#13261c; border-left:4px solid #67c587; padding:0.8rem 1rem; border-radius:8px; }
div.stButton > button { border-radius:10px; font-weight:600; }
</style>
""",
        unsafe_allow_html=True,
    )


def go(page: str):
    st.session_state.page = page


init_state()
css()


# ---------------------------------------------------------------------------
# Flight engine
# ---------------------------------------------------------------------------

def new_flight(stage: dict) -> dict:
    ac = AIRCRAFT[stage["aircraft"]]
    truth = true_plan(stage)
    fuel_plan = st.session_state.player_plan.get("fuel_gal") or truth["fuel_gal"]
    fuel = min(ac["fuel_cap_gal"], max(ac["reserve_gal"], float(fuel_plan)))
    return {
        "stage_id": stage["id"],
        "nm_done": 0.0,
        "leg": 0,
        "alt": 800 if stage["id"] == 1 else 4000,
        "tas": ac["cruise_kt"] * 0.7,
        "fuel": fuel,
        "wind": stage["wind_kt"],
        "wind_from": stage["wind_from"],
        "burn_mult": 1.0,
        "stalls": 0,
        "spacing_ok": True,
        "hold_min": 0.0,
        "in_hold": False,
        "cards": [],
        "log": [],
        "alive": True,
        "arrived": False,
        "hold_survived": False,
        "diverted": False,
        "throttle": 70,
        "pitch": 2,
        "slowed_for_atc": False,
        "clock_min": 0.0,
        "path_alt": [800 if stage["id"] == 1 else 4000],
        "path_nm": [0.0],
    }


def tick(stage: dict, fl: dict) -> dict:
    ac = AIRCRAFT[stage["aircraft"]]
    dt_h = stage["tick_min"] / 60.0
    pitch = fl["pitch"]
    thr = fl["throttle"] / 100.0
    tas = ac["cruise_kt"] * (0.35 + 0.75 * thr)
    if fl.get("density"):
        tas *= 0.9
    stall = tas < ac["stall_kt"] and pitch > 8
    if stall:
        fl["stalls"] += 1
        fl["alt"] = max(0, fl["alt"] - 400)
        fl["log"].append("STALL — nose down, power up.")
        tas = max(ac["stall_kt"] - 8, tas * 0.7)
    vs = pitch * 90 - (8 if fl.get("density") else 0)
    if stall:
        vs = -600
    fl["alt"] = max(0, min(38000, fl["alt"] + vs * stage["tick_min"]))
    if fl["alt"] <= 0 and fl["nm_done"] < total_nm(stage) * 0.95:
        fl["alive"] = False
        fl["log"].append("Terrain. Flight over.")
        return fl
    head = 0.7 * fl["wind"]
    gs = max(35.0, tas - head)
    if fl["in_hold"]:
        fl["hold_min"] += stage["tick_min"]
        used = ac["burn_gph"] * fl["burn_mult"] * dt_h
        fl["fuel"] -= used
        fl["tas"] = tas
        fl["clock_min"] += stage["tick_min"]
        if fl["fuel"] <= 0:
            fl["alive"] = False
            fl["log"].append("Fuel gone in the hold.")
        if fl["hold_min"] >= stage.get("hold_min", 40):
            fl["hold_survived"] = True
            fl["arrived"] = True
            fl["in_hold"] = False
            fl["log"].append("Hold complete. Door is yours.")
        _fire_events(stage, fl)
        fl["path_nm"].append(fl["nm_done"])
        fl["path_alt"].append(fl["alt"])
        return fl

    fl["nm_done"] += gs * dt_h
    used = ac["burn_gph"] * fl["burn_mult"] * dt_h
    fl["fuel"] -= used
    fl["tas"] = tas
    fl["clock_min"] += stage["tick_min"]
    fl["path_nm"].append(fl["nm_done"])
    fl["path_alt"].append(fl["alt"])
    if fl["fuel"] <= 0:
        fl["alive"] = False
        fl["log"].append("Fuel gone.")
        return fl
    _fire_events(stage, fl)
    if fl["nm_done"] >= total_nm(stage) and not stage.get("hold_min"):
        fl["arrived"] = True
    if fl["nm_done"] >= total_nm(stage) and stage.get("hold_min") and not fl["in_hold"] and not fl["arrived"]:
        fl["in_hold"] = True
        fl["log"].append("Entering west hold.")
    return fl


def _fire_events(stage: dict, fl: dict):
    seen = set(fl.get("seen_events", []))
    for i, ev in enumerate(stage["events"]):
        key = f"{i}:{ev['type']}"
        if key in seen:
            continue
        ok = False
        if "at_nm" in ev and fl["nm_done"] >= ev["at_nm"]:
            ok = True
        if "at_hold_min" in ev and fl["hold_min"] >= ev["at_hold_min"]:
            ok = True
        if not ok:
            continue
        seen.add(key)
        fl.setdefault("seen_events", []).append(key)
        if ev["type"] == "callout":
            city = CITIES.get(ev.get("city", ""), {})
            fl["cards"].append(city)
            if ev.get("city") and ev["city"] not in st.session_state.pins:
                st.session_state.pins.append(ev["city"])
        elif ev["type"] == "weather":
            if "wind_add" in ev:
                fl["wind"] += ev["wind_add"]
            if "wind_set" in ev:
                fl["wind"] = ev["wind_set"]
            if "wind_from" in ev:
                fl["wind_from"] = ev["wind_from"]
            fl["log"].append(ev["text"])
        elif ev["type"] == "emergency":
            fl["burn_mult"] = ev.get("burn_mult", fl["burn_mult"])
            fl["log"].append(ev["text"])
        elif ev["type"] == "atc":
            fl["log"].append(ev["text"])
            if not fl.get("slowed_for_atc"):
                fl["spacing_ok"] = False
        elif ev["type"] == "physics":
            fl["density"] = True
            fl["log"].append(ev["text"])
        elif ev["type"] in ("hint", "turnaround", "hold"):
            fl["log"].append(ev["text"])
        else:
            fl["log"].append(ev.get("text", ev["type"]))
    fl["seen_events"] = list(seen)


def score_flight(stage: dict, fl: dict) -> dict:
    ac = AIRCRAFT[stage["aircraft"]]
    truth = true_plan(stage)
    plan = st.session_state.player_plan
    stars = 0
    notes = []
    if not fl["alive"]:
        return {"stars": 0, "pass": False, "notes": ["Did not finish."], "truth": truth}
    passed = fl["arrived"] or fl.get("hold_survived")
    if fl["stalls"]:
        notes.append(f"{fl['stalls']} stall(s).")
    if fl["fuel"] < ac["reserve_gal"]:
        notes.append("Finished below reserve.")
        if stage["id"] >= 3:
            passed = False
    if stage["id"] in (6, 10) and not fl["spacing_ok"]:
        notes.append("ATC spacing broken.")
        passed = False
    if passed:
        stars = 1
        ete_p = plan.get("ete_min")
        if ete_p:
            err = abs(float(ete_p) - truth["ete_min"]) / max(1.0, truth["ete_min"]) * 100
            lim = stage["stars"]["ete_error_pct"]
            if err <= lim * 2:
                stars = 2
            if err <= lim and fl["stalls"] == 0 and fl["fuel"] >= ac["reserve_gal"]:
                stars = 3
        else:
            stars = 2 if fl["stalls"] == 0 else 1
        notes.append("Arrived.")
    hours = fl["clock_min"] / 60.0
    return {"stars": stars, "pass": passed, "notes": notes, "truth": truth, "hours": hours}


def dual_figure(stage: dict, fl: dict):
    dist = total_nm(stage)
    xs = fl["path_nm"]
    ys = fl["path_alt"]
    fig = make_subplots(
        rows=1, cols=2,
        subplot_titles=("Top-down track", "Side profile"),
        horizontal_spacing=0.08,
    )
    # top-down: progress on a straight strip with city marks
    fig.add_trace(
        go.Scatter(
            x=[0, dist], y=[0, 0], mode="lines",
            line=dict(color="#2a3b5a", width=2), name="airway",
        ),
        row=1, col=1,
    )
    acc = 0.0
    for i, icao in enumerate(stage["route"]):
        if i == 0:
            x = 0
        else:
            acc += stage["legs_nm"][i - 1]
            x = acc
        city = CITIES.get(icao, {"name": icao})
        fig.add_trace(
            go.Scatter(
                x=[x], y=[0], mode="markers+text",
                marker=dict(size=11, color="#E8B84A"),
                text=[city.get("name", icao).split("/")[0]],
                textposition="top center",
                name=icao, showlegend=False,
            ),
            row=1, col=1,
        )
    fig.add_trace(
        go.Scatter(
            x=[min(fl["nm_done"], dist)], y=[0],
            mode="markers", marker=dict(size=16, color="#67c587", symbol="triangle-right"),
            name="you",
        ),
        row=1, col=1,
    )
    fig.update_xaxes(title_text="NM along track", row=1, col=1)
    fig.update_yaxes(visible=False, row=1, col=1, range=[-1, 1])

    # terrain
    terrain_x = list(range(0, int(dist) + 1, max(1, int(dist // 40) or 1)))
    if stage["id"] in (5, 10):
        terrain_y = [max(0, (x - dist * 0.55) * 8) if x > dist * 0.45 else 200 for x in terrain_x]
    elif stage["id"] in (8, 9):
        terrain_y = [0 for _ in terrain_x]
    else:
        terrain_y = [80 + 40 * (i % 5) for i, _ in enumerate(terrain_x)]
    fig.add_trace(
        go.Scatter(
            x=terrain_x, y=terrain_y, fill="tozeroy",
            line=dict(color="#3d4a3a", width=1), name="terrain",
            fillcolor="rgba(80,90,60,0.35)",
        ),
        row=1, col=2,
    )
    fig.add_trace(
        go.Scatter(
            x=xs, y=ys, mode="lines",
            line=dict(color="#E8B84A", width=3), name="path",
        ),
        row=1, col=2,
    )
    fig.add_trace(
        go.Scatter(
            x=[xs[-1]], y=[ys[-1]], mode="markers",
            marker=dict(size=14, color="#67c587"), name="now",
        ),
        row=1, col=2,
    )
    fig.update_xaxes(title_text="NM", row=1, col=2)
    fig.update_yaxes(title_text="feet", row=1, col=2)
    fig.update_layout(
        height=360, paper_bgcolor="#0B1220", plot_bgcolor="#0B1220",
        font=dict(color="#E7ECF5", family="IBM Plex Sans"),
        margin=dict(l=40, r=20, t=40, b=40),
        legend=dict(orientation="h", y=-0.22),
    )
    fig.update_xaxes(gridcolor="#1c2740", zeroline=False)
    fig.update_yaxes(gridcolor="#1c2740", zeroline=False)
    return fig


# ---------------------------------------------------------------------------
# Pages
# ---------------------------------------------------------------------------

def page_hub():
    st.markdown(
        """<div class="sq-hero">
        <div class="sq-kicker">SK Y Q U E S T &nbsp; · &nbsp; CADET PROGRAMME</div>
        <h1>Ten stages. Two theatres. One logbook.</h1>
        <p>South Asia and Europe only. Top-down and side view on every hop.
        City history fires in the cockpit. Math is how you stay in the air.</p>
        </div>""",
        unsafe_allow_html=True,
    )
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Rank", rank_for(st.session_state.unlocked))
    c2.metric("Open stage", f"{st.session_state.unlocked} / 10")
    c3.metric("Hours", f"{st.session_state.hours:.1f}")
    c4.metric("Atlas pins", len(st.session_state.pins))

    st.subheader("Campaign")
    for s in STAGES:
        locked = s["id"] > st.session_state.unlocked
        cols = st.columns([0.12, 0.55, 0.18, 0.15])
        cols[0].markdown(f"**{s['id']:02d}**")
        title = s["title"] + ("  🔒" if locked else "")
        cols[1].markdown(f"**{title}**  \n{s['theater']} · {AIRCRAFT[s['aircraft']]['name']} · {total_nm(s):.0f} NM")
        cols[2].caption(s["pressure"] + " pressure")
        if locked:
            cols[3].button("Locked", key=f"l{s['id']}", disabled=True)
        else:
            if cols[3].button("Open", key=f"o{s['id']}"):
                st.session_state.active = s["id"]
                st.session_state.player_plan = {}
                st.session_state.flight = None
                go("brief")
                st.rerun()


def page_brief():
    s = stage_by_id(st.session_state.active)
    ac = AIRCRAFT[s["aircraft"]]
    truth = true_plan(s)
    st.markdown(f"<div class='sq-kicker'>STAGE {s['id']} / 10</div>", unsafe_allow_html=True)
    st.title(s["title"])
    a, b = st.columns(2)
    with a:
        st.markdown(f"<div class='sq-card'><b>Hook</b><br>{s['hook']}</div>", unsafe_allow_html=True)
        st.markdown(f"<div class='sq-card'><b>History</b><br>{s['history']}</div>", unsafe_allow_html=True)
        st.markdown(f"<div class='sq-card'><b>Learn this</b><br>{s['teach']}<br><code>{s['formula']}</code></div>", unsafe_allow_html=True)
    with b:
        st.markdown(
            f"<div class='sq-card'><b>Route</b><br>{' → '.join(CITIES[c]['name'] for c in s['route'])}<br>"
            f"{s['note_nm']}</div>",
            unsafe_allow_html=True,
        )
        st.markdown(
            f"<div class='sq-card'><b>Ship</b> {ac['name']} · cruise {ac['cruise_kt']} kt · "
            f"burn {ac['burn_gph']} gph · reserve {ac['reserve_gal']} gal<br>"
            f"<b>Wind (briefed)</b> {s['wind_kt']} kt from {s['wind_from']}°</div>",
            unsafe_allow_html=True,
        )
        st.markdown(f"<div class='sq-card'><b>Adventure</b><br>{s['adventure']}</div>", unsafe_allow_html=True)
        st.caption(f"Planning sheet (hidden from the kid unless they ask a hint): GS ~ {truth['gs_kt']} kt")
    c1, c2, c3 = st.columns(3)
    if c1.button("← Hub"):
        go("hub"); st.rerun()
    if c2.button("Need a worked example"):
        st.info(
            f"Distance {truth['dist_nm']} NM. If GS is {truth['gs_kt']} kt then "
            f"ETE = {truth['dist_nm']} / {truth['gs_kt']} × 60 ≈ {truth['ete_min']} min. "
            f"Fuel ≈ {ac['burn_gph']} × {truth['ete_min']/60:.2f} + {ac['reserve_gal']} ≈ {truth['fuel_gal']} gal."
        )
    if c3.button("Write the plan →"):
        go("plan"); st.rerun()


def page_plan():
    s = stage_by_id(st.session_state.active)
    ac = AIRCRAFT[s["aircraft"]]
    st.title(f"Plan · {s['title']}")
    st.write("Fill what the flight needs. Wrong numbers still fly — they just land you in trouble.")
    fields = s["plan_fields"]
    plan = {}
    cols = st.columns(2)
    with cols[0]:
        if "legs_sum_nm" in fields:
            plan["legs_sum_nm"] = st.number_input("Sum of legs (NM)", min_value=0.0, step=0.1)
        if "gs_kt" in fields:
            plan["gs_kt"] = st.number_input("Planned groundspeed (kt)", min_value=0.0, step=1.0)
        if "ete_min" in fields:
            plan["ete_min"] = st.number_input("ETE (minutes)", min_value=0.0, step=0.5)
        if "fuel_gal" in fields:
            plan["fuel_gal"] = st.number_input(
                f"Fuel to load (gal)  — cap {ac['fuel_cap_gal']}",
                min_value=0.0, max_value=float(ac["fuel_cap_gal"]), step=0.5,
            )
    with cols[1]:
        if "endurance_h" in fields:
            plan["endurance_h"] = st.number_input("Endurance minus reserve (hours)", min_value=0.0, step=0.1)
        if "pnr_min" in fields:
            plan["pnr_min"] = st.number_input("Point-of-no-return (minutes into hold)", min_value=0.0, step=1.0)
        if "spacing_action" in fields:
            plan["spacing_action"] = st.selectbox(
                "ATC: traffic same speed 8 NM ahead. To have 3 NM at the field you should",
                ["Do nothing", "Slow about 20 kt", "Speed up", "Climb only"],
            )
            if plan["spacing_action"] == "Slow about 20 kt":
                st.session_state.pre_slow = True
            else:
                st.session_state.pre_slow = False
        if "divert" in fields:
            plan["divert"] = st.selectbox("If burn jumps 15% after Naples", ["Press to Athens", "Use Brindisi", "Turn back now"])
        if "arrival_local" in fields:
            plan["arrival_local"] = st.text_input("Local arrival at Dum Dum (IST = UTC+5:30)", placeholder="e.g. 19:40 IST")
    st.session_state.player_plan = plan
    b1, b2 = st.columns(2)
    if b1.button("← Brief"):
        go("brief"); st.rerun()
    if b2.button("Start engines →"):
        fl = new_flight(s)
        if st.session_state.get("pre_slow"):
            fl["slowed_for_atc"] = True
            fl["spacing_ok"] = True
        st.session_state.flight = fl
        go("fly")
        st.rerun()


def page_fly():
    s = stage_by_id(st.session_state.active)
    fl = st.session_state.flight
    if fl is None:
        go("plan"); st.rerun()
    ac = AIRCRAFT[s["aircraft"]]
    st.markdown(f"<div class='sq-kicker'>LIVE · STAGE {s['id']} · {s['title']}</div>", unsafe_allow_html=True)

    left, right = st.columns([0.28, 0.72])
    with left:
        fl["throttle"] = st.slider("Throttle %", 0, 100, int(fl["throttle"]))
        fl["pitch"] = st.slider("Pitch (deg)", -8, 16, int(fl["pitch"]))
        if st.button("Advance 1 tick", type="primary", disabled=not fl["alive"] or fl["arrived"]):
            st.session_state.flight = tick(s, fl)
            st.rerun()
        if s["id"] in (6, 10):
            if st.button("Tell ATC: slowing"):
                fl["slowed_for_atc"] = True
                fl["spacing_ok"] = True
                fl["throttle"] = max(40, fl["throttle"] - 15)
                fl["log"].append("You slowed. Spacing should open.")
                st.rerun()
        if s["id"] == 9 and fl.get("in_hold"):
            cA, cB = st.columns(2)
            if cA.button("TURN BACK"):
                fl["in_hold"] = False
                fl["arrived"] = True
                fl["hold_survived"] = True
                fl["diverted"] = True
                fl["log"].append("Turned back to Shannon. Alive beats pride.")
                st.rerun()
            if cB.button("FINISH HOLD"):
                fl["log"].append("Continuing the hold.")
                st.rerun()
        if (not fl["alive"]) or fl["arrived"]:
            if st.button("Debrief →"):
                res = score_flight(s, fl)
                st.session_state.last_result = res
                if res["pass"]:
                    st.session_state.hours += res.get("hours", 0)
                    if st.session_state.unlocked == s["id"] and s["id"] < 10:
                        st.session_state.unlocked = s["id"] + 1
                    if s["id"] == 10:
                        st.session_state.unlocked = 10
                    st.session_state.logbook.append(
                        {"stage": s["id"], "title": s["title"], "stars": res["stars"], "hours": res.get("hours", 0)}
                    )
                go("debrief")
                st.rerun()

    with right:
        h1, h2, h3, h4, h5 = st.columns(5)
        h1.markdown(f"<div class='hud'>TAS<br><b>{fl['tas']:.0f}</b> kt</div>", unsafe_allow_html=True)
        h2.markdown(f"<div class='hud'>ALT<br><b>{fl['alt']:.0f}</b> ft</div>", unsafe_allow_html=True)
        h3.markdown(f"<div class='hud'>FUEL<br><b>{max(0,fl['fuel']):.1f}</b> gal</div>", unsafe_allow_html=True)
        h4.markdown(f"<div class='hud'>DONE<br><b>{fl['nm_done']:.1f}</b> / {total_nm(s):.1f} NM</div>", unsafe_allow_html=True)
        h5.markdown(f"<div class='hud'>WIND<br><b>{fl['wind']:.0f}</b> kt</div>", unsafe_allow_html=True)
        st.plotly_chart(dual_figure(s, fl), use_container_width=True)

    if fl["cards"]:
        city = fl["cards"][-1]
        if city:
            st.markdown(
                f"<div class='callout'><b>{city.get('name','')}</b> · {city.get('icao','')}<br>"
                f"{city.get('line','')}<br>"
                f"<i>{city.get('geo','')}</i><br>{city.get('av','')}<br>"
                f"<b>Why a pilot cares:</b> {city.get('why','')}</div>",
                unsafe_allow_html=True,
            )
    if fl["log"]:
        last = fl["log"][-1]
        klass = "warn" if any(w in last.upper() for w in ("STALL", "FUEL", "ROUGH", "EMERGENCY", "LEAK", "TERRAIN")) else "ok"
        st.markdown(f"<div class='{klass}'>{last}</div>", unsafe_allow_html=True)

    st.caption(f"Tick = {s['tick_min']} min · decisions this stage are {s['pressure']} pressure · {s['decisions_per_tick']} inputs per tick")


def page_debrief():
    s = stage_by_id(st.session_state.active)
    res = st.session_state.last_result or {}
    fl = st.session_state.flight or {}
    st.title(f"Debrief · {s['title']}")
    stars = "★" * res.get("stars", 0) + "☆" * (3 - res.get("stars", 0))
    st.markdown(f"### {stars}")
    if res.get("pass"):
        st.success("Stage complete. Next door is open." if s["id"] < 10 else "Long hop complete. Explorer rank.")
    else:
        st.error("Not yet. Read the table. Fly it again.")
    truth = res.get("truth", true_plan(s))
    plan = st.session_state.player_plan
    st.write(
        {
            "planned ETE min": plan.get("ete_min"),
            "book ETE min": truth["ete_min"],
            "planned fuel": plan.get("fuel_gal"),
            "book fuel": truth["fuel_gal"],
            "fuel at end": None if not fl else round(fl.get("fuel", 0), 1),
            "stalls": None if not fl else fl.get("stalls"),
            "spacing ok": None if not fl else fl.get("spacing_ok"),
            "notes": res.get("notes"),
        }
    )
    st.caption("Book numbers use briefed wind as a 0.7 headwind component and cruise TAS. Your flown GS changes with throttle.")
    c1, c2, c3 = st.columns(3)
    if c1.button("Hub"):
        go("hub"); st.rerun()
    if c2.button("Fly again"):
        st.session_state.flight = None
        go("plan"); st.rerun()
    if c3.button("Atlas"):
        go("atlas"); st.rerun()


def page_atlas():
    st.title("Atlas")
    st.write("Pins from city cards you flew through. South Asia and Europe only.")
    for icao in st.session_state.pins:
        c = CITIES.get(icao)
        if not c:
            continue
        st.markdown(
            f"<div class='sq-card'><b>{c['name']}</b> · {c['icao']} · {c['region']}<br>"
            f"{c['line']}<br><i>{c['av']}</i></div>",
            unsafe_allow_html=True,
        )
    st.subheader("Logbook")
    if not st.session_state.logbook:
        st.caption("No flights closed yet.")
    else:
        st.table(st.session_state.logbook)


def page_lab():
    st.title("Flight Lab")
    st.write("Four sliders. Watch which force wins. No quiz.")
    lab = st.session_state.lab
    a, b = st.columns(2)
    lab["thrust"] = a.slider("Thrust", 0, 100, lab["thrust"])
    lab["mass"] = a.slider("Mass", 20, 100, lab["mass"])
    lab["flaps"] = b.slider("Flaps (lift + drag)", 0, 40, lab["flaps"])
    lab["wind"] = b.slider("Headwind", 0, 40, lab["wind"])
    lift = 40 + lab["flaps"] * 0.8 + lab["thrust"] * 0.35
    weight = lab["mass"] * 1.1
    thrust = lab["thrust"]
    drag = 20 + lab["flaps"] * 0.5 + lab["wind"] * 0.6
    fig = go.Figure()
    fig.add_trace(go.Bar(x=["Lift", "Weight", "Thrust", "Drag"], y=[lift, weight, thrust, drag],
                         marker_color=["#67c587", "#e07a5f", "#E8B84A", "#7aa2f7"]))
    fig.update_layout(height=320, paper_bgcolor="#0B1220", plot_bgcolor="#0B1220",
                      font=dict(color="#E7ECF5"), yaxis_title="relative force")
    st.plotly_chart(fig, use_container_width=True)
    if lift > weight and thrust > drag:
        st.success("Climbing and accelerating.")
    elif lift > weight:
        st.info("Climbing, but drag is eating speed.")
    elif thrust > drag:
        st.info("Speeding up, but not climbing.")
    else:
        st.warning("Sinking and slowing. This is how a stall starts if you pull.")
    st.caption("Lift is Bernoulli + Newton together. Equal-transit-time is a myth. We do not teach it.")


def page_atc():
    st.title("ATC Tower")
    st.write("NASA-style spacing: two aircraft, one merge, 3 NM minimum. Stage 6 and 10 reuse this live.")
    lead_nm = st.slider("Lead aircraft distance to merge (NM)", 5, 40, 20)
    lead_kt = st.slider("Lead speed (kt)", 80, 250, 140)
    you_nm = st.slider("You distance to merge (NM)", 5, 40, 28)
    you_kt = st.slider("Your speed (kt)", 80, 250, 140)
    t_lead = lead_nm / lead_kt * 60
    t_you = you_nm / you_kt * 60
    # position of lead when you arrive
    lead_when_you = lead_nm - lead_kt * (t_you / 60)
    spacing = abs(lead_when_you) if t_you >= t_lead else abs(you_nm - you_kt * (t_lead / 60))
    # simpler: difference in arrival time * slower? Use arrival gap * lead speed after first arrives
    gap_min = t_you - t_lead
    spacing_nm = abs(gap_min) / 60 * (lead_kt if gap_min > 0 else you_kt)
    st.metric("Arrival gap", f"{gap_min:.1f} min")
    st.metric("Spacing at merge", f"{spacing_nm:.1f} NM")
    if spacing_nm >= 3:
        st.success("Legal. 3 NM or more.")
    else:
        st.error("Conflict. Slow, or take a longer route.")
    st.caption("t = d / v. Spacing ≈ |t₁ − t₂| × speed of the first one through the point.")


def page_deploy_help():
    st.title("GitHub → Streamlit Cloud")
    st.markdown(
        """
1. Create an empty GitHub repository.
2. Upload this `skyquest` folder as the repo root (`app.py` must sit at the root).
3. Open [share.streamlit.io](https://share.streamlit.io), sign in with GitHub.
4. **New app** → pick the repo → branch `main` → main file `app.py`.
5. Deploy. First boot installs `requirements.txt`.

Do not commit `.venv` or secrets. Progress is session-only unless you later add a login.
"""
    )


# ---------------------------------------------------------------------------
# Shell
# ---------------------------------------------------------------------------

with st.sidebar:
    st.markdown("### ✈ SkyQuest")
    st.caption("South Asia · Europe")
    nav = st.radio(
        "Deck",
        ["Hub", "Brief / fly", "Atlas", "Flight Lab", "ATC Tower", "Deploy"],
        label_visibility="collapsed",
    )
    st.markdown(f"Rank **{rank_for(st.session_state.unlocked)}**")
    if st.button("Reset cadet (wipe progress)"):
        for k in list(st.session_state.keys()):
            del st.session_state[k]
        st.rerun()

if nav == "Hub":
    page_hub()
elif nav == "Atlas":
    page_atlas()
elif nav == "Flight Lab":
    page_lab()
elif nav == "ATC Tower":
    page_atc()
elif nav == "Deploy":
    page_deploy_help()
else:
    page = st.session_state.page
    if page == "hub":
        page_hub()
    elif page == "brief":
        page_brief()
    elif page == "plan":
        page_plan()
    elif page == "fly":
        page_fly()
    elif page == "debrief":
        page_debrief()
    else:
        page_hub()
