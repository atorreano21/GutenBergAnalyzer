"""
Project: Project Gutenberg Book Analyzer
Author: Anthony Torreano
Date: 202X-XX-XX
Description: A Tkinter GUI application that parses text files of books from
Project Gutenberg. It extracts the title, filters out common stop words,
finds the ten most frequent meaningful words, and stores the results in a
local SQLite database. It allows querying either by a Gutenberg URL
or by Title (local database search).
"""

import tkinter as tk
from tkinter import messagebox
import sqlite3
import urllib.request
import urllib.error
import re
from collections import Counter

# A comprehensive set of English stop words to filter out
STOP_WORDS = {
    "i", "me", "my", "myself", "we", "our", "ours", "ourselves", "you", "your",
    "yours", "yourself", "yourselves", "he", "him", "his", "himself", "she",
    "her", "hers", "herself", "it", "its", "itself", "they", "them", "their",
    "theirs", "themselves", "what", "which", "who", "whom", "this", "that",
    "these", "those", "am", "is", "are", "was", "were", "be", "been", "being",
    "have", "has", "had", "having", "do", "does", "did", "doing", "a", "an",
    "the", "and", "but", "if", "or", "because", "as", "until", "while", "of",
    "at", "by", "for", "with", "about", "against", "between", "into", "through",
    "during", "before", "after", "above", "below", "to", "from", "up", "down",
    "in", "out", "on", "off", "over", "under", "again", "further", "then",
    "once", "here", "there", "when", "where", "why", "how", "all", "any",
    "both", "each", "few", "more", "most", "other", "some", "such", "no", "nor",
    "not", "only", "own", "same", "so", "than", "too", "very", "s", "t", "can",
    "will", "just", "don", "should", "now", "would", "could", "said", "upon"
}


