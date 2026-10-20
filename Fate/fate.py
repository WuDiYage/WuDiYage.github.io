# -*- coding: utf-8 -*-
"""
正式择日 v4.0

历法、四柱、节气、二十八宿、建除、黄黑道、通书宜忌使用 lunar-python
（寿星天文历）。年柱以立春交节时刻换年，月柱以节交节时刻换月。

时辰由钟点换算。子时跨日采用八字流派 1：
  晚子时 23:00-23:59，日柱与日课按次日，时柱按次日日干起子；
  早子时 00:00-00:59，日柱与日课按当日。

这是传统通书择日，不是科学预测。
"""

import calendar
import sys
import unicodedata
from datetime import date, datetime, timedelta

from lunar_python import Solar

TIAN_GAN = ["甲", "乙", "丙", "丁", "戊", "己", "庚", "辛", "壬", "癸"]
DI_ZHI = ["子", "丑", "寅", "卯", "辰", "巳", "午", "未", "申", "酉", "戌", "亥"]

SHENGXIAO_TO_ZHI = {
    "鼠": "子", "牛": "丑", "虎": "寅", "兔": "卯",
    "龙": "辰", "蛇": "巳", "马": "午", "羊": "未",
    "猴": "申", "鸡": "酉", "狗": "戌", "猪": "亥",
}

CHONG = {
    "子": "午", "丑": "未", "寅": "申", "卯": "酉", "辰": "戌", "巳": "亥",
    "午": "子", "未": "丑", "申": "寅", "酉": "卯", "戌": "辰", "亥": "巳",
}
HAI = {
    "子": "未", "丑": "午", "寅": "巳", "卯": "辰", "辰": "卯", "巳": "寅",
    "午": "丑", "未": "子", "申": "亥", "酉": "戌", "戌": "酉", "亥": "申",
}
XING = {
    "子": ("卯",), "卯": ("子",),
    "寅": ("巳", "申"), "巳": ("寅", "申"), "申": ("寅", "巳"),
    "丑": ("未", "戌"), "未": ("丑", "戌"), "戌": ("丑", "未"),
    "辰": ("辰",), "午": ("午",), "酉": ("酉",), "亥": ("亥",),
}
LIU_HE = {
    "子": "丑", "丑": "子", "寅": "亥", "亥": "寅", "卯": "戌", "戌": "卯",
    "辰": "酉", "酉": "辰", "巳": "申", "申": "巳", "午": "未", "未": "午",
}
SAN_HE = {
    "申": ("申", "子", "辰"), "子": ("申", "子", "辰"), "辰": ("申", "子", "辰"),
    "亥": ("亥", "卯", "未"), "卯": ("亥", "卯", "未"), "未": ("亥", "卯", "未"),
    "寅": ("寅", "午", "戌"), "午": ("寅", "午", "戌"), "戌": ("寅", "午", "戌"),
    "巳": ("巳", "酉", "丑"), "酉": ("巳", "酉", "丑"), "丑": ("巳", "酉", "丑"),
}

# 驿马、咸池以三合局为准：申子辰马在寅、桃花在酉，其余三局类推。
YI_MA = {}
XIAN_CHI = {}
for _horse, _members in (("寅", ("申", "子", "辰")), ("申", ("寅", "午", "戌")),
                         ("亥", ("巳", "酉", "丑")), ("巳", ("亥", "卯", "未"))):
    for _zhi in _members:
        YI_MA[_zhi] = _horse
for _peach, _members in (("酉", ("申", "子", "辰")), ("卯", ("寅", "午", "戌")),
                         ("午", ("巳", "酉", "丑")), ("子", ("亥", "卯", "未"))):
    for _zhi in _members:
        XIAN_CHI[_zhi] = _peach

# 三煞：申子辰煞南，寅午戌煞北，亥卯未煞西，巳酉丑煞东。
SAN_SHA = {}
for _direction, _years, _branches in (
    ("南", ("申", "子", "辰"), ("巳", "午", "未")),
    ("北", ("寅", "午", "戌"), ("亥", "子", "丑")),
    ("西", ("亥", "卯", "未"), ("申", "酉", "戌")),
    ("东", ("巳", "酉", "丑"), ("寅", "卯", "辰")),
):
    for _year in _years:
        SAN_SHA[_year] = (_direction, _branches)

ZHI_DIR = {
    "子": "北", "丑": "东北", "寅": "东北", "卯": "东",
    "辰": "东南", "巳": "东南", "午": "南", "未": "西南",
    "申": "西南", "酉": "西", "戌": "西北", "亥": "西北",
}
DIR_KEYS = ["东北", "东南", "西南", "西北", "东", "南", "西", "北"]
BAGUA_DIR = {
    "坎": "北", "艮": "东北", "震": "东", "巽": "东南",
    "离": "南", "坤": "西南", "兑": "西", "乾": "西北",
}

# 天乙贵人按日干：甲戊庚牛羊，乙己鼠猴乡，丙丁猪鸡位，壬癸兔蛇藏，六辛逢马虎。
TIAN_YI = {
    "甲": ("丑", "未"), "戊": ("丑", "未"), "庚": ("丑", "未"),
    "乙": ("子", "申"), "己": ("子", "申"),
    "丙": ("亥", "酉"), "丁": ("亥", "酉"),
    "壬": ("卯", "巳"), "癸": ("卯", "巳"),
    "辛": ("午", "寅"),
}

