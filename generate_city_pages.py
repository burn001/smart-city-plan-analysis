#!/usr/bin/env python3
"""37개 도시별 상세 HTML 페이지 생성 스크립트."""
import csv, os, json
from collections import Counter

BASE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(BASE, 'data')
OUT = os.path.join(BASE, 'city')
os.makedirs(OUT, exist_ok=True)

# ── 데이터 로드 ──
def load_csv(name):
    with open(os.path.join(DATA, name), encoding='utf-8-sig') as f:
        return list(csv.DictReader(f))

services = load_csv('master_services.csv')
geo = {r['city']: r for r in load_csv('geo_context.csv')}
ware = {r['city']: r for r in load_csv('4ware_scores.csv')}

# 도시별 서비스 그룹핑
city_services = {}
for s in services:
    city_services.setdefault(s['city'], []).append(s)

cities = sorted(city_services.keys())

FIELD_COLORS = {
    'F01':'#0891b2','F02':'#06b6d4','F03':'#14b8a6','F04':'#10b981',
    'F05':'#f59e0b','F06':'#f97316','F07':'#ef4444','F08':'#ec4899',
    'F09':'#8b5cf6','F10':'#6366f1','F11':'#94a3b8'
}
FIELD_NAMES = {
    'F01':'행정','F02':'교통','F03':'보건의료복지','F04':'환경에너지수자원',
    'F05':'방범방재','F06':'시설물관리','F07':'교육','F08':'문화관광스포츠',
    'F09':'물류','F10':'근로고용','F11':'주거'
}
STATUS_COLORS = {'완료':'#10b981','추진중':'#f59e0b','미추진':'#ef4444'}

def esc(s):
    return (s or '').replace('&','&amp;').replace('<','&lt;').replace('>','&gt;').replace('"','&quot;')

