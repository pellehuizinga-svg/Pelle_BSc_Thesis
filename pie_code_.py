# -*- coding: utf-8 -*-
"""
Created on Thu Jun 18 19:49:44 2026

@author: Pelle Huizinga
"""

import geopandas as gpd
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import pandas as pd
import numpy as np
import os

# === LOAD ===
folder = os.path.dirname(os.path.abspath(__file__))

sentinel = gpd.read_file(r"C:\Users\Pelle Huizinga\Downloads\shapefiles_v2 (1)\shapefiles_v2 (1)\Shapefile_SENTINEL_FINAL.shp")
vintage  = gpd.read_file(r"C:\Users\Pelle Huizinga\Downloads\shapefiles_v2 (1)\shapefiles_v2 (1)\Shapefile_VINTAGE_FINAL.shp")

# Reproject to same CRS if needed
if sentinel.crs != vintage.crs:
    vintage = vintage.to_crs(sentinel.crs)

# Clip sentinel to the vintage boundary
vintage_boundary = vintage.dissolve()
sentinel_clipped = sentinel.clip(vintage_boundary)

color_map = {
    "Cloud": "#ffffff",
    "Coral": "#e8a0a0",
    "Grass": "#7ec87e",
    "Land":  "#c8a464",
    "Sand":  "#f5e6a0",
    "Water": "#4ab8d8",
}

# Shared extent from vintage only
b = vintage.total_bounds
pad_x = (b[2] - b[0]) * 0.02
pad_y = (b[3] - b[1]) * 0.02

geo_width  = (b[2] - b[0]) + 2 * pad_x
geo_height = (b[3] - b[1]) + 2 * pad_y
aspect = geo_height / geo_width

# === FIGURE 2: SIDE BY SIDE MAPS ===
fig, axes = plt.subplots(1, 2, figsize=(16, 16 * aspect * 0.5))
fig.patch.set_facecolor("#1a1a2e")

for ax, gdf, title in zip(axes, [vintage, sentinel_clipped], ["Vintage Final", "Sentinel Final (clipped)"]):
    ax.set_facecolor("#1a1a2e")
    for class_name, group in gdf.groupby("Class_name"):
        color = color_map.get(class_name, "#cccccc")
        group.plot(ax=ax, color=color, edgecolor="none")

    ax.set_xlim(b[0] - pad_x, b[2] + pad_x)
    ax.set_ylim(b[1] - pad_y, b[3] + pad_y)
    ax.set_title(title, fontsize=13, fontweight="bold", color="white")
    ax.set_aspect("equal")
    ax.axis("off")

    patches = [mpatches.Patch(color=color_map.get(c, "#cccccc"), label=c)
               for c in color_map if c in gdf["Class_name"].values]
    ax.legend(handles=patches, loc="lower right", fontsize=8,
              framealpha=0.8, facecolor="#2a2a3e", labelcolor="white")

plt.tight_layout()
plt.show()

# === FIGURE 2: PIE CHARTS ===
fig2, axes2 = plt.subplots(1, 2, figsize=(14, 7))
fig2.patch.set_facecolor("#1a1a2e")

for ax, gdf, title in zip(axes2, [vintage, sentinel_clipped], ["Vintage Final", "Sentinel Final (clipped)"]):
    areas = gdf.groupby("Class_name")["geometry"].apply(lambda x: x.area.sum())
    colors = [color_map.get(c, "#cccccc") for c in areas.index]
    ax.pie(areas, labels=areas.index, colors=colors, autopct="%1.1f%%",
           textprops={"color": "white"})
    ax.set_title(title, fontsize=13, fontweight="bold", color="white")

plt.tight_layout()
plt.show()

# === FIGURE 3: BAR CHART ===
fig3, ax = plt.subplots(figsize=(10, 6))
fig3.patch.set_facecolor("#1a1a2e")
ax.set_facecolor("#1a1a2e")

sent_areas = sentinel_clipped.groupby("Class_name")["geometry"].apply(lambda x: x.area.sum())
vint_areas = vintage.groupby("Class_name")["geometry"].apply(lambda x: x.area.sum())

df = pd.DataFrame({"Sentinel": sent_areas, "Vintage": vint_areas}).fillna(0)

