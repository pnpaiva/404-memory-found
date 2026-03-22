#!/usr/bin/env python3
"""
Build script for 404 Memory Found - Windows 95 themed static site generator
Reads posts.json and index.html, generates multi-page static HTML files
"""

import json
import os
import re
from datetime import datetime
from urllib.parse import quote

# Configuration
BASE_URL = "https://404memoryfound.com"
BLOG_NAME = "404 Memory Found"
OUTPUT_DIR = "."  # Deploy directly to repo root for GitHub Pages

def slugify(text):
    """Convert text to URL-safe slug"""
    return re.sub(r'[^\w\-]', '', text.lower().replace(' ', '-').replace('_', '-'))

def get_slug_from_id(post_id):
    """Post ID is already a slug"""
    return post_id

def read_source_files():
    """Read src/index.html (source) and posts.json"""
    source_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'src', 'index.html')
    with open(source_path, 'r', encoding='utf-8') as f:
        html_content = f.read()

    with open('posts.json', 'r', encoding='utf-8') as f:
        posts_data = json.load(f)

    return html_content, posts_data

def extract_css(html_content):
    """Extract CSS from <style> block"""
    match = re.search(r'<style>(.*?)</style>', html_content, re.DOTALL)
    if match:
        return match.group(1).strip()
    return ""

def extract_desktop_icons(html_content):
    """Extract desktop icons HTML block"""
    # Find the opening tag
    start = html_content.find('<div class="desktop-icons">')
    if start == -1:
        return ""

    # Find the closing tag - match nested divs
    depth = 0
    pos = start

    while pos < len(html_content):
        if html_content[pos:pos+4] == '<div':
            depth += 1
        elif html_content[pos:pos+6] == '</div>':
            depth -= 1
            if depth == 0:
                return html_content[start:pos+6]
        pos += 1

    return ""

def extract_window_html(html_content, window_id):
    """Extract a window div by ID, handling nested divs"""
    marker = f'id="{window_id}"'
    start_pos = html_content.find(marker)
    if start_pos == -1:
        return ""

    # Find the opening <div that contains this id
    div_start = html_content.rfind('<div', 0, start_pos)
    if div_start == -1:
        return ""

    # Count nested divs to find the matching closing </div>
    depth = 0
    pos = div_start
    while pos < len(html_content):
        if html_content[pos:pos+4] == '<div':
            depth += 1
        elif html_content[pos:pos+6] == '</div>':
            depth -= 1
            if depth == 0:
                return html_content[div_start:pos+6]
        pos += 1
    return ""

def extract_taskbar(html_content):
    """Extract taskbar HTML, handling nested divs"""
    # Find the opening taskbar div
    start_pos = html_content.find('<div class="taskbar">')
    if start_pos == -1:
        return ""

    # Count nested divs to find the matching closing </div>
    depth = 0
    pos = start_pos
    while pos < len(html_content):
        if html_content[pos:pos+4] == '<div':
            depth += 1
        elif html_content[pos:pos+6] == '</div>':
            depth -= 1
            if depth == 0:
                return html_content[start_pos:pos+6]
        pos += 1
    return ""

def extract_boot_animation(html_content):
    """Extract boot animation HTML"""
    match = re.search(
        r'(<div id="boot-animation".*?</div>)',
        html_content,
        re.DOTALL
    )
    if match:
        return match.group(1)
    return ""

def get_favicon_svg(html_content):
    """Extract favicon from link tag"""
    match = re.search(r'<link rel="icon"[^>]*href="([^"]+)"', html_content)
    if match:
        return match.group(1)
    return ""

def extract_javascript(html_content):
    """Extract the main JavaScript code from the last <script> block"""
    # Find the last <script>...</script> block which contains the main JS
    # Use a simple approach: find last occurrence of bare <script> tag
    last_script_start = html_content.rfind('<script>')
    if last_script_start == -1:
        return ""
    last_script_end = html_content.find('</script>', last_script_start)
    if last_script_end == -1:
        return ""
    js_content = html_content[last_script_start + len('<script>'):last_script_end].strip()
    # Return if we found substantial JS (more than a few chars)
    if js_content and len(js_content) > 100:
        return js_content
    return ""

def create_output_directories():
    """Create dist and dist/posts directories"""
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    os.makedirs(os.path.join(OUTPUT_DIR, 'posts'), exist_ok=True)

