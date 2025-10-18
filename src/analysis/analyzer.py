# FILE: src/analysis/analyzer.py

import re
import nltk
from wordcloud import WordCloud
from collections import Counter
from pathlib import Path

# --- NLTK Data Check ---
try:
    from nltk.corpus import stopwords

    STOPWORDS = set(stopwords.words('english'))
except LookupError:
    # This block executes if the stopwords data is not found.
    # We guide the user to download it manually for reliability.
    print("-" * 80)
    print("!!! NLTK DATA NOT FOUND !!!")
    print("Required 'stopwords' data package is missing.")
    print("Please run the following command in your terminal once to download it:")
    print("\n    python -m nltk.downloader stopwords\n")
    print("-" * 80)
    # Exit gracefully instead of attempting a download, which can be unreliable.
    exit(1)

# Add custom stopwords relevant to academic papers
CUSTOM_STOPWORDS = {
    'abstract', 'paper', 'introduction', 'method', 'methods', 'results', 'conclusion',
    'propose', 'proposed', 'present', 'presents', 'show', 'demonstrate', 'model', 'models',
    'state', 'art', 'state-of-the-art', 'sota', 'approach', 'novel', 'work', 'based',
    'data', 'dataset', 'datasets', 'training', 'learning', 'network', 'networks',
    'performance', 'task', 'tasks', 'key', 'using', 'use', 'et', 'al', 'figure',
    'table', 'results', 'analysis', 'system', 'systems', 'research', 'deep', 'large',
    'also', 'however', 'framework', 'well', 'effective', 'efficient'
}
ALL_STOPWORDS = STOPWORDS.union(CUSTOM_STOPWORDS)


def clean_text(text: str) -> list:
    """Cleans and tokenizes text, removing stopwords and non-alphanumeric characters."""
    text = text.lower()
    text = re.sub(r'[^\w\s]', '', text)  # Remove punctuation
    tokens = text.split()
    return [word for word in tokens if word.isalpha() and word not in ALL_STOPWORDS and len(word) > 2]


def generate_wordcloud_from_papers(papers: list, output_path: Path) -> bool:
    """
    Generates and saves a word cloud image from the titles and abstracts of papers.
    Returns True if successful, False otherwise.
    """
    if not papers:
        return False

    # Combine all titles and abstracts into a single string
    full_text = " ".join([p.get('title', '') + " " + p.get('abstract', '') for p in papers])

    if not full_text.strip():
        print("Warning: No text available to generate word cloud.")
        return False

    word_tokens = clean_text(full_text)

    if not word_tokens:
        print("Warning: No valid words left after cleaning to generate word cloud.")
        return False

    word_freq = Counter(word_tokens)

    try:
        wc = WordCloud(width=1200, height=600, background_color="white", collocations=False).generate_from_frequencies(
            word_freq)
        wc.to_file(str(output_path))
        print(f"Word cloud generated and saved to {output_path}")
        return True
    except Exception as e:
        print(f"Error generating word cloud: {e}")
        return False

# END OF FILE: src/analysis/analyzer.py