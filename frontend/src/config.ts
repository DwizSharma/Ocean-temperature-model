export const CONFIG = {
  DEBUG_MODE: true,

  // Use mock data instead of real API (useful for development/testing)
  USE_MOCK_DATA: import.meta.env.VITE_USE_MOCK_DATA === 'true' || true,

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
  // In development, use proxy to avoid CORS issues
  API_ENDPOINT: import.meta.env.VITE_API_ENDPOINT || '/api/v1/predict',
};
