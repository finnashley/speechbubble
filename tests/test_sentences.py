import os
from wanikani.client import WaniKaniAPI
from wanikani.sentence_builder import SentenceBuilder
from wanikani.models import UserKnowledge, WaniKaniItem, Reading, Meaning
try:
    from keys import WANIKANI_API_KEY, OPENAI_API_KEY
except ImportError:
    print("Warning: keys.py not found or missing API keys. Using environment variables as fallback.")
    WANIKANI_API_KEY = os.getenv("WANIKANI_API_KEY")
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
import json

def get_srs_stage(assignments, subject_id):
    for assignment in assignments:
        if assignment['data']['subject_id'] == subject_id:
            return assignment['data']['srs_stage']
    return None

def main():
    print("Fetching WaniKani data...")
    if not WANIKANI_API_KEY:
        raise ValueError("Please set WANIKANI_API_KEY in keys.py or environment variable")
    
    api = WaniKaniAPI(WANIKANI_API_KEY)
    
    # Get raw vocabulary data first
    print("\nFetching raw vocabulary data...")
    vocab_response = api._make_request(
        "subjects",
        params={
            "types": ["vocabulary"]  # Remove level filter to get all vocabulary
        }
    )
    
    # Get assignments to check which items are started
    print("\nFetching assignments...")
    assignments = api._make_request("assignments")
    
    # Debug assignment counts
    vocab_assignments = [
        a for a in assignments["data"]
        if a["data"]["subject_type"] == "vocabulary"
    ]
    started_assignments = [
        a for a in vocab_assignments
        if a["data"].get("started_at") is not None
    ]
    
    print("\nAssignment Statistics:")
    print(f"Total vocabulary assignments: {len(vocab_assignments)}")
    print(f"Started vocabulary assignments: {len(started_assignments)}")
    
    # Create SRS stage breakdown
    srs_stages = {
        'apprentice': list(range(1, 5)),
        'guru': [5, 6],
        'master': [7],
        'enlightened': [8],
        'burned': [9]
    }
    
    print("\nSRS Stage Breakdown:")
    for stage_name, stages in srs_stages.items():
        count = len([
            a for a in started_assignments
            if a["data"].get("srs_stage") in stages
        ])
        print(f"{stage_name}: {count} items")
    
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
                    user_specific_data={"started_at": "2024-01-01"}  # Dummy date since it's started
                )
            )
    
    # Create UserKnowledge object
    knowledge = UserKnowledge(
        vocabulary=vocab_items,
        kanji=[],  # We're only focusing on vocabulary for now
        level=3
    )
    
    print(f"\nTotal vocabulary items found: {len(vocab_response['data'])}")
    print(f"Total started vocabulary items: {len(vocab_items)}")
    
    # Get available words by part of speech
    print("\nStarted Vocabulary by Part of Speech:\n")
    
    pos_categories = {
        'Verb': ['verb', 'ichidan verb', 'godan verb', 'intransitive verb', 'transitive verb'],
        'Noun': ['noun'],
        'Adjective': ['adjective', 'い adjective', 'な adjective', 'の adjective'],
        'Adverb': ['adverb'],
        'Expression': ['expression']
    }
    
    # Create a dictionary mapping from item ID to data for easy lookup
    vocab_data = {
        item["id"]: item["data"]
        for item in vocab_response["data"]
        if item["id"] in started_vocab
    }
    
    for pos_name, pos_types in pos_categories.items():
        words = []
        for item_id, item in vocab_data.items():
            if any(pos in item.get('parts_of_speech', []) for pos in pos_types):
                words.append(item)
        
        print(f"{pos_name}: {len(words)} words")
        if words:
            print("Examples:\n")
            for word in words[:5]:
                srs_stage = started_vocab[item_id]
                stage_name = next(
                    (name for name, stages in srs_stages.items() 
                     if srs_stage in stages),
                    "started"
                )
                print(f"  {word['characters']} ({word['readings'][0]['reading']}) - {word['meanings'][0]['meaning']}")
                print(f"    Level: {word['level']}")
                print(f"    Parts of speech: {word.get('parts_of_speech', [])}")
                print(f"    SRS Stage: {stage_name} ({srs_stage})")
                print()
    
    # Get user info
    user_info = api.get_user_information()
    print(f"User Level: {user_info.get('level', 1)}")
    
    # Try sentence generation
    print("\nSentence Generation Examples:")
    print("\n1. Using predefined grammar (beginner level):")
    builder = SentenceBuilder(knowledge, grammar_level='beginner')
    sentence = builder.build_basic_sentence()
    if sentence:
        japanese, reading, items = sentence
        print(f"Japanese: {japanese}")
        print(f"Reading:  {reading}")
        print("Word-by-word:")
        for item in items:
            if isinstance(item, dict):
                print(f"  {item['characters']} ({item['reading']}) - {item['meaning']}")
            else:
                print(f"  {item.characters} ({item.primary_reading}) - {item.primary_meaning}")
        print()
    
    # Try GPT-powered sentence generation if OpenAI API key is available
    if OPENAI_API_KEY:
        print("\n2. GPT-Generated Sentences:")
        gpt_builder = SentenceBuilder(knowledge, grammar_level='beginner', openai_api_key=OPENAI_API_KEY)
        sentences = gpt_builder.generate_sentence_with_gpt(num_sentences=3)
        for i, sentence in enumerate(sentences, 1):
            print(f"\nSentence {i}:")
            print(f"Japanese: {sentence['japanese']}")
            print(f"Reading:  {sentence['reading']}")
            print(f"English:  {sentence['english']}")
            print("Word by word:")
            for word in sentence['word_by_word']:
                print(f"  {word['word']} ({word['reading']}) - {word['meaning']} [{word['pos']}]")
    else:
        print("\n2. LLM Prompt for Advanced Sentence Generation:")
        print(builder.get_vocabulary_prompt())

if __name__ == "__main__":
    main() 