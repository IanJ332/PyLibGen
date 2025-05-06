# PyLibGen# LibGen Explorer

A Python-based tool that connects to the Library Genesis API using GUN (Graphical Database Engine) to help users find open-source CS books and textbooks.

## Motivation

Nowadays, many CS books are available as open-source resources, and some textbooks are uploaded to places like GitHub or Library Genesis. This project aims to simplify the process of finding and collecting data from LibGen by providing a user-friendly interface and powerful search capabilities.

## Features

- Connect to LibGen API to search for books
- Extract and analyze data using Pandas
- Rate search results based on keyword overlap and relevance
- Generate summaries in document or text format
- Web interface for easy interaction

## Installation

### Prerequisites

- Python 3.8 or higher
- Node.js 14 or higher (for web interface)
- pip (Python package manager)
- npm (Node.js package manager)
- poetry

### Setting up the environment

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/libgen-explorer.git
   cd libgen-explorer
   ```
2. Install poetry:
    Go to this website to download poetry [https://python-poetry.org/docs/](https://python-poetry.org/docs/)
3. Create and activate a virtual environment:
   ```bash
   # initialize poetry
   poetry init

   # install the dependancy (setup for windows powershell)
   Get-Content requirements.txt | Where-Object { $_ -notmatch '^\s*#' -and $_ -ne '' } | ForEach-Object { poetry add $_ }

   # go into the server directory
   cd web 

   # setup server
   poetry run npm install
   ```

## Usage

### Starting the application

1. Start the local server:
   ```bash
   # run this in the web folder
   poetry run node server.js
   ```

2. Open your web browser and navigate to:
   ```
   http://localhost:3000
   ```

### Using the application

1. Enter search terms in the search box
2. Review the search results, which are ranked by relevance
3. Select books to add to your collection
4. Export your collection in CSV or JSON format

## Development

### Project Structure

The project is organized as follows:

- `libgen_explorer/` - Main Python package containing all the core functionality
- `web/` - Web interface built with Node.js
- `tests/` - Test files for the Python modules

### Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature-name`
3. Commit your changes: `git commit -m 'Add feature'`
4. Push to the branch: `git push origin feature-name`
5. Submit a pull request

## Team

- Ray Zhang - [rui.zhang@sjsu.edu](mailto:rui.zhang@sjsu.edu)
- Ian Jiang - [jisheng.jiang@sjsu.edu](mailto:jisheng.jiang@sjsu.edu)

## License

T