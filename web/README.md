# LibGen Explorer Web Interface

This directory contains the web interface for LibGen Explorer, which provides a user-friendly way to interact with the LibGen API and the analysis tools.

## Features

- Search LibGen for books
- Filter and analyze search results
- Export results in various formats (CSV, JSON, Excel, HTML)
- Generate summary reports
- View and download exported files

## Setup

1. Make sure you have Node.js installed (version 14 or higher)

2. Install dependencies:
   ```bash
   npm install
   ```

3. Start the server:
   ```bash
   npm start
   ```

4. Open your web browser and navigate to:
   ```
   http://localhost:3000
   ```

## Development

For development with automatic server restart:

```bash
npm run dev
```

## Structure

- `server.js` - Express server that handles API requests
- `public/` - Static files
  - `index.html` - Main HTML page
  - `css/` - CSS stylesheets
  - `js/` - JavaScript files

## API Endpoints

- `POST /api/search` - Search LibGen
- `POST /api/filter` - Filter search results
- `POST /api/analyze` - Analyze search results
- `GET /api/files` - Get list of exported files
- `GET /api/files/:filename` - Download a file
- `DELETE /api/files/:filename` - Delete a file

## Technologies Used

- Express.js - Web server
- GUN - Graphical Universal Network database
- Bootstrap - UI framework
- Font Awesome - Icons