/** Mirrors backend constants.py DEPTHS_M. */
export const DEPTHS_M = [
  30, 50, 75, 100, 125, 150, 200, 250, 300, 400,
  500, 600, 700, 800, 900, 1000, 1100, 1200, 1300,
  1400, 1500, 1750, 2000,
];

export const DEPTH_LABELS = DEPTHS_M.map(d => `${d} m`);