def get_related_posts(current_post, all_posts, count=3):
    """Find posts with the most overlapping tags"""
    current_tags = set(current_post.get('tags', []))
    
    scored_posts = []
    for post in all_posts:
        if post['id'] == current_post['id']:
            continue
        post_tags = set(post.get('tags', []))
        # Count overlapping tags
        overlap = len(current_tags & post_tags)
        if overlap > 0:
            scored_posts.append((post, overlap))
    
    # Sort by overlap count (descending) then by date (newest first)
    scored_posts.sort(
        key=lambda x: (-x[1], x[0]['date']),
        reverse=False
    )
    scored_posts.reverse()
    
    return [post for post, _ in scored_posts[:count]]

def generate_post_schema(post, slug):
    """Generate JSON-LD BlogPosting schema"""
    schema = {
        "@context": "https://schema.org",
        "@type": "BlogPosting",
        "headline": post['title'],
        "description": post['excerpt'],
        "datePublished": post['date'],
        "author": {
            "@type": "Person",
            "name": post['author']
        },
        "url": f"{BASE_URL}/posts/{slug}.html"
    }
    return json.dumps(schema)

def generate_index_html(html_content, posts_data):
    """Generate dist/index.html - main page with desktop"""
    posts = posts_data['posts']
    
    css = extract_css(html_content)
    desktop_icons = extract_desktop_icons(html_content)
    about_window = extract_window_html(html_content, 'about-window')
    archives_window = extract_window_html(html_content, 'archives-window')
    blog_window = extract_window_html(html_content, 'blog-window')
    taskbar = extract_taskbar(html_content)
    boot_animation = extract_boot_animation(html_content)
    favicon = get_favicon_svg(html_content)
    javascript = extract_javascript(html_content)
    
    # Generate blog posts list HTML for the window
    blog_posts_html = '<ul class="blog-posts-list">'
    for post in posts:
        slug = get_slug_from_id(post['id'])
        blog_posts_html += f'<li class="blog-post-item" onclick="window.location.href=\'/posts/{slug}.html\'">'
        blog_posts_html += f'<strong>{post["title"]}</strong><br>'
        blog_posts_html += f'<span class="post-date">{post["date"]}</span><br>'
        blog_posts_html += f'<span class="post-excerpt">{post["excerpt"]}</span>'
        blog_posts_html += '</li>'
    blog_posts_html += '</ul>'
    
    # Generate archives by date
    archives_by_month = {}
    for post in posts:
        date_parts = post['date'].split('-')
        month_year = f"{date_parts[0]}-{date_parts[1]}"  # YYYY-MM
        if month_year not in archives_by_month:
            archives_by_month[month_year] = []
        archives_by_month[month_year].append(post)
    
    archives_html = '<div class="archives-list">'
    for month_year in sorted(archives_by_month.keys(), reverse=True):
        archives_html += f'<h3>{month_year}</h3><ul>'
        for post in sorted(archives_by_month[month_year], key=lambda p: p['date'], reverse=True):
            slug = get_slug_from_id(post['id'])
            archives_html += f'<li><a href="/posts/{slug}.html">{post["title"]}</a></li>'
        archives_html += '</ul>'
    archives_html += '</div>'
    
    # Replace the empty blog-posts-list <ul> with pre-rendered posts
    # The source has: <ul class="blog-posts-list" id="blog-posts-list"></ul>
    # We replace it with a populated version for static rendering
    blog_window_modified = blog_window.replace(
        '<ul class="blog-posts-list" id="blog-posts-list"></ul>',
        blog_posts_html
    )
    # Fallback: if the exact match wasn't found, try the simpler injection
    if blog_window_modified == blog_window:
        blog_window_modified = blog_window.replace(
            '<div class="window-content">',
            f'<div class="window-content">{blog_posts_html}',
            1
        )

    # Replace archives list content
    archives_window_modified = archives_window.replace(
        '<ul class="archives-list" id="archives-list"></ul>',
        archives_html
    )
    if archives_window_modified == archives_window:
        archives_window_modified = archives_window.replace(
            '<div class="window-content">',
            f'<div class="window-content">{archives_html}',
            1
        )
    
    # Remove post-window since it's only for individual posts
    post_window = extract_window_html(html_content, 'post-window')
    
    # Build mobile posts list
    mobile_posts_html = ""
    for post in posts:
        slug = get_slug_from_id(post['id'])
        mobile_posts_html += f"""                <li class="mobile-post-item" onclick="window.location.href='/posts/{slug}.html'">
                    <h3>{post['title']}</h3>
                    <div class="mobile-post-date">{post['date']}</div>
                    <div class="mobile-post-excerpt">{post['excerpt']}</div>
                </li>
"""

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <meta name="description" content="404 Memory Found - A nostalgia blog sharing bizarre stories and curious facts from the 90s and 2000s era with a Windows 95/98 desktop aesthetic.">
    <meta name="keywords" content="90s nostalgia, 2000s, retro blog, Windows 95, internet history, bizarre stories">
    <meta property="og:title" content="404 Memory Found - Nostalgia Blog">
    <meta property="og:description" content="Bizarre stories and curious facts from the 90s and 2000s era.">
    <meta property="og:type" content="website">
    <meta property="og:url" content="{BASE_URL}">
    <meta name="twitter:card" content="summary_large_image">
    <meta name="twitter:title" content="404 Memory Found">
    <meta name="twitter:description" content="Bizarre stories and curious facts from the 90s and 2000s era.">
    <meta name="author" content="404 Memory Found">
    <link rel="canonical" href="{BASE_URL}">

    <script type="application/ld+json">
    {{
      "@context": "https://schema.org",
      "@type": "Blog",
      "name": "{BLOG_NAME}",
      "description": "A nostalgia blog sharing bizarre stories and curious facts from the 90s and 2000s era",
      "url": "{BASE_URL}",
      "author": {{
        "@type": "Organization",
        "name": "{BLOG_NAME}"
      }}
    }}
    </script>

    <title>404 Memory Found - Windows 95 Nostalgia Blog</title>
    <link rel="icon" type="image/svg+xml" href="{favicon}">
    <meta name="robots" content="index, follow">

    <style>
{css}
    </style>
