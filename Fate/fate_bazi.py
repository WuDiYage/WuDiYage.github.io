# -*- coding: utf-8 -*-
"""用命主生辰八字排日。

取用只走扶抑：身旺喜克泄耗，身弱喜印比，中和取正神。
日课上的硬禁忌仍由通书判定，命理分高也不能把忌日改成宜。
"""

from datetime import date

import fate


STEMS = "甲乙丙丁戊己庚辛壬癸"
ELEMENTS = ["木", "木", "火", "火", "土", "土", "金", "金", "水", "水"]
HIDE = {
    "子": ("癸",),
    "丑": ("己", "癸", "辛"),
    "寅": ("甲", "丙", "戊"),
    "卯": ("乙",),
    "辰": ("戊", "乙", "癸"),
    "巳": ("丙", "庚", "戊"),
    "午": ("丁", "己"),
    "未": ("己", "丁", "乙"),
    "申": ("庚", "壬", "戊"),
    "酉": ("辛",),
    "戌": ("戊", "辛", "丁"),
    "亥": ("壬", "甲"),
}
YIN = {"正印", "偏印"}
BI = {"比肩", "劫财"}
SHI = {"食神", "伤官"}
CAI = {"正财", "偏财"}
GUAN = {"正官", "七杀"}
HELP = YIN | BI
DRAIN = SHI | CAI | GUAN
ZHENG = {"正印", "食神", "正官", "正财"}
PIAN = {"七杀", "劫财", "伤官"}
GOD_ORDER = ("正印", "偏印", "比肩", "劫财", "食神", "伤官", "正财", "偏财", "正官", "七杀")
ZHI_ANIMAL = {zhi: animal for animal, zhi in fate.SHENGXIAO_TO_ZHI.items()}


def ten_god(day_gan, other_gan):
    """以命主日干看另一个天干的十神。同阴阳为偏，异阴阳为正。"""
    day_index = STEMS.index(day_gan)
    other_index = STEMS.index(other_gan)
    day_element = ELEMENTS[day_index]
    other_element = ELEMENTS[other_index]
    same = (day_index % 2) == (other_index % 2)
    if day_element == other_element:
        return "比肩" if same else "劫财"
    generates = {"木": "火", "火": "土", "土": "金", "金": "水", "水": "木"}
    controls = {"木": "土", "土": "水", "水": "火", "火": "金", "金": "木"}
    if generates[other_element] == day_element:
        return "偏印" if same else "正印"
    if generates[day_element] == other_element:
        return "食神" if same else "伤官"
    if controls[other_element] == day_element:
        return "七杀" if same else "正官"
    return "偏财" if same else "正财"


def _add(lines, total, name, delta):
    if not delta:
        return total
    sign = "+" if delta > 0 else ""
    lines.append(f"{name} {sign}{delta}")
    return total + delta


def _stem_weight(god):
    return 1 if god in HELP else -1


def _hidden_total(zhi, weights, day_gan):
    total = 0
    detail = []
    for index, gan in enumerate(HIDE[zhi]):
        god = ten_god(day_gan, gan)
        delta = weights[index] * _stem_weight(god)
        total += delta
        detail.append(f"{gan}{god}")
    return total, detail


def _preference(band):
    if band == "身旺":
        return DRAIN, HELP
    if band == "身弱":
        return HELP, DRAIN
    return ZHENG, PIAN


def _dayun(eight, gender_code, year):
    yun = eight.getYun(gender_code)
    start = yun.getStartSolar()
    start_text = f"{start.getYear():04d}-{start.getMonth():02d}-{start.getDay():02d}"
    chosen = None
    for item in yun.getDaYun():
        if item.getStartYear() <= year <= item.getEndYear():
            chosen = item
            break
    return {
        "forward": yun.isForward(),
        "start_text": start_text,
        "ganzhi": chosen.getGanZhi() if chosen else "",
        "start_year": chosen.getStartYear() if chosen else 0,
        "end_year": chosen.getEndYear() if chosen else 0,
    }


