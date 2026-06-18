import os
import json
import re
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np
from dotenv import load_dotenv

# Load environment variables from .env
base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
load_dotenv(os.path.join(base_dir, ".env"))

class RAGService:
    def __init__(self, kb_path: str = None):
        if kb_path is None:
            # Resolve path relative to this file: ai/app/services/rag_service.py -> ai/data/mitigation_kb.json
            self.kb_path = os.path.join(base_dir, "data", "mitigation_kb.json")
        else:
            self.kb_path = kb_path
        self.documents = []
        self.vectorizer = TfidfVectorizer(stop_words='english')
        self.load_kb()

    def load_kb(self):
        if not os.path.exists(self.kb_path):
            raise FileNotFoundError(f"Knowledge base not found at {self.kb_path}")
            
        with open(self.kb_path, "r") as f:
            self.documents = json.load(f)
            
        # Build text corpus for vectorization
        self.corpus = []
        for doc in self.documents:
            text = f"{doc['name']} {doc['category']} {doc['description']} {doc['suitable_conditions']} {doc['case_study']}"
            self.corpus.append(text)
            
        # Fit vectorizer
        if self.corpus:
            self.tfidf_matrix = self.vectorizer.fit_transform(self.corpus)

    def retrieve(self, query: str, top_k: int = 2):
        """
        Retrieves the top_k most relevant documents matching the query.
        """
        if not self.corpus:
            return []
            
        query_vec = self.vectorizer.transform([query])
        similarities = cosine_similarity(query_vec, self.tfidf_matrix).flatten()
        top_indices = np.argsort(similarities)[::-1][:top_k]
        
        results = []
        for idx in top_indices:
            results.append({
                "doc": self.documents[idx],
                "score": float(similarities[idx])
            })
        return results

    def query(self, user_message: str, selected_cells: list = None) -> str:
        """
        Executes the full RAG pipeline:
        1. Retrieve relevant context documents from the knowledge base.
        2. Format spatial map context (selected cells) if provided.
        3. Query Gemini LLM (primary), falling back to OpenAI or local compiler.
        """
        retrieved = self.retrieve(user_message, top_k=2)
        
        # Build context string
        context_parts = []
        for r in retrieved:
            d = r["doc"]
            context_parts.append(
                f"Strategy: {d['name']} ({d['category']})\n"
                f"Description: {d['description']}\n"
                f"Cost: {d['cost']}\n"
                f"Cooling Impact: {d['expected_cooling']}\n"
                f"Conditions: {d['suitable_conditions']}\n"
                f"Case Study: {d['case_study']}\n"
            )
        context = "\n---\n".join(context_parts)
        
        # Compile selected cells spatial context
        spatial_context = ""
        if selected_cells:
            cell_descriptions = []
            for cell in selected_cells:
                desc = (
                    f"- Grid Cell #{cell.get('id')}: Center Lat/Lon ({cell.get('lat')}, {cell.get('lon')}), "
                    f"Surface LST: {cell.get('lst')}°C, NDVI (Vegetation index): {cell.get('ndvi')}, "
                    f"Built-up (Concrete Density): {int(cell.get('built_up', 0)*100)}%, Population Density: {cell.get('pop_density')} /km²"
                )
                cell_descriptions.append(desc)
            spatial_context = "\n### Active Spatial Selection (User's Target Map Cells):\n" + "\n".join(cell_descriptions)

        # Check API Keys
        gemini_key = os.getenv("GEMINI_API_KEY")
        openai_key = os.getenv("OPENAI_API_KEY")
        
        prompt = (
            f"You are a Principal Geospatial AI Advisor for ISRO's Urban Heat Mitigation System.\n"
            f"Answer the user's planning query. Use the matching database documents as primary reference context, "
            f"and adapt your recommendations to the user's selected map block/cells metrics (if provided) like its temperature, built-up density, and green cover.\n\n"
            f"--- MITIGATION DATABASE CONTEXT ---\n{context}\n\n"
            f"--- MAP SELECTION CONTEXT ---\n{spatial_context or 'No active cells are selected on the map.'}\n\n"
            f"User Query: {user_message}\n\n"
            f"Answer (Provide structured, actionable advice, using bold headers and markdown lists):"
        )
        
        # 1. Primary: Try Gemini API
        if gemini_key:
            try:
                import google.generativeai as genai
                genai.configure(api_key=gemini_key)
                model = genai.GenerativeModel('gemini-1.5-flash')
                response = model.generate_content(prompt)
                return response.text
            except Exception as e:
                fallback_prefix = f"⚠️ *(Gemini Error: {str(e)} - Attempting OpenAI fallback)*\n\n"
                if openai_key:
                    try:
                        from openai import OpenAI
                        client = OpenAI(api_key=openai_key)
                        response = client.chat.completions.create(
                            model="gpt-4o-mini",
                            messages=[{"role": "user", "content": prompt}],
                            temperature=0.2,
                            max_tokens=500
                        )
                        return fallback_prefix + response.choices[0].message.content
                    except Exception as oe:
                        return fallback_prefix + self._compile_fallback_response(user_message, retrieved) + f"\n\n*(OpenAI Error: {str(oe)})*"
                else:
                    return fallback_prefix + self._compile_fallback_response(user_message, retrieved)
                    
        # 2. Secondary: Try OpenAI API
        elif openai_key:
            try:
                from openai import OpenAI
                client = OpenAI(api_key=openai_key)
                response = client.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=[{"role": "user", "content": prompt}],
                    temperature=0.2,
                    max_tokens=500
                )
                return response.choices[0].message.content
            except Exception as e:
                return self._compile_fallback_response(user_message, retrieved) + f"\n\n*(OpenAI Error: {str(e)} - Switched to Local Compiler)*"
        
        # 3. Fallback: Local Compiler
        else:
            return self._compile_fallback_response(user_message, retrieved)

    def _compile_fallback_response(self, query: str, retrieved: list) -> str:
        """
        Highly polished local natural-language generation when no LLM key is available.
        """
        if not retrieved or retrieved[0]["score"] < 0.05:
            return (
                "Based on the ISRO Heat Mitigation Knowledge Base, I couldn't find a direct match. "
                "Generally, Urban Heat Islands (UHIs) are mitigated through: \n"
                "1. **Albedo Modification**: Cool roofs, white coatings, and cool pavements.\n"
                "2. **Urban Canopy**: Miyawaki forests, green roofs, and tree corridors.\n"
                "3. **Blue Infrastructure**: Lake restoration, channels, and water corridors.\n\n"
                "Please search for specific terms like 'cool roofs', 'miyawaki', 'lakes', or 'green roofs' for detailed parameters."
            )
            
        primary = retrieved[0]["doc"]
        secondary = retrieved[1]["doc"] if len(retrieved) > 1 and retrieved[1]["score"] > 0.05 else None
        
        response = (
            f"### Recommended Strategy: **{primary['name']}**\n\n"
            f"**Overview**: {primary['description']}\n\n"
            f"**Key Parameters**:\n"
            f"- **Estimated Cooling Impact**: {primary['expected_cooling']}\n"
            f"- **Setup Cost**: {primary['cost']}\n"
            f"- **Implementation Timeframe**: {primary['implementation_time']}\n"
            f"- **Maintenance Rating**: {primary['maintenance_cost']}\n\n"
            f"**Target Conditions**: {primary['suitable_conditions']}\n\n"
            f"**Case Study**: {primary['case_study']}\n"
        )
        
        if secondary:
            response += (
                f"\n---\n"
                f"### Secondary Alternative: **{secondary['name']}**\n\n"
                f"**Overview**: {secondary['description']}\n"
                f"- **Cooling Impact**: {secondary['expected_cooling']}\n"
                f"- **Setup Cost**: {secondary['cost']}\n"
                f"- **Case Study**: {secondary['case_study']}\n"
            )
            
        return response
