/**
 * Main Application Logic
 */

// Global state
let appState = {
    config: null,
    results: null
};

// Initialize on page load
document.addEventListener('DOMContentLoaded', () => {
    setupEventListeners();
    loadConfig();
});

/**
 * Setup Event Listeners
 */
function setupEventListeners() {
    // Main buttons
    document.getElementById('run-button').addEventListener('click', runEngine);
    document.getElementById('reset-button').addEventListener('click', resetApp);
}

/**
 * Load Configuration
 */
async function loadConfig() {
    try {
        const response = await fetch('/api/config');
        appState.config = await response.json();
        
        // Set date input to first available date
        if (appState.config.available_dates && appState.config.available_dates.length > 0) {
            const targetDateInput = document.getElementById('target-date');
            // available_dates are stored as YYYY-DD-MM, but <input type="date"> expects YYYY-MM-DD
            const isoDates = appState.config.available_dates.map(d => {
                const parts = d.split('-');
                // parts = [year, day, month]
                return `${parts[0]}-${parts[2]}-${parts[1]}`;
            });
            targetDateInput.min = isoDates[0];
            targetDateInput.max = isoDates[isoDates.length - 1];
            targetDateInput.value = isoDates[isoDates.length - 1]; // Default to latest
        }
    } catch (error) {
        console.error('Failed to load config:', error);
    }
}

/**
 * Run the Macro Engine
 */
async function runEngine() {
    const targetDate = document.getElementById('target-date').value;
    const investorType = document.getElementById('investor-type').value;
    
    if (!targetDate) {
        alert('Please select a target date');
        return;
    }
    
    if (!investorType) {
        alert('Please select an investor type');
        return;
    }
    
    // Show loading state
    const runButton = document.getElementById('run-button');
    runButton.disabled = true;
    runButton.textContent = 'Processing...';
    
    try {
        const tdparts = targetDate.split('-');
        const normalizedDate = `${tdparts[0]}-${tdparts[2]}-${tdparts[1]}`;

        const response = await fetch('/api/run-engine', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                target_date: normalizedDate,
                investor_type: investorType
            })
        });
        
        const data = await response.json();
        
        if (data.error) {
            alert('Error: ' + data.error);
            return;
        }
        
        appState.results = data;
        displayResults(data);
        
        // Show results panel, hide questionnaire
        document.getElementById('questionnaire-panel').classList.add('hidden');
        document.getElementById('results-panel').classList.remove('hidden');
        
    } catch (error) {
        console.error('Error running engine:', error);
        alert('Failed to run engine: ' + error.message);
    } finally {
        runButton.disabled = false;
        runButton.textContent = 'Get Recommendation →';
    }
}

/**
 * Display Results
 */
function displayResults(data) {
    displayPass4Results(data.pass4_output);
    displayPass5Results(data.pass5_output);
    displayPass6Results(data.pass6_output);
}

/**
 * Display Pass 4 Results (Regime Detection)
 */
function displayPass4Results(pass4) {
    const regimeResults = document.getElementById('regime-results');
    
    let html = `<p><strong>Date:</strong> ${pass4.macro_state.DATE}</p>`;
    html += '<p><strong>Active Regimes:</strong></p>';
    
    pass4.active_regimes.forEach(regime => {
        html += `<span class="regime-tag">${regime.replace(/_/g, ' ')}</span>`;
    });
    
    html += '<div class="regime-strength">';
    html += '<strong>Macro Scores:</strong><br>';
    html += `• Inflation: ${pass4.macro_state.Inflation_Score.toFixed(2)}<br>`;
    html += `• Growth: ${pass4.macro_state.Growth_Score.toFixed(2)}<br>`;
    html += `• Macro/Liquidity: ${pass4.macro_state.Macro_Score.toFixed(2)}`;
    html += '</div>';
    
    regimeResults.innerHTML = html;
}

/**
 * Display Pass 5 Results (Portfolio Selection)
 */
function displayPass5Results(pass5) {
    // Portfolio name
    const portfolioName = document.getElementById('portfolio-name');
    portfolioName.textContent = pass5.selected_portfolio;
    
    // Scores
    const scoresDisplay = document.getElementById('portfolio-scores');
    scoresDisplay.innerHTML = `
        <div class="score-card">
            <div class="score-label">Overall Score</div>
            <div class="score-value">${(pass5.portfolio_score * 100).toFixed(0)}%</div>
        </div>
        <div class="score-card">
            <div class="score-label">Macro Alignment</div>
            <div class="score-value">${(pass5.macro_score * 100).toFixed(0)}%</div>
        </div>
        <div class="score-card">
            <div class="score-label">Investor Fit</div>
            <div class="score-value">${(pass5.investor_score * 100).toFixed(0)}%</div>
        </div>
    `;
    
    // Factor allocation
    const allocationDisplay = document.getElementById('portfolio-allocation');
    let allocationHtml = '<strong>Factor Allocation:</strong><div class="factor-allocation">';
    
    Object.entries(pass5.factor_allocation).forEach(([factor, weight]) => {
        allocationHtml += `
            <div class="factor-item">
                <div class="factor-name">${factor}</div>
                <div class="factor-weight">${(weight * 100).toFixed(0)}%</div>
            </div>
        `;
    });
    
    allocationHtml += '</div>';
    allocationDisplay.innerHTML = allocationHtml;
}

/**
 * Display Pass 6 Results (Asset Construction)
 */
function displayPass6Results(pass6) {
    // ETF allocation table
    const etfAllocation = document.getElementById('etf-allocation');
    let tableHtml = '';
    
    Object.entries(pass6.asset_allocation).forEach(([etf, weight]) => {
        tableHtml += `
            <div class="etf-row">
                <div class="etf-symbol">${etf}</div>
                <div class="etf-weight">
                    <span class="pct">${(weight * 100).toFixed(1)}%</span> allocation
                </div>
            </div>
        `;
    });
    
    etfAllocation.innerHTML = tableHtml;
    
    // Factor to ETF mapping
    const etfMapping = document.getElementById('etf-mapping');
    let mappingHtml = '<strong>Factor → ETF Mapping:</strong><br>';
    
    Object.entries(pass6.factor_to_etf_mapping).forEach(([factor, etf]) => {
        mappingHtml += `<span class="regime-tag">${factor}</span> → <strong>${etf}</strong><br>`;
    });
    
    etfMapping.innerHTML = mappingHtml;
    
    // Explanation
    const explanation = document.getElementById('explanation');
    explanation.innerHTML = `<p>${pass6.explainability_rule}</p>`;
}

/**
 * Reset Application
 */
function resetApp() {
    // Reset form
    document.getElementById('target-date').value = '';
    document.getElementById('investor-type').value = '';
    
    // Toggle panels
    document.getElementById('questionnaire-panel').classList.remove('hidden');
    document.getElementById('results-panel').classList.add('hidden');
    
    // Clear results
    appState.results = null;
}
