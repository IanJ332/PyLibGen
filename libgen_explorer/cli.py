"""
Command-line interface for LibGen Explorer.

This module provides a command-line interface to search and export data from LibGen.
"""
import pandas as pd
import numpy as np
import argparse
import logging
import sys
import os
from typing import Dict, List, Any, Optional

from libgen_explorer.api import LibGenAPI
from libgen_explorer.database import GUNDatabase
from libgen_explorer.extraction import DataExtractor
from libgen_explorer.rating import ResultRater
from libgen_explorer.export import FileExporter

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)

def setup_argparse() -> argparse.ArgumentParser:
    """Set up command-line argument parser."""
    parser = argparse.ArgumentParser(description='LibGen Explorer - Search and analyze LibGen resources')
    
    # Search command
    subparsers = parser.add_subparsers(dest='command', help='Command to execute')
    
    search_parser = subparsers.add_parser('search', help='Search for books')
    search_parser.add_argument('query', help='Search query')
    search_parser.add_argument('--limit', type=int, default=25, help='Maximum number of results (default: 25)')
    search_parser.add_argument('--fields', nargs='+', help='Fields to search in (e.g., title author)')
    search_parser.add_argument('--export', choices=['csv', 'json', 'excel', 'html'], 
                              help='Export format for results')
    search_parser.add_argument('--output', help='Output file or directory')
    search_parser.add_argument('--summary', action='store_true', help='Generate a summary report')
    search_parser.add_argument('--rating-weights', type=str, help='Custom rating weights as JSON string')
    
    # Filter command
    filter_parser = subparsers.add_parser('filter', help='Filter existing search results')
    filter_parser.add_argument('--input', required=True, help='Input file with search results')
    filter_parser.add_argument('--format', default='csv', choices=['csv', 'json', 'excel'],
                              help='Format of input file (default: csv)')
    filter_parser.add_argument('--filters', type=str, required=True, 
                              help='Filter criteria as JSON string')
    filter_parser.add_argument('--export', choices=['csv', 'json', 'excel', 'html'], 
                              help='Export format for results')
    filter_parser.add_argument('--output', help='Output file or directory')
    
    # Analyze command
    analyze_parser = subparsers.add_parser('analyze', help='Analyze existing search results')
    analyze_parser.add_argument('--input', required=True, help='Input file with search results')
    analyze_parser.add_argument('--format', default='csv', choices=['csv', 'json', 'excel'],
                                help='Format of input file (default: csv)')
    analyze_parser.add_argument('--keyword-fields', nargs='+', default=['title', 'description'],
                                help='Fields to extract keywords from')
    analyze_parser.add_argument('--top-n', type=int, default=10, help='Number of top keywords to extract')
    analyze_parser.add_argument('--export', choices=['csv', 'json', 'excel', 'html'], 
                                help='Export format for analysis')
    analyze_parser.add_argument('--output', help='Output file or directory')
    
    return parser