</head>
<body>
    <!-- Boot Animation (Desktop only) -->
    <div class="boot-animation">
        <div class="boot-logo">404 MEMORY FOUND</div>
        <div>Initializing Nostalgia Engine...</div>
        <div>Loading 90s vibes...</div>
        <div>Configuring Windows 95 emulation...</div>
        <div>Ready to surf the memories!</div>
    </div>

    <!-- Mobile View -->
    <div class="mobile-container">
        <div class="mobile-header">
            <h1>404 Memory Found</h1>
            <p>A Nostalgia Blog from the 90s &amp; 2000s</p>
        </div>
        <div class="mobile-content">
            <ul class="mobile-post-list" id="mobile-post-list">
{mobile_posts_html}
            </ul>
        </div>
        <div class="mobile-footer">
            <p>&copy; 2026 404 Memory Found. All rights reserved.</p>
            <p>
                <a href="#about">About</a> |
                <a href="#contact">Contact</a> |
                <a href="#privacy">Privacy Policy</a> |
                <a href="#terms">Terms of Use</a>
            </p>
            <div class="mobile-tagline">Powered by nostalgia</div>
        </div>
    </div>

    <!-- Desktop View -->
    <div class="desktop-container">
        <h1 style="position: absolute; left: -9999px; top: -9999px;">404 Memory Found - Windows 95 Nostalgia Blog</h1>

        <div class="desktop-area" onclick="document.querySelectorAll('.desktop-icon.selected').forEach(i => i.classList.remove('selected'))">
            {desktop_icons}
            {blog_window_modified}
            {about_window}
            {archives_window_modified}
        </div>
        {taskbar}
    </div>

    <script>
{javascript}
    </script>