# 五不遇时：时干克日干。
WU_BU_YU = {
    "甲": "庚", "乙": "辛", "丙": "壬", "丁": "癸", "戊": "甲",
    "己": "乙", "庚": "丙", "辛": "丁", "壬": "戊", "癸": "己",
}

GAN_WUXING = {
    "甲": "木", "乙": "木", "丙": "火", "丁": "火", "戊": "土",
    "己": "土", "庚": "金", "辛": "金", "壬": "水", "癸": "水",
}
ZHI_WUXING = {
    "寅": "木", "卯": "木", "巳": "火", "午": "火",
    "申": "金", "酉": "金", "亥": "水", "子": "水",
    "辰": "土", "戌": "土", "丑": "土", "未": "土",
}

JIANCHU_INFO = {
    "建": "宜祭祀祈福，忌动土搬迁",
    "除": "宜除旧治病，忌奠基",
    "满": "宜收纳入库，忌诉讼嫁娶",
    "平": "宜修葺平整，无大利",
    "定": "宜安床签约，忌诉讼搬迁",
    "执": "宜固守谈判，忌冒进远行",
    "破": "宜拆除，忌嫁娶开业",
    "危": "宜决断，不宜常事奠基",
    "成": "宜开业嫁娶等成就之事",
    "收": "宜收敛收债，忌开创",
    "开": "宜出行开业，忌安葬",
    "闭": "宜守成收纳，忌开创外出",
}
JIANCHU_SCORE = {
    "成": 8, "开": 8, "定": 5, "除": 2, "满": 2,
    "平": 0, "建": -2, "执": -2, "收": -2,
    "危": -6, "闭": -6, "破": -10,
}

# 事项专忌宿，与通书宿之吉凶分开计。
BAD_XIU = {
    "marry": {"心", "昴", "参", "鬼"},
    "open": {"虚", "危", "心", "参"},
    "earth": {"危"},
    "travel": set(),
}
EVENT_WORD = {
    "marry": "嫁娶",
    "open": "开市",
    "earth": "动土",
    "travel": "出行",
}
EVENT_CN = {
    "marry": "嫁娶",
    "open": "开市",
    "earth": "动土",
    "travel": "出行",
}
SILI = {"春分", "秋分", "夏至", "冬至"}
SIJUE = {"立春", "立夏", "立秋", "立冬"}
DE_DI = {"长生", "冠带", "临官", "帝旺"}


def display_width(text):
    width = 0
    for ch in str(text):
        width += 2 if unicodedata.east_asian_width(ch) in ("W", "F") else 1
    return width


def pad(text, width):
    text = str(text)
    return text + " " * max(0, width - display_width(text))


def clock_to_shichen(hour):
    """钟点换时辰。23 点为晚子时，返回 (地支, 是否晚子时)。"""
    if hour == 23 or hour == 0:
        return "子", hour == 23
    names = ["丑", "丑", "寅", "寅", "卯", "卯", "辰", "辰", "巳", "巳",
             "午", "午", "未", "未", "申", "申", "酉", "酉", "戌", "戌", "亥", "亥"]
    return names[hour - 1], False


def shichen_label(zhi, late_zi, hour):
    if zhi == "子" and late_zi:
        return "晚子时"
    if zhi == "子" and hour == 0:
        return "早子时"
    return f"{zhi}时"


def parse_clock(text):
    parts = text.strip().split(":")
    if len(parts) != 2:
        raise ValueError("时间须写成 HH:MM，例如 11:30 或 23:05")
    hour, minute = int(parts[0]), int(parts[1])
    if not (0 <= hour <= 23 and 0 <= minute <= 59):
        raise ValueError("时间超出 00:00-23:59")
    return hour, minute


def parse_house(text):
    text = text.strip()
    if "朝" not in text or not text.startswith("坐"):
        return None, None
    sit_text, face_text = text[1:].split("朝", 1)

    def cut(token):
        for key in DIR_KEYS:
            if token.startswith(key):
                return key
        return None

    return cut(sit_text), cut(face_text)


def bagua_to_dir(name):
    return BAGUA_DIR.get(name, name)


def hongsha_zhi(lunar_month):
    month = abs(int(lunar_month))
    if month in (1, 4, 7, 10):
        return "酉"
    if month in (2, 5, 8, 11):
        return "巳"
    if month in (3, 6, 9, 12):
        return "丑"
    return None


def is_xing(day_zhi, other_zhi):
    return other_zhi in XING[day_zhi]


def eve_term(almanac, pan_date):
    """排盘日的次日若交四离、四绝之节气，则本日为四离或四绝。"""
    term = almanac.getNextJieQi()
    solar = term.getSolar()
    term_day = date(solar.getYear(), solar.getMonth(), solar.getDay())
    if term_day - pan_date != timedelta(days=1):
        return None
    name = term.getName()
    if name in SILI:
        return "四离", name
    if name in SIJUE:
        return "四绝", name
    return None


def solar_of(day, hour, minute):
    return Solar.fromYmdHms(day.year, day.month, day.day, hour, minute, 0)


def jie_text(jie):
    solar = jie.getSolar()
    return f"{jie.getName()}（{solar.toYmdHms()}）"


