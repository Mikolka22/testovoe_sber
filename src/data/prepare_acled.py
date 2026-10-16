import pandas as pd

acled = pd.read_excel("data/raw/acled.xlsx")
gdelt = pd.read_csv("data/raw/gdelt.csv")

gdelt["week_start"] = pd.to_datetime(gdelt["week_start"])

israel = acled.loc[
    acled["COUNTRY"] == "Israel",
    ["WEEK", "EVENT_TYPE", "EVENTS", "FATALITIES"],
].copy()

israel["WEEK"] = pd.to_datetime(israel["WEEK"])

# проверка недель в acled
required_acled_weeks = (
    gdelt["week_start"] - pd.Timedelta(days=9)
)
assert required_acled_weeks.isin(israel["WEEK"]).all(), (
    "в исходных данных acled отсутствуют необходимые недели"
)

selected = israel[
    israel["EVENT_TYPE"].isin([
        "Battles",
        "Explosions/Remote violence",
    ])
].copy()

# сумма событий по регионам
acled_weekly = selected.pivot_table(
    index="WEEK",
    columns="EVENT_TYPE",
    values="EVENTS",
    aggfunc="sum",
    fill_value=0,
)

acled_weekly = acled_weekly.rename(columns={
    "Battles": "acled_battles",
    "Explosions/Remote violence": "acled_explosions",
})

acled_weekly["acled_fatalities"] = (
    selected.groupby("WEEK")["FATALITIES"].sum()
)

all_acled_weeks = (
    israel["WEEK"]
    .drop_duplicates()
    .sort_values()
)

acled_weekly = acled_weekly.reindex(
    all_acled_weeks,
    fill_value=0,
)

acled_weekly = (
    acled_weekly
    .rename_axis("acled_week_start")
    .reset_index()
)

acled_weekly.columns.name = None

# задержка публикации
acled_weekly["week_start"] = (
    acled_weekly["acled_week_start"] + pd.Timedelta(days=9)
)

# количества событий за пять дней.
acled_weekly["acled_battles_overlap_estimate"] = (
    acled_weekly["acled_battles"] * 5 / 7
)

acled_weekly["acled_explosions_overlap_estimate"] = (
    acled_weekly["acled_explosions"] * 5 / 7
)

acled_columns = [
    "acled_battles_overlap_estimate",
    "acled_explosions_overlap_estimate",
    "acled_fatalities",
]

acled_for_merge = acled_weekly[
    ["week_start", "acled_week_start"] + acled_columns
]

merged = gdelt.merge(
    acled_for_merge,
    on="week_start",
    how="left",
    validate="one_to_one",
)

merged = merged.sort_values("week_start").reset_index(drop=True)

merged.to_csv(
    "data/processed/israel_weekly_merged.csv",
    index=False,
)