def build_natal(raw):
    """由出生公历排出命盘、旺衰和喜忌。raw 里要有出生年月日时、性别，以及要排的公历年。"""
    birth = date(int(raw["birth_year"]), int(raw["birth_month"]), int(raw["birth_day"]))
    hour, minute = fate.parse_clock(raw["birth_time"])
    solar = fate.solar_of(birth, hour, minute)
    eight = solar.getLunar().getEightChar()
    eight.setSect(1)
    day_gan = eight.getDayGan()
    day_zhi = eight.getDayZhi()
    year_zhi = eight.getYearZhi()
    month_zhi = eight.getMonthZhi()
    time_zhi = eight.getTimeZhi()
    shi_zhi, late = fate.clock_to_shichen(hour)

    strength = 0
    month_main = HIDE[month_zhi][0]
    month_god = ten_god(day_gan, month_main)
    month_total, _month_detail = _hidden_total(month_zhi, (10, 4, 2), day_gan)
    strength += month_total
    for gan in (eight.getYearGan(), eight.getMonthGan(), eight.getTimeGan()):
        strength += 4 * _stem_weight(ten_god(day_gan, gan))
    year_total, _year_detail = _hidden_total(year_zhi, (4, 2, 1), day_gan)
    day_total, _day_detail = _hidden_total(day_zhi, (8, 3, 1), day_gan)
    time_total, _time_detail = _hidden_total(time_zhi, (4, 2, 1), day_gan)
    strength += year_total + day_total + time_total

    if strength >= 8:
        band = "身旺"
    elif strength <= -8:
        band = "身弱"
    else:
        band = "中和"
    xi, ji = _preference(band)
    command = "得令" if month_god in HELP else "失令"

    gender = raw["gender"]
    gender_code = 1 if gender == "男" else 0
    luck = _dayun(eight, gender_code, int(raw["g_year"]))
    direction = "顺行" if luck["forward"] else "逆行"
    animal = ZHI_ANIMAL[year_zhi]
    gods = [
        ten_god(day_gan, eight.getYearGan()),
        ten_god(day_gan, eight.getMonthGan()),
        ten_god(day_gan, eight.getTimeGan()),
        ten_god(day_gan, month_main),
        ten_god(day_gan, HIDE[year_zhi][0]),
        ten_god(day_gan, HIDE[day_zhi][0]),
        ten_god(day_gan, HIDE[time_zhi][0]),
    ]

    lines = [
        f"{gender}命，公历 {birth.isoformat()} {hour:02d}:{minute:02d}",
    ]
    if late:
        lines.append("出生在晚子时，日柱按次日")
    elif shi_zhi == "子":
        lines.append("出生在早子时，日柱按当日")
    lines.extend([
        f"八字 {eight.getYear()}  {eight.getMonth()}  {eight.getDay()}  {eight.getTime()}",
        f"日主{day_gan}{ELEMENTS[STEMS.index(day_gan)]}，{band}（旺衰分 {strength:+d}，月令本气{month_main}为{month_god}，{command}）",
        "喜用 " + "、".join(name for name in GOD_ORDER if name in xi),
        "忌神 " + "、".join(name for name in GOD_ORDER if name in ji),
    ])
    if luck["ganzhi"]:
        luck_god = ten_god(day_gan, luck["ganzhi"][0])
        side = "喜用" if luck_god in xi else "忌神"
        lines.append(
            f"大运{direction}，{luck['ganzhi']}（{luck['start_year']}-{luck['end_year']}），"
            f"运干{luck['ganzhi'][0]}{luck_god}，属{side}。起运 {luck['start_text']}"
        )
    else:
        lines.append(f"大运未起，起运 {luck['start_text']}")
    lines.append(f"年支{year_zhi}（{animal}）。冲年支仍按这个生肖，另外单看冲日支")
    lines.append("取用是扶抑：身旺喜克泄耗，身弱喜印比，中和取正印、食神、正官、正财。通书大忌不会改成宜。")
    return {
        "birth": birth,
        "gender": gender,
        "animal": animal,
        "day_gan": day_gan,
        "day_zhi": day_zhi,
        "year_zhi": year_zhi,
        "kong": eight.getDayXunKong(),
        "xi": xi,
        "ji": ji,
        "band": band,
        "has_shang": "伤官" in gods,
        "lines": lines,
        "brief": f"{gender}命{day_gan}{ELEMENTS[STEMS.index(day_gan)]}{band}",
    }


