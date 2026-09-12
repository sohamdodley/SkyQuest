"""SkyQuest — 10-stage cadet game. South Asia + Europe. Dual-view flights.

Expects a flat GitHub repo root:
  app.py
  cities.json
  stages.json
  aircraft.json
  requirements.txt

JSON is also embedded below, so the app still boots if those files are missing.
"""

from __future__ import annotations

import json
from pathlib import Path

import plotly.graph_objects as go
from plotly.subplots import make_subplots
import streamlit as st

HERE = Path(__file__).resolve().parent

EMBEDDED_CITIES = """{
  "VECC": {"id":"kolkata","icao":"VECC","iata":"CCU","name":"Kolkata / Dum Dum","region":"south_asia","lat":22.6547,"lon":88.4467,"elev_ft":16,"tz":"Asia/Kolkata","geo":"On the Hooghly, gateway to eastern India.","av":"Scheduled traffic from 1924. KLM stopped here on Amsterdam–Batavia. Imperial used Calcutta on London–Australia from 1933. Earhart stopped June 1937.","line":"Dum Dum. In the 1930s this grass was a stop on the Europe–Australia trunk.","why":"Monsoon and river fog. Carry the reserve you calculated."},
  "VEAB": {"id":"prayagraj","icao":"VEAB","iata":"IXD","name":"Prayagraj (Allahabad)","region":"south_asia","lat":25.4401,"lon":81.7339,"elev_ft":322,"tz":"Asia/Kolkata","geo":"Confluence of Ganga and Yamuna.","av":"18 Feb 1911: Henri Pequet flew Allahabad→Naini, about 6 miles / 9.7 km, 6,500 letters — first official airmail flight.","line":"Allahabad. Six miles and a bag of letters started civil flying in India.","why":"The rivers are your map."},
  "NAINI": {"id":"naini","icao":"NAINI","iata":"","name":"Naini","region":"south_asia","lat":25.3960,"lon":81.8620,"elev_ft":312,"tz":"Asia/Kolkata","geo":"Just across the Yamuna from Allahabad.","av":"Landing end of the 18 Feb 1911 airmail hop.","line":"Naini. The world's first official airmail ended in this field.","why":"Short hop. See the whole distance on the side view."},
  "VAAH": {"id":"ahmedabad","icao":"VAAH","iata":"AMD","name":"Ahmedabad","region":"south_asia","lat":23.0772,"lon":72.6347,"elev_ft":189,"tz":"Asia/Kolkata","geo":"Sabarmati river. Desert to the west, coast to the south.","av":"Stop on J.R.D. Tata's 15 Oct 1932 Karachi–Bombay mail flight.","line":"Ahmedabad. Tata put the Puss Moth down here on the first Tata mail day.","why":"A fuel stop turns one long desert leg into two safe ones."},
  "VAJJ": {"id":"juhu","icao":"VAJJ","iata":"","name":"Mumbai / Juhu","region":"south_asia","lat":19.0984,"lon":72.8339,"elev_ft":13,"tz":"Asia/Kolkata","geo":"Island city on the Arabian Sea.","av":"Juhu aerodrome 1928. 15 Oct 1932 Tata landed a Puss Moth here from Karachi via Ahmedabad.","line":"Juhu beach strip. Tata's 1932 mail run ended on this sand.","why":"Sea breeze and monsoon waterlogging."},
  "VIDP": {"id":"delhi","icao":"VIDP","iata":"DEL","name":"Delhi","region":"south_asia","lat":28.5562,"lon":77.1000,"elev_ft":777,"tz":"Asia/Kolkata","geo":"Yamuna. Capital since 1911.","av":"Dec 1912: first international service into India, London–Karachi–Delhi.","line":"Delhi. The first international air service into India aimed at this city in 1912.","why":"Winter fog. Hold or divert — that is an ETA problem."},
  "VEBD": {"id":"bagdogra","icao":"VEBD","iata":"IXB","name":"Bagdogra","region":"south_asia","lat":26.6812,"lon":88.3286,"elev_ft":412,"tz":"Asia/Kolkata","geo":"Siliguri corridor. Plains under the first wall of the Himalaya.","av":"21 May 1927: Bengal Air Transport flew cargo Calcutta–Bagdogra.","line":"Bagdogra. Tea gardens below, mountains ahead.","why":"Afternoon build-ups over the hills."},
  "VNKT": {"id":"kathmandu","icao":"VNKT","iata":"KTM","name":"Kathmandu","region":"south_asia","lat":27.6966,"lon":85.3591,"elev_ft":4390,"tz":"Asia/Kathmandu","geo":"Valley in the Himalaya.","av":"Mountain-gate field. Thin air is the lesson.","line":"Kathmandu valley. Thin air — the wing has less to bite.","why":"Density altitude. Same indicated speed, less lift."},
  "OPKC": {"id":"karachi","icao":"OPKC","iata":"KHI","name":"Karachi","region":"south_asia","lat":24.9065,"lon":67.1608,"elev_ft":100,"tz":"Asia/Karachi","geo":"Arabian Sea. Western door of South Asia.","av":"Western end of the 1932 Tata mail run and Imperial's India service.","line":"Karachi. Where Europe's air route used to hand India the mail.","why":"Desert heat and a sea breeze near the coast."},
  "EGCR": {"id":"croydon","icao":"EGCR","iata":"","name":"London Croydon","region":"europe","lat":51.3514,"lon":-0.1172,"elev_ft":240,"tz":"Europe/London","geo":"South of London. Thames basin.","av":"London's main civil airport from 29 Mar 1920 after Hounslow. Terminal 1928. Closed 1959.","line":"Croydon was London's door to Paris and to India.","why":"Tight airspace. Heading is not a suggestion."},
  "EGLL": {"id":"heathrow","icao":"EGLL","iata":"LHR","name":"London Heathrow","region":"europe","lat":51.4700,"lon":-0.4543,"elev_ft":83,"tz":"Europe/London","geo":"West London.","av":"Took Croydon's trunk traffic after 1946–59.","line":"Heathrow. The field that replaced Croydon.","why":"Crowded. Fly the number you planned."},
  "LFPB": {"id":"lebourget","icao":"LFPB","iata":"LBG","name":"Paris Le Bourget","region":"europe","lat":48.9694,"lon":2.4414,"elev_ft":218,"tz":"Europe/Paris","geo":"North of Paris, Seine basin.","av":"Civil from 1919. Lindbergh landed Spirit of St. Louis here 21 May 1927.","line":"Le Bourget. Lindbergh's Atlantic ended on this grass in 1927.","why":"Short European hop. Good ETA practice."},
  "EDDK": {"id":"cologne","icao":"EDDK","iata":"CGN","name":"Cologne","region":"europe","lat":50.8659,"lon":7.1427,"elev_ft":302,"tz":"Europe/Berlin","geo":"Rhine.","av":"Imperial London–Brussels–Cologne 3 May 1924. India mail turned here 2 Nov 1929.","line":"Cologne. In 1929 the India mail turned here for Vienna.","why":"Rhine fog steals your landmark."},
  "EDDN": {"id":"nuremberg","icao":"EDDN","iata":"NUE","name":"Nuremberg","region":"europe","lat":49.4987,"lon":11.0781,"elev_ft":1046,"tz":"Europe/Berlin","geo":"Franconian basin.","av":"Stop on Imperial's 2 Nov 1929 routing between Cologne and Vienna.","line":"Nuremberg. Next bead after Cologne on the 1929 mail string.","why":"Higher field. Climb costs speed."},
  "LOWW": {"id":"vienna","icao":"LOWW","iata":"VIE","name":"Vienna","region":"europe","lat":48.1103,"lon":16.5697,"elev_ft":600,"tz":"Europe/Vienna","geo":"Danube. Alps to the west.","av":"On Imperial's Nov 1929 central-Europe mail routing.","line":"Vienna. Mail to India once came through this city by air.","why":"Stay on the valley airway."},
  "LHBP": {"id":"budapest","icao":"LHBP","iata":"BUD","name":"Budapest","region":"europe","lat":47.4298,"lon":19.2611,"elev_ft":495,"tz":"Europe/Budapest","geo":"Danube. Buda hills, Pest plain.","av":"On the 1929 mail string. Ferihegy civil from May 1950.","line":"Budapest. The 1929 India mail crossed the Danube here.","why":"Follow the river in."},
  "EGHI": {"id":"southampton","icao":"EGHI","iata":"SOU","name":"Southampton / Calshot","region":"europe","lat":50.9503,"lon":-1.3568,"elev_ft":44,"tz":"Europe/London","geo":"Southampton Water.","av":"Calshot 1913. Empire flying boats from March 1937.","line":"Southampton Water. The Empire boats left this inlet in 1937.","why":"Water chapter. Side view shows a hull."},
  "LFML": {"id":"marseille","icao":"LFML","iata":"MRS","name":"Marseille","region":"europe","lat":43.4393,"lon":5.2214,"elev_ft":69,"tz":"Europe/Paris","geo":"Mediterranean. Rhône delta west.","av":"On later Empire / flying-boat routings toward Italy.","line":"Marseille. France's south door onto the Middle Sea.","why":"Mistral eats inbound groundspeed."},
  "LIRN": {"id":"naples","icao":"LIRN","iata":"NAP","name":"Naples","region":"europe","lat":40.8860,"lon":14.2908,"elev_ft":294,"tz":"Europe/Rome","geo":"Bay of Naples. Vesuvius on the side view.","av":"Imperial flying-boat sectors Genoa–Rome–Naples.","line":"Naples. Volcano on the right, bay under the nose.","why":"The mountain is a wind machine."},
  "LIBR": {"id":"brindisi","icao":"LIBR","iata":"BDS","name":"Brindisi","region":"europe","lat":40.6576,"lon":17.9470,"elev_ft":47,"tz":"Europe/Rome","geo":"Heel of Italy, Adriatic.","av":"Imperial passengers often trained to Brindisi, then boat to Athens.","line":"Brindisi. Where the train handed the Empire route back to a boat.","why":"Sea breeze and a long water fetch."},
  "LGAV": {"id":"athens","icao":"LGAV","iata":"ATH","name":"Athens","region":"europe","lat":37.9364,"lon":23.9445,"elev_ft":308,"tz":"Europe/Athens","geo":"Attica. First glimpse of the Aegean.","av":"Stop on Imperial's eastbound Empire routing. Last European land on Chapter 10.","line":"Athens. After this the old Empire route left Europe.","why":"Last European land before the corridor."},
  "EIDW": {"id":"dublin","icao":"EIDW","iata":"DUB","name":"Dublin","region":"europe","lat":53.4264,"lon":-6.2499,"elev_ft":242,"tz":"Europe/Dublin","geo":"Irish Sea. Liffey.","av":"Opened 19 January 1942. Aer Lingus to Shannon Aug 1942.","line":"Dublin. Opened in 1942; the short sea hop to Britain starts here.","why":"A westerly is a gift going home, a tax going out."},
  "EINN": {"id":"shannon","icao":"EINN","iata":"SNN","name":"Shannon / Foynes","region":"europe","lat":52.7020,"lon":-8.9248,"elev_ft":46,"tz":"Europe/Dublin","geo":"Shannon estuary. Last European land before a lot of Atlantic.","av":"Foynes boats from 1937. Yankee Clipper 9 July 1939. Shannon land 1942–45. Duty-free airport 1947.","line":"Shannon. Flying boats at Foynes, then the first duty-free airport on earth.","why":"Westbound, this is where fuel math gets serious."},
  "EBBR": {"id":"brussels","icao":"EBBR","iata":"BRU","name":"Brussels","region":"europe","lat":50.9014,"lon":4.4844,"elev_ft":184,"tz":"Europe/Brussels","geo":"Low country.","av":"SNETA Brussels–Croydon 25 May 1920. Zaventem terminal 5 July 1958.","line":"Brussels. Sabena's grandparents flew this field to Croydon in 1920.","why":"Flat land. Drift is a number."}
}
"""

