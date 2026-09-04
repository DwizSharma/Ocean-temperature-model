import * as THREE from 'three';
import { CONFIG } from './config';

const _hsl = { h: 0, s: 0, l: 0 };

/**
 * Classifies a raycast intersection as ocean / land / unknown.
 * Returns 'ocean' | 'land' | 'unknown'.
 *
 * Tries, in order:
 *  1. Mesh/material name matching against CONFIG.OCEAN_KEYWORDS / LAND_KEYWORDS
 *  2. (optional) flat material color heuristic — blue-ish reads as ocean
 *  3. gives up and reports 'unknown'
 */
export function classifyIntersection(intersection) {
  const object = intersection.object;
  const name = (object.name || '').toLowerCase();
  const materialName = (object.material?.name || '').toLowerCase();

  if (CONFIG.DEBUG_MODE) {
    // eslint-disable-next-line no-console
    console.log(
      `[ocean-detection] clicked mesh="${object.name || '(unnamed)'}" material="${object.material?.name || '(unnamed)'}"`
    );
  }

  const haystacks = [name, materialName];
  if (haystacks.some((h) => CONFIG.OCEAN_KEYWORDS.some((k) => h.includes(k)))) {
    return 'ocean';
  }
  if (haystacks.some((h) => CONFIG.LAND_KEYWORDS.some((k) => h.includes(k)))) {
    return 'land';
  }

  if (CONFIG.ENABLE_COLOR_FALLBACK && object.material && object.material.color) {
    object.material.color.getHSL(_hsl);
    // Blue hues in three's 0-1 HSL space land roughly between cyan and violet.
    const isBlueish = _hsl.h >= 0.45 && _hsl.h <= 0.72 && _hsl.s > 0.15 && _hsl.l > 0.05;
    if (isBlueish) return 'ocean';
  }

  return 'unknown';
}
