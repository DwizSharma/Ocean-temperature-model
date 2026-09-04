import * as THREE from 'three';
import { CONFIG } from './config';

const _center = new THREE.Vector3();
const _dir = new THREE.Vector3();
const _invQuat = new THREE.Quaternion();

/**
 * Converts a world-space point on the globe into { lat, lon } in degrees.
 *
 * Assumes the globe is (approximately) a sphere. We take the direction
 * from the model group's world-space center to the clicked point, undo
 * the group's own rotation (so spinning the model doesn't change what
 * coordinate a given physical spot reports), and run the standard
 * spherical -> geographic conversion. See CONFIG.LONGITUDE_OFFSET for
 * calibrating against your specific model's texture orientation.
 */
export function pointToLatLon(point, group) {
  group.getWorldPosition(_center);
  _dir.copy(point).sub(_center).normalize();

  _invQuat.copy(group.quaternion).invert();
  _dir.applyQuaternion(_invQuat);

  const lat = THREE.MathUtils.radToDeg(Math.asin(THREE.MathUtils.clamp(_dir.y, -1, 1)));
  let lon = THREE.MathUtils.radToDeg(Math.atan2(_dir.z, _dir.x)) + CONFIG.LONGITUDE_OFFSET;

  // normalize to [-180, 180]
  lon = ((lon + 180) % 360 + 360) % 360 - 180;

  return { lat, lon };
}

export function formatCoord(value, positiveSuffix, negativeSuffix) {
  const suffix = value >= 0 ? positiveSuffix : negativeSuffix;
  return `${Math.abs(value).toFixed(2)}\u00B0${suffix}`;
}

export function formatLat(lat) {
  return formatCoord(lat, 'N', 'S');
}

export function formatLon(lon) {
  return formatCoord(lon, 'E', 'W');
}

export function formatMonth(targetMonth) {
  if (!targetMonth) return '';
  const [year, month] = targetMonth.split('-');
  const date = new Date(Number(year), Number(month) - 1, 1);
  return date.toLocaleDateString(undefined, { year: 'numeric', month: 'long' });
}