def collect_hours(almanac):
    """排盘日的十二时辰。23:00 一档属于次日，不计入本日。"""
    rows = []
    for item in almanac.getTimes():
        if item.getMinHm() == "23:00":
            continue
        zhi = item.getZhi()
        # 本日子时起于前一日 23:00，止于当日 00:59。当日 23:00 已是次日日柱。
        span = "前一日23:00-当日00:59" if zhi == "子" else f"{item.getMinHm()}-{item.getMaxHm()}"
        rows.append({
            "gan": item.getGan(),
            "zhi": zhi,
            "ganzhi": item.getGanZhi(),
            "span": span,
            "shen": item.getTianShen(),
            "luck": item.getTianShenLuck(),
            "kind": item.getTianShenType(),
            "yi": list(item.getYi()),
            "ji": list(item.getJi()),
        })
    return rows


def hide_text(gans, gods):
    return "、".join(f"{gan}{god}" for gan, god in zip(gans, gods))


def add_score(bucket, name, delta):
    if delta:
        bucket.append((name, delta))



SHICHEN_CLOCK = {
    "子": "00:30", "丑": "01:30", "寅": "03:30", "卯": "05:30",
    "辰": "07:30", "巳": "09:30", "午": "11:30", "未": "13:30",
    "申": "15:30", "酉": "17:30", "戌": "19:30", "亥": "21:30",
}


def hour_adjustments(day_gan, person_zhi, word, event, kong, yi_ma, xian_chi, item, label):
    """某个时辰相对日课的加减分，以及不佳原因。"""
    items = []
    bad = []
    if word in item["yi"]:
        items.append((f"{label}宜{word}", 8))
    if word in item["ji"]:
        items.append((f"{label}忌{word}", -10))
        bad.append(f"忌{word}")
    if item["kind"] == "黄道":
        items.append((f"时值{item['shen']}（黄道）", 8))
    else:
        items.append((f"时值{item['shen']}（黑道）", -6))
        bad.append("黑道")
    if item["zhi"] in TIAN_YI[day_gan]:
        items.append(("时支临天乙贵人", 8))
    if CHONG[item["zhi"]] == person_zhi:
        items.append(("时支冲主事", -8))
        bad.append("冲主事")
    if item["gan"] == WU_BU_YU[day_gan]:
        items.append(("五不遇时", -12))
        bad.append("五不遇时")
    if item["zhi"] in kong:
        items.append(("时落旬空", -4))
        bad.append("旬空")
    if event == "marry" and item["zhi"] == xian_chi:
        items.append(("时支咸池桃花", 4))
    if event in ("open", "travel") and item["zhi"] == yi_ma:
        items.append(("时支驿马", 6))
    return items, bad


def rank_hours(chart):
    day_base = chart["score"] - chart["hour_delta"]
    rows = []
    for item in chart["hours"]:
        parts, bad = hour_adjustments(
            chart["day_gan"], chart["person_zhi"], chart["word"], chart["event"],
            chart["kong"], chart["yi_ma"], chart["xian_chi"], item, "本时辰",
        )
        delta = sum(value for _, value in parts)
        rows.append({
            "span": item["span"],
            "zhi": item["zhi"],
            "ganzhi": item["ganzhi"],
            "shen": item["shen"],
            "kind": item["kind"],
            "delta": delta,
            "total": day_base + delta,
            "bad": bad,
            "yi_event": chart["word"] in item["yi"],
        })
    rows.sort(key=lambda row: (-row["total"], DI_ZHI.index(row["zhi"])))
    return rows


def pick_best(ranking):
    clean = [row for row in ranking if not row["bad"]]
    pool = clean or ranking
    best_total = max(row["total"] for row in pool)
    tied = [row for row in pool if row["total"] == best_total]
    tied.sort(key=lambda row: DI_ZHI.index(row["zhi"]))
    return tied


def choose_day_hours(raw):
    probe_raw = dict(raw)
    probe_raw["time"] = "12:00"
    probe_raw.pop("_auto_time", None)
    probe = analyze(probe_raw)
    ranking = rank_hours(probe)
    best = pick_best(ranking)
    picked_raw = dict(raw)
    picked_raw["time"] = SHICHEN_CLOCK[best[0]["zhi"]]
    picked_raw["_auto_time"] = "yes"
    chart = analyze(picked_raw)
    chart["auto_time"] = True
    chart["hour_ranking"] = ranking
    chart["best_hours"] = best
    chart["bad_hours"] = sorted(
        (row for row in ranking if row["bad"]),
        key=lambda row: DI_ZHI.index(row["zhi"]),
    )
    chart["has_clean_hour"] = any(not row["bad"] for row in ranking)
    return chart


