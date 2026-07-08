// Thin premium progress loader at top of screen
function showLoader() {
    let loader = document.getElementById('ajax-loader');
    if (!loader) {
        loader = document.createElement('div');
        loader.id = 'ajax-loader';
        loader.className = 'fixed top-0 left-0 h-1 bg-brand-600 dark:bg-brand-500 z-50 transition-all duration-300 ease-out';
        loader.style.width = '0%';
        document.body.appendChild(loader);
    }
    loader.style.width = '10%';
    loader.style.opacity = '1';
    
    if (window.loaderTimer) clearInterval(window.loaderTimer);
    window.loaderTimer = setInterval(() => {
        const curWidth = parseFloat(loader.style.width);
        if (curWidth < 90) {
            loader.style.width = (curWidth + (90 - curWidth) * 0.15) + '%';
        }
    }, 100);
}

function hideLoader() {
    const loader = document.getElementById('ajax-loader');
    if (!loader) return;
    if (window.loaderTimer) clearInterval(window.loaderTimer);
    loader.style.width = '100%';
    setTimeout(() => {
        loader.style.opacity = '0';
        setTimeout(() => {
            loader.style.width = '0%';
        }, 300);
    }, 200);
}

// Toast notification utility
function showToast(message, type = 'success') {
    let container = document.getElementById('toast-container');
    if (!container) {
        container = document.createElement('div');
        container.id = 'toast-container';
        container.className = 'fixed top-4 right-4 z-50 space-y-2 max-w-sm';
        document.body.appendChild(container);
    }
    
    const toast = document.createElement('div');
    toast.className = `toast toast-${type} px-4 py-3 rounded-xl shadow-lg border text-sm font-medium animate-slide-in transition-all duration-300 transform translate-x-4 opacity-0`;
    
    if (type === 'error') {
        toast.className += ' bg-red-50 border-red-200 text-red-800 dark:bg-red-950/20 dark:border-red-900/50 dark:text-red-400';
    } else if (type === 'success') {
        toast.className += ' bg-emerald-50 border-emerald-200 text-emerald-800 dark:bg-emerald-950/20 dark:border-emerald-900/50 dark:text-emerald-400';
    } else {
        toast.className += ' bg-blue-50 border-blue-200 text-blue-800 dark:bg-blue-950/20 dark:border-blue-900/50 dark:text-blue-400';
    }
    
    toast.textContent = message;
    container.appendChild(toast);
    
    setTimeout(() => {
        toast.classList.remove('translate-x-4', 'opacity-0');
    }, 10);
    
    setTimeout(() => {
        toast.classList.add('translate-x-4', 'opacity-0');
        setTimeout(() => toast.remove(), 300);
    }, 4500);
}

// Generate CSS selector path for uniquely identifying nodes to restore scroll
function getUniqueSelector(el) {
    if (el.id) return `#${el.id}`;
    let path = [];
    while (el && el.nodeType === Node.ELEMENT_NODE) {
        let selector = el.nodeName.toLowerCase();
        if (el.className) {
            const classes = el.className.trim().split(/\s+/).filter(c => c && !c.includes(':')).join('.');
            if (classes) selector += `.${classes}`;
        }
        let sib = el, sibIndex = 1;
        while (sib = sib.previousElementSibling) {
            if (sib.nodeName.toLowerCase() === el.nodeName.toLowerCase()) {
                sibIndex++;
            }
        }
        selector += `:nth-of-type(${sibIndex})`;
        path.unshift(selector);
        el = el.parentNode;
    }
    return path.join(' > ');
}

