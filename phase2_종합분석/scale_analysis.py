import csv, statistics, math, collections, json

BASE = "output/data"

def read_csv(name):
    with open(f"{BASE}/{name}", encoding="utf-8-sig") as f:
        return list(csv.DictReader(f))

# Load all data
master = read_csv("master_services.csv")
field_sum = read_csv("field_summary.csv")
ai_sum = read_csv("ai_summary.csv")
delay_sum = read_csv("delay_summary.csv")
ware_sum = read_csv("4ware_scores.csv")
geo = read_csv("geo_context.csv")
infra = read_csv("infra_counts.csv")

# Build city_type map
city_type_map = {r['city']: r['city_type'] for r in geo}
pop_map = {r['city']: int(r['population']) for r in geo}
source_map = {r['city']: r['source_type'] for r in ai_sum}

types_order = ['광역', '대도시', '중소도시', '소도시', '농어촌']
type_cities = {t: [c for c, ct in city_type_map.items() if ct == t] for t in types_order}

results = {}

# Print cities per type
for t in types_order:
    print(f"{t} ({len(type_cities[t])}): {', '.join(sorted(type_cities[t]))}")

# ===== AXIS 1: 사업 규모 =====
print("\n=== AXIS 1: 사업 규모 ===")
budget_by_city = collections.defaultdict(float)
svc_count_by_city = collections.defaultdict(int)
for r in master:
    city = r['city']
    svc_count_by_city[city] += 1
    if r.get('source_type') == '이행실적' and r.get('budget', ''):
        try:
            budget_by_city[city] += float(r['budget'])
        except:
            pass

axis1 = {}
for t in types_order:
    cities = type_cities[t]
    avg_svc = statistics.mean([svc_count_by_city[c] for c in cities])
    budget_cities = [c for c in cities if source_map.get(c) == '이행실적']
    if budget_cities:
        avg_budget = statistics.mean([budget_by_city[c] for c in budget_cities])
        avg_per_svc = statistics.mean([budget_by_city[c]/svc_count_by_city[c] if svc_count_by_city[c] > 0 else 0 for c in budget_cities])
    else:
        avg_budget = None
        avg_per_svc = None
    axis1[t] = {'avg_svc': avg_svc, 'avg_budget': avg_budget, 'avg_per_svc': avg_per_svc}
    bstr = f"{avg_budget:.1f}" if avg_budget is not None else "N/A"
    pstr = f"{avg_per_svc:.1f}" if avg_per_svc is not None else "N/A"
    print(f"{t}: 평균사업수={avg_svc:.1f}, 평균예산={bstr}백만원, 건당예산={pstr}백만원")
    for c in sorted(cities):
        b = f"{budget_by_city[c]:.0f}" if budget_by_city[c] > 0 else '-'
        print(f"  {c}: 사업수={svc_count_by_city[c]}, 예산={b}")

# ===== AXIS 2: HHI =====
print("\n=== AXIS 2: HHI 편중도 ===")
fields = ['F01','F02','F03','F04','F05','F06','F07','F08','F09','F10','F11']
field_names = {'F01':'행정','F02':'교통','F03':'보건의료복지','F04':'환경에너지수자원',
               'F05':'방범방재','F06':'시설물관리','F07':'교육','F08':'문화관광스포츠',
               'F09':'물류','F10':'산업경제','F11':'주거'}
hhi_by_city = {}
for r in field_sum:
    city = r['city']
    total = int(r['total'])
    if total == 0:
        hhi_by_city[city] = None
        continue
    hhi = sum((int(r[f])/total)**2 for f in fields)
    hhi_by_city[city] = hhi

axis2 = {}
for t in types_order:
    cities = type_cities[t]
    hhis = [hhi_by_city[c] for c in cities if hhi_by_city[c] is not None]
    avg_hhi = statistics.mean(hhis) if hhis else None
    axis2[t] = {'avg_hhi': avg_hhi}
    if avg_hhi:
        print(f"{t}: 평균HHI={avg_hhi:.4f}")
    else:
        print(f"{t}: N/A")
    for c in sorted(cities):
        h = hhi_by_city[c]
        if h:
            print(f"  {c}: HHI={h:.4f}")
        else:
            print(f"  {c}: N/A")