def print_hour_advice(chart):
    if chart["hard"]:
        print("本日有日课禁忌，换时辰不能把这一天变成宜日。下面只比较当天的十二时辰。")
    elif not chart["has_clean_hour"]:
        print("当天没有无禁忌的时辰，下面是扣分最少的一档。")
    if chart["hard"]:
        title = "当日时辰里相对最好"
    elif not chart["has_clean_hour"]:
        title = "相对最佳时间"
    else:
        title = "最佳时间"
    if len(chart["best_hours"]) > 1:
        title += "（并列）"
    print(title + "：")
    for row in chart["best_hours"]:
        event = f"宜{chart['word']}" if row["yi_event"] else f"未写明宜{chart['word']}"
        print(f"  {row['span']} {row['zhi']}时 {row['ganzhi']} {row['shen']}{row['kind']}  {event}")
    best_set = {row["zhi"] for row in chart["best_hours"]}
    bad_set = {row["zhi"] for row in chart["bad_hours"]}
    usable = [row for row in chart["hour_ranking"] if row["zhi"] not in best_set and row["zhi"] not in bad_set]
    usable.sort(key=lambda row: DI_ZHI.index(row["zhi"]))
    if usable:
        usable_title = "其余时辰没有单独的不佳项" if chart["hard"] else "其余可用，但不如最佳"
        brief = "、".join(f"{row['span']}{row['zhi']}时{row['shen']}" for row in usable)
        print(usable_title + "：" + brief)
    print("不佳时间：")
    if chart["bad_hours"]:
        for row in chart["bad_hours"]:
            print(f"  {row['span']} {row['zhi']}时 {row['ganzhi']} {row['shen']}{row['kind']}：{'、'.join(row['bad'])}")
    else:
        print("  无")

