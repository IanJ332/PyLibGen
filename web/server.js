/**
 * LibGen Explorer Web Server
 * 
 * This is a simple Express server that serves the static frontend files
 * and handles API requests to the Python backend.
 */

const express = require('express');
const bodyParser = require('body-parser');
const { spawn } = require('child_process');
const path = require('path');
const fs = require('fs');
const Gun = require('gun');
const multer = require('multer');
const { promisify } = require('util');
const exec = promisify(require('child_process').exec);

// Configure file upload storage
const storage = multer.diskStorage({
  destination: function (req, file, cb) {
    const outputDir = path.join(__dirname, '..', 'output');
    if (!fs.existsSync(outputDir)) {
      fs.mkdirSync(outputDir, { recursive: true });
    }
    cb(null, outputDir);
  },
  filename: function (req, file, cb) {
    cb(null, `${Date.now()}-${file.originalname}`);
  }
});

const upload = multer({ storage: storage });

// Create Express app
const app = express();
const port = process.env.PORT || 3000;

// Middleware
app.use(bodyParser.json());
app.use(bodyParser.urlencoded({ extended: true }));
app.use(express.static(path.join(__dirname, 'public')));

// GUN server setup
const server = app.listen(port, () => {
  console.log(`LibGen Explorer web server running on port ${port}`);
});

// Initialize GUN with the server
const gun = Gun({
  web: server,
  file: 'gun_data'
});

// API Routes

// Search LibGen
app.post('/api/search', async (req, res) => {
  try {
    const { query, limit = 25, fields, exportFormat, generateSummary } = req.body;

    if (!query) {
      return res.status(400).json({ error: 'Query is required' });
    }

    // Build command arguments
    const args = ['search', query];
    
    if (limit) args.push('--limit', limit.toString());
    if (fields && Array.isArray(fields) && fields.length > 0) {
      args.push('--fields', ...fields);
    }
    
    if (exportFormat) {
      args.push('--export', exportFormat);
      args.push('--output', path.join(__dirname, '..', 'output'));
    }
    
    if (generateSummary) {
      args.push('--summary');
    }

    // Execute Python script
    const result = await runPythonScript(args);
    
    res.json(result);
  } catch (error) {
    console.error('Error processing search request:', error);
    res.status(500).json({ error: 'An error occurred while processing your request' });
  }
});

// Filter results
app.post('/api/filter', upload.single('file'), async (req, res) => {
  try {
    const { filters, format = 'csv', exportFormat } = req.body;
    const inputFile = req.file;

    if (!inputFile || !filters) {
      return res.status(400).json({ error: 'Input file and filters are required' });
    }

    // Build command arguments
    const args = [
      'filter',
      '--input', inputFile.path,
      '--format', format,
      '--filters', filters
    ];
    
    if (exportFormat) {
      args.push('--export', exportFormat);
      args.push('--output', path.join(__dirname, '..', 'output'));
    }

    // Execute Python script
    const result = await runPythonScript(args);
    
    res.json(result);
  } catch (error) {
    console.error('Error processing filter request:', error);
    res.status(500).json({ error: 'An error occurred while processing your request' });
  }
});

// Analyze results
app.post('/api/analyze', upload.single('file'), async (req, res) => {
  try {
    const { keywordFields, topN = 10, format = 'csv', exportFormat } = req.body;
    const inputFile = req.file;

    if (!inputFile) {
      return res.status(400).json({ error: 'Input file is required' });
    }

    // Build command arguments
    const args = [
      'analyze',
      '--input', inputFile.path,
      '--format', format,
      '--top-n', topN.toString()
    ];
    
    if (keywordFields && Array.isArray(keywordFields) && keywordFields.length > 0) {
      args.push('--keyword-fields', ...keywordFields);
    }
    
    if (exportFormat) {
      args.push('--export', exportFormat);
      args.push('--output', path.join(__dirname, '..', 'output'));
    }

    // Execute Python script
    const result = await runPythonScript(args);
    
    res.json(result);
  } catch (error) {
    console.error('Error processing analyze request:', error);
    res.status(500).json({ error: 'An error occurred while processing your request' });
  }
});

