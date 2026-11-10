"""Build one row per NYC community district from NYC Health Dept EH Data Portal files."""
import json, sys
import pandas as pd

root = sys.argv[1]; out = sys.argv[2]
tp = pd.DataFrame(json.load(open(f"{root}/indicators/metadata/TimePeriods.json")))[["TimePeriodID", "TimePeriod"]]

def get_geo(ind, measure, period, name, geotype):
    d = pd.DataFrame(json.load(open(f"{root}/indicators/data/{ind}.json")))
    d = d.merge(tp, on="TimePeriodID")
    d = d[(d.MeasureID == measure) & (d.GeoType == geotype) & (d.TimePeriod == period)]
    d = d[["GeoID", "Value"]].rename(columns={"Value": name})
    d["GeoID"] = d["GeoID"].astype(int)
    return d

def get(ind, measure, period, name):
    d = pd.DataFrame(json.load(open(f"{root}/indicators/data/{ind}.json")))
    d = d.merge(tp, on="TimePeriodID")
    d = d[(d.MeasureID == measure) & (d.GeoType == "CD") & (d.TimePeriod == period)]
    d = d[["GeoID", "Value"]].rename(columns={"Value": name})
    d["GeoID"] = d["GeoID"].astype(int)
    return d

names = pd.read_csv(f"{root}/geography/cd_names.csv").rename(columns={"geo_entity_id": "GeoID", "name": "district"})
boro = {1: "Bronx", 2: "Brooklyn", 3: "Manhattan", 4: "Queens", 5: "Staten Island"}
names["borough"] = names["borough_id"].map(boro)

df = names[["GeoID", "district", "borough"]]
for part in [
    get(2380, 1199, "2023", "asthma_ed_adult_ageadj"),   # adult asthma ED visits, age-adjusted per 10,000
    get(2379, 1196, "2023", "asthma_ed_child_5_17"),      # child (5-17) asthma ED visits per 10,000
    get(2023, 1425, "2023", "pm25"),                      # PM2.5 annual mean, ug/m3
    get(2025, 1431, "2023", "no2"),                       # NO2 annual mean, ppb
]:
    df = df.merge(part, on="GeoID", how="left")

# Poverty 2019-23 is published for 2020 Community District Tabulation Areas (CDTA), which closely
# follow community districts. Match them by borough + district number, e.g. "(CD 1)" in the Bronx -> 201.
look = pd.read_csv(f"{root}/geography/GeoLookup.csv")
cdta = look[look.GeoType == "CDTA2020"].copy()
cdta["cdnum"] = cdta["Name"].str.extract(r"\(CD (\d+)\)")[0].astype(int)
boro_code = {"Manhattan": 100, "Bronx": 200, "Brooklyn": 300, "Queens": 400, "Staten Island": 500}
cdta["CD_GeoID"] = cdta["Borough"].map(boro_code) + cdta["cdnum"]
pov = get_geo(103, 221, "2019-23", "poverty_pct", "CDTA2020").merge(cdta[["GeoID", "CD_GeoID"]], on="GeoID")
df = df.merge(pov[["CD_GeoID", "poverty_pct"]].rename(columns={"CD_GeoID": "GeoID"}), on="GeoID", how="left")
df.to_csv(out, index=False)
print(df.shape); print(df.isna().sum().to_string()); print(df.groupby("borough").size().to_string())
