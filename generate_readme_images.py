"""
Generate all README illustration images for OceanEmbed.
Run: python3 generate_readme_images.py
Output: public/*.png
"""
import os
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import matplotlib.patches as FancyArrowPatch
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch
from matplotlib.patheffects import withStroke
import matplotlib.gridspec as gridspec
from matplotlib.colors import LinearSegmentedColormap

OUT = "public"
os.makedirs(OUT, exist_ok=True)

DPI = 150
BG = "#0a0a0f"
FG = "#e0e0f0"
ACCENT = "#667eea"
ACCENT2 = "#26c6da"
ORANGE = "#ffa726"
RED = "#ef5350"
GREEN = "#66bb6a"

def savefig(name):
    plt.savefig(os.path.join(OUT, name), dpi=DPI, bbox_inches='tight',
                facecolor=BG, edgecolor='none')
    plt.close()
    print(f"  ✓ {name}")

# ─────────────────────────────────────────────────────────────────────────────
# 1. System Architecture diagram
# ─────────────────────────────────────────────────────────────────────────────
def make_architecture():
    fig, ax = plt.subplots(figsize=(13, 7), facecolor=BG)
    ax.set_facecolor(BG)
    ax.set_xlim(0, 13)
    ax.set_ylim(0, 7)
    ax.axis('off')

    def box(x, y, w, h, label, sublabel="", color=ACCENT, alpha=0.18):
        rect = FancyBboxPatch((x, y), w, h,
                              boxstyle="round,pad=0.12",
                              linewidth=1.8, edgecolor=color,
                              facecolor=color, alpha=alpha)
        ax.add_patch(rect)
        rect2 = FancyBboxPatch((x, y), w, h,
                               boxstyle="round,pad=0.12",
                               linewidth=1.8, edgecolor=color,
                               facecolor='none')
        ax.add_patch(rect2)
        ax.text(x + w/2, y + h/2 + (0.18 if sublabel else 0), label,
                ha='center', va='center', color=FG, fontsize=11, fontweight='bold',
                path_effects=[withStroke(linewidth=2, foreground=BG)])
        if sublabel:
            ax.text(x + w/2, y + h/2 - 0.26, sublabel,
                    ha='center', va='center', color=color, fontsize=8.5,
                    path_effects=[withStroke(linewidth=2, foreground=BG)])

    def arrow(x1, y1, x2, y2, label="", color=ACCENT2):
        ax.annotate("", xy=(x2, y2), xytext=(x1, y1),
                    arrowprops=dict(arrowstyle="-|>", color=color, lw=1.6))
        if label:
            mx, my = (x1+x2)/2, (y1+y2)/2
            ax.text(mx, my + 0.18, label, ha='center', va='bottom',
                    color=color, fontsize=8, style='italic',
                    path_effects=[withStroke(linewidth=2, foreground=BG)])

    # ── Row 1: Data sources ──────────────────────────────────────
    box(0.3,  5.3, 2.2, 1.1, "Satellite SST", "NetCDF grids", ACCENT2)
    box(2.9,  5.3, 2.2, 1.1, "Satellite SSH/SLA", "NetCDF grids", ACCENT2)

    # ── Row 2: Backend ───────────────────────────────────────────
    box(0.3,  3.5, 1.5, 1.2, "Temporal\nService", "window months", ACCENT, 0.22)
    box(2.1,  3.5, 1.5, 1.2, "SST / SSH\nRepos", "load + reindex", ACCENT, 0.22)
    box(3.9,  3.5, 1.5, 1.2, "Preprocessor", "fill NaN + norm", ACCENT, 0.22)
    box(5.7,  3.5, 1.8, 1.2, "ConvLSTM\nModel", "180×360×23", "#764ba2", 0.28)
    box(7.9,  3.5, 1.6, 1.2, "Location\nService", "extract profile", ACCENT, 0.22)

    # Backend border
    backend_rect = FancyBboxPatch((0.1, 3.3), 9.6, 1.7,
                                  boxstyle="round,pad=0.08",
                                  linewidth=1.2, edgecolor="#444466",
                                  facecolor='none', linestyle='--')
    ax.add_patch(backend_rect)
    ax.text(0.22, 5.05, "FastAPI Backend", color="#888899", fontsize=8.5, style='italic')

    # ── Row 3: API / Transport ───────────────────────────────────
    box(3.9, 1.85, 2.4, 1.0, "POST /api/v1/predict", "{lat, lon, month}", ORANGE, 0.18)

    # ── Row 4: Frontend ──────────────────────────────────────────
    box(0.4,  0.2, 2.0, 1.1, "3D Globe\n(Three.js)", "click → lat/lon", GREEN, 0.18)
    box(2.7,  0.2, 2.0, 1.1, "ocean-api.js", "fetch + validate", GREEN, 0.18)
    box(5.1,  0.2, 2.2, 1.1, "Depth Layers\nViz", "23 colored strata", GREEN, 0.18)
    box(7.6,  0.2, 2.2, 1.1, "Alarm Panel", "threshold alerts\n+ Telegram", RED, 0.18)

    frontend_rect = FancyBboxPatch((0.2, 0.05), 9.8, 1.4,
                                   boxstyle="round,pad=0.08",
                                   linewidth=1.2, edgecolor="#334433",
                                   facecolor='none', linestyle='--')
    ax.add_patch(frontend_rect)
    ax.text(0.32, 1.5, "React Frontend", color="#668866", fontsize=8.5, style='italic')

    # ── Arrows ───────────────────────────────────────────────────
    # data sources → repos
    arrow(1.4, 5.3, 1.4, 4.7, color=ACCENT2)
    arrow(4.0, 5.3, 3.0, 4.7, color=ACCENT2)
    # temporal → repos
    arrow(1.5, 3.5, 2.4, 3.5, color=FG)   # same row horizontal
    # repos → preprocessor
    arrow(3.6, 4.1, 3.9, 4.1, color=FG)
    # preprocessor → model
    arrow(5.4, 4.1, 5.7, 4.1, color=FG)
    # model → location
    arrow(7.5, 4.1, 7.9, 4.1, color=FG)
    # location → API response (down)
    arrow(8.7, 3.5, 6.5, 2.85, "profile JSON", color=ORANGE)
    # frontend click → API call
    arrow(3.7, 0.75, 4.5, 1.85, "{lat,lon,month}", color=ORANGE)
    # API response → viz
    arrow(5.7, 1.85, 6.0, 1.3, color=ORANGE)
    # globe → ocean-api
    arrow(2.4, 0.75, 2.7, 0.75, color=GREEN)
    # ocean-api → viz
    arrow(4.7, 0.75, 5.1, 0.75, color=GREEN)

    ax.set_title("OceanEmbed — System Architecture", color=FG, fontsize=15,
                 fontweight='bold', pad=10)
    savefig("architecture.png")

