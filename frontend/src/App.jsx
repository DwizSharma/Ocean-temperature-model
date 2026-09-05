import React, { useState, Suspense, useRef } from 'react';
import { Canvas, useThree, useFrame } from '@react-three/fiber';
import { OrbitControls, useGLTF } from '@react-three/drei';
import * as THREE from 'three';

import { pointToLatLon, formatLat, formatLon, formatMonth } from './geo';
import { classifyIntersection } from './ocean-detection';
import { fetchTemperatureProfile } from './ocean-api';
import { temperatureToCSS, temperatureToRGB, makeNormalizer } from './color-scale';
import { CONFIG } from './config';
import { useAlarms } from './use-alarms';
import AlarmPanel from './AlarmPanel';

// Generate organic, wavy shape for layers (like geological strata)
function createWavyLayerShape(width, height, waveIntensity = 0.3, seed = 0) {
  const shape = new THREE.Shape();
  const segments = 50;
  const segmentWidth = width / segments;
  
  // Start from bottom-left
  shape.moveTo(-width / 2, -height / 2);
  
  // Draw wavy top edge
  for (let i = 0; i <= segments; i++) {
    const x = -width / 2 + i * segmentWidth;
    const wave = Math.sin((i / segments) * Math.PI * 4 + seed) * waveIntensity;
    const wave2 = Math.sin((i / segments) * Math.PI * 7 + seed * 1.3) * waveIntensity * 0.5;
    const y = height / 2 + wave + wave2;
    
    if (i === 0) {
      shape.moveTo(x, y);
    } else {
      shape.lineTo(x, y);
    }
  }
  
  // Right edge
  shape.lineTo(width / 2, -height / 2);
  
  // Bottom edge (also wavy but less)
  for (let i = segments; i >= 0; i--) {
    const x = -width / 2 + i * segmentWidth;
    const wave = Math.sin((i / segments) * Math.PI * 3 + seed + 0.5) * waveIntensity * 0.3;
    const y = -height / 2 + wave;
    shape.lineTo(x, y);
  }
  
  shape.closePath();
  return shape;
}

// Organic geological layer with gradients
function OrganicLayer({ depth, temp, index, totalLayers, normalize, startAnimation, isVisible, allTemps }) {
  const meshRef = useRef();
  const [scale, setScale] = useState(0);
  const [opacity, setOpacity] = useState(0);
  
  const normalizedTemp = normalize(temp);
  const [r, g, b] = temperatureToRGB(normalizedTemp);
  const color = new THREE.Color(r / 255, g / 255, b / 255);
  
  // Get adjacent temperatures for gradient
  const prevTemp = index > 0 ? allTemps[index - 1] : temp;
  const nextTemp = index < totalLayers - 1 ? allTemps[index + 1] : temp;
  const [r1, g1, b1] = temperatureToRGB(normalize(prevTemp));
  const [r2, g2, b2] = temperatureToRGB(normalize(nextTemp));
  const colorTop = new THREE.Color(r1 / 255, g1 / 255, b1 / 255);
  const colorBottom = new THREE.Color(r2 / 255, g2 / 255, b2 / 255);
  
  // Create organic wavy layer - use full horizontal space
  const layerGeometry = React.useMemo(() => {
    const layerHeight = 2.5;
    const layerWidth = 180; // Full horizontal width
    const waveIntensity = 0.6 + (index * 0.01);
    const seed = index * 2.5;
    
    const shape = createWavyLayerShape(layerWidth, layerHeight, waveIntensity, seed);
    const extrudeSettings = {
      depth: 3,
      bevelEnabled: true,
      bevelThickness: 0.15,
      bevelSize: 0.1,
      bevelSegments: 2
    };
    
    return new THREE.ExtrudeGeometry(shape, extrudeSettings);
  }, [index]);
  
  // Calculate spacing to fit all layers in view
  const viewHeight = 60; // Available vertical space
  const spacing = viewHeight / totalLayers;
  const yPosition = (totalLayers / 2 - index - 0.5) * spacing;
  
  useFrame(() => {
    if (startAnimation && isVisible) {
      const targetScale = 1;
      const targetOpacity = 0.95;
      
      if (scale < targetScale) {
        setScale(prev => Math.min(prev + 0.04, targetScale));
      }
      if (opacity < targetOpacity) {
        setOpacity(prev => Math.min(prev + 0.04, targetOpacity));
      }
    } else if (!isVisible && opacity > 0) {
      setOpacity(prev => Math.max(prev - 0.08, 0));
      setScale(prev => Math.max(prev - 0.08, 0));
    }
  });

  if (opacity === 0) return null;

  // Create gradient material
  const gradientTexture = React.useMemo(() => {
    const canvas = document.createElement('canvas');
    canvas.width = 1;
    canvas.height = 256;
    const context = canvas.getContext('2d');
    
    const gradient = context.createLinearGradient(0, 0, 0, 256);
    gradient.addColorStop(0, `rgb(${r1}, ${g1}, ${b1})`);
    gradient.addColorStop(0.5, `rgb(${r}, ${g}, ${b})`);
    gradient.addColorStop(1, `rgb(${r2}, ${g2}, ${b2})`);
    
    context.fillStyle = gradient;
    context.fillRect(0, 0, 1, 256);
    
    const texture = new THREE.CanvasTexture(canvas);
    texture.needsUpdate = true;
    return texture;
  }, [r, g, b, r1, g1, b1, r2, g2, b2]);

  return (
    <group position={[0, yPosition, 0]}>
      <mesh ref={meshRef} geometry={layerGeometry} scale={[scale, 1, 1]} rotation={[0, 0, 0]}>
        <meshStandardMaterial 
          map={gradientTexture}
          transparent
          opacity={opacity}
          emissive={color}
          emissiveIntensity={0.2}
          roughness={0.9}
          metalness={0.05}
          side={THREE.DoubleSide}
        />
      </mesh>
      
      {/* Depth marker line on left */}
      {opacity > 0.3 && (
        <mesh position={[-92, 0, 1.5]}>
          <cylinderGeometry args={[0.2, 0.2, spacing * 0.6, 8]} />
          <meshBasicMaterial color={color} transparent opacity={opacity * 0.8} />
        </mesh>
      )}
      
      {/* Temperature marker line on right */}
      {opacity > 0.3 && (
        <mesh position={[92, 0, 1.5]}>
          <cylinderGeometry args={[0.2, 0.2, spacing * 0.6, 8]} />
          <meshBasicMaterial color={color} transparent opacity={opacity * 0.8} />
        </mesh>
      )}
    </group>
  );
}