def analyze(raw):
    if str(raw.get("time", "")).strip() == "":
        return choose_day_hours(raw)
    hour_label = "选用时辰" if raw.get("_auto_time") == "yes" else "所填时辰"
    year = int(raw["g_year"])
    month = int(raw["g_month"])
    day_num = int(raw["g_day"])
    civil = date(year, month, day_num)
    hour, minute = parse_clock(raw["time"])
    shi_zhi, late_zi = clock_to_shichen(hour)
    animal = raw["zhushi_shengxiao"].strip()
    if animal not in SHENGXIAO_TO_ZHI:
        raise ValueError(f"无法识别生肖「{animal}」")
    event = raw["event_type"].strip()
    if event not in EVENT_WORD:
        raise ValueError("event_type 只能是 marry、open、earth、travel")
    house_text = raw.get("house_dir", "").strip()
    sit_dir, face_dir = parse_house(house_text)
    person_zhi = SHENGXIAO_TO_ZHI[animal]
    word = EVENT_WORD[event]
    pan_date = civil + timedelta(days=1) if late_zi else civil

    exact = solar_of(civil, hour, minute).getLunar()
    eight = exact.getEightChar()
    eight.setSect(1)
    almanac = solar_of(pan_date, 12, 0).getLunar()

    day_gan = eight.getDayGan()
    day_zhi = eight.getDayZhi()
    month_zhi = eight.getMonthZhi()
    year_zhi = eight.getYearZhi()
    time_gan = eight.getTimeGan()
    time_zhi = eight.getTimeZhi()
    if time_zhi != shi_zhi:
        raise RuntimeError(f"时辰换算与排盘不一致：{shi_zhi} / {time_zhi}")
    if f"{day_gan}{day_zhi}" != almanac.getDayInGanZhi():
        raise RuntimeError("晚子时日柱与次日日课不一致")

    hours = collect_hours(almanac)
    chosen = next(item for item in hours if item["zhi"] == shi_zhi)
    day_yi = list(almanac.getDayYi())
    day_ji = list(almanac.getDayJi())
    ji_shen = list(almanac.getDayJiShen())
    xiong = list(almanac.getDayXiongSha())
    xiu = almanac.getXiu()
    xiu_luck = almanac.getXiuLuck()
    zhixing = almanac.getZhiXing()
    day_kind = almanac.getDayTianShenType()
    lunar_month = almanac.getMonth()
    hongsha = hongsha_zhi(lunar_month)
    term_eve = eve_term(almanac, pan_date)
    sha_dir, sha_branches = SAN_SHA[year_zhi]
    tai_sui_dir = ZHI_DIR[year_zhi]
    sui_po = CHONG[year_zhi]
    yue_po = CHONG[month_zhi]

    in_day_yi = word in day_yi
    in_day_ji = word in day_ji
    in_hour_yi = word in chosen["yi"]
    in_hour_ji = word in chosen["ji"]
    wu_bu_yu = time_gan == WU_BU_YU[day_gan]
    is_hongsha = day_zhi == hongsha
    is_yuepo = day_zhi == yue_po
    is_suipo = day_zhi == sui_po
    in_sansha = day_zhi in sha_branches
    chong_person = CHONG[day_zhi] == person_zhi
    xing_person = is_xing(day_zhi, person_zhi)
    hai_person = HAI[day_zhi] == person_zhi
    he_person = LIU_HE[day_zhi] == person_zhi
    sanhe_person = person_zhi in SAN_HE[day_zhi] and person_zhi != day_zhi
    hour_chong = CHONG[time_zhi] == person_zhi
    gui_ren = TIAN_YI[day_gan]
    hour_gui = time_zhi in gui_ren
    de_ling = ZHI_WUXING[month_zhi] == GAN_WUXING[day_gan]
    de_di = eight.getDayDiShi() in DE_DI
    kong = eight.getDayXunKong()
    hour_kong = time_zhi in kong
    xi_dir = bagua_to_dir(almanac.getDayPositionXi())
    cai_dir = bagua_to_dir(almanac.getDayPositionCai())
    fu_dir = bagua_to_dir(almanac.getDayPositionFu())
    face_xi = face_dir is not None and face_dir == xi_dir
    face_cai = face_dir is not None and face_dir == cai_dir
    sit_taisui = sit_dir is not None and sit_dir == tai_sui_dir
    sit_suipo = sit_dir is not None and sit_dir == ZHI_DIR[sui_po]
    sit_sansha = sit_dir is not None and sit_dir == sha_dir

    score_items = []
    hard = []
    notes = []

    add_score(score_items, "通书日宜" + word, 18 if in_day_yi else 0)
    add_score(score_items, "通书日忌" + word, -22 if in_day_ji else 0)
    add_score(score_items, f"日值{almanac.getDayTianShen()}（{day_kind}）", 8 if day_kind == "黄道" else -6)
    add_score(score_items, f"建除{zhixing}", JIANCHU_SCORE[zhixing])
    add_score(score_items, f"二十八宿{xiu}（{xiu_luck}）", 6 if xiu_luck == "吉" else -6)
    if "天德" in ji_shen:
        add_score(score_items, "天德", 8)
    if "月德" in ji_shen:
        add_score(score_items, "月德", 8)
    if "天德合" in ji_shen:
        add_score(score_items, "天德合", 5)
    if "月德合" in ji_shen:
        add_score(score_items, "月德合", 5)
    add_score(score_items, "日主得令", 4 if de_ling else 0)
    add_score(score_items, f"日主{eight.getDayDiShi()}", 4 if de_di else 0)
    add_score(score_items, "与主事六合", 6 if he_person else 0)
    add_score(score_items, "与主事三合", 4 if sanhe_person else 0)
    add_score(score_items, "冲主事生肖", -16 if chong_person else 0)
    add_score(score_items, "刑主事生肖", -8 if xing_person else 0)
    add_score(score_items, "害主事生肖", -6 if hai_person else 0)
    add_score(score_items, "岁破", -20 if is_suipo else 0)
    add_score(score_items, "月破", -20 if is_yuepo else 0)
    add_score(score_items, "三煞", -12 if in_sansha else 0)
    add_score(score_items, "红沙", -16 if is_hongsha else 0)
    if term_eve:
        add_score(score_items, term_eve[0], -18)
    if event == "marry" and face_xi:
        add_score(score_items, "房屋朝向合喜神", 4)
    if event == "open" and face_cai:
        add_score(score_items, "房屋朝向合财神", 4)
    if event == "earth" and sit_taisui:
        add_score(score_items, "坐山犯太岁", -15)
    if event == "earth" and sit_suipo:
        add_score(score_items, "坐山犯岁破", -12)
    if event == "earth" and sit_sansha:
        add_score(score_items, "坐山犯三煞", -15)

    if in_day_ji:
        hard.append(f"通书日忌{word}")
    if is_suipo:
        hard.append(f"岁破（太岁{year_zhi}，岁破在{sui_po}）")
    if is_yuepo:
        hard.append(f"月破（月令{month_zhi}，月破在{yue_po}）")
    if is_hongsha and event in ("marry", "travel"):
        hard.append(f"红沙日（本月红沙在{hongsha}）")
    if term_eve and event in ("marry", "open", "earth"):
        hard.append(f"{term_eve[0]}（次日{term_eve[1]}）")
    if chong_person and event == "marry":
        hard.append(f"日支{day_zhi}冲主事{animal}（{person_zhi}）")
    if xiu in BAD_XIU[event]:
        hard.append(f"二十八宿{xiu}为{EVENT_CN[event]}忌宿")
    if event == "earth" and in_sansha:
        hard.append(f"日支{day_zhi}落三煞（{sha_dir}，{'、'.join(sha_branches)}）")
    if event == "earth" and sit_taisui:
        hard.append(f"坐山{sit_dir}犯太岁（{tai_sui_dir}）")
    if event == "earth" and sit_sansha:
        hard.append(f"坐山{sit_dir}犯三煞（{sha_dir}）")
    if is_hongsha and event == "earth":
        notes.append(f"红沙日，地支{hongsha}，动土宜再避")
    if sit_dir is None or face_dir is None:
        notes.append("房屋坐向未按「坐某朝某」识别，方位合参未计入")
    if not hard:
        if hour_chong:
            notes.append(f"{hour_label}冲主事生肖，可改用其他黄道时")
        if wu_bu_yu:
            notes.append(f"{hour_label}为五不遇时，大事宜改时")
        if in_hour_ji and not in_day_ji:
            notes.append(f"日课未忌{word}，但{hour_label}忌{word}")

    hour_items, _hour_bad = hour_adjustments(
        day_gan, person_zhi, word, event, kong, YI_MA[day_zhi], XIAN_CHI[day_zhi], chosen, hour_label
    )
    for _name, _delta in hour_items:
        add_score(score_items, _name, _delta)
    score = sum(delta for _, delta in score_items)
    if hard:
        conclusion = "不宜"
    elif in_day_yi and (in_hour_ji or wu_bu_yu or hour_chong):
        conclusion = "宜改时"
    elif in_day_yi and chosen["kind"] == "黄道":
        conclusion = "宜"
    elif in_day_yi or score >= 12:
        conclusion = "可备选"
    else:
        conclusion = "平"

    good_hours = []
    for item in hours:
        if item["kind"] != "黄道":
            continue
        if item["gan"] == WU_BU_YU[day_gan]:
            continue
        if word in item["ji"]:
            continue
        good_hours.append(item)

    return {
        "civil": civil,
        "hour": hour,
        "minute": minute,
        "late_zi": late_zi,
        "shi_zhi": shi_zhi,
        "shi_label": shichen_label(shi_zhi, late_zi, hour),
        "pan_date": pan_date,
        "animal": animal,
        "person_zhi": person_zhi,
        "event": event,
        "event_cn": EVENT_CN[event],
        "word": word,
        "house_text": house_text,
        "sit_dir": sit_dir,
        "face_dir": face_dir,
        "year_gz": eight.getYear(),
        "month_gz": eight.getMonth(),
        "day_gz": eight.getDay(),
        "time_gz": eight.getTime(),
        "day_gan": day_gan,
        "day_zhi": day_zhi,
        "month_zhi": month_zhi,
        "year_zhi": year_zhi,
        "year_gan": eight.getYearGan(),
        "month_gan": eight.getMonthGan(),
        "time_gan": time_gan,
        "nayin": eight.getDayNaYin(),
        "kong": kong,
        "dishi_day": eight.getDayDiShi(),
        "shishen": (
            eight.getYearShiShenGan(),
            eight.getMonthShiShenGan(),
            eight.getTimeShiShenGan(),
        ),
        "hide": (
            hide_text(eight.getYearHideGan(), eight.getYearShiShenZhi()),
            hide_text(eight.getMonthHideGan(), eight.getMonthShiShenZhi()),
            hide_text(eight.getDayHideGan(), eight.getDayShiShenZhi()),
            hide_text(eight.getTimeHideGan(), eight.getTimeShiShenZhi()),
        ),
        "lunar_text": almanac.toString(),
        "lunar_month": lunar_month,
        "prev_jie": jie_text(exact.getPrevJie()),
        "next_jie": jie_text(exact.getNextJie()),
        "xiu": xiu,
        "xiu_luck": xiu_luck,
        "zheng": almanac.getZheng(),
        "zhixing": zhixing,
        "day_shen": almanac.getDayTianShen(),
        "day_kind": day_kind,
        "day_yi": day_yi,
        "day_ji": day_ji,
        "ji_shen": ji_shen,
        "xiong": xiong,
        "pengzu": f"{almanac.getPengZuGan()}；{almanac.getPengZuZhi()}",
        "day_chong": f"{almanac.getDayChong()}（{almanac.getDayChongShengXiao()}）",
        "day_sha": almanac.getDaySha(),
        "xi_text": f"{almanac.getDayPositionXiDesc()}（{xi_dir}）",
        "cai_text": f"{almanac.getDayPositionCaiDesc()}（{cai_dir}）",
        "fu_text": f"{almanac.getDayPositionFuDesc()}（{fu_dir}）",
        "gui_ren": "、".join(gui_ren),
        "yi_ma": YI_MA[day_zhi],
        "xian_chi": XIAN_CHI[day_zhi],
        "sha_dir": sha_dir,
        "sha_branches": sha_branches,
        "tai_sui_dir": tai_sui_dir,
        "sui_po": sui_po,
        "yue_po": yue_po,
        "hongsha": hongsha,
        "is_hongsha": is_hongsha,
        "term_eve": term_eve,
        "de_ling": de_ling,
        "chosen": chosen,
        "hours": hours,
        "good_hours": good_hours,
        "chong_person": chong_person,
        "xing_person": xing_person,
        "hai_person": hai_person,
        "he_person": he_person,
        "sanhe_person": sanhe_person,
        "score_items": score_items,
        "score": score,
        "hour_delta": sum(_delta for _, _delta in hour_items),
        "auto_time": raw.get("_auto_time") == "yes",
        "hard": hard,
        "notes": notes,
        "conclusion": conclusion,
    }



