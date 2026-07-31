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
            link.closest('form')) {
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

// ---- Bookmark toggle ----
function toggleBookmark(btn) {
    var articleId = btn.dataset.articleId;
    if (!articleId) return;
    fetch('/bookmarks/toggle/' + articleId, { method: 'POST' })
        .then(function(res) { return res.json(); })
        .then(function(data) {
            if (data.status === 'added') {
                btn.classList.remove('btn-outline');
                btn.classList.add('btn-danger');
                btn.innerHTML = '🔖 已收藏';
            } else if (data.status === 'removed') {
                btn.classList.remove('btn-danger');
                btn.classList.add('btn-outline');
                btn.innerHTML = '🔖 收藏';
                var box = btn.closest('.Box');
                if (box) {
                    box.style.opacity = '0';
                    box.style.transition = 'opacity 0.3s';
                    setTimeout(function() { box.remove(); }, 300);
                }
            }
        })
        .catch(function(err) { console.error('Bookmark toggle failed:', err); });
}