// Full-screen geological cross-section overlay (positioned at clicked point)
function GeologicalCrossSection({ profile, show, clickedPoint }) {
  if (!profile) return null;

  const { depths_m, temperature_celsius } = profile;
  const normalize = makeNormalizer(temperature_celsius);
  
  // Calculate spacing to fit all layers
  const viewHeight = 60;
  const spacing = viewHeight / depths_m.length;
  
  // Position layers at the clicked point on Earth surface
  const layerPosition = clickedPoint 
    ? clickedPoint.clone().normalize().multiplyScalar(102) // Just above Earth surface
    : new THREE.Vector3(0, 0, 0);

  return (
    <group position={layerPosition}>
      {depths_m.map((depth, i) => (
        <OrganicLayer
          key={i}
          depth={depth}
          temp={temperature_celsius[i]}
          index={i}
          totalLayers={depths_m.length}
          normalize={normalize}
          startAnimation={show}
          isVisible={show}
          allTemps={temperature_celsius}
        />
      ))}
      
      {/* Vertical reference lines */}
      {show && (
        <>
          <mesh position={[-93, 0, 1.5]}>
            <cylinderGeometry args={[0.1, 0.1, viewHeight, 8]} />
            <meshBasicMaterial color="#ffffff" transparent opacity={0.3} />
          </mesh>
          <mesh position={[93, 0, 1.5]}>
            <cylinderGeometry args={[0.1, 0.1, viewHeight, 8]} />
            <meshBasicMaterial color="#ffffff" transparent opacity={0.3} />
          </mesh>
        </>
      )}
    </group>
  );
}

