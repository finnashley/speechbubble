from client import WaniKaniAPI
import os
from pprint import pprint

def main():
    # Get API key from environment variable
    api_key = os.getenv("WANIKANI_API_KEY")
    if not api_key:
        print("Please set your WANIKANI_API_KEY environment variable")
        return

    # Initialize the client
    client = WaniKaniAPI(api_key)

    try:
        # Get user information
        user_info = client.get_user_information()
        print(f"\nUser Level: {user_info.get('level', 'Unknown')}")
        
        # Get vocabulary progress
        progress = client.get_vocabulary_progress()
        print("\nVocabulary Progress:")
        for status, count in progress.items():
            print(f"{status.title()}: {count}")

        # Get vocabulary for current level
        current_level = user_info.get('level', 1)
        level_vocab = client.get_vocabulary_by_level(current_level)
        
        print(f"\nVocabulary for Level {current_level}:")
        for vocab in level_vocab:
            print(f"\n{vocab['characters']}")
            print(f"Meanings: {', '.join(vocab['meanings'])}")
            print(f"Readings: {', '.join(vocab['readings'])}")

    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    main() 