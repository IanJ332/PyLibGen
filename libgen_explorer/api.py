"""
LibGen API connection module.

This module provides functionality to connect to and query the LibGen API.
"""

import logging
import requests

from bs4 import BeautifulSoup
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
        print("searchField",query,fields)
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
            print("here2", response)

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
            print("here3",response)
            data = response.json()
            if data and isinstance(data, list) and len(data) > 0:
                return data[0]
            return None
            
        except requests.RequestException as e:
            logger.error(f"Error getting book details: {e}")
            return None

    # not sure why but it keeps telling me Size: 0.00 MB
    # Update at 4.17, Jisheng, Task: just did fetch URL.
    # see if this version works
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
            
            # Find the main table with results - updated selector for libgen.is
            table = soup.find('table', class_='c')
            
            if not table:
                # Try alternative table structure
                table = soup.find('table', attrs={'cellpadding': '2', 'cellspacing': '1'})
                
            if not table:
                logger.warning("Could not find results table in HTML")
                return []
                
            # Skip the header row
            rows = table.find_all('tr')[1:]
            for row in rows:
                cells = row.find_all('td')
                
                # Skip rows with insufficient cells
                if len(cells) < 8:
                    continue
                    
                # Extract book data - adjusted for current libgen.is structure
                book = {
                    'id': cells[0].text.strip() if len(cells) > 0 else '',
                    'author': cells[1].text.strip() if len(cells) > 1 else '',
                    'title': cells[2].text.strip() if len(cells) > 2 else '',
                    'publisher': cells[3].text.strip() if len(cells) > 3 else '',
                    'year': cells[4].text.strip() if len(cells) > 4 else '',
                    'pages': cells[5].text.strip() if len(cells) > 5 else '',
                    'language': cells[6].text.strip() if len(cells) > 6 else '',
                    'size': cells[7].text.strip() if len(cells) > 7 else '',
                    'extension': cells[8].text.strip() if len(cells) > 8 else '',
                }
                
                # Extract download links
                download_links = {}
                
                # Extract the main link if available
                if len(cells) > 9:
                    links = cells[9].find_all('a')
                    if links:
                        book['link'] = links[0].get('href', '')
                        
                        try:
                            download_links['get'] = f"https://library.lol/main/{book['link'].split('/')[-1]}"
                        except Exception as e:
                            logger.warning(f"Could not extract GET link: {e}")
                        
                        download_links['ipfs_cloudflare'] = f"https://cloudflare-ipfs.com/ipfs/{book['id']}"
                        download_links['ipfs_io'] = f"https://ipfs.io/ipfs/{book['id']}"
                        download_links['ipfs_pinata'] = f"https://gateway.pinata.cloud/ipfs/{book['id']}"
                        download_links['tor_mirror'] = f"http://libgenfrialc7tguyjywa36vtrdcplxydrxnm3f6zjbwxprqsycqad.onion/main/{book['id']}"
                
                book['download_links'] = download_links
                print("download_link2",download_links)
                # Extract filesize in bytes
                size_text = book['size']
                filesize = 0
                
                if size_text:
                    size_parts = size_text.split()
                    if len(size_parts) == 2:
                        try:
                            size_value = float(size_parts[0].replace(',', '.'))
                            size_unit = size_parts[1].upper()
                            
                            if 'KB' in size_unit:
                                filesize = size_value * 1024
                            elif 'MB' in size_unit:
                                filesize = size_value * 1024 * 1024
                            elif 'GB' in size_unit:
                                filesize = size_value * 1024 * 1024 * 1024
                            elif 'B' in size_unit:
                                filesize = size_value
                        except (ValueError, IndexError):
                            logger.warning(f"Could not parse size: {size_text}")
                
                book['filesize'] = int(filesize)
                results.append(book)
            
            logger.info(f"Parsed {len(results)} results from HTML")
            target_url = results[0]['link']
            response = requests.get(target_url, timeout=10)
            response.raise_for_status()

            soup = BeautifulSoup(response.text,'html.parser')
            downloadLink = soup.select_one('h2 + div > a')
            print(downloadLink)            
            return results
            
        except Exception as e:
            logger.error(f"Error parsing HTML results: {e}")
            return []