def _god_delta(natal, god, weight):
    if god in natal["xi"]:
        return weight
    if god in natal["ji"]:
        return -weight
    return 0


def hour_points(natal, chart, item):
    """这个时辰对命主的加减分。挑时辰时只用这一段，日柱对十二时辰是一样的。"""
    lines = []
    total = 0
    stem_god = ten_god(natal["day_gan"], item["gan"])
    branch_god = ten_god(natal["day_gan"], HIDE[item["zhi"]][0])
    total = _add(lines, total, f"时干{item['gan']}{stem_god}", _god_delta(natal, stem_god, 6))
    total = _add(lines, total, f"时支{item['zhi']}{branch_god}", _god_delta(natal, branch_god, 4))
    if fate.CHONG[item["zhi"]] == natal["day_zhi"]:
        total = _add(lines, total, "时支冲命主日支", -10)
    event = chart["event"]
    if event == "marry" and natal["gender"] == "男" and stem_god in CAI:
        gain = 4 if stem_god in natal["xi"] else 2
        total = _add(lines, total, f"男命时上妻星{stem_god}", gain)
    if event == "marry" and natal["gender"] == "女":
        if stem_god == "正官":
            gain = 4 if stem_god in natal["xi"] else 2
            total = _add(lines, total, "女命时上正官", gain)
        elif stem_god == "七杀":
            total = _add(lines, total, "女命时上七杀", 3 if stem_god in natal["xi"] else -4)
        if natal["has_shang"] and stem_god == "正官":
            total = _add(lines, total, "女命伤官见官", -8)
    if event == "open" and stem_god in (CAI | SHI) and stem_god in natal["xi"]:
        total = _add(lines, total, f"开市时干{stem_god}", 3)
    if event == "travel" and item["zhi"] == fate.YI_MA[natal["year_zhi"]]:
        total = _add(lines, total, "时支为命主年马", 6)
    if event == "earth" and stem_god in (YIN | BI) and stem_god in natal["xi"]:
        total = _add(lines, total, f"动土时干{stem_god}", 3)
    return total, lines


def _preferred_zhi(chart, natal):
    ranking = fate.rank_hours(chart)
    scored = []
    for row in ranking:
        item = next(hour for hour in chart["hours"] if hour["zhi"] == row["zhi"])
        points, _lines = hour_points(natal, chart, item)
        scored.append((points, row))
    clean = [item for item in scored if not item[1]["bad"]]
    pool = clean or scored
    pool.sort(key=lambda item: (-item[0], -item[1]["total"], fate.DI_ZHI.index(item[1]["zhi"])))
    return pool[0][1]["zhi"]


def _mark_hours(chart, natal):
    ranking = fate.rank_hours(chart)
    scored = []
    for row in ranking:
        item = next(hour for hour in chart["hours"] if hour["zhi"] == row["zhi"])
        points, _lines = hour_points(natal, chart, item)
        scored.append((points, row))
    clean = [item for item in scored if not item[1]["bad"]]
    pool = clean or scored
    top = max(item[0] for item in pool)
    best = [item[1] for item in pool if item[0] == top]
    best.sort(key=lambda row: fate.DI_ZHI.index(row["zhi"]))
    chart["hour_ranking"] = ranking
    chart["best_hours"] = best
    chart["bad_hours"] = sorted(
        (row for row in ranking if row["bad"]),
        key=lambda row: fate.DI_ZHI.index(row["zhi"]),
    )
    chart["has_clean_hour"] = any(not row["bad"] for row in ranking)


