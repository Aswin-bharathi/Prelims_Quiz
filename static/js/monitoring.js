const POLL_MS = 3000;

function formatTime(seconds) {
    const m = Math.floor(seconds / 60);
    const s = seconds % 60;
    return `${m}:${s < 10 ? '0' : ''}${s}`;
}

function statusBadge(status) {
    const map = {
        running: 'bg-blue-100 text-blue-700 dark:bg-blue-900/30 dark:text-blue-400',
        ended: 'bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-400',
        scheduled: 'bg-amber-100 text-amber-700 dark:bg-amber-900/30 dark:text-amber-400',
        active: 'bg-emerald-100 text-emerald-700 dark:bg-emerald-900/30 dark:text-emerald-400',
        inactive: 'bg-slate-200 text-slate-600 dark:bg-slate-800 dark:text-slate-400',
    };
    return map[status] || 'bg-slate-100 text-slate-600 dark:bg-slate-800 dark:text-slate-400';
}

function renderCard(q) {
    return `
    <div class="bg-white dark:bg-slate-900 rounded-2xl border border-slate-200 dark:border-slate-800 p-6 shadow-sm hover:shadow-md transition">
        <div class="flex items-start justify-between mb-4">
            <div>
                <h3 class="font-bold text-lg text-slate-800 dark:text-white">${q.name}</h3>
                <code class="text-xs font-mono text-slate-500 dark:text-slate-400">${q.entry_code}</code>
            </div>
            <span class="px-2.5 py-1 rounded-full text-xs font-semibold ${statusBadge(q.quiz_status)}">${q.quiz_status}</span>
        </div>
        <div class="grid grid-cols-2 gap-3 mb-4">
            <div class="p-3 rounded-xl bg-slate-50 dark:bg-slate-800/40">
                <p class="text-xs text-slate-500 dark:text-slate-400">Registered</p>
                <p class="text-xl font-bold text-slate-800 dark:text-white">${q.registered_teams}</p>
            </div>
            <div class="p-3 rounded-xl bg-blue-50 dark:bg-blue-900/10">
                <p class="text-xs text-blue-600 dark:text-blue-400">Active</p>
                <p class="text-xl font-bold text-blue-700 dark:text-blue-300">${q.active_teams}</p>
            </div>
            <div class="p-3 rounded-xl bg-emerald-50 dark:bg-emerald-900/10">
                <p class="text-xs text-emerald-600 dark:text-emerald-400">Completed</p>
                <p class="text-xl font-bold text-emerald-700 dark:text-emerald-300">${q.completed_teams}</p>
            </div>
            <div class="p-3 rounded-xl bg-amber-50 dark:bg-amber-900/10">
                <p class="text-xs text-amber-600 dark:text-amber-400">Remaining</p>
                <p class="text-xl font-bold text-amber-700 dark:text-amber-300">${q.remaining_teams}</p>
            </div>
        </div>
        <div class="flex items-center justify-between text-sm border-t border-slate-100 dark:border-slate-800 pt-4">
            <span class="text-slate-600 dark:text-slate-400">Q ${q.current_question || 0} / ${q.question_count}</span>
            <span class="font-mono font-semibold text-brand-600 dark:text-brand-400">${formatTime(q.remaining_seconds)} left</span>
        </div>
    </div>`;
}

async function refreshMonitoring() {
    try {
        const res = await fetch('/admin/api/monitoring');
        if (!res.ok) return;
        const data = await res.json();
        const grid = document.getElementById('monitoring-grid');
        if (!grid) return;
        if (!data.quizzes || data.quizzes.length === 0) {
            grid.innerHTML = '<p class="text-slate-500 dark:text-slate-400 col-span-full text-center py-12">No quiz types configured.</p>';
            return;
        }
        grid.innerHTML = data.quizzes.map(renderCard).join('');
    } catch (e) {
        console.error('Monitoring refresh failed', e);
    }
}

// Clear any existing interval to prevent leaks
if (window.monitoringInterval) {
    clearInterval(window.monitoringInterval);
}
refreshMonitoring();
window.monitoringInterval = setInterval(refreshMonitoring, POLL_MS);
