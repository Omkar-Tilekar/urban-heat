import os
import json
import numpy as np

class GISService:
    def __init__(self, data_path: str = None):
        # Resolve data directory relative to this file
        base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        self.data_dir = os.path.join(base_dir, "data")
        self.grids = {}
        self.load_all_grids()

    def load_all_grids(self):
        regions = ["india", "bengaluru", "mumbai", "delhi"]
        for r in regions:
            # Map region to filename
            filename = "delhi_grid.json" if r == "delhi" else f"{r}_grid.json"
            path = os.path.join(self.data_dir, filename)
            if os.path.exists(path):
                with open(path, "r") as f:
                    grid_data = json.load(f)
                self.grids[r] = grid_data
                self.compute_risk_index(r)
            else:
                # Fallback: if only bengaluru_grid.json is found, load it as default
                if r == "india" and os.path.exists(os.path.join(self.data_dir, "bengaluru_grid.json")):
                    with open(os.path.join(self.data_dir, "bengaluru_grid.json"), "r") as f:
                        self.grids["india"] = json.load(f)
                    self.compute_risk_index("india")
                    
        # Make sure india has at least some grid loaded
        if "india" not in self.grids and len(self.grids) > 0:
            self.grids["india"] = list(self.grids.values())[0]

    def compute_risk_index(self, region: str):
        grid_data = self.grids.get(region)
        if not grid_data:
            return

        lst_vals = [cell["lst"] for cell in grid_data]
        ndvi_vals = [cell["ndvi"] for cell in grid_data]
        built_vals = [cell["built_up"] for cell in grid_data]
        pop_vals = [cell["pop_density"] for cell in grid_data]

        min_lst, max_lst = min(lst_vals), max(lst_vals)
        min_ndvi, max_ndvi = min(ndvi_vals), max(ndvi_vals)
        min_built, max_built = min(built_vals), max(built_vals)
        min_pop, max_pop = min(pop_vals), max(pop_vals)

        # Helper to avoid division by zero
        def norm(val, min_v, max_v):
            return (val - min_v) / (max_v - min_v) if max_v > min_v else 0.0

        for cell in grid_data:
            lst_n = norm(cell["lst"], min_lst, max_lst)
            ndvi_n = norm(cell["ndvi"], min_ndvi, max_ndvi)
            built_n = norm(cell["built_up"], min_built, max_built)
            pop_n = norm(cell["pop_density"], min_pop, max_pop)

            # High NDVI reduces heat risk, so we use (1 - ndvi_n)
            heat_risk = (
                0.4 * lst_n +
                0.2 * built_n +
                0.2 * (1.0 - ndvi_n) +
                0.2 * pop_n
            )
            # Scale to 0-100
            cell["risk_score"] = round(heat_risk * 100, 1)

            # Categorize Risk Level
            if cell["risk_score"] < 20:
                cell["risk_level"] = "Very Low"
            elif cell["risk_score"] < 40:
                cell["risk_level"] = "Low"
            elif cell["risk_score"] < 60:
                cell["risk_level"] = "Moderate"
            elif cell["risk_score"] < 80:
                cell["risk_level"] = "High"
            else:
                cell["risk_level"] = "Extreme"

    def get_grid(self, region: str = "india"):
        return self.grids.get(region, self.grids.get("india", []))

    def get_summary_stats(self, region: str = "india"):
        grid_data = self.get_grid(region)
        if not grid_data:
            return {}

        lst_vals = [cell["lst"] for cell in grid_data]
        ndvi_vals = [cell["ndvi"] for cell in grid_data]
        built_vals = [cell["built_up"] for cell in grid_data]
        risk_vals = [cell["risk_score"] for cell in grid_data]

        levels = [cell["risk_level"] for cell in grid_data]
        unique_levels, counts = np.unique(levels, return_counts=True)
        level_counts = dict(zip(unique_levels, [int(c) for c in counts]))

        return {
            "avg_lst": round(float(np.mean(lst_vals)), 1),
            "max_lst": round(float(np.max(lst_vals)), 1),
            "avg_ndvi": round(float(np.mean(ndvi_vals)), 2),
            "avg_built_up": round(float(np.mean(built_vals)) * 100, 1),
            "avg_risk": round(float(np.mean(risk_vals)), 1),
            "risk_distribution": level_counts,
            "total_cells": len(grid_data)
        }