def _rerun(chart, natal, zhi, month_label, animal=None):
    raw = {
        "g_year": str(chart["civil"].year),
        "g_month": str(chart["civil"].month),
        "g_day": str(chart["civil"].day),
        "time": fate.SHICHEN_CLOCK[zhi],
        "zhushi_shengxiao": animal or natal["animal"],
        "event_type": chart["event"],
        "house_dir": chart["house_text"],
        "_auto_time": "yes",
    }
    fresh = fate.analyze(raw)
    if month_label:
        fresh["month_scan"] = month_label
    return fresh


def _day_points(chart, natal):
    lines = []
    total = 0
    hard = []
    day_god = ten_god(natal["day_gan"], chart["day_gan"])
    branch_god = ten_god(natal["day_gan"], HIDE[chart["day_zhi"]][0])
    year_god = ten_god(natal["day_gan"], chart["year_gan"])
    month_god = ten_god(natal["day_gan"], chart["month_gan"])
    total = _add(lines, total, f"流年{chart['year_gan']}{year_god}", _god_delta(natal, year_god, 3))
    total = _add(lines, total, f"流月{chart['month_gan']}{month_god}", _god_delta(natal, month_god, 3))
    total = _add(lines, total, f"日干{chart['day_gan']}{day_god}", _god_delta(natal, day_god, 10))
    total = _add(lines, total, f"日支{chart['day_zhi']}{branch_god}", _god_delta(natal, branch_god, 8))

    if fate.CHONG[chart["day_zhi"]] == natal["day_zhi"]:
        total = _add(lines, total, "日支冲命主日柱", -16)
        hard.append(f"日支{chart['day_zhi']}冲命主日柱{natal['day_zhi']}")
    if fate.is_xing(chart["day_zhi"], natal["day_zhi"]):
        total = _add(lines, total, "日支刑命主日支", -8)
    if fate.HAI[chart["day_zhi"]] == natal["day_zhi"]:
        total = _add(lines, total, "日支害命主日支", -6)
    if fate.LIU_HE[chart["day_zhi"]] == natal["day_zhi"]:
        total = _add(lines, total, "日支六合命主日支", 6)
    if natal["day_zhi"] in fate.SAN_HE[chart["day_zhi"]] and natal["day_zhi"] != chart["day_zhi"]:
        total = _add(lines, total, "日支三合命主日支", 4)
    if fate.CHONG[chart["day_zhi"]] == natal["year_zhi"]:
        total = _add(lines, total, "日支冲命主年支", -8)
    if chart["day_zhi"] in natal["kong"]:
        total = _add(lines, total, "日支落命主旬空", -6)

    event = chart["event"]
    if event == "marry" and natal["gender"] == "男" and day_god in CAI:
        gain = 6 if day_god in natal["xi"] else 2
        total = _add(lines, total, f"男命日干妻星{day_god}", gain)
    if event == "marry" and natal["gender"] == "女":
        if day_god == "正官":
            gain = 6 if day_god in natal["xi"] else 2
            total = _add(lines, total, "女命日干正官", gain)
        elif day_god == "七杀":
            total = _add(lines, total, "女命日干七杀", 4 if day_god in natal["xi"] else -6)
        if natal["has_shang"] and day_god == "正官":
            total = _add(lines, total, "女命伤官见官", -8)
    if event == "open" and day_god in (CAI | SHI) and day_god in natal["xi"]:
        total = _add(lines, total, f"开市日干{day_god}", 4)
    if event == "travel" and chart["day_zhi"] == fate.YI_MA[natal["year_zhi"]]:
        total = _add(lines, total, "日支为命主年马", 6)
    if event == "earth" and day_god in GUAN and day_god in natal["ji"]:
        total = _add(lines, total, "身弱见官杀，不宜动土", -4)
    return total, lines, hard


def _verdict(almanac_conclusion, bazi_score, bazi_hard):
    if almanac_conclusion == "不宜" or bazi_hard:
        return "不宜"
    if almanac_conclusion == "宜改时":
        return "宜改时" if bazi_score >= 0 else "平"
    if bazi_score >= 12 and almanac_conclusion == "宜":
        return "宜"
    if bazi_score >= 12 or (bazi_score >= 0 and almanac_conclusion == "宜"):
        return "可备选"
    return "平"