make_architecture()

# ─────────────────────────────────────────────────────────────────────────────
# 2. Model tensor I/O diagram
# ─────────────────────────────────────────────────────────────────────────────
def make_tensor_diagram():
    fig, ax = plt.subplots(figsize=(12, 5), facecolor=BG)
    ax.set_facecolor(BG)
    ax.set_xlim(0, 12)
    ax.set_ylim(0, 5)
    ax.axis('off')

    def cube(ax, ox, oy, w, h, d, color, label, sublabel="", alpha=0.7):
        # front face
        front = plt.Polygon([[ox, oy], [ox+w, oy], [ox+w, oy+h], [ox, oy+h]],
                             closed=True, facecolor=color, alpha=alpha,
                             edgecolor='white', linewidth=0.8)
        ax.add_patch(front)
        # top face
        top = plt.Polygon([[ox, oy+h], [ox+w, oy+h],
                           [ox+w+d*0.6, oy+h+d*0.4], [ox+d*0.6, oy+h+d*0.4]],
                          closed=True, facecolor=color, alpha=alpha*0.7,
                          edgecolor='white', linewidth=0.8)
        ax.add_patch(top)
        # right face
        right = plt.Polygon([[ox+w, oy], [ox+w+d*0.6, oy+d*0.4],
                             [ox+w+d*0.6, oy+h+d*0.4], [ox+w, oy+h]],
                            closed=True, facecolor=color, alpha=alpha*0.5,
                            edgecolor='white', linewidth=0.8)
        ax.add_patch(right)
        cx = ox + w/2
        cy = oy + h/2
        ax.text(cx, cy+0.15, label, ha='center', va='center', color='white',
                fontsize=10, fontweight='bold',
                path_effects=[withStroke(linewidth=2, foreground='black')])
        if sublabel:
            ax.text(cx, cy-0.3, sublabel, ha='center', va='center', color='white',
                    fontsize=8,
                    path_effects=[withStroke(linewidth=2, foreground='black')])

    # Input tensor: (1, 3, 180, 360, 2)
    # Draw as 3 stacked grids (3 months) with 2 channels each
    colors_in = ['#1565c0', '#0288d1', '#26c6da']
    labels_in = ['Jan', 'Feb', 'Mar']
    for i, (c, lbl) in enumerate(zip(colors_in, labels_in)):
        cube(ax, 0.4 + i*0.25, 0.8 + i*0.2, 2.6, 3.2, 0.5, c, lbl, "180×360")

    # Channel labels
    ax.text(1.7, 0.5, "Input  (1, 3, 180, 360, 2)", ha='center', color=ACCENT2,
            fontsize=10, fontweight='bold')
    ax.text(1.7, 0.15, "3 months × [SST, SSH/SLA] channels", ha='center',
            color=FG, fontsize=8.5, alpha=0.8)

    # Arrow
    ax.annotate("", xy=(5.6, 2.4), xytext=(4.0, 2.4),
                arrowprops=dict(arrowstyle="-|>", color=ORANGE, lw=2.5))
    ax.text(4.8, 2.85, "ConvLSTM\nInference", ha='center', va='center',
            color=ORANGE, fontsize=9, fontweight='bold')

    # Model box
    model_rect = FancyBboxPatch((5.7, 1.35), 2.1, 2.1,
                                boxstyle="round,pad=0.15",
                                linewidth=2, edgecolor="#764ba2",
                                facecolor="#764ba2", alpha=0.25)
    ax.add_patch(model_rect)
    ax.text(6.75, 2.4, "ConvLSTM\nModel", ha='center', va='center',
            color="#ce93d8", fontsize=10, fontweight='bold')

    # Arrow out
    ax.annotate("", xy=(8.3, 2.4), xytext=(7.8, 2.4),
                arrowprops=dict(arrowstyle="-|>", color=ORANGE, lw=2.5))

    # Output tensor: (1, 180, 360, 23)
    cube(ax, 8.4, 0.8, 2.8, 3.2, 0.7, '#2e7d32', "(1, 180, 360, 23)", "")
    ax.text(9.8, 0.5, "Output  (1, 180, 360, 23)", ha='center', color=GREEN,
            fontsize=10, fontweight='bold')
    ax.text(9.8, 0.15, "global temp field — 23 depths", ha='center',
            color=FG, fontsize=8.5, alpha=0.8)

    # Depth extraction callout
    ax.annotate("", xy=(11.3, 2.0), xytext=(11.3, 1.2),
                arrowprops=dict(arrowstyle="-|>", color=ACCENT, lw=1.5))
    ax.text(11.3, 0.9, "extract\nprofile\nat lat/lon", ha='center', color=ACCENT,
            fontsize=8, alpha=0.9)

    ax.set_title("ConvLSTM Model — Tensor Contract", color=FG, fontsize=14,
                 fontweight='bold', pad=8)
    savefig("model_tensor.png")