// API Mapping table
function getApiUrl(pageUrl) {
    let urlObj = new URL(pageUrl, window.location.origin);
    let path = urlObj.pathname;
    
    if (path === '/admin/questions/add') return '/admin/api/questions';
    if (path.match(/^\/admin\/questions\/(\d+)\/edit$/)) {
        return path.replace(/^\/admin\/questions\/(\d+)\/edit$/, '/admin/api/questions/$1');
    }
    if (path.match(/^\/admin\/questions\/(\d+)\/delete$/)) {
        return path.replace(/^\/admin\/questions\/(\d+)\/delete$/, '/admin/api/questions/$1/delete');
    }
    if (path === '/admin/questions/bulk-delete') return '/admin/api/questions/bulk-delete';
    
    if (path === '/admin/teams/add') return '/admin/api/teams';
    if (path.match(/^\/admin\/teams\/(\d+)\/edit$/)) {
        return path.replace(/^\/admin\/teams\/(\d+)\/edit$/, '/admin/api/teams/$1');
    }
    if (path.match(/^\/admin\/teams\/(\d+)\/delete$/)) {
        return path.replace(/^\/admin\/teams\/(\d+)\/delete$/, '/admin/api/teams/$1/delete');
    }
    if (path === '/admin/teams/sync') return '/admin/api/teams/sync';
    
    if (path === '/admin/quiz-types/create') return '/admin/api/quiz-types';
    if (path.match(/^\/admin\/quiz-types\/(\d+)\/edit$/)) {
        return path.replace(/^\/admin\/quiz-types\/(\d+)\/edit$/, '/admin/api/quiz-types/$1');
    }
    if (path.match(/^\/admin\/quiz-types\/(\d+)\/delete$/)) {
        return path.replace(/^\/admin\/quiz-types\/(\d+)\/delete$/, '/admin/api/quiz-types/$1/delete');
    }
    if (path.match(/^\/admin\/quiz-types\/(\d+)\/toggle$/)) {
        return path.replace(/^\/admin\/quiz-types\/(\d+)\/toggle$/, '/admin/api/quiz-types/$1/toggle');
    }
    if (path.match(/^\/admin\/quiz-types\/(\d+)\/start$/)) {
        return path.replace(/^\/admin\/quiz-types\/(\d+)\/start$/, '/admin/api/quiz-types/$1/start');
    }
    if (path.match(/^\/admin\/quiz-types\/(\d+)\/end$/)) {
        return path.replace(/^\/admin\/quiz-types\/(\d+)\/end$/, '/admin/api/quiz-types/$1/end');
    }
    
    if (path === '/admin/settings') return '/admin/api/settings';
    
    return null;
}

// Global AJAX Page Navigation
async function navigateTo(url, pushState = true) {
    showLoader();
    
    // Clear dynamic intervals to prevent leaks
    if (window.monitoringInterval) clearInterval(window.monitoringInterval);
    if (window.resultsInterval) clearInterval(window.resultsInterval);
    
    try {
        const response = await fetch(url);
        if (!response.ok) {
            showToast('Failed to load page', 'error');
            hideLoader();
            return;
        }
        
        const htmlText = await response.text();
        
        // Save focus and cursor
        const activeElementId = document.activeElement ? document.activeElement.name || document.activeElement.id : null;
        const selectionStart = document.activeElement ? document.activeElement.selectionStart : null;
        const selectionEnd = document.activeElement ? document.activeElement.selectionEnd : null;
        
        // Save scroll states
        const scrollPositions = [];
        document.querySelectorAll('*').forEach(el => {
            if (el.scrollTop > 0 || el.scrollLeft > 0) {
                try {
                    scrollPositions.push({
                        selector: getUniqueSelector(el),
                        scrollTop: el.scrollTop,
                        scrollLeft: el.scrollLeft
                    });
                } catch (err) {}
            }
        });
        
        // Parse HTML
        const parser = new DOMParser();
        const doc = parser.parseFromString(htmlText, 'text/html');
        
        // Swap Main content
        const newMain = doc.querySelector('main');
        const currentMain = document.querySelector('main');
        if (newMain && currentMain) {
            currentMain.innerHTML = newMain.innerHTML;
        }
        
        // Swap Page Title
        const newHeaderTitle = doc.querySelector('header h2');
        const currentHeaderTitle = document.querySelector('header h2');
        if (newHeaderTitle && currentHeaderTitle) {
            currentHeaderTitle.innerHTML = newHeaderTitle.innerHTML;
        }
        
        document.title = doc.title;
        
        // Highlight active nav item
        const urlObj = new URL(url, window.location.origin);
        const path = urlObj.pathname;
        document.querySelectorAll('aside nav a').forEach(link => {
            const linkUrl = new URL(link.getAttribute('href'), window.location.origin);
            if (linkUrl.pathname === path) {
                link.className = 'flex items-center gap-3 px-4 py-2.5 rounded-lg text-sm font-medium transition-colors bg-brand-600 text-white';
            } else {
                link.className = 'flex items-center gap-3 px-4 py-2.5 rounded-lg text-sm font-medium transition-colors text-slate-300 hover:bg-slate-800 dark:hover:bg-slate-800 hover:text-white';
            }
        });
        
        // Remove and rerun dynamic scripts
        document.querySelectorAll('.dynamic-script').forEach(el => el.remove());
        doc.querySelectorAll('body script, main script').forEach(oldScript => {
            if (oldScript.src && oldScript.src.includes('admin.js')) return;
            const newScript = document.createElement('script');
            newScript.className = 'dynamic-script';
            Array.from(oldScript.attributes).forEach(attr => newScript.setAttribute(attr.name, attr.value));
            newScript.appendChild(document.createTextNode(oldScript.innerHTML));
            document.body.appendChild(newScript);
        });
        
        // Restore focus
        if (activeElementId) {
            const el = document.querySelector(`[name="${activeElementId}"], #${activeElementId}`);
            if (el) {
                el.focus();
                if (selectionStart !== null && selectionEnd !== null) {
                    try {
                        el.setSelectionRange(selectionStart, selectionEnd);
                    } catch (e) {}
                }
            }
        }
        
        // Restore scroll
        scrollPositions.forEach(pos => {
            const el = document.querySelector(pos.selector);
            if (el) {
                el.scrollTop = pos.scrollTop;
                el.scrollLeft = pos.scrollLeft;
            }
        });
        
        if (pushState) {
            window.history.pushState(null, '', url);
        }
        
        // Handle mobile sidebar collapse
        const sidebar = document.getElementById('sidebar');
        const overlay = document.getElementById('sidebar-overlay');
        if (sidebar && !sidebar.classList.contains('-translate-x-full')) {
            sidebar.classList.add('-translate-x-full');
            overlay.classList.add('hidden');
        }
        
        // Show new flash messages as toasts
        doc.querySelectorAll('#toast-container .toast').forEach(t => {
            const type = t.className.includes('toast-error') ? 'error' : 'success';
            showToast(t.textContent.trim(), type);
        });
        
        hideLoader();
    } catch (e) {
        console.error(e);
        hideLoader();
        showToast('Error navigating to page', 'error');
    }
}

