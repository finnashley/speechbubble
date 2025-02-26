from typing import List, Optional, Dict, Union
from wanikani.client import WaniKaniAPI
from wanikani.models import UserKnowledge, WaniKaniItem, SrsStage
import random
import openai
import os
import json

# Basic grammar elements not covered by WaniKani
GRAMMAR_ELEMENTS = {
    'beginner': {
        'particles': {
            'は': {'characters': 'は', 'reading': 'wa', 'meaning': 'topic marker'},
            'が': {'characters': 'が', 'reading': 'ga', 'meaning': 'subject marker'},
            'を': {'characters': 'を', 'reading': 'o', 'meaning': 'object marker'},
            'に': {'characters': 'に', 'reading': 'ni', 'meaning': 'indirect object, destination'},
            'で': {'characters': 'で', 'reading': 'de', 'meaning': 'location of action'},
            'の': {'characters': 'の', 'reading': 'no', 'meaning': 'possession'},
            'と': {'characters': 'と', 'reading': 'to', 'meaning': 'with, and'},
            'も': {'characters': 'も', 'reading': 'mo', 'meaning': 'also, too'},
        },
        'verb_endings': {
            'ます': {'characters': 'ます', 'reading': 'masu', 'meaning': 'polite present'},
            'ました': {'characters': 'ました', 'reading': 'mashita', 'meaning': 'polite past'},
            'ません': {'characters': 'ません', 'reading': 'masen', 'meaning': 'polite negative'},
        }
    },
    'intermediate': {
        'particles': {
            'へ': {'characters': 'へ', 'reading': 'e', 'meaning': 'towards'},
            'から': {'characters': 'から', 'reading': 'kara', 'meaning': 'from'},
            'まで': {'characters': 'まで', 'reading': 'made', 'meaning': 'until'},
            'より': {'characters': 'より', 'reading': 'yori', 'meaning': 'than'},
            'だけ': {'characters': 'だけ', 'reading': 'dake', 'meaning': 'only'},
        },
        'verb_endings': {
            'て': {'characters': 'て', 'reading': 'te', 'meaning': 'te-form'},
            'た': {'characters': 'た', 'reading': 'ta', 'meaning': 'past'},
            'ない': {'characters': 'ない', 'reading': 'nai', 'meaning': 'negative'},
        }
    }
}

class SentenceBuilder:
    def __init__(self, knowledge: UserKnowledge, grammar_level: str = 'beginner', openai_api_key: Optional[str] = None):
        self.knowledge = knowledge
        self.grammar_level = grammar_level
        self.started_vocab = set()  # Will store IDs of started vocabulary
        self._initialize_started_vocab()
        self.openai_api_key = openai_api_key or os.getenv("OPENAI_API_KEY")
        if self.openai_api_key:
            openai.api_key = self.openai_api_key
        
    def _initialize_started_vocab(self):
        """Initialize the set of started vocabulary IDs"""
        for word in self.knowledge.vocabulary:
            if word.user_specific_data.get('started_at'):
                self.started_vocab.add(word.id)
    
    def get_available_words_by_pos(self) -> Dict[str, List[WaniKaniItem]]:
        """Get available words organized by part of speech, only including started items"""
        pos_dict = {
            "verb": [],
            "noun": [],
            "adjective": [],
            "adverb": [],
            "expression": []
        }
        
        for word in self.knowledge.vocabulary:
            if word.id not in self.started_vocab:
                continue
                
            for pos in word.parts_of_speech:
                normalized_pos = self._normalize_pos(pos)
                if normalized_pos in pos_dict:
                    pos_dict[normalized_pos].append(word)
        
        return pos_dict
    
    def _normalize_pos(self, pos: str) -> str:
        """Normalize part of speech categories"""
        if any(verb_type in pos for verb_type in ['ichidan verb', 'godan verb', 'verb']):
            return 'verb'
        if any(adj_type in pos for adj_type in ['い adjective', 'な adjective', 'の adjective']):
            return 'adjective'
        return pos
    
    def get_grammar_elements(self) -> dict:
        """Get grammar elements for the current level"""
        elements = {}
        for level in ['beginner', self.grammar_level]:
            if level in GRAMMAR_ELEMENTS:
                for category, items in GRAMMAR_ELEMENTS[level].items():
                    if category not in elements:
                        elements[category] = {}
                    elements[category].update(items)
        return elements
    
    def get_vocabulary_prompt(self) -> str:
        """Generate a prompt for LLM sentence generation"""
        available_words = self.get_available_words_by_pos()
        grammar = self.get_grammar_elements()
        
        prompt = "Generate a natural Japanese sentence using these components:\n\n"
        prompt += "Available vocabulary:\n"
        
        for pos, words in available_words.items():
            if words:
                prompt += f"\n{pos.title()}s:\n"
                for word in words[:5]:  # Limit to 5 examples per category
                    prompt += f"- {word.characters} ({word.primary_reading}) - {word.primary_meaning}\n"
        
        prompt += "\nAvailable grammar elements:\n"
        for category, elements in grammar.items():
            prompt += f"\n{category.title()}:\n"
            for char, info in elements.items():
                prompt += f"- {info['characters']} ({info['reading']}) - {info['meaning']}\n"
        
        prompt += "\nPlease generate a natural sentence using some of these vocabulary items and grammar elements."
        return prompt
    
    def build_basic_sentence(self) -> Optional[tuple[str, str, List[Union[WaniKaniItem, dict]]]]:
        """
        Build a basic subject-object-verb sentence
        Note: This is a fallback method. Prefer using LLM-generated sentences.
        """
        available_words = self.get_available_words_by_pos()
        grammar = self.get_grammar_elements()
        
        # Need at least one noun and one verb
        if not available_words["noun"] or not available_words["verb"]:
            return None
            
        # Build sentence components
        subject = random.choice(available_words["noun"])
        object_ = random.choice([n for n in available_words["noun"] if n != subject])
        verb = random.choice(available_words["verb"])
        
        # Add particles
        particles = grammar.get('particles', {})
        wa = particles['は']
        wo = particles['を']
        
        # Build the sentence
        sentence_items = [subject, wa, object_, wo, verb]
        japanese = "".join(
            item['characters'] if isinstance(item, dict) else item.characters
            for item in sentence_items
        )
        reading = "".join(
            item['reading'] if isinstance(item, dict) else item.primary_reading
            for item in sentence_items
        )
        
        return japanese, reading, sentence_items

    def generate_sentence_with_gpt(self, num_sentences: int = 1) -> List[Dict[str, str]]:
        """
        Generate sentences using GPT-4 based on available vocabulary and grammar.
        
        Args:
            num_sentences: Number of sentences to generate
            
        Returns:
            List of dictionaries containing:
                - japanese: Japanese sentence
                - reading: Reading in hiragana
                - english: English translation
                - word_by_word: List of dictionaries with word-level information
        """
        if not self.openai_api_key:
            raise ValueError("OpenAI API key is required for sentence generation")

        prompt = self.get_vocabulary_prompt()
        prompt += f"\n\nPlease generate {num_sentences} natural Japanese sentence(s) and provide:\n"
        prompt += "1. The Japanese sentence\n"
        prompt += "2. The reading in hiragana\n"
        prompt += "3. English translation\n"
        prompt += "4. Word-by-word breakdown showing:\n"
        prompt += "   - The word in Japanese\n"
        prompt += "   - Its reading\n"
        prompt += "   - Its meaning\n"
        prompt += "   - Its part of speech\n\n"
        prompt += "Format your response in JSON like this:\n"
        prompt += '''
{
  "sentences": [
    {
      "japanese": "日本語を勉強します",
      "reading": "にほんごをべんきょうします",
      "english": "I will study Japanese",
      "word_by_word": [
        {
          "word": "日本語",
          "reading": "にほんご",
          "meaning": "Japanese language",
          "pos": "noun"
        },
        {
          "word": "を",
          "reading": "を",
          "meaning": "object marker",
          "pos": "particle"
        },
        {
          "word": "勉強",
          "reading": "べんきょう",
          "meaning": "study",
          "pos": "noun"
        },
        {
          "word": "します",
          "reading": "します",
          "meaning": "to do",
          "pos": "verb"
        }
      ]
    }
  ]
}
'''

        try:
            client = openai.OpenAI(api_key=self.openai_api_key)
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "You are a Japanese language expert. Generate natural Japanese sentences using only the provided vocabulary and grammar elements. Ensure all responses are in the specified JSON format."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                response_format={ "type": "json_object" }
            )
            
            result = json.loads(response.choices[0].message.content)
            return result["sentences"]
            
        except Exception as e:
            print(f"Error generating sentences with GPT: {e}")
            return []

