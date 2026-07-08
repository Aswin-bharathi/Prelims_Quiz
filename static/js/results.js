const POLL_MS = 3000;

function formatTime(seconds) {
    const m = Math.floor(seconds / 60);
    const s = seconds % 60;
    return `${m}:${s < 10 ? '0' : ''}${s}`;
}

// Global variable for polling
if (window.resultsInterval) {
    clearInterval(window.resultsInterval);
}

async function refreshResults() {
    const searchInput = document.querySelector('input[name="search"]');
    const quizSelect = document.querySelector('select[name="quiz_type_id"]');
    const topNSelect = document.querySelector('select[name="top_n"]');
    
    if (!searchInput || !quizSelect || !topNSelect) return;
    
    const search = searchInput.value;
    const quiz_type_id = quizSelect.value;
    const top_n = topNSelect.value;
    
    try {
        const url = `/admin/api/results/data?search=${encodeURIComponent(search)}&quiz_type_id=${encodeURIComponent(quiz_type_id)}&top_n=${encodeURIComponent(top_n)}`;
        const res = await fetch(url);
        if (!res.ok) return;
        const json = await res.json();
        const data = json.data;
        
        // Update top cards if changed
        updateTopCards(data.top_teams, data.top_n);
        
        // Update table rankings
        updateRankingsTable(data.results, data.top_n);
    } catch (e) {
        console.error('Results auto-refresh failed', e);
    }
}

function updateTopCards(teams, top_n) {
    const container = document.querySelector('.grid.grid-cols-1.sm\\:grid-cols-2');
    if (!container) return;
    
    // Simple deep compare of team list to decide if we re-render cards
    const currentTeamsState = container.getAttribute('data-teams-state') || '';
    const newTeamsState = teams.map(t => `${t.lotname}:${t.rank}:${t.score}:${t.duration}`).join('|');
    
    if (currentTeamsState === newTeamsState) {
        return; // No change, skip DOM updates to prevent flickering
    }
    
    container.setAttribute('data-teams-state', newTeamsState);
    
    if (teams.length === 0) {
        container.innerHTML = '';
        const h3 = document.querySelector('h3.text-lg.font-bold');
        if (h3) h3.classList.add('hidden');
        return;
    }
    
    const h3 = document.querySelector('h3.text-lg.font-bold');
    if (h3) {
        h3.classList.remove('hidden');
        h3.innerHTML = `<span class="text-2xl">🏆</span> Top ${top_n} Teams`;
    }
    
    container.innerHTML = teams.map(team => {
        const isFirst = team.rank === 1;
        const borderClass = isFirst ? 'border-amber-400' : 'border-slate-200 dark:border-slate-800';
        const rankBg = team.rank === 1 ? 'bg-amber-100 text-amber-700 dark:bg-amber-900/30 dark:text-amber-400' :
                     team.rank === 2 ? 'bg-slate-200 text-slate-700 dark:bg-slate-800 dark:text-slate-300' :
                     team.rank === 3 ? 'bg-orange-100 text-orange-700 dark:bg-orange-900/30 dark:text-orange-400' :
                     'bg-blue-50 text-blue-700 dark:bg-blue-900/30 dark:text-blue-400';
                     
        return `
        <div class="bg-white dark:bg-slate-900 rounded-2xl border-2 ${borderClass} p-5 shadow-sm text-center relative overflow-hidden transition">
            ${isFirst ? '<div class="absolute top-0 left-0 right-0 h-1 bg-gradient-to-r from-amber-400 to-yellow-300"></div>' : ''}
            <div class="w-10 h-10 rounded-full mx-auto mb-3 flex items-center justify-center font-bold text-lg ${rankBg}">
                #${team.rank}
            </div>
            <p class="font-bold text-sm truncate text-slate-800 dark:text-slate-200">${team.lotname}</p>
            <p class="text-xs text-slate-500 dark:text-slate-400 mt-1">${team.quiz_type_name}</p>
            <p class="text-2xl font-bold text-brand-600 dark:text-brand-400 mt-2">${team.score}</p>
            <p class="text-xs text-slate-500 dark:text-slate-400">${team.duration_formatted}</p>
        </div>`;
    }).join('');
}

function updateRankingsTable(results, top_n) {
    const tbody = document.querySelector('tbody.divide-y');
    if (!tbody) return;
    
    // Check if results state changed
    const currentTableState = tbody.getAttribute('data-table-state') || '';
    const newTableState = results.map(r => `${r.lotname}:${r.rank}:${r.score}:${r.duration}`).join('|');
    
    if (currentTableState === newTableState) {
        return; // No change, skip DOM updates
    }
    
    tbody.setAttribute('data-table-state', newTableState);
    
    if (results.length === 0) {
        tbody.innerHTML = `<tr><td colspan="5" class="px-6 py-12 text-center text-slate-500 dark:text-slate-400 bg-white dark:bg-slate-900">No results yet.</td></tr>`;
        return;
    }
    
    tbody.innerHTML = results.map(r => {
        const topRowClass = r.rank <= top_n ? 'bg-amber-50/30 dark:bg-amber-950/10' : '';
        return `
        <tr class="hover:bg-slate-50 dark:hover:bg-slate-800/40 text-slate-800 dark:text-slate-200 ${topRowClass}">
            <td class="px-6 py-4 font-bold">${r.rank}</td>
            <td class="px-6 py-4 font-semibold">${r.lotname}</td>
            <td class="px-6 py-4"><span class="px-2 py-1 rounded-full text-xs bg-blue-100 text-blue-700 dark:bg-blue-900/30 dark:text-blue-400 font-semibold">${r.quiz_type_name}</span></td>
            <td class="px-6 py-4 font-bold text-brand-600 dark:text-brand-400">${r.score}/${r.total_questions}</td>
            <td class="px-6 py-4 font-mono text-xs">${r.duration_formatted}</td>
        </tr>`;
    }).join('');
}

// Start polling
window.resultsInterval = setInterval(refreshResults, POLL_MS);
// Run once immediately
refreshResults();