def generate_page(city, svc_list):
    g = geo.get(city, {})
    w = ware.get(city, {})
    src = svc_list[0].get('source_type','')
    total = len(svc_list)
    ai_count = sum(1 for s in svc_list if s.get('ai_real')=='Y')
    ai_pct = f"{ai_count/total*100:.1f}" if total else "0"

    # 이행 현황 (이행실적만)
    statuses = Counter(s.get('status','') for s in svc_list)
    completed = statuses.get('완료',0) + statuses.get('완료(기완료)',0)
    in_prog = statuses.get('추진중',0)
    not_started = statuses.get('미추진',0)
    comp_pct = f"{completed/total*100:.1f}" if total else "-"

    # 분야별
    field_cnt = Counter(s.get('field_code','') for s in svc_list)
    field_labels = [FIELD_NAMES.get(k,k) for k in sorted(field_cnt.keys())]
    field_values = [field_cnt[k] for k in sorted(field_cnt.keys())]
    field_colors = [FIELD_COLORS.get(k,'#94a3b8') for k in sorted(field_cnt.keys())]

    # 4-Ware
    hw = w.get('hw_score','?')
    sw = w.get('sw_score','?')
    hu = w.get('human_score','?')
    og = w.get('org_score','?')
    avg_4w = w.get('avg_score','?')

    # Nav
    idx = cities.index(city)
    prev_city = cities[idx-1] if idx > 0 else None
    next_city = cities[idx+1] if idx < len(cities)-1 else None

    # 미추진 사유
    delay_cnt = Counter()
    for s in svc_list:
        dc = s.get('delay_code','')
        if dc:
            delay_cnt[dc] += 1

    # 서비스 테이블 rows
    table_rows = []
    for s in svc_list:
        ai_badge = '<span class="tag tag-ai">AI</span>' if s.get('ai_real')=='Y' else ''
        st = s.get('status','')
        st_color = STATUS_COLORS.get(st, '#94a3b8')
        budget = s.get('budget','')
        try:
            budget_str = f"{float(budget):,.0f}" if budget and budget not in ('','미기재') else '-'
        except ValueError:
            budget_str = budget
        rate = s.get('exec_rate','')
        try:
            rate_str = f"{float(rate.rstrip('*')):.0f}%" if rate and rate not in ('','미기재') else '-'
        except ValueError:
            rate_str = rate
        delay = esc(s.get('delay_reason',''))
        note = esc(s.get('note',''))
        fname = FIELD_NAMES.get(s.get('field_code',''),'')

        table_rows.append(f'''<tr>
<td class="num-cell">{s.get('no','')}</td>
<td class="svc-name">{esc(s.get('service_name',''))} {ai_badge}</td>
<td><span class="tag-field">{fname}</span></td>
<td class="num-cell">{budget_str}</td>
<td class="num-cell">{rate_str}</td>
<td><span class="status-dot" style="background:{st_color}"></span>{st}</td>
<td class="delay-cell">{delay}</td>
<td class="note-cell">{note}</td>
</tr>''')

    pop = g.get('population','')
    pop_str = f"{int(pop):,}명" if pop else '-'
    city_type = g.get('city_type','')
    region = g.get('region','')

    html = f'''<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{city} - 스마트도시 서비스 상세</title>
<script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.1/dist/chart.umd.min.js"></script>
<style>
:root {{
  --bg:#f0f4f8; --surface:#fff; --surface2:#e2e8f0;
  --header-bg:#0f2b46; --text:#1a202c; --text2:#64748b; --text3:#94a3b8;
  --accent:#0891b2; --green:#10b981; --yellow:#f59e0b; --red:#ef4444;
  --purple:#8b5cf6; --border:#e2e8f0; --shadow:0 1px 3px rgba(0,0,0,0.08); --radius:12px;
}}
* {{ margin:0; padding:0; box-sizing:border-box; }}
body {{ font-family:'Pretendard','Segoe UI',system-ui,sans-serif; background:var(--bg); color:var(--text); line-height:1.6; }}

.header {{ background:linear-gradient(135deg,#0f2b46 0%,#164e63 100%); color:#fff; padding:32px 0 24px; }}
.header-inner {{ max-width:1200px; margin:0 auto; padding:0 24px; }}
.header h1 {{ font-size:1.6rem; font-weight:800; margin-bottom:4px; }}
.header .meta {{ color:#94a3b8; font-size:0.85rem; display:flex; gap:16px; flex-wrap:wrap; margin-bottom:16px; }}
.stat-bar {{ display:flex; gap:10px; flex-wrap:wrap; }}
.stat-pill {{ background:rgba(255,255,255,0.1); border:1px solid rgba(255,255,255,0.15); border-radius:99px; padding:6px 16px; font-size:0.82rem; font-weight:600; }}
.stat-pill .num {{ color:#38bdf8; }}

.nav-bar {{ background:var(--surface); border-bottom:1px solid var(--border); padding:10px 0; position:sticky; top:0; z-index:10; }}
.nav-inner {{ max-width:1200px; margin:0 auto; padding:0 24px; display:flex; justify-content:space-between; align-items:center; font-size:0.82rem; }}
.nav-inner a {{ color:var(--accent); text-decoration:none; font-weight:600; }}
.nav-inner a:hover {{ text-decoration:underline; }}

.container {{ max-width:1200px; margin:0 auto; padding:24px; }}
.section {{ margin-bottom:28px; }}
.section-title {{ font-size:1.05rem; font-weight:700; color:var(--header-bg); margin-bottom:14px; padding-left:10px; border-left:4px solid var(--accent); }}

.card {{ background:var(--surface); border-radius:var(--radius); padding:20px; box-shadow:var(--shadow); border:1px solid var(--border); }}
.card-title {{ font-size:0.8rem; font-weight:600; color:var(--text2); text-transform:uppercase; letter-spacing:0.04em; margin-bottom:12px; }}
.grid-2 {{ display:grid; grid-template-columns:1fr 1fr; gap:16px; }}
.grid-4 {{ display:grid; grid-template-columns:repeat(4,1fr); gap:12px; }}
@media(max-width:900px) {{ .grid-2,.grid-4 {{ grid-template-columns:1fr; }} }}

.mini-stat {{ text-align:center; padding:16px 12px; }}
.mini-stat .big {{ font-size:1.8rem; font-weight:800; line-height:1.1; }}
.mini-stat .label {{ font-size:0.72rem; color:var(--text2); margin-top:4px; }}

.ware-grid {{ display:grid; grid-template-columns:repeat(4,1fr); gap:12px; margin-bottom:12px; }}
.ware-item {{ text-align:center; padding:14px 8px; background:var(--bg); border-radius:8px; }}
.ware-item .score {{ font-size:1.6rem; font-weight:800; }}
.ware-item .wlabel {{ font-size:0.72rem; color:var(--text2); margin-top:2px; }}

/* Table */
.tbl-wrap {{ overflow-x:auto; }}
.svc-table {{ width:100%; border-collapse:collapse; font-size:0.78rem; }}
.svc-table th {{ text-align:left; padding:8px 10px; font-weight:600; color:var(--text2); font-size:0.7rem; text-transform:uppercase; border-bottom:2px solid var(--border); background:#f8fafc; position:sticky; top:0; }}
.svc-table td {{ padding:8px 10px; border-bottom:1px solid var(--border); vertical-align:top; }}
.svc-table tr:hover td {{ background:#f0fdfa; }}
.num-cell {{ text-align:right; font-variant-numeric:tabular-nums; }}
.svc-name {{ font-weight:600; min-width:180px; }}
.delay-cell,.note-cell {{ max-width:220px; font-size:0.72rem; color:var(--text2); word-break:keep-all; }}
.tag-ai {{ display:inline-block; padding:1px 6px; border-radius:3px; font-size:0.65rem; font-weight:700; background:#dbeafe; color:#1d4ed8; margin-left:4px; vertical-align:middle; }}
.tag-field {{ display:inline-block; padding:1px 6px; border-radius:3px; font-size:0.68rem; font-weight:600; background:#f0fdfa; color:#0d9488; white-space:nowrap; }}
.status-dot {{ display:inline-block; width:8px; height:8px; border-radius:50%; margin-right:4px; vertical-align:middle; }}

.search-box {{ width:100%; padding:8px 12px; border:1px solid var(--border); border-radius:8px; font-size:0.82rem; margin-bottom:12px; }}
.search-box:focus {{ outline:none; border-color:var(--accent); }}

.filter-bar {{ display:flex; gap:8px; margin-bottom:12px; flex-wrap:wrap; }}
.filter-btn {{ padding:4px 12px; border:1px solid var(--border); border-radius:6px; font-size:0.72rem; cursor:pointer; background:var(--surface); color:var(--text2); font-weight:600; }}
.filter-btn.active {{ background:var(--accent); color:#fff; border-color:var(--accent); }}

footer {{ text-align:center; padding:24px; color:var(--text3); font-size:0.72rem; border-top:1px solid var(--border); margin-top:16px; }}
footer a {{ color:var(--accent); text-decoration:none; }}
</style>
</head>
<body>

<div class="header">
  <div class="header-inner">
    <h1>{city}</h1>
    <div class="meta">
      <span>{region} / {city_type}</span>
      <span>인구 {pop_str}</span>
      <span>소스: {src}</span>
    </div>
    <div class="stat-bar">
      <div class="stat-pill"><span class="num">{total}</span>건 서비스</div>
      <div class="stat-pill"><span class="num">{ai_count}</span>건 AI ({ai_pct}%)</div>
      <div class="stat-pill"><span class="num">{comp_pct}%</span> 완료율</div>
      <div class="stat-pill">4-Ware <span class="num">{avg_4w}</span></div>
    </div>
  </div>
</div>

<div class="nav-bar">
  <div class="nav-inner">
    <div>{"<a href=\""+prev_city+".html\">&larr; "+prev_city+"</a>" if prev_city else "<span></span>"}</div>
    <a href="../index.html">&#x1F3E0; 대시보드</a>
    <div>{"<a href=\""+next_city+".html\">"+next_city+" &rarr;</a>" if next_city else "<span></span>"}</div>
  </div>
</div>

<div class="container">

<!-- 기본정보 + 4-Ware -->
<div class="section">
  <h2 class="section-title">기본 현황</h2>
  <div class="grid-2">
    <div class="card">
      <div class="card-title">이행 현황</div>
      <div class="grid-4" style="margin-bottom:12px;">
        <div class="mini-stat"><div class="big" style="color:var(--accent);">{total}</div><div class="label">전체</div></div>
        <div class="mini-stat"><div class="big" style="color:var(--green);">{completed}</div><div class="label">완료</div></div>
        <div class="mini-stat"><div class="big" style="color:var(--yellow);">{in_prog}</div><div class="label">추진중</div></div>
        <div class="mini-stat"><div class="big" style="color:var(--red);">{not_started}</div><div class="label">미추진</div></div>
      </div>
      <div style="height:24px;background:var(--surface2);border-radius:4px;overflow:hidden;display:flex;">
        <div style="width:{completed/total*100 if total else 0:.1f}%;background:var(--green);"></div>
        <div style="width:{in_prog/total*100 if total else 0:.1f}%;background:var(--yellow);"></div>
        <div style="width:{not_started/total*100 if total else 0:.1f}%;background:var(--red);"></div>
      </div>
    </div>
    <div class="card">
      <div class="card-title">4-Ware 성숙도</div>
      <div class="ware-grid">
        <div class="ware-item"><div class="score" style="color:var(--accent);">{hw}</div><div class="wlabel">Hardware</div></div>
        <div class="ware-item"><div class="score" style="color:var(--green);">{sw}</div><div class="wlabel">Software</div></div>
        <div class="ware-item"><div class="score" style="color:var(--yellow);">{hu}</div><div class="wlabel">Human</div></div>
        <div class="ware-item"><div class="score" style="color:var(--red);">{og}</div><div class="wlabel">Orgware</div></div>
      </div>
      <div style="text-align:center;font-size:0.82rem;color:var(--text2);">평균 <strong style="color:var(--accent);font-size:1.1rem;">{avg_4w}</strong> / 4.0</div>
    </div>
  </div>
</div>

<!-- 차트 -->
<div class="section">
  <h2 class="section-title">분야별 분포</h2>
  <div class="grid-2">
    <div class="card">
      <div class="card-title">11개 법정 분야</div>
      <div style="max-width:280px;margin:0 auto;"><canvas id="chartField"></canvas></div>
    </div>
    <div class="card">
      <div class="card-title">이행 상태</div>
      <div style="max-width:280px;margin:0 auto;"><canvas id="chartStatus"></canvas></div>
    </div>
  </div>
</div>

<!-- 서비스 목록 -->
<div class="section">
  <h2 class="section-title">서비스 목록 ({total}건)</h2>
  <div class="card">
    <input type="text" class="search-box" id="searchInput" placeholder="서비스명, 분야, 상태로 검색...">
    <div class="filter-bar" id="filterBar">
      <button class="filter-btn active" data-filter="all">전체</button>
      <button class="filter-btn" data-filter="ai">AI만</button>
      <button class="filter-btn" data-filter="완료">완료</button>
      <button class="filter-btn" data-filter="추진중">추진중</button>
      <button class="filter-btn" data-filter="미추진">미추진</button>
    </div>
    <div class="tbl-wrap">
      <table class="svc-table" id="svcTable">
        <thead>
          <tr>
            <th>No</th><th>서비스명</th><th>분야</th><th>예산(백만)</th><th>이행률</th><th>상태</th><th>미추진 사유</th><th>비고</th>
          </tr>
        </thead>
        <tbody>
          {"".join(table_rows)}
        </tbody>
      </table>
    </div>
  </div>
</div>

</div><!-- container -->

<footer>
  <a href="../index.html">&#x1F3E0; 대시보드로 돌아가기</a> |
  데이터 기준일: 2026-03-04 | {city} 상세 페이지
</footer>

<script>
// Field chart
new Chart(document.getElementById('chartField'), {{
  type:'doughnut',
  data:{{
    labels:{json.dumps(field_labels, ensure_ascii=False)},
    datasets:[{{ data:{json.dumps(field_values)}, backgroundColor:{json.dumps(field_colors)}, borderWidth:2, borderColor:'#fff' }}]
  }},
  options:{{ responsive:true, cutout:'50%', plugins:{{ legend:{{ position:'bottom', labels:{{ font:{{ size:10 }}, padding:8 }} }} }} }}
}});

// Status chart
const statusData = [
  {completed}, {in_prog}, {not_started},
  {total - completed - in_prog - not_started}
];
const statusLabels = ['완료','추진중','미추진','기타'];
const statusColors = ['#10b981','#f59e0b','#ef4444','#94a3b8'];
new Chart(document.getElementById('chartStatus'), {{
  type:'doughnut',
  data:{{
    labels: statusLabels.filter((_,i) => statusData[i]>0),
    datasets:[{{ data: statusData.filter(v=>v>0), backgroundColor: statusColors.filter((_,i)=>statusData[i]>0), borderWidth:2, borderColor:'#fff' }}]
  }},
  options:{{ responsive:true, cutout:'50%', plugins:{{ legend:{{ position:'bottom', labels:{{ font:{{ size:10 }}, padding:8 }} }} }} }}
}});

// Search & filter
const searchInput = document.getElementById('searchInput');
const table = document.getElementById('svcTable');
const rows = table.querySelectorAll('tbody tr');
const filterBtns = document.querySelectorAll('.filter-btn');
let activeFilter = 'all';

function applyFilters() {{
  const q = searchInput.value.toLowerCase();
  rows.forEach(row => {{
    const text = row.textContent.toLowerCase();
    const matchSearch = !q || text.includes(q);
    let matchFilter = true;
    if (activeFilter === 'ai') matchFilter = row.innerHTML.includes('tag-ai');
    else if (activeFilter !== 'all') {{
      const statusCell = row.cells[5]?.textContent.trim();
      matchFilter = statusCell === activeFilter;
    }}
    row.style.display = (matchSearch && matchFilter) ? '' : 'none';
  }});
}}

searchInput.addEventListener('input', applyFilters);
filterBtns.forEach(btn => {{
  btn.addEventListener('click', () => {{
    filterBtns.forEach(b => b.classList.remove('active'));
    btn.classList.add('active');
    activeFilter = btn.dataset.filter;
    applyFilters();
  }});
}});
</script>
</body>
</html>'''
    return html


# ── 생성 ──
for city in cities:
    html = generate_page(city, city_services[city])
    path = os.path.join(OUT, f'{city}.html')
    with open(path, 'w', encoding='utf-8') as f:
        f.write(html)
    print(f'  {city} ({len(city_services[city])}건)')

print(f'\n완료: {len(cities)}개 도시 페이지 → {OUT}/')
