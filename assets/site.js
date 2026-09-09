// Firebase - load on demand (not render-blocking)
        let fbDb = null;
        let firebaseLoading = false;
        function getFirebaseDb() {
            if (fbDb) return fbDb;
            if (typeof firebase !== 'undefined') {
                firebase.initializeApp({
                    apiKey: "AIzaSyAKVA3k7k8neozrd55NwJB-Dugkscbwl0Y",
                    databaseURL: "https://memory-found-404-default-rtdb.firebaseio.com",
                    projectId: "memory-found-404",
                    appId: "1:788154947211:web:01dcbe843386b5d094668e"
                });
                fbDb = firebase.database();
                return fbDb;
            }
            // Load Firebase scripts dynamically if not yet loaded
            if (!firebaseLoading) {
                firebaseLoading = true;
                const s1 = document.createElement('script');
                s1.src = 'https://www.gstatic.com/firebasejs/9.23.0/firebase-app-compat.js';
                s1.onload = function() {
                    const s2 = document.createElement('script');
                    s2.src = 'https://www.gstatic.com/firebasejs/9.23.0/firebase-database-compat.js';
                    s2.onload = function() {
                        firebase.initializeApp({
                            apiKey: "AIzaSyAKVA3k7k8neozrd55NwJB-Dugkscbwl0Y",
                            databaseURL: "https://memory-found-404-default-rtdb.firebaseio.com",
                            projectId: "memory-found-404",
                            appId: "1:788154947211:web:01dcbe843386b5d094668e"
                        });
                        fbDb = firebase.database();
                    };
                    document.head.appendChild(s2);
                };
                document.head.appendChild(s1);
            }
            return null;
        }

        let blogPosts = [];
        const baseUrl = 'https://404memoryfound.com';
        let currentPage = 'home';
        let currentSlug = null;
        let activeTags = [];
        let isMobile = window.innerWidth <= 768;
        let windowStates = {};
        let draggedWindow = null;
        let dragOffset = { x: 0, y: 0 };
        let resizedWindow = null;
        let resizeStart = { x: 0, y: 0, width: 0, height: 0 };
        let resizeDirection = null;

        // Load posts from posts.js (script tag) or fetch posts.json as fallback
        async function loadPosts() {
            let data = null;

            // Generated pages (posts, tags, about...) are fully static: no index needed.
            if (typeof isPostPage !== 'undefined' && isPostPage) {
                blogPosts = [];
                initializeUI();
                return;
            }

            // Homepage: load the lightweight index (title/date/excerpt/tags, no bodies).
            // Post bodies are fetched on demand from /posts/<slug>.json when opened.
            if (window.__POSTS_DATA__ && window.__POSTS_DATA__.posts) {
                data = window.__POSTS_DATA__;
            } else {
                try {
                    const response = await fetch('/posts-index.json?v=' + (window.__BUILD__ || ''));
                    if (!response.ok) throw new Error('HTTP ' + response.status);
                    data = await response.json();
                } catch (error) {
                    console.error('Error loading posts:', error);
                }
            }

            if (data && data.posts) {
                blogPosts = data.posts.map(post => {
                    let content = post.body;
                    while (content && typeof content === 'object' && content.body) {
                        content = content.body;
                    }
                    return {
                        ...post,
                        slug: post.id,
                        excerpt: post.excerpt,
                        content: content || '',
                        tags: post.tags || []
                    };
                });
                // Sort newest first
                blogPosts.sort((a, b) => b.date.localeCompare(a.date));
            } else {
                blogPosts = [];
            }

            initializeUI();
        }

        function initializeUI() {
            if (isMobile) {
                populateMobilePosts();
                populateMobileTagFilters();
                initMobileReadingProgress();
                // Check if arriving on a post URL
                const hash = location.hash;
                if (hash.startsWith('#/post/')) {
                    const slug = hash.substring(7);
                    openPost(slug);
                }
            } else {
                populateBlogPostsList();
                populateArchives();
                populateTagFilters();
                initializeTaskbar();
                initReadingProgress();
                startClock();
                loadVisitorCount();
                showCookieBanner();

                // On post pages (generated by build.py), skip boot delay
                if (typeof isPostPage !== 'undefined' && isPostPage) {
                    // Post window is already visible via inline style
                    // Just make it active and register in taskbar
                    makeActive('post-window');
                } else {
                    // Homepage: Auto-open Blog Posts window after boot animation
                    setTimeout(() => {
                        const hash = location.hash;
                        const windowHash = hash.match(/^#(about|archives|guestbook|contact|privacy|terms|blog)$/);
                        if (hash.startsWith('#/post/')) {
                            const slug = hash.substring(7);
                            openPost(slug);
                        } else if (windowHash) {
                            const name = windowHash[1] === 'contact' ? 'guestbook' : windowHash[1];
                            openWindow(name + '-window');
                        } else {
                            openWindow('blog-window');
                        }
                    }, 3600);
                }
            }
        }

        let mobileActiveTags = [];

        // Lazy-load thumbnail background images via IntersectionObserver
        let thumbObserver = null;
        function initThumbObserver() {
            if (thumbObserver) return;
            if (!('IntersectionObserver' in window)) {
                // Fallback: load all immediately
                document.querySelectorAll('.mobile-post-thumb[data-bg]').forEach(el => {
                    el.style.backgroundImage = "url('" + el.dataset.bg + "')";
                });
                return;
            }
            thumbObserver = new IntersectionObserver(function(entries) {
                entries.forEach(function(entry) {
                    if (entry.isIntersecting) {
                        const el = entry.target;
                        if (el.dataset.bg) {
                            el.style.backgroundImage = "url('" + el.dataset.bg + "')";
                            el.removeAttribute('data-bg');
                        }
                        thumbObserver.unobserve(el);
                    }
                });
            }, { rootMargin: '200px' });
        }

        function observeThumbs() {
            if (!thumbObserver) initThumbObserver();
            if (!thumbObserver) return;
            document.querySelectorAll('[data-bg]').forEach(el => {
                thumbObserver.observe(el);
            });
        }

        function populateMobilePosts() {
            const list = document.getElementById('mobile-post-list');
            if (!list) return;
            const filtered = filterMobilePosts();
            list.innerHTML = filtered.map(post => {
                const imgUrl = post.thumb || post.image || '';
                const dataAttr = imgUrl ? `data-bg="${imgUrl}"` : '';
                return `
                <li class="mobile-post-item">
                    <a href="/posts/${post.slug}.html" onclick="event.preventDefault(); openPost('${post.slug}')">
                    <div class="mobile-post-thumb" ${dataAttr} style="background-color:#c0c0c0;"></div>
                    <div class="mobile-post-info">
                        <h3>${post.title}</h3>
                        <div class="mobile-post-date">${post.date} · ${readingLabel(post)}</div>
                        <div class="mobile-post-excerpt">${post.excerpt}</div>
                        <div class="mobile-post-tags">${(post.tags || []).slice(0, 3).join(' · ')}</div>
                    </div>
                    </a>
                </li>`;
            }).join('');
            // Lazy-load thumbnails
            observeThumbs();
            // Update status bar count
            const countEl = document.getElementById('mobile-post-count');
            if (countEl) countEl.textContent = filtered.length + ' post' + (filtered.length !== 1 ? 's' : '');
        }

        function filterMobilePosts() {
            let filtered = blogPosts;
            const searchTerm = document.getElementById('mobile-search-input')?.value?.toLowerCase() || '';
            if (searchTerm) {
                filtered = filtered.filter(p =>
                    p.title.toLowerCase().includes(searchTerm) ||
                    p.excerpt.toLowerCase().includes(searchTerm) ||
                    (p.tags || []).some(t => t.toLowerCase().includes(searchTerm))
                );
            }
            if (mobileActiveTags.length > 0) {
                filtered = filtered.filter(p =>
                    mobileActiveTags.some(tag => (p.tags || []).includes(tag))
                );
            }
            return filtered;
        }

        function handleMobileSearch() {
            populateMobilePosts();
        }

        function populateMobileTagFilters() {
            const container = document.getElementById('mobile-tag-filters');
            if (!container) return;
            const tagCounts = {};
            blogPosts.forEach(p => (p.tags || []).forEach(t => { tagCounts[t] = (tagCounts[t] || 0) + 1; }));
            const topTags = Object.entries(tagCounts)
                .sort((a, b) => b[1] - a[1])
                .slice(0, 8)
                .map(e => e[0]);
            container.innerHTML = topTags.map(tag => `
                <a class="mobile-tag-btn ${mobileActiveTags.includes(tag) ? 'active' : ''}" href="/tags/${tagSlug(tag)}.html"
                        onclick="event.preventDefault(); toggleMobileTag('${tag}')">${tag}</a>
            `).join('');
        }

        function toggleMobileTag(tag) {
            const idx = mobileActiveTags.indexOf(tag);
            if (idx >= 0) { mobileActiveTags.splice(idx, 1); }
            else { mobileActiveTags.push(tag); }
            populateMobileTagFilters();
            populateMobilePosts();
        }

        // Mobile reading progress
        function initMobileReadingProgress() {
            const content = document.getElementById('mobile-content');
            if (!content) return;
            content.addEventListener('scroll', function() {
                const detail = document.getElementById('mobile-post-detail');
                if (!detail || detail.style.display === 'none') return;
                const fill = document.getElementById('mobile-reading-progress-fill');
                if (!fill) return;
                const scrollTop = content.scrollTop;
                const scrollHeight = content.scrollHeight - content.clientHeight;
                const pct = scrollHeight > 0 ? Math.min(100, Math.round((scrollTop / scrollHeight) * 100)) : 0;
                fill.style.width = pct + '%';
            });
        }

        // Mobile share functions
        function mobileShareTwitter() {
            if (!currentSlug) return;
            const post = blogPosts.find(p => p.slug === currentSlug);
            const url = baseUrl + '/posts/' + currentSlug + '.html';
            window.open('https://twitter.com/intent/tweet?text=' + encodeURIComponent(post.title) + '&url=' + encodeURIComponent(url), '_blank');
        }
        function mobileShareThreads() {
            if (!currentSlug) return;
            const post = blogPosts.find(p => p.slug === currentSlug);
            const url = baseUrl + '/posts/' + currentSlug + '.html';
            window.open('https://www.threads.net/intent/post?text=' + encodeURIComponent(post.title + ' ' + url), '_blank');
        }
        function mobileShareFacebook() {
            if (!currentSlug) return;
            const url = baseUrl + '/posts/' + currentSlug + '.html';
            window.open('https://www.facebook.com/sharer/sharer.php?u=' + encodeURIComponent(url), '_blank');
        }
        function mobileCopyLink() {
            if (!currentSlug) return;
            const url = baseUrl + '/posts/' + currentSlug + '.html';
            navigator.clipboard.writeText(url).then(() => {
                const btn = event.target;
                btn.textContent = 'Copied!';
                setTimeout(() => { btn.textContent = 'Copy Link'; }, 1500);
            });
        }

        function populateBlogPostsList() {
            const list = document.getElementById('blog-posts-list');
            if (!list) return;
            const filtered = filterPosts();
            list.innerHTML = filtered.map(post => {
                const thumbUrl = post.thumb || post.image || '';
                const dataAttr = thumbUrl ? `data-bg="${thumbUrl}"` : '';
                return `
                <li class="blog-post-item">
                    <a href="/posts/${post.slug}.html" onclick="event.preventDefault(); openPost('${post.slug}')">
                        <div class="blog-post-thumb" ${dataAttr} style="background-color:#c0c0c0;"></div>
                        <div class="blog-post-text">
                            <h3>${post.title}</h3>
                            <div class="date">${post.date} <span class="reading-time">${readingLabel(post)}</span></div>
                            <div class="excerpt">${post.excerpt}</div>
                            <div class="tags">${post.tags.join(', ')}</div>
                        </div>
                    </a>
                </li>`;
            }).join('');
            // Lazy-load desktop thumbnails
            observeThumbs();
        }

        function populateArchives() {
            const list = document.getElementById('archives-list');
            if (!list) return;
            // Group posts by month/year
            const monthMap = {};
            const monthNames = ['January','February','March','April','May','June','July','August','September','October','November','December'];

            // Sort posts by date descending (newest first)
            const sorted = [...blogPosts].sort((a, b) => new Date(b.date) - new Date(a.date));

            sorted.forEach(post => {
                const d = new Date(post.date);
                const key = `${d.getFullYear()}-${String(d.getMonth()).padStart(2,'0')}`;
                const label = `${monthNames[d.getMonth()]} ${d.getFullYear()}`;
                if (!monthMap[key]) monthMap[key] = { label, posts: [] };
                monthMap[key].posts.push(post);
            });

            list.innerHTML = Object.keys(monthMap).sort().reverse().map(key => `
                <li class="archive-tag">
                    <div class="archive-tag-name">📅 ${monthMap[key].label}</div>
                    <ul class="archive-posts">
                        ${monthMap[key].posts.map(post => `
                            <li class="archive-post">
                                <a href="/posts/${post.slug}.html" onclick="event.preventDefault(); openPost('${post.slug}')">
                                    <div class="title">${post.title}</div>
                                    <div class="date">${post.date}</div>
                                </a>
                            </li>
                        `).join('')}
                    </ul>
                </li>
            `).join('');
        }

        function populateTagFilters() {
            const container = document.getElementById('tag-filters');
            if (!container) return;
            // Count posts per tag, sort by frequency, cap at 8 filters
            const tagCounts = {};
            blogPosts.forEach(p => (p.tags || []).forEach(t => { tagCounts[t] = (tagCounts[t] || 0) + 1; }));
            const topTags = Object.entries(tagCounts)
                .sort((a, b) => b[1] - a[1])
                .slice(0, 8)
                .map(e => e[0]);
            container.innerHTML = topTags.map(tag => `
                <a class="tag-button ${activeTags.includes(tag) ? 'active' : ''}" href="/tags/${tagSlug(tag)}.html"
                        onclick="event.preventDefault(); toggleTag('${tag}')">${tag}</a>
            `).join('');
        }

        function filterPosts() {
            let filtered = blogPosts;
            const searchTerm = document.getElementById('search-input')?.value?.toLowerCase() || '';
            if (searchTerm) {
                filtered = filtered.filter(p =>
                    p.title.toLowerCase().includes(searchTerm) ||
                    p.excerpt.toLowerCase().includes(searchTerm)
                );
            }
            if (activeTags.length > 0) {
                filtered = filtered.filter(p =>
                    activeTags.some(tag => p.tags.includes(tag))
                );
            }
            return filtered;
        }

        function handleSearch() {
            populateBlogPostsList();
        }

        function toggleTag(tag) {
            const idx = activeTags.indexOf(tag);
            if (idx >= 0) {
                activeTags.splice(idx, 1);
            } else {
                activeTags.push(tag);
            }
            populateTagFilters();
            populateBlogPostsList();
        }

        function openPost(slug) {
            const post = blogPosts.find(p => p.slug === slug);
            if (!post) return;

            if (!post.content) {
                fetch('/posts/' + slug + '.json?v=' + (window.__BUILD__ || ''))
                    .then(r => { if (!r.ok) throw new Error('HTTP ' + r.status); return r.json(); })
                    .then(d => { post.content = d.body || ''; openPost(slug); })
                    .catch(err => console.error('Could not load post', slug, err));
                return;
            }

            currentSlug = slug;

            // Calculate related posts
            const related = blogPosts
                .filter(p => p.slug !== slug && p.tags.some(t => post.tags.includes(t)))
                .sort((a, b) => {
                    const aMatch = a.tags.filter(t => post.tags.includes(t)).length;
                    const bMatch = b.tags.filter(t => post.tags.includes(t)).length;
                    return bMatch - aMatch;
                })
                .slice(0, 3);

            if (isMobile) {
                // Mobile: show post detail view
                document.getElementById('mobile-post-list').style.display = 'none';
                // Hide toolbar, update title bar
                const toolbar = document.getElementById('mobile-toolbar');
                if (toolbar) toolbar.style.display = 'none';
                const headerTitle = document.getElementById('mobile-header-title');
                if (headerTitle) headerTitle.textContent = '📖 ' + post.title;

                const detail = document.getElementById('mobile-post-detail');
                detail.style.display = 'block';
                document.getElementById('mobile-post-title').textContent = post.title;
                document.getElementById('mobile-post-detail-date').textContent = post.date + (post.authorName ? ' · by ' + post.authorName : '') + ' · ' + readingLabel(post);
                document.getElementById('mobile-post-detail-body').innerHTML = post.content;
                // Reset reading progress
                const mFill = document.getElementById('mobile-reading-progress-fill');
                if (mFill) mFill.style.width = '0%';
                // Add lazy loading to dynamically inserted images
                document.querySelectorAll('#mobile-post-detail-body img').forEach(img => {
                    if (!img.hasAttribute('loading')) { img.loading = 'lazy'; img.decoding = 'async'; }
                });

                const mobileRelated = document.getElementById('mobile-related-posts');
                if (related.length > 0) {
                    mobileRelated.innerHTML = '<div class="mobile-related-title">📂 Related Posts</div>' +
                        related.map(r => `<a class="mobile-related-item" href="/posts/${r.slug}.html" onclick="event.preventDefault(); openPost('${r.slug}')">${r.title}</a>`).join('');
                } else {
                    mobileRelated.innerHTML = '';
                }

                // Scroll to top of content
                document.querySelector('.mobile-content').scrollTop = 0;
            } else {
                // Desktop: open in post window
                document.getElementById('post-title').textContent = post.title;
                document.getElementById('post-window-title').textContent = post.title;
                document.getElementById('post-date').textContent = post.date;
                const authorEl = document.getElementById('post-author');
                if (authorEl) authorEl.textContent = post.authorName || '404 Memory Found';
                document.getElementById('post-reading-time').textContent = readingLabel(post);
                // Reset progress bar
                const fill = document.getElementById('reading-progress-fill');
                const label = document.getElementById('reading-progress-label');
                if (fill) fill.style.width = '0%';
                if (label) label.textContent = '0%';
                document.getElementById('post-body').innerHTML = post.content;
                // Add lazy loading to dynamically inserted images
                document.querySelectorAll('#post-body img').forEach(img => {
                    if (!img.hasAttribute('loading')) { img.loading = 'lazy'; img.decoding = 'async'; }
                });

                const relatedContainer = document.getElementById('related-posts-container');
                if (relatedContainer) {
                    relatedContainer.innerHTML = related.length > 0
                        ? related.map(r => `<a class="related-post" href="/posts/${r.slug}.html" onclick="event.preventDefault(); openPost('${r.slug}')">${r.title}</a>`).join('')
                        : '<div style="color:#666;font-style:italic;">No related posts yet.</div>';
                }

                openWindow('post-window');
                makeActive('post-window');

                // Scroll post window content to top
                const postContent = document.querySelector('#post-window .window-content');
                if (postContent) postContent.scrollTop = 0;
            }

            updatePageMeta('post', slug);
            location.hash = `/post/${slug}`;
        }

        function closeMobilePost() {
            document.getElementById('mobile-post-detail').style.display = 'none';
            document.getElementById('mobile-post-list').style.display = '';
            // Restore toolbar and title bar
            const toolbar = document.getElementById('mobile-toolbar');
            if (toolbar) toolbar.style.display = '';
            const headerTitle = document.getElementById('mobile-header-title');
            if (headerTitle) headerTitle.textContent = '404 Memory Found';
            location.hash = '';
            updatePageMeta('home');
            document.querySelector('.mobile-content').scrollTop = 0;
        }

        function updatePageMeta(page = 'home', slug = null) {
            const baseTitle = '404 Memory Found';
            const baseDescription = 'A nostalgia blog sharing bizarre stories and curious facts from the 90s and 2000s era.';

            if (page === 'post' && slug) {
                const post = blogPosts.find(p => p.slug === slug);
                if (post) {
                    document.title = `${post.title} | ${baseTitle}`;
                    document.querySelector('meta[name="description"]').content = post.excerpt;
                    document.querySelector('meta[property="og:title"]').content = post.title;
                    document.querySelector('meta[property="og:description"]').content = post.excerpt;
                    document.querySelector('meta[property="og:type"]').content = 'article';
                    document.querySelector('meta[property="og:url"]').content = `${baseUrl}/posts/${slug}.html`;

                    const schema = {
                        "@context": "https://schema.org",
                        "@type": "BlogPosting",
                        "headline": post.title,
                        "description": post.excerpt,
                        "datePublished": post.date,
                        "author": {
                            "@type": "Organization",
                            "name": "404 Memory Found"
                        }
                    };
                    document.getElementById('schema-markup').textContent = JSON.stringify(schema);
                }
            } else {
                // Reset to home defaults
                document.title = baseTitle;
                document.querySelector('meta[name="description"]').content = baseDescription;
                document.querySelector('meta[property="og:title"]').content = baseTitle;
                document.querySelector('meta[property="og:description"]').content = baseDescription;
                document.querySelector('meta[property="og:type"]').content = 'website';
                document.querySelector('meta[property="og:url"]').content = baseUrl;
            }
        }

        function readingLabel(post) {
            return post.readingTime || getReadingTime(post.content || '');
        }

        function tagSlug(tag) {
            return tag.toLowerCase().replace(/&/g, ' ').replace(/[^a-z0-9]+/g, '-').replace(/^-+|-+$/g, '');
        }

        function getReadingTime(htmlContent) {
            const text = htmlContent.replace(/<[^>]*>/g, ' ').replace(/\s+/g, ' ').trim();
            const words = text.split(' ').filter(w => w.length > 0).length;
            const minutes = Math.max(1, Math.round(words / 230));
            return minutes + ' min read';
        }

        function initReadingProgress() {
            const postContent = document.querySelector('#post-window .window-content');
            if (!postContent) return;
            postContent.addEventListener('scroll', function() {
                const scrollTop = postContent.scrollTop;
                const scrollHeight = postContent.scrollHeight - postContent.clientHeight;
                if (scrollHeight <= 0) return;
                const pct = Math.min(100, Math.round((scrollTop / scrollHeight) * 100));
                const fill = document.getElementById('reading-progress-fill');
                const label = document.getElementById('reading-progress-label');
                if (fill) fill.style.width = pct + '%';
                if (label) label.textContent = pct + '%';
            });
        }

        function goHome() {
            currentSlug = null;
            if (isMobile) {
                closeMobilePost();
                return;
            }
            updatePageMeta('home');
            location.hash = '/';
        }

        function copyPostLink() {
            if (currentSlug) {
                const url = `${baseUrl}/#/post/${currentSlug}`;
                navigator.clipboard.writeText(url).then(() => {
                    var btn = document.querySelector('.share-buttons .share-button');
                    if (btn) {
                        var orig = btn.textContent;
                        btn.textContent = 'Copied!';
                        btn.classList.add('copied');
                        setTimeout(function() {
                            btn.textContent = orig;
                            btn.classList.remove('copied');
                        }, 2000);
                    }
                });
            }
        }

        function shareOnTwitter() {
            if (currentSlug) {
                const post = blogPosts.find(p => p.slug === currentSlug);
                const url = `${baseUrl}/#/post/${currentSlug}`;
                window.open(`https://twitter.com/intent/tweet?text=${encodeURIComponent(post.title)}&url=${encodeURIComponent(url)}`, '_blank');
            }
        }

        function shareOnFacebook() {
            if (currentSlug) {
                const url = `${baseUrl}/#/post/${currentSlug}`;
                window.open(`https://www.facebook.com/sharer/sharer.php?u=${encodeURIComponent(url)}`, '_blank');
            }
        }

        function shareOnThreads() {
            if (currentSlug) {
                const post = blogPosts.find(p => p.slug === currentSlug);
                const url = `${baseUrl}/#/post/${currentSlug}`;
                const text = post.title + ' ' + url;
                window.open(`https://www.threads.net/intent/post?text=${encodeURIComponent(text)}`, '_blank');
            }
        }

        function initializeTaskbar() {
            populateTagFilters();
            updateTaskbar();
        }

        function updateTaskbar() {
            const container = document.getElementById('taskbar-buttons');
            const windows = ['blog-window', 'about-window', 'archives-window', 'guestbook-window', 'post-window'];
            const titles = {
                'blog-window': '📝 Blog Posts',
                'about-window': 'ℹ️ About',
                'archives-window': '📚 Archives',
                'guestbook-window': '✍️ Guestbook',
                'post-window': '📖 Post'
            };

            container.innerHTML = windows.map(id => {
                const el = document.getElementById(id);
                if (!el) return '';
                const isMinimized = el.classList.contains('minimized');
                const isActive = el.classList.contains('active');
                const isOpen = !isMinimized || el.dataset.wasOpen;
                const title = titles[id];
                // Show taskbar button for any window that has been opened
                if (isMinimized && !el.dataset.wasOpen) return '';
                return `
                    <button class="taskbar-button ${isActive && !isMinimized ? 'active' : ''}"
                            onclick="toggleWindowTaskbar('${id}')">${title}</button>
                `;
            }).join('');
        }

        function toggleWindowTaskbar(id) {
            const el = document.getElementById(id);
            if (!el) return;

            if (el.classList.contains('minimized')) {
                el.classList.remove('minimized');
                el.style.display = 'flex';
                makeActive(id);
            } else {
                el.classList.add('minimized');
                el.style.display = 'none';
            }
            updateTaskbar();
        }

        function openWindow(id) {
            const el = document.getElementById(id);
            if (!el) {
                // Generated pages only carry the post window: open the rest on the homepage
                if (typeof isPostPage !== 'undefined' && isPostPage) {
                    location.href = '/#' + id.replace('-window', '');
                }
                return;
            }
            el.classList.remove('minimized');
            el.style.display = 'flex';
            el.dataset.wasOpen = 'true';
            makeActive(id);
            updateTaskbar();
        }

        function closeWindow(id) {
            const el = document.getElementById(id);
            if (!el) return;
            el.classList.add('minimized');
            el.classList.remove('active');
            el.style.display = 'none';
            delete el.dataset.wasOpen;
            // Reset maximize state on close
            if (windowStates[id]) {
                const state = windowStates[id];
                el.style.left = state.left;
                el.style.top = state.top;
                el.style.width = state.width;
                el.style.height = state.height;
                windowStates[id] = null;
                const maxBtn = el.querySelector('.btn-restore');
                if (maxBtn) maxBtn.className = 'btn-maximize';
            }
            updateTaskbar();
        }

        function minimizeWindow(id) {
            const el = document.getElementById(id);
            if (!el) return;
            el.classList.add('minimized');
            el.style.display = 'none';
            updateTaskbar();
        }

        function makeActive(id) {
            document.querySelectorAll('.window').forEach(w => w.classList.remove('active'));
            const el = document.getElementById(id);
            if (el) el.classList.add('active');
            updateTaskbar();
        }

        function toggleMaximizeWindow(id) {
            const el = document.getElementById(id);
            if (!el) return;
            const maxBtn = el.querySelector('.btn-maximize, .btn-restore');

            if (!windowStates[id]) {
                // Save current computed dimensions (works even without inline styles)
                const computed = window.getComputedStyle(el);
                windowStates[id] = {
                    left: el.style.left || computed.left,
                    top: el.style.top || computed.top,
                    width: el.style.width || computed.width,
                    height: el.style.height || computed.height
                };
                const desktopArea = document.querySelector('.desktop-area');
                el.style.left = '0';
                el.style.top = '0';
                el.style.width = desktopArea.offsetWidth + 'px';
                el.style.height = desktopArea.offsetHeight + 'px';
                if (maxBtn) { maxBtn.className = 'btn-restore'; }
            } else {
                const state = windowStates[id];
                el.style.left = state.left;
                el.style.top = state.top;
                el.style.width = state.width;
                el.style.height = state.height;
                windowStates[id] = null;
                if (maxBtn) { maxBtn.className = 'btn-maximize'; }
            }
        }

        // Window dragging
        document.addEventListener('mousedown', (e) => {
            const titleBar = e.target.closest('.title-bar');
            const isButton = e.target.closest('.window-button');
            if (!isMobile && titleBar && !isButton) {
                const win = titleBar.closest('.window');
                if (win) {
                    draggedWindow = win;
                    dragOffset.x = e.clientX - win.offsetLeft;
                    dragOffset.y = e.clientY - win.offsetTop;
                    makeActive(win.id);
                    e.preventDefault();
                }
            } else if (!isMobile && e.target.classList.contains('resize-handle')) {
                const win = e.target.closest('.window');
                if (win) {
                    resizedWindow = win;
                    resizeStart = {
                        x: e.clientX,
                        y: e.clientY,
                        width: win.offsetWidth,
                        height: win.offsetHeight,
                        left: win.offsetLeft,
                        top: win.offsetTop
                    };
                    resizeDirection = e.target.className.match(/resize-handle-(\w+)/)[1];
                    e.preventDefault();
                }
            }
        });

        document.addEventListener('mousemove', (e) => {
            if (draggedWindow) {
                draggedWindow.style.left = (e.clientX - dragOffset.x) + 'px';
                draggedWindow.style.top = (e.clientY - dragOffset.y) + 'px';
            } else if (resizedWindow) {
                const deltaX = e.clientX - resizeStart.x;
                const deltaY = e.clientY - resizeStart.y;
                const minWidth = 300;
                const minHeight = 150;

                if (resizeDirection.includes('e')) {
                    resizedWindow.style.width = Math.max(minWidth, resizeStart.width + deltaX) + 'px';
                }
                if (resizeDirection.includes('s')) {
                    resizedWindow.style.height = Math.max(minHeight, resizeStart.height + deltaY) + 'px';
                }
                if (resizeDirection.includes('w')) {
                    const newWidth = Math.max(minWidth, resizeStart.width - deltaX);
                    resizedWindow.style.width = newWidth + 'px';
                    resizedWindow.style.left = (resizeStart.left + resizeStart.width - newWidth) + 'px';
                }
                if (resizeDirection.includes('n')) {
                    const newHeight = Math.max(minHeight, resizeStart.height - deltaY);
                    resizedWindow.style.height = newHeight + 'px';
                    resizedWindow.style.top = (resizeStart.top + resizeStart.height - newHeight) + 'px';
                }
            }
        });

        document.addEventListener('mouseup', () => {
            draggedWindow = null;
            resizedWindow = null;
            resizeDirection = null;
        });

        function startClock() {
            function updateClock() {
                const now = new Date();
                const hours = String(now.getHours()).padStart(2, '0');
                const minutes = String(now.getMinutes()).padStart(2, '0');
                const el = document.getElementById('clock-time');
                if (el) el.textContent = `${hours}:${minutes}`;
            }
            updateClock();
            setInterval(updateClock, 60000);
        }

        function handleSubscribe() {
            var emailInput = document.getElementById('subscribe-email');
            var msgEl = document.getElementById('subscribe-msg');
            var email = (emailInput.value || '').trim().toLowerCase();

            if (!email || !email.includes('@') || !email.includes('.') || email.length < 5) {
                msgEl.style.display = 'block';
                msgEl.style.color = '#cc0000';
                msgEl.textContent = 'Please enter a valid email address.';
                return;
            }

            // Disable button while submitting
            var btn = emailInput.parentElement.querySelector('button');
            btn.disabled = true;
            btn.textContent = 'Sending...';

            var entry = { email: email, date: Date.now(), source: 'About Window' };
            var db = getFirebaseDb(); if (!db) { msgEl.style.display='block'; msgEl.textContent='Loading, please try again...'; btn.disabled=false; return; }
            db.ref('subscribers').push(entry, function(err) {
                if (err) {
                    msgEl.style.display = 'block';
                    msgEl.style.color = '#cc0000';
                    msgEl.textContent = 'Something went wrong. Please try again.';
                    btn.disabled = false;
                    btn.textContent = 'Subscribe';
                } else {
                    msgEl.style.display = 'block';
                    msgEl.style.color = '#008000';
                    msgEl.textContent = 'You\'re subscribed! Welcome aboard.';
                    emailInput.value = '';
                    btn.textContent = 'Subscribed!';
                }
            });
        }

        function loadVisitorCount() {
            var el = document.getElementById('visitor-count');
            if (!el) return;
            // Public hit counter (no keys, no Firebase). Counts one visit per browser session:
            // the first page of a session calls /hit (increment), later pages call /get (read).
            var base = 'https://abacus.jasoncameron.dev';
            var counted = null;
            try { counted = sessionStorage.getItem('404mf_counted'); } catch(e) {}
            var url = base + (counted ? '/get' : '/hit') + '/404memoryfound/visits';
            if (counted) el.textContent = 'Visitor #' + parseInt(counted, 10).toLocaleString();
            fetch(url, { cache: 'no-store' })
                .then(function(r) { return r.ok ? r.json() : null; })
                .then(function(data) {
                    if (!data || typeof data.value !== 'number') return;
                    el.textContent = 'Visitor #' + data.value.toLocaleString();
                    if (!counted) { try { sessionStorage.setItem('404mf_counted', data.value); } catch(e) {} }
                })
                .catch(function() { if (!counted) el.textContent = ''; });
        }

        function showCookieBanner() {
            const banner = document.getElementById('cookie-banner');
            if (!banner) return;
            const hasConsent = localStorage.getItem('cookie-consent');
            if (!hasConsent) {
                banner.classList.add('show');
            }
        }

        function acceptCookies() {
            localStorage.setItem('cookie-consent', 'accepted');
            document.getElementById('cookie-banner').classList.remove('show');
        }

        function declineCookies() {
            localStorage.setItem('cookie-consent', 'declined');
            document.getElementById('cookie-banner').classList.remove('show');
        }

        // Initialize on load
        window.addEventListener('load', () => {
            observeThumbs();
            loadPosts();
            // Boot animation: skip on post pages, play on homepage
            const bootEl = document.getElementById('boot-animation');
            if (bootEl) {
                if (typeof isPostPage !== 'undefined' && isPostPage) {
                    bootEl.classList.add('hidden');
                    setTimeout(() => { bootEl.style.display = 'none'; }, 50);
                } else {
                    // Sequenced terminal boot animation
                    const lines = ['boot-l1','boot-l2','boot-l3','boot-l4','boot-l5'];
                    let delay = 200;
                    lines.forEach((id, i) => {
                        setTimeout(() => {
                            const el = document.getElementById(id);
                            if (el) el.classList.add('visible');
                        }, delay);
                        delay += 350;
                    });
                    // Show 404 title
                    setTimeout(() => {
                        const el = document.getElementById('boot-404');
                        if (el) el.classList.add('visible');
                    }, delay);
                    delay += 300;
                    // Show "memory found"
                    setTimeout(() => {
                        const el = document.getElementById('boot-found');
                        if (el) el.classList.add('visible');
                    }, delay);
                    delay += 200;
                    // Show progress bar and fill it
                    setTimeout(() => {
                        const bar = document.getElementById('boot-bar');
                        if (bar) bar.classList.add('visible');
                        setTimeout(() => {
                            const fill = document.getElementById('boot-fill');
                            if (fill) fill.style.width = '100%';
                        }, 50);
                    }, delay);
                    delay += 300;
                    // Show enter text
                    setTimeout(() => {
                        const el = document.getElementById('boot-enter');
                        if (el) el.classList.add('visible');
                    }, delay);
                    // Fade out and hide, then show tutorial if first visit
                    delay += 800;
                    setTimeout(() => {
                        bootEl.classList.add('hidden');
                        setTimeout(() => {
                            bootEl.style.display = 'none';
                            showTutorialIfFirstVisit();
                        }, 500);
                    }, delay);
                }
            }
        });

        // First-time visitor tutorial
        function showTutorialIfFirstVisit() {
            try {
                if (localStorage.getItem('404mf_visited')) return;
                const tut = document.getElementById('tutorial-overlay');
                if (tut) tut.style.display = 'flex';
            } catch(e) {}
        }
        function dismissTutorial() {
            const tut = document.getElementById('tutorial-overlay');
            if (tut) tut.style.display = 'none';
            try { localStorage.setItem('404mf_visited', '1'); } catch(e) {}
        }

        // Handle hash-based routing
        window.addEventListener('hashchange', () => {
            const hash = location.hash;
            if (hash.startsWith('#/post/')) {
                const slug = hash.substring(7);
                openPost(slug);
            } else {
                goHome();
            }
        });

        // Windows-style click-and-drag selection rectangle
        (function() {
            const desktopArea = document.getElementById('desktop-area');
            const selRect = document.getElementById('selection-rect');
            if (!desktopArea || !selRect) return;

            let isDragging = false;
            let startX = 0, startY = 0;

            desktopArea.addEventListener('mousedown', function(e) {
                // Only start selection on left-click directly on the desktop area (not on icons or windows)
                if (e.button !== 0) return;
                const target = e.target;
                if (target.closest('.desktop-icon') || target.closest('.window')) return;

                isDragging = true;
                const rect = desktopArea.getBoundingClientRect();
                startX = e.clientX - rect.left;
                startY = e.clientY - rect.top;

                selRect.style.left = startX + 'px';
                selRect.style.top = startY + 'px';
                selRect.style.width = '0px';
                selRect.style.height = '0px';
                selRect.style.display = 'block';

                // Clear previous selections
                document.querySelectorAll('.desktop-icon.selected').forEach(i => i.classList.remove('selected'));

                e.preventDefault();
            });

            document.addEventListener('mousemove', function(e) {
                if (!isDragging) return;
                const rect = desktopArea.getBoundingClientRect();
                const currentX = e.clientX - rect.left;
                const currentY = e.clientY - rect.top;

                const x = Math.min(startX, currentX);
                const y = Math.min(startY, currentY);
                const w = Math.abs(currentX - startX);
                const h = Math.abs(currentY - startY);

                selRect.style.left = x + 'px';
                selRect.style.top = y + 'px';
                selRect.style.width = w + 'px';
                selRect.style.height = h + 'px';

                // Check which icons intersect with the selection rectangle
                const selBox = { left: x, top: y, right: x + w, bottom: y + h };
                document.querySelectorAll('.desktop-icon').forEach(function(icon) {
                    const iconRect = icon.getBoundingClientRect();
                    const iconBox = {
                        left: iconRect.left - rect.left,
                        top: iconRect.top - rect.top,
                        right: iconRect.right - rect.left,
                        bottom: iconRect.bottom - rect.top
                    };
                    const intersects = !(selBox.right < iconBox.left || selBox.left > iconBox.right ||
                                        selBox.bottom < iconBox.top || selBox.top > iconBox.bottom);
                    if (intersects) {
                        icon.classList.add('selected');
                    } else {
                        icon.classList.remove('selected');
                    }
                });
            });

            document.addEventListener('mouseup', function(e) {
                if (!isDragging) return;
                isDragging = false;
                selRect.style.display = 'none';
            });

            // Click on empty desktop clears selection
            desktopArea.addEventListener('click', function(e) {
                if (e.target === desktopArea || e.target === desktopArea.querySelector('.selection-rect')) {
                    document.querySelectorAll('.desktop-icon.selected').forEach(i => i.classList.remove('selected'));
                }
            });

            // Enter key opens all selected icons
            document.addEventListener('keydown', function(e) {
                if (e.key === 'Enter') {
                    const selected = document.querySelectorAll('.desktop-icon.selected');
                    if (selected.length > 0) {
                        selected.forEach(function(icon) {
                            // Trigger the double-click action
                            const dblHandler = icon.getAttribute('ondblclick');
                            if (dblHandler) {
                                eval(dblHandler);
                            }
                        });
                        // Clear selection after opening
                        selected.forEach(i => i.classList.remove('selected'));
                        e.preventDefault();
                    }
                }
            });
        })();

        // Start Menu
        function toggleStartMenu() {
            const menu = document.getElementById('start-menu');
            menu.classList.toggle('open');
        }
        document.addEventListener('click', (e) => {
            const menu = document.getElementById('start-menu');
            if (menu && menu.classList.contains('open') && !e.target.closest('.start-menu') && !e.target.closest('.start-button')) {
                menu.classList.remove('open');
            }
        });

        // ====== LEADERBOARD SYSTEM ======
        function getLeaderboard(game) {
            try {
                return JSON.parse(localStorage.getItem('lb_' + game) || '[]');
            } catch(e) { return []; }
        }
        function saveLeaderboard(game, board) {
            try { localStorage.setItem('lb_' + game, JSON.stringify(board)); } catch(e) {}
        }
        function addScore(game, name, score) {
            const board = getLeaderboard(game);
            board.push({ name: name.substring(0, 12) || 'Anonymous', score: score, date: Date.now() });
            board.sort((a, b) => b.score - a.score);
            const top10 = board.slice(0, 10);
            saveLeaderboard(game, top10);
            return top10;
        }
        function renderLeaderboard(containerId, board, highlightScore) {
            const el = document.getElementById(containerId);
            if (!el) return;
            if (board.length === 0) {
                el.innerHTML = '<div class="lb-title">~ LEADERBOARD ~</div><div style="color:#666;font-size:11px;text-align:center;">No scores yet</div>';
                return;
            }
            let html = '<div class="lb-title">~ LEADERBOARD ~</div>';
            let highlighted = false;
            board.forEach((entry, i) => {
                const isYou = !highlighted && entry.score === highlightScore;
                if (isYou) highlighted = true;
                html += '<div class="lb-row' + (isYou ? ' you' : '') + '">' +
                    '<span class="lb-rank">' + (i + 1) + '.</span>' +
                    '<span class="lb-name">' + entry.name + '</span>' +
                    '<span class="lb-score">' + entry.score + '</span></div>';
            });
            el.innerHTML = html;
        }

        // Snake leaderboard helpers (Firebase global leaderboard)
        let lastSnakeScore = 0;
        function fetchSnakeLeaderboard(callback) {
            var db = getFirebaseDb(); if (!db) { callback([]); return; }
            db.ref('leaderboard/snake').orderByChild('score').limitToLast(10).once('value', function(snap) {
                const board = [];
                snap.forEach(function(child) { board.push(child.val()); });
                board.sort(function(a, b) { return b.score - a.score; });
                callback(board);
            }, function(err) {
                console.warn('Firebase read failed:', err);
                callback([]);
            });
        }
        function addSnakeScore(name, score, callback) {
            const entry = { name: name.substring(0, 12) || 'Anonymous', score: score, date: Date.now() };
            var db = getFirebaseDb(); if (!db) { callback([]); return; }
            db.ref('leaderboard/snake').push(entry, function(err) {
                if (err) { console.warn('Firebase write failed:', err); callback([]); return; }
                // After writing, fetch fresh top 10
                fetchSnakeLeaderboard(callback);
            });
        }
        function showSnakeOverlay(score) {
            lastSnakeScore = score;
            document.getElementById('snake-final-score').textContent = 'Score: ' + score;
            document.getElementById('snake-gameover').style.display = 'flex';
            const savedName = localStorage.getItem('lb_player_name') || '';
            document.getElementById('snake-name-input').value = savedName;
            fetchSnakeLeaderboard(function(board) {
                renderLeaderboard('snake-leaderboard', board, -1);
            });
            setTimeout(() => document.getElementById('snake-name-input').focus(), 50);
        }
        function hideSnakeOverlay() {
            const el = document.getElementById('snake-gameover');
            if (el) el.style.display = 'none';
        }
        function submitSnakeScore() {
            const name = document.getElementById('snake-name-input').value.trim() || 'Anonymous';
            localStorage.setItem('lb_player_name', name);
            document.getElementById('snake-name-input').disabled = true;
            document.querySelector('#snake-gameover button').style.display = 'none';
            addSnakeScore(name, lastSnakeScore, function(board) {
                renderLeaderboard('snake-leaderboard', board, lastSnakeScore);
            });
        }
        function restartSnake() {
            hideSnakeOverlay();
            document.getElementById('snake-name-input').disabled = false;
            document.querySelector('#snake-gameover button').style.display = '';
            startSnakeGame();
        }

        // Pong leaderboard helpers
        let lastPongScore = 0;
        let lastPongDifficulty = 'medium';
        function showPongOverlay(playerScore, cpuScore, won) {
            // Pong score = player points scored, weighted by difficulty
            const diffMultiplier = { easy: 1, medium: 2, hard: 3 };
            lastPongScore = playerScore * (diffMultiplier[lastPongDifficulty] || 1);
            document.getElementById('pong-result-title').textContent = won ? 'YOU WIN!' : 'YOU LOSE';
            document.getElementById('pong-result-title').style.color = won ? '#0f0' : '#f44';
            document.getElementById('pong-final-score').textContent = playerScore + ' - ' + cpuScore + ' (' + lastPongDifficulty + ')';
            document.getElementById('pong-gameover').style.display = 'flex';
            const savedName = localStorage.getItem('lb_player_name') || '';
            document.getElementById('pong-name-input').value = savedName;
            renderLeaderboard('pong-leaderboard', getLeaderboard('pong'), -1);
            if (won) {
                setTimeout(() => document.getElementById('pong-name-input').focus(), 50);
            } else {
                // Lost - hide save button, only show play again
                document.querySelector('#pong-gameover input').style.display = 'none';
                document.querySelector('#pong-gameover button:first-child').style.display = 'none';
            }
        }
        function hidePongOverlay() {
            const el = document.getElementById('pong-gameover');
            if (!el) return;
            el.style.display = 'none';
            const inp = el.querySelector('input');
            if (inp) { inp.style.display = ''; inp.disabled = false; }
            const btn = el.querySelector('button');
            if (btn) btn.style.display = '';
        }
        function submitPongScore() {
            const name = document.getElementById('pong-name-input').value.trim() || 'Anonymous';
            localStorage.setItem('lb_player_name', name);
            const board = addScore('pong', name, lastPongScore);
            renderLeaderboard('pong-leaderboard', board, lastPongScore);
            document.getElementById('pong-name-input').disabled = true;
            document.querySelector('#pong-gameover button:first-child').style.display = 'none';
        }

        // ====== SNAKE GAME ======
        let snakeInterval = null;
        function startSnakeGame() {
            const canvas = document.getElementById('snake-canvas');
            if (!canvas) return;
            const ctx = canvas.getContext('2d');
            const grid = 15;
            const cols = canvas.width / grid;
            const rows = canvas.height / grid;
            let snake = [{x: 5, y: 5}];
            let dir = {x: 1, y: 0};
            let nextDir = {x: 1, y: 0};
            let food = spawnFood();
            let score = 0;
            let running = true;

            function spawnFood() {
                let f;
                do {
                    f = {x: Math.floor(Math.random() * cols), y: Math.floor(Math.random() * rows)};
                } while (snake.some(s => s.x === f.x && s.y === f.y));
                return f;
            }

            function tick() {
                if (!running) return;
                dir = nextDir;
                const head = {x: snake[0].x + dir.x, y: snake[0].y + dir.y};
                if (head.x < 0 || head.x >= cols || head.y < 0 || head.y >= rows || snake.some(s => s.x === head.x && s.y === head.y)) {
                    running = false;
                    showSnakeOverlay(score);
                    return;
                }
                snake.unshift(head);
                if (head.x === food.x && head.y === food.y) {
                    score++;
                    document.getElementById('snake-score').textContent = 'Score: ' + score;
                    food = spawnFood();
                } else {
                    snake.pop();
                }
                // Draw
                ctx.fillStyle = '#111';
                ctx.fillRect(0, 0, canvas.width, canvas.height);
                ctx.fillStyle = '#f00';
                ctx.fillRect(food.x * grid + 1, food.y * grid + 1, grid - 2, grid - 2);
                snake.forEach((s, i) => {
                    ctx.fillStyle = i === 0 ? '#0f0' : '#0a0';
                    ctx.fillRect(s.x * grid + 1, s.y * grid + 1, grid - 2, grid - 2);
                });
            }

            if (snakeInterval) clearInterval(snakeInterval);
            snakeInterval = setInterval(tick, 120);

            canvas._snakeHandler = (e) => {
                const sw = document.getElementById('snake-window');
                if (sw && sw.style.display !== 'none') {
                    if (['ArrowUp','ArrowDown','ArrowLeft','ArrowRight','Space',' '].includes(e.key)) e.preventDefault();
                    if (e.key === 'ArrowUp' && dir.y !== 1) nextDir = {x:0, y:-1};
                    if (e.key === 'ArrowDown' && dir.y !== -1) nextDir = {x:0, y:1};
                    if (e.key === 'ArrowLeft' && dir.x !== 1) nextDir = {x:-1, y:0};
                    if (e.key === 'ArrowRight' && dir.x !== -1) nextDir = {x:1, y:0};
                    if ((e.key === ' ' || e.key === 'Space') && !running) {
                        hideSnakeOverlay();
                        document.getElementById('snake-name-input').disabled = false;
                        const btn = document.querySelector('#snake-gameover button');
                        if (btn) btn.style.display = '';
                        snake = [{x: 5, y: 5}];
                        dir = {x: 1, y: 0};
                        nextDir = {x: 1, y: 0};
                        food = spawnFood();
                        score = 0;
                        running = true;
                        document.getElementById('snake-score').textContent = 'Score: 0';
                    }
                }
            };
            document.addEventListener('keydown', canvas._snakeHandler);
        }
        function stopSnake() {
            if (snakeInterval) { clearInterval(snakeInterval); snakeInterval = null; }
            hideSnakeOverlay();
            const canvas = document.getElementById('snake-canvas');
            if (canvas && canvas._snakeHandler) {
                document.removeEventListener('keydown', canvas._snakeHandler);
                canvas._snakeHandler = null;
            }
        }

        // ====== PONG GAME ======
        let pongRAF = null;
        function startPongGame(difficulty) {
            difficulty = difficulty || 'medium';
            lastPongDifficulty = difficulty;
            hidePongOverlay();
            const diffSettings = {
                easy:   { ballSpeed: 1.8, cpuSpeed: 1.2, accel: 1.02 },
                medium: { ballSpeed: 2.5, cpuSpeed: 2.0, accel: 1.04 },
                hard:   { ballSpeed: 3.5, cpuSpeed: 3.0, accel: 1.06 }
            };
            const diff = diffSettings[difficulty];
            // Show canvas, hide difficulty selector
            document.getElementById('pong-difficulty').style.display = 'none';
            const canvas = document.getElementById('pong-canvas');
            canvas.style.display = 'block';
            document.getElementById('pong-score').style.display = 'block';
            document.getElementById('pong-instructions').style.display = 'block';
            if (!canvas) return;
            const ctx = canvas.getContext('2d');
            const W = canvas.width, H = canvas.height;
            const paddleH = 50, paddleW = 8, ballR = 5;
            let playerY = H/2 - paddleH/2, cpuY = H/2 - paddleH/2;
            let ball = {x: W/2, y: H/2, vx: diff.ballSpeed, vy: diff.ballSpeed * 0.6};
            let pScore = 0, cScore = 0;
            let running = false;

            function reset() {
                ball = {x: W/2, y: H/2, vx: (Math.random() > 0.5 ? diff.ballSpeed : -diff.ballSpeed), vy: (Math.random() - 0.5) * diff.ballSpeed * 1.2};
                playerY = H/2 - paddleH/2;
                cpuY = H/2 - paddleH/2;
            }

            function tick() {
                if (!running) { pongRAF = requestAnimationFrame(tick); return; }
                // CPU AI
                const cpuCenter = cpuY + paddleH/2;
                if (cpuCenter < ball.y - 10) cpuY += diff.cpuSpeed;
                else if (cpuCenter > ball.y + 10) cpuY -= diff.cpuSpeed;
                cpuY = Math.max(0, Math.min(H - paddleH, cpuY));

                // Ball movement
                ball.x += ball.vx;
                ball.y += ball.vy;
                if (ball.y <= ballR || ball.y >= H - ballR) ball.vy *= -1;

                // Paddle collision - player
                if (ball.x - ballR <= paddleW + 10 && ball.y >= playerY && ball.y <= playerY + paddleH && ball.vx < 0) {
                    ball.vx *= -diff.accel;
                    ball.vy += (ball.y - (playerY + paddleH/2)) * 0.1;
                }
                // Paddle collision - cpu
                if (ball.x + ballR >= W - paddleW - 10 && ball.y >= cpuY && ball.y <= cpuY + paddleH && ball.vx > 0) {
                    ball.vx *= -diff.accel;
                    ball.vy += (ball.y - (cpuY + paddleH/2)) * 0.1;
                }

                // Scoring
                const winScore = 5;
                if (ball.x < 0) { cScore++; reset(); }
                if (ball.x > W) { pScore++; reset(); }
                document.getElementById('pong-score').textContent = 'You: ' + pScore + ' | CPU: ' + cScore;
                if (pScore >= winScore || cScore >= winScore) {
                    running = false;
                    showPongOverlay(pScore, cScore, pScore >= winScore);
                    return;
                }

                // Draw
                ctx.fillStyle = '#111';
                ctx.fillRect(0, 0, W, H);
                ctx.setLineDash([4, 4]);
                ctx.strokeStyle = '#333';
                ctx.beginPath();
                ctx.moveTo(W/2, 0);
                ctx.lineTo(W/2, H);
                ctx.stroke();
                ctx.setLineDash([]);
                ctx.fillStyle = '#fff';
                ctx.fillRect(10, playerY, paddleW, paddleH);
                ctx.fillRect(W - 10 - paddleW, cpuY, paddleW, paddleH);
                ctx.beginPath();
                ctx.arc(ball.x, ball.y, ballR, 0, Math.PI * 2);
                ctx.fill();

                pongRAF = requestAnimationFrame(tick);
            }

            canvas._pongKeyHandler = (e) => {
                const pw = document.getElementById('pong-window');
                if (pw && pw.style.display !== 'none') {
                    if (['ArrowUp','ArrowDown','Space',' '].includes(e.key)) e.preventDefault();
                    if (e.key === 'ArrowUp') playerY = Math.max(0, playerY - 20);
                    if (e.key === 'ArrowDown') playerY = Math.min(H - paddleH, playerY + 20);
                    if ((e.key === ' ' || e.key === 'Space') && !running) { running = true; }
                }
            };
            canvas._pongMouseHandler = (e) => {
                const rect = canvas.getBoundingClientRect();
                playerY = e.clientY - rect.top - paddleH/2;
                playerY = Math.max(0, Math.min(H - paddleH, playerY));
                if (!running) running = true;
            };
            document.addEventListener('keydown', canvas._pongKeyHandler);
            canvas.addEventListener('mousemove', canvas._pongMouseHandler);

            if (pongRAF) cancelAnimationFrame(pongRAF);
            pongRAF = requestAnimationFrame(tick);
        }
        function stopPong() {
            if (pongRAF) { cancelAnimationFrame(pongRAF); pongRAF = null; }
            const canvas = document.getElementById('pong-canvas');
            if (canvas) {
                if (canvas._pongKeyHandler) { document.removeEventListener('keydown', canvas._pongKeyHandler); canvas._pongKeyHandler = null; }
                if (canvas._pongMouseHandler) { canvas.removeEventListener('mousemove', canvas._pongMouseHandler); canvas._pongMouseHandler = null; }
                canvas.style.display = 'none';
            }
            hidePongOverlay();
            const diffEl = document.getElementById('pong-difficulty');
            if (diffEl) diffEl.style.display = 'block';
            const scoreEl = document.getElementById('pong-score');
            if (scoreEl) { scoreEl.style.display = 'none'; scoreEl.textContent = 'You: 0 | CPU: 0'; }
            const instrEl = document.getElementById('pong-instructions');
            if (instrEl) instrEl.style.display = 'none';
        }

        // Auto-start games when windows open
        const origOpenWindow = openWindow;
        openWindow = function(id) {
            origOpenWindow(id);
            if (id === 'snake-window') setTimeout(startSnakeGame, 100);
            // Pong shows difficulty selector, no auto-start
        };

        // Enter key to submit scores
        document.getElementById('snake-name-input')?.addEventListener('keydown', (e) => {
            if (e.key === 'Enter') submitSnakeScore();
        });
        document.getElementById('pong-name-input')?.addEventListener('keydown', (e) => {
            if (e.key === 'Enter') submitPongScore();
        });

        // ==========================================
        // DIAL-UP CONNECTION DIALOG
        // ==========================================
        let dialUpTimer = null;
        let dialUpConnected = false;

        function openDialUpDialog() {
            const overlay = document.getElementById('dialup-overlay');
            overlay.style.display = 'flex';
            // Reset state
            dialUpConnected = false;
            document.getElementById('dialup-status').innerHTML = '<div class="dialup-status-line">Status: Ready to connect</div>';
            document.getElementById('dialup-progress-fill').style.width = '0%';
            document.getElementById('dialup-speed').textContent = '';
            document.getElementById('dialup-connect-btn').textContent = 'Connect';
            document.getElementById('dialup-connect-btn').disabled = false;
            document.querySelectorAll('#dialup-signal .dialup-signal-dot').forEach(d => d.classList.remove('active'));
        }

        function closeDialUp() {
            document.getElementById('dialup-overlay').style.display = 'none';
            if (dialUpTimer) { clearTimeout(dialUpTimer); dialUpTimer = null; }
        }

        function startDialUpConnection() {
            if (dialUpConnected) { closeDialUp(); return; }
            const btn = document.getElementById('dialup-connect-btn');
            btn.textContent = 'Connecting...';
            btn.disabled = true;
            const status = document.getElementById('dialup-status');
            const fill = document.getElementById('dialup-progress-fill');
            const speed = document.getElementById('dialup-speed');
            const dots = document.querySelectorAll('#dialup-signal .dialup-signal-dot');

            // Play dial-up sound
            playDialUpSound();

            const steps = [
                { msg: 'Dialing 1-800-NOSTALGIA...', pct: 10, delay: 0 },
                { msg: 'Dialing 1-800-NOSTALGIA...', pct: 15, delay: 600 },
                { msg: 'Ringing...', pct: 20, delay: 1200 },
                { msg: 'Ringing...', pct: 25, delay: 1600 },
                { msg: 'Modem handshaking...', pct: 35, delay: 2000, dotIdx: 0 },
                { msg: 'Modem handshaking...', pct: 45, delay: 2500, dotIdx: 1 },
                { msg: 'Verifying username and password...', pct: 55, delay: 3000, dotIdx: 2 },
                { msg: 'Authenticating... user: webmaster', pct: 65, delay: 3500 },
                { msg: 'Obtaining IP address from DHCP...', pct: 75, delay: 4000, dotIdx: 3 },
                { msg: 'IP assigned: 192.168.0.' + Math.floor(Math.random() * 254 + 1), pct: 85, delay: 4400 },
                { msg: 'Registering on the information superhighway...', pct: 90, delay: 4800, dotIdx: 4 },
                { msg: 'Connected!', pct: 100, delay: 5400 }
            ];

            steps.forEach(function(step) {
                dialUpTimer = setTimeout(function() {
                    status.innerHTML = '<div class="dialup-status-line">Status: ' + step.msg + '</div>';
                    fill.style.width = step.pct + '%';
                    if (typeof step.dotIdx !== 'undefined') {
                        for (let d = 0; d <= step.dotIdx; d++) {
                            dots[d].classList.add('active');
                        }
                    }
                    if (step.pct === 100) {
                        speed.textContent = 'Connected at 56,000 bps  |  Duration: 00:00:0' + Math.floor(Math.random() * 4 + 3);
                        btn.textContent = 'Disconnect';
                        btn.disabled = false;
                        dialUpConnected = true;
                        dots.forEach(d => d.classList.add('active'));
                    }
                }, step.delay);
            });
        }

        // ==========================================
        // EASTER EGGS
        // ==========================================

        // --- 1. KONAMI CODE BSOD ---
        const konamiSequence = ['ArrowUp','ArrowUp','ArrowDown','ArrowDown','ArrowLeft','ArrowRight','ArrowLeft','ArrowRight','b','a'];
        let konamiIndex = 0;
        document.addEventListener('keydown', function(e) {
            if (document.getElementById('bsod-overlay').style.display === 'flex') {
                closeBSOD();
                return;
            }
            if (e.key === konamiSequence[konamiIndex] || e.key.toLowerCase() === konamiSequence[konamiIndex]) {
                konamiIndex++;
                if (konamiIndex === konamiSequence.length) {
                    konamiIndex = 0;
                    showBSOD();
                }
            } else {
                konamiIndex = 0;
            }
        });

        function showBSOD() {
            const bsod = document.getElementById('bsod-overlay');
            bsod.style.display = 'flex';
            bsod.style.flexDirection = 'column';
        }

        function closeBSOD() {
            document.getElementById('bsod-overlay').style.display = 'none';
        }

        // --- 2. MY COMPUTER ---
        function openMyComputer() {
            // Calculate real blog stats
            const postCount = blogPosts.length;
            let totalWords = 0;
            blogPosts.forEach(p => {
                const text = (p.content || '').replace(/<[^>]*>/g, ' ').replace(/\s+/g, ' ').trim();
                totalWords += text.split(' ').filter(w => w.length > 0).length;
            });
            document.getElementById('sys-post-count').textContent = postCount + ' posts loaded';
            document.getElementById('sys-word-count').textContent = totalWords.toLocaleString() + ' words';
            // Blog launched ~2024
            const launchDate = new Date('2025-01-01');
            const now = new Date();
            const days = Math.floor((now - launchDate) / 86400000);
            document.getElementById('sys-uptime').textContent = days + ' days (since launch)';
            openWindow('mycomputer-window');
            makeActive('mycomputer-window');
        }

        // --- 3. DIAL-UP SOUND (Web Audio API synthesized) ---
        let dialUpPlaying = false;
        function playDialUpSound() {
            if (dialUpPlaying) return;
            dialUpPlaying = true;
            const ctx = new (window.AudioContext || window.webkitAudioContext)();
            const duration = 4;
            const sampleRate = ctx.sampleRate;
            const buffer = ctx.createBuffer(1, sampleRate * duration, sampleRate);
            const data = buffer.getChannelData(0);

            // Synthesize dial-up-like sounds
            for (let i = 0; i < data.length; i++) {
                const t = i / sampleRate;
                let v = 0;
                if (t < 0.5) {
                    // Dial tone
                    v = 0.3 * Math.sin(2 * Math.PI * 350 * t) + 0.3 * Math.sin(2 * Math.PI * 440 * t);
                } else if (t < 1.2) {
                    // Ring
                    v = 0.2 * Math.sin(2 * Math.PI * 480 * t) + 0.2 * Math.sin(2 * Math.PI * 620 * t);
                    v *= (Math.sin(2 * Math.PI * 20 * t) > 0 ? 1 : 0);
                } else if (t < 2.5) {
                    // Handshake noise
                    const f1 = 1200 + 600 * Math.sin(2 * Math.PI * 8 * t);
                    const f2 = 2400 + 400 * Math.cos(2 * Math.PI * 12 * t);
                    v = 0.15 * Math.sin(2 * Math.PI * f1 * t) + 0.15 * Math.sin(2 * Math.PI * f2 * t);
                    v += 0.08 * (Math.random() * 2 - 1);
                } else {
                    // Static/white noise fade out
                    const fade = 1 - ((t - 2.5) / 1.5);
                    v = 0.12 * (Math.random() * 2 - 1) * fade;
                    v += 0.08 * Math.sin(2 * Math.PI * 1800 * t) * fade;
                }
                data[i] = Math.max(-1, Math.min(1, v));
            }

            const source = ctx.createBufferSource();
            source.buffer = buffer;
            const gain = ctx.createGain();
            gain.gain.value = 0.4;
            source.connect(gain);
            gain.connect(ctx.destination);
            source.start();
            source.onended = () => { dialUpPlaying = false; ctx.close(); };
        }

        // --- 4a. MEMORY DEFRAG ---
        let defragInterval = null;
        const defragColors = ['#000080','#00aa00','#ff0000','#ffff00','#ffffff','#808080','#000000'];
        function openDefrag() {
            openWindow('defrag-window');
            makeActive('defrag-window');
            startDefrag();
        }
        function startDefrag() {
            const grid = document.getElementById('defrag-grid');
            // 32x16 grid = 512 blocks
            grid.innerHTML = '';
            const blocks = [];
            for (let i = 0; i < 512; i++) {
                const b = document.createElement('div');
                b.className = 'defrag-block';
                b.style.background = defragColors[Math.floor(Math.random() * defragColors.length)];
                grid.appendChild(b);
                blocks.push(b);
            }
            const statuses = [
                'Analyzing memory clusters...',
                'Reading nostalgia sectors...',
                'Defragmenting AIM away messages...',
                'Consolidating ICQ chat logs...',
                'Reorganizing Winamp playlists...',
                'Compacting MySpace Top 8 data...',
                'Recovering deleted Neopets saves...',
                'Optimizing dial-up cache...',
                'Defragmentation 42% complete...',
                'Moving LimeWire downloads to safe zone...',
                'Cleaning GeoCities visitor counters...',
                'Defragmentation 78% complete...',
                'Recovering MSN Messenger emoticons...',
                'Restoring Netscape bookmarks...',
                'Defragmentation complete! Nostalgia optimized.'
            ];
            let step = 0;
            let statusIdx = 0;
            defragInterval = setInterval(() => {
                // Move 3-5 random blocks to "optimized" (blue)
                for (let j = 0; j < 4; j++) {
                    const idx = Math.floor(Math.random() * 512);
                    blocks[idx].style.background = step < 400 ? '#000080' : '#00aa00';
                }
                step++;
                if (step % 30 === 0 && statusIdx < statuses.length) {
                    document.getElementById('defrag-status').textContent = statuses[statusIdx++];
                }
                if (step > 500) {
                    clearInterval(defragInterval);
                    defragInterval = null;
                    blocks.forEach(b => b.style.background = '#000080');
                    document.getElementById('defrag-status').textContent = statuses[statuses.length - 1];
                }
            }, 50);
        }
        function stopDefrag() {
            if (defragInterval) { clearInterval(defragInterval); defragInterval = null; }
        }

        // --- 4b. NOSTALGIA SCANNER ---
        let scanInterval = null;
        function openScanner() {
            openWindow('scanner-window');
            makeActive('scanner-window');
            document.getElementById('scan-output').textContent = 'C:\\NOSTALGIA> scan /deep /all\n\nReady. Click "Start Scan" to begin.';
            document.getElementById('scan-progress-fill').style.width = '0%';
            document.getElementById('scan-start-btn').disabled = false;
        }
        function startNostalgiaScanner() {
            document.getElementById('scan-start-btn').disabled = true;
            const output = document.getElementById('scan-output');
            const progressFill = document.getElementById('scan-progress-fill');
            output.textContent = 'C:\\NOSTALGIA> scan /deep /all\n\nScanning system...';

            const findings = [
                'Scanning C:\\Program Files\\...',
                'Found: AOL Instant Messenger v5.9 (last login: 2004)',
                'Found: 23 forgotten passwords in Netscape Password Manager',
                'Scanning C:\\My Documents\\...',
                'Found: 47 unread AIM away messages',
                'Found: 1 Neopet (still alive, somehow)',
                'WARNING: Neopet is hungry. Very hungry.',
                'Scanning C:\\Windows\\Temp\\...',
                'Found: 312 downloaded Winamp skins',
                'Found: LimeWire folder (94 GB of "linux_distros")',
                'Scanning C:\\Games\\...',
                'Found: Minesweeper high score: 12 seconds (suspicious)',
                'Found: 3 unfinished Oregon Trail saves',
                'Found: SkiFree.exe (the abominable snowman is waiting)',
                'Scanning Windows Registry...',
                'Found: Bonzi Buddy remnants (attempting quarantine...)',
                'WARNING: 14 Ask Jeeves toolbars detected',
                'Found: RealPlayer buffering... still buffering...',
                'Found: 1,247 GeoCities bookmarks (all broken)',
                'Found: MapQuest directions printed in 2001 (37 pages)',
                'Scanning email archives...',
                'Found: 89 chain emails (bad luck if not forwarded)',
                'Found: "You\'ve Got Mail!" notification stuck in loop',
                'Found: MySpace profile backup (Top 8 friends preserved)',
                '',
                '=== SCAN COMPLETE ===',
                'Total nostalgia artifacts found: 2,847',
                'Recommendation: Do not delete. These are precious.',
                'Estimated emotional value: Priceless'
            ];

            let idx = 0;
            scanInterval = setInterval(() => {
                if (idx < findings.length) {
                    output.textContent += '\n' + findings[idx];
                    output.scrollTop = output.scrollHeight;
                    progressFill.style.width = Math.round(((idx + 1) / findings.length) * 100) + '%';
                    idx++;
                } else {
                    clearInterval(scanInterval);
                    scanInterval = null;
                    document.getElementById('scan-start-btn').disabled = false;
                }
            }, 400);
        }
        function stopScanner() {
            if (scanInterval) { clearInterval(scanInterval); scanInterval = null; }
        }

        // --- 6. CURSOR TRAIL ---
        let cursorTrailEnabled = false;
        let trailDots = [];
        const TRAIL_LENGTH = 12;

        function toggleCursorTrail() {
            cursorTrailEnabled = !cursorTrailEnabled;
            document.getElementById('cursor-trail-label').textContent = 'Cursor Trail: ' + (cursorTrailEnabled ? 'ON' : 'OFF');
            if (!cursorTrailEnabled) {
                trailDots.forEach(d => d.remove());
                trailDots = [];
            }
        }

        document.addEventListener('mousemove', function(e) {
            if (!cursorTrailEnabled) return;

            const dot = document.createElement('div');
            dot.className = 'cursor-trail-dot';
            dot.style.left = e.clientX + 'px';
            dot.style.top = e.clientY + 'px';
            document.body.appendChild(dot);
            trailDots.push(dot);

            if (trailDots.length > TRAIL_LENGTH) {
                const old = trailDots.shift();
                old.remove();
            }

            // Fade effect
            trailDots.forEach((d, i) => {
                d.style.opacity = ((i + 1) / trailDots.length) * 0.8;
                const size = 2 + ((i + 1) / trailDots.length) * 4;
                d.style.width = size + 'px';
                d.style.height = size + 'px';
            });
        });