</body>
</html>"""
    
    return html

def generate_post_html(post, all_posts, html_content, posts_data):
    """Generate individual post HTML file"""
    slug = get_slug_from_id(post['id'])
    related_posts = get_related_posts(post, all_posts, count=3)
    
    css = extract_css(html_content)
    desktop_icons = extract_desktop_icons(html_content)
    about_window = extract_window_html(html_content, 'about-window')
    archives_window = extract_window_html(html_content, 'archives-window')
    blog_window = extract_window_html(html_content, 'blog-window')
    taskbar = extract_taskbar(html_content)
    boot_animation = extract_boot_animation(html_content)
    favicon = get_favicon_svg(html_content)
    javascript = extract_javascript(html_content)
    
    # Generate blog posts list for the window
    blog_posts_html = '<ul class="blog-posts-list">'
    for p in all_posts:
        p_slug = get_slug_from_id(p['id'])
        blog_posts_html += f'<li class="blog-post-item" onclick="window.location.href=\'/posts/{p_slug}.html\'">'
        blog_posts_html += f'<strong>{p["title"]}</strong><br>'
        blog_posts_html += f'<span class="post-date">{p["date"]}</span><br>'
        blog_posts_html += f'<span class="post-excerpt">{p["excerpt"]}</span>'
        blog_posts_html += '</li>'
    blog_posts_html += '</ul>'
    
    blog_window_modified = blog_window.replace(
        '<ul class="blog-posts-list" id="blog-posts-list"></ul>',
        blog_posts_html
    )
    if blog_window_modified == blog_window:
        blog_window_modified = blog_window.replace(
            '<div class="window-content">',
            f'<div class="window-content">{blog_posts_html}',
            1
        )

    # Create post window content
    post_body = post['body']
    
    # Related posts HTML
    related_html = '<div class="related-posts" style="margin-top:20px;padding:10px;background:#f0f0f0;border:1px solid #999;">'
    related_html += '<strong>Related Posts:</strong><ul style="list-style:none;margin:10px 0 0 0;padding:0;">'
    for related_post in related_posts:
        related_slug = get_slug_from_id(related_post['id'])
        related_html += f'<li style="padding:5px 0;"><a href="/posts/{related_slug}.html">{related_post["title"]}</a></li>'
    related_html += '</ul></div>'
    
    # Back to blog button
    back_to_blog = '<div style="margin:10px 0;"><a href="/" style="padding:5px 10px;background:#c0c0c0;border:2px outset #dfdfdf;color:#000;text-decoration:none;display:inline-block;font-family:\'MS Sans Serif\',Arial,sans-serif;">← Back to Blog</a></div>'
    
    post_content = post_body + related_html + back_to_blog
    
    # Generate post window (should be open by default)
    # Must match source HTML structure: title-bar (not window-title), title-bar-controls (not window-buttons)
    # No inline onmousedown - the JS uses event delegation on .title-bar
    # Must include all 8 resize handles
    post_window = f'''<div class="window" id="post-window" style="left:150px;top:20px;width:650px;height:500px;display:block;">
                <div class="title-bar">
                    <div class="title-bar-title">📖 {post['title']}</div>
                    <div class="title-bar-controls">
                        <button class="window-button" onclick="minimizeWindow('post-window')">_</button>
                        <button class="window-button" onclick="toggleMaximizeWindow('post-window')">□</button>
                        <button class="window-button" onclick="closeWindow('post-window'); window.location.href='/'">×</button>
                    </div>
                </div>
                <div class="window-content">
                    {post_content}
                </div>
                <div class="resize-handle resize-handle-n"></div>
                <div class="resize-handle resize-handle-s"></div>
                <div class="resize-handle resize-handle-e"></div>
                <div class="resize-handle resize-handle-w"></div>
                <div class="resize-handle resize-handle-ne"></div>
                <div class="resize-handle resize-handle-nw"></div>
                <div class="resize-handle resize-handle-se"></div>
                <div class="resize-handle resize-handle-sw"></div>
            </div>'''
    
    post_schema = generate_post_schema(post, slug)
    
    # Build mobile related posts
    mobile_related_html = ""
    for related_post in related_posts:
        related_slug = get_slug_from_id(related_post['id'])
        mobile_related_html += f'                        <li style="padding:5px 0;"><a href="/posts/{related_slug}.html">{related_post["title"]}</a></li>\n'

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <meta name="description" content="{post['excerpt']}">
    <meta property="og:title" content="{post['title']}">
    <meta property="og:description" content="{post['excerpt']}">
    <meta property="og:type" content="article">
    <meta property="og:url" content="{BASE_URL}/posts/{slug}.html">
    <meta name="twitter:card" content="summary_large_image">
    <meta name="twitter:title" content="{post['title']}">
    <meta name="twitter:description" content="{post['excerpt']}">
    <meta name="author" content="{post['author']}">
    <link rel="canonical" href="{BASE_URL}/posts/{slug}.html">

    <script type="application/ld+json">
    {post_schema}
    </script>

    <title>{post['title']} | 404 Memory Found</title>
    <link rel="icon" type="image/svg+xml" href="{favicon}">
    <meta name="robots" content="index, follow">

    <style>
{css}
    </style>
</head>
<body>
    <!-- Boot Animation (Desktop only) -->
    <div class="boot-animation">
        <div class="boot-logo">404 MEMORY FOUND</div>
        <div>Initializing Nostalgia Engine...</div>
        <div>Loading 90s vibes...</div>
        <div>Configuring Windows 95 emulation...</div>
        <div>Ready to surf the memories!</div>
    </div>

    <!-- Mobile View -->
    <div class="mobile-container">
        <div class="mobile-header">
            <h1>{post['title']}</h1>
            <p>{post['date']} by {post['author']}</p>
        </div>
        <div class="mobile-content">
            <article style="padding:16px;">
                {post_body}
                <div style="margin-top:20px;padding:10px;background:#f0f0f0;">
                    <strong>Related Posts:</strong>
                    <ul style="list-style:none;margin:10px 0 0 0;padding:0;">
{mobile_related_html}
                    </ul>
                </div>
                <div style="margin:10px 0;"><a href="/" style="padding:5px 10px;background:#c0c0c0;color:#000;text-decoration:none;display:inline-block;">&#8592; Back to Blog</a></div>
            </article>
        </div>
        <div class="mobile-footer">
            <p>&copy; 2026 404 Memory Found. All rights reserved.</p>
            <p style="font-size:10px;margin-top:8px;">Posted on {post['date']} by {post['author']}</p>
        </div>
    </div>

    <!-- Desktop View -->
    <div class="desktop-container">
        <h1 style="position: absolute; left: -9999px; top: -9999px;">{post['title']} | 404 Memory Found</h1>

        <div class="desktop-area" onclick="document.querySelectorAll('.desktop-icon.selected').forEach(i => i.classList.remove('selected'))">
            {desktop_icons}
            {post_window}
            {blog_window_modified}
            {about_window}
            {archives_window}
        </div>
        {taskbar}
    </div>

    <script>
{javascript}
    </script>
</body>
</html>"""
    
    return html

