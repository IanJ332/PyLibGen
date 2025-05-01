/**
 * LibGen Explorer Web Interface
 * Main JavaScript file for the web interface
 */

// Initialize GUN
const gun = Gun();

// Current view (table or list)
let currentView = 'list';
// Store parsed results for easy switching between views
let parsedResults = [];

document.addEventListener('DOMContentLoaded', function() {
    // Navigation
    setupNavigation();
    
    // Form Handlers
    setupSearchForm();
    setupFilterForm();
    setupAnalyzeForm();
    
    // Files Section
    loadFiles();
    
    // Initialize tooltips
    initTooltips();
});

/**
 * Setup navigation between sections
 */
function setupNavigation() {
    const navLinks = document.querySelectorAll('.navbar-nav .nav-link');
    
    navLinks.forEach(link => {
        link.addEventListener('click', function(e) {
            e.preventDefault();
            
            // Get target section from href
            const targetId = this.getAttribute('href').substring(1);
            const targetSection = document.getElementById(`${targetId}-section`);
            
            if (!targetSection) return;
            
            // Update active nav link
            navLinks.forEach(link => link.classList.remove('active'));
            this.classList.add('active');
            
            // Update active section
            document.querySelectorAll('.section').forEach(section => {
                section.classList.remove('active');
            });
            targetSection.classList.add('active');
            
            // Special handling for files section
            if (targetId === 'files') {
                loadFiles();
            }
        });
    });
}

/**
 * Setup search form submission
 */
function setupSearchForm() {
    const searchForm = document.getElementById('search-form');
    
    if (!searchForm) return;
    
    // Add event listeners for view toggle buttons
    document.querySelectorAll('.view-toggle').forEach(button => {
        button.addEventListener('click', function() {
            const view = this.dataset.view;
            
            // Update active button
            document.querySelectorAll('.view-toggle').forEach(btn => {
                btn.classList.remove('active');
            });
            this.classList.add('active');
            
            // Switch view
            currentView = view;
            
            // Redisplay results if we have them
            if (parsedResults.length > 0) {
                displayResults(parsedResults);
            }
        });
    });
    
    searchForm.addEventListener('submit', async function(e) {
        e.preventDefault();
        
        // Get form values
        const query = document.getElementById('search-query').value.trim();
        const limit = document.getElementById('search-limit').value;
        const fieldsSelect = document.getElementById('search-fields');
        const fields = Array.from(fieldsSelect.selectedOptions).map(option => option.value);
        const exportFormat = document.getElementById('export-format').value;
        const generateSummary = document.getElementById('generate-summary').checked;
        
        if (!query) {
            showError('Please enter a search query');
            return;
        }
        
        // Show results section
        const resultsSection = document.getElementById('search-results');
        resultsSection.classList.remove('d-none');
        
        // Show loading state
        const loadingElement = resultsSection.querySelector('.loading');
        const resultsContainer = resultsSection.querySelector('.results-container');
        loadingElement.classList.remove('d-none');
        resultsContainer.innerHTML = '';
        
        try {
            // Send search request to API
            const response = await fetch('/api/search', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    query,
                    limit: parseInt(limit),
                    fields,
                    exportFormat,
                    generateSummary
                })
            });
            
            const data = await response.json();
            
            if (!response.ok) {
                throw new Error(data.error || 'Failed to perform search');
            }
            
            // Add these console.log statements here
            console.log("Search response data:", data);
            
            // Update results count
            const resultsCountElement = resultsSection.querySelector('.results-count');
            if (resultsCountElement && data.output) {
                // Extract number of results from output
                const match = data.output.match(/Found (\d+) results/);
                if (match && match[1]) {
                    resultsCountElement.textContent = match[1];
                } else {
                    resultsCountElement.textContent = 'N/A';
                }
            }
            
            // Parse results from output
            parsedResults = parseSearchResults(data.output || '');
            
            // Add this console.log after parsing
            console.log("Parsed results:", parsedResults);
            
            // Display results based on current view
            displayResults(parsedResults);
            
            // If files were exported, refresh files list
            if (exportFormat) {
                setTimeout(loadFiles, 1000);
            }
        } catch (error) {
            showError(error.message || 'An error occurred during search');
            resultsContainer.innerHTML = `
                <div class="alert alert-danger">
                    <i class="fas fa-exclamation-circle me-2"></i>
                    Search failed: ${error.message || 'Unknown error'}
                </div>
            `;
        } finally {
            // Hide loading state
            loadingElement.classList.add('d-none');
        }
    });
}

