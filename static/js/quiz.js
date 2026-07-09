(function () {
    'use strict';

    function initQuizSecurity() {
        if (!document.getElementById('quiz-form')) return;

        const scene = document.querySelector('.quiz-active-scene');
        const preventCopy = scene ? scene.dataset.preventCopy !== '0' : true;

        if (preventCopy) {
            document.addEventListener('contextmenu', (e) => {
                e.preventDefault();
            });

            document.addEventListener('keydown', (e) => {
                if (e.ctrlKey || e.metaKey || e.key === 'F12' || e.key === 'PrintScreen') {
                    e.preventDefault();
                    trackTabSwitch();
                }
            });

            document.addEventListener('dragstart', (e) => e.preventDefault());
        }

        document.addEventListener('visibilitychange', () => {
            if (document.hidden) trackTabSwitch();
        });

        history.pushState(null, null, location.href);
        window.addEventListener('popstate', () => {
            history.go(1);
            trackTabSwitch();
        });
    }

    function trackTabSwitch() {
        fetch('/quiz/track_tab_switch', { method: 'POST', credentials: 'same-origin' })
            .then((r) => r.json())
            .then((data) => {
                if (data.auto_submit) {
                    const form = document.getElementById('quiz-form');
                    if (form) form.submit();
                }
            })
            .catch(() => {});
    }

    function initTimer(remainingSeconds) {
        const display = document.getElementById('quiz-timer');
        const form = document.getElementById('quiz-form');
        if (!display || !form) return;

        let timeLeft = remainingSeconds;

        const tick = () => {
            if (timeLeft <= 0) {
                form.submit();
                return;
            }
            const m = Math.floor(timeLeft / 60);
            const s = timeLeft % 60;
            display.textContent = `${m}:${s < 10 ? '0' : ''}${s}`;
            if (timeLeft <= 60) display.classList.add('warning');
            timeLeft--;
        };

        tick();
        setInterval(tick, 1000);
    }

    function initCountdown(redirectUrl, seconds) {
        const el = document.getElementById('countdown-num');
        if (!el) return;
        let count = seconds;
        el.textContent = count;
        const interval = setInterval(() => {
            count--;
            if (count <= 0) {
                clearInterval(interval);
                window.location.href = redirectUrl;
            } else {
                el.textContent = count;
            }
        }, 1000);
    }

    function initProgressTracking() {
        document.querySelectorAll('.quiz-question-card').forEach((card, index) => {
            const observer = new IntersectionObserver((entries) => {
                entries.forEach((entry) => {
                    if (entry.isIntersecting) {
                        fetch('/quiz/api/progress', {
                            method: 'POST',
                            credentials: 'same-origin',
                            headers: { 'Content-Type': 'application/json' },
                            body: JSON.stringify({ current_question: index + 1 }),
                        }).catch(() => {});
                    }
                });
            }, { threshold: 0.5 });
            observer.observe(card);
        });
    }

    function initQuestionNavigation() {
        const form = document.getElementById('quiz-form');
        if (!form) return;

        const cards = Array.from(document.querySelectorAll('.quiz-question-card'));
        if (!cards.length) return;

        const storagePrefix = `quiz-answers-${location.pathname}`;
        const savedIndex = parseInt(sessionStorage.getItem('quiz-current-question'), 10);
        let currentIndex = Number.isInteger(savedIndex) ? savedIndex : 0;
        currentIndex = Math.min(Math.max(currentIndex, 0), cards.length - 1);

        const nav = document.createElement('div');
        nav.className = 'quiz-navigation';
        nav.innerHTML = `
            <div class="quiz-navigation-status">
                <span id="quiz-nav-progress"></span>
                <span id="quiz-nav-answer-count"></span>
            </div>
            <div class="quiz-navigation-actions">
                <button type="button" id="quiz-prev" class="quiz-btn">Previous</button>
                <button type="button" id="quiz-next" class="quiz-btn quiz-btn-primary">Next</button>
            </div>
        `;

        const submitWrap = document.querySelector('.quiz-submit-wrap');
        if (submitWrap) {
            submitWrap.parentNode.insertBefore(nav, submitWrap);
        } else {
            form.appendChild(nav);
        }

        const prevButton = nav.querySelector('#quiz-prev');
        const nextButton = nav.querySelector('#quiz-next');
        const progressLabel = nav.querySelector('#quiz-nav-progress');
        const answerCountLabel = nav.querySelector('#quiz-nav-answer-count');

        const updateNav = () => {
            cards.forEach((card, index) => {
                card.style.display = index === currentIndex ? 'block' : 'none';
            });
            prevButton.disabled = currentIndex === 0;
            nextButton.textContent = currentIndex === cards.length - 1 ? 'Review & Submit' : 'Next';
            progressLabel.textContent = `Question ${currentIndex + 1} of ${cards.length}`;
            const answered = cards.reduce((count, card) => {
                return count + (card.querySelector('input[type=radio]:checked') ? 1 : 0);
            }, 0);
            answerCountLabel.textContent = `Answered ${answered} of ${cards.length}`;
            sessionStorage.setItem('quiz-current-question', currentIndex);
        };

        const restoreAnswers = () => {
            cards.forEach((card, index) => {
                const savedValue = localStorage.getItem(`${storagePrefix}-${index}`);
                if (!savedValue) return;
                const input = Array.from(card.querySelectorAll('input[type=radio]')).find((radio) => radio.value === savedValue);
                if (input) input.checked = true;
            });
        };

        const attachInputListeners = () => {
            cards.forEach((card, index) => {
                card.querySelectorAll('input[type=radio]').forEach((input) => {
                    input.addEventListener('change', () => {
                        if (input.checked) {
                            localStorage.setItem(`${storagePrefix}-${index}`, input.value);
                            updateNav();
                        }
                    });
                });
            });
        };

        prevButton.addEventListener('click', () => {
            if (currentIndex > 0) {
                currentIndex -= 1;
                updateNav();
            }
        });

        nextButton.addEventListener('click', () => {
            if (currentIndex < cards.length - 1) {
                currentIndex += 1;
                updateNav();
                return;
            }
            const submitEvent = new Event('submit', { cancelable: true });
            if (form.dispatchEvent(submitEvent)) {
                form.submit();
            }
        });

        restoreAnswers();
        attachInputListeners();
        
        form.addEventListener('submit', () => {
            cards.forEach((_, index) => {
                localStorage.removeItem(`${storagePrefix}-${index}`);
            });
            sessionStorage.removeItem('quiz-current-question');
        });

        updateNav();
    }

    function initBubbles() {
        const container = document.getElementById('bubble-container');
        if (!container) return;
        for (let i = 0; i < 8; i++) {
            const b = document.createElement('div');
            b.className = 'quiz-bubble';
            const size = Math.random() * 40 + 20;
            b.style.width = `${size}px`;
            b.style.height = `${size}px`;
            b.style.left = `${Math.random() * 100}%`;
            b.style.animationDuration = `${Math.random() * 8 + 10}s`;
            b.style.animationDelay = `${Math.random() * 5}s`;
            container.appendChild(b);
        }
    }

    document.addEventListener('DOMContentLoaded', () => {
        initQuizSecurity();
        initBubbles();
        initQuestionNavigation();

        const timerEl = document.getElementById('quiz-timer');
        if (timerEl && timerEl.dataset.remaining) {
            initTimer(parseInt(timerEl.dataset.remaining, 10));
            initProgressTracking();
        }

        const countdownEl = document.getElementById('countdown-num');
        if (countdownEl && countdownEl.dataset.redirect) {
            initCountdown(countdownEl.dataset.redirect, parseInt(countdownEl.dataset.seconds || '3', 10));
        }
        initPasswordToggle();
        initLoginNormalization();
    });

    function initPasswordToggle() {
        const passwordInput = document.getElementById('password');
        const toggle = document.getElementById('show-password');
        if (!passwordInput || !toggle) return;

        toggle.addEventListener('change', () => {
            passwordInput.type = toggle.checked ? 'text' : 'password';
        });
    }

    function initLoginNormalization() {
        const form = document.getElementById('quiz-login-form');
        if (!form) return;

        form.addEventListener('submit', () => {
            const lotname = document.getElementById('lotname');
            const entryCode = document.getElementById('entry_code');
            const password = document.getElementById('password');

            if (lotname) {
                lotname.value = lotname.value.replace(/\s+/g, '').toLowerCase();
            }
            if (entryCode) {
                entryCode.value = entryCode.value.replace(/\s+/g, '').toUpperCase();
            }
            if (password) {
                password.value = password.value.replace(/\s+/g, '').toLowerCase();
            }
        });
    }
})();
