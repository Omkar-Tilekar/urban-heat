import os
import json
import math
import numpy as np
from shapely.geometry import Polygon, Point

def generate_data():
    print("Generating representative India state-wide geospatial dataset...")
    # Bounding Box for India
    # Lat: 8.0 to 36.5
    # Lon: 68.0 to 97.5
    grid_size = 60 # 60x60 grid = 3600 potential cells
    lats = np.linspace(8.0, 36.5, grid_size)
    lons = np.linspace(68.0, 97.5, grid_size)
    
    # Bounding polygon coordinates of India landmass outline (roughly approximated)
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
    
    # Major metropolitan hubs in India to model local urban heat density
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
            # 1. Himalayas (alpine cold zone, low population)
            is_himalayas = lat >= 30.0
            
            # 2. Thar Desert (extreme hot, dry, low vegetation)
            is_thar = (lat >= 23.0) and (lon < 75.0) and (not is_himalayas)
            
            # 3. Gangetic Plains (dense residential crop land, high population)
            is_gangetic = (23.0 <= lat < 30.0) and (75.0 <= lon < 89.0) and (not is_himalayas)
            
            # 4. Western Ghats / Sahyadri & Southwest Coast (cool elevation, high forest)
            is_ghats = (lat < 20.0) and (lon < 76.5)
            
            # 5. Northeast Hills (extreme rain forest, dense trees, cool)
            is_northeast = (lon >= 89.0) and (not is_himalayas)
            
            # 6. Deccan Plateau / South-Central (hot, dry plains)
            is_deccan = (lat < 23.0) and (75.0 <= lon < 85.0) and (not is_ghats)
            
            # Establish Baseline Values based on regional climate zones
            if is_himalayas:
                base_lst = 16.0 + (36.5 - lat) * 1.5 + np.random.normal(0, 1.2) # drops as you go north
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
            else: # is_deccan (plateau default)
                base_lst = 38.5 + np.random.normal(0, 0.7)
                base_ndvi = 0.22 + np.random.normal(0, 0.03)
                base_built = 0.26 + np.random.normal(0, 0.05)
                base_pop = 2400.0 + np.random.normal(0, 600)
                
            # Factor in City centers
            for city in cities:
                dist = math.sqrt((lat - city["lat"])**2 + (lon - city["lon"])**2)
                
                # Model local metro heat footprint (range of 1.2 degrees ≈ 130 km)
                if dist < 1.2:
                    influence = (1.2 - dist) / 1.2 # peak at center
                    base_built = max(base_built, city["built_val"] * influence)
                    base_pop = max(base_pop, city["pop_val"] * influence)
                    base_ndvi = max(0.04, base_ndvi - 0.4 * influence)
                    
                    # Local city thermal anomaly
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
            
    # Save output
    os.makedirs("backend/data", exist_ok=True)
    with open("backend/data/bengaluru_grid.json", "w") as f:
        # Save to the same path so existing loaders load India data automatically
        json.dump(grid, f, indent=2)
    print(f"India dataset generated! Active landmass cells inside boundary: {len(grid)}")

if __name__ == "__main__":
    generate_data()
