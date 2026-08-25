"""
Cultivation Advisory Service
─────────────────────────────
Provides a DOA-aligned crop agronomic knowledge base covering:
  - Seasonal suitability (Maha / Yala / Year-Round)
  - Step-by-step 6-stage cultivation timeline
  - Basal and top-dressing fertilizer schedules (per acre)
  - Integrated Pest & Disease Management (IPM) protocols

Data is structured as a static, curated agronomic dictionary validated
against Department of Agriculture Sri Lanka crop production guidelines.
"""

from __future__ import annotations
from typing import Optional

# ─────────────────────────────────────────────────────────────────────────────
# AGRONOMIC KNOWLEDGE BASE — DOA Sri Lanka Validated Protocols
# ─────────────────────────────────────────────────────────────────────────────

CROP_DB: dict[str, dict] = {
    "tomato": {
        "id": "tomato",
        "name": "Tomato",
        "botanical_name": "Solanum lycopersicum",
        "emoji": "🍅",
        "seasons": ["Maha", "Yala", "Year-Round"],
        "soil_types": ["Reddish Brown Earth", "Sandy Loam", "Alluvial"],
        "ideal_ph": "6.0 – 6.8",
        "water_requirement": "Moderate (Irrigation / Agrowell)",
        "growth_days": 110,
        "nursery_days": 25,
        "plant_spacing_cm": "60 × 60",
        "yield_per_acre_tons_min": 12.0,
        "yield_per_acre_tons_max": 18.0,
        "estimated_cost_per_acre_lkr": 320000,
        "avg_wholesale_price_lkr_per_kg": 95.0,
        "market_demand": "Very High",
        "risk_level": "Medium",
        "roi_estimate_pct": 65,
        "timeline_stages": [
            {
                "stage": 1,
                "name": "Land Preparation",
                "weeks": "Week 1 – 2",
                "actions": [
                    "Deep plough to 30 cm, remove weeds and previous crop residues.",
                    "Apply 5–6 MT/acre of well-decomposed compost or cattle manure.",
                    "Form raised beds (1.2 m wide, 20 cm high) or flat beds with drainage furrows.",
                    "Pre-water the soil 2 days before planting to settle compost.",
                    "Apply lime if soil pH is below 6.0 (2–4 bags/acre, target pH 6.5)."
                ]
            },
            {
                "stage": 2,
                "name": "Nursery & Seed Management",
                "weeks": "Week 2 – 4",
                "actions": [
                    "Prepare polythene bag nursery with sterilized coco peat + compost (1:1).",
                    "Sow 1 seed per bag at 1 cm depth; recommended varieties: KC-1, Ravi, T-245.",
                    "Maintain nursery under 50% shade net to prevent damping-off.",
                    "Water twice daily using watering can (avoid overhead irrigation).",
                    "Apply Previcur / Ridomil at 0.2% concentration if damping-off appears.",
                    "Seedlings ready for transplant at 15–18 cm height (~Day 25)."
                ]
            },
            {
                "stage": 3,
                "name": "Field Transplanting",
                "weeks": "Week 4 – 5",
                "actions": [
                    "Transplant seedlings in late afternoon to avoid wilting stress.",
                    "Spacing: 60 cm × 60 cm in single rows, or 75 cm × 45 cm for high density.",
                    "Apply DAP or TSP directly in planting hole (25 g/plant).",
                    "Water immediately after transplant; shade young plants for 2 days.",
                    "Apply basal dressing within 3 days of transplanting (see fertilizer schedule)."
                ]
            },
            {
                "stage": 4,
                "name": "Vegetative Growth & Staking",
                "weeks": "Week 5 – 9",
                "actions": [
                    "Install bamboo stakes or wire trellis at Week 6 (plants reach 30 cm).",
                    "Prune lateral shoots below first flower truss (desuckering) for indeterminate varieties.",
                    "Apply 1st top dressing fertilizer at Week 3 after transplant.",
                    "Irrigate every 3–4 days; avoid waterlogging — leads to Bacterial Wilt.",
                    "Monitor for Whitefly and Aphids (use yellow sticky traps).",
                    "Spray Neem Oil (5 ml/L) preventively at Week 6 and Week 8."
                ]
            },
            {
                "stage": 5,
                "name": "Flowering & Fruit Setting",
                "weeks": "Week 9 – 14",
                "actions": [
                    "Apply 2nd top dressing fertilizer at Week 9–10 (onset of flowering).",
                    "Apply Boron (Solubor 0.2%) foliar spray to improve fruit set.",
                    "Avoid excessive nitrogen during flowering (causes flower drop).",
                    "Inspect daily for Fruit Borer; apply Bacillus thuringiensis (BT) at first detection.",
                    "Monitor for Early Blight — spray Mancozeb 0.2% preventively.",
                    "Maintain soil moisture consistency to prevent Blossom End Rot."
                ]
            },
            {
                "stage": 6,
                "name": "Harvesting & Post-Harvest",
                "weeks": "Week 14 – 16",
                "actions": [
                    "Harvest when fruits turn light pink/red (for transport); fully red for local market.",
                    "Harvest every 3–4 days during peak season to maximize yield.",
                    "Use harvesting trays/crates to avoid bruising; grade A, B, and processing quality.",
                    "Apply 3rd top dressing after first harvest to extend yield for 3–4 more pickings.",
                    "Store at 12°C (cold chain) to extend shelf life to 7–10 days.",
                    "Deliver Grade A to Dambulla Economic Centre; Grade B/Processing to B2B factories."
                ]
            },
        ],
        "fertilizer_schedule": {
            "basal": {
                "timing": "At transplanting (Day 1)",
                "inputs": [
                    {"name": "Compost / Cattle Manure", "quantity": "5,000 kg/acre", "method": "Soil incorporation"},
                    {"name": "Urea (46% N)", "quantity": "25 kg/acre", "method": "Incorporated into bed"},
                    {"name": "Triple Super Phosphate (TSP)", "quantity": "60 kg/acre", "method": "Incorporated"},
                    {"name": "Muriate of Potash (MOP)", "quantity": "40 kg/acre", "method": "Incorporated"},
                ]
            },
            "top_dressing_1": {
                "timing": "3 weeks after transplanting",
                "inputs": [
                    {"name": "Urea (46% N)", "quantity": "30 kg/acre", "method": "Ring application"},
                    {"name": "Muriate of Potash (MOP)", "quantity": "25 kg/acre", "method": "Ring application"},
                ]
            },
            "top_dressing_2": {
                "timing": "At first flower bud appearance (Week 9–10)",
                "inputs": [
                    {"name": "Urea (46% N)", "quantity": "25 kg/acre", "method": "Ring application"},
                    {"name": "Muriate of Potash (MOP)", "quantity": "30 kg/acre", "method": "Ring application"},
                    {"name": "Calcium Nitrate", "quantity": "15 kg/acre", "method": "Foliar spray 0.5%"},
                    {"name": "Boron (Solubor)", "quantity": "0.2 kg/acre", "method": "Foliar spray 0.2%"},
                ]
            },
            "top_dressing_3": {
                "timing": "After first harvest (Week 14–15)",
                "inputs": [
                    {"name": "Urea (46% N)", "quantity": "20 kg/acre", "method": "Ring application"},
                    {"name": "Muriate of Potash (MOP)", "quantity": "20 kg/acre", "method": "Ring application"},
                ]
            }
        },
        "pests_and_diseases": [
            {
                "type": "pest",
                "name": "Whitefly (Bemisia tabaci)",
                "category": "Sucking Pest / TYLCV Vector",
                "symptoms": "Yellowing leaves, sticky honeydew deposit, sooty mold on leaves. Primary vector for Tomato Yellow Leaf Curl Virus.",
                "organic_control": "Yellow sticky traps (2/acre), Neem Oil spray 5 ml/L weekly, reflective silver mulch.",
                "chemical_control": "Imidacloprid 17.8% SL (0.5 ml/L) or Spirotetramat 240 SC (0.5 ml/L). Rotate insecticide class every 2 applications."
            },
            {
                "type": "pest",
                "name": "Tomato Fruit Borer (Helicoverpa armigera)",
                "category": "Lepidopteran Fruit Pest",
                "symptoms": "Small entry holes on developing fruits, caterpillar frass (black droppings) at hole entry point.",
                "organic_control": "Pheromone traps (2–3/acre), Bacillus thuringiensis (BT) spray 1 g/L at egg hatching stage.",
                "chemical_control": "Chlorantraniliprole 18.5% SC (0.4 ml/L) or Emamectin Benzoate 5% SG (0.4 g/L)."
            },
            {
                "type": "pest",
                "name": "Aphids (Myzus persicae)",
                "category": "Foliage Pest",
                "symptoms": "Curled young leaves, sticky secretion, colony of soft-bodied insects on leaf undersides.",
                "organic_control": "Neem Oil 5 ml/L, soap spray (10 g/L), encourage natural predators (ladybird beetles).",
                "chemical_control": "Acetamiprid 20 SP (0.3 g/L) or Thiamethoxam 25 WG (0.3 g/L)."
            },
            {
                "type": "disease",
                "name": "Early Blight (Alternaria solani)",
                "category": "Fungal Leaf Disease",
                "symptoms": "Concentric ring spots (bull's-eye pattern) on older leaves starting from leaf tips. Spreads upward during wet weather.",
                "organic_control": "Trichoderma viride soil drench, avoid overhead irrigation, remove infected leaves promptly.",
                "chemical_control": "Mancozeb 75 WP (2.5 g/L) or Chlorothalonil 75 WP (2 g/L) spray every 10–14 days."
            },
            {
                "type": "disease",
                "name": "Bacterial Wilt (Ralstonia solanacearum)",
                "category": "Soil-Borne Vascular Disease",
                "symptoms": "Sudden, rapid wilting of entire plant in young growth stage. White bacterial ooze visible when stem is cut.",
                "organic_control": "Crop rotation (3+ years away from Solanaceae family), use grafted resistant rootstock, improve drainage.",
                "chemical_control": "No curative treatment available. Remove and burn infected plants immediately. Apply Copper Oxychloride to soil."
            },
            {
                "type": "disease",
                "name": "Late Blight (Phytophthora infestans)",
                "category": "Oomycete Blight",
                "symptoms": "Water-soaked grey-green lesions on leaves and stems. White fuzzy sporulation on leaf underside in humid conditions.",
                "organic_control": "Avoid evening irrigation, improve field air circulation, destroy infected plant material.",
                "chemical_control": "Metalaxyl + Mancozeb (Ridomil Gold) 2 g/L or Cymoxanil 8% + Mancozeb 64% (Curzate) 2.5 g/L."
            }
        ]
    },

    "carrot": {
        "id": "carrot",
        "name": "Carrot",
        "botanical_name": "Daucus carota",
        "emoji": "🥕",
        "seasons": ["Maha", "Yala"],
        "soil_types": ["Sandy Loam", "Reddish Brown Earth"],
        "ideal_ph": "6.0 – 6.8",
        "water_requirement": "Moderate (Drip / Agrowell)",
        "growth_days": 100,
        "nursery_days": 0,
        "plant_spacing_cm": "30 × 10",
        "yield_per_acre_tons_min": 8.0,
        "yield_per_acre_tons_max": 14.0,
        "estimated_cost_per_acre_lkr": 280000,
        "avg_wholesale_price_lkr_per_kg": 120.0,
        "market_demand": "High",
        "risk_level": "Low",
        "roi_estimate_pct": 72,
        "timeline_stages": [
            {"stage": 1, "name": "Land Preparation", "weeks": "Week 1 – 2",
             "actions": ["Deep plough to 40 cm for root penetration.", "Break up clods, remove stones.", "Apply 4 MT/acre compost.", "Form narrow raised beds (60 cm wide) with deep inter-row channels.", "Soil must be loose and well-drained — hard soil causes forked roots."]},
            {"stage": 2, "name": "Direct Seeding", "weeks": "Week 2",
             "actions": ["Mix seeds with fine sand (1:10) for uniform sowing.", "Sow at 1 cm depth in rows 30 cm apart.", "Press seeds gently into soil, cover with light compost.", "Mulch with paddy straw to retain moisture during germination."]},
            {"stage": 3, "name": "Thinning & Weeding", "weeks": "Week 3 – 5",
             "actions": ["Thin seedlings to 10 cm within rows at 3-leaf stage.", "Hand-weed twice during vegetative phase.", "Avoid deep cultivation near rows to prevent root damage."]},
            {"stage": 4, "name": "Vegetative Growth", "weeks": "Week 5 – 10",
             "actions": ["Apply 1st top dressing at Week 4.", "Irrigate every 4–5 days; avoid drought stress (causes cracking).", "Monitor for Carrot Fly and Leaf Blight.", "Hill up (earth up) around plant base at Week 6 to prevent green shoulders."]},
            {"stage": 5, "name": "Root Bulking", "weeks": "Week 10 – 14",
             "actions": ["Apply 2nd top dressing at Week 10.", "Reduce irrigation frequency slightly to concentrate sugars.", "Check roots by gentle soil probe — harvest when shoulder is 2–3 cm diameter."]},
            {"stage": 6, "name": "Harvesting", "weeks": "Week 14 – 16",
             "actions": ["Harvest by loosening soil around roots with fork.", "Grade: Large (>16 cm) export grade, Medium (10–16 cm) wholesale, Small (<10 cm) processing.", "Wash, trim tops to 2 cm, pack in ventilated crates.", "Store in cool shade or at 4–8°C for shelf life up to 4 weeks."]}
        ],
        "fertilizer_schedule": {
            "basal": {"timing": "At seeding (Day 1)",
                      "inputs": [
                          {"name": "Compost", "quantity": "4,000 kg/acre", "method": "Incorporated"},
                          {"name": "TSP", "quantity": "55 kg/acre", "method": "Incorporated"},
                          {"name": "MOP", "quantity": "35 kg/acre", "method": "Incorporated"},
                      ]},
            "top_dressing_1": {"timing": "4 weeks after seeding",
                               "inputs": [
                                   {"name": "Urea", "quantity": "25 kg/acre", "method": "Side dressing"},
                                   {"name": "MOP", "quantity": "20 kg/acre", "method": "Side dressing"},
                               ]},
            "top_dressing_2": {"timing": "10 weeks after seeding (root bulking stage)",
                               "inputs": [
                                   {"name": "Urea", "quantity": "20 kg/acre", "method": "Side dressing"},
                                   {"name": "MOP", "quantity": "25 kg/acre", "method": "Side dressing"},
                               ]},
        },
        "pests_and_diseases": [
            {"type": "pest", "name": "Carrot Fly (Psila rosae)", "category": "Root Maggot Pest",
             "symptoms": "Rusty-brown tunnels inside roots made by white maggots. Entry points visible at root crown.",
             "organic_control": "Crop rotation, companion planting with onions/chives, row covers during egg-laying season.",
             "chemical_control": "Soil drench with Chlorpyrifos 20 EC (2 ml/L) at thinning stage."},
            {"type": "disease", "name": "Leaf Blight (Alternaria dauci)", "category": "Fungal Foliage Disease",
             "symptoms": "Yellow, water-soaked spots on leaves that turn brown with yellow halos.",
             "organic_control": "Avoid overhead irrigation; ensure good air flow; remove affected leaves.",
             "chemical_control": "Mancozeb 75 WP (2.5 g/L) every 10 days."},
        ]
    },

    "green_beans": {
        "id": "green_beans",
        "name": "Green Beans",
        "botanical_name": "Phaseolus vulgaris",
        "emoji": "🫘",
        "seasons": ["Maha", "Yala", "Year-Round"],
        "soil_types": ["Sandy Loam", "Reddish Brown Earth", "Alluvial"],
        "ideal_ph": "6.0 – 7.0",
        "water_requirement": "Low to Moderate",
        "growth_days": 65,
        "nursery_days": 0,
        "plant_spacing_cm": "45 × 15",
        "yield_per_acre_tons_min": 3.0,
        "yield_per_acre_tons_max": 6.0,
        "estimated_cost_per_acre_lkr": 180000,
        "avg_wholesale_price_lkr_per_kg": 140.0,
        "market_demand": "High",
        "risk_level": "Low",
        "roi_estimate_pct": 80,
        "timeline_stages": [
            {"stage": 1, "name": "Land Preparation", "weeks": "Week 1", "actions": ["Plough to 20 cm. Apply 3 MT/acre compost. Form flat beds with good drainage."]},
            {"stage": 2, "name": "Direct Seeding", "weeks": "Week 1 – 2", "actions": ["Sow 2 seeds per station at 3 cm depth. Spacing: 45 cm between rows × 15 cm within rows.", "Germination occurs in 5–7 days."]},
            {"stage": 3, "name": "Vegetative Growth", "weeks": "Week 2 – 5", "actions": ["Apply basal dressing at sowing.", "Irrigate every 4–5 days. Bush varieties need no staking; pole types need trellis at Week 3.", "Monitor for Bean Fly."]},
            {"stage": 4, "name": "Flowering", "weeks": "Week 5 – 7", "actions": ["Apply 1st top dressing at Week 4.", "Avoid excess irrigation during flowering (causes flower drop).", "Spray micronutrient foliar to improve pod set."]},
            {"stage": 5, "name": "Pod Development", "weeks": "Week 7 – 9", "actions": ["Monitor for Pod Borer — apply BT at first damage signs.", "Harvest when pods snap cleanly (not soft or bulging with seeds)."]},
            {"stage": 6, "name": "Harvesting", "weeks": "Week 9 – 10", "actions": ["Harvest every 2–3 days during peak. Grade A: straight, 12–15 cm pods. Pack upright in crates with ventilation.", "Total harvest period: 3–4 weeks."]}
        ],
        "fertilizer_schedule": {
            "basal": {"timing": "At sowing", "inputs": [
                {"name": "Compost", "quantity": "3,000 kg/acre", "method": "Incorporated"},
                {"name": "TSP", "quantity": "45 kg/acre", "method": "Incorporated"},
                {"name": "MOP", "quantity": "30 kg/acre", "method": "Incorporated"},
            ]},
            "top_dressing_1": {"timing": "4 weeks after sowing", "inputs": [
                {"name": "Urea", "quantity": "20 kg/acre", "method": "Side dressing"},
                {"name": "MOP", "quantity": "15 kg/acre", "method": "Side dressing"},
            ]},
        },
        "pests_and_diseases": [
            {"type": "pest", "name": "Bean Fly (Ophiomyia phaseoli)", "category": "Stem Miner Pest",
             "symptoms": "Young seedling stems show water-soaked swelling at soil level, plants collapse at 2-leaf stage.",
             "organic_control": "Seed treatment with Trichoderma; avoid replanting Fabaceae family in same plot.",
             "chemical_control": "Imidacloprid seed treatment (5 ml/kg) or Dimethoate 40 EC soil drench (1 ml/L)."},
            {"type": "disease", "name": "Anthracnose (Colletotrichum lindemuthianum)", "category": "Fungal Pod Spot",
             "symptoms": "Dark sunken lesions on pods, stems, and leaves with pink spore masses in humid conditions.",
             "organic_control": "Use disease-free certified seeds, avoid wet foliage.",
             "chemical_control": "Carbendazim 50 WP (1 g/L) or Thiophanate Methyl (1 g/L) every 10 days."},
        ]
    },

    "eggplant": {
        "id": "eggplant",
        "name": "Eggplant (Brinjal)",
        "botanical_name": "Solanum melongena",
        "emoji": "🍆",
        "seasons": ["Maha", "Yala", "Year-Round"],
        "soil_types": ["Reddish Brown Earth", "Sandy Loam", "Alluvial", "Clay Loam"],
        "ideal_ph": "5.5 – 6.8",
        "water_requirement": "Moderate",
        "growth_days": 130,
        "nursery_days": 30,
        "plant_spacing_cm": "75 × 60",
        "yield_per_acre_tons_min": 10.0,
        "yield_per_acre_tons_max": 20.0,
        "estimated_cost_per_acre_lkr": 290000,
        "avg_wholesale_price_lkr_per_kg": 80.0,
        "market_demand": "High",
        "risk_level": "Low",
        "roi_estimate_pct": 75,
        "timeline_stages": [
            {"stage": 1, "name": "Land Preparation", "weeks": "Week 1 – 2", "actions": ["Plough to 25 cm. Apply 5 MT/acre compost. Form raised beds."]},
            {"stage": 2, "name": "Nursery Management", "weeks": "Week 2 – 5", "actions": ["Sow in polythene bags with coco peat. Recommended varieties: HORDI Lena, HORDI Padma.", "Shade with 50% net. Transplant at 20–25 cm height."]},
            {"stage": 3, "name": "Field Transplanting", "weeks": "Week 5 – 6", "actions": ["Transplant at 75 × 60 cm spacing. Apply basal dressing in planting holes."]},
            {"stage": 4, "name": "Vegetative Growth", "weeks": "Week 6 – 11", "actions": ["Stake at Week 7. Apply 1st top dressing at Week 4 after transplant.", "Monitor for Eggplant Shoot & Fruit Borer — most critical pest."]},
            {"stage": 5, "name": "Flowering & Fruit Set", "weeks": "Week 11 – 15", "actions": ["Apply 2nd top dressing. Harvest begins when fruits reach market size with glossy skin."]},
            {"stage": 6, "name": "Continuous Harvesting", "weeks": "Week 15 – 19", "actions": ["Harvest every 4–5 days. Apply 3rd top dressing after sustained harvesting begins.", "Production cycle may extend 5–6 months with good management."]}
        ],
        "fertilizer_schedule": {
            "basal": {"timing": "At transplanting", "inputs": [
                {"name": "Compost", "quantity": "5,000 kg/acre", "method": "Incorporated"},
                {"name": "Urea", "quantity": "20 kg/acre", "method": "Incorporated"},
                {"name": "TSP", "quantity": "60 kg/acre", "method": "Incorporated"},
                {"name": "MOP", "quantity": "40 kg/acre", "method": "Incorporated"},
            ]},
            "top_dressing_1": {"timing": "3 weeks after transplant", "inputs": [
                {"name": "Urea", "quantity": "30 kg/acre", "method": "Ring application"},
                {"name": "MOP", "quantity": "25 kg/acre", "method": "Ring application"},
            ]},
            "top_dressing_2": {"timing": "At first flowering", "inputs": [
                {"name": "Urea", "quantity": "25 kg/acre", "method": "Ring application"},
                {"name": "MOP", "quantity": "30 kg/acre", "method": "Ring application"},
                {"name": "Calcium Nitrate", "quantity": "12 kg/acre", "method": "Foliar spray"},
            ]},
        },
        "pests_and_diseases": [
            {"type": "pest", "name": "Eggplant Shoot & Fruit Borer (Leucinodes orbonalis)", "category": "Major Lepidopteran Pest",
             "symptoms": "Wilted growing tip (dead heart), entry holes with caterpillar frass on fruits.",
             "organic_control": "Pheromone traps (2/acre), remove and destroy infested shoots/fruits daily, Neem oil 5 ml/L.",
             "chemical_control": "Chlorantraniliprole 18.5% SC (0.3 ml/L) alternated with Spinosad 45 SC (0.5 ml/L)."},
            {"type": "disease", "name": "Phomopsis Fruit Rot", "category": "Fungal Fruit Rot",
             "symptoms": "Dark, sunken water-soaked spots on fruits enlarging rapidly in humid conditions.",
             "organic_control": "Improve drainage, avoid wetting fruits during irrigation.",
             "chemical_control": "Carbendazim 50 WP (1 g/L) spray every 14 days from fruiting."},
        ]
    },

    "cabbage": {
        "id": "cabbage",
        "name": "Cabbage",
        "botanical_name": "Brassica oleracea",
        "emoji": "🥬",
        "seasons": ["Maha", "Yala"],
        "soil_types": ["Sandy Loam", "Reddish Brown Earth", "Alluvial"],
        "ideal_ph": "6.0 – 7.0",
        "water_requirement": "Moderate to High",
        "growth_days": 90,
        "nursery_days": 25,
        "plant_spacing_cm": "45 × 45",
        "yield_per_acre_tons_min": 10.0,
        "yield_per_acre_tons_max": 16.0,
        "estimated_cost_per_acre_lkr": 260000,
        "avg_wholesale_price_lkr_per_kg": 55.0,
        "market_demand": "High",
        "risk_level": "Medium",
        "roi_estimate_pct": 58,
        "timeline_stages": [
            {"stage": 1, "name": "Land Preparation", "weeks": "Week 1 – 2", "actions": ["Plough to 30 cm. Apply 4 MT/acre compost. Lime if pH below 6.0."]},
            {"stage": 2, "name": "Nursery & Seedling", "weeks": "Week 2 – 5", "actions": ["Sow in seedbed or polythene bags. Varieties: KY Cross, Green Challenge.", "Transplant at 15 cm height with 6–8 true leaves."]},
            {"stage": 3, "name": "Field Transplanting", "weeks": "Week 5 – 6", "actions": ["Transplant at 45 × 45 cm spacing. Apply basal dressing at transplanting."]},
            {"stage": 4, "name": "Vegetative Expansion", "weeks": "Week 6 – 10", "actions": ["Apply 1st top dressing at Week 3 after transplant.", "Monitor for Diamondback Moth — most destructive pest for cabbage.", "Irrigate every 3–4 days."]},
            {"stage": 5, "name": "Head Formation (Hearting)", "weeks": "Week 10 – 13", "actions": ["Apply 2nd top dressing at Week 10. Avoid excess water (causes head splitting).", "Monitor for Black Rot — remove infected plants."]},
            {"stage": 6, "name": "Harvesting", "weeks": "Week 13 – 14", "actions": ["Harvest when head is firm and compact (80–90% density).", "Cut at base, retain 2–3 wrapper leaves. Grade by head weight.", "Market within 5 days of harvest (no cold chain needed for local market)."]}
        ],
        "fertilizer_schedule": {
            "basal": {"timing": "At transplanting", "inputs": [
                {"name": "Compost", "quantity": "4,000 kg/acre", "method": "Incorporated"},
                {"name": "Urea", "quantity": "20 kg/acre", "method": "Incorporated"},
                {"name": "TSP", "quantity": "55 kg/acre", "method": "Incorporated"},
                {"name": "MOP", "quantity": "35 kg/acre", "method": "Incorporated"},
            ]},
            "top_dressing_1": {"timing": "3 weeks after transplant", "inputs": [
                {"name": "Urea", "quantity": "30 kg/acre", "method": "Ring application"},
                {"name": "MOP", "quantity": "20 kg/acre", "method": "Ring application"},
            ]},
            "top_dressing_2": {"timing": "10 weeks after transplant (head initiation)", "inputs": [
                {"name": "Urea", "quantity": "20 kg/acre", "method": "Ring application"},
                {"name": "MOP", "quantity": "25 kg/acre", "method": "Ring application"},
            ]},
        },
        "pests_and_diseases": [
            {"type": "pest", "name": "Diamondback Moth (Plutella xylostella)", "category": "Major Brassica Pest",
             "symptoms": "Window paning damage on leaves (transparent patches), small holes through leaves.",
             "organic_control": "Bacillus thuringiensis (BT) spray 2 g/L weekly, Neem oil spray, yellow sticky traps.",
             "chemical_control": "Indoxacarb 14.5 SC (0.8 ml/L) or Spinosad 45 SC (0.5 ml/L) — rotate to avoid resistance."},
            {"type": "disease", "name": "Black Rot (Xanthomonas campestris)", "category": "Bacterial Foliage Disease",
             "symptoms": "V-shaped yellow lesions at leaf margins with dark veins. Affects head quality severely.",
             "organic_control": "Use certified disease-free seeds, avoid overhead irrigation, practice crop rotation.",
             "chemical_control": "Copper Oxychloride 50 WP (3 g/L) spray every 10 days."},
        ]
    },

    "green_chilli": {
        "id": "green_chilli",
        "name": "Green Chilli",
        "botanical_name": "Capsicum annuum",
        "emoji": "🌶️",
        "seasons": ["Maha", "Yala", "Year-Round"],
        "soil_types": ["Sandy Loam", "Reddish Brown Earth", "Alluvial"],
        "ideal_ph": "6.0 – 6.8",
        "water_requirement": "Moderate (Drip ideal)",
        "growth_days": 120,
        "nursery_days": 30,
        "plant_spacing_cm": "60 × 45",
        "yield_per_acre_tons_min": 5.0,
        "yield_per_acre_tons_max": 10.0,
        "estimated_cost_per_acre_lkr": 300000,
        "avg_wholesale_price_lkr_per_kg": 180.0,
        "market_demand": "Very High",
        "risk_level": "Medium",
        "roi_estimate_pct": 85,
        "timeline_stages": [
            {"stage": 1, "name": "Land Preparation", "weeks": "Week 1 – 2", "actions": ["Plough to 25 cm. Apply 4 MT/acre compost. Raised beds preferred."]},
            {"stage": 2, "name": "Nursery Management", "weeks": "Week 2 – 5", "actions": ["Sow in polythene bags. Varieties: MI-1, HORDI Golden Green.", "Transplant at 20 cm height with 6 true leaves."]},
            {"stage": 3, "name": "Field Transplanting", "weeks": "Week 5 – 6", "actions": ["Spacing 60 × 45 cm. Apply basal in planting holes. Install drip lines if available."]},
            {"stage": 4, "name": "Vegetative Growth", "weeks": "Week 6 – 10", "actions": ["Stake at Week 7. Apply 1st top dressing at Week 4 after transplant.", "Monitor for Thrips and Mites — key vectors for Chilli Mosaic Virus."]},
            {"stage": 5, "name": "Flowering & Fruit Set", "weeks": "Week 10 – 14", "actions": ["Apply 2nd top dressing. Ensure pollinator access.", "Monitor for Anthracnose on fruits during wet conditions."]},
            {"stage": 6, "name": "Harvesting", "weeks": "Week 14 – 20", "actions": ["Harvest green stage for fresh market; red stage for dried chilli.", "Harvest every 5–7 days. Yield continues for 4–6 months with maintenance."]}
        ],
        "fertilizer_schedule": {
            "basal": {"timing": "At transplanting", "inputs": [
                {"name": "Compost", "quantity": "4,000 kg/acre", "method": "Incorporated"},
                {"name": "Urea", "quantity": "20 kg/acre", "method": "Incorporated"},
                {"name": "TSP", "quantity": "55 kg/acre", "method": "Incorporated"},
                {"name": "MOP", "quantity": "35 kg/acre", "method": "Incorporated"},
            ]},
            "top_dressing_1": {"timing": "3–4 weeks after transplant", "inputs": [
                {"name": "Urea", "quantity": "28 kg/acre", "method": "Ring application"},
                {"name": "MOP", "quantity": "22 kg/acre", "method": "Ring application"},
            ]},
            "top_dressing_2": {"timing": "At first flower bud", "inputs": [
                {"name": "Urea", "quantity": "22 kg/acre", "method": "Ring application"},
                {"name": "MOP", "quantity": "28 kg/acre", "method": "Ring application"},
                {"name": "Boron (Solubor)", "quantity": "0.2%", "method": "Foliar spray"},
            ]},
        },
        "pests_and_diseases": [
            {"type": "pest", "name": "Thrips (Scirtothrips dorsalis)", "category": "Vector Pest",
             "symptoms": "Silvery streaks on leaves, distorted young shoots, bronzing of fruit surface.",
             "organic_control": "Blue/yellow sticky traps, Neem oil spray weekly, avoid drought stress.",
             "chemical_control": "Spinosad 45 SC (0.5 ml/L) or Fipronil 5 SC (1 ml/L)."},
            {"type": "disease", "name": "Chilli Anthracnose (Colletotrichum capsici)", "category": "Fungal Fruit Rot",
             "symptoms": "Sunken dark lesions with orange spore masses on ripe and ripening fruits.",
             "organic_control": "Avoid wetting fruits; collect and destroy infected fruits.",
             "chemical_control": "Carbendazim 50 WP (1 g/L) + Mancozeb 75 WP (2 g/L) combination spray."},
        ]
    }
}