def search_command(args: argparse.Namespace) -> None:
    """
    Handle the search command.
    
    Args:
        args: Command-line arguments
    """
    try:
        # Initialize components
        libgen_api = LibGenAPI()
        database = GUNDatabase()
        extractor = DataExtractor()
        
        # Parse rating weights if provided
        rating_weights = None
        if args.rating_weights:
            import json
            try:
                rating_weights = json.loads(args.rating_weights)
            except json.JSONDecodeError:
                logger.error("Invalid JSON for rating weights")
                sys.exit(1)
                
        rater = ResultRater(weight_config=rating_weights)
        
        # Create exporter with output directory if provided
        output_dir = None
        if args.output and os.path.isdir(args.output):
            output_dir = args.output
            
        exporter = FileExporter(output_dir=output_dir)
        
        # Perform search
        logger.info(f"Searching for: {args.query}")
        search_results = libgen_api.search(args.query, fields=args.fields, limit=args.limit)
        
        if not search_results:
            logger.info("No results found")
            return
            
        logger.info(f"Found {len(search_results)} results")
        
        # Store results in database
        database.store_search_results(args.query, search_results)
        
        # Convert to DataFrame
        df = extractor.convert_to_dataframe(search_results)
        
        # Extract additional features
        df = extractor.extract_features(df)
        
        # Rate results
        df = rater.rate_results(df, args.query)
        
        # Get top results (fixed the hardcoded 5)
        display_limit = min(args.limit, len(df))
        top_results = rater.get_top_results(df, n=display_limit)
        
        # Log search results to a timestamped file
        log_file = log_search_results(args.query, args.limit, df, top_results)
        logger.info(f"Search log created at: {log_file}")
        
        # Export results if requested
        if args.export:
            output_file = args.output if args.output and not os.path.isdir(args.output) else None
            
            if not output_file:
                # Generate filename from query
                sanitized_query = args.query.replace(' ', '_')[:30]
                output_file = f"libgen_search_{sanitized_query}"
                
            exporter.export_df(df, output_file, format=args.export)
            
        # Generate summary if requested
        if args.summary:
            # Extract keywords for summary
            keywords = extractor.extract_keywords(
                df, ['title', 'author', 'description'] if 'description' in df.columns else ['title', 'author']
            )
            
            # Get rating explanations
            ratings = rater.explain_ratings(df)
            
            # Export summary
            summary_format = args.export if args.export in ['json', 'html'] else 'txt'
            exporter.export_summary(args.query, df, ratings, keywords, format=summary_format)
            
        # Display top results
        # Display top results
        print(f"\nTop {display_limit} Results:")
        print("-------------")

        for i, (_, row) in enumerate(top_results.iterrows(), 1):
            print(f"{i}. ID\t{row.get('id', 'N/A')}")
            print(f"    Author(s)\t{row.get('author', 'N/A')}")
            print(f"    Title\t{row.get('title', 'N/A')}")
            print(f"    Publisher\t{row.get('publisher', 'N/A')}")
            print(f"    Year\t{row.get('year', 'N/A')}")
            print(f"    Language(s)\t{row.get('language', 'N/A')}")
            
            # Format file size - only use one block
            if 'filesize' in row:
                size_mb = row['filesize'] / (1024 * 1024) if row['filesize'] else 0
                print(f"    Size\t{size_mb:.2f} MB")
            else:
                print(f"    Size\tN/A")
                
            print(f"    Extension\t{row.get('extension', 'N/A')}")
            
            # Add an empty line between entries
            if i < len(top_results):
                print()
            
    except Exception as e:
        logger.error(f"Error during search command: {e}")
        
def filter_command(args: argparse.Namespace) -> None:
    """
    Handle the filter command.
    
    Args:
        args: Command-line arguments
    """
    try:
        # Initialize components
        extractor = DataExtractor()
        
        # Create exporter with output directory if provided
        output_dir = None
        if args.output and os.path.isdir(args.output):
            output_dir = args.output
            
        exporter = FileExporter(output_dir=output_dir)
        
        # Read input file
        logger.info(f"Reading input file: {args.input}")
        
        if args.format == 'csv':
            df = pd.read_csv(args.input)
        elif args.format == 'json':
            df = pd.read_json(args.input)
        elif args.format == 'excel':
            df = pd.read_excel(args.input)
        else:
            logger.error(f"Unsupported input format: {args.format}")
            sys.exit(1)
            
        if df.empty:
            logger.info("Input file contains no data")
            return
            
        # Parse filter criteria
        import json
        try:
            filters = json.loads(args.filters)
        except json.JSONDecodeError:
            logger.error("Invalid JSON for filter criteria")
            sys.exit(1)
            
        # Apply filters
        filtered_df = extractor.filter_dataframe(df, filters)
        
        logger.info(f"Filtered from {len(df)} to {len(filtered_df)} rows")
        
        # Export results if requested
        if args.export:
            output_file = args.output if args.output and not os.path.isdir(args.output) else None
            
            if not output_file:
                # Generate filename
                base_name = os.path.splitext(os.path.basename(args.input))[0]
                output_file = f"{base_name}_filtered"
                
            exporter.export_df(filtered_df, output_file, format=args.export)
            
        # Display filtered results
        print(f"\nFiltered Results ({len(filtered_df)} rows):")
        print("-------------------")
        
        for i, (_, row) in enumerate(filtered_df.head(5).iterrows(), 1):
            title = row.get('title', 'Unknown title')
            author = row.get('author', 'Unknown author')
            
            print(f"{i}. {title} by {author}")
            
        if len(filtered_df) > 5:
            print(f"... and {len(filtered_df) - 5} more results")
            
    except Exception as e:
        logger.error(f"Error during filter command: {e}")

