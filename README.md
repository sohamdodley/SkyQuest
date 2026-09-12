# SkyQuest

A 10-stage aviation cadet game for about age 12.  
Theatres: **South Asia** and **Europe** only.  
Every flight shows a **top-down chart** and a **side profile**.  
City history cards fire in the cockpit. Math is how you finish the hop.

This is not Microsoft Flight Simulator. It is a mission loop: brief → plan → fly → debrief.

## Deploy on Streamlit Community Cloud (via GitHub)

1. Create a new GitHub repository (public is fine).
2. Put **this folder** at the **root** of the repo so GitHub shows:

```
app.py
requirements.txt
README.md
LICENSE
.gitignore
.streamlit/config.toml
data/aircraft.json
data/cities.json
data/stages.json
```

3. Push to `main`.
4. Go to [https://share.streamlit.io](https://share.streamlit.io) and sign in with GitHub.
5. **New app** → repository → branch `main` → main file path `app.py`.
6. Deploy. The cloud install uses `requirements.txt`.

Local run (after you have Python 3.10+):

```bash
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
streamlit run app.py
```

## Ten stages (each one tighter than the last)

| # | Title | Route | New pressure |
|---|---|---|---|
| 1 | Grass Circuit | Dum Dum box, 12 NM | Four forces, dual view |
| 2 | Six Miles of Mail | Allahabad → Naini, **5.2 NM** (documented 6-mile 1911 hop) | `t = d / v` |
| 3 | Tata's Beach | Ahmedabad → Juhu, 239.1 NM | Fuel + headwind |
| 4 | Eastern Trunk | Delhi → Allahabad → Kolkata, 714.7 NM | Multi-leg, city cards |
| 5 | Himalaya Gate | Kolkata → Bagdogra → Kathmandu, 411.7 NM | Thin air, terrain |
| 6 | Silver Wing | Croydon → Le Bourget, 173.6 NM | 3 NM ATC spacing, time zone |
| 7 | Mail String | Cologne → Nuremberg → Vienna → Budapest, 520.6 NM | Wind flip each border |
| 8 | Boat Chain | Southampton → Marseille → Naples → Brindisi → Athens, 1445.5 NM | Water, fuel leak |
| 9 | Atlantic Door | Dublin → Shannon + 40 min west hold | Point of no return, immediate pick |
| 10 | The Long Hop | London → Athens → Karachi → Delhi → Kolkata, 4919.5 NM | Everything stacked |

Distances except stage 1 and the 1911 mail hop are **haversine NM** from published airport coordinates.  
Stage 2 uses the documented 6 miles / 9.7 km, not a noisy coordinate pair.

Athens–Karachi is **overflight only**. No Cairo / Baghdad / Sharjah missions.

## What is sourced

City cards in `data/cities.json` are short public facts (1911 Allahabad airmail, 1932 Tata Juhu landing, 1924 KLM at Calcutta, Croydon 1920, Le Bourget 1927, Shannon duty-free 1947, etc.). If a date was not solid, it is not on the card.

Lift is taught as Bernoulli **and** Newton. Equal-transit-time is not used.

## Save data

Progress lives in the Streamlit session. A reset button wipes the cadet. Add a database later if you want cross-device saves.

## License

MIT.
