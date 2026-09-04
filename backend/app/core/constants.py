"""Stable, model-independent API constants."""

DEPTHS_M = [30, 50, 75, 100, 125, 150, 200, 250, 300, 400, 500, 600,
            700, 800, 900, 1000, 1100, 1200, 1300, 1400, 1500, 1750, 2000]
GRID_LATITUDES = tuple(-89.5 + index for index in range(180))
GRID_LONGITUDES = tuple(0.5 + index for index in range(360))
INPUT_SHAPE = (3, 180, 360, 2)
OUTPUT_SHAPE = (180, 360, 23)
INPUT_CHANNELS = ["SST", "SSH/SLA"]