make_tensor_diagram()

# ─────────────────────────────────────────────────────────────────────────────
# 3. Depth–temperature profile (example output)
# ─────────────────────────────────────────────────────────────────────────────
def make_depth_profile():
    depths = [30, 50, 75, 100, 125, 150, 200, 250, 300,
              400, 500, 600, 700, 800, 900, 1000,
              1100, 1200, 1300, 1400, 1500, 1750, 2000]

    # Realistic-ish profile: warm surface, thermocline, cold deep
    temps = [28.1, 27.6, 26.8, 25.2, 23.1, 20.4, 16.2, 13.0, 10.8,
             8.2,  6.5,  5.3,  4.6,  4.1,  3.7,  3.4,
             3.2,  3.0,  2.9,  2.8,  2.7,  2.5,  2.3]

    # Color map: warm → cold
    cmap = LinearSegmentedColormap.from_list(
        'ocean', ['#0d47a1', '#1565c0', '#0288d1', '#26c6da',
                  '#80deea', '#ffe082', '#ffb300', '#ef6c00', '#b71c1c'])
    norm_t = np.array([(t - min(temps)) / (max(temps) - min(temps)) for t in temps])
    colors = [cmap(1 - v) for v in norm_t]   # cold deep = blue end

    fig, axes = plt.subplots(1, 2, figsize=(11, 7), facecolor=BG,
                             gridspec_kw={'width_ratios': [2, 1]})

    # Left: horizontal bars (depth layers)
    ax = axes[0]
    ax.set_facecolor(BG)
    bar_height = 0.75
    y_positions = list(range(len(depths)))

    for i, (d, t, c) in enumerate(zip(depths, temps, colors)):
        bar = ax.barh(y_positions[i], t, height=bar_height, color=c, alpha=0.85,
                      edgecolor='white', linewidth=0.4)
        ax.text(t + 0.3, y_positions[i], f"{t:.1f}°C",
                va='center', ha='left', color=FG, fontsize=8.5, fontweight='bold')

    ax.set_yticks(y_positions)
    ax.set_yticklabels([f"{d} m" for d in depths], color=FG, fontsize=9)
    ax.invert_yaxis()
    ax.set_xlabel("Temperature (°C)", color=FG, fontsize=10)
    ax.set_title("Temperature Profile\n(example output — 20.5°N, 75.5°E, 2020-03)",
                 color=FG, fontsize=11, fontweight='bold')
    ax.tick_params(colors=FG)
    ax.spines[:].set_color('#333355')
    ax.set_xlim(0, 35)
    ax.axvline(0, color='#333355', lw=0.8)
    ax.grid(axis='x', color='#1a1a2e', linewidth=0.6, alpha=0.6)

    # Right: vertical line plot (classic oceanographic style)
    ax2 = axes[1]
    ax2.set_facecolor(BG)
    ax2.plot(temps, depths, color=ACCENT2, lw=2.2, zorder=3)
    for t, d, c in zip(temps, depths, colors):
        ax2.scatter([t], [d], color=c, s=40, zorder=4, edgecolors='white', linewidths=0.4)
    ax2.invert_yaxis()
    ax2.set_xlabel("°C", color=FG, fontsize=9)
    ax2.set_ylabel("Depth (m)", color=FG, fontsize=9)
    ax2.set_title("Profile\n(classic view)", color=FG, fontsize=10, fontweight='bold')
    ax2.tick_params(colors=FG)
    ax2.spines[:].set_color('#333355')
    ax2.grid(color='#1a1a2e', linewidth=0.6, alpha=0.6)
    ax2.set_ylim(2100, 0)

    # Annotate thermocline
    ax2.axhspan(100, 300, color=ACCENT, alpha=0.08)
    ax2.text(max(temps)*0.55, 200, "thermocline", color=ACCENT, fontsize=8,
             alpha=0.85, style='italic')

    plt.tight_layout(pad=1.5)
    savefig("depth_profile.png")