class GutenbergAnalyzerApp:
    def __init__(self, root):
        """
        Initializes the main Tkinter window and sets up the database.
        """
        self.root = root
        self.root.title("Project Gutenberg Book Analyzer")
        self.root.geometry("600x550")

        self.db_name = "gutenberg_books.db"
        self.init_db()
        self.build_gui()

    def init_db(self):
        """
        Initializes the SQLite database. Creates the book_stats table if it doesn't exist.
        """
        try:
            conn = sqlite3.connect(self.db_name)
            cursor = conn.cursor()
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS book_stats (
                    title TEXT,
                    word TEXT,
                    frequency INTEGER
                )
            ''')
            conn.commit()
            conn.close()
        except sqlite3.Error as e:
            messagebox.showerror("Database Error", f"Failed to initialize database: {e}")

    def build_gui(self):
        """
        Constructs the Tkinter graphical user interface.
        """
        # --- Local Search Section ---
        local_frame = tk.LabelFrame(self.root, text="Search Local Database", padx=10, pady=10)
        local_frame.pack(fill="x", padx=15, pady=10)

        tk.Label(local_frame, text="Book Title:").grid(row=0, column=0, sticky="w")
        self.title_entry = tk.Entry(local_frame, width=40)
        self.title_entry.grid(row=0, column=1, padx=10)

        local_search_btn = tk.Button(local_frame, text="Search DB", command=self.search_local_db)
        local_search_btn.grid(row=0, column=2)

        # --- Web Scraping Section ---
        web_frame = tk.LabelFrame(self.root, text="Fetch from Project Gutenberg", padx=10, pady=10)
        web_frame.pack(fill="x", padx=15, pady=10)

        tk.Label(web_frame, text="Book URL:").grid(row=0, column=0, sticky="w")
        self.url_entry = tk.Entry(web_frame, width=40)
        self.url_entry.grid(row=0, column=1, padx=10)

        web_search_btn = tk.Button(web_frame, text="Fetch & Save", command=self.fetch_from_web)
        web_search_btn.grid(row=0, column=2)

        # --- Display Results Section ---
        results_frame = tk.LabelFrame(self.root, text="Top 10 Word Frequencies", padx=10, pady=10)
        results_frame.pack(fill="both", expand=True, padx=15, pady=10)

        self.result_text = tk.Text(results_frame, height=15, state=tk.DISABLED, font=("Consolas", 11))
        self.result_text.pack(fill="both", expand=True)

    def display_results(self, title, words_data):
        """
        Formats and displays the search results in the Tkinter Text widget.
        """
        self.result_text.config(state=tk.NORMAL)
        self.result_text.delete(1.0, tk.END)

        if not words_data:
            self.result_text.insert(tk.END, f"Book '{title}' was not found.\n")
        else:
            self.result_text.insert(tk.END, f"Results for: {title}\n")
            self.result_text.insert(tk.END, "-" * 40 + "\n")
            self.result_text.insert(tk.END, f"{'WORD'.ljust(20)} | {'FREQUENCY'}\n")
            self.result_text.insert(tk.END, "-" * 40 + "\n")

            for word, freq in words_data:
                self.result_text.insert(tk.END, f"{word.ljust(20)} | {freq}\n")

        self.result_text.config(state=tk.DISABLED)

    def search_local_db(self):
        """
        Queries the local SQLite database for a book title and displays the frequencies.
        """
        title_query = self.title_entry.get().strip()
        if not title_query:
            messagebox.showwarning("Input Error", "Please enter a book title.")
            return

        try:
            conn = sqlite3.connect(self.db_name)
            cursor = conn.cursor()
            # Case insensitive search using LIKE
            cursor.execute("SELECT word, frequency FROM book_stats WHERE title LIKE ? ORDER BY frequency DESC",
                           (title_query,))
            results = cursor.fetchall()
            conn.close()

            if results:
                # To get the exact capitalization from the DB, we can run a separate query,
                # but we'll use the query string for display simplicity.
                self.display_results(title_query, results)
            else:
                self.display_results(title_query, [])
                messagebox.showinfo("Not Found", "Book was not found in local database. Try fetching it via URL.")

        except sqlite3.Error as e:
            messagebox.showerror("Database Error", f"An error occurred: {e}")

    def fetch_from_web(self):
        """
        Downloads a text file from the provided URL, parses the text to find the
        title and top 10 words, saves them to the DB, and displays them.
        """
        url = self.url_entry.get().strip()
        if not url:
            messagebox.showwarning("Input Error", "Please enter a valid Project Gutenberg URL.")
            return

        try:
            # Fetch content from URL
            response = urllib.request.urlopen(url)
            text_data = response.read().decode('utf-8')

            # Extract Title using regular expressions
            title_match = re.search(r'Title:\s*(.*?)\r?\n', text_data)
            book_title = title_match.group(1).strip() if title_match else "Unknown Title"

            # Clean up text: convert to lower case and find all alphabetical words
            words = re.findall(r'\b[a-z]+\b', text_data.lower())

            # Filter out stop words and single-character words
            filtered_words = [w for w in words if w not in STOP_WORDS and len(w) > 1]

            # Get top 10 most common words
            word_counts = Counter(filtered_words)
            top_10_words = word_counts.most_common(10)

            # Save to Database
            self.save_to_db(book_title, top_10_words)

            # Display
            self.display_results(book_title, top_10_words)

            # Automatically fill the title field for convenience
            self.title_entry.delete(0, tk.END)
            self.title_entry.insert(0, book_title)

            messagebox.showinfo("Success", f"Successfully fetched and saved data for '{book_title}'")

        except urllib.error.URLError as e:
            messagebox.showerror("Network Error",
                                 f"Failed to retrieve book. Check the URL or your connection.\nDetails: {e}")
        except Exception as e:
            messagebox.showerror("Error", f"An unexpected error occurred: {e}")

    def save_to_db(self, title, word_data):
        """
        Saves the title and top 10 words/frequencies into the SQLite database.
        If the book already exists, it updates/overwrites it.
        """
        try:
            conn = sqlite3.connect(self.db_name)
            cursor = conn.cursor()

            # Remove old entries for this book to avoid duplicates on re-fetch
            cursor.execute("DELETE FROM book_stats WHERE title = ?", (title,))

            # Insert new words
            for word, freq in word_data:
                cursor.execute("INSERT INTO book_stats (title, word, frequency) VALUES (?, ?, ?)",
                               (title, word, freq))

            conn.commit()
            conn.close()
        except sqlite3.Error as e:
            messagebox.showerror("Database Error", f"Failed to save to database: {e}")


if __name__ == "__main__":
    root = tk.Tk()
    app = GutenbergAnalyzerApp(root)
    root.mainloop()