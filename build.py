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
OUTPUT_DIR = "dist"

def slugify(text):
    """Convert text to URL-safe slug"""
    return re.sub(r'[^\w\-]', '', text.lower().replace(' ', '-').replace('_', '-'))

def get_slug_from_id(post_id):
    """Post ID is already a slug"""
    return post_id

def read_source_files():
    """Read index.html and posts.json"""
    with open('index.html', 'r', encoding='utf-8') as f:
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
        if html_content[pos:pos+5] == '<div ':
            depth += 1
        elif html_content[pos:pos+6] == '</div>':
            depth -= 1
            if depth == 0:
                return html_content[start:pos+6]
        pos += 1

    return ""

def extract_window_html(html_content, window_id):
    """Extract a window div by ID"""
    pattern = rf'(<div class="window[^"]*" id="{window_id}".*?</div>\s*</div>)'
    match = re.search(pattern, html_content, re.DOTALL)
    if match:
        return match.group(1)
    return ""

def extract_taskbar(html_content):
    """Extract taskbar HTML"""
    match = re.search(
        r'(<div class="taskbar">.*?</div>)',
        html_content,
        re.DOTALL
    )
    if match:
        return match.group(1)
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
    """Extract the JavaScript code from <script> tags (excluding src scripts)"""
    # Find all script tags that don't have src attribute
    scripts = []
    pattern = r'<script[^>]*(?<!/)>([^<]*(?:<(?!/script>)[^<]*)*)</script>'
    for match in re.finditer(pattern, html_content, re.DOTALL):
        script_content = match.group(1).strip()
        # Skip empty scripts and script that sets schema-markup
        if script_content and 'schema-markup' not in match.group(0):
            # Skip the posts.js reference and JSON-LD
            if 'src=' not in match.group(0) and '@context' not in script_content:
                scripts.append(script_content)
    return '\n'.join(scripts) if scripts else ""

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
    
    # Replace window content placeholders with actual content
    blog_window_modified = blog_window.replace(
        '<div class="window-content">',
        f'<div class="window-content">{blog_posts_html}',
        1
    )
    archives_window_modified = archives_window.replace(
        '<div class="window-content">',
        f'<div class="window-content">{archives_html}',
        1
    )
    
    # Remove post-window since it's only for individual posts
    post_window = extract_window_html(html_content, 'post-window')
    
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
    <div id="boot-animation" style="display:none;">
        <div class="boot-screen">
            <div class="boot-content">
                <div class="windows-logo"></div>
                <div class="boot-text">Windows 95</div>
            </div>
        </div>
    </div>

    <div class="desktop-container">
        <div class="desktop-area">
            {desktop_icons}
            <div class="windows-container">
                {blog_window_modified}
                {about_window}
                {archives_window_modified}
            </div>
        </div>
        {taskbar}
    </div>

    <div class="mobile-container">
        <div class="mobile-header">
            <h1>404 Memory Found</h1>
            <p>Windows 95 nostalgia blog</p>
        </div>
        <div class="mobile-content">
            <ul class="mobile-post-list">
"""
    
    # Add mobile posts
    for post in posts:
        slug = get_slug_from_id(post['id'])
        html += f"""                <li class="mobile-post-item" onclick="window.location.href='/posts/{slug}.html'">
                    <h3>{post['title']}</h3>
                    <div class="mobile-post-date">{post['date']}</div>
                    <div class="mobile-post-excerpt">{post['excerpt']}</div>
                </li>
"""
    
    html += """            </ul>
        </div>
        <div class="mobile-footer">
            <p>© 2026 404 Memory Found</p>
            <p class="mobile-tagline">Retro computing nostalgia with a Windows 95 aesthetic</p>
        </div>
    </div>

    <script>
"""
    html += javascript
    html += """
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
    post_window = f'''<div class="window" id="post-window" style="left:150px;top:20px;width:650px;height:500px;display:block;">
                <div class="window-title" onmousedown="startDrag(event, 'post-window')">
                    <span>{post['title']}</span>
                    <div class="window-buttons">
                        <button class="window-button" onclick="minimizeWindow('post-window')">_</button>
                        <button class="window-button" onclick="toggleMaximizeWindow('post-window')">□</button>
                        <button class="window-button" onclick="closeWindow('post-window'); window.location.href='/'">×</button>
                    </div>
                </div>
                <div class="window-content">
                    {post_content}
                </div>
            </div>'''
    
    post_schema = generate_post_schema(post, slug)
    
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
    <div id="boot-animation" style="display:none;">
        <div class="boot-screen">
            <div class="boot-content">
                <div class="windows-logo"></div>
                <div class="boot-text">Windows 95</div>
            </div>
        </div>
    </div>

    <div class="desktop-container">
        <div class="desktop-area">
            {desktop_icons}
            <div class="windows-container">
                {post_window}
                {blog_window_modified}
                {about_window}
                {archives_window}
            </div>
        </div>
        {taskbar}
    </div>

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
"""
    
    for related_post in related_posts:
        related_slug = get_slug_from_id(related_post['id'])
        html += f'                        <li style="padding:5px 0;"><a href="/posts/{related_slug}.html">{related_post["title"]}</a></li>\n'
    
    html += f"""                    </ul>
                </div>
                <div style="margin:10px 0;"><a href="/" style="padding:5px 10px;background:#c0c0c0;color:#000;text-decoration:none;display:inline-block;">← Back to Blog</a></div>
            </article>
        </div>
        <div class="mobile-footer">
            <p>© 2026 404 Memory Found</p>
            <p style="font-size:10px;margin-top:8px;">Posted on {post['date']} by {post['author']}</p>
        </div>
    </div>

    <script>
"""
    html += javascript
    html += """
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