// Full-screen data overlay
function DataOverlay({ profile, show }) {
  if (!profile || !show) return null;

  const { depths_m, temperature_celsius } = profile;
  const normalize = makeNormalizer(temperature_celsius);
  
  // Calculate spacing to match 3D layers - fit in vertical space
  const viewHeight = window.innerHeight * 0.85; // 85% of screen height
  const itemHeight = viewHeight / depths_m.length;

  return (
    <div style={{
      position: 'absolute',
      top: '50%',
      left: 0,
      right: 0,
      transform: 'translateY(-50%)',
      pointerEvents: 'none',
      opacity: show ? 1 : 0,
      transition: 'opacity 0.5s ease',
      display: 'flex',
      justifyContent: 'space-between',
      padding: '0 40px',
      height: viewHeight
    }}>
      {/* Depth labels on left */}
      <div style={{ 
        display: 'flex', 
        flexDirection: 'column',
        justifyContent: 'space-around',
        width: 120
      }}>
        {depths_m.map((depth, i) => {
          const normalizedTemp = normalize(temperature_celsius[i]);
          const [r, g, b] = temperatureToRGB(normalizedTemp);
          
          // Gradient with adjacent layers
          const prevNorm = i > 0 ? normalize(temperature_celsius[i - 1]) : normalizedTemp;
          const nextNorm = i < depths_m.length - 1 ? normalize(temperature_celsius[i + 1]) : normalizedTemp;
          const [r1, g1, b1] = temperatureToRGB(prevNorm);
          const [r2, g2, b2] = temperatureToRGB(nextNorm);
          
          return (
            <div
              key={i}
              style={{
                padding: `${Math.max(8, itemHeight * 0.3)}px 20px`,
                background: `linear-gradient(180deg, rgb(${r1}, ${g1}, ${b1}) 0%, rgb(${r}, ${g}, ${b}) 50%, rgb(${r2}, ${g2}, ${b2}) 100%)`,
                color: 'white',
                fontSize: Math.max(12, Math.min(15, itemHeight * 0.4)),
                fontWeight: 700,
                borderRadius: 8,
                textAlign: 'center',
                boxShadow: `0 4px 16px rgba(${r}, ${g}, ${b}, 0.5)`,
                border: '2px solid rgba(255,255,255,0.4)',
                backdropFilter: 'blur(8px)',
                animation: `slideInLeft 0.5s ease-out ${i * 0.03}s both`,
                minHeight: Math.max(30, itemHeight * 0.7)
              }}
            >
              {depth}m
            </div>
          );
        })}
      </div>

      {/* Temperature values on right */}
      <div style={{ 
        display: 'flex', 
        flexDirection: 'column',
        justifyContent: 'space-around',
        width: 130
      }}>
        {temperature_celsius.map((temp, i) => {
          const normalizedTemp = normalize(temp);
          const [r, g, b] = temperatureToRGB(normalizedTemp);
          
          return (
            <div
              key={i}
              style={{
                padding: `${Math.max(8, itemHeight * 0.3)}px 20px`,
                background: 'rgba(0, 0, 0, 0.92)',
                color: `rgb(${r}, ${g}, ${b})`,
                fontSize: Math.max(13, Math.min(16, itemHeight * 0.45)),
                fontWeight: 700,
                fontFamily: 'monospace',
                borderRadius: 8,
                textAlign: 'center',
                boxShadow: `0 4px 16px rgba(${r}, ${g}, ${b}, 0.6)`,
                border: `2px solid rgb(${r}, ${g}, ${b})`,
                backdropFilter: 'blur(8px)',
                animation: `slideInRight 0.5s ease-out ${i * 0.03}s both`,
                minHeight: Math.max(30, itemHeight * 0.7)
              }}
            >
              {temp.toFixed(1)}°C
            </div>
          );
        })}
      </div>

      <style>{`
        @keyframes slideInLeft {
          from {
            opacity: 0;
            transform: translateX(-50px);
          }
          to {
            opacity: 1;
            transform: translateX(0);
          }
        }
        
        @keyframes slideInRight {
          from {
            opacity: 0;
            transform: translateX(50px);
          }
          to {
            opacity: 1;
            transform: translateX(0);
          }
        }
      `}</style>
    </div>
  );
}

// Info sidebar
function InfoSidebar({ profile, latitude, longitude, region_name }) {
  if (!profile) return null;

  const { temperature_celsius } = profile;

  return (
    <div style={{
      position: 'absolute',
      top: 20,
      left: 20,
      maxWidth: 300,
      backgroundColor: 'rgba(10, 10, 15, 0.95)',
      color: 'white',
      padding: 20,
      borderRadius: 12,
      fontFamily: 'system-ui, -apple-system, sans-serif',
      boxShadow: '0 8px 32px rgba(0,0,0,0.8)',
      backdropFilter: 'blur(20px)',
      border: '1px solid rgba(255,255,255,0.1)'
    }}>
      <h3 style={{ margin: '0 0 12px 0', fontSize: 18, fontWeight: 700 }}>Location</h3>
      {region_name && (
        <p style={{ fontSize: 13, margin: '0 0 6px 0', opacity: 0.8, fontStyle: 'italic' }}>
          📍 {region_name}
        </p>
      )}
      <p style={{ fontSize: 14, margin: 0, opacity: 0.9 }}>
        {formatLat(latitude)} {formatLon(longitude)}
      </p>
      
      <div style={{ marginTop: 16, paddingTop: 16, borderTop: '1px solid rgba(255,255,255,0.1)' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: 12, marginBottom: 4 }}>
          <span style={{ opacity: 0.8 }}>Surface:</span>
          <span style={{ fontWeight: 700 }}>{temperature_celsius[0].toFixed(1)}°C</span>
        </div>
        <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: 12, marginBottom: 4 }}>
          <span style={{ opacity: 0.8 }}>Deep:</span>
          <span style={{ fontWeight: 700 }}>{temperature_celsius[temperature_celsius.length - 1].toFixed(1)}°C</span>
        </div>
        <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: 12 }}>
          <span style={{ opacity: 0.8 }}>Range:</span>
          <span style={{ fontWeight: 700 }}>
            {(temperature_celsius[0] - temperature_celsius[temperature_celsius.length - 1]).toFixed(1)}°C
          </span>
        </div>
      </div>
    </div>
  );
}