print("\n주요 분야 비중 (type별):")
type_field_shares = {}
for t in types_order:
    cities_set = set(type_cities[t])
    field_totals = {f: 0 for f in fields}
    grand_total = 0
    for r in field_sum:
        if r['city'] in cities_set:
            for f in fields:
                field_totals[f] += int(r[f])
            grand_total += int(r['total'])
    if grand_total > 0:
        shares = {f: field_totals[f]/grand_total*100 for f in fields}
        top3 = sorted(fields, key=lambda f: field_totals[f], reverse=True)[:3]
        parts = [f"{field_names[f]}({field_totals[f]}/{grand_total}, {shares[f]:.1f}%)" for f in top3]
        type_field_shares[t] = {field_names[f]: round(shares[f], 1) for f in fields}
        type_field_shares[t]['top3'] = [(field_names[f], round(shares[f], 1)) for f in top3]
        print(f"  {t}: {', '.join(parts)}")

# ===== AXIS 3: AI =====
print("\n=== AXIS 3: AI 서비스 비율 ===")
ai_map = {r['city']: {'real': int(r['ai_real_count']), 'ratio': float(r['ai_real_ratio']), 'total': int(r['total_services'])} for r in ai_sum}
axis3 = {}
for t in types_order:
    cities = type_cities[t]
    ratios = [ai_map[c]['ratio'] for c in cities]
    total_ai = sum(ai_map[c]['real'] for c in cities)
    total_svc = sum(ai_map[c]['total'] for c in cities)
    avg_ratio = statistics.mean(ratios)
    axis3[t] = {'avg_ratio': avg_ratio, 'total_ai': total_ai, 'total_svc': total_svc}
    print(f"{t}: 평균AI비율={avg_ratio:.1f}%, 총AI건수={total_ai}, 총사업수={total_svc}")
    for c in sorted(cities):
        print(f"  {c}: AI={ai_map[c]['real']}/{ai_map[c]['total']} ({ai_map[c]['ratio']}%)")

# ===== AXIS 4: 이행률 =====
print("\n=== AXIS 4: 이행률 ===")
delay_map = {}
delay_codes = ['D01','D02','D03','D04','D05','D06','D07']
delay_names_map = {'D01':'예산미확보','D02':'기술부족','D03':'협력부재','D04':'수요변경','D05':'유사대체','D06':'정책변경','D07':'기타'}
for r in delay_sum:
    delay_map[r['city']] = r

axis4 = {}
for t in types_order:
    cities = type_cities[t]
    ih_cities = [c for c in cities if c in delay_map]
    if not ih_cities:
        axis4[t] = None
        print(f"{t}: 이행실적 도시 없음")
        continue
    comp_rates = [float(delay_map[c]['completion_rate']) for c in ih_cities]
    not_started_rates = [int(delay_map[c]['not_started'])/int(delay_map[c]['total'])*100 for c in ih_cities]
    avg_comp = statistics.mean(comp_rates)
    avg_nostart = statistics.mean(not_started_rates)
    dc_totals = {d: sum(int(delay_map[c][d]) for c in ih_cities) for d in delay_codes}
    top_dc = sorted(delay_codes, key=lambda d: dc_totals[d], reverse=True)[:3]
    dc_str = ', '.join([f"{delay_names_map[d]}({dc_totals[d]}건)" for d in top_dc if dc_totals[d] > 0])
    axis4[t] = {'avg_comp': avg_comp, 'avg_nostart': avg_nostart, 'delay_top': dc_str, 'n': len(ih_cities)}
    print(f"{t}: 평균완료율={avg_comp:.1f}%, 평균미추진율={avg_nostart:.1f}%, 주요지연=[{dc_str}]")
    for c in sorted(ih_cities):
        r = delay_map[c]
        print(f"  {c}: 완료율={r['completion_rate']}%, 미추진={r['not_started']}/{r['total']}")