async function reloadPageContent() {
    await navigateTo(window.location.href, false);
}

// Handle Form Post submissions
async function handleFormPost(form, action) {
    showLoader();
    const apiUrl = getApiUrl(action);
    const formData = new FormData(form);
    
    try {
        let response;
        if (apiUrl) {
            // Build standard JSON object
            const obj = {};
            formData.forEach((value, key) => {
                if (key.endsWith('[]') || form.querySelector(`[name="${key}"][multiple]`)) {
                    if (!obj[key]) obj[key] = [];
                    obj[key].push(value);
                } else if (form.querySelectorAll(`[name="${key}"]`).length > 1 && 
                           (form.querySelector(`[name="${key}"][type="checkbox"]`) || form.querySelector(`[name="${key}"][type="radio"]`))) {
                    if (form.querySelector(`[name="${key}"][type="checkbox"]`)) {
                        if (!obj[key]) obj[key] = [];
                        obj[key].push(value);
                    } else {
                        obj[key] = value;
                    }
                } else {
                    obj[key] = value;
                }
            });
            
            response = await fetch(apiUrl, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(obj)
            });
            
            const json = await response.json();
            hideLoader();
            
            if (response.ok && json.status === 'success') {
                showToast(json.message || 'Operation completed successfully.', 'success');
                
                // Route redirection mappings for Add/Edit forms
                const path = window.location.pathname;
                if (path.includes('/add') || path.includes('/edit') || path.includes('/create') || path.includes('/upload') || path.includes('/sync')) {
                    let redirectUrl = '/admin/dashboard';
                    if (path.includes('/questions')) redirectUrl = '/admin/questions';
                    if (path.includes('/teams')) redirectUrl = '/admin/teams';
                    if (path.includes('/quiz-types')) redirectUrl = '/admin/quiz-types';
                    
                    if (obj.quiz_type_id) {
                        redirectUrl += `?quiz_type_id=${obj.quiz_type_id}`;
                    }
                    navigateTo(redirectUrl);
                } else {
                    reloadPageContent();
                }
            } else {
                showToast(json.message || 'Action failed.', 'error');
            }
        } else {
            // Standard action POST (like file uploads)
            response = await fetch(action, {
                method: 'POST',
                body: formData
            });
            
            const htmlText = await response.text();
            hideLoader();
            
            if (response.ok) {
                const parser = new DOMParser();
                const doc = parser.parseFromString(htmlText, 'text/html');
                
                const toasts = doc.querySelectorAll('#toast-container .toast');
                if (toasts.length > 0) {
                    toasts.forEach(t => {
                        const type = t.className.includes('toast-error') ? 'error' : 'success';
                        showToast(t.textContent.trim(), type);
                    });
                } else {
                    showToast('Data uploaded successfully.', 'success');
                }
                
                const path = window.location.pathname;
                let redirectUrl = window.location.pathname;
                if (path.includes('/questions')) redirectUrl = '/admin/questions';
                if (path.includes('/teams')) redirectUrl = '/admin/teams';
                navigateTo(redirectUrl);
            } else {
                showToast('Upload failed', 'error');
            }
        }
    } catch (e) {
        console.error(e);
        hideLoader();
        showToast('Network error occurred.', 'error');
    }
}