# ─────────────────────────────────────────────────────────────────────────────
# SERVICE FUNCTIONS
# ─────────────────────────────────────────────────────────────────────────────

def get_all_crops() -> list[dict]:
    """Return high-level summary cards for all crops in the knowledge base."""
    summaries = []
    for crop in CROP_DB.values():
        summaries.append({
            "id": crop["id"],
            "name": crop["name"],
            "botanical_name": crop["botanical_name"],
            "emoji": crop["emoji"],
            "seasons": crop["seasons"],
            "soil_types": crop["soil_types"],
            "ideal_ph": crop["ideal_ph"],
            "water_requirement": crop["water_requirement"],
            "growth_days": crop["growth_days"],
            "yield_per_acre_tons_min": crop["yield_per_acre_tons_min"],
            "yield_per_acre_tons_max": crop["yield_per_acre_tons_max"],
            "estimated_cost_per_acre_lkr": crop["estimated_cost_per_acre_lkr"],
            "avg_wholesale_price_lkr_per_kg": crop["avg_wholesale_price_lkr_per_kg"],
            "market_demand": crop["market_demand"],
            "risk_level": crop["risk_level"],
            "roi_estimate_pct": crop["roi_estimate_pct"],
        })
    return summaries


def get_crop_guide(crop_id: str) -> Optional[dict]:
    """Return the complete agronomic guide for a specific crop."""
    return CROP_DB.get(crop_id)


