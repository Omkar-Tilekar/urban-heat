import numpy as np
from sklearn.cluster import DBSCAN
from sklearn.linear_model import Ridge
import json

class MLService:
    def __init__(self, gis_service):
        self.gis_service = gis_service
        self.model = Ridge()
        self.train_simulator()

    def train_simulator(self):
        """
        Trains a Ridge regression model LST = f(NDVI, BuiltUp)
        to predict temperatures dynamically based on land cover.
        """
        grid = self.gis_service.get_grid()
        X = []
        y = []
        for cell in grid:
            X.append([cell["ndvi"], cell["built_up"]])
            y.append(cell["lst"])
            
        self.X_train = np.array(X)
        self.y_train = np.array(y)
        self.model.fit(self.X_train, self.y_train)
        print(f"Regression Simulator trained. Coeffs: NDVI={self.model.coef_[0]:.3f}, BuiltUp={self.model.coef_[1]:.3f}. Intercept={self.model.intercept_:.3f}")

    def detect_hotspots(self, eps_deg: float = 0.4, min_samples: int = 4, lst_percentile: float = 85.0):
        """
        Detects Urban Heat Islands (UHIs) using DBSCAN clustering.
        Identifies cells with temperatures above the given percentile,
        then clusters their lat/lon coordinates.
        """
        grid = self.gis_service.get_grid()
        lst_vals = [cell["lst"] for cell in grid]
        threshold = np.percentile(lst_vals, lst_percentile)
        
        # Filter cells above threshold
        hot_cells = [cell for cell in grid if cell["lst"] >= threshold]
        if not hot_cells:
            return []
            
        coords = np.array([[cell["lon"], cell["lat"]] for cell in hot_cells])
        
        # DBSCAN clustering
        db = DBSCAN(eps=eps_deg, min_samples=min_samples).fit(coords)
        labels = db.labels_
        
        # Build response
        hotspots = []
        for idx, label in enumerate(labels):
            if label == -1:
                continue # Ignore noise
                
            cell = hot_cells[idx]
            # Explain root cause for this hot cell
            rca = self.explain_cell(cell)
            
            hotspots.append({
                "cell_id": cell["id"],
                "lat": cell["lat"],
                "lon": cell["lon"],
                "lst": cell["lst"],
                "ndvi": cell["ndvi"],
                "built_up": cell["built_up"],
                "pop_density": cell["pop_density"],
                "risk_score": cell["risk_score"],
                "cluster_id": int(label),
                "root_causes": rca
            })
            
        return hotspots

    def explain_cell(self, cell):
        """
        Explainable AI component: Root Cause Analysis.
        Determines the main drivers of elevated temperature in a cell.
        """
        reasons = []
        # Calculate contribution metrics relative to average grid characteristics
        grid = self.gis_service.get_grid()
        avg_ndvi = np.mean([c["ndvi"] for c in grid])
        avg_built = np.mean([c["built_up"] for c in grid])
        avg_pop = np.mean([c["pop_density"] for c in grid])
        
        ndvi_diff = avg_ndvi - cell["ndvi"]
        built_diff = cell["built_up"] - avg_built
        pop_diff = cell["pop_density"] - avg_pop
        
        if ndvi_diff > 0.05:
            reasons.append({
                "cause": "Deficit in Green Cover / Vegetation Canopy",
                "importance": float(ndvi_diff * 10)
            })
        if built_diff > 0.05:
            reasons.append({
                "cause": "High Concrete / Built-up Density",
                "importance": float(built_diff * 8)
            })
        if pop_diff > 1000:
            reasons.append({
                "cause": "High Anthropogenic Heat / Population Exposure",
                "importance": float(pop_diff / 10000)
            })
            
        # Sort by impact
        reasons.sort(key=lambda x: x["importance"], reverse=True)
        return [r["cause"] for r in reasons]

    def simulate_intervention(self, cell_ids: list, intervention_type: str):
        """
        Simulates the cooling effect of interventions.
        Modifies features, uses the Ridge model to predict new LST,
        and returns the modified cells.
        
        Intervention impacts:
        - 'cool_roof': Applied to built-up areas. Lowers effective built_up contribution, reduces LST.
        - 'green_roof': Increases NDVI by 0.20, reduces effective built_up by 0.15.
        - 'urban_forest': Miyawaki forest. Increases NDVI by 0.40, reduces effective built_up by 0.30.
        - 'cool_pave': Cool pavements. Reduces effective built_up by 0.10.
        """
        grid = self.gis_service.get_grid()
        grid_dict = {cell["id"]: cell for cell in grid}
        
        # In-place simulation metrics
        ndvi_delta = 0.0
        built_delta = 0.0
        
        if intervention_type == "cool_roof":
            built_delta = -0.20
        elif intervention_type == "green_roof":
            ndvi_delta = 0.20
            built_delta = -0.15
        elif intervention_type == "urban_forest":
            ndvi_delta = 0.40
            built_delta = -0.30
        elif intervention_type == "cool_pave":
            built_delta = -0.10
        
        updated_cells = []
        for cid in cell_ids:
            if cid not in grid_dict:
                continue
            
            cell = grid_dict[cid]
            orig_lst = cell["lst"]
            orig_ndvi = cell["ndvi"]
            orig_built = cell["built_up"]
            
            # Compute new simulated features (capped at valid boundaries)
            sim_ndvi = np.clip(orig_ndvi + ndvi_delta, 0.05, 0.85)
            sim_built = np.clip(orig_built + built_delta, 0.02, 0.95)
            
            # Predict new LST using Ridge Regressor
            features = np.array([[sim_ndvi, sim_built]])
            sim_lst = float(self.model.predict(features)[0])
            # Ensure temperature decreases or is realistic
            sim_lst = min(orig_lst, round(sim_lst, 2))
            lst_diff = round(sim_lst - orig_lst, 2)
            
            # Calculate explainable cooling driver comments
            if lst_diff >= 0.0:
                driver = "No change (Cell is already at physical cooling limit)"
            elif orig_built < 0.15 and intervention_type in ["cool_roof", "cool_pave"]:
                driver = f"Low effect: Concrete density ({int(orig_built*100)}%) is too low for albedo paints"
            elif orig_ndvi > 0.65 and intervention_type in ["green_roof", "urban_forest"]:
                driver = f"Low effect: Forest canopy (NDVI: {orig_ndvi}) is already near maximum density"
            elif lst_diff <= -3.0:
                driver = f"High impact: Evapotranspiration forest block cooling ({lst_diff}°C)"
            elif lst_diff <= -1.5:
                driver = f"Mod impact: Structural albedo & canopy shading ({lst_diff}°C)"
            else:
                driver = f"Minor impact: Shading & pavement regulation ({lst_diff}°C)"
            
            updated_cells.append({
                "id": cell["id"],
                "lat": cell["lat"],
                "lon": cell["lon"],
                "orig_lst": orig_lst,
                "sim_lst": sim_lst,
                "orig_ndvi": orig_ndvi,
                "sim_ndvi": round(float(sim_ndvi), 3),
                "orig_built": orig_built,
                "sim_built": round(float(sim_built), 3),
                "lst_diff": lst_diff,
                "driver": driver
            })
            
        return updated_cells
