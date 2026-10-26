/**
 * Smart Expense Tracker - Client-side Interactive Engine
 */

let monthlyTrendChartInstance = null;
let categoryDonutChartInstance = null;

document.addEventListener('DOMContentLoaded', () => {
    initTheme();
    initCurrentDate();
    initSidebarToggle();
    loadCategoriesForModals();
    applyDynamicBadges();

    // Default dates in modal inputs
    const today = new Date().toISOString().split('T')[0];
    const stdDateInput = document.getElementById('stdDateInput');
    if (stdDateInput) stdDateInput.value = today;
});

// Dynamic badge styling and progress bar calculation without inline CSS lint issues
function applyDynamicBadges() {
    document.querySelectorAll('[data-badge-color]').forEach(el => {
        const c = el.getAttribute('data-badge-color');
        if (c) {
            el.style.backgroundColor = c + '20';
            el.style.color = c;
            el.style.borderColor = c + '40';
        }
    });
    document.querySelectorAll('[data-progress-width]').forEach(el => {
        const w = el.getAttribute('data-progress-width');
        if (w !== null) {
            el.style.width = w + '%';
        }
    });
}

function handleEditExpenseClick(btn) {
    const ds = btn.dataset;
    if (typeof openEditExpenseModal === 'function') {
        openEditExpenseModal(ds.id, ds.title, ds.amount, ds.categoryId, ds.date, ds.method, ds.notes);
    }
}

// Theme Management (Light / Dark)
function initTheme() {
    const savedTheme = localStorage.getItem('smartspend_theme') || 'dark';
    document.documentElement.setAttribute('data-bs-theme', savedTheme);
    updateThemeIcon(savedTheme);

    const themeToggleBtn = document.getElementById('themeToggleBtn');
    if (themeToggleBtn) {
        themeToggleBtn.addEventListener('click', () => {
            const current = document.documentElement.getAttribute('data-bs-theme');
            const next = current === 'dark' ? 'light' : 'dark';
            document.documentElement.setAttribute('data-bs-theme', next);
            localStorage.setItem('smartspend_theme', next);
            updateThemeIcon(next);

            // Re-render charts with new theme colors if active
            if (window.activeDashboardMonth) {
                initDashboardCharts(window.activeDashboardMonth);
            }
            if (window.activeAnalyticsMonth) {
                initAnalyticsCharts(window.activeAnalyticsMonth);
            }
        });
    }
}

function updateThemeIcon(theme) {
    const icon = document.getElementById('themeIcon');
    if (icon) {
        if (theme === 'dark') {
            icon.className = 'fa-solid fa-sun';
        } else {
            icon.className = 'fa-solid fa-moon';
        }
    }
}

// Current Date Badge
function initCurrentDate() {
    const el = document.getElementById('currentDateDisplay');
    if (el) {
        const options = { weekday: 'short', month: 'short', day: 'numeric', year: 'numeric' };
        el.textContent = new Date().toLocaleDateString('en-US', options);
    }
}

// Sidebar Drawer for Mobile
function initSidebarToggle() {
    const openBtn = document.getElementById('sidebarOpenBtn');
    const closeBtn = document.getElementById('sidebarCloseBtn');
    const sidebar = document.getElementById('appSidebar');

    if (openBtn && sidebar) {
        openBtn.addEventListener('click', () => sidebar.classList.add('show'));
    }
    if (closeBtn && sidebar) {
        closeBtn.addEventListener('click', () => sidebar.classList.remove('show'));
    }
}

// Fetch Categories for Modal Dropdowns
let cachedCategories = [];
async function loadCategoriesForModals() {
    try {
        const res = await fetch('/api/stats/category-breakdown');
        // If not fetched through that endpoint, we can also query select elements directly
        const selects = [
            document.getElementById('smartParsedCategory'),
            document.getElementById('stdCategorySelect'),
            document.getElementById('budgetCategorySelect')
        ];

        // Gather existing options from one select if already present
        const sampleSelect = document.getElementById('editCategory');
        if (sampleSelect && sampleSelect.options.length > 0) {
            selects.forEach(select => {
                if (select && select.options.length === 0) {
                    Array.from(sampleSelect.options).forEach(opt => {
                        select.add(new Option(opt.text, opt.value));
                    });
                }
            });
        }
    } catch (e) {
        console.error('Error loading categories:', e);
    }
}

