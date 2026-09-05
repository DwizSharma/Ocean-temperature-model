/**
 * useAlarms — manages alarm CRUD and browser/Telegram notification polling.
 *
 * Status model (mirrors backend):
 *   active  → condition not yet met, polling
 *   firing  → condition currently met, notification fires every cycle
 *   error   → last poll threw
 *
 * In mock mode the hook polls generateMockProfile client-side and calls
 * the backend /trigger endpoint so Telegram fires server-side.
 */
import { useState, useEffect, useRef, useCallback } from 'react';
import { CONFIG } from './config';
import { generateMockProfile } from './mock-data';

const API_BASE = '/api/v1/alarms';

// ── helpers ────────────────────────────────────────────────────────────────

function conditionMet(condition, value, threshold) {
  return condition === 'above' ? value > threshold : value < threshold;
}

async function apiFetch(path, options = {}) {
  const res = await fetch(path, {
    headers: { 'Content-Type': 'application/json' },
    ...options,
  });
  if (!res.ok) {
    const text = await res.text().catch(() => '');
    const err = new Error(`[${res.status}] ${text || res.statusText}`);
    err.status = res.status;
    throw err;
  }
  return res.status === 204 ? null : res.json();
}

async function fireNotification(alarm, value) {
  const label = alarm.label ? ` (${alarm.label})` : '';
  const body =
    `${value.toFixed(2)}°C is ${alarm.condition} ${alarm.threshold_celsius}°C ` +
    `at ${alarm.latitude.toFixed(2)}°, ${alarm.longitude.toFixed(2)}°`;

  // Browser notification
  if ('Notification' in window) {
    const perm = Notification.permission === 'default'
      ? await Notification.requestPermission()
      : Notification.permission;
    if (perm === 'granted') {
      new Notification(`🚨 Ocean Alarm${label}`, { body, tag: alarm.id });
    }
  }

  // Backend Telegram dispatch (works even in mock mode via /trigger endpoint)
  apiFetch(`${API_BASE}/${alarm.id}/trigger`, {
    method: 'POST',
    body: JSON.stringify({ value_celsius: value }),
  }).catch(e => console.warn('[useAlarms] /trigger failed:', e.message));
}

// ── main hook ───────────────────────────────────────────────────────────────

export function useAlarms(pollIntervalMs = CONFIG.ALARM_POLL_INTERVAL_MS ?? 2000) {
  const [alarms, setAlarms] = useState([]);
  const [error, setError]   = useState(null);
  const timersRef = useRef({});  // alarmId → intervalId

  // ── request browser notification permission once on mount ─────────────
  useEffect(() => {
    if (!('Notification' in window)) return;
    if (Notification.permission === 'default') {
      Notification.requestPermission().then(perm => {
        if (perm !== 'granted') {
          console.warn('[useAlarms] Browser notifications denied — only UI and Telegram will fire.');
        }
      });
    }
  }, []);

  // Cleanup all intervals on unmount
  useEffect(() => () => Object.values(timersRef.current).forEach(clearInterval), []);

  // ── mock poll ─────────────────────────────────────────────────────────
  const startMockPoll = useCallback((alarm) => {
    if (timersRef.current[alarm.id]) return;

    timersRef.current[alarm.id] = setInterval(async () => {
      try {
        const profile = generateMockProfile({
          latitude:     alarm.latitude,
          longitude:    alarm.longitude,
          target_month: alarm.target_month,
        });
        const value = profile.temperature_celsius[alarm.depth_index];
        const met   = conditionMet(alarm.condition, value, alarm.threshold_celsius);

        if (met) {
          // Fire notification every cycle while condition holds
          await fireNotification(alarm, value);
          setAlarms(prev => prev.map(a => a.id !== alarm.id ? a : {
            ...a,
            status: 'firing',
            last_value_celsius: value,
            triggered_at: new Date().toISOString(),
          }));
        } else {
          // Condition cleared — reset so it can fire again if it crosses later
          setAlarms(prev => prev.map(a => a.id !== alarm.id ? a : {
            ...a,
            status: 'active',
            last_value_celsius: value,
          }));
        }
      } catch (e) {
        setAlarms(prev => prev.map(a => a.id !== alarm.id ? a : {
          ...a, status: 'error', error_detail: e.message,
        }));
        // Keep the interval running — backend resets error→active automatically
      }
    }, pollIntervalMs);
  }, [pollIntervalMs]);

  const stopMockPoll = useCallback((alarmId) => {
    clearInterval(timersRef.current[alarmId]);
    delete timersRef.current[alarmId];
  }, []);

  // ── public API ────────────────────────────────────────────────────────

  const addAlarm = useCallback(async (payload) => {
    setError(null);
    if (CONFIG.USE_MOCK_DATA) {
      // Register on the backend first to get the server-assigned ID (needed for /trigger).
      // Fall back to a local UUID if the backend is unreachable.
      let backendId = null;
      try {
        const serverAlarm = await apiFetch(API_BASE, {
          method: 'POST',
          body: JSON.stringify(payload),
        });
        backendId = serverAlarm.id;
      } catch {
        console.warn('[useAlarms] Backend unreachable — Telegram notifications disabled for this alarm');
      }

      const alarm = {
        id: backendId ?? crypto.randomUUID(),
        ...payload,
        status: 'active',
        last_value_celsius: null,
        triggered_at: null,
        created_at: new Date().toISOString(),
        error_detail: null,
      };
      setAlarms(prev => [...prev, alarm]);
      startMockPoll(alarm);
      return alarm;
    }

    // Real mode — backend owns the poll loop
    try {
      const alarm = await apiFetch(API_BASE, {
        method: 'POST',
        body: JSON.stringify(payload),
      });
      setAlarms(prev => [...prev, alarm]);
      return alarm;
    } catch (e) {
      setError(e.message);
      throw e;
    }
  }, [startMockPoll]);

  const removeAlarm = useCallback(async (alarmId) => {
    setError(null);
    stopMockPoll(alarmId);  // safe to call even in real mode (no-op if no timer)
    if (CONFIG.USE_MOCK_DATA) {
      setAlarms(prev => prev.filter(a => a.id !== alarmId));
      // Best-effort backend cleanup
      apiFetch(`${API_BASE}/${alarmId}`, { method: 'DELETE' }).catch(() => {});
      return;
    }
    try {
      await apiFetch(`${API_BASE}/${alarmId}`, { method: 'DELETE' });
      setAlarms(prev => prev.filter(a => a.id !== alarmId));
    } catch (e) {
      setError(e.message);
      throw e;
    }
  }, [stopMockPoll]);

  /** Sync alarm statuses from the backend (real mode only). */
  const refreshAlarms = useCallback(async () => {
    if (CONFIG.USE_MOCK_DATA) return;
    try {
      setAlarms(await apiFetch(API_BASE));
    } catch (e) {
      setError(e.message);
    }
  }, []);

  return { alarms, error, addAlarm, removeAlarm, refreshAlarms };
}
