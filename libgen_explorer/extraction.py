"""
Data extraction module using Pandas.

This module provides functionality to extract and process book data from LibGen
API results using Pandas for analysis and manipulation.
"""

import logging
import pandas as pd
import numpy as np
from typing import Dict, List, Any, Optional, Union, Tuple
from collections import Counter

logger = logging.getLogger(__name__)

class DataExtractor:
    """Extract and process data from LibGen API results using Pandas."""
    
    # Columns that are typically important for analysis
    IMPORTANT_COLUMNS = [
        'id', 'title', 'author', 'year', 'language', 'filesize', 
        'extension', 'pages', 'publisher', 'isbn', 'doi'
    ]
    
    def __init__(self):
        """Initialize the data extractor."""
        logger.info("Data extractor initialized")
        
    def convert_to_dataframe(self, books_data: List[Dict[str, Any]]) -> pd.DataFrame:
        """
        Convert a list of book dictionaries to a Pandas DataFrame.
        
        Args:
            books_data: List of book dictionaries from LibGen API
            
        Returns:
            Pandas DataFrame containing the book data
        """
        if not books_data:
            logger.warning("No book data provided to convert")
            return pd.DataFrame()
            
        try:
            df = pd.DataFrame(books_data)
            
            # Ensure important columns exist (with NaN if missing)
            for col in self.IMPORTANT_COLUMNS:
                if col not in df.columns:
                    df[col] = np.nan
                    
            # Convert numeric columns
            for col in ['year', 'filesize', 'pages']:
                if col in df.columns:
                    df[col] = pd.to_numeric(df[col], errors='coerce')
                    
            logger.info(f"Converted {len(books_data)} books to DataFrame with {len(df.columns)} columns")
            return df
            
        except Exception as e:
            logger.error(f"Error converting books to DataFrame: {e}")
            return pd.DataFrame()
        
    def filter_dataframe(self, df: pd.DataFrame, filters: Dict[str, Any]) -> pd.DataFrame:
        """
        Filter a DataFrame based on specified criteria.
        
        Args:
            df: Input DataFrame to filter
            filters: Dictionary mapping column names to filter values
            
        Returns:
            Filtered DataFrame
        """
        if df.empty:
            return df
            
        filtered_df = df.copy()
        
        try:
            for col, value in filters.items():
                if col not in filtered_df.columns:
                    logger.warning(f"Column '{col}' not found in DataFrame, skipping filter")
                    continue
                    
                if isinstance(value, list):
                    # If value is a list, check if column value is in the list
                    filtered_df = filtered_df[filtered_df[col].isin(value)]
                elif isinstance(value, tuple) and len(value) == 2:
                    # If value is a tuple of (min, max), filter for range
                    min_val, max_val = value
                    filtered_df = filtered_df[(filtered_df[col] >= min_val) & 
                                             (filtered_df[col] <= max_val)]
                elif callable(value):
                    # If value is a function, apply it as a filter
                    filtered_df = filtered_df[filtered_df[col].apply(value)]
                else:
                    # Otherwise, filter for exact match
                    filtered_df = filtered_df[filtered_df[col] == value]
                    
            logger.info(f"Filtered DataFrame from {len(df)} to {len(filtered_df)} rows")
            return filtered_df
            
        except Exception as e:
            logger.error(f"Error filtering DataFrame: {e}")
            return df
            
    def extract_keywords(self, df: pd.DataFrame, text_columns: List[str], 
                        top_n: int = 10) -> Dict[str, List[Tuple[str, int]]]:
        """
        Extract most frequent keywords from text columns.
        
        Args:
            df: Input DataFrame
            text_columns: List of column names containing text to analyze
            top_n: Number of top keywords to extract
            
        Returns:
            Dictionary mapping column names to lists of (keyword, frequency) tuples
        """
        if df.empty:
            return {}
            
        try:
            import nltk
            try:
                nltk.data.find('tokenizers/punkt')
            except LookupError:
                nltk.download('punkt', quiet=True)
                
            try:
                nltk.data.find('corpora/stopwords')
            except LookupError:
                nltk.download('stopwords', quiet=True)
                
            from nltk.tokenize import word_tokenize
            from nltk.corpus import stopwords
            
            stop_words = set(stopwords.words('english'))
            
            result = {}
            
            for col in text_columns:
                if col not in df.columns:
                    logger.warning(f"Column '{col}' not found in DataFrame, skipping keyword extraction")
                    continue
                    
                # Combine all text in the column
                all_text = ' '.join(df[col].astype(str).fillna(''))
                
                # Tokenize and filter out stopwords and non-alphabetic tokens
                tokens = [word.lower() for word in word_tokenize(all_text) 
                         if word.isalpha() and word.lower() not in stop_words and len(word) > 2]
                
                # Count frequencies
                counter = Counter(tokens)
                
                # Get top N keywords
                top_keywords = counter.most_common(top_n)
                
                result[col] = top_keywords
                
            logger.info(f"Extracted keywords from {len(text_columns)} columns")
            return result
            
        except Exception as e:
            logger.error(f"Error extracting keywords: {e}")
            return {}
            
    def aggregate_by_column(self, df: pd.DataFrame, group_by: str, 
                           agg_columns: Dict[str, List[str]]) -> pd.DataFrame:
        """
        Aggregate DataFrame by a column with specified aggregation functions.
        
        Args:
            df: Input DataFrame
            group_by: Column name to group by
            agg_columns: Dictionary mapping column names to lists of aggregation functions
            
        Returns:
            Aggregated DataFrame
        """
        if df.empty or group_by not in df.columns:
            logger.warning(f"Cannot aggregate: DataFrame is empty or '{group_by}' column not found")
            return df
            
        try:
            # Prepare aggregation dictionary
            agg_dict = {}
            
            for col, funcs in agg_columns.items():
                if col in df.columns:
                    agg_dict[col] = funcs
                    
            if not agg_dict:
                logger.warning("No valid aggregation columns specified")
                return df
                
            # Perform aggregation
            aggregated = df.groupby(group_by).agg(agg_dict)
            
            # Flatten multi-level column names if needed
            if isinstance(aggregated.columns, pd.MultiIndex):
                aggregated.columns = ['_'.join(col).strip() for col in aggregated.columns.values]
                
            logger.info(f"Aggregated DataFrame into {len(aggregated)} groups")
            return aggregated
            
        except Exception as e:
            logger.error(f"Error aggregating DataFrame: {e}")
            return df
            
    def detect_outliers(self, df: pd.DataFrame, numeric_columns: List[str], 
                       method: str = 'iqr', threshold: float = 1.5) -> pd.DataFrame:
        """
        Detect outliers in numeric columns.
        
        Args:
            df: Input DataFrame
            numeric_columns: List of numeric column names to check for outliers
            method: Method to use ('iqr' for interquartile range or 'zscore')
            threshold: Threshold for outlier detection
            
        Returns:
            DataFrame with outlier flags (True for outliers)
        """
        if df.empty:
            return pd.DataFrame()
            
        try:
            result = df.copy()
            
            for col in numeric_columns:
                if col not in df.columns or not pd.api.types.is_numeric_dtype(df[col]):
                    logger.warning(f"Column '{col}' not found or not numeric, skipping outlier detection")
                    continue
                    
                outlier_col = f"{col}_outlier"
                
                if method == 'iqr':
                    # IQR method
                    Q1 = df[col].quantile(0.25)
                    Q3 = df[col].quantile(0.75)
                    IQR = Q3 - Q1
                    
                    result[outlier_col] = ((df[col] < (Q1 - threshold * IQR)) |
                                          (df[col] > (Q3 + threshold * IQR)))
                                          
                elif method == 'zscore':
                    # Z-score method
                    from scipy import stats
                    z_scores = stats.zscore(df[col].fillna(df[col].mean()))
                    result[outlier_col] = abs(z_scores) > threshold
                    
                else:
                    logger.warning(f"Unknown outlier detection method: {method}")
                    
            logger.info(f"Detected outliers in {len(numeric_columns)} columns")
            return result
            
        except Exception as e:
            logger.error(f"Error detecting outliers: {e}")
            return df
            
    def extract_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Extract additional features from existing data.
        
        Args:
            df: Input DataFrame
            
        Returns:
            DataFrame with additional features
        """
        if df.empty:
            return df
            
        try:
            result = df.copy()
            
            # Extract year from date if available
            if 'date' in result.columns and 'year' not in result.columns:
                result['year'] = pd.to_datetime(result['date'], errors='coerce').dt.year
                
            # Calculate book age
            if 'year' in result.columns:
                import datetime
                current_year = datetime.datetime.now().year
                result['book_age'] = current_year - result['year']
                
            # Calculate file size in MB if available in bytes
            if 'filesize' in result.columns:
                result['filesize_mb'] = result['filesize'] / (1024 * 1024)
                
            # Extract language code if available
            if 'language' in result.columns:
                result['language_code'] = result['language'].str[:2].str.lower()
                
            # Flag recent books (published in last 5 years)
            if 'year' in result.columns:
                import datetime
                current_year = datetime.datetime.now().year
                result['is_recent'] = result['year'] >= (current_year - 5)
                
            logger.info("Extracted additional features from data")
            return result
            
        except Exception as e:
            logger.error(f"Error extracting features: {e}")
            return df
            
    def summarize_dataframe(self, df: pd.DataFrame) -> Dict[str, Any]:
        """
        Generate a summary of the DataFrame.
        
        Args:
            df: Input DataFrame
            
        Returns:
            Dictionary with summary statistics
        """
        if df.empty:
            return {"empty": True}
            
        try:
            summary = {
                "row_count": len(df),
                "column_count": len(df.columns),
                "columns": list(df.columns),
                "missing_values": df.isnull().sum().to_dict(),
                "numeric_stats": {},
                "categorical_stats": {}
            }
            
            # Generate statistics for numeric columns
            numeric_cols = df.select_dtypes(include=np.number).columns
            for col in numeric_cols:
                summary["numeric_stats"][col] = {
                    "min": float(df[col].min()),
                    "max": float(df[col].max()),
                    "mean": float(df[col].mean()),
                    "median": float(df[col].median()),
                    "std": float(df[col].std())
                }
                
            # Generate statistics for categorical columns
            cat_cols = df.select_dtypes(exclude=np.number).columns
            for col in cat_cols:
                val_counts = df[col].value_counts()
                summary["categorical_stats"][col] = {
                    "unique_values": int(df[col].nunique()),
                    "top_values": dict(val_counts.head(5).items())
                }
                
            logger.info("Generated DataFrame summary")
            return summary
            
        except Exception as e:
            logger.error(f"Error summarizing DataFrame: {e}")
            return {"error": str(e)}