# ===== AXIS 5: 4-Ware =====
print("\n=== AXIS 5: 4-Ware 성숙도 ===")
ware_map = {r['city']: r for r in ware_sum}
axis5 = {}
for t in types_order:
    cities = type_cities[t]
    hw = statistics.mean([float(ware_map[c]['hw_score']) for c in cities])
    sw = statistics.mean([float(ware_map[c]['sw_score']) for c in cities])
    hu = statistics.mean([float(ware_map[c]['human_score']) for c in cities])
    org = statistics.mean([float(ware_map[c]['org_score']) for c in cities])
    avg = statistics.mean([float(ware_map[c]['avg_score']) for c in cities])
    tech = (hw + sw) / 2
    inst = (hu + org) / 2
    gap = tech - inst
    axis5[t] = {'hw': hw, 'sw': sw, 'human': hu, 'org': org, 'avg': avg, 'gap': gap}
    print(f"{t}: HW={hw:.2f}, SW={sw:.2f}, Human={hu:.2f}, Org={org:.2f}, 평균={avg:.2f}, gap={gap:.2f}")

# ===== AXIS 6: 인프라 밀도 =====
print("\n=== AXIS 6: 인프라 밀도 ===")
infra_map = {r['city']: int(r['total_infra']) for r in infra}
axis6 = {}
for t in types_order:
    cities = type_cities[t]
    avg_infra = statistics.mean([infra_map.get(c, 0) for c in cities])
    densities = [infra_map.get(c, 0) / pop_map[c] * 10000 for c in cities]
    avg_density = statistics.mean(densities)
    axis6[t] = {'avg_infra': avg_infra, 'avg_density': avg_density}
    print(f"{t}: 평균인프라={avg_infra:.1f}개, 만명당={avg_density:.1f}개")
    for c in sorted(cities):
        inf = infra_map.get(c, 0)
        dens = inf / pop_map[c] * 10000
        print(f"  {c}: 인프라={inf}, 만명당={dens:.1f}")

# ===== OUTLIERS =====
print("\n=== 이상치 분석 ===")
def find_outliers(metric_map, label):
    outliers = []
    for t in types_order:
        cities = type_cities[t]
        vals = [(c, metric_map.get(c)) for c in cities if metric_map.get(c) is not None]
        if len(vals) < 3:
            continue
        mean_v = statistics.mean([v for _, v in vals])
        stdev_v = statistics.stdev([v for _, v in vals]) if len(vals) > 1 else 0
        if stdev_v == 0:
            continue
        for c, v in vals:
            z = (v - mean_v) / stdev_v
            if abs(z) > 1.5:
                direction = "HIGH" if z > 0 else "LOW"
                outliers.append((c, t, label, v, mean_v, z, direction))
    return outliers

all_outliers = []
all_outliers += find_outliers({c: svc_count_by_city[c] for c in city_type_map}, "사업수")
all_outliers += find_outliers(hhi_by_city, "HHI")
all_outliers += find_outliers({c: ai_map[c]['ratio'] for c in ai_map}, "AI비율")
all_outliers += find_outliers({c: float(delay_map[c]['completion_rate']) for c in delay_map}, "완료율")
all_outliers += find_outliers({c: float(ware_map[c]['avg_score']) for c in ware_map}, "4Ware")
all_outliers += find_outliers({c: infra_map.get(c, 0) / pop_map[c] * 10000 for c in city_type_map}, "인프라밀도")

for o in sorted(all_outliers, key=lambda x: abs(x[5]), reverse=True):
    c, t, label, v, mean_v, z, d = o
    print(f"  {d} {c}({t}): {label}={v:.1f} (유형평균={mean_v:.1f}, z={z:.2f})")

# Store all results as JSON for report generation
output = {
    'type_cities': {t: sorted(type_cities[t]) for t in types_order},
    'axis1': axis1,
    'axis2': axis2,
    'axis3': axis3,
    'axis4': axis4,
    'axis5': axis5,
    'axis6': axis6,
    'type_field_shares': type_field_shares,
    'outliers': [(c, t, label, round(v,2), round(mean_v,2), round(z,2), d) for c,t,label,v,mean_v,z,d in all_outliers]
}
with open("output/phase2_종합분석/scale_data.json", "w", encoding="utf-8") as f:
    json.dump(output, f, ensure_ascii=False, indent=2)
print("\nJSON saved.")