make_depth_profile()

# ─────────────────────────────────────────────────────────────────────────────
# 4. Temperature → color scale
# ─────────────────────────────────────────────────────────────────────────────
def make_color_scale():
    fig, ax = plt.subplots(figsize=(10, 2.2), facecolor=BG)
    ax.set_facecolor(BG)

    cmap = LinearSegmentedColormap.from_list(
        'ocean', ['#0d47a1', '#1565c0', '#0288d1', '#26c6da',
                  '#80deea', '#ffe082', '#ffb300', '#ef6c00', '#b71c1c'])
    gradient = np.linspace(0, 1, 512).reshape(1, -1)
    ax.imshow(gradient, aspect='auto', cmap=cmap,
              extent=[2, 30, 0, 1])
    ax.set_yticks([])
    ticks = [2, 5, 8, 11, 14, 17, 20, 23, 26, 30]
    ax.set_xticks(ticks)
    ax.set_xticklabels([f"{t}°C" for t in ticks], color=FG, fontsize=9)
    ax.tick_params(colors=FG)
    ax.spines[:].set_color('#333355')

    # Labels
    ax.text(2.4, 0.5, "cold / deep", color='#90caf9', fontsize=9, va='center',
            fontweight='bold',
            path_effects=[withStroke(linewidth=2, foreground=BG)])
    ax.text(28.5, 0.5, "warm / surface", color='#ef9a9a', fontsize=9, va='center',
            ha='right', fontweight='bold',
            path_effects=[withStroke(linewidth=2, foreground=BG)])

    ax.set_title("Temperature → Color Mapping (layer visualization)", color=FG,
                 fontsize=11, fontweight='bold', pad=6)
    plt.tight_layout()
    savefig("color_scale.png")

make_color_scale()

