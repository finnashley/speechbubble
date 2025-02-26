from dataclasses import dataclass, asdict
from typing import List, Optional, Dict, Any
from enum import Enum

class SubjectType(Enum):
    VOCABULARY = "vocabulary"
    KANJI = "kanji"
    RADICAL = "radical"

class SrsStage(Enum):
    APPRENTICE = "apprentice"  # 1-4
    GURU = "guru"          # 5-6
    MASTER = "master"      # 7
    ENLIGHTENED = "enlightened"  # 8
    BURNED = "burned"      # 9

@dataclass
class Reading:
    reading: str
    primary: bool
    accepted_answer: bool
    type: str  # 'kunyomi', 'onyomi', or 'nanori' for kanji; 'reading' for vocabulary

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

@dataclass
class Meaning:
    meaning: str
    primary: bool
    accepted_answer: bool

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

@dataclass
class WaniKaniItem:
    id: int
    object: str
    level: int
    characters: str
    meanings: List[Meaning]
    readings: List[Reading]
    parts_of_speech: List[str]  # Only for vocabulary
    component_subject_ids: List[int]  # Kanji used in vocabulary or radicals used in kanji
    srs_stage: Optional[int] = None
    user_specific_data: Optional[dict] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "object": self.object,
            "level": self.level,
            "characters": self.characters,
            "meanings": [m.to_dict() for m in self.meanings],
            "readings": [r.to_dict() for r in self.readings],
            "parts_of_speech": self.parts_of_speech,
            "component_subject_ids": self.component_subject_ids,
            "srs_stage": self.srs_stage,
            "user_specific_data": self.user_specific_data
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'WaniKaniItem':
        data = data.copy()
        data['meanings'] = [Meaning(**m) for m in data['meanings']]
        data['readings'] = [Reading(**r) for r in data['readings']]
        return cls(**data)

    @property
    def primary_reading(self) -> Optional[str]:
        """Get the primary reading for this item"""
        primary_readings = [r.reading for r in self.readings if r.primary]
        return primary_readings[0] if primary_readings else None

    @property
    def primary_meaning(self) -> Optional[str]:
        """Get the primary meaning for this item"""
        primary_meanings = [m.meaning for m in self.meanings if m.primary]
        return primary_meanings[0] if primary_meanings else None

    @property
    def srs_stage_name(self) -> Optional[str]:
        """Get the SRS stage name"""
        if self.srs_stage is None:
            return None
        if 1 <= self.srs_stage <= 4:
            return SrsStage.APPRENTICE.value
        elif 5 <= self.srs_stage <= 6:
            return SrsStage.GURU.value
        elif self.srs_stage == 7:
            return SrsStage.MASTER.value
        elif self.srs_stage == 8:
            return SrsStage.ENLIGHTENED.value
        elif self.srs_stage == 9:
            return SrsStage.BURNED.value
        return None

@dataclass
class UserKnowledge:
    vocabulary: List[WaniKaniItem]
    kanji: List[WaniKaniItem]
    level: int
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "vocabulary": [v.to_dict() for v in self.vocabulary],
            "kanji": [k.to_dict() for k in self.kanji],
            "level": self.level
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'UserKnowledge':
        return cls(
            vocabulary=[WaniKaniItem.from_dict(v) for v in data['vocabulary']],
            kanji=[WaniKaniItem.from_dict(k) for k in data['kanji']],
            level=data['level']
        )
    
    def get_vocab_by_level(self, level: int) -> List[WaniKaniItem]:
        """Get vocabulary items for a specific level"""
        return [v for v in self.vocabulary if v.level == level]
    
    def get_vocab_by_srs(self, stage: SrsStage) -> List[WaniKaniItem]:
        """Get vocabulary items at a specific SRS stage"""
        return [v for v in self.vocabulary if v.srs_stage_name == stage.value]
    
    def get_vocab_by_parts_of_speech(self, pos: str) -> List[WaniKaniItem]:
        """Get vocabulary items by part of speech"""
        return [v for v in self.vocabulary if pos in v.parts_of_speech]
    
    def get_kanji_in_vocab(self, vocab_item: WaniKaniItem) -> List[WaniKaniItem]:
        """Get all kanji components of a vocabulary item"""
        return [k for k in self.kanji if k.id in vocab_item.component_subject_ids] 