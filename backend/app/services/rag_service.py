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
            # Resolve path relative to this file: backend/app/services/rag_service.py -> backend/data/mitigation_kb.json
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
            # Only include if there is some positive similarity, or just get top_k
            results.append({
                "doc": self.documents[idx],
                "score": float(similarities[idx])
            })
        return results

    def query(self, user_message: str) -> str:
        """
        Executes the full RAG pipeline:
        1. Retrieve relevant context documents.
        2. Generate response using OpenAI (if API key exists) or local template synthesis.
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
        
        # Check for OpenAI API Key
        api_key = os.getenv("OPENAI_API_KEY")
        if api_key:
            try:
                from openai import OpenAI
                client = OpenAI(api_key=api_key)
                prompt = (
                    f"You are a Principal Geospatial AI Advisor for ISRO's Urban Heat Mitigation System.\n"
                    f"Answer the user query based ONLY on the following context. If you don't know, refer to general urban heat principles.\n\n"
                    f"Context:\n{context}\n\n"
                    f"User Query: {user_message}\n\n"
                    f"Answer:"
                )
                response = client.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=[{"role": "user", "content": prompt}],
                    temperature=0.2,
                    max_tokens=500
                )
                return response.choices[0].message.content
            except Exception as e:
                # Fallback to local response on OpenAI failure
                return self._compile_fallback_response(user_message, retrieved) + f"\n\n*(OpenAI Error: {str(e)} - Switched to Local Compiler)*"
        else:
            return self._compile_fallback_response(user_message, retrieved)

    def _compile_fallback_response(self, query: str, retrieved: list) -> str:
        """
        Highly polished local natural-language generation when no LLM key is available.
        Uses matched contexts to answer questions dynamically.
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