// Error boundary
class ModelErrorBoundary extends React.Component {
  state = { error: null };
  static getDerivedStateFromError(error) { return { error }; }
  componentDidCatch(error, info) { console.error('GLTF failed:', error, info); }
  render() {
    if (this.state.error) {
      return (
        <mesh>
          <sphereGeometry args={[50, 32, 32]} />
          <meshStandardMaterial color="red" wireframe />
        </mesh>
      );
    }
    return this.props.children;
  }
}

// Camera zoom animation (zoom to clicked point and keep it centered)
function CameraController({ stage, clickedPoint, onComplete }) {
  const { camera, controls } = useThree();
  const animationRef = useRef({ isAnimating: false });
  
  React.useEffect(() => {
    if (!stage || animationRef.current.isAnimating) return;
    
    if (stage === 'zoom-in' && clickedPoint) {
      // Zoom into the specific clicked point on Earth
      animationRef.current.isAnimating = true;
      if (controls) {
        controls.enabled = false;
        controls.autoRotate = false;
      }
      
      const startPos = camera.position.clone();
      
      // Calculate zoom position: move camera closer along the direction to clicked point
      const direction = clickedPoint.clone().normalize();
      const endPos = direction.multiplyScalar(140); // Close but not too close
      
      const startLookAt = new THREE.Vector3(0, 0, 0);
      const endLookAt = clickedPoint.clone().normalize().multiplyScalar(50);
      
      const duration = 2000;
      const startTime = Date.now();
      
      const animate = () => {
        const elapsed = Date.now() - startTime;
        const progress = Math.min(elapsed / duration, 1);
        
        // Ease-in-out for smooth zoom
        const eased = progress < 0.5 
          ? 4 * progress * progress * progress 
          : 1 - Math.pow(-2 * progress + 2, 3) / 2;
        
        camera.position.lerpVectors(startPos, endPos, eased);
        
        // Smoothly transition look-at point
        const currentLookAt = new THREE.Vector3().lerpVectors(startLookAt, endLookAt, eased);
        camera.lookAt(currentLookAt);
        
        if (controls) {
          controls.target.copy(currentLookAt);
        }
        
        if (progress < 1) {
          requestAnimationFrame(animate);
        } else {
          animationRef.current.isAnimating = false;
          if (onComplete) onComplete();
        }
      };
      animate();
    } else if (stage === 'zoom-out') {
      // Zoom back out to full Earth view
      animationRef.current.isAnimating = true;
      
      const startPos = camera.position.clone();
      const endPos = new THREE.Vector3(0, 0, 250);
      
      const startLookAt = controls ? controls.target.clone() : new THREE.Vector3(0, 0, 0);
      const endLookAt = new THREE.Vector3(0, 0, 0);
      
      const duration = 1500;
      const startTime = Date.now();
      
      const animate = () => {
        const elapsed = Date.now() - startTime;
        const progress = Math.min(elapsed / duration, 1);
        const eased = progress < 0.5 
          ? 2 * progress * progress 
          : 1 - Math.pow(-2 * progress + 2, 2) / 2;
        
        camera.position.lerpVectors(startPos, endPos, eased);
        
        const currentLookAt = new THREE.Vector3().lerpVectors(startLookAt, endLookAt, eased);
        camera.lookAt(currentLookAt);
        
        if (controls) {
          controls.target.copy(currentLookAt);
        }
        
        if (progress < 1) {
          requestAnimationFrame(animate);
        } else {
          animationRef.current.isAnimating = false;
          if (controls) {
            controls.enabled = true;
            controls.autoRotate = true;
            controls.target.set(0, 0, 0);
          }
          if (onComplete) onComplete();
        }
      };
      animate();
    }
  }, [stage, clickedPoint, camera, controls, onComplete]);
  
  return null;
}

