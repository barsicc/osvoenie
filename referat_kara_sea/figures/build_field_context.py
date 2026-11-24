"""Собрать обзорную карту с условными подписями групп по S107 и S417."""
import argparse
import json
from math import cos, radians
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Polygon

WEST, EAST, SOUTH, NORTH = 52, 90, 68, 81
REFERENCE_PARALLEL = 75
LONGITUDE_FACTOR = cos(radians(REFERENCE_PARALLEL))


def x(longitude):
    return (longitude - WEST) * LONGITUDE_FACTOR


def draw_land(ax, geojson):
    for feature in geojson["features"]:
        geometry = feature["geometry"]
        coordinates = geometry["coordinates"]
        polygons = coordinates if geometry["type"] == "MultiPolygon" else [coordinates]
        for polygon in polygons:
            exterior = polygon[0]
            longitudes, latitudes = zip(*exterior)
            if (
                max(longitudes) < WEST
                or min(longitudes) > EAST
                or max(latitudes) < SOUTH
                or min(latitudes) > NORTH
            ):
                continue
            ax.add_patch(
                Polygon(
                    [(x(lon), lat) for lon, lat in exterior],
                    facecolor="#e8e3d6",
                    edgecolor="#77867c",
                    linewidth=0.65,
                )
            )


def group(ax, lon, lat, label):
    ax.text(
        x(lon), lat, label, color="white", ha="center", va="center",
        fontsize=14, weight="bold",
        bbox={"boxstyle": "circle,pad=0.35", "facecolor": "#164c56", "edgecolor": "white"},
    )


def draw_map(fig, geojson):
    ax = fig.add_axes([0.065, 0.13, 0.525, 0.72])
    ax.set_facecolor("#eaf4f8")
    ax.set_xlim(x(WEST), x(EAST))
    ax.set_ylim(SOUTH, NORTH)
    ax.set_aspect("equal")
    ax.set_xticks([x(lon) for lon in (55, 65, 75, 85)], ["55°", "65°", "75°", "85°"])
    ax.set_yticks((70, 72, 74, 76, 78, 80), [f"{lat}°" for lat in (70, 72, 74, 76, 78, 80)])
    ax.tick_params(axis="both", labelsize=9, colors="#536c71", length=0, pad=5)
    ax.grid(color="#cedfe4", linewidth=0.65, zorder=0)
    for spine in ax.spines.values():
        spine.set_color("#a5bcc1")
    draw_land(ax, geojson)

    ax.text(x(75), 77.85, "Карское море", ha="center", fontsize=15, color="#28596a", style="italic")
    ax.text(x(57.2), 73.1, "Новая Земля", rotation=55, ha="center", fontsize=10, color="#263b40")
    ax.text(x(70), 70.8, "Ямал", ha="center", fontsize=10, color="#263b40")
    ax.annotate(
        "Обская и\nТазовская губы",
        (x(74.1), 69.2), xytext=(x(79.5), 68.68),
        ha="left", va="center", fontsize=9, color="#35555b",
        arrowprops={"arrowstyle": "-", "color": "#617d82"},
        annotation_clip=False,
    )
    group(ax, 65.8, 75.8, "Б")
    group(ax, 66.6, 72.9, "А")


def draw_labels(fig):
    fig.text(0.60, 0.78, "А  Приямальский шельф", fontsize=15, weight="bold", color="#164c56")
    fig.text(
        0.60, 0.72,
        "Русановское\nим. В. А. Динкова\nЛенинградское\nНярмейское\nим. 75 лет Победы",
        fontsize=13, va="top", linespacing=1.46, color="#162c32",
    )
    fig.text(0.60, 0.43, "Б  Восточно-Приновоземельский\n     сектор", fontsize=14, weight="bold", color="#164c56")
    fig.text(
        0.60, 0.37,
        "Победа\nим. маршала Г. К. Жукова\nим. маршала К. К. Рокоссовского",
        fontsize=13, va="top", linespacing=1.46, color="#162c32",
    )


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("land_geojson", type=Path, help="Natural Earth ne_50m_land.geojson, v5.1.2")
    parser.add_argument("output", type=Path, help="Файл PNG")
    args = parser.parse_args()
    fig = plt.figure(figsize=(11.2, 7.2), facecolor="white")
    fig.text(0.065, 0.93, "Группы месторождений южной части Карского моря", fontsize=19, weight="bold", color="#162c32")
    fig.text(0.065, 0.884, "Открытый шельф", fontsize=12, color="#38545a")
    draw_map(fig, json.loads(args.land_geojson.read_text(encoding="utf-8")))
    draw_labels(fig)
    fig.text(
        0.065, 0.056, "Буквы обозначают группы. Координаты скважин и контуры залежей не нанесены.",
        fontsize=10, color="#38545a",
    )
    fig.text(
        0.065, 0.029, "Береговая основа: Natural Earth 1:50 млн (S683). Группировка: S107, с. 141–144 и S417, абз. 1–4.",
        fontsize=9, color="#38545a",
    )
    fig.savefig(args.output, dpi=215)
    plt.close(fig)


if __name__ == "__main__":
    main()
