#!/usr/bin/env python3
"""
Build script for 404 Memory Found - Windows 95 themed static site generator

Homepage: Uses the source SPA (src/index.html) with SEO enhancements.
          Posts load dynamically from posts.json via JavaScript.
          All interactive features work natively (drag, resize, tag filters, search, etc.)

Post pages: Static HTML for SEO crawlers and direct links.
            Each post gets its own URL with proper meta tags and JSON-LD schema.
            No boot animation on post pages for smoother UX.
"""

import json
import os
import re
import shutil
from datetime import datetime

# Configuration
BASE_URL = "https://404memoryfound.com"
BLOG_NAME = "404 Memory Found"
OUTPUT_DIR = "."  # Deploy directly to repo root for GitHub Pages


def read_source_files():
    """Read src/index.html (source) and posts.json"""
    source_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'src', 'index.html')
    with open(source_path, 'r', encoding='utf-8') as f:
        html_content = f.read()

    with open('posts.json', 'r', encoding='utf-8') as f:
        posts_data = json.load(f)

    return html_content, posts_data


def get_slug_from_id(post_id):
    """Post ID is already a slug"""
    return post_id


def create_output_directories():
    """Create posts directory"""
    os.makedirs(os.path.join(OUTPUT_DIR, 'posts'), exist_ok=True)


def extract_css(html_content):
    """Extract CSS from <style> block"""
    match = re.search(r'<style>(.*?)</style>', html_content, re.DOTALL)
    return match.group(1).strip() if match else ""


def extract_div_by_marker(html_content, marker):
    """Extract a div and all its nested content using depth counting.
    marker: a string that appears inside the opening div tag (e.g. 'class="taskbar"' or 'id="blog-window"')
    """
    start_pos = html_content.find(marker)
    if start_pos == -1:
        return ""

    # Find the opening <div that contains this marker
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


def extract_javascript(html_content):
    """Extract the main JavaScript code from the last <script> block"""
    last_script_start = html_content.rfind('<script>')
    if last_script_start == -1:
        return ""
    last_script_end = html_content.find('</script>', last_script_start)
    if last_script_end == -1:
        return ""
    js_content = html_content[last_script_start + len('<script>'):last_script_end].strip()
    if js_content and len(js_content) > 100:
        return js_content
    return ""


def get_favicon_link(html_content):
    """Extract favicon link tag and URL-encode the SVG data URI.

    Raw SVG in data URIs breaks HTML parsing because the browser's parser
    treats < and > inside the href as HTML tags. URL-encoding fixes this.
    """
    from urllib.parse import quote
    for line in html_content.split('\n'):
        if '<link rel="icon"' in line:
            line = line.strip()
            # Extract the SVG data and URL-encode the < > characters
            prefix = 'href="data:image/svg+xml,'
            idx = line.find(prefix)
            if idx == -1:
                return line
            svg_start = idx + len(prefix)
            svg_end = line.rfind('">')
            if svg_end == -1:
                return line
            svg_raw = line[svg_start:svg_end]
            svg_encoded = quote(svg_raw, safe='')
            return f'<link rel="icon" type="image/svg+xml" href="data:image/svg+xml,{svg_encoded}">'
    return ""


