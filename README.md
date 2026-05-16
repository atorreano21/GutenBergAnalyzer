# Project Gutenberg Book Analyzer

A Python-based Tkinter desktop application that fetches free eBooks from Project Gutenberg, parses their text to find the top 10 most frequent meaningful words (filtering out stop words), and caches the data into a local SQLite database for offline retrieval.

## Features
- **Web Scraping:** Downloads text directly via Project Gutenberg URLs using standard Python APIs.
- **Data Optimization:** Automatically strips punctuation and standard English stop words (articles, prepositions, common verbs).
- **Local Caching:** Utilizes an SQLite3 database backend to save titles and word-frequency pairs.
- **Clean UI:** Simple, dual-pane Tkinter interface separating local database queries from live web fetching.

## How to Run
1. Ensure you have Python 3.x installed.
2. Clone this repository or download the source code.
3. Run the script:
   ```bash
   python gutenberg_analyzer.py
