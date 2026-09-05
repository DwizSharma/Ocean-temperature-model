import React, { useState, Suspense, useRef } from 'react';
import { Canvas, useThree } from '@react-three/fiber';
import { OrbitControls, useGLTF } from '@react-three/drei';
import * as THREE from 'three';

import { pointToLatLon, formatLat, formatLon, formatMonth } from './geo';
import { classifyIntersection } from './ocean-detection';
import { fetchTemperatureProfile } from './ocean-api';
import { temperatureToCSS, makeNormalizer } from './color-scale';

function TemperatureLayers({ profile }) {
  if (!profile) return null;

  const { depths_m, temperature_celsius, latitude, longitude, target_month } = profile;
  
  // Create normalizer for color coding
  const normalize = makeNormalizer(temperature_celsius);

  return (
    <div>
      <div style={{ marginBottom: 16 }}>
        <h3 style={{ margin: '0 0 8px 0', fontSize: 16 }}>Location</h3>
        <p style={{ fontSize: 14, margin: 0, opacity: 0.9 }}>
          {formatLat(latitude)} {formatLon(longitude)}
          {target_month && <> • {formatMonth(target_month)}</>}
        </p>
      </div>
      
      <div style={{ marginBottom: 12 }}>
        <h3 style={{ margin: '0 0 8px 0', fontSize: 16 }}>Temperature Profile</h3>
        <p style={{ fontSize: 12, opacity: 0.7, margin: 0 }}>
          {depths_m.length} depth measurements
        </p>
      </div>

      <div style={{ maxHeight: 400, overflowY: 'auto' }}>
        <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: 13 }}>
          <thead style={{ position: 'sticky', top: 0, background: 'rgba(20, 20, 25, 0.95)', zIndex: 1 }}>
            <tr style={{ borderBottom: '2px solid rgba(255,255,255,0.3)' }}>
              <th style={{ textAlign: 'left', padding: '8px 4px' }}>Depth (m)</th>
              <th style={{ textAlign: 'right', padding: '8px 4px' }}>Temp (°C)</th>
              <th style={{ textAlign: 'center', padding: '8px 4px', width: 60 }}>Color</th>
            </tr>
          </thead>
          <tbody>
            {depths_m.map((d, i) => {
              const temp = temperature_celsius[i];
              const normalizedTemp = normalize(temp);
              const color = temperatureToCSS(normalizedTemp);
              
              return (
                <tr key={i} style={{ 
                  borderBottom: '1px solid rgba(255,255,255,0.08)',
                  transition: 'background 0.2s'
                }}>
                  <td style={{ padding: '6px 4px', fontWeight: 500 }}>{d.toFixed(0)}</td>
                  <td style={{ padding: '6px 4px', textAlign: 'right', fontFamily: 'monospace' }}>
                    {temp.toFixed(2)}
                  </td>
                  <td style={{ padding: '6px 4px', textAlign: 'center' }}>
                    <div style={{
                      width: 40,
                      height: 20,
                      background: color,
                      borderRadius: 3,
                      margin: '0 auto',
                      border: '1px solid rgba(255,255,255,0.2)'
                    }} />
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>

      {/* Temperature Legend */}
      <div style={{ marginTop: 16, padding: 12, background: 'rgba(0,0,0,0.3)', borderRadius: 6 }}>
        <p style={{ fontSize: 11, opacity: 0.8, margin: '0 0 8px 0', textTransform: 'uppercase', letterSpacing: '0.5px' }}>
          Temperature Scale
        </p>
        <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
          <span style={{ fontSize: 11 }}>Cold</span>
          <div style={{ 
            flex: 1, 
            height: 20, 
            background: 'linear-gradient(to right, #2b1454, #2354a8, #229ebc, #62c779, #f2c444, #e0543f)',
            borderRadius: 3,
            border: '1px solid rgba(255,255,255,0.2)'
          }} />
          <span style={{ fontSize: 11 }}>Warm</span>
        </div>
        <div style={{ display: 'flex', justifyContent: 'space-between', marginTop: 4, fontSize: 10, opacity: 0.7 }}>
          <span>{Math.min(...temperature_celsius).toFixed(1)}°C</span>
          <span>{Math.max(...temperature_celsius).toFixed(1)}°C</span>
        </div>
      </div>
    </div>
  );
}

class ModelErrorBoundary extends React.Component {
  state = { error: null };

  static getDerivedStateFromError(error) {
    return { error };
  }

  componentDidCatch(error, info) {
    console.error('GLTF failed to load:', error, info);
  }

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

function CameraController({ targetPosition, shouldZoom, onZoomComplete }) {
  const { camera } = useThree();
  const isAnimatingRef = useRef(false);
  
  React.useEffect(() => {
    if (shouldZoom && targetPosition && !isAnimatingRef.current) {
      isAnimatingRef.current = true;
      
      // Smoothly zoom to the clicked location
      const startPosition = camera.position.clone();
      const duration = 1500; // ms
      const startTime = Date.now();
      
      const animate = () => {
        const elapsed = Date.now() - startTime;
        const progress = Math.min(elapsed / duration, 1);
        
        // Ease-in-out function
        const eased = progress < 0.5
          ? 2 * progress * progress
          : 1 - Math.pow(-2 * progress + 2, 2) / 2;
        
        camera.position.lerpVectors(startPosition, targetPosition, eased);
        camera.lookAt(0, 0, 0);
        
        if (progress < 1) {
          requestAnimationFrame(animate);
        } else {
          isAnimatingRef.current = false;
          if (onZoomComplete) onZoomComplete();
        }
      };
      
      animate();
    }
  }, [targetPosition, shouldZoom, camera, onZoomComplete]);
  
  return null;
}

function Earth({ onOceanClick, onZoomToPoint }) {
  const gltf = useGLTF('/earth.glb');
  const { scene } = gltf;

  // Load the extracted texture
  const earthTexture = React.useMemo(() => {
    const loader = new THREE.TextureLoader();
    const texture = loader.load('/earth-texture-extracted.jpg',
      () => console.log('✅ Texture loaded successfully'),
      undefined,
      (error) => console.error('❌ Error loading texture:', error)
    );
    texture.encoding = THREE.sRGBEncoding;
    return texture;
  }, []);

  // Fix materials and scale
  React.useEffect(() => {
    console.log('🌍 Setting up Earth model...');

    // Calculate bounding box and scale
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

    // Apply texture to all meshes
    let meshCount = 0;
    scene.traverse((child) => {
      if (child.isMesh) {
        meshCount++;
        console.log(`Applying texture to mesh ${meshCount}: ${child.name}`);

        // Replace material with textured one
        child.material = new THREE.MeshStandardMaterial({
          map: earthTexture,
          roughness: 0.8,
          metalness: 0.2
        });

        child.castShadow = true;
        child.receiveShadow = true;
      }
    });

    console.log(`✅ Applied texture to ${meshCount} mesh(es)`);
  }, [scene, earthTexture]);

  const handleClick = (e) => {
    e.stopPropagation();
    const intersection = e.intersections[0];
    if (!intersection) return;

    const type = classifyIntersection(intersection);
    if (type === 'land') {
      alert('Clicked land. Please click an ocean region.');
      return;
    }

    const { lat, lon } = pointToLatLon(intersection.point, scene);
    
    // Zoom to the clicked point
    const clickPoint = intersection.point.clone().normalize().multiplyScalar(150);
    onZoomToPoint(clickPoint);
    
    onOceanClick({ lat, lon });
  };

  return <primitive object={scene} onClick={handleClick} />;
}

// Preload the model before the component renders
useGLTF.preload('/earth.glb');

export default function App() {
  const [loading, setLoading] = useState(false);
  const [profile, setProfile] = useState(null);
  const [error, setError] = useState(null);
  const [zoomTarget, setZoomTarget] = useState(null);
  const [shouldZoom, setShouldZoom] = useState(false);
  const controlsRef = useRef();

  const handleOceanClick = async ({ lat, lon }) => {
    setLoading(true);
    setError(null);
    try {
      const data = await fetchTemperatureProfile({
        latitude: lat,
        longitude: lon,
        target_month: '2020-03',
      });
      console.log('✅ Received temperature data:', data);
      setProfile(data);
    } catch (err) {
      console.error('❌ Failed to fetch temperature data:', err);
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleZoomToPoint = (point) => {
    setZoomTarget(point);
    setShouldZoom(true);
  };

  const handleZoomComplete = () => {
    setShouldZoom(false);
  };

  const handleResetView = () => {
    setZoomTarget(new THREE.Vector3(0, 0, 250));
    setShouldZoom(true);
    setProfile(null);
    setError(null);
  };

  return (
    <div style={{ width: '100vw', height: '100vh', position: 'relative', backgroundColor: '#050505' }}>
      <Canvas camera={{ position: [0, 0, 250], fov: 45, near: 1, far: 2000 }}>
        {/* Better lighting setup for Earth */}
        <ambientLight intensity={0.3} />
        <directionalLight position={[5, 3, 5]} intensity={1} />
        <directionalLight position={[-5, -3, -5]} intensity={0.5} />
        <hemisphereLight args={['#ffffff', '#080820', 0.4]} />

        <CameraController 
          targetPosition={zoomTarget} 
          shouldZoom={shouldZoom}
          onZoomComplete={handleZoomComplete}
        />

        <ModelErrorBoundary>
          <Suspense fallback={
            <mesh>
              <sphereGeometry args={[50, 32, 32]} />
              <meshStandardMaterial color="#4a90e2" wireframe />
            </mesh>
          }>
            <Earth 
              onOceanClick={handleOceanClick}
              onZoomToPoint={handleZoomToPoint}
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
        />
      </Canvas>

      {/* UI Overlay */}
      <div
        style={{
          position: 'absolute',
          top: 20,
          right: 20,
          width: 360,
          maxHeight: 'calc(100vh - 40px)',
          backgroundColor: 'rgba(20, 20, 25, 0.95)',
          color: 'white',
          padding: 20,
          borderRadius: 12,
          fontFamily: 'system-ui, -apple-system, sans-serif',
          overflowY: 'auto',
          boxShadow: '0 8px 32px rgba(0,0,0,0.6)',
          backdropFilter: 'blur(10px)',
          border: '1px solid rgba(255,255,255,0.1)'
        }}
      >
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16 }}>
          <h2 style={{ margin: 0, fontSize: 20, fontWeight: 600 }}>Ocean Temperature Analysis</h2>
          {profile && (
            <button 
              onClick={handleResetView}
              style={{
                background: 'rgba(255,255,255,0.1)',
                border: '1px solid rgba(255,255,255,0.2)',
                color: 'white',
                padding: '6px 12px',
                borderRadius: 6,
                cursor: 'pointer',
                fontSize: 12,
                fontWeight: 500,
                transition: 'all 0.2s'
              }}
              onMouseOver={(e) => e.target.style.background = 'rgba(255,255,255,0.2)'}
              onMouseOut={(e) => e.target.style.background = 'rgba(255,255,255,0.1)'}
            >
              Reset View
            </button>
          )}
        </div>

        {loading && (
          <div style={{ textAlign: 'center', padding: '40px 0' }}>
            <div style={{ 
              width: 40, 
              height: 40, 
              border: '3px solid rgba(255,255,255,0.1)',
              borderTop: '3px solid white',
              borderRadius: '50%',
              margin: '0 auto 16px',
              animation: 'spin 1s linear infinite'
            }} />
            <p style={{ margin: 0, opacity: 0.8 }}>Fetching temperature data...</p>
            <style>{`
              @keyframes spin {
                0% { transform: rotate(0deg); }
                100% { transform: rotate(360deg); }
              }
            `}</style>
          </div>
        )}
        
        {error && (
          <div style={{ 
            padding: 16, 
            background: 'rgba(224, 84, 63, 0.15)', 
            border: '1px solid rgba(224, 84, 63, 0.4)',
            borderRadius: 8,
            color: '#ff9999'
          }}>
            <strong style={{ display: 'block', marginBottom: 8 }}>⚠️ Error</strong>
            {error}
          </div>
        )}
        
        {!loading && !profile && !error && (
          <div style={{ 
            textAlign: 'center', 
            padding: '40px 20px',
            background: 'rgba(255,255,255,0.03)',
            borderRadius: 8,
            border: '1px dashed rgba(255,255,255,0.2)'
          }}>
            <div style={{ fontSize: 48, marginBottom: 16 }}>🌊</div>
            <p style={{ margin: '0 0 8px 0', fontSize: 15, fontWeight: 500 }}>
              Click on the ocean to view temperature profile
            </p>
            <p style={{ margin: 0, fontSize: 13, opacity: 0.6 }}>
              Data from the last 20 years
            </p>
          </div>
        )}

        {profile && !loading && <TemperatureLayers profile={profile} />}
      </div>
    </div>
  );
}
