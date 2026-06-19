import os
import json
import math
import numpy as np
from shapely.geometry import Polygon, Point

# India landmass outline (roughly approximated)
india_poly = Polygon([
    (68.1, 23.7), # West border / Gujarat
    (72.5, 24.5), # Rajasthan West
    (73.8, 29.0), # Punjab/Rajasthan
    (74.5, 34.5), # Kashmir West
    (77.0, 36.5), # Kashmir North Tip
    (80.2, 34.0), # Ladakh East
    (79.5, 30.5), # Uttarakhand border
    (80.3, 28.5), # Nepal West
    (88.0, 27.5), # Sikkim / Nepal East
    (91.5, 27.8), # Arunachal West
    (97.2, 28.2), # Arunachal East Tip (East border)
    (95.3, 24.5), # Nagaland / Manipur
    (92.2, 22.0), # Mizoram/Tripura
    (89.0, 22.0), # Bangladesh border
    (88.0, 24.0), # West Bengal
    (87.0, 21.5), # Odisha Coast
    (83.0, 18.0), # Andhra North Coast
    (80.2, 13.5), # Chennai Coast
    (79.8, 9.2),  # Tamil Nadu South Tip (Kanyakumari)
    (77.2, 8.1),  # Kerala South
    (76.0, 10.5), # Kerala Coast
    (74.5, 15.0), # Goa/Karnataka Coast
    (72.8, 19.0), # Mumbai Coast
    (68.1, 23.7)  # Close loop
])

# Resolve output data directory relative to this script
script_dir = os.path.dirname(os.path.abspath(__file__)) # backend/app
data_dir = os.path.join(os.path.dirname(script_dir), "data") # backend/data

def generate_india_grid():
    print("Generating representative India state-wide geospatial dataset...")
    grid_size = 60 # 60x60 grid = 3600 potential cells
    lats = np.linspace(8.0, 36.5, grid_size)
    lons = np.linspace(68.0, 97.5, grid_size)
    
    cities = [
        {"name": "Delhi NCR", "lat": 28.6139, "lon": 77.2090, "lst_mod": 4.5, "built_val": 0.96, "pop_val": 42000.0, "ndvi_val": 0.08},
        {"name": "Mumbai", "lat": 19.0760, "lon": 72.8777, "lst_mod": -2.0, "built_val": 0.95, "pop_val": 45000.0, "ndvi_val": 0.12},
        {"name": "Bengaluru", "lat": 12.9716, "lon": 77.5946, "lst_mod": -1.0, "built_val": 0.90, "pop_val": 32000.0, "ndvi_val": 0.18},
        {"name": "Kolkata", "lat": 22.5726, "lon": 88.3639, "lst_mod": 1.5, "built_val": 0.92, "pop_val": 35000.0, "ndvi_val": 0.11},
        {"name": "Chennai", "lat": 13.0827, "lon": 80.2707, "lst_mod": 2.0, "built_val": 0.92, "pop_val": 30000.0, "ndvi_val": 0.10},
        {"name": "Hyderabad", "lat": 17.3850, "lon": 78.4867, "lst_mod": 2.5, "built_val": 0.88, "pop_val": 25000.0, "ndvi_val": 0.15}
    ]
    
    grid = []
    np.random.seed(42)
    cell_id = 0
    
    for i, lat in enumerate(lats):
        for j, lon in enumerate(lons):
            point = Point(lon, lat)
            
            # Check if point is inside India land boundary
            if not india_poly.contains(point):
                continue
                
            # Determine Regional Climatic Zones
            is_himalayas = lat >= 30.0
            is_thar = (lat >= 23.0) and (lon < 75.0) and (not is_himalayas)
            is_gangetic = (23.0 <= lat < 30.0) and (75.0 <= lon < 89.0) and (not is_himalayas)
            is_ghats = (lat < 20.0) and (lon < 76.5)
            is_northeast = (lon >= 89.0) and (not is_himalayas)
            is_deccan = (lat < 23.0) and (75.0 <= lon < 85.0) and (not is_ghats)
            
            # Establish Baseline Values based on regional climate zones
            if is_himalayas:
                base_lst = 16.0 + (36.5 - lat) * 1.5 + np.random.normal(0, 1.2)
                base_ndvi = 0.65 + np.random.normal(0, 0.06)
                base_built = 0.08 + np.random.normal(0, 0.02)
                base_pop = 500.0 + np.random.normal(0, 150)
            elif is_thar:
                base_lst = 44.5 + np.random.normal(0, 0.6)
                base_ndvi = 0.08 + np.random.normal(0, 0.02)
                base_built = 0.15 + np.random.normal(0, 0.04)
                base_pop = 600.0 + np.random.normal(0, 150)
            elif is_gangetic:
                base_lst = 41.5 + np.random.normal(0, 0.5)
                base_ndvi = 0.28 + np.random.normal(0, 0.04)
                base_built = 0.35 + np.random.normal(0, 0.08)
                base_pop = 6500.0 + np.random.normal(0, 1200)
            elif is_ghats:
                base_lst = 29.0 + np.random.normal(0, 0.6)
                base_ndvi = 0.74 + np.random.normal(0, 0.05)
                base_built = 0.12 + np.random.normal(0, 0.03)
                base_pop = 1200.0 + np.random.normal(0, 300)
            elif is_northeast:
                base_lst = 27.5 + np.random.normal(0, 0.8)
                base_ndvi = 0.78 + np.random.normal(0, 0.04)
                base_built = 0.10 + np.random.normal(0, 0.02)
                base_pop = 1000.0 + np.random.normal(0, 200)
            else: # is_deccan
                base_lst = 38.5 + np.random.normal(0, 0.7)
                base_ndvi = 0.22 + np.random.normal(0, 0.03)
                base_built = 0.26 + np.random.normal(0, 0.05)
                base_pop = 2400.0 + np.random.normal(0, 600)
                
            # Factor in City centers
            for city in cities:
                dist = math.sqrt((lat - city["lat"])**2 + (lon - city["lon"])**2)
                if dist < 1.2:
                    influence = (1.2 - dist) / 1.2
                    base_built = max(base_built, city["built_val"] * influence)
                    base_pop = max(base_pop, city["pop_val"] * influence)
                    base_ndvi = max(0.04, base_ndvi - 0.4 * influence)
                    base_lst += city["lst_mod"] * influence + (10.0 * base_built * influence)
            
            # Final Clamping
            lst = np.clip(base_lst, 10.0, 52.0)
            ndvi = np.clip(base_ndvi, 0.05, 0.90)
            built_up = np.clip(base_built, 0.02, 0.98)
            pop_density = np.clip(base_pop, 50.0, 48000.0)
            
            grid.append({
                "id": cell_id,
                "lat": float(lat),
                "lon": float(lon),
                "lst": round(float(lst), 2),
                "ndvi": round(float(ndvi), 3),
                "built_up": round(float(built_up), 3),
                "pop_density": round(float(pop_density), 1)
            })
            cell_id += 1
            
    out_path = os.path.join(data_dir, "india_grid.json")
    with open(out_path, "w") as f:
        json.dump(grid, f, indent=2)
    print(f"India dataset generated! Active landmass cells: {len(grid)}")

