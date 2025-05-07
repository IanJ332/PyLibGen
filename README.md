
# PyLibGen – LibGen Explorer

A Python-based tool that connects to the Library Genesis API using GUN (Graphical Database Engine) to help users find open-source CS books and textbooks.

## Motivation

Many CS books are now available as open-source resources, and some textbooks are uploaded to platforms like GitHub or Library Genesis. This project simplifies the process of finding and collecting data from LibGen by offering a user-friendly interface and powerful search capabilities.

## Features

- Connect to the LibGen API to search for books
- Extract and analyze data using Pandas
- Rank search results based on keyword overlap and relevance
- Generate summaries in document or text format
- Web interface for easy interaction

## Installation

### Prerequisites

- Python 3.8 or higher
- Node.js 14 or higher (for web interface)
- pip (Python package manager)
- npm (Node.js package manager)
- poetry

### Setting up the Environment
1. Clone the repository:
```
   git clone https://github.com/yourusername/libgen-explorer.git
   cd libgen_explorer
````

2. Install Poetry:

   Visit [https://python-poetry.org/docs/](https://python-poetry.org/docs/) and follow the installation guide.

3. Initialize the Python environment:

   ```bash
   poetry init
   ```

4. Return to the root folder:

   ```bash
   cd ..
   ```

5. Install dependencies (PowerShell):

   ```powershell
   Get-Content requirements.txt | Where-Object { $_ -notmatch '^\s*#' -and $_ -ne '' } | ForEach-Object { poetry add $_ }
   ```

6. Go into the server directory:

   ```bash
   cd web
   poetry run npm install
   ```

## Usage

### Starting the Application

1. Start the local server:

   ```bash
   poetry run node server.js
   ```

2. Open your web browser and navigate to:

   ```
   http://localhost:3000
   ```

### Using the Application

1. Enter search terms in the search box
2. Review the search results, which are ranked by relevance
3. Select books to add to your collection
4. Export your collection in CSV or JSON format

## Development

### Project Structure

* `libgen_explorer/` - Main Python package containing all the core functionality
* `web/` - Web interface built with Node.js
* `tests/` - Test files for the Python modules
* `export_output` - Output files(even you don't choose to generate any report, it still will produce `.txt` file which inorder to let you check search history)

## Team

* Ray Zhang - [rui.zhang@sjsu.edu](mailto:rui.zhang@sjsu.edu)
* Ian Jiang - [jisheng.jiang@sjsu.edu](mailto:jisheng.jiang@sjsu.edu)

## License

TBD

