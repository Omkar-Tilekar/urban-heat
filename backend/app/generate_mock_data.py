import os
import json
import math
import numpy as np
from shapely.geometry import Polygon, Point

def generate_data():
    print("Generating representative Maharashtra state-wide geospatial dataset...")
    # Bounding Box for Maharashtra
    # Lat: 15.5 to 22.1
    # Lon: 72.5 to 81.0
    grid_size = 40 # 40x40 grid = 1600 potential cells
    lats = np.linspace(15.5, 22.1, grid_size)
    lons = np.linspace(72.5, 81.0, grid_size)
    
    # Bounding polygon coordinates of Maharashtra state outline (roughly approximated)
    maharashtra_poly = Polygon([
        (72.8, 18.9), # Mumbai
        (72.7, 20.1), # Palghar/NW Coast
        (73.8, 22.0), # NW Tip (Nandurbar)
        (76.5, 21.5), # North Border
        (78.5, 21.7), # Nagpur North
        (80.9, 21.4), # Gondia (NE corner)
        (80.2, 18.7), # Gadchiroli (East)
        (78.0, 18.0), # Nanded/SE Border
        (76.1, 17.2), # Solapur (South)
        (74.2, 15.6), # Kolhapur/Goa border (SW corner)
        (73.6, 15.7), # Sindhudurg Coast
        (73.1, 18.0), # Ratnagiri Coast
        (72.8, 18.9)  # Close loop
    ])
    
    # Major cities in Maharashtra to model local urban heat density
    cities = [
        {"name": "Mumbai", "lat": 19.0760, "lon": 72.8777, "lst_mod": -3.0, "built_val": 0.95, "pop_val": 42000.0, "ndvi_val": 0.1},
        {"name": "Pune", "lat": 18.5204, "lon": 73.8567, "lst_mod": -1.0, "built_val": 0.85, "pop_val": 22000.0, "ndvi_val": 0.2},
        {"name": "Nagpur", "lat": 21.1458, "lon": 79.0882, "lst_mod": 2.5, "built_val": 0.82, "pop_val": 15000.0, "ndvi_val": 0.15},
        {"name": "Nashik", "lat": 19.9975, "lon": 73.7898, "lst_mod": -0.5, "built_val": 0.75, "pop_val": 12000.0, "ndvi_val": 0.22},
        {"name": "Aurangabad", "lat": 19.8762, "lon": 75.3433, "lst_mod": 1.0, "built_val": 0.70, "pop_val": 11000.0, "ndvi_val": 0.18}
    ]
    
    grid = []
    np.random.seed(42)
    cell_id = 0
    
    for i, lat in enumerate(lats):
        for j, lon in enumerate(lons):
            point = Point(lon, lat)
            
            # Filter: Check if point is inside Maharashtra boundary
            if not maharashtra_poly.contains(point):
                continue # Skip cells outside the state
                
            # Determine Regional Climatic Zones
            # 1. Konkan Coastal Belt (high pop, high concrete, tempered summer LST)
            is_konkan = lon < 73.5
            
            # 2. Western Ghats / Sahyadri (cool high-altitude mountains, dense green forest)
            is_ghats = (73.5 <= lon < 74.3) and (lat < 20.5)
            
            # 3. Vidarbha / East (extreme dry heatwave zone in summer)
            is_vidarbha = lon >= 77.8
            
            # 4. Marathwada & Khandesh / Central Plains (dry hot plains)
            is_central = (74.3 <= lon < 77.8)
            
            # Establish Baseline Values
            if is_ghats:
                # Cool forest area
                base_lst = 28.0 + np.random.normal(0, 0.8)
                base_ndvi = 0.75 + np.random.normal(0, 0.05)
                base_built = 0.08 + np.random.normal(0, 0.02)
                base_pop = 800.0 + np.random.normal(0, 200)
            elif is_konkan:
                # Damp coast
                base_lst = 32.5 + np.random.normal(0, 0.5)
                base_ndvi = 0.30 + np.random.normal(0, 0.04)
                base_built = 0.45 + np.random.normal(0, 0.1)
                base_pop = 8000.0 + np.random.normal(0, 2000)
            elif is_vidarbha:
                # Dry heat zone (Nagpur, Chandrapur)
                base_lst = 43.5 + np.random.normal(0, 0.7)
                base_ndvi = 0.14 + np.random.normal(0, 0.03)
                base_built = 0.25 + np.random.normal(0, 0.05)
                base_pop = 1500.0 + np.random.normal(0, 400)
            else: # is_central
                # Warm plains (Aurangabad, Jalgaon)
                base_lst = 39.0 + np.random.normal(0, 0.6)
                base_ndvi = 0.22 + np.random.normal(0, 0.03)
                base_built = 0.28 + np.random.normal(0, 0.06)
                base_pop = 2200.0 + np.random.normal(0, 500)
                
            # Factor in City centers
            for city in cities:
                dist = math.sqrt((lat - city["lat"])**2 + (lon - city["lon"])**2)
                
                # If close to city center, increase built-up, population, and adjust LST
                if dist < 0.4:
                    influence = (0.4 - dist) / 0.4 # peaks at 1.0 at center
                    base_built = max(base_built, city["built_val"] * influence)
                    base_pop = max(base_pop, city["pop_val"] * influence)
                    base_ndvi = max(0.05, base_ndvi - 0.3 * influence)
                    
                    # Local city thermal anomaly
                    base_lst += city["lst_mod"] * influence + (8.0 * base_built * influence)
            
            # Final Clamping
            lst = np.clip(base_lst, 25.0, 48.0)
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
        # Keep name same so endpoints don't break, but it contains Maharashtra grid!
        json.dump(grid, f, indent=2)
    print(f"Maharashtra dataset generated! Active cells within boundary: {len(grid)}")

if __name__ == "__main__":
    generate_data()
