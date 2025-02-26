import requests
from typing import List, Dict, Optional, Union
from datetime import datetime, timezone
import time
import json
from pathlib import Path
from wanikani.models import WaniKaniItem, Reading, Meaning, UserKnowledge, SubjectType, SrsStage

class WaniKaniAPI:
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://api.wanikani.com/v2"
        self.headers = {
            "Authorization": f"Bearer {api_key}",
            "Wanikani-Revision": "20170710"
        }
        # Create cache directory if it doesn't exist
        Path("wanikani/cache").mkdir(parents=True, exist_ok=True)

    def _make_request(self, endpoint: str, params: Optional[Dict] = None) -> Dict:
        """Make a request to the WaniKani API with automatic pagination"""
        url = f"{self.base_url}/{endpoint}"
        results = []
        
        while url:
            response = requests.get(url, headers=self.headers, params=params)
            response.raise_for_status()
            data = response.json()
            
            # For non-collection endpoints, return the data directly
            if endpoint == "user":
                return data
            
            # Add the current page's data to our results
            if "data" in data:
                results.extend(data["data"])
            
            # Get the next page URL if it exists
            url = data.get("pages", {}).get("next_url")
            
            # Respect rate limiting
            time.sleep(0.5)
        
        return {"data": results}

    def save_cache(self, data: Dict, filename: str) -> None:
        """Save data to cache file with timestamp"""
        cache_data = {
            "timestamp": datetime.now().isoformat(),
            "data": data
        }
        cache_path = Path("wanikani/cache") / f"{filename}.json"
        with open(cache_path, "w", encoding="utf-8") as f:
            json.dump(cache_data, f, ensure_ascii=False, indent=2)

    def load_cache(self, filename: str, max_age_hours: int = 24) -> Optional[Dict]:
        """Load data from cache file if it's not too old"""
        cache_path = Path("wanikani/cache") / f"{filename}.json"
        try:
            with open(cache_path, "r", encoding="utf-8") as f:
                cache_data = json.load(f)
                
            # Check cache age
            cache_time = datetime.fromisoformat(cache_data["timestamp"])
            age = datetime.now() - cache_time
            if age.total_seconds() / 3600 > max_age_hours:
                return None
                
            return cache_data["data"]
        except (FileNotFoundError, KeyError, ValueError):
            return None

    def _convert_to_wanikani_item(self, raw_data: Dict, srs_stage: Optional[int] = None) -> WaniKaniItem:
        """Convert raw API data to WaniKaniItem"""
        data = raw_data["data"]
        return WaniKaniItem(
            id=raw_data["id"],
            object=raw_data["object"],
            level=data["level"],
            characters=data["characters"],
            meanings=[
                Meaning(
                    meaning=m["meaning"],
                    primary=m.get("primary", False),
                    accepted_answer=m.get("accepted_answer", True)
                )
                for m in data["meanings"]
            ],
            readings=[
                Reading(
                    reading=r["reading"],
                    primary=r.get("primary", False),
                    accepted_answer=r.get("accepted_answer", True),
                    type=r.get("type", "reading")
                )
                for r in data["readings"]
            ],
            parts_of_speech=data.get("parts_of_speech", []),
            component_subject_ids=data.get("component_subject_ids", []),
            srs_stage=srs_stage,
            user_specific_data=raw_data.get("user_specific_data", {})
        )

    def get_user_knowledge(self, use_cache: bool = True, max_age_hours: int = 24) -> UserKnowledge:
        """Get all user's knowledge including vocabulary and kanji"""
        cache_key = f"knowledge_cache_{self.api_key[-8:]}"
        
        if use_cache:
            cached_data = self.load_cache(cache_key, max_age_hours)
            if cached_data:
                return UserKnowledge.from_dict(cached_data)

        # Get user level
        user_info = self.get_user_information()
        user_level = user_info.get("level", 1)

        # Get assignments for SRS stages
        assignments = self._make_request(
            "assignments",
            params={
                "subject_types": ["vocabulary", "kanji"],
                "started": True  # Only get started assignments
            }
        )

        # Create assignment lookup
        assignment_lookup = {
            a["data"]["subject_id"]: a["data"]["srs_stage"]
            for a in assignments["data"]
            if a["data"].get("started_at") is not None  # Only include started assignments
        }

        # Get vocabulary and kanji for the user's level and below
        vocab_data = self._make_request(
            "subjects",
            params={
                "types": ["vocabulary"],
                "levels": list(range(1, user_level + 1))  # Get vocab up to current level
            }
        )
        
        kanji_data = self._make_request(
            "subjects",
            params={
                "types": ["kanji"],
                "levels": list(range(1, user_level + 1))  # Get kanji up to current level
            }
        )

        # Convert to WaniKaniItems
        vocabulary = [
            self._convert_to_wanikani_item(
                v, 
                srs_stage=assignment_lookup.get(v["id"])
            )
            for v in vocab_data["data"]
        ]
        
        kanji = [
            self._convert_to_wanikani_item(
                k,
                srs_stage=assignment_lookup.get(k["id"])
            )
            for k in kanji_data["data"]
        ]

        knowledge = UserKnowledge(
            vocabulary=vocabulary,
            kanji=kanji,
            level=user_level
        )

        # Save to cache
        if use_cache:
            self.save_cache(knowledge.to_dict(), cache_key)

        return knowledge

    def get_user_information(self) -> Dict:
        """Get user information including level and subscription status"""
        response = self._make_request("user")
        return response.get("data", {}) 