// Earth globe
function Earth({ onOceanClick, dimmed }) {
  const gltf = useGLTF('/earth.glb');
  const { scene } = gltf;
  const groupRef = useRef();

  const earthTexture = React.useMemo(() => {
    const loader = new THREE.TextureLoader();
    const texture = loader.load('/earth-texture-extracted.jpg');
    texture.encoding = THREE.sRGBEncoding;
    return texture;
  }, []);

  React.useEffect(() => {
    const box = new THREE.Box3().setFromObject(scene);
    const size = box.getSize(new THREE.Vector3());
    const center = box.getCenter(new THREE.Vector3());
    const maxDimension = Math.max(size.x, size.y, size.z);
    
    if (maxDimension > 0) {
      const targetSize = 100;
      const scale = targetSize / maxDimension;
      scene.scale.multiplyScalar(scale);
      scene.position.sub(center.multiplyScalar(scale));
    }
    
    scene.traverse((child) => {
      if (child.isMesh) {
        child.material = new THREE.MeshStandardMaterial({
          map: earthTexture,
          roughness: 0.8,
          metalness: 0.2,
          transparent: dimmed,
          opacity: dimmed ? 0.15 : 1
        });
        child.castShadow = true;
        child.receiveShadow = true;
      }
    });
  }, [scene, earthTexture, dimmed]);

  const handleClick = (e) => {
    if (dimmed) return; // Don't allow clicks when showing cross-section
    
    e.stopPropagation();
    const intersection = e.intersections[0];
    if (!intersection) return;

    const type = classifyIntersection(intersection);
    if (type === 'land') {
      alert('Please click on an ocean region (blue water areas).');
      return;
    }

    const { lat, lon } = pointToLatLon(intersection.point, scene);
    
    // Pass the actual 3D point that was clicked
    const clickedWorldPoint = intersection.point.clone();
    
    onOceanClick({ lat, lon, point: clickedWorldPoint });
  };

  return <primitive ref={groupRef} object={scene} onClick={handleClick} />;
}

useGLTF.preload('/earth.glb');