/**
 * Parse search results from command output
 * 
 * @param {string} output - Output from the search command
 * @returns {Array} - Array of parsed result objects
 */
function parseSearchResults(output) {
    console.log("Raw output to parse:", output); // Debug log
    
    const lines = output.split('\n');
    let inResults = false;
    let results = [];
    let currentResult = null;

    for (const line of lines) {
        // Check if we're in the results section
        if (line.match(/Top\s+\d+\s+Results/) || line.includes('Top Results:')) {
            inResults = true;
            console.log("Found results section marker:", line); // Debug log
            continue;
        }
        
        if (!inResults) continue;
        
        // Check for result entry (starts with number followed by ID)
        // const idMatch = line.match(/^(\d+)\.\s+ID\s+(.+)$/);
        // const idMatch = line.match(/^(\d+)\.\s*ID\s+(\d+)/);
        const idMatch = line.match(/^(\d+)\.\s*ID\s+(\d+)/);

        if (idMatch) {
            if (currentResult) {
                results.push(currentResult);
            }
            
            currentResult = {
                number: idMatch[1],
                id: idMatch[2].trim(),
                ipfsLinks: {}
            };
            continue;
        }
        
        // Match other book details
        if (currentResult) {
            // Strip leading spaces and tabs for more reliable matching
            const trimmedLine = line.trim();
            
            if (trimmedLine.startsWith('Author(s)')) {
                const authorMatch = trimmedLine.match(/Author\(s\)\s+(.+)$/);
                if (authorMatch) currentResult.author = authorMatch[1].trim();
            }
            else if (trimmedLine.startsWith('Title')) {
                const titleMatch = trimmedLine.match(/Title\s+(.+)$/);
                if (titleMatch) currentResult.title = titleMatch[1].trim();
            }
            else if (trimmedLine.startsWith('Publisher')) {
                const publisherMatch = trimmedLine.match(/Publisher\s+(.+)$/);
                if (publisherMatch) currentResult.publisher = publisherMatch[1].trim();
            }
            else if (trimmedLine.startsWith('Year')) {
                const yearMatch = trimmedLine.match(/Year\s+(.+)$/);
                if (yearMatch) currentResult.year = yearMatch[1].trim();
            }
            else if (trimmedLine.startsWith('Language(s)')) {
                const langMatch = trimmedLine.match(/Language\(s\)\s+(.+)$/);
                if (langMatch) currentResult.language = langMatch[1].trim();
            }
            else if (trimmedLine.startsWith('Size')) {
                const sizeMatch = trimmedLine.match(/Size\s+(.+)$/);
                if (sizeMatch) currentResult.size = sizeMatch[1].trim();
            }
            else if (trimmedLine.startsWith('Extension')) {
                const formatMatch = trimmedLine.match(/Extension\s+(.+)$/);
                if (formatMatch) currentResult.format = formatMatch[1].trim();
            }
            // Match main download URL
            else if (trimmedLine.startsWith('URL:')) {
                const urlMatch = trimmedLine.match(/URL:\s+(.+)$/);
                if (urlMatch) currentResult.url = urlMatch[1].trim();
            }
            // Match GET download link
            else if (trimmedLine.startsWith('GET Download:')) {
                const getLinkMatch = trimmedLine.match(/GET Download:\s+(.+)$/);
                if (getLinkMatch) currentResult.getLink = getLinkMatch[1].trim();
            }
            // Match IPFS links
            else if (trimmedLine.includes('Cloudflare:')) {
                const cloudflareMatch = trimmedLine.match(/Cloudflare:\s+(.+)$/);
                if (cloudflareMatch) currentResult.ipfsLinks.cloudflare = cloudflareMatch[1].trim();
            }
            else if (trimmedLine.includes('IPFS.io:')) {
                const ipfsioMatch = trimmedLine.match(/IPFS\.io:\s+(.+)$/);
                if (ipfsioMatch) currentResult.ipfsLinks.ipfsio = ipfsioMatch[1].trim();
            }
            else if (trimmedLine.includes('Pinata:')) {
                const pinataMatch = trimmedLine.match(/Pinata:\s+(.+)$/);
                if (pinataMatch) currentResult.ipfsLinks.pinata = pinataMatch[1].trim();
            }
            // Match Tor mirror link
            else if (trimmedLine.startsWith('Tor Mirror:')) {
                const torMatch = trimmedLine.match(/Tor Mirror:\s+(.+)$/);
                if (torMatch) currentResult.torMirror = torMatch[1].trim();
            }
        }
    }

    // Add the last result if it exists
    if (currentResult) {
        results.push(currentResult);
    }
    
    console.log("Parsed results:", results); // Debug log
    return results;
}