EMBEDDED_STAGES = """[
  {
    "id": 1,
    "code": "S1_CIRCUIT",
    "title": "Grass Circuit",
    "rank_unlock": "Cadet",
    "theater": "South Asia",
    "aircraft": "trainer",
    "hook": "Dum Dum. A grass strip by the Hooghly. Your first job is not India or Europe. It is one clean circuit.",
    "history": "Calcutta Aerodrome took scheduled traffic from 1924. You start where that field still sits.",
    "teach": "Four forces: lift, weight, thrust, drag. Climb when lift beats weight. Speed up when thrust beats drag.",
    "formula": "Lift ↑ with speed and wing angle — until the wing stalls.",
    "route": ["VECC", "VECC"],
    "legs_nm": [12.0],
    "note_nm": "A 12 NM box around Dum Dum (not a great-circle city pair).",
    "wind_kt": 5,
    "wind_from": 180,
    "tick_min": 1.0,
    "pressure": "low",
    "decisions_per_tick": 2,
    "info_level": 1,
    "adventure": "Keep 800–1500 ft on the side view. Do not stall. Land with fuel left.",
    "events": [
      {"at_nm": 3, "type": "hint", "text": "Downwind. Throttle back a little. The side view should flatten."},
      {"at_nm": 8, "type": "hint", "text": "Base to final. Nose down a touch. Speed is life."}
    ],
    "plan_fields": ["ete_min"],
    "pass": {"no_stall": true, "fuel_left": true, "alt_band": [600, 2000]},
    "stars": {"ete_error_pct": 25}
  },
  {
    "id": 2,
    "code": "S2_MAIL6",
    "title": "Six Miles of Mail",
    "rank_unlock": "Cadet",
    "theater": "South Asia",
    "aircraft": "trainer",
    "hook": "18 February 1911. Henri Pequet lifts a Humber biplane off Allahabad with 6,500 letters. Naini is six miles away.",
    "history": "This is treated as the world's first official airmail flight. Distance: about 6 miles / 9.7 km (5.2 NM).",
    "teach": "Time equals distance divided by speed.",
    "formula": "t = d / v    (hours = NM / knots; minutes = hours × 60)",
    "route": ["VEAB", "NAINI"],
    "legs_nm": [5.2],
    "note_nm": "5.2 NM is the documented 6-mile hop, not the raw coordinate pair.",
    "wind_kt": 0,
    "wind_from": 0,
    "tick_min": 0.5,
    "pressure": "low",
    "decisions_per_tick": 2,
    "info_level": 2,
    "adventure": "Compute ETE before you start. The whole hop fits on the side view.",
    "events": [
      {"at_nm": 2.5, "type": "callout", "city": "NAINI"}
    ],
    "plan_fields": ["ete_min", "fuel_gal"],
    "pass": {"no_stall": true, "fuel_left": true, "arrived": true},
    "stars": {"ete_error_pct": 15}
  },
  {
    "id": 3,
    "code": "S3_TATA",
    "title": "Tata's Beach",
    "rank_unlock": "Student Pilot",
    "theater": "South Asia",
    "aircraft": "puss",
    "hook": "15 October 1932. J.R.D. Tata flies mail Karachi–Ahmedabad–Juhu in a Puss Moth. You fly the last land leg.",
    "history": "That service became Tata Airlines, later Air India. Juhu (1928) was India's first civil aerodrome.",
    "teach": "Fuel required = burn × hours + reserve. A headwind makes hours longer.",
    "formula": "fuel = burn_gph × (distance / groundspeed) + reserve",
    "route": ["VAAH", "VAJJ"],
    "legs_nm": [239.1],
    "note_nm": "Haversine Ahmedabad–Juhu.",
    "wind_kt": 12,
    "wind_from": 210,
    "tick_min": 4.0,
    "pressure": "medium",
    "decisions_per_tick": 3,
    "info_level": 3,
    "adventure": "Headwind on the nose. If you planned with TAS instead of groundspeed, you will arrive thin on fuel.",
    "events": [
      {"at_nm": 80, "type": "weather", "text": "The wind picks up 6 kt. Recheck groundspeed in your head.", "wind_add": 6},
      {"at_nm": 200, "type": "callout", "city": "VAJJ"}
    ],
    "plan_fields": ["ete_min", "fuel_gal", "gs_kt"],
    "pass": {"no_stall": true, "fuel_above_reserve": true, "arrived": true},
    "stars": {"ete_error_pct": 12}
  },
  {
    "id": 4,
    "code": "S4_TRUNK",
    "title": "Eastern Trunk",
    "rank_unlock": "Student Pilot",
    "theater": "South Asia",
    "aircraft": "puss",
    "hook": "Imperial and Indian Trans-Continental used Jodhpur–Delhi–Cawnpore–Allahabad–Calcutta. You fly Delhi–Allahabad–Kolkata.",
    "history": "Calcutta was an overnight stop on the London–Australia path from 1933.",
    "teach": "Add legs. Total time is the sum. City cards fire inside 25 NM.",
    "formula": "total_d = d1 + d2     total_t = total_d / gs",
    "route": ["VIDP", "VEAB", "VECC"],
    "legs_nm": [310.5, 404.2],
    "note_nm": "Haversine Delhi–Prayagraj–Kolkata.",
    "wind_kt": 8,
    "wind_from": 280,
    "tick_min": 5.0,
    "pressure": "medium",
    "decisions_per_tick": 3,
    "info_level": 4,
    "adventure": "Two landings. A city card at Allahabad. Do not skip the fuel top-off decision.",
    "events": [
      {"at_nm": 280, "type": "callout", "city": "VEAB"},
      {"at_nm": 310.5, "type": "turnaround", "text": "Allahabad. Top off? A missed top-off is a later fuel emergency."},
      {"at_nm": 650, "type": "callout", "city": "VECC"}
    ],
    "plan_fields": ["ete_min", "fuel_gal", "legs_sum_nm"],
    "pass": {"no_stall": true, "fuel_above_reserve": true, "arrived": true},
    "stars": {"ete_error_pct": 10}
  },
  {
    "id": 5,
    "code": "S5_HIMALAYA",
    "title": "Himalaya Gate",
    "rank_unlock": "Private",
    "theater": "South Asia",
    "aircraft": "puss",
    "hook": "Cargo went Calcutta–Bagdogra on 21 May 1927. Beyond the tea gardens the wall of the Himalaya stands up. Then the valley at Kathmandu.",
    "history": "Bagdogra sits in the Siliguri corridor. Kathmandu field sits near 4,390 ft. Thin air is not a metaphor.",
    "teach": "Density altitude: high + hot = less lift. Same indicated speed, weaker climb.",
    "formula": "If lift < weight, you descend — even with the nose up.",
    "route": ["VECC", "VEBD", "VNKT"],
    "legs_nm": [241.8, 169.9],
    "note_nm": "Haversine Kolkata–Bagdogra–Kathmandu.",
    "wind_kt": 15,
    "wind_from": 270,
    "tick_min": 4.0,
    "pressure": "medium-high",
    "decisions_per_tick": 4,
    "info_level": 5,
    "adventure": "Build-ups on the second leg. If you pull the nose up to out-climb the hills at low speed, you stall.",
    "events": [
      {"at_nm": 220, "type": "callout", "city": "VEBD"},
      {"at_nm": 260, "type": "weather", "text": "Cu build-ups over the first ridges. Stay below the anvil, above the floor.", "turb": true},
      {"at_nm": 390, "type": "physics", "text": "Valley elevation. Climb gradient dies. Lower the nose, add power.", "density": true},
      {"at_nm": 400, "type": "callout", "city": "VNKT"}
    ],
    "plan_fields": ["ete_min", "fuel_gal", "gs_kt"],
    "pass": {"no_stall": true, "fuel_above_reserve": true, "arrived": true},
    "stars": {"ete_error_pct": 10}
  },
  {
    "id": 6,
    "code": "S6_SILVER",
    "title": "Silver Wing",
    "rank_unlock": "Private",
    "theater": "Europe",
    "aircraft": "silver",
    "hook": "Croydon to Le Bourget. The first dense international airway. Meals on the 1927 Silver Wing. You also have traffic.",
    "history": "Croydon became London's customs airport on 29 March 1920. Lindbergh landed at Le Bourget 21 May 1927.",
    "teach": "ATC spacing: stay at least 3 NM behind the aircraft ahead. Time zones: Paris is UTC+1 when London is UTC+0 (standard).",
    "formula": "time_to_close = extra_distance / extra_speed",
    "route": ["EGCR", "LFPB"],
    "legs_nm": [173.6],
    "note_nm": "Haversine Croydon–Le Bourget.",
    "wind_kt": 18,
    "wind_from": 250,
    "tick_min": 2.0,
    "pressure": "high",
    "decisions_per_tick": 4,
    "info_level": 6,
    "adventure": "Traffic 8 NM ahead at your speed. Slow 20 kt or the merge fails.",
    "events": [
      {"at_nm": 40, "type": "atc", "text": "Traffic 8 NM ahead, same level, same speed. Slow to open 3 NM by Le Bourget.", "need_slow": 20},
      {"at_nm": 150, "type": "callout", "city": "LFPB"}
    ],
    "plan_fields": ["ete_min", "fuel_gal", "gs_kt", "spacing_action"],
    "pass": {"no_stall": true, "fuel_above_reserve": true, "arrived": true, "spacing_ok": true},
    "stars": {"ete_error_pct": 8}
  },
  {
    "id": 7,
    "code": "S7_MAILSTRING",
    "title": "Mail String",
    "rank_unlock": "Cross-Country",
    "theater": "Europe",
    "aircraft": "silver",
    "hook": "2 November 1929. Imperial turns the India mail north: London–Cologne–Nuremberg–Vienna–Budapest–…–Athens.",
    "history": "You fly the German–Austrian–Hungarian beads. Four cities. Wind changes at each border.",
    "teach": "Recompute groundspeed when the wind card flips. Four callouts, no pause unless you pin.",
    "formula": "GS ≈ TAS − headwind   (use the new wind each leg)",
    "route": ["EDDK", "EDDN", "LOWW", "LHBP"],
    "legs_nm": [172.1, 232.5, 116.0],
    "note_nm": "Haversine Cologne–Nuremberg–Vienna–Budapest.",
    "wind_kt": 10,
    "wind_from": 270,
    "tick_min": 3.0,
    "pressure": "high",
    "decisions_per_tick": 5,
    "info_level": 7,
    "adventure": "Wind flips at Nuremberg (now 20 kt on the nose) and again at Vienna (10 kt tail). If you keep the first plan, fuel dies.",
    "events": [
      {"at_nm": 150, "type": "callout", "city": "EDDN"},
      {"at_nm": 172.1, "type": "weather", "text": "Nuremberg. Wind now 20 kt on the nose.", "wind_set": 20, "wind_from": 280},
      {"at_nm": 390, "type": "callout", "city": "LOWW"},
      {"at_nm": 404.6, "type": "weather", "text": "Vienna. Tail 10 kt. Do not overspeed the descent.", "wind_set": 10, "wind_from": 100},
      {"at_nm": 500, "type": "callout", "city": "LHBP"}
    ],
    "plan_fields": ["ete_min", "fuel_gal", "legs_sum_nm", "gs_kt"],
    "pass": {"no_stall": true, "fuel_above_reserve": true, "arrived": true},
    "stars": {"ete_error_pct": 8}
  },
  {
    "id": 8,
    "code": "S8_BOAT",
    "title": "Boat Chain",
    "rank_unlock": "Cross-Country",
    "theater": "Europe",
    "aircraft": "boat",
    "hook": "March 1937. Short Empire boats leave Southampton Water. The old path toward Athens ran the Middle Sea: Marseille, Naples, Brindisi.",
    "history": "Brindisi is where many Imperial passengers left the train and returned to a flying boat.",
    "teach": "Long water. Fuel is the adventure. Side view is hull over sea, not wheels over dirt.",
    "formula": "endurance_h = (fuel − reserve) / burn",
    "route": ["EGHI", "LFML", "LIRN", "LIBR", "LGAV"],
    "legs_nm": [524.3, 431.5, 166.8, 322.9],
    "note_nm": "Haversine Southampton–Marseille–Naples–Brindisi–Athens.",
    "wind_kt": 16,
    "wind_from": 300,
    "tick_min": 6.0,
    "pressure": "high",
    "decisions_per_tick": 5,
    "info_level": 8,
    "adventure": "Mistral at Marseille. A fuel-leak event after Naples (burn +15%). Divert Brindisi or press with new math.",
    "events": [
      {"at_nm": 500, "type": "callout", "city": "LFML"},
      {"at_nm": 530, "type": "weather", "text": "Mistral. North wind 28 kt. Inbound groundspeed collapses.", "wind_set": 28, "wind_from": 350},
      {"at_nm": 940, "type": "callout", "city": "LIRN"},
      {"at_nm": 960, "type": "emergency", "text": "Fuel smell. Burn is 15% high. Recompute endurance to Brindisi and Athens.", "burn_mult": 1.15},
      {"at_nm": 1120, "type": "callout", "city": "LIBR"},
      {"at_nm": 1400, "type": "callout", "city": "LGAV"}
    ],
    "plan_fields": ["ete_min", "fuel_gal", "endurance_h", "divert"],
    "pass": {"no_stall": true, "fuel_above_reserve": true, "arrived": true},
    "stars": {"ete_error_pct": 7}
  },
  {
    "id": 9,
    "code": "S9_ATLANTIC",
    "title": "Atlantic Door",
    "rank_unlock": "Airline Cadet",
    "theater": "Europe",
    "aircraft": "dakota",
    "hook": "Dublin opened 19 January 1942. Shannon took the ocean. Foynes boats had already made this estuary the door to the Atlantic.",
    "history": "First scheduled transatlantic through Shannon: 24 October 1945. Duty-free airport: 1947.",
    "teach": "Point of no return. If remaining fuel cannot cover both onward and back, you have already decided.",
    "formula": "PNR when fuel_to_go = fuel_to_return",
    "route": ["EIDW", "EINN"],
    "legs_nm": [105.8],
    "note_nm": "Haversine Dublin–Shannon, then a 40-minute west hold over water.",
    "hold_min": 40,
    "wind_kt": 22,
    "wind_from": 250,
    "tick_min": 2.0,
    "pressure": "very-high",
    "decisions_per_tick": 6,
    "info_level": 9,
    "adventure": "After landing Shannon you must hold west 40 min (range practice). Mid-hold: engine roughness, burn +25%. Turn back or continue the hold — you have 30 seconds of sim time to pick.",
    "events": [
      {"at_nm": 90, "type": "callout", "city": "EINN"},
      {"at_nm": 105.8, "type": "hold", "text": "Shannon below. Turn west. 40 minutes. Count fuel every tick."},
      {"at_hold_min": 18, "type": "emergency", "text": "Roughness. Burn +25%. TURN BACK or FINISH HOLD. Now.", "burn_mult": 1.25, "immediate": true}
    ],
    "plan_fields": ["ete_min", "fuel_gal", "endurance_h", "pnr_min"],
    "pass": {"no_stall": true, "fuel_above_reserve": true, "hold_survived": true},
    "stars": {"ete_error_pct": 6}
  },
  {
    "id": 10,
    "code": "S10_LONGHOP",
    "title": "The Long Hop",
    "rank_unlock": "Explorer",
    "theater": "Europe + South Asia",
    "aircraft": "jet",
    "hook": "London to Kolkata. You may land only in Europe and South Asia. The dashed historic track is drawn. The middle is water and time.",
    "history": "Imperial's real beads ran Mediterranean and Gulf. This game will not open those theaters. Athens is the last European land. Karachi is the first South Asian land.",
    "teach": "Stack everything: legs, wind flips, time zones (London UTC+0 → Athens +2 → Karachi +5 → India +5:30), ATC spacing, monsoon, density at Delhi.",
    "formula": "local_arrival = depart + ETE + zone_shift",
    "route": ["EGLL", "LGAV", "OPKC", "VIDP", "VECC"],
    "legs_nm": [1310.1, 2324.7, 576.0, 708.7],
    "note_nm": "Haversine London–Athens–Karachi–Delhi–Kolkata. Corridor Athens–Karachi is overflight only.",
    "wind_kt": 40,
    "wind_from": 270,
    "tick_min": 8.0,
    "pressure": "maximum",
    "decisions_per_tick": 7,
    "info_level": 10,
    "adventure": "Jetstream tail out of London. ATC merge into Athens. Corridor night. Heat at Karachi. Fog threat at Delhi. Monsoon cell on final to Dum Dum. You do not get a quiet tick.",
    "events": [
      {"at_nm": 400, "type": "weather", "text": "Jetstream. Tailwind 60 kt. Recalculate Athens ETA.", "wind_set": 60, "wind_from": 270},
      {"at_nm": 1200, "type": "atc", "text": "Athens arrivals. Traffic 6 NM ahead. Do not close inside 3 NM.", "need_slow": 30},
      {"at_nm": 1280, "type": "callout", "city": "LGAV"},
      {"at_nm": 1310.1, "type": "turnaround", "text": "Athens. Last European land. Corridor next. No city cards until Karachi."},
      {"at_nm": 2500, "type": "hint", "text": "Overwater. The dashed Imperial / KLM track is under you. Do not invent a field."},
      {"at_nm": 3550, "type": "callout", "city": "OPKC"},
      {"at_nm": 3600, "type": "physics", "text": "Karachi heat. Climb is lazy. Nose up will stall you.", "density": true},
      {"at_nm": 4100, "type": "weather", "text": "Delhi. Visibility dropping. If you miss, fuel must cover a hold.", "wind_set": 8, "wind_from": 320},
      {"at_nm": 4180, "type": "callout", "city": "VIDP"},
      {"at_nm": 4800, "type": "weather", "text": "Monsoon cell on the Hooghly. Deviate 12 NM or ride turbulence.", "turb": true},
      {"at_nm": 4880, "type": "callout", "city": "VECC"}
    ],
    "plan_fields": ["ete_min", "fuel_gal", "legs_sum_nm", "gs_kt", "arrival_local"],
    "pass": {"no_stall": true, "fuel_above_reserve": true, "arrived": true, "spacing_ok": true},
    "stars": {"ete_error_pct": 5}
  }
]
"""