def generate_index_html(html_content, posts_data):
    """Generate index.html - use the source SPA with SEO enhancements.

    The source HTML already handles everything dynamically:
    - Loads posts from posts.json
    - Populates blog list, archives, tag filters via JS
    - Opens posts in post-window without page navigation
    - All windows (blog, about, archives, post, guestbook) work
    - Boot animation, drag, resize, taskbar all functional

    We just add SEO meta tags and a noscript fallback for crawlers.
    """
    posts = posts_data['posts']

    # Build noscript fallback: a simple list of links for SEO crawlers
    noscript_html = '\n<noscript>\n<div style="padding:20px;font-family:Arial,sans-serif;">\n'
    noscript_html += '<h1>404 Memory Found - Nostalgia Blog</h1>\n'
    noscript_html += '<p>Bizarre stories and curious facts from the 90s and 2000s era.</p>\n<ul>\n'
    for post in posts:
        slug = get_slug_from_id(post['id'])
        noscript_html += f'<li><a href="/posts/{slug}.html">{post["title"]}</a> - {post["date"]}</li>\n'
    noscript_html += '</ul>\n</div>\n</noscript>\n'

    # Inject SEO meta tags into <head>
    seo_meta = f"""    <meta name="description" content="404 Memory Found - A nostalgia blog sharing bizarre stories and curious facts from the 90s and 2000s era with a Windows 95/98 desktop aesthetic.">
    <meta name="keywords" content="90s nostalgia, 2000s, retro blog, Windows 95, internet history, bizarre stories, then vs now">
    <meta property="og:title" content="404 Memory Found - Nostalgia Blog">
    <meta property="og:description" content="Bizarre stories and curious facts from the 90s and 2000s era.">
    <meta property="og:type" content="website">
    <meta property="og:url" content="{BASE_URL}">
    <meta name="twitter:card" content="summary_large_image">
    <meta name="twitter:title" content="404 Memory Found">
    <meta name="twitter:description" content="Bizarre stories and curious facts from the 90s and 2000s era.">
    <meta name="author" content="404 Memory Found">
    <link rel="canonical" href="{BASE_URL}">
    <meta name="robots" content="index, follow">
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
    </script>"""

    # Start with the source HTML
    output = html_content

    # Inject SEO meta after <meta charset> line
    output = output.replace(
        '<meta charset="UTF-8">',
        f'<meta charset="UTF-8">\n{seo_meta}',
        1
    )

    # Inject noscript fallback before closing </body>
    output = output.replace('</body>', f'{noscript_html}</body>', 1)

    return output


def get_related_posts(current_post, all_posts, count=3):
    """Find posts with the most overlapping tags"""
    current_tags = set(current_post.get('tags', []))
    scored_posts = []
    for post in all_posts:
        if post['id'] == current_post['id']:
            continue
        post_tags = set(post.get('tags', []))
        overlap = len(current_tags & post_tags)
        if overlap > 0:
            scored_posts.append((post, overlap))
    scored_posts.sort(key=lambda x: (-x[1], x[0]['date']))
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