// Get list of output files
app.get('/api/files', (req, res) => {
  const outputDir = path.join(__dirname, '..', 'output');
  // res.json({ status: 'ok', message: 'Server is running properly' });

  if (!fs.existsSync(outputDir)) {
    return res.json({ files: [] });
  }
  
  const files = fs.readdirSync(outputDir)
    .filter(file => {
      const filePath = path.join(outputDir, file);
      return fs.statSync(filePath).isFile();
    })
    .map(file => {
      const filePath = path.join(outputDir, file);
      const stats = fs.statSync(filePath);
      return {
        name: file,
        path: `/api/files/${file}`,
        size: stats.size,
        created: stats.ctime
      };
    });
    
  res.json({ files });
});

// Download a file
app.get('/api/files/:filename', (req, res) => {
  const filename = req.params.filename;
  const filePath = path.join(__dirname, '..', 'output', filename);
  
  if (!fs.existsSync(filePath)) {
    return res.status(404).json({ error: 'File not found' });
  }
  
  res.download(filePath);
});

// Delete a file
app.delete('/api/files/:filename', (req, res) => {
  const filename = req.params.filename;
  const filePath = path.join(__dirname, '..', 'output', filename);
  
  if (!fs.existsSync(filePath)) {
    return res.status(404).json({ error: 'File not found' });
  }
  
  fs.unlinkSync(filePath);
  res.json({ success: true });
});

// Testing GUN realted with ISSUES_1
app.get('/api/test-gun', (req, res) => {
  // Test writing to GUN
  const testData = { test: 'data', timestamp: Date.now() };
  gun.get('test').put(testData);
  
  // Test reading from GUN
  gun.get('test').once((data) => {
    res.json({ 
      status: 'ok', 
      message: 'GUN database test', 
      data: data 
    });
  });
});

// Catch-all route for SPA
app.get('*', (req, res) => {
  res.sendFile(path.join(__dirname, 'public', 'index.html'));
});

/**
 * Run the Python CLI script with the given arguments
 * 
 * @param {Array<string>} args - Command-line arguments to pass to the script
 * @returns {Promise<Object>} - Result of the script execution
 */
async function runPythonScript(args) {
  return new Promise((resolve, reject) => {
    // Get the path to the Python script
    // const scriptPath = path.join(__dirname, '..', 'libgen_explorer', 'cli.py');
    const scriptPath = path.join(__dirname, '..', 'libgen-explorer.py');
    
    // Ensure we use the correct Python executable
    let pythonExecutable = 'python';
    
    // Check if we're in a virtual environment
    const venvPython = path.join(__dirname, '..', 'venv', 'bin', 'python');
    if (fs.existsSync(venvPython)) {
      pythonExecutable = venvPython;
    } else {
      // On Windows, check for Scripts directory instead
      const venvPythonWin = path.join(__dirname, '..', 'venv', 'Scripts', 'python.exe');
      if (fs.existsSync(venvPythonWin)) {
        pythonExecutable = venvPythonWin;
      }
    }
    
    console.log(`Executing: ${pythonExecutable} ${scriptPath} ${args.join(' ')}`);
    
    // Spawn the Python process
    const pythonProcess = spawn(pythonExecutable, [scriptPath, ...args], {
      cwd: path.join(__dirname, '..'),
      env: { ...process.env, PYTHONIOENCODING: 'utf-8' }
    });
    
    let stdout = '';
    let stderr = '';
    
    // Collect stdout data
    pythonProcess.stdout.on('data', (data) => {
      const chunk = data.toString();
      stdout += chunk;
      console.log(`Python stdout: ${chunk}`);
    });
    
    // Collect stderr data
    pythonProcess.stderr.on('data', (data) => {
      const chunk = data.toString();
      stderr += chunk;
      console.error(`Python stderr: ${chunk}`);
    });
    
    // Handle process completion
    pythonProcess.on('close', (code) => {
      console.log(`Python process exited with code ${code}`);
      
      if (code !== 0) {
        console.error(`Python script exited with code ${code}`);
        console.error(`stderr: ${stderr}`);
        return reject(new Error(`Python script error: ${stderr}`));
      }
      
      // Try to parse output as JSON if possible
      try {
        const jsonOutput = JSON.parse(stdout);
        resolve(jsonOutput);
      } catch (e) {
        // Not JSON, return as text with stdout/stderr
        resolve({
          output: stdout,
          code
        });
      }
    });
    
    // Handle process errors
    pythonProcess.on('error', (error) => {
      console.error('Failed to start Python process:', error);
      reject(error);
    });
  });
}