/**
 * Display results based on current view
 * 
 * @param {Array} results - Array of parsed result objects
 */
function displayResults(results) {
    const resultsContainer = document.querySelector('.results-container');
    
    if (!resultsContainer) {
        console.error("Results container not found");
        return;
    }
    
    console.log(`Displaying ${results.length} results in ${currentView} view`);
    
    if (!results || results.length === 0) {
        resultsContainer.innerHTML = `
            <div class="alert alert-info">
                <i class="fas fa-info-circle me-2"></i>
                No results found. Try modifying your search query.
            </div>
        `;
        return;
    }
    
    if (currentView === 'table') {
        displayTableView(results, resultsContainer);
    } else {
        displayListView(results, resultsContainer);
    }
}

/**
 * Update the search form submission function to better handle the response
 */
function setupSearchForm() {
    const searchForm = document.getElementById('search-form');
    
    if (!searchForm) return;
    
    // Add event listeners for view toggle buttons
    document.querySelectorAll('.view-toggle').forEach(button => {
        button.addEventListener('click', function() {
            const view = this.dataset.view;
            
            // Update active button
            document.querySelectorAll('.view-toggle').forEach(btn => {
                btn.classList.remove('active');
            });
            this.classList.add('active');
            
            // Switch view
            currentView = view;
            
            // Redisplay results if we have them
            if (parsedResults.length > 0) {
                displayResults(parsedResults);
            }
        });
    });
    
    searchForm.addEventListener('submit', async function(e) {
        e.preventDefault();
        
        // Get form values
        const query = document.getElementById('search-query').value.trim();
        const limit = document.getElementById('search-limit').value;
        const fieldsSelect = document.getElementById('search-fields');
        const fields = Array.from(fieldsSelect.selectedOptions).map(option => option.value);
        const exportFormat = document.getElementById('export-format').value;
        const generateSummary = document.getElementById('generate-summary').checked;
        
        if (!query) {
            showError('Please enter a search query');
            return;
        }
        
        // Show results section
        const resultsSection = document.getElementById('search-results');
        resultsSection.classList.remove('d-none');
        
        // Show loading state
        const loadingElement = resultsSection.querySelector('.loading');
        const resultsContainer = resultsSection.querySelector('.results-container');
        loadingElement.classList.remove('d-none');
        resultsContainer.innerHTML = '';
        
        try {
            // Send search request to API
            const response = await fetch('/api/search', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    query,
                    limit: parseInt(limit),
                    fields,
                    exportFormat,
                    generateSummary
                })
            });
            
            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.error || 'Failed to perform search');
            }
            
            const data = await response.json();
            console.log("Search response data:", data);

            // Update results count
            const resultsCountElement = resultsSection.querySelector('.results-count');
            if (resultsCountElement && data.output) {
                // Extract number of results from output
                const match = data.output.match(/Found (\d+) results/);
                if (match && match[1]) {
                    resultsCountElement.textContent = match[1];
                } else {
                    resultsCountElement.textContent = 'N/A';
                }
            }
            
            // Parse results from output
            parsedResults = parseSearchResults(data.output || '');
            console.log("Parsed results:", parsedResults);
            
            // Display results based on current view
            displayResults(parsedResults);
            
            // If files were exported, refresh files list
            if (exportFormat) {
                setTimeout(loadFiles, 1000);
            }
        } catch (error) {
            console.error("Search error:", error);
            showError(error.message || 'An error occurred during search');
            resultsContainer.innerHTML = `
                <div class="alert alert-danger">
                    <i class="fas fa-exclamation-circle me-2"></i>
                    Search failed: ${error.message || 'Unknown error'}
                </div>
            `;
        } finally {
            // Hide loading state
            loadingElement.classList.add('d-none');
        }
    });
}

