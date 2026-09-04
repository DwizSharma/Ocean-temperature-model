import { CONFIG } from './config';
export class OceanApiError extends Error {
  constructor(message, cause) {
    super(message);
    this.name = 'OceanApiError';
    this.cause = cause;
  }
}

/**
 * POSTs { latitude, longitude, target_month } to the backend and returns
 * the parsed temperature-profile response.
 */
export async function fetchTemperatureProfile({ latitude, longitude, target_month }, { signal } = {}) {
  let response;
  try {
    response = await fetch(CONFIG.API_ENDPOINT, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ latitude, longitude, target_month }),
      signal,
    });
  } catch (err) {
    if (err.name === 'AbortError') throw err;
    throw new OceanApiError(
      `Couldn't reach the backend at ${CONFIG.API_ENDPOINT}. Is it running on :8080?`,
      err
    );
  }

  if (!response.ok) {
    let detail = '';
    try {
      detail = await response.text();
    } catch {
      /* ignore */
    }
    throw new OceanApiError(`Backend returned ${response.status} ${response.statusText}${detail ? ` — ${detail}` : ''}`);
  }

  const data = await response.json();

  if (!Array.isArray(data.depths_m) || !Array.isArray(data.temperature_celsius)) {
    throw new OceanApiError('Backend response is missing depths_m / temperature_celsius arrays.');
  }

  return data;
}
