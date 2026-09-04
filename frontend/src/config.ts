export const CONFIG = {
  DEBUG_MODE: true,

  // Longitude offset applied when converting 3D click positions to lat/lon.
  // Set to 0 for standard earth models; adjust if the texture is rotated.
  LONGITUDE_OFFSET: 0,

  // Mesh / material name keywords used to classify ocean vs land clicks.
  OCEAN_KEYWORDS: ['ocean', 'sea', 'water', 'deep'],
  LAND_KEYWORDS: ['land', 'continent', 'terrain', 'earth', 'ground'],

  // When true, falls back to a blue-ish color heuristic if name matching
  // doesn't classify the clicked mesh.
  ENABLE_COLOR_FALLBACK: true,

  // Backend API URL for temperature predictions.
  API_ENDPOINT: 'http://localhost:8080/api/predict',
};