/**
 * Display results in table view
 * 
 * @param {Array} results - Array of parsed result objects
 * @param {HTMLElement} container - Container element to display results in
 */
function displayTableView(results, container) {
    let html = `
        <div class="table-responsive">
            <table class="table table-striped table-hover">
                <thead class="table-light">
                    <tr>
                        <th>#</th>
                        <th>Title</th>
                        <th>Author(s)</th>
                        <th>Year</th>
                        <th>Publisher</th>
                        <th>Format</th>
                        <th>Size</th>
                        <th>Actions</th>
                    </tr>
                </thead>
                <tbody>
    `;
    
    for (const result of results) {
        html += `
            <tr>
                <td>${result.number}</td>
                <td class="title-cell">${result.title || 'N/A'}</td>
                <td class="author-cell">${result.author || 'N/A'}</td>
                <td>${result.year || 'N/A'}</td>
                <td class="publisher-cell">${result.publisher || 'N/A'}</td>
                <td>${result.format || 'N/A'}</td>
                <td>${result.size || 'N/A'}</td>
                <td>
                    <div class="btn-group">
                        ${result.url ? `
                            <a href="${result.url}" class="btn btn-sm btn-outline-primary" target="_blank" title="Visit source page">
                                <i class="fas fa-external-link-alt"></i> <span>Visit</span>
                            </a>
                        ` : ''}
                        ${result.getLink ? `
                            <a href="${result.getLink}" class="btn btn-sm btn-success" target="_blank" title="Download file">
                                <i class="fas fa-download"></i> <span>Download</span>
                            </a>
                        ` : ''}                       
                        ${Object.keys(result.ipfsLinks).length > 0 ? `
                            <div class="dropdown d-inline-block">
                                <button class="btn btn-sm btn-outline-info dropdown-toggle" type="button" data-bs-toggle="dropdown" aria-expanded="false">
                                    <i class="fas fa-network-wired"></i> <span>IPFS</span>
                                </button>
                                <ul class="dropdown-menu">
                                    ${result.ipfsLinks.cloudflare ? `
                                        <li><a class="dropdown-item" href="${result.ipfsLinks.cloudflare}" target="_blank">Cloudflare</a></li>
                                    ` : ''}
                                    ${result.ipfsLinks.ipfsio ? `
                                        <li><a class="dropdown-item" href="${result.ipfsLinks.ipfsio}" target="_blank">IPFS.io</a></li>
                                    ` : ''}
                                    ${result.ipfsLinks.pinata ? `
                                        <li><a class="dropdown-item" href="${result.ipfsLinks.pinata}" target="_blank">Pinata</a></li>
                                    ` : ''}
                                </ul>
                            </div>
                        ` : ''}
                    </div>
                </td>
            </tr>
        `;
    }
    
    html += `
                </tbody>
            </table>
        </div>
    `;
    
    container.innerHTML = html;
}

/**
 * Display results in list view (original view)
 * 
 * @param {Array} results - Array of parsed result objects
 * @param {HTMLElement} container - Container element to display results in
 */
