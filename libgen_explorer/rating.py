"""
Rating module for evaluating search results.

This module provides functionality to rate and rank search results based on
various criteria like keyword matches, relevance, popularity, etc.
"""

import logging
import pandas as pd
import numpy as np
from typing import Dict, List, Any, Optional, Tuple, Set
from collections import Counter
import re

logger = logging.getLogger(__name__)

class ResultRater:
    """Rate and rank search results based on various criteria."""
    
    def __init__(self, weight_config: Optional[Dict[str, float]] = None):
        """
        Initialize the result rater with optional weight configuration.
        
        Args:
            weight_config: Dictionary mapping rating factors to their weights
        """
        # Default weights for different factors
        self.weights = {
            'title_match': 0.4,
            'author_match': 0.2,
            'recency': 0.1,
            'popularity': 0.1,
            'quality': 0.2
        }
        
        # Update with provided weights if any
        if weight_config:
            self.weights.update(weight_config)
            
        logger.info("Result rater initialized with weights: %s", self.weights)
        
    def rate_results(self, df: pd.DataFrame, query: str, 
                    additional_keywords: Optional[List[str]] = None) -> pd.DataFrame:
        """
        Rate search results based on multiple factors.
        
        Args:
            df: DataFrame with search results
            query: Original search query
            additional_keywords: Optional list of additional keywords to consider
            
        Returns:
            DataFrame with added rating columns and overall score
        """
        if df.empty:
            logger.warning("Cannot rate empty results")
            return df
            
        try:
            result = df.copy()
            query_terms = self._extract_terms(query)
            
            if additional_keywords:
                query_terms.update(self._extract_terms(' '.join(additional_keywords)))
                
            # Calculate individual factor scores
            if 'title' in result.columns:
                result['title_match_score'] = result['title'].apply(
                    lambda x: self._calculate_term_match_score(x, query_terms)
                )
            else:
                result['title_match_score'] = 0.0
                
            if 'author' in result.columns:
                result['author_match_score'] = result['author'].apply(
                    lambda x: self._calculate_term_match_score(x, query_terms)
                )
            else:
                result['author_match_score'] = 0.0
                
            if 'year' in result.columns:
                result['recency_score'] = self._calculate_recency_score(result['year'])
            else:
                result['recency_score'] = 0.5  # Neutral score if no year data
                
            # Popularity score (using filesize or download count if available)
            if 'filesize' in result.columns:
                result['popularity_score'] = self._normalize_column(result['filesize'])
            elif 'download_count' in result.columns:
                result['popularity_score'] = self._normalize_column(result['download_count'])
            else:
                result['popularity_score'] = 0.5
                
            # Quality score (using extension, pages, or other indicators)
            result['quality_score'] = self._calculate_quality_score(result)
            
            # Calculate weighted overall score
            result['overall_score'] = (
                self.weights['title_match'] * result['title_match_score'] +
                self.weights['author_match'] * result['author_match_score'] +
                self.weights['recency'] * result['recency_score'] +
                self.weights['popularity'] * result['popularity_score'] +
                self.weights['quality'] * result['quality_score']
            )
            
            # Sort by overall score in descending order
            result = result.sort_values('overall_score', ascending=False)
            
            logger.info("Rated %d search results", len(result))
            return result
            
        except Exception as e:
            logger.error("Error rating results: %s", e)
            return df
            
    def _extract_terms(self, text: str) -> Set[str]:
        """
        Extract meaningful terms from text.
        
        Args:
            text: Input text string
            
        Returns:
            Set of extracted terms
        """
        if not text or not isinstance(text, str):
            return set()
            
        # Convert to lowercase and split on non-alphanumeric chars
        terms = re.findall(r'\b\w+\b', text.lower())
        
        # Filter out common stopwords
        stopwords = {
            'a', 'an', 'the', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for',
            'with', 'by', 'of', 'from', 'as', 'is', 'are', 'was', 'were', 'be',
            'this', 'that', 'these', 'those', 'it'
        }
        
        return {term for term in terms if term not in stopwords and len(term) > 1}
        
    def _calculate_term_match_score(self, text: str, terms: Set[str]) -> float:
        """
        Calculate a score based on how many query terms match.
        
        Args:
            text: Text to check for matches
            terms: Set of terms to look for
            
        Returns:
            Match score between 0.0 and 1.0
        """
        if not text or not isinstance(text, str) or not terms:
            return 0.0
            
        text_terms = self._extract_terms(text)
        
        if not text_terms:
            return 0.0
            
        # Calculate number of matching terms and their ratio
        matching_terms = text_terms.intersection(terms)
        
        if not matching_terms:
            return 0.0
            
        # Score based on both match ratio and coverage
        match_ratio = len(matching_terms) / len(text_terms)
        coverage = len(matching_terms) / len(terms)
        
        # Combine the two metrics with emphasis on coverage
        return 0.4 * match_ratio + 0.6 * coverage
        
    def _calculate_recency_score(self, years_series: pd.Series) -> pd.Series:
        """
        Calculate recency score based on publication year.
        
        Args:
            years_series: Series of publication years
            
        Returns:
            Series of recency scores between 0.0 and 1.0
        """
        # Handle empty or non-numeric series
        years = pd.to_numeric(years_series, errors='coerce')
        
        if years.isna().all():
            return pd.Series([0.5] * len(years_series), index=years_series.index)
            
        import datetime
        current_year = datetime.datetime.now().year
        
        # Calculate years since publication
        years_since = current_year - years
        
        # Convert to a 0-1 score where newer is higher
        # Use a logarithmic scale to avoid excessive penalty for older books
        max_age = 50  # Books 50+ years old get minimum score
        
        scores = 1 - np.log1p(years_since.clip(0, max_age)) / np.log1p(max_age)
        
        return scores
        
    def _calculate_quality_score(self, df: pd.DataFrame) -> pd.Series:
        """
        Calculate quality score based on available indicators.
        
        Args:
            df: DataFrame with book information
            
        Returns:
            Series of quality scores between 0.0 and 1.0
        """
        # Initialize with neutral score
        scores = pd.Series([0.5] * len(df), index=df.index)
        
        # Adjust score based on file extension if available
        if 'extension' in df.columns:
            # Preferred formats get bonuses
            ext_scores = df['extension'].map({
                'pdf': 0.2,      # PDF is good standard format
                'epub': 0.25,    # EPUB is great for e-readers
                'mobi': 0.2,     # MOBI is good for Kindle
                'djvu': 0.15,    # DJVU is good for scanned docs
                'azw3': 0.2,     # AZW3 is good Kindle format
                'fb2': 0.15,     # FB2 is decent e-book format
                'txt': 0.0,      # TXT is very basic
                'html': 0.05,    # HTML may need processing
                'cbz': 0.1,      # CBZ is good for comics
                'cbr': 0.1       # CBR is good for comics
            }).fillna(0.0)
            
            scores += ext_scores
            
        # Adjust score based on file size (penalize extremely small files)
        if 'filesize' in df.columns:
            size_mb = df['filesize'] / (1024 * 1024)
            size_scores = pd.Series([0.0] * len(df), index=df.index)
            
            # Very small files (<100KB) might be incomplete
            small_mask = size_mb < 0.1
            size_scores[small_mask] = -0.2
            
            # Small files (100KB-1MB) get small penalty
            small_mask = (size_mb >= 0.1) & (size_mb < 1)
            size_scores[small_mask] = -0.1
            
            # Medium files (1MB-10MB) are neutral
            medium_mask = (size_mb >= 1) & (size_mb < 10)
            size_scores[medium_mask] = 0.0
            
            # Large files (10MB-50MB) get bonus
            large_mask = (size_mb >= 10) & (size_mb < 50)
            size_scores[large_mask] = 0.1
            
            # Very large files (>50MB) get bigger bonus (likely high quality scans/content)
            vlarge_mask = size_mb >= 50
            size_scores[vlarge_mask] = 0.15
            
            scores += size_scores
            
        # Adjust score based on number of pages if available
        if 'pages' in df.columns:
            pages = pd.to_numeric(df['pages'], errors='coerce').fillna(0)
            
            # Books with 0 pages get penalty
            zero_mask = pages == 0
            scores[zero_mask] -= 0.2
            
            # Books with many pages might be more comprehensive
            many_pages_mask = pages > 300
            scores[many_pages_mask] += 0.1
            
        # Clip final scores to 0-1 range
        return scores.clip(0, 1)
        
    def _normalize_column(self, series: pd.Series) -> pd.Series:
        """
        Normalize a numeric column to 0-1 range.
        
        Args:
            series: Series to normalize
            
        Returns:
            Normalized series
        """
        s = pd.to_numeric(series, errors='coerce').fillna(0)
        
        if s.max() == s.min():
            return pd.Series([0.5] * len(s), index=s.index)
            
        return (s - s.min()) / (s.max() - s.min())
        
    def get_top_results(self, df: pd.DataFrame, n: int = 10) -> pd.DataFrame:
        """
        Get top N rated results.
        
        Args:
            df: DataFrame with rated results
            n: Number of top results to return
            
        Returns:
            DataFrame with top N results
        """
        if 'overall_score' not in df.columns:
            logger.warning("DataFrame does not contain rating scores, returning unsorted results")
            return df.head(n)
            
        return df.sort_values('overall_score', ascending=False).head(n)
        
    def explain_ratings(self, df: pd.DataFrame, n: int = 10) -> List[Dict[str, Any]]:
        """
        Generate explanations for why results were rated as they were.
        
        Args:
            df: DataFrame with rated results
            n: Number of top results to explain
            
        Returns:
            List of dictionaries with rating explanations
        """
        if df.empty or 'overall_score' not in df.columns:
            return []
            
        top_df = self.get_top_results(df, n)
        explanations = []
        
        for _, row in top_df.iterrows():
            explanation = {
                'title': row.get('title', 'Unknown title'),
                'author': row.get('author', 'Unknown author'),
                'overall_score': float(row.get('overall_score', 0)),
                'factors': {}
            }
            
            # Add factor-specific scores and explanations
            if 'title_match_score' in row:
                explanation['factors']['title_match'] = {
                    'score': float(row['title_match_score']),
                    'weight': self.weights['title_match'],
                    'explanation': f"Title relevance to query: {row['title_match_score']:.2f}"
                }
                
            if 'author_match_score' in row:
                explanation['factors']['author_match'] = {
                    'score': float(row['author_match_score']),
                    'weight': self.weights['author_match'],
                    'explanation': f"Author relevance to query: {row['author_match_score']:.2f}"
                }
                
            if 'recency_score' in row:
                explanation['factors']['recency'] = {
                    'score': float(row['recency_score']),
                    'weight': self.weights['recency'],
                    'explanation': f"Recency score: {row['recency_score']:.2f}"
                }
                
            if 'popularity_score' in row:
                explanation['factors']['popularity'] = {
                    'score': float(row['popularity_score']),
                    'weight': self.weights['popularity'],
                    'explanation': f"Popularity score: {row['popularity_score']:.2f}"
                }
                
            if 'quality_score' in row:
                explanation['factors']['quality'] = {
                    'score': float(row['quality_score']),
                    'weight': self.weights['quality'],
                    'explanation': f"Quality score: {row['quality_score']:.2f}"
                }
                
            explanations.append(explanation)
            
        return explanations