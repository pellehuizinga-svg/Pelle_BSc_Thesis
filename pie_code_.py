import geopandas as gpd
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches

# Load
import os

folder = os.path.dirname(os.path.abspath(__file__))

sentinel = gpd.read_file(os.path.join(folder, "Shapefile_SENTINEL_FINAL.shp"))
vintage  = gpd.read_file(os.path.join(folder, "Shapefile_VINTAGE_FINAL.shp"))

# Reproject to same CRS if needed (was needed, slightly)
if sentinel.crs != vintage.crs:
    vintage = vintage.to_crs(sentinel.crs)

# Clip sentinel to the vintage boundary
vintage_boundary = vintage.dissolve()  # single polygon of full vintage extent
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

fig, axes = plt.subplots(1, 2, figsize=(16, 16 * aspect * 0.5))
fig.patch.set_facecolor("#1a1a2e")

for ax, gdf, title in zip(axes, [sentinel_clipped, vintage], ["Sentinel Final (clipped)", "Vintage Final"]):
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

#pie charts

fig2, axes2 = plt.subplots(1, 2, figsize=(14, 7))
fig2.patch.set_facecolor("#1a1a2e")

for ax, gdf, title in zip(axes2, [sentinel_clipped, vintage], ["Sentinel Final", "Vintage Final"]):
    areas = gdf.groupby("Class_name")["geometry"].apply(lambda x: x.area.sum())
    colors = [color_map.get(c, "#cccccc") for c in areas.index]
    ax.pie(areas, labels=areas.index, colors=colors, autopct="%1.1f%%",
           textprops={"color": "white"})
    ax.set_title(title, fontsize=13, fontweight="bold", color="white")

plt.tight_layout()
plt.show()

#bar charts toevoegen

fig3, ax = plt.subplots(figsize=(10, 6))
fig3.patch.set_facecolor("#1a1a2e")
ax.set_facecolor("#1a1a2e")

sent_areas = sentinel_clipped.groupby("Class_name")["geometry"].apply(lambda x: x.area.sum())
vint_areas = vintage.groupby("Class_name")["geometry"].apply(lambda x: x.area.sum())

import pandas as pd
df = pd.DataFrame({"Sentinel": sent_areas, "Vintage": vint_areas}).fillna(0)

x = range(len(df))
width = 0.35
bars1 = ax.bar([i - width/2 for i in x], df["Vintage"], width, label="Vintage", color="#c8964a")
bars2 = ax.bar([i + width/2 for i in x], df["Sentinel"], width, label="Sentinel", color="#4ab8d8")

ax.set_xticks(list(x))
ax.set_xticklabels(df.index, color="white", fontsize=11)
ax.set_ylabel("Area (m²)", color="white")
ax.set_title("Class Area: Vintage vs Sentinel", fontsize=13, fontweight="bold", color="white")
ax.tick_params(colors="white")
ax.legend(facecolor="#2a2a3e", labelcolor="white")
ax.spines[["top", "right"]].set_visible(False)
for spine in ["left", "bottom"]:
    ax.spines[spine].set_color("white")

plt.tight_layout()
plt.show()

#percentile changes printen

for cls, row in df.iterrows():
    print(f"{cls}: Vintage={row['Vintage']:,.0f} m²  Sentinel={row['Sentinel']:,.0f} m²")

sent_areas = sentinel_clipped.groupby("Class_name")["geometry"].apply(lambda x: x.area.sum())
vint_areas = vintage.groupby("Class_name")["geometry"].apply(lambda x: x.area.sum())

df = pd.DataFrame({"Vintage": vint_areas, "Sentinel": sent_areas}).fillna(0)
df["Change (%)"] = ((df["Sentinel"] - df["Vintage"]) / df["Vintage"] * 100).round(1)

for cls, row in df.iterrows():
    sign = "+" if row["Change (%)"] > 0 else ""
    print(f"{cls}: {sign}{row['Change (%)']}%")
## Edge effect in goede nogwat realiseren 

bands = [0, 50, 100, 200, 500]  # meters, willekeur

print("Distance from edge | Change rate")
print("-----------------------------------")

for i in range(len(bands)-1):
    inner = vintage_boundary.buffer(-bands[i])
    outer = vintage_boundary.buffer(-bands[i+1])
    band  = gpd.GeoDataFrame(geometry=inner.difference(outer), crs=vintage.crs)

    sent_band = sentinel_clipped.clip(band)
    vint_band = vintage.clip(band)

    sent_area = sent_band.groupby("Class_name")["geometry"].apply(lambda x: x.area.sum())
    vint_area = vint_band.groupby("Class_name")["geometry"].apply(lambda x: x.area.sum())

    all_classes = set(sent_area.index) | set(vint_area.index)
    changed = sum(abs(sent_area.get(c, 0) - vint_area.get(c, 0)) for c in all_classes)
    total   = vint_band.geometry.area.sum()

    print(f"  {bands[i]:>4}-{bands[i+1]}m       | {changed/total*100:.1f}% change")
 #resultaten lijken te wijzen op complicaties met geometric misalignment met vintage photo's, conclusie trekken dat edge effect analysis vanuit programeren minder handig is en beter naar grote structures gekekenen kan worden zoals de change map uit Arcgis
