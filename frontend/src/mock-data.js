/**
 * Mock ocean temperature data for different regions
 * Each region has realistic temperature profiles based on geographic location
 */

const DEPTHS = [30, 50, 75, 100, 125, 150, 200, 250, 300, 400, 500, 600, 700, 800, 900, 1000, 1100, 1200, 1300, 1400, 1500, 1750, 2000];

// Helper function to generate realistic temperature gradients
function generateTempProfile(surfaceTemp, deepTemp, thermoclineDepth = 200) {
  return DEPTHS.map(depth => {
    if (depth < thermoclineDepth) {
      // Linear decrease in thermocline
      const ratio = depth / thermoclineDepth;
      return surfaceTemp - (surfaceTemp - deepTemp) * ratio * 0.7;
    } else {
      // Slower decrease in deep ocean
      const deepRatio = (depth - thermoclineDepth) / (2000 - thermoclineDepth);
      return deepTemp + (surfaceTemp - deepTemp) * 0.3 * Math.exp(-deepRatio * 2);
    }
  });
}

// Mock data for different ocean regions
export const MOCK_OCEAN_DATA = {
  // Tropical regions (warm)
  tropical_pacific: {
    name: "Tropical Pacific",
    latitude_range: [-5, 5],
    longitude_range: [-180, -120],
    surfaceTemp: 28.5,
    deepTemp: 2.1,
    thermoclineDepth: 150
  },
  
  arabian_sea: {
    name: "Arabian Sea",
    latitude_range: [10, 20],
    longitude_range: [60, 75],
    surfaceTemp: 29.2,
    deepTemp: 2.3,
    thermoclineDepth: 180
  },
  
  caribbean: {
    name: "Caribbean Sea",
    latitude_range: [10, 20],
    longitude_range: [-85, -60],
    surfaceTemp: 27.8,
    deepTemp: 2.5,
    thermoclineDepth: 160
  },

  // Subtropical regions (moderate-warm)
  mediterranean: {
    name: "Mediterranean Sea",
    latitude_range: [30, 40],
    longitude_range: [10, 30],
    surfaceTemp: 24.5,
    deepTemp: 13.5,
    thermoclineDepth: 200
  },
  
  south_china_sea: {
    name: "South China Sea",
    latitude_range: [5, 20],
    longitude_range: [105, 120],
    surfaceTemp: 28.1,
    deepTemp: 2.8,
    thermoclineDepth: 170
  },

  // Temperate regions (moderate)
  north_atlantic: {
    name: "North Atlantic",
    latitude_range: [35, 45],
    longitude_range: [-50, -30],
    surfaceTemp: 18.5,
    deepTemp: 3.2,
    thermoclineDepth: 250
  },
  
  south_atlantic: {
    name: "South Atlantic",
    latitude_range: [-35, -25],
    longitude_range: [-40, -20],
    surfaceTemp: 19.8,
    deepTemp: 3.1,
    thermoclineDepth: 230
  },
  
  indian_ocean: {
    name: "Indian Ocean",
    latitude_range: [-20, -10],
    longitude_range: [70, 90],
    surfaceTemp: 26.4,
    deepTemp: 2.6,
    thermoclineDepth: 190
  },

  // Cold regions
  north_pacific: {
    name: "North Pacific",
    latitude_range: [40, 50],
    longitude_range: [-160, -140],
    surfaceTemp: 12.3,
    deepTemp: 2.1,
    thermoclineDepth: 300
  },
  
  southern_ocean: {
    name: "Southern Ocean",
    latitude_range: [-60, -50],
    longitude_range: [0, 50],
    surfaceTemp: 3.5,
    deepTemp: 0.8,
    thermoclineDepth: 400
  },

  // Polar regions (very cold)
  arctic_ocean: {
    name: "Arctic Ocean",
    latitude_range: [70, 85],
    longitude_range: [-180, 180],
    surfaceTemp: -1.2,
    deepTemp: -0.5,
    thermoclineDepth: 500
  },

  // Special regions
  gulf_of_mexico: {
    name: "Gulf of Mexico",
    latitude_range: [20, 30],
    longitude_range: [-95, -85],
    surfaceTemp: 26.7,
    deepTemp: 4.2,
    thermoclineDepth: 180
  }
};

/**
 * Find the closest region based on latitude and longitude
 */
function findClosestRegion(lat, lon) {
  let closestRegion = null;
  let minDistance = Infinity;

  for (const [key, region] of Object.entries(MOCK_OCEAN_DATA)) {
    const latMid = (region.latitude_range[0] + region.latitude_range[1]) / 2;
    const lonMid = (region.longitude_range[0] + region.longitude_range[1]) / 2;
    
    const distance = Math.sqrt(
      Math.pow(lat - latMid, 2) + 
      Math.pow(lon - lonMid, 2)
    );

    if (distance < minDistance) {
      minDistance = distance;
      closestRegion = { key, ...region };
    }
  }

  return closestRegion;
}

/**
 * Generate mock temperature profile for given coordinates
 */
export function generateMockProfile({ latitude, longitude, target_month }) {
  const region = findClosestRegion(latitude, longitude);
  
  // Add seasonal variation (approximate)
  const month = target_month ? parseInt(target_month.split('-')[1]) : 3;
  const seasonalOffset = latitude >= 0
    ? Math.sin((month - 3) * Math.PI / 6) * 2.5  // Northern hemisphere
    : Math.sin((month - 9) * Math.PI / 6) * 2.5; // Southern hemisphere
  
  const adjustedSurfaceTemp = region.surfaceTemp + seasonalOffset;
  
  // Generate temperature profile
  const temperatures = generateTempProfile(
    adjustedSurfaceTemp,
    region.deepTemp,
    region.thermoclineDepth
  );

  // Add small random variations to make it more realistic
  const temperatureWithNoise = temperatures.map(temp => 
    temp + (Math.random() - 0.5) * 0.3
  );

  return {
    latitude: parseFloat(latitude.toFixed(2)),
    longitude: parseFloat(longitude.toFixed(2)),
    grid_latitude: parseFloat(latitude.toFixed(1)),
    grid_longitude: parseFloat(longitude.toFixed(1)),
    target_month: target_month || '2020-03',
    region_name: region.name,
    depths_m: DEPTHS,
    temperature_celsius: temperatureWithNoise.map(t => parseFloat(t.toFixed(2))),
    model_version: 'mock-v1'
  };
}

/**
 * Simulate API delay for realistic mock
 */
export async function fetchMockProfile(params) {
  // Simulate network delay
  await new Promise(resolve => setTimeout(resolve, 300 + Math.random() * 400));
  
  return generateMockProfile(params);
}