def main():
    # Get API keys from environment variables
    wanikani_api_key = os.getenv("WANIKANI_API_KEY")
    openai_api_key = os.getenv("OPENAI_API_KEY")
    
    if not wanikani_api_key:
        print("Please set your WANIKANI_API_KEY environment variable")
        return
    
    if not openai_api_key:
        print("Please set your OPENAI_API_KEY environment variable")
        print("Continuing without GPT sentence generation...")

    # Initialize the client and get user knowledge
    client = WaniKaniAPI(wanikani_api_key)
    knowledge = client.get_user_knowledge()
    
    # Create sentence builder
    builder = SentenceBuilder(knowledge, grammar_level='intermediate', openai_api_key=openai_api_key)
    
    # Get available words by part of speech
    pos_dict = builder.get_available_words_by_pos()
    
    print("\nAvailable Started Vocabulary by Part of Speech:")
    for pos, words in pos_dict.items():
        print(f"\n{pos.title()}: {len(words)} words")
        for word in words[:5]:  # Show first 5 examples
            print(f"  {word.characters} ({word.primary_reading}) - {word.primary_meaning}")
    
    if openai_api_key:
        print("\nGenerating sentences with GPT:")
        sentences = builder.generate_sentence_with_gpt(num_sentences=3)
        for i, sentence in enumerate(sentences, 1):
            print(f"\nSentence {i}:")
            print(f"Japanese: {sentence['japanese']}")
            print(f"Reading:  {sentence['reading']}")
            print(f"English:  {sentence['english']}")
            print("Word by word:")
            for word in sentence['word_by_word']:
                print(f"  {word['word']} ({word['reading']}) - {word['meaning']} [{word['pos']}]")
    else:
        # Fallback to basic sentence generation
        print("\nFalling back to basic sentence generation:")
        sentence = builder.build_basic_sentence()
        if sentence:
            japanese, reading, items = sentence
            print("\nGenerated Sentence:")
            print(f"Japanese: {japanese}")
            print(f"Reading: {reading}")
            print("Word-by-word:")
            for item in items:
                if isinstance(item, dict):
                    print(f"  {item['characters']} ({item['reading']}) - {item['meaning']}")
                else:
                    print(f"  {item.characters} ({item.primary_reading}) - {item.primary_meaning}")
        else:
            print("\nNot enough vocabulary to build a basic sentence yet.")

if __name__ == "__main__":
    main() 