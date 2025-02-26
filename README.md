# SpeechBubble

Generate natural Japanese sentences using your WaniKani vocabulary and OpenAI's GPT models.

## Features

- Fetches your learned vocabulary from WaniKani
- Uses GPT to generate natural Japanese sentences
- Provides readings and English translations
- Word-by-word breakdowns of generated sentences
- Supports different grammar levels (beginner/intermediate)

## Installation

1. Clone this repository:
   ```bash
   git clone https://github.com/yourusername/speechbubble.git
   cd speechbubble
   ```

2. Create and activate a virtual environment:
   ```bash
   python3 -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## Configuration

You'll need two API keys:
1. A WaniKani V2 API key (get it from your [WaniKani API page](https://www.wanikani.com/settings/personal_access_tokens))
2. An OpenAI API key (get it from your [OpenAI dashboard](https://platform.openai.com/api-keys))

On first run, the program will prompt you for these keys and store them securely in `~/.config/speechbubble/config.json`.

## Usage

Basic usage:
```bash
python main.py
```

This will generate 3 sentences using beginner-level grammar.

Options:
- `-n N, --num-sentences N`: Generate N sentences (default: 3)
- `-l LEVEL, --level LEVEL`: Grammar level: 'beginner' or 'intermediate' (default: beginner)
- `--stats-only`: Only show vocabulary statistics, don't generate sentences

Examples:
```bash
# Generate 5 sentences
python main.py -n 5

# Use intermediate grammar
python main.py -l intermediate

# Just show vocabulary statistics
python main.py --stats-only
```

## How it Works

1. The program fetches your learned vocabulary from WaniKani
2. It organizes the vocabulary by part of speech (nouns, verbs, adjectives, etc.)
3. Using GPT, it generates natural Japanese sentences using your vocabulary
4. Each sentence comes with:
   - Japanese text
   - Reading in hiragana
   - English translation
   - Word-by-word breakdown

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
