"""
LibGen API connection module.

This module provides functionality to connect to and query the LibGen API.
"""

import logging
import requests
from typing import Dict, List, Any, Optional, Union
from urllib.parse import urljoin

logger = logging.getLogger(__name__)

class LibGenAPI:
    """Class for interacting with the LibGen API."""
    
    # LibGen mirrors and API endpoints
    DEFAULT_MIRRORS = [
        "http://libgen.rs",
        "http://libgen.is",
        "http://libgen.st",
        # Add more mirrors as backup
    ]
    
    SEARCH_ENDPOINT = "/search.php"
    LOOKUP_ENDPOINT = "/json.php"
    
    def __init__(self, mirror: Optional[str] = None):
        """
        Initialize the LibGen API connector.
        
        Args:
            mirror: Optional URL of the LibGen mirror to use. If None, the first
                   working mirror from DEFAULT_MIRRORS will be used.
        """
        self.mirror = mirror
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "LibGenExplorer/0.1.0",
            "Accept": "application/json, text/html",
        })
        
        if not self.mirror:
            self.mirror = self._find_working_mirror()
            
        logger.info(f"Using LibGen mirror: {self.mirror}")
    
    def _find_working_mirror(self) -> str:
        """
        Find the first working mirror from the DEFAULT_MIRRORS list.
        
        Returns:
            str: URL of the first working mirror
            
        Raises:
            ConnectionError: If no working mirrors found
        """
        for mirror in self.DEFAULT_MIRRORS:
            try:
                response = self.session.get(mirror, timeout=5)
                if response.status_code == 200:
                    return mirror
            except requests.RequestException:
                continue
        
        raise ConnectionError("Could not connect to any LibGen mirror")
    
    def search(self, query: str, fields: Optional[List[str]] = None, 
               limit: int = 25) -> List[Dict[str, Any]]:
        """
        Search for books in LibGen.
        
        Args:
            query: Search query string
            fields: List of fields to search in (title, author, etc.)
            limit: Maximum number of results to return
            
        Returns:
            List of book records as dictionaries
        """
        params = {"req": query, "limit": limit}
        
        if fields:
            params["column"] = ",".join(fields)
        
        url = urljoin(self.mirror, self.SEARCH_ENDPOINT)
        try:
            response = self.session.get(url, params=params, timeout=10)
            response.raise_for_status()
            
            # LibGen may return HTML or JSON depending on the endpoint
            content_type = response.headers.get("Content-Type", "")
            if "application/json" in content_type:
                return response.json()
            else:
                # If HTML, we need to parse the results
                return self._parse_html_results(response.text)
                
        except requests.RequestException as e:
            logger.error(f"Error searching LibGen: {e}")
            return []
    
    def get_book_details(self, book_id: Union[str, int]) -> Optional[Dict[str, Any]]:
        """
        Get detailed information about a specific book.
        
        Args:
            book_id: The LibGen ID of the book
            
        Returns:
            Dictionary with book details or None if not found
        """
        params = {"ids": str(book_id)}
        url = urljoin(self.mirror, self.LOOKUP_ENDPOINT)
        
        try:
            response = self.session.get(url, params=params, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            if data and isinstance(data, list) and len(data) > 0:
                return data[0]
            return None
            
        except requests.RequestException as e:
            logger.error(f"Error getting book details: {e}")
            return None
    
    def _parse_html_results(self, html_content: str) -> List[Dict[str, Any]]:
        """
        Parse HTML search results into structured data.
        
        Args:
            html_content: HTML content from search results
            
        Returns:
            List of book records as dictionaries
        """
        try:
            from bs4 import BeautifulSoup
            
            soup = BeautifulSoup(html_content, 'html.parser')
            results = []
            
            # Find the main table with results
            table = soup.find('table', class_='c')
            
            if not table:
                logger.warning("Could not find results table in HTML")
                return []
                
            # Skip the header row
            rows = table.find_all('tr')[1:]
            
            for row in rows:
                cells = row.find_all('td')
                
                # Skip rows with insufficient cells
                if len(cells) < 9:
                    continue
                    
                # Extract book data
                book = {
                    'id': cells[0].text.strip(),
                    'author': cells[1].text.strip(),
                    'title': cells[2].text.strip(),
                    'publisher': cells[3].text.strip(),
                    'year': cells[4].text.strip(),
                    'pages': cells[5].text.strip(),
                    'language': cells[6].text.strip(),
                    'size': cells[7].text.strip(),
                    'extension': cells[8].text.strip(),
                }
                
                # Extract filesize in bytes for sorting
                size_text = cells[7].text.strip()
                filesize = 0
                if 'KB' in size_text:
                    filesize = float(size_text.replace('KB', '').strip()) * 1024
                elif 'MB' in size_text:
                    filesize = float(size_text.replace('MB', '').strip()) * 1024 * 1024
                
                book['filesize'] = int(filesize)
                
                # Extract download link if available
                link_cell = cells[9] if len(cells) > 9 else None
                if link_cell and link_cell.find('a'):
                    book['link'] = link_cell.find('a').get('href', '')
                
                results.append(book)
            
            logger.info(f"Parsed {len(results)} results from HTML")
            return results
            
        except Exception as e:
            logger.error(f"Error parsing HTML results: {e}")
            return []