x = range(len(df))
width = 0.35
ax.bar([i - width/2 for i in x], df["Vintage"],  width, label="Vintage",  color="#c8964a")
ax.bar([i + width/2 for i in x], df["Sentinel"], width, label="Sentinel", color="#4ab8d8")

ax.set_xticks(list(x))
ax.set_xticklabels(df.index, color="white", fontsize=11)
ax.set_ylabel("Area (m²)", color="white")
ax.set_title("Class Area: Vintage → Sentinel", fontsize=13, fontweight="bold", color="white")
ax.tick_params(colors="white")
ax.legend(facecolor="#2a2a3e", labelcolor="white")
ax.spines[["top", "right"]].set_visible(False)
for spine in ["left", "bottom"]:
    ax.spines[spine].set_color("white")

plt.tight_layout()
plt.show()

# === PRINT: AREA PER CLASS ===
for cls, row in df.iterrows():
    print(f"{cls}: Vintage={row['Vintage']:,.0f} m²  Sentinel={row['Sentinel']:,.0f} m²")

# === PRINT: PERCENTAGE CHANGE ===
df["Change (%)"] = ((df["Sentinel"] - df["Vintage"]) / df["Vintage"] * 100).round(1)

for cls, row in df.iterrows():
    sign = "+" if row["Change (%)"] > 0 else ""
    print(f"{cls}: {sign}{row['Change (%)']}%")

# === PRINT: TOTAL RESEARCH AREA ===
total_area_m2  = vintage.geometry.area.sum()
total_area_km2 = total_area_m2 / 1_000_000
print(f"\nTotal research area: {total_area_km2:.2f} km²")

# === PRINT: EDGE EFFECT DISTANCE BANDS ===
bands  = [0, 50, 100, 200, 500]

print("\nDistance from edge | Change rate")
print("-----------------------------------")

for i in range(len(bands) - 1):
    inner = vintage_boundary.buffer(-bands[i])
    outer = vintage_boundary.buffer(-bands[i + 1])
    band  = gpd.GeoDataFrame(geometry=inner.difference(outer), crs=vintage.crs)

    sent_band = sentinel_clipped.clip(band)
    vint_band = vintage.clip(band)

    sent_area = sent_band.groupby("Class_name")["geometry"].apply(lambda x: x.area.sum())
    vint_area = vint_band.groupby("Class_name")["geometry"].apply(lambda x: x.area.sum())

    all_classes = set(sent_area.index) | set(vint_area.index)
    changed = sum(abs(sent_area.get(c, 0) - vint_area.get(c, 0)) for c in all_classes)
    total   = vint_band.geometry.area.sum()

    print(f"  {bands[i]:>4}-{bands[i+1]}m       | {changed/total*100:.1f}% change")

# === PRINT & PLOT: EDi + LANDSCAPE METRICS ===
vintage["dist_to_edge"]         = vintage.geometry.centroid.distance(vintage_boundary.boundary.iloc[0])
sentinel_clipped["dist_to_edge"] = sentinel_clipped.geometry.centroid.distance(vintage_boundary.boundary.iloc[0])

vintage["complexity"]          = vintage.geometry.length / vintage.geometry.area
sentinel_clipped["complexity"] = sentinel_clipped.geometry.length / sentinel_clipped.geometry.area

bin_labels = ["0-50m", "50-100m", "100-200m", "200-500m", "500m+"]
bin_edges  = [0, 50, 100, 200, 500, 99999]

for name, gdf in [("Vintage", vintage), ("Sentinel", sentinel_clipped)]:
    print(f"\n=== {name} ===")

    for cls in gdf["Class_name"].unique():
        subset = gdf[gdf["Class_name"] == cls].copy()
        subset["area"]      = subset.geometry.area
        subset["perimeter"] = subset.geometry.length
        subset["EDi"]       = subset["perimeter"] / subset["area"]

        total_area = subset["area"].sum()
        max_area   = subset["area"].max()
        np_count   = len(subset)
        mpa        = subset["area"].mean()
        lpi        = (max_area / total_area) * 100
        ed         = subset["perimeter"].sum() / total_area
        edi_median = subset["EDi"].median()

        print(f"  {cls:<8} | NP={np_count:>5} | MPA={mpa:>10,.0f} m² | LPI={lpi:>5.1f}% | ED={ed:.4f} | EDi median={edi_median:.4f}")

