# -*- coding: utf-8 -*-
"""
Created on Thu Jun 18 19:49:44 2026
@author: Pelle Huizinga

Corrected + fast (point-sampling) version. Edge-distance is measured from the
1943 seagrass patch edges. Cloud is excluded from the landscape-metric summary.
Figure 7 is a clean table (landscape metrics + distance summary) instead of a
console dump.
"""

import geopandas as gpd
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import pandas as pd
import numpy as np
import os

# LOAD
folder = os.path.dirname(os.path.abspath(__file__))

sentinel = gpd.read_file(r"C:\Users\Pelle Huizinga\Downloads\shapefiles_v2 (1)\shapefiles_v2 (1)\Shapefile_SENTINEL_FINAL.shp").explode(index_parts=False).reset_index(drop=True)
vintage  = gpd.read_file(r"C:\Users\Pelle Huizinga\Downloads\shapefiles_v2 (1)\shapefiles_v2 (1)\Shapefile_VINTAGE_FINAL.shp").explode(index_parts=False).reset_index(drop=True)

if sentinel.crs != vintage.crs:
    vintage = vintage.to_crs(sentinel.crs)

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

# EDGE REFERENCE GEOMETRY (computed once, reused everywhere)
SIMP = 10.0

study_geom     = vintage_boundary.geometry.iloc[0].buffer(0)
study_boundary = study_geom.boundary
study_s        = study_geom.simplify(SIMP)

grass_geom    = vintage[vintage["Class_name"] == "Grass"].dissolve().geometry.iloc[0].buffer(0)
grass_outline = grass_geom.boundary
edge_tol  = 2.0
real_edge = grass_outline.difference(study_boundary.buffer(edge_tol))
edge_s    = real_edge.simplify(SIMP)

# Shared extent from vintage only
b = vintage.total_bounds
pad_x = (b[2] - b[0]) * 0.02
pad_y = (b[3] - b[1]) * 0.02
geo_width  = (b[2] - b[0]) + 2 * pad_x
geo_height = (b[3] - b[1]) + 2 * pad_y
aspect = geo_height / geo_width

# FIGURE 1: SIDE BY SIDE MAPS
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

# FIGURE 2: PIE CHARTS
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

# FIGURE 3: BAR CHART
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

# PRINT: AREA PER CLASS
for cls, row in df.iterrows():
    print(f"{cls}: Vintage={row['Vintage']:,.0f} m²  Sentinel={row['Sentinel']:,.0f} m²")

# PRINT: PERCENTAGE CHANGE
df["Change (%)"] = ((df["Sentinel"] - df["Vintage"]) / df["Vintage"] * 100).round(1)
for cls, row in df.iterrows():
    sign = "+" if row["Change (%)"] > 0 else ""
    print(f"{cls}: {sign}{row['Change (%)']}%")

# PRINT: TOTAL RESEARCH AREA
total_area_km2 = vintage.geometry.area.sum() / 1_000_000
print(f"\nTotal research area: {total_area_km2:.2f} km²")

# CHANGE BY DISTANCE FROM SEAGRASS EDGE (point sampling)
GRID_STEP = 30.0

minx, miny, maxx, maxy = study_geom.bounds
xx, yy = np.meshgrid(np.arange(minx, maxx, GRID_STEP), np.arange(miny, maxy, GRID_STEP))
pts = gpd.GeoDataFrame(geometry=gpd.points_from_xy(xx.ravel(), yy.ravel()), crs=vintage.crs)
pts = pts[pts.within(study_s)].reset_index(drop=True)
pts["dist"] = pts.geometry.distance(edge_s)

def _classify(points, poly_gdf):
    j = gpd.sjoin(points[["geometry"]], poly_gdf[["Class_name", "geometry"]],
                  predicate="within", how="left")
    j = j[~j.index.duplicated(keep="first")]
    return j["Class_name"].reindex(points.index).values

pts["vint_cls"] = _classify(pts, vintage)
pts["sent_cls"] = _classify(pts, sentinel_clipped)
pts = pts.dropna(subset=["vint_cls", "sent_cls"]).copy()
pts["changed"] = pts["vint_cls"] != pts["sent_cls"]

