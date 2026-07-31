// blog - main.js

// ---- SPA-like page transition (header + footer stay, content fades) ----
(function() {
    var main = document.querySelector('.site-main');

    // Fade content in on initial load
    if (main) {
        main.classList.add('content-visible');
    }

    // Intercept all internal link clicks
    document.addEventListener('click', function(e) {
        var link = e.target.closest('a');
        if (!link) return;

        var href = link.getAttribute('href');
        if (!href || href.startsWith('#') || href.startsWith('javascript:') ||
            href.startsWith('http') || href.startsWith('//') ||
            link.getAttribute('target') === '_blank' ||
            link.getAttribute('download') ||
            link.closest('form') ||
            link.hasAttribute('data-full') ||
            href.endsWith('/logout')) {
            return;
        }

        e.preventDefault();
        navigateTo(href);
    });

    // Handle browser back/forward
    window.addEventListener('popstate', function(e) {
        if (e.state && e.state.url) {
            loadContent(e.state.url, false);
        }
    });

    function navigateTo(url) {
        history.pushState({ url: url }, '', url);
        loadContent(url, true);
    }

    function loadContent(url, addToHistory) {
        var main = document.querySelector('.site-main');
        if (!main) { window.location.href = url; return; }

        // Fade out content
        main.classList.remove('content-visible');

        setTimeout(function() {
            fetch(url, { headers: { 'X-Requested-With': 'XMLHttpRequest' } })
                .then(function(res) {
                    if (!res.ok) throw new Error('Network error');
                    return res.text();
                })
                .then(function(html) {
                    var parser = new DOMParser();
                    var doc = parser.parseFromString(html, 'text/html');

                    // Update title
                    var newTitle = doc.querySelector('title');
                    if (newTitle) document.title = newTitle.textContent;

                    // Replace main content
                    var newMain = doc.querySelector('.site-main');
                    if (newMain) {
                        main.innerHTML = newMain.innerHTML;
                    }

                    // Re-run scripts in the new content
                    var scripts = main.querySelectorAll('script');
                    scripts.forEach(function(s) {
                        var newScript = document.createElement('script');
                        if (s.src) {
                            newScript.src = s.src;
                        } else {
                            newScript.textContent = s.textContent;
                        }
                        s.parentNode.replaceChild(newScript, s);
                    });

                    // Fade in
                    requestAnimationFrame(function() {
                        main.classList.add('content-visible');
                    });

                    // Scroll to top
                    window.scrollTo({ top: 0, behavior: 'instant' });
                })
                .catch(function() {
                    // Fallback: full page navigation
                    window.location.href = url;
                });
        }, 200);
    }
})();

// ---- Confirm form interceptor ----
document.addEventListener('submit', function(e) {
    var form = e.target.closest('.confirm-form');
    if (!form) return;
    e.preventDefault();
    var msg = form.getAttribute('data-confirm') || '确定执行此操作？';
    var icon = form.getAttribute('data-icon') || '⚠️';
    var okText = form.getAttribute('data-ok') || '确认';
    var okClass = form.getAttribute('data-ok-class') || 'btn-danger';
    showConfirm(msg, icon, okText, okClass, function(confirmed) {
        if (confirmed) form.submit();
    });
});

// ---- Confirm modal ----
function showConfirm(message, icon, okText, okClass, callback) {
    document.getElementById('confirmMessage').textContent = message;
    document.getElementById('confirmIcon').textContent = icon || '⚠️';
    var okBtn = document.getElementById('confirmOk');
    okBtn.textContent = okText || '确认';
    okBtn.className = 'btn btn-sm ' + (okClass || 'btn-danger');
    document.getElementById('confirmModal').classList.add('show');
    document.body.style.overflow = 'hidden';

    function cleanup() {
        document.getElementById('confirmModal').classList.remove('show');
        document.body.style.overflow = '';
        document.getElementById('confirmOk').onclick = null;
        document.getElementById('confirmCancel').onclick = null;
        document.getElementById('confirmModal').onclick = null;
    }

    document.getElementById('confirmOk').onclick = function() { cleanup(); if (callback) callback(true); };
    document.getElementById('confirmCancel').onclick = function() { cleanup(); if (callback) callback(false); };
    document.getElementById('confirmModal').onclick = function(e) {
        if (e.target === document.getElementById('confirmModal')) { cleanup(); if (callback) callback(false); }
    };
    document.addEventListener('keydown', function escHandler(e) {
        if (e.key === 'Escape') { cleanup(); if (callback) callback(false); document.removeEventListener('keydown', escHandler); }
    });
}

// ---- Toast notification ----
function showToast(message, type) {
    // Remove existing toast
    var existing = document.querySelector('.toast-notification');
    if (existing) existing.remove();

    var toast = document.createElement('div');
    toast.className = 'toast-notification toast-' + (type || 'success');
    toast.textContent = message;
    document.body.appendChild(toast);

    // Trigger animation
    requestAnimationFrame(function() {
        toast.classList.add('toast-show');
    });

    // Auto dismiss
    setTimeout(function() {
        toast.classList.remove('toast-show');
        setTimeout(function() { toast.remove(); }, 300);
    }, 2000);
}

// ---- Bookmark toggle (event delegation — works with SPA) ----
document.addEventListener('click', function(e) {
    var btn = e.target.closest('.bookmark-btn');
    if (!btn) return;
    e.preventDefault();

    var articleId = btn.getAttribute('data-article-id');
    if (!articleId) return;

    fetch('/bookmarks/toggle/' + articleId, {
        method: 'POST',
        headers: { 'X-Requested-With': 'XMLHttpRequest' }
    })
        .then(function(res) { return res.json(); })
        .then(function(data) {
            if (data.status === 'added') {
                btn.classList.remove('btn-outline');
                btn.classList.add('btn-danger');
                btn.innerHTML = '🔖 已收藏';
                showToast('✅ 收藏成功', 'success');
            } else if (data.status === 'removed') {
                btn.classList.remove('btn-danger');
                btn.classList.add('btn-outline');
                btn.innerHTML = '🔖 收藏';
                showToast('已取消收藏', 'info');
                var box = btn.closest('.Box');
                if (box) {
                    box.style.opacity = '0';
                    box.style.transition = 'opacity 0.3s';
                    setTimeout(function() { box.remove(); }, 300);
                }
            }
        })
        .catch(function(err) { console.error('Bookmark toggle failed:', err); });
});