def generate_sitemap(posts_data):
    """Generate sitemap.xml"""
    posts = posts_data['posts']
    
    sitemap = f"""<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
  <url>
    <loc>{BASE_URL}/</loc>
    <lastmod>{datetime.now().strftime('%Y-%m-%d')}</lastmod>
    <changefreq>daily</changefreq>
    <priority>1.0</priority>
  </url>
"""
    
    for post in posts:
        slug = get_slug_from_id(post['id'])
        sitemap += f"""  <url>
    <loc>{BASE_URL}/posts/{slug}.html</loc>
    <lastmod>{post['date']}</lastmod>
    <changefreq>monthly</changefreq>
    <priority>0.8</priority>
  </url>
"""
    
    sitemap += """</urlset>"""
    
    return sitemap

def generate_robots_txt():
    """Generate robots.txt"""
    return f"""User-agent: *
Allow: /
Sitemap: {BASE_URL}/sitemap.xml
"""

def generate_cname():
    """Generate CNAME file for GitHub Pages"""
    return "404memoryfound.com"

def main():
    """Main build process"""
    print("🔨 Building 404 Memory Found static site...")
    
    # Read source files
    print("📖 Reading source files...")
    html_content, posts_data = read_source_files()
    posts = posts_data['posts']
    
    # Create output directories
    print("📁 Creating output directories...")
    create_output_directories()
    
    # Generate index.html
    print("📄 Generating index.html...")
    index_html = generate_index_html(html_content, posts_data)
    with open(os.path.join(OUTPUT_DIR, 'index.html'), 'w', encoding='utf-8') as f:
        f.write(index_html)
    
    # Generate individual post pages
    print("📝 Generating individual post pages...")
    for post in posts:
        slug = get_slug_from_id(post['id'])
        post_html = generate_post_html(post, posts, html_content, posts_data)
        post_path = os.path.join(OUTPUT_DIR, 'posts', f'{slug}.html')
        with open(post_path, 'w', encoding='utf-8') as f:
            f.write(post_html)
        print(f"   ✓ {slug}.html")
    
    # Generate sitemap.xml
    print("🗺️  Generating sitemap.xml...")
    sitemap = generate_sitemap(posts_data)
    with open(os.path.join(OUTPUT_DIR, 'sitemap.xml'), 'w', encoding='utf-8') as f:
        f.write(sitemap)
    
    # Generate robots.txt
    print("🤖 Generating robots.txt...")
    robots = generate_robots_txt()
    with open(os.path.join(OUTPUT_DIR, 'robots.txt'), 'w', encoding='utf-8') as f:
        f.write(robots)
    
    # Generate CNAME
    print("🌐 Generating CNAME...")
    cname = generate_cname()
    with open(os.path.join(OUTPUT_DIR, 'CNAME'), 'w', encoding='utf-8') as f:
        f.write(cname)
    
    print("\n✅ Build complete!")
    print(f"   📂 Output directory: {OUTPUT_DIR}/")
    print(f"   📄 Files generated: {1 + len(posts) + 3} total")
    print(f"      - index.html")
    print(f"      - {len(posts)} post pages in posts/")
    print(f"      - sitemap.xml, robots.txt, CNAME")

if __name__ == '__main__':
    main()