band_edges  = [0, 50, 100, 200, 500]
band_labels = ["0-50m", "50-100m", "100-200m", "200-500m"]
pts["band"] = pd.cut(pts["dist"], bins=band_edges, labels=band_labels)

frac  = pts.groupby("band", observed=False)["changed"].mean() * 100
count = pts.groupby("band", observed=False)["changed"].count()
dist_summary = {str(k): float(v) for k, v in frac.items()}   # stored for Figure 7

print("\nDistance from seagrass patch edge | % of ground changed | n points")
print("------------------------------------------------------------------")
for lbl in band_labels:
    n = int(count.get(lbl, 0))
    if n == 0:
        print(f"  {lbl:<9} | (no points in band)")
    else:
        print(f"  {lbl:<9} | {dist_summary[lbl]:5.1f}% |  {n:>6}")

# LANDSCAPE METRICS (Cloud excluded)
def class_metrics(gdf, cls):
    sub  = gdf[gdf["Class_name"] == cls]
    area = sub.geometry.area
    per  = sub.geometry.length
    tot  = area.sum()
    return {
        "NP":  len(sub),
        "MPA": area.mean() if len(sub) else 0.0,
        "LPI": (area.max() / tot * 100) if tot else 0.0,
        "EDi": (per / area).median() if len(sub) else float("nan"),
    }

metrics = {}
for name, gdf in [("Vintage", vintage), ("Sentinel", sentinel_clipped)]:
    print(f"\n=== {name} ===")
    metrics[name] = {}
    for cls in [c for c in gdf["Class_name"].unique() if c != "Cloud"]:
        m = class_metrics(gdf, cls)
        metrics[name][cls] = m
        print(f"  {cls:<8} | NP={m['NP']:>5} | MPA={m['MPA']:>10,.0f} m² | LPI={m['LPI']:>5.1f}% | EDi median={m['EDi']:.4f}")

# FIGURE 7: LANDSCAPE METRICS + DISTANCE SUMMARY (clean table)
def arrow(v1, v2, fmt):
    return f"{format(v1, fmt)} \u2192 {format(v2, fmt)}"

table_classes = ["Grass", "Sand", "Coral"]
rows = []
for cls in table_classes:
    v, s = metrics["Vintage"][cls], metrics["Sentinel"][cls]
    rows.append([
        cls,
        arrow(v["NP"],  s["NP"],  ",d"),
        arrow(v["MPA"], s["MPA"], ",.0f"),
        arrow(v["LPI"], s["LPI"], ".1f"),
        arrow(v["EDi"], s["EDi"], ".3f"),
    ])
cols = ["Class", "NP (1943\u21922025)", "MPA m² (1943\u21922025)",
        "LPI % (1943\u21922025)", "EDi median (1943\u21922025)"]

dist_rows = [[lbl.replace("-", "\u2013") + " m" if "m" not in lbl else lbl.replace("-", "\u2013"),
              f"{dist_summary[lbl]:.1f}%"] for lbl in band_labels]

BG, FG, HDR = "#1a1a2e", "white", "#2a2a3e"
fig7 = plt.figure(figsize=(11, 4.2))
fig7.patch.set_facecolor(BG)

axm = fig7.add_axes([0.03, 0.42, 0.94, 0.5]); axm.axis("off")
axm.set_title("Landscape metrics per class", color=FG, fontsize=12, fontweight="bold", pad=8, loc="left")
tm = axm.table(cellText=rows, colLabels=cols, cellLoc="center", loc="center")
tm.auto_set_font_size(False); tm.set_fontsize(10); tm.scale(1, 1.6)
for (r, c), cell in tm.get_celld().items():
    cell.set_edgecolor("#44445a")
    if r == 0:
        cell.set_facecolor(HDR); cell.set_text_props(color=FG, fontweight="bold")
    else:
        cell.set_facecolor(BG); cell.set_text_props(color=FG)

axd = fig7.add_axes([0.03, 0.05, 0.55, 0.28]); axd.axis("off")
axd.set_title("Change with distance from seagrass edge (% of ground changed)",
              color=FG, fontsize=11, fontweight="bold", pad=6, loc="left")