EMBEDDED_AIRCRAFT = """{
  "trainer": {
    "name": "Cadet 12",
    "type": "single-engine trainer",
    "cruise_kt": 85,
    "stall_kt": 48,
    "max_thrust_factor": 1.0,
    "burn_gph": 8.0,
    "fuel_cap_gal": 28,
    "reserve_gal": 4,
    "wing_area_note": "high-lift trainer wing"
  },
  "puss": {
    "name": "Mail Moth",
    "type": "mail monoplane (Puss Moth class)",
    "cruise_kt": 95,
    "stall_kt": 52,
    "max_thrust_factor": 1.0,
    "burn_gph": 9.5,
    "fuel_cap_gal": 42,
    "reserve_gal": 6,
    "wing_area_note": "thin mail wing"
  },
  "silver": {
    "name": "Silver Wing",
    "type": "1920s airliner class",
    "cruise_kt": 140,
    "stall_kt": 62,
    "max_thrust_factor": 1.05,
    "burn_gph": 48,
    "fuel_cap_gal": 220,
    "reserve_gal": 24,
    "wing_area_note": "biplane airliner"
  },
  "boat": {
    "name": "Empire Boat",
    "type": "flying boat (Short Empire class)",
    "cruise_kt": 145,
    "stall_kt": 68,
    "max_thrust_factor": 1.05,
    "burn_gph": 72,
    "fuel_cap_gal": 520,
    "reserve_gal": 40,
    "wing_area_note": "hull + high wing"
  },
  "dakota": {
    "name": "Dakota Mail",
    "type": "twin transport",
    "cruise_kt": 160,
    "stall_kt": 64,
    "max_thrust_factor": 1.1,
    "burn_gph": 80,
    "fuel_cap_gal": 480,
    "reserve_gal": 40,
    "wing_area_note": "transport wing"
  },
  "jet": {
    "name": "Cadet Jet",
    "type": "early jet transport class",
    "cruise_kt": 420,
    "stall_kt": 110,
    "max_thrust_factor": 1.2,
    "burn_gph": 1400,
    "fuel_cap_gal": 12000,
    "reserve_gal": 800,
    "wing_area_note": "swept jet wing"
  }
}
"""


def _read_json(name: str, embedded: str):
    for folder in (HERE, Path.cwd().resolve(), HERE / "data", Path.cwd() / "data"):
        path = folder / name
        if path.is_file():
            with open(path, encoding="utf-8") as f:
                return json.load(f)
    return json.loads(embedded)


st.set_page_config(
    page_title="SkyQuest",
    page_icon="✈",
    layout="wide",
    initial_sidebar_state="expanded",
)

CITIES = _read_json("cities.json", EMBEDDED_CITIES)
STAGES = _read_json("stages.json", EMBEDDED_STAGES)
AIRCRAFT = _read_json("aircraft.json", EMBEDDED_AIRCRAFT)


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
Put `app.py` and `requirements.txt` on the repo root of `main`.
Game data is embedded in `app.py`, so missing JSON files will not crash Cloud.
Optional at the same level: `cities.json`, `stages.json`, `aircraft.json`.
Streamlit Cloud: branch `main` → main file `app.py` → Reboot after push.
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
