import os
import json
import numpy as np

class GISService:
    def __init__(self, data_path: str = None):
        if data_path is None:
            # Resolve path relative to this file: backend/app/services/gis_service.py -> backend/data/bengaluru_grid.json
            base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            self.data_path = os.path.join(base_dir, "data", "bengaluru_grid.json")
        else:
            self.data_path = data_path
        self.grid_data = []
        self.load_grid()

    def load_grid(self):
        if not os.path.exists(self.data_path):
            raise FileNotFoundError(f"Geospatial data not found at {self.data_path}. Please run generate_mock_data.py first.")
        
        with open(self.data_path, "r") as f:
            self.grid_data = json.load(f)
        
        # Calculate risk scores upon load
        self.compute_risk_index()

    def compute_risk_index(self):
        """
        Computes the Urban Heat Risk Index (UHRI) based on:
        UHRI = 0.4 * LST_norm + 0.2 * BuiltUp_norm + 0.2 * (1 - NDVI_norm) + 0.2 * Pop_norm
        """
        if not self.grid_data:
            return

        lst_vals = [cell["lst"] for cell in self.grid_data]
        ndvi_vals = [cell["ndvi"] for cell in self.grid_data]
        built_vals = [cell["built_up"] for cell in self.grid_data]
        pop_vals = [cell["pop_density"] for cell in self.grid_data]

        min_lst, max_lst = min(lst_vals), max(lst_vals)
        min_ndvi, max_ndvi = min(ndvi_vals), max(ndvi_vals)
        min_built, max_built = min(built_vals), max(built_vals)
        min_pop, max_pop = min(pop_vals), max(pop_vals)

        # Helper to avoid division by zero
        def norm(val, min_v, max_v):
            return (val - min_v) / (max_v - min_v) if max_v > min_v else 0.0

        for cell in self.grid_data:
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

    def get_grid(self):
        return self.grid_data

    def get_summary_stats(self):
        """
        Generates aggregate city metrics for the dashboard overview cards.
        """
        lst_vals = [cell["lst"] for cell in self.grid_data]
        ndvi_vals = [cell["ndvi"] for cell in self.grid_data]
        built_vals = [cell["built_up"] for cell in self.grid_data]
        risk_vals = [cell["risk_score"] for cell in self.grid_data]

        levels = [cell["risk_level"] for cell in self.grid_data]
        unique_levels, counts = np.unique(levels, return_counts=True)
        level_counts = dict(zip(unique_levels, [int(c) for c in counts]))

        return {
            "avg_lst": round(float(np.mean(lst_vals)), 1),
            "max_lst": round(float(np.max(lst_vals)), 1),
            "avg_ndvi": round(float(np.mean(ndvi_vals)), 2),
            "avg_built_up": round(float(np.mean(built_vals)) * 100, 1),
            "avg_risk": round(float(np.mean(risk_vals)), 1),
            "risk_distribution": level_counts,
            "total_cells": len(self.grid_data)
        }