CONCLUSION_RANK = {"宜": 0, "宜改时": 1, "可备选": 2, "平": 3, "不宜": 4}


def chart_rank(chart):
    return (CONCLUSION_RANK.get(chart["conclusion"], 9), -chart["score"], chart["civil"].toordinal())


def scan_month(raw, quiet=False):
    year = int(raw["g_year"])
    month = int(raw["g_month"])
    if month < 1 or month > 12:
        raise ValueError("月份须在 1 到 12")
    last = calendar.monthrange(year, month)[1]
    label = f"{year}年{month}月"
    if not quiet:
        print(f"正在比较{label}的 {last} 天...", flush=True)
    charts = []
    for day in range(1, last + 1):
        day_raw = dict(raw)
        day_raw["g_day"] = str(day)
        try:
            chart = analyze(day_raw)
        except Exception as exc:
            raise ValueError(f"{year}-{month:02d}-{day:02d}：{exc}") from exc
        chart["month_scan"] = label
        charts.append(chart)
    return charts


def print_month(days):
    days.sort(key=chart_rank)
    best = days[0]
    best_key = chart_rank(best)[:2]
    tied = [item for item in days if chart_rank(item)[:2] == best_key]
    rejected = sum(1 for item in days if item["conclusion"] == "不宜")
    label = best["month_scan"]
    print(f"{label}共 {len(days)} 天，其中不宜 {rejected} 天。")
    if best["conclusion"] == "不宜":
        print("本月没有宜日。下面是扣分较少的一天，仍不宜用于该事项。")
    if len(tied) == 1:
        print(f"本月最佳：{clock_text(best)}  {best['shi_label']}  {best['day_gz']}日  {best['conclusion']}  {best['score']}分")
    else:
        print("本月最佳（并列）：")
        for item in tied:
            print(f"  {clock_text(item)}  {item['shi_label']}  {item['day_gz']}日  {item['conclusion']}  {item['score']}分")
    print(f"{label}每日对比（先按宜、可备选、不宜，同一类再按分数从高到低）：")
    print_table(days)
    print()
    print("展开本月最佳日：")
    print_detail(best)
    print()

