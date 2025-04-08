import json
import os
from typing import List, Dict, Optional

class BookDatabase:
    def __init__(self, db_file: str = 'data/books.json'):
        self.db_file = db_file
        self.books = self._load_books()
    
    def _load_books(self) -> List[Dict]:
        """Load books from JSON file."""
        try:
            with open(self.db_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            return []
        except json.JSONDecodeError:
            return []
    
    def search_books(self, query: str, limit: int = 3) -> List[Dict]:
        """Search books by title, author, or genre."""
        if not query or not self.books:
            return []
        
        query = query.lower()
        results = []
        
        for book in self.books:
            if (query in book['title'].lower() or 
                query in book['author'].lower() or 
                any(query in genre.lower() for genre in book['genres'])):
                results.append(book)
                if len(results) >= limit:
                    break
        
        return results
    
    def get_book_by_title(self, title: str) -> Optional[Dict]:
        """Get a book by exact title match."""
        for book in self.books:
            if book['title'].lower() == title.lower():
                return book
        return None
    
    def get_books_by_mood(self, mood: str, limit: int = 3) -> List[Dict]:
        """Get books that match a specific mood."""
        mood_mapping = {
            'adventurous': ['Adventure', 'Action', 'Thriller', 'Fantasy'],
            'romantic': ['Romance', 'Contemporary', 'Historical Fiction'],
            'mysterious': ['Mystery', 'Thriller', 'Horror', 'Crime'],
            'thoughtful': ['Literary Fiction', 'Philosophy', 'Biography', 'History']
        }
        
        genres = mood_mapping.get(mood.lower(), [])
        if not genres:
            return []
        
        results = []
        for book in self.books:
            if any(genre in genres for genre in book['genres']):
                results.append(book)
                if len(results) >= limit:
                    break
        
        return results