# ─────────────────────────────────────────────────────────────────────────────
# 5. Request / response flow
# ─────────────────────────────────────────────────────────────────────────────
def make_request_flow():
    fig, ax = plt.subplots(figsize=(12, 6), facecolor=BG)
    ax.set_facecolor(BG)
    ax.set_xlim(0, 12)
    ax.set_ylim(0, 6)
    ax.axis('off')

    steps = [
        (0.5,  4.4, "1  Click Globe", "User clicks ocean point", GREEN),
        (0.5,  3.3, "2  Classify Click", "ocean-detection.js\nocean / land / unknown", ACCENT),
        (0.5,  2.2, "3  Convert Coords", "geo.js → lat, lon", ACCENT),
        (0.5,  1.1, "4  API Request", "POST /api/v1/predict\n{lat, lon, month}", ORANGE),
        (6.3,  4.4, "5  Temporal Window", "TemporalService\n[Jan, Feb, Mar] 2020", ACCENT),
        (6.3,  3.3, "6  Load Grids", "SSTRepo + SSHRepo\n180×360 NetCDF", ACCENT2),
        (6.3,  2.2, "7  Preprocess", "fill NaN → normalize\n→ tensor (1,3,180,360,2)", ACCENT),
        (6.3,  1.1, "8  Infer + Extract", "ConvLSTM → (1,180,360,23)\nextract profile at cell", "#764ba2"),
    ]

    for x, y, title, sub, color in steps:
        rect = FancyBboxPatch((x, y), 5.3, 0.85,
                              boxstyle="round,pad=0.1",
                              linewidth=1.5, edgecolor=color,
                              facecolor=color, alpha=0.15)
        ax.add_patch(rect)
        rect2 = FancyBboxPatch((x, y), 5.3, 0.85,
                               boxstyle="round,pad=0.1",
                               linewidth=1.5, edgecolor=color, facecolor='none')
        ax.add_patch(rect2)
        ax.text(x + 0.18, y + 0.6, title, color=color, fontsize=10, fontweight='bold',
                va='center',
                path_effects=[withStroke(linewidth=2, foreground=BG)])
        ax.text(x + 0.18, y + 0.24, sub, color=FG, fontsize=8.3, va='center', alpha=0.88,
                path_effects=[withStroke(linewidth=2, foreground=BG)])

    # Left column arrows
    for y in [4.4, 3.3, 2.2]:
        ax.annotate("", xy=(3.15, y), xytext=(3.15, y + 0.85 - 0.02),
                    arrowprops=dict(arrowstyle="-|>", color='#555577', lw=1.3))

    # Right column arrows
    for y in [4.4, 3.3, 2.2]:
        ax.annotate("", xy=(8.95, y), xytext=(8.95, y + 0.85 - 0.02),
                    arrowprops=dict(arrowstyle="-|>", color='#555577', lw=1.3))

    # Step 4 → Step 5 (cross)
    ax.annotate("", xy=(6.3, 4.82), xytext=(5.8, 1.52),
                arrowprops=dict(arrowstyle="-|>", color=ORANGE, lw=1.8,
                                connectionstyle="arc3,rad=-0.35"))
    ax.text(6.05, 3.15, "HTTP", color=ORANGE, fontsize=8.5, ha='center',
            style='italic',
            path_effects=[withStroke(linewidth=2, foreground=BG)])

    # Response arrow (bottom right → bottom left)
    ax.annotate("", xy=(0.5+5.3, 1.1+0.42), xytext=(6.3, 1.52),
                arrowprops=dict(arrowstyle="-|>", color=GREEN, lw=1.8,
                                connectionstyle="arc3,rad=0.4"))
    ax.text(6.0, 0.6, "JSON response\n{depths_m, temperature_celsius}", color=GREEN,
            fontsize=8.5, ha='center',
            path_effects=[withStroke(linewidth=2, foreground=BG)])

    ax.set_title("OceanEmbed — Request / Response Flow", color=FG, fontsize=14,
                 fontweight='bold', pad=10)
    savefig("request_flow.png")

make_request_flow()

