#!/usr/bin/env python3
import os
import sys
import json
import argparse
from pathlib import Path
from typing import Optional, Dict

from wanikani.client import WaniKaniAPI
from wanikani.sentence_builder import SentenceBuilder
from wanikani.models import UserKnowledge, WaniKaniItem, Reading, Meaning

CONFIG_DIR = Path.home() / ".config" / "speechbubble"
CONFIG_FILE = CONFIG_DIR / "config.json"

def load_config() -> Dict[str, str]:
    """Load configuration from config file"""
    if not CONFIG_FILE.exists():
        return {}
    
    with open(CONFIG_FILE) as f:
        return json.load(f)

def save_config(config: Dict[str, str]) -> None:
    """Save configuration to config file"""
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    with open(CONFIG_FILE, "w") as f:
        json.dump(config, f, indent=2)

def get_api_keys() -> tuple[str, str]:
    """Get API keys from config file or prompt user"""
    config = load_config()
    
    wanikani_key = config.get("wanikani_api_key")
    openai_key = config.get("openai_api_key")
    
    if not wanikani_key:
        print("WaniKani API key not found.")
        wanikani_key = input("Please enter your WaniKani API key (v2): ").strip()
        config["wanikani_api_key"] = wanikani_key
        save_config(config)
    
    if not openai_key:
        print("\nOpenAI API key not found.")
        openai_key = input("Please enter your OpenAI API key: ").strip()
        config["openai_api_key"] = openai_key
        save_config(config)
    
    return wanikani_key, openai_key

def fetch_vocabulary(api: WaniKaniAPI) -> list[WaniKaniItem]:
    """Fetch vocabulary from WaniKani API"""
    print("Fetching vocabulary data...")
    
    # Get raw vocabulary data
    vocab_response = api._make_request(
        "subjects",
        params={"types": ["vocabulary"]}
    )
    
    # Get assignments to check which items are started
    assignments = api._make_request("assignments")
    
    # Get started vocabulary IDs with their SRS stages
    started_vocab = {
        a["data"]["subject_id"]: a["data"].get("srs_stage", 0)
        for a in assignments["data"]
        if (
            a["data"].get("started_at") is not None
            and a["data"]["subject_type"] == "vocabulary"
        )
    }
    
    # Convert response data to WaniKaniItems
    vocab_items = []
    for item in vocab_response["data"]:
        if item["id"] in started_vocab:
            data = item["data"]
            vocab_items.append(
                WaniKaniItem(
                    id=item["id"],
                    object=item["object"],
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
                    srs_stage=started_vocab[item["id"]],
                    user_specific_data={"started_at": "2024-01-01"}
                )
            )
    
    return vocab_items

def print_vocabulary_stats(vocab_items: list[WaniKaniItem]) -> None:
    """Print vocabulary statistics"""
    # Count by part of speech
    pos_counts = {}
    for item in vocab_items:
        for pos in item.parts_of_speech:
            pos_counts[pos] = pos_counts.get(pos, 0) + 1
    
    print("\nVocabulary Statistics:")
    print(f"Total vocabulary items: {len(vocab_items)}")
    print("\nBreakdown by part of speech:")
    for pos, count in sorted(pos_counts.items()):
        print(f"  {pos}: {count} words")

def generate_sentences(vocab_items: list[WaniKaniItem], openai_key: str, num_sentences: int = 3, grammar_level: str = 'beginner') -> None:
    """Generate sentences using the vocabulary"""
    knowledge = UserKnowledge(
        vocabulary=vocab_items,
        kanji=[],
        level=3
    )
    
    builder = SentenceBuilder(knowledge, grammar_level=grammar_level, openai_api_key=openai_key)
    print(f"\nGenerating {num_sentences} sentences...")
    sentences = builder.generate_sentence_with_gpt(num_sentences=num_sentences)
    
    for i, sentence in enumerate(sentences, 1):
        print(f"\nSentence {i}:")
        print(f"Japanese: {sentence['japanese']}")
        print(f"Reading:  {sentence['reading']}")
        print(f"English:  {sentence['english']}")
        print("Word by word:")
        for word in sentence['word_by_word']:
            print(f"  {word['word']} ({word['reading']}) - {word['meaning']} [{word['pos']}]")

def main():
    parser = argparse.ArgumentParser(description="Generate Japanese sentences using your WaniKani vocabulary")
    parser.add_argument("-n", "--num-sentences", type=int, default=3,
                      help="Number of sentences to generate (default: 3)")
    parser.add_argument("-l", "--level", choices=['beginner', 'intermediate'],
                      default='beginner', help="Grammar level (default: beginner)")
    parser.add_argument("--stats-only", action="store_true",
                      help="Only show vocabulary statistics, don't generate sentences")
    args = parser.parse_args()
    
    try:
        # Get API keys
        wanikani_key, openai_key = get_api_keys()
        
        # Initialize WaniKani client
        api = WaniKaniAPI(wanikani_key)
        
        # Fetch vocabulary
        vocab_items = fetch_vocabulary(api)
        
        # Print statistics
        print_vocabulary_stats(vocab_items)
        
        # Generate sentences if requested
        if not args.stats_only:
            generate_sentences(vocab_items, openai_key, args.num_sentences, args.level)
            
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main() 