function displayListView(results, container) {
    let html = '';
    
    for (const result of results) {
        html += `
            <div class="result-item">
                <div class="result-title">${result.number}. ${result.title}</div>
                <div class="result-author">by ${result.author || 'Unknown'} ${result.year ? `(${result.year})` : ''}</div>
                <div class="result-meta">
                    ${result.publisher ? `<span><i class="fas fa-building"></i> ${result.publisher}</span>` : ''}
                    ${result.format ? `<span><i class="fas fa-file"></i> ${result.format}</span>` : ''}
                    ${result.size ? `<span><i class="fas fa-weight"></i> ${result.size}</span>` : ''}
                    ${result.language ? `<span><i class="fas fa-language"></i> ${result.language}</span>` : ''}
                </div>
                <div class="result-links mt-2">
                    ${result.url ? `
                        <a href="${result.url}" class="btn btn-sm btn-outline-primary me-2" target="_blank">
                            <i class="fas fa-link"></i> Main Link
                        </a>
                    ` : ''}
                    ${result.getLink ? `
                        <a href="${result.getLink}" class="btn btn-sm btn-success me-2" target="_blank">
                            <i class="fas fa-download"></i> GET
                        </a>
                    ` : ''}                   
                    ${Object.keys(result.ipfsLinks).length > 0 ? `
                        <div class="dropdown d-inline-block me-2">
                            <button class="btn btn-sm btn-outline-info dropdown-toggle" type="button" id="dropdownIpfs${result.number}" data-bs-toggle="dropdown" aria-expanded="false">
                                <i class="fas fa-network-wired"></i> IPFS
                            </button>
                            <ul class="dropdown-menu" aria-labelledby="dropdownIpfs${result.number}">
                                ${result.ipfsLinks.cloudflare ? `
                                    <li><a class="dropdown-item" href="${result.ipfsLinks.cloudflare}" target="_blank">Cloudflare</a></li>
                                ` : ''}
                                ${result.ipfsLinks.ipfsio ? `
                                    <li><a class="dropdown-item" href="${result.ipfsLinks.ipfsio}" target="_blank">IPFS.io</a></li>
                                ` : ''}
                                ${result.ipfsLinks.pinata ? `
                                    <li><a class="dropdown-item" href="${result.ipfsLinks.pinata}" target="_blank">Pinata</a></li>
                                ` : ''}
                            </ul>
                        </div>
                    ` : ''}
                    ${result.torMirror ? `
                        <a href="${result.torMirror}" class="btn btn-sm btn-outline-dark" target="_blank">
                            <i class="fas fa-mask"></i> Tor Mirror
                        </a>
                    ` : ''}
                </div>
            </div>
        `;
    }
    
    container.innerHTML = html;
}

/**
 * Setup filter form submission
 */
function setupFilterForm() {
    const filterForm = document.getElementById('filter-form');
    
    if (!filterForm) return;
    
    filterForm.addEventListener('submit', async function(e) {
        e.preventDefault();
        
        // Get form values
        const fileInput = document.getElementById('filter-file');
        const format = document.getElementById('filter-format').value;
        const criteria = document.getElementById('filter-criteria').value.trim();
        const exportFormat = document.getElementById('filter-export-format').value;
        
        if (!fileInput.files || fileInput.files.length === 0) {
            showError('Please select a file to filter');
            return;
        }
        
        if (!criteria) {
            showError('Please enter filter criteria');
            return;
        }
        
        // Validate JSON
        try {
            JSON.parse(criteria);
        } catch (e) {
            showError('Invalid JSON format for filter criteria');
            return;
        }
        
        // Show results section
        const resultsSection = document.getElementById('filter-results');
        resultsSection.classList.remove('d-none');
        
        // Show loading state
        const loadingElement = resultsSection.querySelector('.filter-loading');
        const resultsContainer = resultsSection.querySelector('.filter-results-container');
        loadingElement.classList.remove('d-none');
        resultsContainer.innerHTML = '';
        
        try {
            // Create form data
            const formData = new FormData();
            formData.append('file', fileInput.files[0]);
            formData.append('format', format);
            formData.append('filters', criteria);
            
            if (exportFormat) {
                formData.append('exportFormat', exportFormat);
            }
            
            // Send filter request to API
            const response = await fetch('/api/filter', {
                method: 'POST',
                body: formData
            });
            
            const data = await response.json();
            
            if (!response.ok) {
                throw new Error(data.error || 'Failed to filter results');
            }
            
            // Update results count
            const resultsCountElement = resultsSection.querySelector('.filter-results-count');
            if (resultsCountElement && data.output) {
                // Extract number of results from output
                const match = data.output.match(/Filtered Results \((\d+) rows\)/);
                if (match && match[1]) {
                    resultsCountElement.textContent = match[1];
                } else {
                    resultsCountElement.textContent = 'N/A';
                }
            }
            
            // Display results
            displayFilterResults(data.output || 'No output from filter command');
            
            // If files were exported, refresh files list
            if (exportFormat) {
                setTimeout(loadFiles, 1000);
            }
        } catch (error) {
            showError(error.message || 'An error occurred during filtering');
            resultsContainer.innerHTML = `
                <div class="alert alert-danger">
                    <i class="fas fa-exclamation-circle me-2"></i>
                    Filtering failed: ${error.message || 'Unknown error'}
                </div>
            `;
        } finally {
            // Hide loading state
            loadingElement.classList.add('d-none');
        }
    });
}