# ─────────────────────────────────────────────────────────────────────────────
# 6. Alarm system diagram
# ─────────────────────────────────────────────────────────────────────────────
def make_alarm_diagram():
    fig, ax = plt.subplots(figsize=(12, 5.5), facecolor=BG)
    ax.set_facecolor(BG)
    ax.set_xlim(0, 12)
    ax.set_ylim(0, 5.5)
    ax.axis('off')

    def box(x, y, w, h, text, color=ACCENT, alpha=0.18, fontsize=10):
        r = FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.12",
                           linewidth=1.6, edgecolor=color, facecolor=color, alpha=alpha)
        ax.add_patch(r)
        r2 = FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.12",
                            linewidth=1.6, edgecolor=color, facecolor='none')
        ax.add_patch(r2)
        lines = text.split('\n')
        for j, line in enumerate(lines):
            oy = 0.15 * (len(lines) - 1 - j*2) / 2
            ax.text(x+w/2, y+h/2 + oy, line, ha='center', va='center',
                    color=FG if j > 0 else color, fontsize=fontsize if j == 0 else fontsize-1.5,
                    fontweight='bold' if j == 0 else 'normal',
                    path_effects=[withStroke(linewidth=2, foreground=BG)])

    def arr(x1, y1, x2, y2, lbl="", color=ACCENT2, style="arc3,rad=0"):
        ax.annotate("", xy=(x2, y2), xytext=(x1, y1),
                    arrowprops=dict(arrowstyle="-|>", color=color, lw=1.5,
                                   connectionstyle=style))
        if lbl:
            mx, my = (x1+x2)/2, (y1+y2)/2
            ax.text(mx+0.05, my+0.18, lbl, color=color, fontsize=8, style='italic',
                    ha='center',
                    path_effects=[withStroke(linewidth=2, foreground=BG)])

    # User adds alarm
    box(0.3, 3.9, 2.4, 1.1, "Alarm Panel\n(Frontend UI)", GREEN)
    box(3.1, 3.9, 2.6, 1.1, "POST /api/v1/alarms\n{lat, lon, month, depth_idx,\ncondition, threshold}", ORANGE, fontsize=8.5)
    box(6.1, 3.9, 2.5, 1.1, "AlarmRepository\n(in-memory store)", ACCENT)

    arr(2.7, 4.45, 3.1, 4.45, "create alarm")
    arr(5.7, 4.45, 6.1, 4.45, "persist")

    # Poll loop
    box(0.3, 2.35, 2.4, 1.0, "AlarmService\npoll loop (every 2 s)", ACCENT)
    box(3.1, 2.35, 2.6, 1.0, "PredictionService\n.predict(lat, lon, month)", "#764ba2", 0.25)
    box(6.1, 2.35, 2.5, 1.0, "condition check\nval > / < threshold", ACCENT2)

    arr(2.7, 2.85, 3.1, 2.85, "per alarm")
    arr(5.7, 2.85, 6.1, 2.85, "value")
    arr(6.1, 3.9, 1.5, 3.35, "", "#555577", "arc3,rad=0.25")   # loop start

    # Firing path
    box(0.3,  0.8, 2.4, 1.0, "Browser\nNotification", GREEN, 0.22)
    box(3.1,  0.8, 2.6, 1.0, "Telegram\nMessage (HTML)", ACCENT2, 0.22)
    box(6.1,  0.8, 2.5, 1.0, "alarm.status\n→ firing", RED, 0.22)

    arr(8.35, 2.35, 7.35, 1.8, "condition MET", RED)
    arr(6.35, 1.8, 6.35, 2.35, "", "#333355")
    arr(6.1,  1.3,  5.7, 1.3, "notify", RED)
    arr(3.1,  1.3,  2.7, 1.3, "", RED)

    # Status cycle label
    ax.text(9.2, 3.0, "Status cycle:", color=FG, fontsize=9, fontweight='bold',
            path_effects=[withStroke(linewidth=2, foreground=BG)])
    for i, (s, c) in enumerate([("active", ACCENT2), ("firing", RED), ("error", ORANGE)]):
        ax.text(9.2, 2.65 - i*0.38, f"● {s}", color=c, fontsize=9,
                path_effects=[withStroke(linewidth=2, foreground=BG)])

    ax.set_title("OceanEmbed — Alarm & Notification System", color=FG, fontsize=14,
                 fontweight='bold', pad=10)
    savefig("alarm_system.png")

make_alarm_diagram()

