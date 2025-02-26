# SpeechBubble

A project for Japanese language learning integration.

## WaniKani Integration

The WaniKani integration allows you to fetch and manage your WaniKani vocabulary data.

### Setup

1. Install the required dependencies:
```bash
pip install -r requirements.txt
```

2. Get your WaniKani API key:
   - Go to your [WaniKani Settings](https://www.wanikani.com/settings/personal_access_tokens)
   - Generate a new API token
   - Copy the token

3. Set your API key as an environment variable:
```bash
export WANIKANI_API_KEY="your-api-key-here"
```

### Usage

The integration provides several features:

1. Get unlocked vocabulary:
```python
from wanikani.client import WaniKaniAPI

client = WaniKaniAPI("your-api-key-here")
vocab_list = client.get_vocabulary_summary()
```

2. Get vocabulary for a specific level:
```python
level_vocab = client.get_vocabulary_by_level(5)  # Get level 5 vocabulary
```

3. Get vocabulary progress:
```python
progress = client.get_vocabulary_progress()
```

4. Get user information:
```python
user_info = client.get_user_information()
```

### Example

Run the example script to see it in action:
```bash
python wanikani/example.py
```

### Features

- Automatic pagination handling
- Rate limiting protection
- Caching support for better performance
- Progress tracking across SRS stages
- Detailed vocabulary information including meanings and readings

### Cache Management

The integration automatically caches vocabulary data to reduce API calls. The cache is stored in `wanikani/cache/`. To bypass the cache, use:

```python
vocab_list = client.get_vocabulary_summary(use_cache=False)
```
