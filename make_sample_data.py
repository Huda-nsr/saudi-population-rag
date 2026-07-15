"""Generate synthetic-but-realistic Saudi population/census sample data so the
project runs immediately offline. Numbers are on the scale of the 2022 Census but
are SYNTHETIC (deterministic via seed). Comma-formatted numbers keep the cleaning
step honest. Replace with real open.data.gov.sa / GASTAT CSVs later (see CURATION.md)."""
import csv, pathlib, random

raw = pathlib.Path("data/raw"); raw.mkdir(parents=True, exist_ok=True)
random.seed(42)

# region -> approximate 2022 total population (synthetic, Census-scale)
REGIONS = {
    "Riyadh": 8_600_000, "Makkah": 8_540_000, "Eastern Province": 5_100_000,
    "Asir": 2_240_000, "Madinah": 2_130_000, "Qassim": 1_420_000, "Tabuk": 910_000,
}
YEARS = [2020, 2021, 2022]
NATIONAL_2022 = sum(REGIONS.values())


def comma(n):  # messy-but-realistic formatting: "8,600,000"
    return f"{int(round(n)):,}"


# 1) population by region x gender x year
with open(raw / "pop-by-region.csv", "w", newline="", encoding="utf-8") as f:
    w = csv.writer(f); w.writerow(["region", "gender", "year", "population"])
    for region, base in REGIONS.items():
        male_frac = 0.54 + random.random() * 0.05          # ~0.54-0.59 (expat skew)
        for y in YEARS:
            total = base * (1 + (y - 2022) * 0.018)         # earlier years slightly smaller
            male = total * male_frac
            w.writerow([region, "Male", y, comma(male)])
            w.writerow([region, "Female", y, comma(total - male)])

# 2) population by age group x gender (2022)
AGE_SHARES = {"0-14": 0.245, "15-24": 0.155, "25-39": 0.305, "40-64": 0.240, "65+": 0.055}
with open(raw / "pop-by-age-group.csv", "w", newline="", encoding="utf-8") as f:
    w = csv.writer(f); w.writerow(["age_group", "gender", "year", "population"])
    for grp, share in AGE_SHARES.items():
        grp_total = NATIONAL_2022 * share
        male_frac = 0.60 if grp in ("25-39", "40-64") else 0.51  # working-age expat skew
        male = grp_total * male_frac
        w.writerow([grp, "Male", 2022, comma(male)])
        w.writerow([grp, "Female", 2022, comma(grp_total - male)])

# 3) population by region x nationality (2022)
with open(raw / "pop-by-nationality.csv", "w", newline="", encoding="utf-8") as f:
    w = csv.writer(f); w.writerow(["region", "nationality", "year", "population"])
    for region, base in REGIONS.items():
        saudi_frac = 0.55 + random.random() * 0.20          # ~0.55-0.75 varies by region
        saudi = base * saudi_frac
        w.writerow([region, "Saudi", 2022, comma(saudi)])
        w.writerow([region, "Non-Saudi", 2022, comma(base - saudi)])

# land area per region (km2), roughly realistic — used for density
AREA_KM2 = {
    "Riyadh": 404_240, "Makkah": 153_148, "Eastern Province": 672_522,
    "Asir": 76_693, "Madinah": 151_990, "Qassim": 58_046, "Tabuk": 146_072,
}

# 4) households and average household size by region (2022)
with open(raw / "households-by-region.csv", "w", newline="", encoding="utf-8") as f:
    w = csv.writer(f); w.writerow(["region", "year", "households", "avg_household_size"])
    for region, base in REGIONS.items():
        avg_size = round(4.8 + random.random() * 1.4, 1)   # ~4.8-6.2 persons per household
        households = base / avg_size
        w.writerow([region, 2022, comma(households), avg_size])

# 5) population density by region (2022)
with open(raw / "population-density.csv", "w", newline="", encoding="utf-8") as f:
    w = csv.writer(f); w.writerow(["region", "year", "area_km2", "population", "density_per_km2"])
    for region, base in REGIONS.items():
        density = base / AREA_KM2[region]
        w.writerow([region, 2022, comma(AREA_KM2[region]), comma(base), round(density, 1)])

print("wrote 5 population sample CSVs to data/raw/")
for p in sorted(raw.glob("*.csv")):
    print("  ", p.name)