def read_candidates(path):
    rows = []
    with open(path, "r", encoding="utf-8") as handle:
        for line_no, line in enumerate(handle, 1):
            text = line.strip()
            if not text or text.startswith("#"):
                continue
            raw = {}
            for part in text.split(";"):
                if "=" not in part:
                    raise ValueError(f"第{line_no}行格式错误：{part}")
                key, value = part.split("=", 1)
                raw[key.strip()] = value.strip()
            if "shi_zhi" in raw and "time" not in raw:
                raise ValueError(f"第{line_no}行仍在填地支。请改成 time=HH:MM，或者不填 time")
            missing = [key for key in ("g_year", "g_month", "zhushi_shengxiao", "event_type", "house_dir") if key not in raw]
            if missing:
                raise ValueError(f"第{line_no}行缺少：{', '.join(missing)}")
            try:
                if not str(raw.get("g_day", "")).strip():
                    rows.extend(scan_month(raw))
                    continue
                chart = analyze(raw)
            except Exception as exc:
                raise ValueError(f"第{line_no}行无法排盘：{exc}") from exc
            rows.append(chart)
    return rows


def clock_text(chart):
    return f"{chart['civil'].isoformat()} {chart['hour']:02d}:{chart['minute']:02d}"


def print_table(charts):
    headers = ["排名", "钟表时间", "时辰", "排盘日", "四柱", "建除", "日课", "宿", "总分", "结论"]
    widths = [6, 18, 10, 12, 26, 6, 12, 8, 6, 10]
    print("".join(pad(title, width) for title, width in zip(headers, widths)))
    print("-" * 108)
    for index, chart in enumerate(charts, 1):
        pillars = f"{chart['year_gz']} {chart['month_gz']} {chart['day_gz']} {chart['time_gz']}"
        day_luck = f"{chart['day_shen']}{chart['day_kind'][:1]}"
        shi_show = chart["shi_label"]
        if chart.get("auto_time") and len(chart.get("best_hours", [])) > 1:
            shi_show += "等"
        cells = [
            str(index),
            clock_text(chart),
            shi_show,
            chart["pan_date"].isoformat(),
            pillars,
            chart["zhixing"],
            day_luck,
            f"{chart['xiu']}{chart['xiu_luck']}",
            str(chart["score"]),
            chart["conclusion"],
        ]
        print("".join(pad(cell, width) for cell, width in zip(cells, widths)))


def yn(flag):
    return "是" if flag else "否"