# ─────────────────────────────────────────────────────────────────────────────
# 7. Data pipeline / preprocessing
# ─────────────────────────────────────────────────────────────────────────────
def make_data_pipeline():
    fig, ax = plt.subplots(figsize=(13, 4.5), facecolor=BG)
    ax.set_facecolor(BG)
    ax.set_xlim(0, 13)
    ax.set_ylim(0, 4.5)
    ax.axis('off')

    stages = [
        (0.3,  "NetCDF\nFiles\n(SST+SSH)", ACCENT2),
        (2.5,  "Reindex\nto 180×360\ngrid", ACCENT),
        (4.7,  "Fill NaN\nwith training\nmeans", ACCENT),
        (6.9,  "Normalize\n÷ training\nstd", ACCENT),
        (9.1,  "Stack\n(1,3,180,\n360,2)", ACCENT),
        (11.3, "ConvLSTM\nInference", "#764ba2"),
    ]

    bw, bh = 1.9, 2.6
    by = 0.9

    for i, (x, lbl, color) in enumerate(stages):
        r = FancyBboxPatch((x, by), bw, bh, boxstyle="round,pad=0.12",
                           linewidth=1.6, edgecolor=color, facecolor=color, alpha=0.18)
        ax.add_patch(r)
        r2 = FancyBboxPatch((x, by), bw, bh, boxstyle="round,pad=0.12",
                            linewidth=1.6, edgecolor=color, facecolor='none')
        ax.add_patch(r2)
        lines = lbl.split('\n')
        for j, line in enumerate(lines):
            yoff = 0.35 * (len(lines)/2 - j - 0.3)
            ax.text(x + bw/2, by + bh/2 + yoff, line,
                    ha='center', va='center', color=FG if j > 0 else color,
                    fontsize=9.5 if j == 0 else 8.5,
                    fontweight='bold' if j == 0 else 'normal',
                    path_effects=[withStroke(linewidth=2, foreground=BG)])

        if i < len(stages) - 1:
            ax.annotate("", xy=(x + bw + 0.1, by + bh/2),
                        xytext=(x + bw, by + bh/2),
                        arrowprops=dict(arrowstyle="-|>", color='#555577', lw=1.5))

    # Preprocessing stats annotation
    ax.text(5.55, 0.35, "preprocessing_stats.npz", color=ORANGE, fontsize=9,
            ha='center', style='italic',
            path_effects=[withStroke(linewidth=2, foreground=BG)])
    ax.annotate("", xy=(5.55, 0.88), xytext=(5.55, 0.5),
                arrowprops=dict(arrowstyle="-|>", color=ORANGE, lw=1.3))
    ax.annotate("", xy=(7.75, 0.88), xytext=(7.75, 0.5),
                arrowprops=dict(arrowstyle="-|>", color=ORANGE, lw=1.3))

    ax.set_title("OceanEmbed — Preprocessing Pipeline", color=FG, fontsize=14,
                 fontweight='bold', pad=8)
    savefig("data_pipeline.png")

make_data_pipeline()