def generate_city_grid(city_name, center_lat, center_lon, filename):
    print(f"Generating high-resolution {city_name} geospatial grid...")
    grid_size = 40 # 40x40 grid = 1600 points
    lats = np.linspace(center_lat - 0.2, center_lat + 0.2, grid_size)
    lons = np.linspace(center_lon - 0.2, center_lon + 0.2, grid_size)
    
    grid = []
    np.random.seed(100 + len(city_name))
    cell_id = 0
    
    for lat in lats:
        for lon in lons:
            dist_to_center = math.sqrt((lat - center_lat)**2 + (lon - center_lon)**2)
            
            # Mumbai coast masking
            if city_name == "Mumbai" and lon < 72.81:
                lst = 27.5 + np.random.normal(0, 0.2)
                ndvi = 0.12 + np.random.normal(0, 0.01)
                built_up = 0.02
                pop_density = 0.0
            else:
                influence = max(0.0, (0.24 - dist_to_center) / 0.24) # peaks at center
                
                # Base parameters per city
                if city_name == "Bengaluru":
                    base_lst = 29.5 + np.random.normal(0, 0.4)
                    base_ndvi = 0.38 + np.random.normal(0, 0.04)
                    base_built = 0.28 + np.random.normal(0, 0.05)
                    base_pop = 4000.0 + np.random.normal(0, 800)
                elif city_name == "Mumbai":
                    base_lst = 31.0 + np.random.normal(0, 0.5)
                    base_ndvi = 0.22 + np.random.normal(0, 0.03)
                    base_built = 0.45 + np.random.normal(0, 0.05)
                    base_pop = 16000.0 + np.random.normal(0, 1500)
                else: # Delhi NCR
                    base_lst = 39.0 + np.random.normal(0, 0.6)
                    base_ndvi = 0.16 + np.random.normal(0, 0.02)
                    base_built = 0.42 + np.random.normal(0, 0.05)
                    base_pop = 14000.0 + np.random.normal(0, 1200)
                    
                # Proximity updates
                built_up = np.clip(base_built + 0.54 * influence, 0.02, 0.98)
                pop_density = np.clip(base_pop + 28000.0 * influence, 50.0, 48000.0)
                ndvi = np.clip(base_ndvi - 0.26 * influence, 0.05, 0.90)
                lst = np.clip(base_lst + 9.0 * built_up * influence + np.random.normal(0, 0.4), 10.0, 52.0)
                
                # Custom local features
                if city_name == "Bengaluru":
                    # Cubbon Park
                    if 0.02 < dist_to_center < 0.05 and lat > center_lat:
                        ndvi = 0.72
                        lst -= 4.0
                        built_up = 0.04
                    # Lakes
                    if (abs(lat - 13.04) < 0.012 and abs(lon - 77.59) < 0.012) or \
                       (abs(lat - 12.93) < 0.012 and abs(lon - 77.63) < 0.012):
                        lst = 25.5
                        ndvi = 0.25
                        built_up = 0.02
                        pop_density = 100.0
                        
                # Delhi NCR River Yamuna
                if city_name == "Delhi NCR":
                    if abs(lon - 77.23 - (lat - center_lat)*0.08) < 0.01:
                        lst = 28.5
                        ndvi = 0.42
                        built_up = 0.03
                        pop_density = 200.0
            
            grid.append({
                "id": cell_id,
                "lat": float(lat),
                "lon": float(lon),
                "lst": round(float(lst), 2),
                "ndvi": round(float(ndvi), 3),
                "built_up": round(float(built_up), 3),
                "pop_density": round(float(pop_density), 1)
            })
            cell_id += 1
            
    out_path = os.path.join(data_dir, filename)
    with open(out_path, "w") as f:
        json.dump(grid, f, indent=2)
    print(f"High-res grid generated for {city_name}! Cells count: {len(grid)}")

def generate_all_data():
    os.makedirs(data_dir, exist_ok=True)
    generate_india_grid()
    generate_city_grid("Bengaluru", 12.9716, 77.5946, "bengaluru_grid.json")
    generate_city_grid("Mumbai", 19.0760, 72.8777, "mumbai_grid.json")
    generate_city_grid("Delhi NCR", 28.6139, 77.2090, "delhi_grid.json")

if __name__ == "__main__":
    generate_all_data()