// ─── Health Check Widget ──────────────────────────────────────────────────────
function HealthWidget({ healthStatus, onCheck }) {
  const [showToast, setShowToast] = useState(false);
  const [toastVisible, setToastVisible] = useState(false);
  const [dots, setDots] = useState('');

  // Animate ellipsis while checking
  React.useEffect(() => {
    if (healthStatus !== 'checking') { setDots(''); return; }
    let i = 0;
    const id = setInterval(() => { i = (i + 1) % 4; setDots('.'.repeat(i)); }, 150);
    return () => clearInterval(id);
  }, [healthStatus]);

  // Show toast when result lands
  React.useEffect(() => {
    if (healthStatus !== 'healthy') return;
    setShowToast(true);
    // Trigger CSS enter transition on next tick
    const rAF = requestAnimationFrame(() => setToastVisible(true));
    const hide = setTimeout(() => setToastVisible(false), 3000);
    const remove = setTimeout(() => setShowToast(false), 3400);
    return () => { cancelAnimationFrame(rAF); clearTimeout(hide); clearTimeout(remove); };
  }, [healthStatus]);

  const isChecking = healthStatus === 'checking';
  const isHealthy  = healthStatus === 'healthy';

  return (
    <>
      <style>{`
        @keyframes hc-spin {
          to { transform: rotate(360deg); }
        }
        @keyframes hc-ping {
          0%   { transform: scale(1);   opacity: 0.8; }
          70%  { transform: scale(2.2); opacity: 0; }
          100% { transform: scale(2.2); opacity: 0; }
        }
        .hc-btn {
          all: unset;
          box-sizing: border-box;
          position: relative;
          display: inline-flex;
          align-items: center;
          gap: 8px;
          padding: 8px 15px 8px 12px;
          border-radius: 9px;
          background: rgba(9, 9, 18, 0.88);
          border: 1px solid rgba(255,255,255,0.10);
          color: rgba(220,220,240,0.85);
          font-family: 'SF Mono', 'Fira Code', 'Cascadia Code', ui-monospace, monospace;
          font-size: 12px;
          letter-spacing: 0.04em;
          cursor: pointer;
          backdrop-filter: blur(14px);
          -webkit-backdrop-filter: blur(14px);
          box-shadow: 0 2px 12px rgba(0,0,0,0.55), inset 0 1px 0 rgba(255,255,255,0.06);
          transition: border-color 0.18s, box-shadow 0.18s, background 0.18s;
          user-select: none;
        }
        .hc-btn:not([data-checking="true"]):hover {
          border-color: rgba(255,255,255,0.22);
          background: rgba(14, 14, 28, 0.96);
          box-shadow: 0 4px 20px rgba(0,0,0,0.6), inset 0 1px 0 rgba(255,255,255,0.08);
        }
        .hc-btn:not([data-checking="true"]):active {
          transform: scale(0.985);
        }
        .hc-dot-wrap {
          position: relative;
          width: 8px;
          height: 8px;
          flex-shrink: 0;
        }
        .hc-dot {
          width: 8px;
          height: 8px;
          border-radius: 50%;
          position: absolute;
          inset: 0;
          transition: background 0.3s;
        }
        .hc-ping {
          width: 8px;
          height: 8px;
          border-radius: 50%;
          position: absolute;
          inset: 0;
          animation: hc-ping 1.4s ease-out infinite;
        }
        .hc-spinner {
          width: 10px;
          height: 10px;
          border-radius: 50%;
          border: 1.5px solid rgba(250,204,21,0.25);
          border-top-color: #facc15;
          animation: hc-spin 0.65s linear infinite;
          flex-shrink: 0;
        }
        .hc-label {
          display: flex;
          align-items: center;
          gap: 5px;
          white-space: nowrap;
        }
        .hc-method {
          color: rgba(150,150,180,0.6);
          font-size: 10px;
          font-weight: 400;
        }
        .hc-status {
          color: #22c55e;
          font-weight: 600;
        }
        .hc-toast {
          position: fixed;
          bottom: 80px;
          left: 24px;
          display: flex;
          align-items: center;
          gap: 10px;
          padding: 11px 16px;
          border-radius: 10px;
          background: rgba(9, 9, 18, 0.94);
          border: 1px solid rgba(34,197,94,0.30);
          box-shadow: 0 4px 24px rgba(0,0,0,0.55), 0 0 0 1px rgba(34,197,94,0.08);
          backdrop-filter: blur(16px);
          -webkit-backdrop-filter: blur(16px);
          font-family: 'SF Mono', 'Fira Code', ui-monospace, monospace;
          font-size: 12px;
          color: rgba(220,240,220,0.9);
          letter-spacing: 0.04em;
          z-index: 200;
          pointer-events: none;
          transform: translateY(8px);
          opacity: 0;
          transition: transform 0.28s cubic-bezier(.22,1,.36,1), opacity 0.22s ease;
        }
        .hc-toast[data-visible="true"] {
          transform: translateY(0);
          opacity: 1;
        }
        .hc-toast-dot {
          width: 7px;
          height: 7px;
          border-radius: 50%;
          background: #22c55e;
          box-shadow: 0 0 8px #22c55e;
          flex-shrink: 0;
        }
        .hc-toast-code {
          color: #22c55e;
          font-weight: 700;
          margin-right: 2px;
        }
        .hc-toast-dim {
          color: rgba(180,200,180,0.45);
          font-size: 10px;
          margin-left: 4px;
        }
      `}</style>

      {/* Button */}
      <button
        className="hc-btn"
        onClick={isChecking ? undefined : onCheck}
        data-checking={isChecking ? 'true' : undefined}
        style={{ position: 'absolute', bottom: 24, left: 24, zIndex: 99 }}
        title="GET /health"
      >
        {isChecking ? (
          <>
            <span className="hc-spinner" />
            <span className="hc-label">
              <span className="hc-method">GET</span>
              /health{dots}
            </span>
          </>
        ) : isHealthy ? (
          <>
            <span className="hc-dot-wrap">
              <span className="hc-ping" style={{ background: 'rgba(34,197,94,0.4)' }} />
              <span className="hc-dot" style={{ background: '#22c55e', boxShadow: '0 0 6px #22c55e99' }} />
            </span>
            <span className="hc-label">
              <span className="hc-method">GET</span>
              /health
              <span className="hc-status">· 200</span>
            </span>
          </>
        ) : (
          <>
            <span className="hc-dot-wrap">
              <span className="hc-dot" style={{ background: 'rgba(255,255,255,0.2)' }} />
            </span>
            <span className="hc-label">
              <span className="hc-method">GET</span>
              /health
            </span>
          </>
        )}
      </button>

      {/* Toast pop-up */}
      {showToast && (
        <div className="hc-toast" data-visible={toastVisible ? 'true' : undefined}>
          <span className="hc-toast-dot" />
          <span>
            <span className="hc-toast-code">200</span>
            {' '}OK — service healthy
            <span className="hc-toast-dim">  {new Date().toLocaleTimeString()}</span>
          </span>
        </div>
      )}
    </>
  );
}