# ─────────────────────────────────────────────────────────────────────────────
# 8. Frontend UI mockup (annotated wireframe)
# ─────────────────────────────────────────────────────────────────────────────
def make_ui_mockup():
    fig, ax = plt.subplots(figsize=(12, 7.2), facecolor="#0a0a0f")
    ax.set_facecolor("#0a0a0f")
    ax.set_xlim(0, 12)
    ax.set_ylim(0, 7.2)
    ax.axis('off')

    # Screen chrome
    screen = FancyBboxPatch((0.2, 0.3), 11.6, 6.7, boxstyle="round,pad=0.05",
                            linewidth=2, edgecolor="#333355", facecolor="#0d0d18")
    ax.add_patch(screen)

    # Earth globe (circle)
    earth = plt.Circle((6.0, 3.6), 2.8, color="#1a3a5c", linewidth=1.5,
                        edgecolor="#2255aa")
    ax.add_patch(earth)
    # Latitude lines
    for lat in [-1.5, -0.5, 0.5, 1.5]:
        w = 2 * np.sqrt(max(0, 2.8**2 - lat**2))
        ellipse = matplotlib.patches.Ellipse((6.0, 3.6 + lat), w, 0.25,
                                             color='none', linewidth=0.5,
                                             edgecolor="#1e4d7a", alpha=0.7)
        ax.add_patch(ellipse)
    # Longitude lines
    for lon_x in [-1.5, -0.5, 0.5, 1.5]:
        ellipse = matplotlib.patches.Ellipse((6.0 + lon_x*0.3, 3.6), 0.3, 5.6,
                                             color='none', linewidth=0.5,
                                             edgecolor="#1e4d7a", alpha=0.5)
        ax.add_patch(ellipse)
    # Continents (rough blobs)
    for cx, cy, rx, ry in [(5.5, 4.3, 0.9, 0.55),
                            (7.0, 3.9, 0.55, 0.7),
                            (5.0, 3.0, 0.4, 0.35),
                            (6.8, 2.8, 0.3, 0.4),
                            (4.3, 4.0, 0.35, 0.3)]:
        land = matplotlib.patches.Ellipse((cx, cy), rx*2, ry*2,
                                          color="#2d5a1b", alpha=0.75)
        ax.add_patch(land)

    # Click marker
    click_x, click_y = 7.4, 4.7
    ax.plot(click_x, click_y, 'o', color=ORANGE, markersize=10, zorder=5)
    ax.plot(click_x, click_y, 'o', color=ORANGE, markersize=20, alpha=0.25, zorder=4)

    # Instructions banner (bottom center)
    banner = FancyBboxPatch((3.5, 0.55), 5.0, 0.6, boxstyle="round,pad=0.1",
                            linewidth=1, edgecolor="#333355", facecolor="#111122", alpha=0.9)
    ax.add_patch(banner)
    ax.text(6.0, 0.85, "🌊  Click any ocean to explore temperature layers",
            ha='center', va='center', color=FG, fontsize=9)

    # Top-right: alarm bell button
    bell_rect = FancyBboxPatch((10.8, 6.3), 0.7, 0.5, boxstyle="round,pad=0.07",
                               linewidth=1, edgecolor="#333355", facecolor="#111122")
    ax.add_patch(bell_rect)
    ax.text(11.15, 6.55, "🔔", ha='center', va='center', fontsize=11)

    # Left panel: info sidebar
    sidebar = FancyBboxPatch((0.35, 4.6), 2.5, 2.2, boxstyle="round,pad=0.08",
                             linewidth=1, edgecolor="#333355", facecolor="#0d0d18", alpha=0.95)
    ax.add_patch(sidebar)
    ax.text(0.55, 6.6, "Location", color=FG, fontsize=9, fontweight='bold')
    ax.text(0.55, 6.35, "📍 Arabian Sea", color=FG, fontsize=8, alpha=0.8, style='italic')
    ax.text(0.55, 6.1,  "20.5°N  75.5°E", color=FG, fontsize=8)
    ax.text(0.55, 5.8,  "Surface:   28.1°C", color=FG, fontsize=8)
    ax.text(0.55, 5.55, "Deep:       2.3°C", color=FG, fontsize=8)
    ax.text(0.55, 5.3,  "Range:     25.8°C", color=FG, fontsize=8)

    # Right: depth layer cross-section visualization
    depths_vis = [30, 75, 150, 300, 600, 1000, 1500, 2000]
    temps_vis  = [28.1, 26.8, 20.4, 10.8, 5.3, 3.4, 2.7, 2.3]
    cmap = LinearSegmentedColormap.from_list(
        'ocean', ['#0d47a1', '#0288d1', '#26c6da', '#80deea',
                  '#ffe082', '#ffb300', '#ef6c00', '#b71c1c'])
    tmin, tmax = min(temps_vis), max(temps_vis)

    layer_x0, layer_x1 = 9.0, 11.5
    layer_y0, layer_y1 = 1.0, 6.8
    total_h = layer_y1 - layer_y0
    layer_h = total_h / len(depths_vis)

    for i, (d, t) in enumerate(zip(depths_vis, temps_vis)):
        norm = (t - tmin) / (tmax - tmin)
        c = cmap(norm)
        ly = layer_y1 - (i+1)*layer_h
        rect = FancyBboxPatch((layer_x0, ly), layer_x1-layer_x0, layer_h*0.88,
                              boxstyle="round,pad=0.03",
                              facecolor=c, edgecolor='white', linewidth=0.4, alpha=0.85)
        ax.add_patch(rect)
        ax.text(layer_x0 - 0.08, ly + layer_h*0.44, f"{d}m",
                ha='right', va='center', color=FG, fontsize=7.5)
        ax.text(layer_x1 + 0.08, ly + layer_h*0.44, f"{t:.1f}°C",
                ha='left', va='center', color=FG, fontsize=7.5)

    # Annotations
    def callout(ax, tx, ty, text, color, xoff=1.2, yoff=0):
        ex, ey = tx + xoff, ty + yoff
        ax.annotate(text, xy=(tx, ty), xytext=(ex, ey),
                    arrowprops=dict(arrowstyle="-", color=color, lw=1),
                    color=color, fontsize=8, fontweight='bold',
                    path_effects=[withStroke(linewidth=2, foreground=BG)])

    callout(ax, click_x, click_y, "ocean click", ORANGE, xoff=0.7, yoff=0.5)
    callout(ax, 10.25, 3.9, "depth layers\n(animated)", ACCENT, xoff=-2.2, yoff=-1.2)

    ax.set_title("OceanEmbed — Frontend UI (interactive 3D globe)", color=FG,
                 fontsize=13, fontweight='bold', pad=8)
    savefig("ui_mockup.png")

make_ui_mockup()

print("\nAll images written to public/")