def print_detail(chart):
    cross = "晚子时，日柱与日课按次日" if chart["late_zi"] else "不跨日"
    if chart["shi_zhi"] == "子" and not chart["late_zi"]:
        cross = "早子时，日柱按当日"
    print("=" * 72)
    if chart.get("month_scan") and chart.get("auto_time"):
        print(f"未填日期和钟点，选用 {clock_text(chart)}  →  {chart['shi_label']}（{chart['chosen']['span']}），{cross}")
        print_hour_advice(chart)
    elif chart.get("month_scan"):
        print(f"未填日期，按所填钟点 {clock_text(chart)}  →  {chart['shi_label']}（{chart['chosen']['span']}），{cross}")
    elif chart.get("auto_time"):
        print(f"未填钟点，选用 {clock_text(chart)}  →  {chart['shi_label']}（{chart['chosen']['span']}），{cross}")
        print_hour_advice(chart)
    else:
        print(f"钟表时间：{clock_text(chart)}  →  {chart['shi_label']}（{chart['chosen']['span']}），{cross}")
    print(f"排盘日：{chart['pan_date'].isoformat()}  农历：{chart['lunar_text']}")
    print(f"四柱：{chart['year_gz']}  {chart['month_gz']}  {chart['day_gz']}  {chart['time_gz']}")
    print(f"日柱纳音：{chart['nayin']}    日旬空：{chart['kong']}")
    print(f"上一节：{chart['prev_jie']}")
    print(f"下一节：{chart['next_jie']}")
    print(f"主事：{chart['animal']}（{chart['person_zhi']}）  事项：{chart['event_cn']}  房屋：{chart['house_text'] or '未填'}")

    year_god, month_god, time_god = chart["shishen"]
    year_hide, month_hide, day_hide, time_hide = chart["hide"]
    print(f"十神（日主{chart['day_gan']}）：年{chart['year_gan']}{year_god}  月{chart['month_gan']}{month_god}  时{chart['time_gan']}{time_god}")
    print(f"藏干：年[{year_hide}] 月[{month_hide}] 日[{day_hide}] 时[{time_hide}]")
    print(f"日主：月令{chart['month_zhi']}{'得令' if chart['de_ling'] else '不得令'}，日支长生十二神为{chart['dishi_day']}")

    print(f"日课：{chart['day_shen']}（{chart['day_kind']}）  建除：{chart['zhixing']}（{JIANCHU_INFO[chart['zhixing']]}）")
    print(f"二十八宿：{chart['xiu']}{chart['zheng']}（{chart['xiu_luck']}）")
    _picked = "选用时辰" if chart.get("auto_time") else "所填时辰"
    print(f"{_picked}：{chart['chosen']['ganzhi']}  {chart['chosen']['shen']}（{chart['chosen']['kind']}）")
    print("日宜：" + "、".join(chart["day_yi"]))
    print("日忌：" + "、".join(chart["day_ji"]))
    print("吉神：" + ("、".join(chart["ji_shen"]) if chart["ji_shen"] else "无"))
    print("凶煞：" + ("、".join(chart["xiong"]) if chart["xiong"] else "无"))
    print(f"彭祖百忌：{chart['pengzu']}")
    print(f"日冲：{chart['day_chong']}  日煞：{chart['day_sha']}")
    print(f"喜神：{chart['xi_text']}  财神：{chart['cai_text']}  福神：{chart['fu_text']}")
    print(f"天乙贵人（日干{chart['day_gan']}）：{chart['gui_ren']}  日支驿马：{chart['yi_ma']}  日支桃花：{chart['xian_chi']}")
    print(f"太岁{chart['year_zhi']}在{chart['tai_sui_dir']}，岁破{chart['sui_po']}在{ZHI_DIR[chart['sui_po']]}")
    yuepo_today = "是" if chart["day_zhi"] == chart["yue_po"] else "否"
    suipo_today = "是" if chart["day_zhi"] == chart["sui_po"] else "否"
    print(f"三煞在{chart['sha_dir']}（{'、'.join(chart['sha_branches'])}）")
    print(f"月破地支：{chart['yue_po']}（本日{yuepo_today}）  岁破地支：{chart['sui_po']}（本日{suipo_today}）")
    print(f"红沙地支：{chart['hongsha']}（本日{yn(chart['is_hongsha'])}）")
    if chart["term_eve"]:
        print(f"{chart['term_eve'][0]}：次日交{chart['term_eve'][1]}")
    else:
        print("四离四绝：不是")
    print(
        "与主事："
        f"冲{yn(chart['chong_person'])}  "
        f"刑{yn(chart['xing_person'])}  "
        f"害{yn(chart['hai_person'])}  "
        f"六合{yn(chart['he_person'])}  "
        f"三合{yn(chart['sanhe_person'])}"
    )
    if chart["sit_dir"]:
        print(f"坐山{chart['sit_dir']}，朝向{chart['face_dir']}")

    print("十二时辰（排盘日；子时含前一日 23:00 起）：")
    for item in chart["hours"]:
        if chart.get("auto_time"):
            best_zhi = {row["zhi"] for row in chart["best_hours"]}
            bad_zhi = {row["zhi"] for row in chart["bad_hours"]}
            if item["zhi"] in best_zhi:
                mark = "  ←最佳"
            elif item["zhi"] in bad_zhi:
                mark = "  ←不佳"
            else:
                mark = ""
        else:
            mark = "  ←所填" if item["zhi"] == chart["shi_zhi"] else ""
        event_mark = ""
        if chart["word"] in item["yi"]:
            event_mark = f"  宜{chart['word']}"
        elif chart["word"] in item["ji"]:
            event_mark = f"  忌{chart['word']}"
        print(f"  {item['span']} {item['ganzhi']} {item['shen']}{item['kind']}{event_mark}{mark}")

    if not chart.get("auto_time"):
        if chart["good_hours"]:
            brief = "、".join(f"{item['span']}{item['zhi']}时{item['shen']}" for item in chart["good_hours"])
            if chart["hard"]:
                print(f"对照黄道时（日课已不宜，改时辰去不掉禁忌）：{brief}")
            else:
                print(f"可考虑的黄道时（已避开五不遇和时忌{chart['word']}）：{brief}")
        else:
            print(f"本日没有同时满足黄道、非五不遇、不忌{chart['word']}的时辰")

    print("计分：")
    for name, delta in chart["score_items"]:
        sign = "+" if delta > 0 else ""
        print(f"  {name} {sign}{delta}")
    print(f"总分：{chart['score']}")
    if chart["hard"]:
        print("不宜原因：" + "；".join(chart["hard"]))
    for note in chart["notes"]:
        print("提示：" + note)
    print(f"结论：{chart['conclusion']}（{chart['event_cn']}）")


def main():
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    path = sys.argv[1] if len(sys.argv) > 1 else "candidates.txt"
    print("正式择日 v4.0  节气四柱用寿星天文历；晚子时（23:00-23:59）日柱算次日；不填 g_day 则比较全月；不填 time 则比较当天十二时辰")
    try:
        charts = read_candidates(path)
    except FileNotFoundError:
        print(f"找不到候选文件：{path}")
        return 1
    except ValueError as exc:
        print(str(exc))
        return 1
    if not charts:
        print("候选文件里没有日期")
        return 1
    groups = []
    singles = []
    for chart in charts:
        label = chart.get("month_scan")
        if label:
            if not groups or groups[-1][0] != label:
                groups.append([label, [chart]])
            else:
                groups[-1][1].append(chart)
        else:
            singles.append(chart)
    for _label, days in groups:
        print_month(days)
    if singles:
        singles.sort(key=chart_rank)
        print("指定日期对比（先按宜、可备选、不宜，同一类再按分数从高到低）：")
        print_table(singles)
        print()
        for chart in singles:
            print_detail(chart)
            print()
    return 0


if __name__ == "__main__":
    sys.exit(main())
