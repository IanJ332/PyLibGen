"""
File export module.

This module provides functionality to export data to various file formats,
such as CSV, JSON, Excel, etc.
"""

import logging
import os
import json
import pandas as pd
from typing import Dict, List, Any, Optional, Union

logger = logging.getLogger(__name__)

class FileExporter:
    """Export data to various file formats."""
    
    SUPPORTED_FORMATS = ['csv', 'json', 'excel', 'html', 'yaml', 'txt']
    
    def __init__(self, output_dir: Optional[str] = None):
        """
        Initialize the file exporter.
        
        Args:
            output_dir: Optional directory to save output files.
                        If None, current directory is used.
        """
        self.output_dir = output_dir or os.getcwd()
        
        # Create output directory if it doesn't exist
        if not os.path.exists(self.output_dir):
            os.makedirs(self.output_dir)
            
        logger.info(f"File exporter initialized with output directory: {self.output_dir}")
        
    def export_df(self, df: pd.DataFrame, filename: str, 
                 format: str = 'csv', **kwargs) -> str:
        """
        Export a DataFrame to a file.
        
        Args:
            df: DataFrame to export
            filename: Base filename (without extension)
            format: Export format (csv, json, excel, html, yaml, txt)
            **kwargs: Additional format-specific arguments
            
        Returns:
            Path to the saved file
            
        Raises:
            ValueError: If format is not supported
        """
        if df.empty:
            logger.warning("Attempting to export empty DataFrame")
            
        format = format.lower()
        if format not in self.SUPPORTED_FORMATS:
            raise ValueError(f"Unsupported export format: {format}. "
                            f"Supported formats are: {', '.join(self.SUPPORTED_FORMATS)}")
                            
        # Generate file path
        if not filename.endswith(f'.{format}'):
            filename = f"{filename}.{format}"
            
        file_path = os.path.join(self.output_dir, filename)
        
        try:
            if format == 'csv':
                df.to_csv(file_path, index=False, **kwargs)
                
            elif format == 'json':
                # Use orient='records' by default for more readable JSON
                orient = kwargs.pop('orient', 'records')
                df.to_json(file_path, orient=orient, **kwargs)
                
            elif format == 'excel':
                df.to_excel(file_path, index=False, **kwargs)
                
            elif format == 'html':
                df.to_html(file_path, index=False, **kwargs)
                
            elif format == 'yaml':
                import yaml
                with open(file_path, 'w') as f:
                    yaml.dump(df.to_dict(orient='records'), f, **kwargs)
                    
            elif format == 'txt':
                # Simple text format with tab separation by default
                sep = kwargs.pop('sep', '\t')
                df.to_csv(file_path, index=False, sep=sep, **kwargs)
                
            logger.info(f"Exported DataFrame with {len(df)} rows to {file_path}")
            return file_path
            
        except Exception as e:
            logger.error(f"Error exporting DataFrame to {format}: {e}")
            raise
            
    def export_json(self, data: Union[Dict, List], filename: str, **kwargs) -> str:
        """
        Export dictionary or list to JSON file.
        
        Args:
            data: Dictionary or list to export
            filename: Filename (with or without .json extension)
            **kwargs: Additional arguments for json.dump
            
        Returns:
            Path to the saved file
        """
        if not filename.endswith('.json'):
            filename = f"{filename}.json"
            
        file_path = os.path.join(self.output_dir, filename)
        
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                # Use indentation by default for readability
                indent = kwargs.pop('indent', 2)
                json.dump(data, f, indent=indent, **kwargs)
                
            logger.info(f"Exported JSON data to {file_path}")
            return file_path
            
        except Exception as e:
            logger.error(f"Error exporting JSON data: {e}")
            raise
            
    def export_summary(self, search_query: str, results_df: pd.DataFrame, 
                      ratings: Optional[List[Dict[str, Any]]] = None,
                      keywords: Optional[Dict[str, Any]] = None,
                      format: str = 'txt') -> str:
        """
        Generate and export a summary report of search results.
        
        Args:
            search_query: Original search query
            results_df: DataFrame with search results
            ratings: Optional list of rating explanations
            keywords: Optional dictionary of extracted keywords
            format: Output format ('txt', 'html', or 'json')
            
        Returns:
            Path to the saved file
        """
        if results_df.empty:
            logger.warning("Attempting to export summary of empty results")
            
        format = format.lower()
        if format not in ['txt', 'html', 'json']:
            logger.warning(f"Unsupported summary format: {format}, using txt instead")
            format = 'txt'
            
        # Generate a sanitized filename from the query
        filename = f"libgen_summary_{self._sanitize_filename(search_query)}.{format}"
        file_path = os.path.join(self.output_dir, filename)
        
        try:
            if format == 'txt':
                self._export_txt_summary(file_path, search_query, results_df, ratings, keywords)
                
            elif format == 'html':
                self._export_html_summary(file_path, search_query, results_df, ratings, keywords)
                
            elif format == 'json':
                self._export_json_summary(file_path, search_query, results_df, ratings, keywords)
                
            logger.info(f"Exported search summary to {file_path}")
            return file_path
            
        except Exception as e:
            logger.error(f"Error exporting summary: {e}")
            raise
            
    def _sanitize_filename(self, filename: str) -> str:
        """
        Sanitize a string to be used as a filename.
        
        Args:
            filename: Input string
            
        Returns:
            Sanitized string
        """
        # Replace invalid filename characters
        invalid_chars = '<>:"/\\|?*'
        for char in invalid_chars:
            filename = filename.replace(char, '_')
            
        # Limit length and remove leading/trailing spaces
        return filename.strip()[:50]
        
    def _export_txt_summary(self, file_path: str, search_query: str, 
                           results_df: pd.DataFrame, ratings: Optional[List[Dict[str, Any]]],
                           keywords: Optional[Dict[str, Any]]) -> None:
        """
        Export summary as plain text.
        
        Args:
            file_path: Output file path
            search_query: Original search query
            results_df: DataFrame with search results
            ratings: Optional list of rating explanations
            keywords: Optional dictionary of extracted keywords
        """
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(f"LIBGEN SEARCH SUMMARY\n")
            f.write(f"====================\n\n")
            
            f.write(f"Search Query: {search_query}\n")
            f.write(f"Results Found: {len(results_df)}\n\n")
            
            # Summary of top results
            f.write(f"TOP RESULTS\n")
            f.write(f"----------\n\n")
            
            top_n = min(10, len(results_df))
            for i, (_, row) in enumerate(results_df.head(top_n).iterrows(), 1):
                title = row.get('title', 'Unknown title')
                author = row.get('author', 'Unknown author')
                year = row.get('year', 'Unknown year')
                f.write(f"{i}. {title} by {author} ({year})\n")
                
                if 'extension' in row and 'filesize' in row:
                    size_mb = row['filesize'] / (1024 * 1024) if row['filesize'] else 0
                    f.write(f"   Format: {row['extension']}, Size: {size_mb:.2f} MB\n")
                    
                f.write("\n")
                
            # Keywords if available
            if keywords:
                f.write(f"EXTRACTED KEYWORDS\n")
                f.write(f"-----------------\n\n")
                
                for field, terms in keywords.items():
                    f.write(f"From {field}:\n")
                    for term, count in terms:
                        f.write(f"  - {term}: {count}\n")
                    f.write("\n")
                    
            # Rating explanations if available
            if ratings:
                f.write(f"RATING EXPLANATIONS\n")
                f.write(f"-----------------\n\n")
                
                for i, rating in enumerate(ratings, 1):
                    f.write(f"{i}. {rating['title']} by {rating['author']}\n")
                    f.write(f"   Overall Score: {rating['overall_score']:.2f}\n")
                    
                    for factor, info in rating['factors'].items():
                        f.write(f"   - {info['explanation']}\n")
                        
                    f.write("\n")
            
    def _export_html_summary(self, file_path: str, search_query: str, 
                           results_df: pd.DataFrame, ratings: Optional[List[Dict[str, Any]]],
                           keywords: Optional[Dict[str, Any]]) -> None:
        """
        Export summary as HTML.
        
        Args:
            file_path: Output file path
            search_query: Original search query
            results_df: DataFrame with search results
            ratings: Optional list of rating explanations
            keywords: Optional dictionary of extracted keywords
        """
        html = [
            "<!DOCTYPE html>",
            "<html>",
            "<head>",
            "    <title>LibGen Search Summary</title>",
            "    <style>",
            "        body { font-family: Arial, sans-serif; margin: 40px; line-height: 1.6; }",
            "        h1 { color: #2c3e50; }",
            "        h2 { color: #3498db; margin-top: 30px; }",
            "        .result { margin-bottom: 20px; border-bottom: 1px solid #eee; padding-bottom: 15px; }",
            "        .meta { color: #7f8c8d; font-size: 0.9em; }",
            "        .keywords { display: flex; flex-wrap: wrap; }",
            "        .keyword { background: #f1f1f1; padding: 5px 10px; margin: 5px; border-radius: 3px; }",
            "        .factor { margin-left: 20px; color: #555; }",
            "    </style>",
            "</head>",
            "<body>",
            f"    <h1>LibGen Search Summary</h1>",
            f"    <p><strong>Search Query:</strong> {search_query}</p>",
            f"    <p><strong>Results Found:</strong> {len(results_df)}</p>",
            "    <h2>Top Results</h2>"
        ]
        
        # Top results
        top_n = min(10, len(results_df))
        for i, (_, row) in enumerate(results_df.head(top_n).iterrows(), 1):
            title = row.get('title', 'Unknown title')
            author = row.get('author', 'Unknown author')
            year = row.get('year', 'Unknown year')
            
            html.append(f'    <div class="result">')
            html.append(f'        <h3>{i}. {title}</h3>')
            html.append(f'        <div class="meta">')
            html.append(f'            <p>Author: {author} | Year: {year}</p>')
            
            if 'extension' in row and 'filesize' in row:
                size_mb = row['filesize'] / (1024 * 1024) if row['filesize'] else 0
                html.append(f'            <p>Format: {row["extension"]} | Size: {size_mb:.2f} MB</p>')
                
            html.append(f'        </div>')
            html.append(f'    </div>')
            
        # Keywords if available
        if keywords:
            html.append(f'    <h2>Extracted Keywords</h2>')
            
            for field, terms in keywords.items():
                html.append(f'    <h3>From {field}:</h3>')
                html.append(f'    <div class="keywords">')
                
                for term, count in terms:
                    html.append(f'        <div class="keyword">{term} ({count})</div>')
                    
                html.append(f'    </div>')
                
        # Rating explanations if available
        if ratings:
            html.append(f'    <h2>Rating Explanations</h2>')
            
            for i, rating in enumerate(ratings, 1):
                html.append(f'    <div class="result">')
                html.append(f'        <h3>{i}. {rating["title"]} by {rating["author"]}</h3>')
                html.append(f'        <p>Overall Score: {rating["overall_score"]:.2f}</p>')
                
                for factor, info in rating['factors'].items():
                    html.append(f'        <p class="factor">{info["explanation"]}</p>')
                    
                html.append(f'    </div>')
                
        # Close HTML tags
        html.extend([
            "</body>",
            "</html>"
        ])
        
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write('\n'.join(html))
            
    def _export_json_summary(self, file_path: str, search_query: str, 
                           results_df: pd.DataFrame, ratings: Optional[List[Dict[str, Any]]],
                           keywords: Optional[Dict[str, Any]]) -> None:
        """
        Export summary as JSON.
        
        Args:
            file_path: Output file path
            search_query: Original search query
            results_df: DataFrame with search results
            ratings: Optional list of rating explanations
            keywords: Optional dictionary of extracted keywords
        """
        # Create summary dictionary
        summary = {
            "search_query": search_query,
            "results_count": len(results_df),
            "timestamp": pd.Timestamp.now().isoformat(),
            "top_results": []
        }
        
        # Add top results
        top_n = min(10, len(results_df))
        for _, row in results_df.head(top_n).iterrows():
            result = {}
            
            # Add important fields
            for col in results_df.columns:
                if col in ['title', 'author', 'year', 'extension', 'filesize', 'pages',
                          'publisher', 'language', 'isbn', 'id', 'url']:
                    # Convert numpy/pandas types to Python native types for JSON serialization
                    if pd.notnull(row.get(col)):
                        if isinstance(row[col], (pd.Timestamp, pd._libs.tslibs.timestamps.Timestamp)):
                            result[col] = row[col].isoformat()
                        else:
                            result[col] = row[col]
                            
            summary["top_results"].append(result)
            
        # Add keywords if available
        if keywords:
            summary["keywords"] = {
                field: [{"term": term, "count": count} for term, count in terms]
                for field, terms in keywords.items()
            }
            
        # Add ratings if available
        if ratings:
            summary["ratings"] = ratings
            
        # Export to JSON file
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(summary, f, indent=2)