// Smart AI Natural Language Parsing
async function handleSmartParse() {
    const input = document.getElementById('smartPromptInput');
    const query = input.value.trim();
    if (!query) {
        alert('Please enter a description or expense phrase first.');
        return;
    }

    const parseBtn = document.getElementById('btnParseSmart');
    const originalText = parseBtn.innerHTML;
    parseBtn.innerHTML = '<i class="fa-solid fa-spinner fa-spin me-1"></i> Analyzing syntax...';
    parseBtn.disabled = true;

    try {
        const res = await fetch('/api/smart-parse', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ query })
        });
        const data = await res.json();

        if (res.ok) {
            document.getElementById('smartParsedTitle').value = data.title || '';
            document.getElementById('smartParsedAmount').value = data.amount || '';
            document.getElementById('smartParsedDate').value = data.date || '';
            if (data.payment_method) {
                document.getElementById('smartParsedMethod').value = data.payment_method;
            }
            if (data.notes) {
                document.getElementById('smartParsedNotes').value = data.notes;
            }

            // Set Category
            const catSelect = document.getElementById('smartParsedCategory');
            if (catSelect) {
                for (let i = 0; i < catSelect.options.length; i++) {
                    if (catSelect.options[i].text.toLowerCase() === (data.category || '').toLowerCase()) {
                        catSelect.selectedIndex = i;
                        break;
                    }
                }
            }
        } else {
            alert('Could not parse: ' + (data.error || 'Check input format'));
        }
    } catch (e) {
        console.error('Parsing failed', e);
        alert('Error connecting to AI parser engine.');
    } finally {
        parseBtn.innerHTML = originalText;
        parseBtn.disabled = false;
    }
}

function fillSmartPrompt(text) {
    const input = document.getElementById('smartPromptInput');
    if (input) {
        input.value = text;
        handleSmartParse();
    }
}

// Realtime Category Auto-Suggestion for Standard Modal
let debounceTimer;
function autoSuggestCategory(text) {
    clearTimeout(debounceTimer);
    if (!text || text.length < 3) {
        document.getElementById('categorySuggestionBadge').style.display = 'none';
        return;
    }

    debounceTimer = setTimeout(async () => {
        try {
            const res = await fetch('/api/predict-category', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ text })
            });
            const data = await res.json();
            if (data.category_name) {
                const badge = document.getElementById('categorySuggestionBadge');
                badge.style.display = 'block';
                badge.innerHTML = `<i class="fa-solid fa-wand-magic-sparkles me-1"></i>Auto-suggested: <strong>${data.category_name}</strong>`;

                const select = document.getElementById('stdCategorySelect');
                if (select) {
                    for (let i = 0; i < select.options.length; i++) {
                        if (select.options[i].text === data.category_name) {
                            select.selectedIndex = i;
                            break;
                        }
                    }
                }
            }
        } catch (e) {
            console.error('Auto predict error', e);
        }
    }, 300);
}

