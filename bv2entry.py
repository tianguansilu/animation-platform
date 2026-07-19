#!/usr/bin/env python3
"""
B站 BV→作品条目 转换脚本
用法: python bv2entry.py BV1Ai421f7zF
输出: 可直接粘贴到 HTML WORKS 数组的 JS 代码
"""
import sys, json, urllib.request, datetime, re, os

def bv_to_entry(bvid):
    url = f"https://api.bilibili.com/x/web-interface/view?bvid={bvid}"
    req = urllib.request.Request(url, headers={
        'Referer': 'https://www.bilibili.com/',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'
    })
    resp = urllib.request.urlopen(req, timeout=15)
    d = json.loads(resp.read())
    if d['code'] != 0:
        return None, f"API Error: {d}"
    
    v = d['data']
    raw_title = v['title']
    owner = v['owner']['name'] if v.get('owner') else ''
    duration = v['duration']
    dur = f"{duration//60}:{duration%60:02d}"
    pubdate = datetime.datetime.fromtimestamp(v['pubdate'])
    year = pubdate.year
    pic = v['pic'].replace('http://', 'https://')  # force HTTPS
    desc = v['desc'] or ''
    
    # Clean title: remove 【】 brackets content as auxiliary, keep main title
    bracket_items = re.findall(r'【([^】]+)】', raw_title)
    clean = re.sub(r'【[^】]+】', '', raw_title).strip()
    
    # Try to detect director from UP主 name or description
    director = owner if owner else ''
    
    # Guess group/category from title and description
    group = 'festival'  # default
    
    school_map = {
        '东京艺术大学': 'geidai', '東京藝術大学': 'geidai', '东艺大': 'geidai',
        '多摩美术大学': 'tama', '多摩美術大学': 'tama',
        '京都精华大学': 'seika', '京都精華大学': 'seika',
        '东京造形大学': 'zokei', '東京造形大学': 'zokei',
        'Gobelins': 'gobelins', 'GOBELINS': 'gobelins',
        'CalArts': 'calarts', 'CALARTS': 'calarts',
        '中国传媒大学': 'other', '北京电影学院': 'other',
    }
    all_text = raw_title + ' ' + desc
    for school, g in school_map.items():
        if school in all_text:
            group = g
            break
    
    # Detect technique from description
    tech_hints = {
        '2D': '2D 手绘', '手绘': '2D 手绘', '3D': '3D CGI', 'CGI': '3D CGI',
        'CG': '3D CGI', '定格': '定格动画', '实验': '实验动画',
        '水彩': '水彩动画', '水墨': '水墨动画', '剪纸': '剪纸动画',
    }
    technique = ''
    for kw, t in tech_hints.items():
        if kw in desc or kw in raw_title:
            technique = t
            break
    
    # Detect country
    country_hints = {
        '日本': '日本', '中国': '中国', '美国': '美国', '法国': '法国',
        '英国': '英国', '韩国': '韩国', '伊朗': '伊朗', '加拿大': '加拿大',
        '俄罗斯': '俄罗斯', '智利': '智利',
    }
    country = ''
    for kw, c in country_hints.items():
        if kw in all_text:
            country = c
            break
    
    # Tags
    tags = [str(year)]
    if group != 'festival':
        tags.append({'geidai':'东京艺大','tama':'多摩美术','seika':'京都精华',
                     'zokei':'东造形大','gobelins':'Gobelins','calarts':'CalArts'}.get(group, ''))
    tags.append('B站')
    if technique:
        tags.append(technique)
    tags = [t for t in tags if t]
    
    # Build entry
    sq = chr(39)  # single quote
    bs = chr(92)  # backslash
    esc = lambda s: s.replace(sq, bs+sq)
    desc_clean = desc[:200].replace(chr(10), chr(32))
    tags_str = ','.join(f"'{t}'" for t in tags)
    entry = f"""  {{
    id: 'auto-{bvid.lower()}',
    title: '{esc(clean)}',
    titleEn: '{esc(clean)}',
    director: '{esc(director)}',
    year: {year}, group: '{group}',
    technique: '{technique}',
    country: '{country}',
    duration: '{dur}',
    description: '{esc(desc[:200].replace(chr(10), chr(32)))}',
    bvid: '{bvid}',
    bcover: '{pic}',
    tags: [{tags_str}]
  }},"""
    
    return entry, None

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Usage: python bv2entry.py BVxxxxxxxx")
        sys.exit(1)
    
    bvid = sys.argv[1].strip()
    if not bvid.startswith('BV'):
        print("Not a B站 BV number")
        sys.exit(1)
    
    entry, err = bv_to_entry(bvid)
    if err:
        print(f"Error: {err}")
        sys.exit(1)
    
    print(entry)
    nl = chr(10)
    print(f"\n# 检测到：标题={entry.split(nl)[2].split(':')[-1].strip().strip(chr(39))}")