def log_search_results(query: str, limit: int, results_df: pd.DataFrame, top_results: pd.DataFrame) -> str:
    """
    Log search results to a text file with timestamp as filename.
    
    Args:
        query: The search query
        limit: The limit parameter used
        results_df: Full results DataFrame
        top_results: DataFrame with top N results
        
    Returns:
        Path to the created log file
    """
    import datetime
    
    # Create timestamp for filename
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    log_filename = f"search_log_{timestamp}.txt"
    
    # Create output directory if it doesn't exist
    output_dir = os.path.join(os.getcwd(), "search_logs")
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
        
    log_path = os.path.join(output_dir, log_filename)
    
    # Format the log content
    with open(log_path, "w", encoding="utf-8") as f:
        # Header information
        current_time = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        f.write(f"Time: {current_time}\n")
        f.write(f"Query Condition: {query}\n")
        f.write(f"Limit the number of results: {limit}\n")
        f.write(f"Total results found: {len(results_df)}\n\n")
        
        # Results header
        f.write("Query Results.\n")
        f.write("-------------\n")
        
        # Write top results in the structured format
        for i, (_, row) in enumerate(top_results.iterrows(), 1):
            f.write(f"{i}. ID\t{row.get('id', 'N/A')}\n")
            f.write(f"    Author(s)\t{row.get('author', 'N/A')}\n")
            
            # Title might be split over multiple lines if it's long
            title = row.get('title', 'N/A')
            f.write(f"    Title\t{title}\n")
            
            f.write(f"    Publisher\t{row.get('publisher', 'N/A')}\n")
            f.write(f"    Year\t{row.get('year', 'N/A')}\n")
            f.write(f"    Language(s)\t{row.get('language', 'N/A')}\n")
            
            # Format file size
            if 'filesize' in row:
                size_mb = row['filesize'] / (1024 * 1024) if row['filesize'] else 0
                f.write(f"    Size\t{size_mb:.2f} MB\n")
            else:
                f.write(f"    Size\tN/A\n")
                
            f.write(f"    Extension\t{row.get('extension', 'N/A')}\n")
            
            # Add an empty line between entries
            if i < len(top_results):
                f.write("\n")
    
    logger.info(f"Search log saved to {log_path}")
    return log_path
        
def analyze_command(args: argparse.Namespace) -> None:
    """
    Handle the analyze command.
    
    Args:
        args: Command-line arguments
    """
    try:
        # Initialize components
        extractor = DataExtractor()
        
        # Create exporter with output directory if provided
        output_dir = None
        if args.output and os.path.isdir(args.output):
            output_dir = args.output
            
        exporter = FileExporter(output_dir=output_dir)
        
        # Read input file
        logger.info(f"Reading input file: {args.input}")
        
        if args.format == 'csv':
            df = pd.read_csv(args.input)
        elif args.format == 'json':
            df = pd.read_json(args.input)
        elif args.format == 'excel':
            df = pd.read_excel(args.input)
        else:
            logger.error(f"Unsupported input format: {args.format}")
            sys.exit(1)
            
        if df.empty:
            logger.info("Input file contains no data")
            return
            
        # Extract keywords
        keyword_fields = [field for field in args.keyword_fields if field in df.columns]
        
        if not keyword_fields:
            logger.warning("None of the specified keyword fields found in data")
            keyword_fields = [col for col in df.columns if df[col].dtype == 'object'][:2]
            logger.info(f"Using fields: {keyword_fields}")
            
        keywords = extractor.extract_keywords(df, keyword_fields, top_n=args.top_n)
        
        # Generate summary
        summary = extractor.summarize_dataframe(df)
        
        # Combine into analysis results
        analysis = {
            "summary": summary,
            "keywords": keywords
        }
        
        # Export analysis if requested
        if args.export:
            output_file = args.output if args.output and not os.path.isdir(args.output) else None
            
            if not output_file:
                # Generate filename
                base_name = os.path.splitext(os.path.basename(args.input))[0]
                output_file = f"{base_name}_analysis"
                
            exporter.export_json(analysis, output_file)
            
        # Display analysis results
        print("\nData Analysis:")
        print("-------------")
        print(f"Total records: {summary['row_count']}")
        print(f"Columns: {len(summary['columns'])}")
        
        # Display some numeric stats if available
        if summary['numeric_stats']:
            print("\nNumeric Statistics:")
            for col, stats in list(summary['numeric_stats'].items())[:3]:
                print(f"  {col}: min={stats['min']:.2f}, max={stats['max']:.2f}, mean={stats['mean']:.2f}")
            
        # Display keywords
        print("\nTop Keywords:")
        for field, terms in keywords.items():
            print(f"  From {field}:")
            for term, count in terms[:5]:
                print(f"    - {term}: {count}")
                
    except Exception as e:
        logger.error(f"Error during analyze command: {e}")
        
def main() -> None:
    """Main entry point for the CLI."""
    parser = setup_argparse()
    args = parser.parse_args()
    
    if args.command == 'search':
        search_command(args)
    elif args.command == 'filter':
        filter_command(args)
    elif args.command == 'analyze':
        analyze_command(args)
    else:
        parser.print_help()
        
if __name__ == '__main__':
    main()