def _apply(chart, natal):
    almanac_score = chart["score"]
    almanac_conclusion = chart["conclusion"]
    chosen = next(hour for hour in chart["hours"] if hour["zhi"] == chart["shi_zhi"])
    day_total, day_lines, hard = _day_points(chart, natal)
    hour_total, hour_lines = hour_points(natal, chart, chosen)
    total = day_total + hour_total
    conclusion = _verdict(almanac_conclusion, total, hard)
    lines = [
        *day_lines,
        *hour_lines,
        f"命理分 {total}",
    ]
    if hard:
        lines.append("命理不宜：" + "；".join(hard))
    lines.append(f"结论：{conclusion}")
    chart["use_bazi"] = True
    chart["natal_lines"] = natal["lines"]
    chart["bazi_lines"] = lines
    chart["bazi_score"] = total
    chart["almanac_score"] = almanac_score
    chart["almanac_conclusion"] = almanac_conclusion
    chart["score"] = total
    chart["conclusion"] = conclusion
    return chart


def finish(chart, natal):
    """通书排完一日之后，按命主改选时辰并改写得分、结论。"""
    label = chart.get("month_scan")
    if chart.get("auto_time"):
        zhi = _preferred_zhi(chart, natal)
        if zhi != chart["shi_zhi"]:
            chart = _rerun(chart, natal, zhi, label)
        _mark_hours(chart, natal)
    return _apply(chart, natal)


def bazi_rank(chart):
    return (
        fate.CONCLUSION_RANK.get(chart["conclusion"], 9),
        -chart["bazi_score"],
        -chart["almanac_score"],
        chart["civil"].toordinal(),
    )


def _combined_rows(chart, natal):
    """同一时辰上的通书分加八字分。日柱对十二时辰相同，只让时辰分变化。"""
    ranking = fate.rank_hours(chart)
    day_total, _lines, _hard = _day_points(chart, natal)
    rows = []
    for row in ranking:
        item = next(hour for hour in chart["hours"] if hour["zhi"] == row["zhi"])
        points, _hour_lines = hour_points(natal, chart, item)
        rows.append((row["total"] + day_total + points, row))
    return ranking, rows


def _combined_zhi(chart, natal):
    _ranking, rows = _combined_rows(chart, natal)
    clean = [item for item in rows if not item[1]["bad"]]
    pool = clean or rows
    pool.sort(key=lambda item: (-item[0], -item[1]["total"], fate.DI_ZHI.index(item[1]["zhi"])))
    return pool[0][1]["zhi"]


def _mark_combined(chart, natal):
    ranking, rows = _combined_rows(chart, natal)
    clean = [item for item in rows if not item[1]["bad"]]
    pool = clean or rows
    top = max(item[0] for item in pool)
    best = [item[1] for item in pool if item[0] == top]
    best.sort(key=lambda row: fate.DI_ZHI.index(row["zhi"]))
    chart["hour_ranking"] = ranking
    chart["best_hours"] = best
    chart["bad_hours"] = sorted(
        (row for row in ranking if row["bad"]),
        key=lambda row: fate.DI_ZHI.index(row["zhi"]),
    )
    chart["has_clean_hour"] = any(not row["bad"] for row in ranking)


def attach_both(chart, natal):
    """通书和八字都算时，选两边分数之和最高的时辰，两套分数都留在这一时辰上。"""
    label = chart.get("month_scan")
    if chart.get("auto_time"):
        zhi = _combined_zhi(chart, natal)
        if zhi != chart["shi_zhi"]:
            chart = _rerun(chart, natal, zhi, label, chart["animal"])
        _mark_combined(chart, natal)
    chart = _apply(chart, natal)
    chart["total_score"] = chart["almanac_score"] + chart["bazi_score"]
    return chart


def total_rank(chart):
    """不宜排在后面。能用的日子之间，按通书分加八字分从高到低。"""
    blocked = chart["conclusion"] == "不宜"
    return (blocked, -chart["total_score"], chart["civil"].toordinal())