// Side-bar mobile toggle
function toggleSidebar() {
    const sidebar = document.getElementById('sidebar');
    const overlay = document.getElementById('sidebar-overlay');
    if (!sidebar || !overlay) return;
    sidebar.classList.toggle('-translate-x-full');
    overlay.classList.toggle('hidden');
}

// Event Listeners initialization
document.addEventListener('DOMContentLoaded', () => {
    // Intercept inline this.form.submit()
    const originalSubmit = HTMLFormElement.prototype.submit;
    HTMLFormElement.prototype.submit = function() {
        const event = new Event('submit', { bubbles: true, cancelable: true });
        this.dispatchEvent(event);
        if (!event.defaultPrevented) {
            originalSubmit.call(this);
        }
    };
    
    // Theme toggle setup (since header is persistent, this DOMContentLoaded runs once)
    const themeToggleBtn = document.getElementById('theme-toggle');
    if (themeToggleBtn) {
        const themeToggleDarkIcon = document.getElementById('theme-toggle-dark-icon');
        const themeToggleLightIcon = document.getElementById('theme-toggle-light-icon');
        
        if (document.documentElement.classList.contains('dark')) {
            if (themeToggleLightIcon) themeToggleLightIcon.classList.remove('hidden');
        } else {
            if (themeToggleDarkIcon) themeToggleDarkIcon.classList.remove('hidden');
        }
        
        themeToggleBtn.addEventListener('click', () => {
            if (themeToggleDarkIcon) themeToggleDarkIcon.classList.toggle('hidden');
            if (themeToggleLightIcon) themeToggleLightIcon.classList.toggle('hidden');
            
            if (document.documentElement.classList.contains('dark')) {
                document.documentElement.classList.remove('dark');
                localStorage.setItem('color-theme', 'light');
            } else {
                document.documentElement.classList.add('dark');
                localStorage.setItem('color-theme', 'dark');
            }
        });
    }
    
    // Intercept clicks on links
    document.addEventListener('click', (e) => {
        const link = e.target.closest('a');
        if (!link) return;
        
        if (e.button !== 0 || e.metaKey || e.ctrlKey || e.shiftKey || e.altKey) return;
        if (link.hasAttribute('download') || link.getAttribute('target') === '_blank') return;
        
        const href = link.getAttribute('href');
        if (!href) return;
        if (href.startsWith('javascript:') || href.startsWith('#')) return;
        
        const url = new URL(href, window.location.origin);
        if (url.origin === window.location.origin && url.pathname.startsWith('/admin') && !url.pathname.includes('/logout')) {
            e.preventDefault();
            navigateTo(url.pathname + url.search);
        }
    });
    
    // Intercept form submissions
    document.addEventListener('submit', async (e) => {
        const form = e.target.closest('form');
        if (!form) return;
        if (form.hasAttribute('data-no-ajax')) return;
        
        e.preventDefault();
        
        const method = form.method.toUpperCase();
        const action = form.getAttribute('action') || window.location.pathname;
        
        if (method === 'GET') {
            const formData = new FormData(form);
            const params = new URLSearchParams();
            for (const [key, val] of formData.entries()) {
                if (val) params.append(key, val);
            }
            const queryString = params.toString();
            navigateTo(action + (queryString ? '?' + queryString : ''));
        } else {
            await handleFormPost(form, action);
        }
    });
    
    // Intercept browser back/forward buttons
    window.addEventListener('popstate', () => {
        navigateTo(window.location.href, false);
    });
    
    // Fade out initially flashed toasts
    document.querySelectorAll('#toast-container .toast').forEach((toast, index) => {
        setTimeout(() => {
            toast.style.transition = 'opacity 0.3s, transform 0.3s';
            toast.style.opacity = '0';
            toast.style.transform = 'translateX(1rem)';
            setTimeout(() => toast.remove(), 300);
        }, 4000 + index * 500);
    });
});