def generate_post_html(post, all_posts, html_content, posts_data):
    """Generate individual post HTML file for SEO.

    These pages exist so search engines can crawl individual post URLs.
    They show the post content directly (no boot animation needed).
    Close/back navigates to the homepage SPA.
    """
    slug = get_slug_from_id(post['id'])
    related_posts = get_related_posts(post, all_posts, count=3)

    css = extract_css(html_content)
    desktop_icons = extract_div_by_marker(html_content, 'class="desktop-icons">')
    taskbar = extract_div_by_marker(html_content, 'class="taskbar">')
    favicon_link = get_favicon_link(html_content)
    javascript = extract_javascript(html_content)

    post_body = post['body']
    post_schema = generate_post_schema(post, slug)

    # Related posts HTML
    related_html = '<div class="related-posts" style="margin-top:20px;padding:10px;background:#f0f0f0;border:1px solid #999;">'
    related_html += '<strong>Related Posts:</strong><ul style="list-style:none;margin:10px 0 0 0;padding:0;">'
    for rp in related_posts:
        rp_slug = get_slug_from_id(rp['id'])
        related_html += f'<li style="padding:5px 0;"><a href="/posts/{rp_slug}.html">{rp["title"]}</a></li>'
    related_html += '</ul></div>'

    back_btn = '<div style="margin:10px 0;"><a href="/" style="padding:5px 10px;background:#c0c0c0;border:2px outset #dfdfdf;color:#000;text-decoration:none;display:inline-block;font-family:\'MS Sans Serif\',Arial,sans-serif;">&larr; Back to Blog</a></div>'

    post_content = post_body + related_html + back_btn

    # Post window - open by default, proper structure
    post_window = f'''<div class="window" id="post-window" style="left:120px;top:15px;width:850px;height:620px;display:flex;">
                <div class="title-bar">
                    <div class="title-bar-title">📖 {post['title']}</div>
                    <div class="title-bar-controls">
                        <button class="window-button" onclick="minimizeWindow('post-window')"><span class="btn-minimize"></span></button>
                        <button class="window-button" onclick="toggleMaximizeWindow('post-window')"><span class="btn-maximize"></span></button>
                        <button class="window-button" onclick="closeWindow('post-window'); if (window.opener || window.history.length <= 1) {{ window.close(); }} else {{ window.location.href='/'; }}"><span class="btn-close">×</span></button>
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

    # Mobile related posts
    mobile_related = ""
    for rp in related_posts:
        rp_slug = get_slug_from_id(rp['id'])
        mobile_related += f'<li style="padding:5px 0;"><a href="/posts/{rp_slug}.html">{rp["title"]}</a></li>\n'

    # JS wrapper that skips boot animation and auto-opens post window
    post_js_wrapper = f"""
        // On post pages: skip boot animation, just initialize
        var isPostPage = true;
        var postPageSlug = '{slug}';
        {javascript}
    """

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
    <meta name="robots" content="index, follow">
    <script type="application/ld+json">
    {post_schema}
    </script>

    <title>{post['title']} | 404 Memory Found</title>
    {favicon_link}

    <style>
{css}
    </style>
</head>
<body>
    <!-- No boot animation on post pages for faster load -->

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
{mobile_related}
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
        </div>
        {taskbar}
    </div>

    <script>
{post_js_wrapper}
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
    return f"""User-agent: *
Allow: /
Sitemap: {BASE_URL}/sitemap.xml
"""


def generate_cname():
    return "404memoryfound.com"


def main():
    """Main build process"""
    print("🔨 Building 404 Memory Found static site...")

    print("📖 Reading source files...")
    html_content, posts_data = read_source_files()
    posts = posts_data['posts']

    print("📁 Creating output directories...")
    create_output_directories()

    # Homepage: SPA based on source HTML
    print("📄 Generating index.html (SPA)...")
    index_html = generate_index_html(html_content, posts_data)
    with open(os.path.join(OUTPUT_DIR, 'index.html'), 'w', encoding='utf-8') as f:
        f.write(index_html)

    # Copy posts.json to output (needed by SPA JavaScript)
    print("📋 Copying posts.json...")
    src_posts = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'posts.json')
    dst_posts = os.path.join(OUTPUT_DIR, 'posts.json')
    if os.path.abspath(src_posts) != os.path.abspath(dst_posts):
        shutil.copy2(src_posts, dst_posts)

    # Individual post pages for SEO
    print("📝 Generating individual post pages...")
    for post in posts:
        slug = get_slug_from_id(post['id'])
        post_html = generate_post_html(post, posts, html_content, posts_data)
        post_path = os.path.join(OUTPUT_DIR, 'posts', f'{slug}.html')
        with open(post_path, 'w', encoding='utf-8') as f:
            f.write(post_html)
        print(f"   ✓ {slug}.html")

    # Generate sitemap, robots.txt, CNAME
    print("🗺️  Generating sitemap.xml...")
    with open(os.path.join(OUTPUT_DIR, 'sitemap.xml'), 'w', encoding='utf-8') as f:
        f.write(generate_sitemap(posts_data))

    print("🤖 Generating robots.txt...")
    with open(os.path.join(OUTPUT_DIR, 'robots.txt'), 'w', encoding='utf-8') as f:
        f.write(generate_robots_txt())

    print("🌐 Generating CNAME...")
    with open(os.path.join(OUTPUT_DIR, 'CNAME'), 'w', encoding='utf-8') as f:
        f.write(generate_cname())

    print(f"\n✅ Build complete!")
    print(f"   📂 Output directory: {OUTPUT_DIR}/")
    print(f"   📄 Files generated: {1 + len(posts) + 3} total")
    print(f"      - index.html (SPA homepage)")
    print(f"      - posts.json (data for SPA)")
    print(f"      - {len(posts)} post pages in posts/")
    print(f"      - sitemap.xml, robots.txt, CNAME")


if __name__ == '__main__':
    main()