# === FIGURE 5: EDGE EFFECT PATCH METRICS BY DISTANCE BAND ===
summaries = {}
for name, gdf in [("Vintage", vintage), ("Sentinel", sentinel_clipped)]:
    gdf["band"] = pd.cut(gdf["dist_to_edge"], bins=bin_edges, labels=bin_labels)
    summaries[name] = gdf.groupby("band", observed=True).agg(
        patch_count      =("geometry", "count"),
        avg_patch_size_m2=("geometry", lambda x: x.area.mean()),
        avg_complexity   =("complexity", "mean")
    )

fig6, axes6 = plt.subplots(1, 3, figsize=(16, 5))
fig6.patch.set_facecolor("#1a1a2e")

metrics = ["patch_count", "avg_patch_size_m2", "avg_complexity"]
titles  = ["Patch Count", "Avg Patch Size (m²)", "Avg Shape Complexity"]
x       = range(len(bin_labels))
width   = 0.35

for ax, metric, title in zip(axes6, metrics, titles):
    ax.set_facecolor("#1a1a2e")
    ax.bar([i - width/2 for i in x], summaries["Vintage"][metric],  width, label="Vintage",  color="#c8964a")
    ax.bar([i + width/2 for i in x], summaries["Sentinel"][metric], width, label="Sentinel", color="#4ab8d8")
    ax.set_xticks(list(x))
    ax.set_xticklabels(bin_labels, color="white", fontsize=8, rotation=15)
    ax.set_title(title, fontsize=11, fontweight="bold", color="white")
    ax.tick_params(colors="white")
    ax.legend(facecolor="#2a2a3e", labelcolor="white", fontsize=8)
    ax.spines[["top", "right"]].set_visible(False)
    for spine in ["left", "bottom"]:
        ax.spines[spine].set_color("white")

plt.suptitle("Edge Effect Analysis: Patch Metrics by Distance from Boundary",
             fontsize=13, fontweight="bold", color="white")
plt.tight_layout()
plt.show()

# === FIGURE 6: EDi DISTRIBUTION - GRASS (with outlier filter) ===
fig7, axes7 = plt.subplots(1, 2, figsize=(14, 5))
fig7.patch.set_facecolor("#1a1a2e")

for ax, name, gdf in zip(axes7, ["Vintage", "Sentinel"], [vintage, sentinel_clipped]):
    ax.set_facecolor("#1a1a2e")

    grass = gdf[gdf["Class_name"] == "Grass"].copy()
    grass["EDi"] = grass.geometry.length / grass.geometry.area

    cutoff          = grass["EDi"].quantile(0.95)
    grass_filtered  = grass[grass["EDi"] <= cutoff]

    ax.hist(grass_filtered["EDi"], bins=30, color=color_map["Grass"], edgecolor="none", alpha=0.8)
    ax.set_title(f"EDi Distribution - Grass ({name})", fontsize=11, fontweight="bold", color="white")
    ax.set_xlabel("EDi (perimeter/area)", color="white")
    ax.set_ylabel("Number of patches", color="white")
    ax.tick_params(colors="white")
    ax.spines[["top", "right"]].set_visible(False)
    for spine in ["left", "bottom"]:
        ax.spines[spine].set_color("white")

plt.tight_layout()
plt.show()

# === FIGURE 7: PATCH SIZE DISTRIBUTION - GRASS ===
fig8, axes8 = plt.subplots(1, 2, figsize=(14, 5))
fig8.patch.set_facecolor("#1a1a2e")

for ax, name, gdf in zip(axes8, ["Vintage", "Sentinel"], [vintage, sentinel_clipped]):
    ax.set_facecolor("#1a1a2e")

    grass = gdf[gdf["Class_name"] == "Grass"].copy()
    grass["log_area"] = np.log10(grass.geometry.area)

    ax.hist(grass["log_area"], bins=30, color=color_map["Grass"], edgecolor="none", alpha=0.8)
    ax.set_title(f"Patch Size Distribution - Grass ({name})", fontsize=11, fontweight="bold", color="white")
    ax.set_xlabel("Log10(Area m²)", color="white")
    ax.set_ylabel("Number of patches", color="white")
    ax.tick_params(colors="white")
    ax.spines[["top", "right"]].set_visible(False)
    for spine in ["left", "bottom"]:
        ax.spines[spine].set_color("white")

plt.tight_layout()
plt.show()