/**
 * Display filter results in the results container
 * 
 * @param {string} output - Output from the filter command
 */
function displayFilterResults(output) {
    const resultsContainer = document.querySelector('.filter-results-container');
    
    if (!resultsContainer) return;
    
    // For simplicity, display raw output
    resultsContainer.innerHTML = `
        <pre class="bg-light p-3 rounded">${output}</pre>
    `;
}

/**
 * Setup analyze form submission
 */
function setupAnalyzeForm() {
    const analyzeForm = document.getElementById('analyze-form');
    
    if (!analyzeForm) return;
    
    analyzeForm.addEventListener('submit', async function(e) {
        e.preventDefault();
        
        // Get form values
        const fileInput = document.getElementById('analyze-file');
        const format = document.getElementById('analyze-format').value;
        const keywordFieldsSelect = document.getElementById('keyword-fields');
        const keywordFields = Array.from(keywordFieldsSelect.selectedOptions).map(option => option.value);
        const topN = document.getElementById('top-n').value;
        const exportFormat = document.getElementById('analyze-export-format').value;
        
        if (!fileInput.files || fileInput.files.length === 0) {
            showError('Please select a file to analyze');
            return;
        }
        
        // Show results section
        const resultsSection = document.getElementById('analysis-results');
        resultsSection.classList.remove('d-none');
        
        // Show loading state
        const loadingElement = resultsSection.querySelector('.analysis-loading');
        const resultsContainer = resultsSection.querySelector('.analysis-results-container');
        loadingElement.classList.remove('d-none');
        resultsContainer.innerHTML = '';
        
        try {
            // Create form data
            const formData = new FormData();
            formData.append('file', fileInput.files[0]);
            formData.append('format', format);
            
            if (keywordFields.length > 0) {
                keywordFields.forEach(field => {
                    formData.append('keywordFields[]', field);
                });
            }
            
            formData.append('topN', topN);
            
            if (exportFormat) {
                formData.append('exportFormat', exportFormat);
            }
            
            // Send analyze request to API
            const response = await fetch('/api/analyze', {
                method: 'POST',
                body: formData
            });
            
            const data = await response.json();
            
            if (!response.ok) {
                throw new Error(data.error || 'Failed to analyze results');
            }
            
            // Display results
            displayAnalysisResults(data.output || 'No output from analyze command');
            
            // If files were exported, refresh files list
            if (exportFormat) {
                setTimeout(loadFiles, 1000);
            }
        } catch (error) {
            showError(error.message || 'An error occurred during analysis');
            resultsContainer.innerHTML = `
                <div class="alert alert-danger">
                    <i class="fas fa-exclamation-circle me-2"></i>
                    Analysis failed: ${error.message || 'Unknown error'}
                </div>
            `;
        } finally {
            // Hide loading state
            loadingElement.classList.add('d-none');
        }
    });
}

/**
 * Display analysis results in the results container
 * 
 * @param {string} output - Output from the analyze command
 */
function displayAnalysisResults(output) {
    const resultsContainer = document.querySelector('.analysis-results-container');
    
    if (!resultsContainer) return;
    
    // For simplicity, display raw output
    resultsContainer.innerHTML = `
        <pre class="bg-light p-3 rounded">${output}</pre>
    `;
}

/**
 * Load the list of exported files
 */
