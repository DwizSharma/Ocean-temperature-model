// Diverging thermal scale: cold/deep -> warm/surface.
// Chosen to be readable on a dark instrument-panel background rather
// than a generic rainbow map.
const STOPS = [
  { t: 0.0, rgb: [43, 20, 84] }, // deep violet — coldest / deepest
  { t: 0.22, rgb: [35, 84, 168] }, // blue
  { t: 0.45, rgb: [34, 158, 188] }, // teal
  { t: 0.65, rgb: [98, 199, 121] }, // green
  { t: 0.82, rgb: [242, 196, 68] }, // amber
  { t: 1.0, rgb: [224, 84, 63] }, // coral red — warmest / surface
];

function lerp(a, b, t) {
  return a + (b - a) * t;
}

/** t in [0,1] -> [r,g,b] each 0-255 */
export function temperatureToRGB(t) {
  const clamped = Math.min(1, Math.max(0, t));
  for (let i = 0; i < STOPS.length - 1; i++) {
    const a = STOPS[i];
    const b = STOPS[i + 1];
    if (clamped >= a.t && clamped <= b.t) {
      const localT = (clamped - a.t) / (b.t - a.t || 1);
      return [
        lerp(a.rgb[0], b.rgb[0], localT),
        lerp(a.rgb[1], b.rgb[1], localT),
        lerp(a.rgb[2], b.rgb[2], localT),
      ];
    }
  }
  return STOPS[STOPS.length - 1].rgb;
}

export function temperatureToCSS(t) {
  const [r, g, b] = temperatureToRGB(t);
  return `rgb(${Math.round(r)}, ${Math.round(g)}, ${Math.round(b)})`;
}

export function temperatureToHex(t) {
  const [r, g, b] = temperatureToRGB(t);
  const toHex = (v) => Math.round(v).toString(16).padStart(2, '0');
  return `#${toHex(r)}${toHex(g)}${toHex(b)}`;
}

/** Builds a normalizer over a data-driven [min,max] range. */
export function makeNormalizer(values) {
  const min = Math.min(...values);
  const max = Math.max(...values);
  const span = max - min || 1;
  return (v) => (v - min) / span;
}