// Dashboard Charts Initialization
async function initDashboardCharts(month) {
    window.activeDashboardMonth = month;
    const isDark = document.documentElement.getAttribute('data-bs-theme') === 'dark';
    const gridColor = isDark ? 'rgba(255, 255, 255, 0.06)' : 'rgba(0, 0, 0, 0.06)';
    const textColor = isDark ? '#94a3b8' : '#64748b';

    // 1. Monthly Trend Bar Chart
    const trendCtx = document.getElementById('monthlyTrendChart');
    if (trendCtx) {
        try {
            const res = await fetch('/api/stats/monthly-chart');
            const data = await res.json();

            if (monthlyTrendChartInstance) {
                monthlyTrendChartInstance.destroy();
            }

            monthlyTrendChartInstance = new Chart(trendCtx, {
                type: 'bar',
                data: {
                    labels: data.labels,
                    datasets: [
                        {
                            label: 'Expenses',
                            data: data.expenses,
                            backgroundColor: 'rgba(239, 68, 68, 0.75)',
                            borderColor: '#ef4444',
                            borderRadius: 6,
                            borderWidth: 1
                        },
                        {
                            label: 'Income',
                            data: data.incomes,
                            backgroundColor: 'rgba(16, 185, 129, 0.75)',
                            borderColor: '#10b981',
                            borderRadius: 6,
                            borderWidth: 1
                        }
                    ]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                        legend: {
                            position: 'top',
                            labels: { color: textColor, font: { family: 'Plus Jakarta Sans', weight: 600 } }
                        },
                        tooltip: {
                            callbacks: {
                                label: ctx => ` ${ctx.dataset.label}: $${Number(ctx.raw).toLocaleString(undefined, {minimumFractionDigits: 2})}`
                            }
                        }
                    },
                    scales: {
                        x: {
                            grid: { display: false },
                            ticks: { color: textColor }
                        },
                        y: {
                            grid: { color: gridColor },
                            ticks: {
                                color: textColor,
                                callback: val => '$' + val
                            }
                        }
                    }
                }
            });
        } catch (e) {
            console.error('Error rendering trend chart', e);
        }
    }

    // 2. Category Donut Chart
    const donutCtx = document.getElementById('categoryDonutChart');
    if (donutCtx) {
        try {
            const res = await fetch(`/api/stats/category-breakdown?month=${month}`);
            const data = await res.json();

            if (categoryDonutChartInstance) {
                categoryDonutChartInstance.destroy();
            }

            categoryDonutChartInstance = new Chart(donutCtx, {
                type: 'doughnut',
                data: {
                    labels: data.labels,
                    datasets: [{
                        data: data.data,
                        backgroundColor: data.colors.length ? data.colors : ['#6366f1', '#10b981', '#f59e0b', '#ec4899', '#06b6d4'],
                        borderWidth: isDark ? 2 : 1,
                        borderColor: isDark ? '#111827' : '#ffffff'
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    cutout: '72%',
                    plugins: {
                        legend: {
                            position: 'bottom',
                            labels: {
                                color: textColor,
                                boxWidth: 12,
                                padding: 10,
                                font: { family: 'Plus Jakarta Sans', size: 11 }
                            }
                        },
                        tooltip: {
                            callbacks: {
                                label: ctx => ` ${ctx.label}: $${Number(ctx.raw).toLocaleString(undefined, {minimumFractionDigits: 2})}`
                            }
                        }
                    }
                }
            });
        } catch (e) {
            console.error('Error rendering donut chart', e);
        }
    }
}

// Analytics View Charts Initialization
async function initAnalyticsCharts(month) {
    window.activeAnalyticsMonth = month;
    const isDark = document.documentElement.getAttribute('data-bs-theme') === 'dark';
    const gridColor = isDark ? 'rgba(255, 255, 255, 0.06)' : 'rgba(0, 0, 0, 0.06)';
    const textColor = isDark ? '#94a3b8' : '#64748b';

    // 1. Trajectory Chart
    const trajCtx = document.getElementById('analyticsTrajectoryChart');
    if (trajCtx) {
        const res = await fetch('/api/stats/monthly-chart');
        const data = await res.json();
        new Chart(trajCtx, {
            type: 'line',
            data: {
                labels: data.labels,
                datasets: [
                    {
                        label: 'Income ($)',
                        data: data.incomes,
                        borderColor: '#10b981',
                        backgroundColor: 'rgba(16, 185, 129, 0.1)',
                        fill: true,
                        tension: 0.35,
                        pointRadius: 4
                    },
                    {
                        label: 'Spending ($)',
                        data: data.expenses,
                        borderColor: '#ef4444',
                        backgroundColor: 'rgba(239, 68, 68, 0.1)',
                        fill: true,
                        tension: 0.35,
                        pointRadius: 4
                    }
                ]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: { legend: { labels: { color: textColor } } },
                scales: {
                    x: { ticks: { color: textColor }, grid: { display: false } },
                    y: { ticks: { color: textColor, callback: val => '$' + val }, grid: { color: gridColor } }
                }
            }
        });
    }

    // 2. Category Share
    const catCtx = document.getElementById('analyticsCategoryChart');
    if (catCtx) {
        const res = await fetch(`/api/stats/category-breakdown?month=${month}`);
        const data = await res.json();
        new Chart(catCtx, {
            type: 'polarArea',
            data: {
                labels: data.labels,
                datasets: [{
                    data: data.data,
                    backgroundColor: data.colors.map(c => c + 'aa')
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: { legend: { position: 'right', labels: { color: textColor, font: { size: 10 } } } },
                scales: { r: { ticks: { display: false }, grid: { color: gridColor } } }
            }
        });
    }

    // 3. Daily Velocity Line Chart
    const dailyCtx = document.getElementById('analyticsDailyChart');
    if (dailyCtx) {
        const res = await fetch(`/api/stats/daily-trend?month=${month}`);
        const data = await res.json();
        new Chart(dailyCtx, {
            type: 'line',
            data: {
                labels: data.labels,
                datasets: [{
                    label: 'Daily Spending',
                    data: data.data,
                    borderColor: '#6366f1',
                    backgroundColor: 'rgba(99, 102, 241, 0.15)',
                    fill: true,
                    tension: 0.3,
                    pointRadius: 4,
                    pointBackgroundColor: '#6366f1'
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: { legend: { display: false } },
                scales: {
                    x: { ticks: { color: textColor }, grid: { display: false } },
                    y: { ticks: { color: textColor, callback: val => '$' + val }, grid: { color: gridColor } }
                }
            }
        });
    }

    // 4. Payment Method Distribution Chart
    const payCtx = document.getElementById('analyticsPaymentChart');
    if (payCtx) {
        const res = await fetch(`/api/stats/payment-methods?month=${month}`);
        const data = await res.json();
        new Chart(payCtx, {
            type: 'doughnut',
            data: {
                labels: data.labels,
                datasets: [{
                    data: data.data,
                    backgroundColor: ['#6366f1', '#06b6d4', '#10b981', '#f59e0b', '#ec4899', '#8b5cf6'],
                    borderWidth: 1
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: { legend: { position: 'bottom', labels: { color: textColor, font: { size: 11 } } } }
            }
        });
    }
}