async function loadFiles() {
    const filesContainer = document.querySelector('.files-container');
    const loadingElement = document.querySelector('.files-loading');
    const noFilesElement = document.querySelector('.no-files');
    
    if (!filesContainer || !loadingElement || !noFilesElement) return;
    
    // Show loading state
    loadingElement.classList.remove('d-none');
    noFilesElement.classList.add('d-none');
    filesContainer.innerHTML = '';
    
    try {
        // Fetch files from API
        const response = await fetch('/api/files');
        const data = await response.json();
        
        if (!response.ok) {
            throw new Error(data.error || 'Failed to load files');
        }
        
        if (!data.files || data.files.length === 0) {
            // No files found
            noFilesElement.classList.remove('d-none');
            return;
        }
        
        // Build HTML for files
        let html = '';
        
        for (const file of data.files) {
            const fileExtension = file.name.split('.').pop().toLowerCase();
            let iconClass = 'fa-file';
            
            // Set icon based on file type
            if (['csv', 'xlsx', 'xls'].includes(fileExtension)) {
                iconClass = 'fa-file-csv';
            } else if (fileExtension === 'json') {
                iconClass = 'fa-file-code';
            } else if (fileExtension === 'html') {
                iconClass = 'fa-file-code';
            } else if (fileExtension === 'txt') {
                iconClass = 'fa-file-alt';
            }
            
            // Format date
            const fileDate = new Date(file.created).toLocaleString();
            
            // Format file size
            let fileSize = file.size;
            let sizeUnit = 'B';
            
            if (fileSize > 1024) {
                fileSize = fileSize / 1024;
                sizeUnit = 'KB';
            }
            
            if (fileSize > 1024) {
                fileSize = fileSize / 1024;
                sizeUnit = 'MB';
            }
            
            fileSize = fileSize.toFixed(2);
            
            html += `
                <div class="file-item" data-filename="${file.name}">
                    <div class="file-icon">
                        <i class="fas ${iconClass}"></i>
                    </div>
                    <div class="file-info">
                        <div class="file-name">${file.name}</div>
                        <div class="file-meta">
                            <span>${fileSize} ${sizeUnit}</span> &bull; <span>${fileDate}</span>
                        </div>
                    </div>
                    <div class="file-actions">
                        <a href="${file.path}" class="btn btn-sm btn-outline-primary download-file">
                            <i class="fas fa-download"></i> Download
                        </a>
                        <button type="button" class="btn btn-sm btn-outline-danger delete-file">
                            <i class="fas fa-trash"></i> Delete
                        </button>
                    </div>
                </div>
            `;
        }
        
        filesContainer.innerHTML = html;
        
        // Add event listeners for delete buttons
        document.querySelectorAll('.delete-file').forEach(button => {
            button.addEventListener('click', function() {
                const fileItem = this.closest('.file-item');
                const filename = fileItem.dataset.filename;
                
                if (filename) {
                    showDeleteConfirmation(filename);
                }
            });
        });
    } catch (error) {
        filesContainer.innerHTML = `
            <div class="alert alert-danger">
                <i class="fas fa-exclamation-circle me-2"></i>
                Failed to load files: ${error.message || 'Unknown error'}
            </div>
        `;
    } finally {
        // Hide loading state
        loadingElement.classList.add('d-none');
    }
}

/**
 * Show delete confirmation modal
 * 
 * @param {string} filename - Name of the file to delete
 */
function showDeleteConfirmation(filename) {
    const modal = document.getElementById('file-delete-modal');
    const filenameElement = document.getElementById('delete-filename');
    const confirmButton = document.getElementById('confirm-delete');
    
    if (!modal || !filenameElement || !confirmButton) return;
    
    // Set filename in modal
    filenameElement.textContent = filename;
    
    // Set up confirm button
    confirmButton.onclick = async function() {
        try {
            // Send delete request to API
            const response = await fetch(`/api/files/${filename}`, {
                method: 'DELETE'
            });
            
            const data = await response.json();
            
            if (!response.ok) {
                throw new Error(data.error || 'Failed to delete file');
            }
            
            // Close modal
            const bsModal = bootstrap.Modal.getInstance(modal);
            bsModal.hide();
            
            // Refresh files list
            loadFiles();
        } catch (error) {
            showError(error.message || 'An error occurred while deleting the file');
        }
    };
    
    // Show modal
    const bsModal = new bootstrap.Modal(modal);
    bsModal.show();
}

/**
 * Show error modal with message
 * 
 * @param {string} message - Error message to display
 */
function showError(message) {
    const modal = document.getElementById('error-modal');
    const messageElement = document.getElementById('error-message');
    
    if (!modal || !messageElement) return;
    
    messageElement.textContent = message;
    
    const bsModal = new bootstrap.Modal(modal);
    bsModal.show();
}

/**
 * Initialize Bootstrap tooltips
 */
function initTooltips() {
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    tooltipTriggerList.map(function(tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });
}