td = axd.table(cellText=dist_rows, colLabels=["Distance band", "% changed"],
               cellLoc="center", loc="center")
td.auto_set_font_size(False); td.set_fontsize(10); td.scale(1, 1.5)
for (r, c), cell in td.get_celld().items():
    cell.set_edgecolor("#44445a")
    if r == 0:
        cell.set_facecolor(HDR); cell.set_text_props(color=FG, fontweight="bold")
    else:
        cell.set_facecolor(BG); cell.set_text_props(color=FG)

plt.show()

# Prepare per-patch distance + complexity for the by-band figure
vintage["dist_to_edge"]          = vintage.geometry.centroid.distance(edge_s)
sentinel_clipped["dist_to_edge"] = sentinel_clipped.geometry.centroid.distance(edge_s)
vintage["complexity"]            = vintage.geometry.length / vintage.geometry.area
sentinel_clipped["complexity"]   = sentinel_clipped.geometry.length / sentinel_clipped.geometry.area

bin_labels = ["0-50m", "50-100m", "100-200m", "200-500m", "500m+"]
bin_edges  = [0, 50, 100, 200, 500, 99999]

# FIGURE 4: PATCH METRICS BY DISTANCE FROM SEAGRASS EDGE
summaries = {}
for name, gdf in [("Vintage", vintage), ("Sentinel", sentinel_clipped)]:
    gdf["band"] = pd.cut(gdf["dist_to_edge"], bins=bin_edges, labels=bin_labels)
    summaries[name] = (
        gdf.groupby("band", observed=True)
           .agg(patch_count=("geometry", "count"),
                avg_patch_size_m2=("geometry", lambda x: x.area.mean()),
                avg_complexity=("complexity", "mean"))
           .reindex(bin_labels).fillna(0)
    )

fig4, axes4 = plt.subplots(1, 3, figsize=(16, 5))
fig4.patch.set_facecolor("#1a1a2e")
metrics_cols = ["patch_count", "avg_patch_size_m2", "avg_complexity"]
titles  = ["Patch Count", "Avg Patch Size (m²)", "Avg Shape Complexity"]
x = range(len(bin_labels)); width = 0.35
for ax, metric, title in zip(axes4, metrics_cols, titles):
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
plt.suptitle("Patch Metrics by Distance from Seagrass Edge", fontsize=13, fontweight="bold", color="white")
plt.tight_layout()
plt.show()

# FIGURE 5: EDi DISTRIBUTION - GRASS (95th-percentile outlier filter)
fig5, axes5 = plt.subplots(1, 2, figsize=(14, 5))
fig5.patch.set_facecolor("#1a1a2e")
for ax, name, gdf in zip(axes5, ["Vintage", "Sentinel"], [vintage, sentinel_clipped]):
    ax.set_facecolor("#1a1a2e")
    grass = gdf[gdf["Class_name"] == "Grass"].copy()
    grass["EDi"] = grass.geometry.length / grass.geometry.area
    cutoff = grass["EDi"].quantile(0.95)
    grass_f = grass[grass["EDi"] <= cutoff]
    ax.hist(grass_f["EDi"], bins=30, color=color_map["Grass"], edgecolor="none", alpha=0.8)
    ax.set_title(f"EDi Distribution - Grass ({name})", fontsize=11, fontweight="bold", color="white")
    ax.set_xlabel("EDi (perimeter/area)", color="white")
    ax.set_ylabel("Number of patches", color="white")
    ax.tick_params(colors="white")
    ax.spines[["top", "right"]].set_visible(False)
    for spine in ["left", "bottom"]:
        ax.spines[spine].set_color("white")
plt.tight_layout()
plt.show()

# FIGURE 6: PATCH SIZE DISTRIBUTION - GRASS
fig6, axes6 = plt.subplots(1, 2, figsize=(14, 5))
fig6.patch.set_facecolor("#1a1a2e")
for ax, name, gdf in zip(axes6, ["Vintage", "Sentinel"], [vintage, sentinel_clipped]):
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