def get_recommendations(
    season: str,
    soil_type: str,
    water_source: str,
    land_area_acres: float,
    centre_id: str,
) -> list[dict]:
    """
    Rank and return crop recommendations based on farm parameters.
    Scoring: ROI (40%) + Market Demand (30%) + Seasonal Fit (20%) + Soil Fit (10%)
    """
    demand_score = {"Very High": 30, "High": 22, "Medium": 14, "Low": 6}
    season_map = {"maha": "Maha", "yala": "Yala", "year-round": "Year-Round"}
    target_season = season_map.get(season.lower(), "Maha")

    results = []
    for crop in CROP_DB.values():
        # Seasonal suitability check
        seasonal_ok = (target_season in crop["seasons"]) or ("Year-Round" in crop["seasons"])
        seasonal_score = 20 if seasonal_ok else 0

        # Soil type check (fuzzy match)
        soil_match = any(
            target_soil.lower() in s.lower() or s.lower() in target_soil.lower()
            for s in crop["soil_types"]
            for target_soil in [soil_type]
        )
        soil_score = 10 if soil_match else 4

        # ROI and demand
        roi_score = int(crop["roi_estimate_pct"] * 0.40)
        d_score = demand_score.get(crop["market_demand"], 10)

        total_score = roi_score + d_score + seasonal_score + soil_score

        # Estimated revenue for the given land area
        avg_yield = (crop["yield_per_acre_tons_min"] + crop["yield_per_acre_tons_max"]) / 2
        total_yield = avg_yield * land_area_acres
        gross_revenue = total_yield * 1000 * crop["avg_wholesale_price_lkr_per_kg"]
        total_cost = crop["estimated_cost_per_acre_lkr"] * land_area_acres
        net_profit = gross_revenue - total_cost

        results.append({
            "id": crop["id"],
            "name": crop["name"],
            "botanical_name": crop["botanical_name"],
            "emoji": crop["emoji"],
            "score": total_score,
            "seasons": crop["seasons"],
            "growth_days": crop["growth_days"],
            "seasonal_fit": seasonal_ok,
            "soil_fit": soil_match,
            "avg_yield_tons": round(total_yield, 1),
            "estimated_gross_revenue_lkr": round(gross_revenue),
            "estimated_cost_lkr": round(total_cost),
            "estimated_net_profit_lkr": round(net_profit),
            "roi_estimate_pct": crop["roi_estimate_pct"],
            "risk_level": crop["risk_level"],
            "market_demand": crop["market_demand"],
            "avg_wholesale_price_lkr_per_kg": crop["avg_wholesale_price_lkr_per_kg"],
        })

    results.sort(key=lambda x: x["score"], reverse=True)
    return results