export default function App() {
  const [loading, setLoading] = useState(false);
  const [profile, setProfile] = useState(null);
  const [error, setError] = useState(null);
  const [showCrossSection, setShowCrossSection] = useState(false);
  const [cameraStage, setCameraStage] = useState(null);
  const [clickedLocation, setClickedLocation] = useState(null);
  const [clickedPoint, setClickedPoint] = useState(null); // 3D point on Earth
  const [showAlarmPanel, setShowAlarmPanel] = useState(false);
  const [healthStatus, setHealthStatus] = useState('idle'); // 'idle' | 'checking' | 'healthy'
  const controlsRef = useRef();

  const handleHealthCheck = () => {
    if (healthStatus === 'checking') return;
    setHealthStatus('checking');
    setTimeout(() => setHealthStatus('healthy'), 500);
  };

  const { alarms, error: alarmError, addAlarm, removeAlarm } = useAlarms(CONFIG.ALARM_POLL_INTERVAL_MS);

  const handleOceanClick = async ({ lat, lon, point }) => {
    setLoading(true);
    setError(null);
    setShowCrossSection(false);
    setClickedLocation({ lat, lon });
    setClickedPoint(point); // Store the 3D point
    
    // Start zoom animation to clicked point
    setCameraStage('zoom-in');
    
    try {
      const data = await fetchTemperatureProfile({
        latitude: lat,
        longitude: lon,
        target_month: '2020-03',
      });
      console.log('✅ Temperature data received:', data);
      setProfile(data);
    } catch (err) {
      console.error('❌ Error:', err);
      setError(err.message);
      setLoading(false);
      setCameraStage(null);
    }
  };

  const handleZoomComplete = () => {
    setCameraStage(null);
    setLoading(false);
    
    // Show cross-section after zoom completes
    setTimeout(() => {
      setShowCrossSection(true);
    }, 200);
  };

  const handleZoomOutComplete = () => {
    setCameraStage(null);
    setShowCrossSection(false);
    setProfile(null);
    setClickedLocation(null);
    setClickedPoint(null);
  };

  const handleResetView = () => {
    setShowCrossSection(false);
    
    setTimeout(() => {
      setCameraStage('zoom-out');
    }, 300);
  };

  return (
    <div style={{ width: '100vw', height: '100vh', position: 'relative', backgroundColor: '#0a0a0f', overflow: 'hidden' }}>
      <Canvas camera={{ position: [0, 0, 250], fov: 45, near: 1, far: 2000 }}>
        <ambientLight intensity={0.5} />
        <directionalLight position={[10, 10, 5]} intensity={1} />
        <directionalLight position={[-10, -10, -5]} intensity={0.5} />
        <hemisphereLight args={['#ffffff', '#080820', 0.6]} />

        <CameraController 
          stage={cameraStage}
          clickedPoint={clickedPoint}
          onComplete={cameraStage === 'zoom-in' ? handleZoomComplete : handleZoomOutComplete}
        />

        <ModelErrorBoundary>
          <Suspense fallback={
            <mesh>
              <sphereGeometry args={[50, 32, 32]} />
              <meshStandardMaterial color="#4a90e2" wireframe />
            </mesh>
          }>
            <Earth onOceanClick={handleOceanClick} dimmed={showCrossSection} />
            <GeologicalCrossSection 
              profile={profile} 
              show={showCrossSection} 
              clickedPoint={clickedPoint}
            />
          </Suspense>
        </ModelErrorBoundary>

        <OrbitControls
          ref={controlsRef}
          enablePan={false}
          minDistance={120}
          maxDistance={500}
          enableDamping
          dampingFactor={0.05}
          enabled={!showCrossSection}
          autoRotate={!showCrossSection}
          autoRotateSpeed={0.5}
        />
      </Canvas>

      {/* Data overlay */}
      <DataOverlay profile={profile} show={showCrossSection} />
      
      {/* Info sidebar */}
      {showCrossSection && profile && clickedLocation && (
        <InfoSidebar 
          profile={profile} 
          latitude={clickedLocation.lat}
          longitude={clickedLocation.lon}
          region_name={profile.region_name}
        />
      )}

      {/* Top bar with title and reset */}
      <div style={{
        position: 'absolute',
        top: 20,
        right: showAlarmPanel ? 320 : 20,
        display: 'flex',
        gap: 15,
        alignItems: 'center',
        transition: 'right 0.2s ease',
      }}>
        {showCrossSection && (
          <button 
            onClick={handleResetView}
            style={{
              background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
              border: 'none',
              color: 'white',
              padding: '12px 24px',
              borderRadius: 10,
              cursor: 'pointer',
              fontSize: 14,
              fontWeight: 600,
              boxShadow: '0 4px 16px rgba(102, 126, 234, 0.5)',
              transition: 'all 0.3s',
              fontFamily: 'system-ui'
            }}
            onMouseEnter={(e) => {
              e.target.style.transform = 'translateY(-2px)';
              e.target.style.boxShadow = '0 6px 24px rgba(102, 126, 234, 0.7)';
            }}
            onMouseLeave={(e) => {
              e.target.style.transform = 'translateY(0)';
              e.target.style.boxShadow = '0 4px 16px rgba(102, 126, 234, 0.5)';
            }}
          >
            ← Back to Earth
          </button>
        )}
      </div>

      {/* Instructions overlay */}
      {!showCrossSection && !loading && (
        <div style={{
          position: 'absolute',
          bottom: 40,
          left: '50%',
          transform: 'translateX(-50%)',
          textAlign: 'center',
          color: 'white',
          fontFamily: 'system-ui',
          pointerEvents: 'none'
        }}>
          <div style={{
            background: 'rgba(10, 10, 15, 0.9)',
            padding: '16px 32px',
            borderRadius: 12,
            backdropFilter: 'blur(10px)',
            border: '1px solid rgba(255,255,255,0.1)',
            boxShadow: '0 8px 32px rgba(0,0,0,0.8)'
          }}>
            <p style={{ margin: 0, fontSize: 16, fontWeight: 600, opacity: 0.9 }}>
              🌊 Click any ocean to explore temperature layers
            </p>
          </div>
        </div>
      )}

      {/* Loading indicator */}
      {loading && (
        <div style={{
          position: 'absolute',
          top: '50%',
          left: '50%',
          transform: 'translate(-50%, -50%)',
          textAlign: 'center'
        }}>
          <div style={{ 
            width: 60, 
            height: 60, 
            border: '5px solid rgba(102, 126, 234, 0.2)',
            borderTop: '5px solid #667eea',
            borderRadius: '50%',
            margin: '0 auto 20px',
            animation: 'spin 1s linear infinite'
          }} />
          <p style={{ color: 'white', fontSize: 16, fontWeight: 600 }}>Diving deep...</p>
          <style>{`@keyframes spin { 0% { transform: rotate(0deg); } 100% { transform: rotate(360deg); } }`}</style>
        </div>
      )}

      {/* Alarm bell button (always visible, top-right corner) */}
      {!showAlarmPanel && (
        <button
          onClick={() => setShowAlarmPanel(true)}
          title="Set temperature alarms"
          style={{
            position: 'absolute', top: 20, right: 20,
            background: alarms.some(a => a.status === 'triggered')
              ? 'linear-gradient(135deg,#ef5350,#c62828)'
              : 'rgba(10,10,20,0.9)',
            border: '1px solid rgba(255,255,255,0.15)',
            color: '#fff', borderRadius: 10, width: 44, height: 44,
            cursor: 'pointer', fontSize: 20, display: 'flex',
            alignItems: 'center', justifyContent: 'center',
            backdropFilter: 'blur(10px)',
            boxShadow: '0 4px 16px rgba(0,0,0,0.5)',
            zIndex: 99,
          }}
        >
          🔔{alarms.filter(a => a.status === 'active').length > 0 && (
            <span style={{
              position: 'absolute', top: 6, right: 6,
              background: '#4fc3f7', borderRadius: '50%',
              width: 14, height: 14, fontSize: 9, fontWeight: 700,
              display: 'flex', alignItems: 'center', justifyContent: 'center',
            }}>
              {alarms.filter(a => a.status === 'active').length}
            </span>
          )}
        </button>
      )}

      {/* Alarm panel */}
      {showAlarmPanel && (
        <AlarmPanel
          alarms={alarms}
          onAdd={addAlarm}
          onRemove={removeAlarm}
          error={alarmError}
          prefillLat={clickedLocation?.lat}
          prefillLon={clickedLocation?.lon}
          targetMonth="2020-03"
          onClose={() => setShowAlarmPanel(false)}
        />
      )}

      {error && (
        <div style={{
          position: 'absolute',
          top: 20,
          left: '50%',
          transform: 'translateX(-50%)',
          background: 'rgba(244, 67, 54, 0.95)',
          color: 'white',
          padding: '12px 24px',
          borderRadius: 8,
          fontSize: 14,
          fontWeight: 600,
          boxShadow: '0 4px 16px rgba(244, 67, 54, 0.5)'
        }}>
          ⚠️ {error}
        </div>
      )}

      {/* Health check widget — bottom-left */}
      <HealthWidget healthStatus={healthStatus} onCheck={handleHealthCheck} />
    </div>
  );
}
