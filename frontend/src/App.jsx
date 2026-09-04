import React, { useState, Suspense } from 'react';
import { Canvas } from '@react-three/fiber';
import { OrbitControls, useGLTF, Html } from '@react-three/drei';
import * as THREE from 'three';

import { pointToLatLon, formatLat, formatLon, formatMonth } from './geo';
import { classifyIntersection } from './ocean-detection';
import { fetchTemperatureProfile } from './ocean-api';

function TemperatureLayers({ profile }) {
  if (!profile) return null;

  const { depths_m, temperature_celsius, latitude, longitude, target_month } = profile;

  return (
    <div>
      <p style={{ fontSize: 14, marginBottom: 8 }}>
        {formatLat(latitude)} {formatLon(longitude)}
        {target_month && <> &middot; {formatMonth(target_month)}</>}
      </p>
      <div style={{ maxHeight: 300, overflowY: 'auto' }}>
        <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: 13 }}>
          <thead>
            <tr style={{ borderBottom: '1px solid rgba(255,255,255,0.2)' }}>
              <th style={{ textAlign: 'left', padding: '4px 0' }}>Depth (m)</th>
              <th style={{ textAlign: 'right', padding: '4px 0' }}>&deg;C</th>
            </tr>
          </thead>
          <tbody>
            {depths_m.map((d, i) => (
              <tr key={i} style={{ borderBottom: '1px solid rgba(255,255,255,0.05)' }}>
                <td style={{ padding: '3px 0' }}>{d.toFixed(1)}</td>
                <td style={{ padding: '3px 0', textAlign: 'right' }}>{temperature_celsius[i].toFixed(2)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}

// -----------------------------------------------------------------------
// Error boundary: Suspense only covers the *loading* state. If the GLTF
// load rejects (bad path, corrupt file, parser error, CORS, etc.) that
// error is NOT caught by Suspense — it just disappears and your fallback
// (null) stays up forever, which looks identical to "stuck loading".
// This boundary makes load failures visible instead of silent.
// -----------------------------------------------------------------------
class ModelErrorBoundary extends React.Component {
  state = { error: null };

  static getDerivedStateFromError(error) {
    return { error };
  }

  componentDidCatch(error, info) {
    // This is the line to watch in your console — it will tell you
    // exactly why the model failed to load.
    console.error('GLTF failed to load:', error, info);
  }

  render() {
    if (this.state.error) {
      return (
        <mesh>
          <sphereGeometry args={[1, 32, 32]} />
          <meshStandardMaterial color="red" wireframe />
        </mesh>
      );
    }
    return this.props.children;
  }
}

function Earth({ onOceanClick }) {
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

  const handleOceanClick = async ({ lat, lon }) => {
    setLoading(true);
    setError(null);
    try {
      const data = await fetchTemperatureProfile({
        latitude: lat,
        longitude: lon,
        target_month: '2020-03',
      });
      setProfile(data);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={{ width: '100vw', height: '100vh', position: 'relative', backgroundColor: '#050505' }}>
      <Canvas camera={{ position: [0, 0, 250], fov: 45, near: 1, far: 2000 }}>
        {/* Better lighting setup for Earth */}
        <ambientLight intensity={0.3} />
        <directionalLight position={[5, 3, 5]} intensity={1} />
        <directionalLight position={[-5, -3, -5]} intensity={0.5} />
        <hemisphereLight args={['#ffffff', '#080820', 0.4]} />

        <ModelErrorBoundary>
          <Suspense fallback={
            <mesh>
              <sphereGeometry args={[50, 32, 32]} />
              <meshStandardMaterial color="#4a90e2" wireframe />
            </mesh>
          }>
            <Earth onOceanClick={handleOceanClick} />
          </Suspense>
        </ModelErrorBoundary>

        <OrbitControls
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
          width: 320,
          maxHeight: 'calc(100vh - 40px)',
          backgroundColor: 'rgba(20, 20, 25, 0.9)',
          color: 'white',
          padding: 20,
          borderRadius: 8,
          fontFamily: 'sans-serif',
          overflowY: 'auto',
          boxShadow: '0 4px 20px rgba(0,0,0,0.5)',
          backdropFilter: 'blur(10px)',
        }}
      >
        <h2>Ocean Temperature</h2>

        {loading && <p>Fetching data...</p>}
        {error && <p style={{ color: '#ff6b6b' }}>{error}</p>}
        {!loading && !profile && <p>Click on the ocean to view the temperature profile.</p>}

        {profile && !loading && <TemperatureLayers profile={profile} />}
      </div>
    </div>
  );
}
