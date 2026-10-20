# -*- coding: utf-8 -*-
"""把择日结果整理成手机界面用的结构。"""

from datetime import date

import fate
import fate_bazi


def _calendar_date(year_text, month_text, day_text, day_required, day_label):
    if not year_text or not month_text or (day_required and not day_text):
        raise ValueError(f"请填写{day_label}")
    try:
        year = int(year_text)
        month = int(month_text)
        day = int(day_text) if day_text else 0
    except ValueError as exc:
        raise ValueError("年和月、日要填数字") from exc
    if not 1900 <= year <= 2100:
        raise ValueError("年份请填 1900 到 2100")
    if not 1 <= month <= 12:
        raise ValueError("月份要在 1 到 12")
    if day_text:
        try:
            date(year, month, day)
        except ValueError as exc:
            raise ValueError("这一天在公历里不存在") from exc
    return year, month, str(day) if day_text else ""


def normalize_query(raw, method="almanac"):
    if not isinstance(raw, dict):
        raise ValueError("请求格式不对")
    fields = ("g_year", "g_month", "g_day", "time", "zhushi_shengxiao", "event_type", "house_dir")
    out = {key: str(raw.get(key, "")).strip() for key in fields}
    year, month, day_text = _calendar_date(out["g_year"], out["g_month"], out["g_day"], False, "公历年和公历月")
    out["g_year"] = str(year)
    out["g_month"] = str(month)
    out["g_day"] = day_text
    if out["time"]:
        try:
            hour, minute = fate.parse_clock(out["time"])
        except ValueError as exc:
            raise ValueError("时间请写成 24 小时制，例如 11:30") from exc
        out["time"] = f"{hour:02d}:{minute:02d}"
    if out["event_type"] not in fate.EVENT_WORD:
        raise ValueError("请选择事项")
    if not out["house_dir"]:
        raise ValueError("请填写房屋坐向，例如坐北朝南")
    if method == "almanac":
        if out["zhushi_shengxiao"] not in fate.SHENGXIAO_TO_ZHI:
            raise ValueError("请选择生肖")
        return out
    birth_fields = ("birth_year", "birth_month", "birth_day", "birth_time", "gender")
    for key in birth_fields:
        out[key] = str(raw.get(key, "")).strip()
    birth_year, birth_month, birth_day = _calendar_date(
        out["birth_year"], out["birth_month"], out["birth_day"], True, "出生年月日"
    )
    out["birth_year"] = str(birth_year)
    out["birth_month"] = str(birth_month)
    out["birth_day"] = birth_day
    if not out["birth_time"]:
        raise ValueError("请选择出生时间")
    try:
        birth_hour, birth_minute = fate.parse_clock(out["birth_time"])
    except ValueError as exc:
        raise ValueError("出生时间请写成 24 小时制，例如 10:30") from exc
    out["birth_time"] = f"{birth_hour:02d}:{birth_minute:02d}"
    if out["gender"] not in ("男", "女"):
        raise ValueError("请选择性别")
    return out


def advice_lines(chart):
    if not chart.get("auto_time"):
        return []
    lines = []
    if chart["hard"]:
        lines.append("本日有日课禁忌，换时辰不能把这一天变成宜日。")
    elif not chart["has_clean_hour"]:
        lines.append("当天没有无禁忌的时辰，下面是扣分最少的一档。")
    if chart["hard"]:
        title = "当日时辰里相对最好"
    elif not chart["has_clean_hour"]:
        title = "相对最佳时间"
    else:
        title = "最佳时间"
    if len(chart["best_hours"]) > 1:
        title += "（并列）"
    lines.append(title + "：")
    for row in chart["best_hours"]:
        event = f"宜{chart['word']}" if row["yi_event"] else f"未写明宜{chart['word']}"
        lines.append(f"{row['span']} {row['zhi']}时 {row['ganzhi']} {row['shen']}{row['kind']} {event}")
    best_set = {row["zhi"] for row in chart["best_hours"]}
    bad_set = {row["zhi"] for row in chart["bad_hours"]}
    usable = [row for row in chart["hour_ranking"] if row["zhi"] not in best_set and row["zhi"] not in bad_set]
    usable.sort(key=lambda row: fate.DI_ZHI.index(row["zhi"]))
    if usable:
        usable_title = "其余时辰没有单独的不佳项" if chart["hard"] else "其余可用，但不如最佳"
        brief = "、".join(f"{row['span']} {row['zhi']}时{row['shen']}" for row in usable)
        lines.append(usable_title + "：" + brief)
    if chart["bad_hours"]:
        lines.append("不佳时间：")
        for row in chart["bad_hours"]:
            lines.append(f"{row['span']} {row['zhi']}时 {row['ganzhi']} {row['shen']}{row['kind']}：{'、'.join(row['bad'])}")
    else:
        lines.append("不佳时间：无")
    return lines


def _hour_lines(chart):
    lines = []
    for item in chart["hours"]:
        if chart.get("auto_time"):
            best_zhi = {row["zhi"] for row in chart["best_hours"]}
            bad_zhi = {row["zhi"] for row in chart["bad_hours"]}
            if item["zhi"] in best_zhi:
                mark = "最佳"
            elif item["zhi"] in bad_zhi:
                mark = "不佳"
            else:
                mark = ""
        else:
            mark = "所填" if item["zhi"] == chart["shi_zhi"] else ""
        event_mark = ""
        if chart["word"] in item["yi"]:
            event_mark = f"宜{chart['word']}"
        elif chart["word"] in item["ji"]:
            event_mark = f"忌{chart['word']}"
        bits = [item["span"], item["ganzhi"], f"{item['shen']}{item['kind']}"]
        if event_mark:
            bits.append(event_mark)
        if mark:
            bits.append(mark)
        lines.append("  ".join(bits))
    if not chart.get("auto_time"):
        if chart["good_hours"]:
            brief = "、".join(f"{item['span']}{item['zhi']}时{item['shen']}" for item in chart["good_hours"])
            if chart["hard"]:
                lines.append(f"对照黄道时（日课已不宜，改时辰去不掉禁忌）：{brief}")
            else:
                lines.append(f"可考虑的黄道时：{brief}")
        else:
            lines.append(f"本日没有同时满足黄道、非五不遇、不忌{chart['word']}的时辰")
    return lines


def chart_view(chart):
    cross = "晚子时，日柱与日课按次日" if chart["late_zi"] else "不跨日"
    if chart["shi_zhi"] == "子" and not chart["late_zi"]:
        cross = "早子时，日柱按当日"
    picked = "选用时辰" if chart.get("auto_time") else "所填时辰"
    year_god, month_god, time_god = chart["shishen"]
    year_hide, month_hide, day_hide, time_hide = chart["hide"]
    yuepo_today = "是" if chart["day_zhi"] == chart["yue_po"] else "否"
    suipo_today = "是" if chart["day_zhi"] == chart["sui_po"] else "否"
    relation = (
        f"冲{fate.yn(chart['chong_person'])}  "
        f"刑{fate.yn(chart['xing_person'])}  "
        f"害{fate.yn(chart['hai_person'])}  "
        f"六合{fate.yn(chart['he_person'])}  "
        f"三合{fate.yn(chart['sanhe_person'])}"
    )
    shen_lines = [
        f"喜神 {chart['xi_text']}  财神 {chart['cai_text']}  福神 {chart['fu_text']}",
        f"天乙贵人 {chart['gui_ren']}  驿马 {chart['yi_ma']}  桃花 {chart['xian_chi']}",
        f"太岁{chart['year_zhi']}在{chart['tai_sui_dir']}，岁破{chart['sui_po']}在{fate.ZHI_DIR[chart['sui_po']]}",
        f"三煞在{chart['sha_dir']}（{'、'.join(chart['sha_branches'])}）",
        f"月破 {chart['yue_po']}（本日{yuepo_today}）  岁破 {chart['sui_po']}（本日{suipo_today}）",
        f"红沙 {chart['hongsha']}（本日{fate.yn(chart['is_hongsha'])}）",
        f"{chart['term_eve'][0]}：次日交{chart['term_eve'][1]}" if chart["term_eve"] else "四离四绝：不是",
        f"与主事 {relation}",
    ]
    if chart["sit_dir"]:
        shen_lines.append(f"坐山{chart['sit_dir']}，朝向{chart['face_dir']}")
    score_lines = []
    for name, delta in chart["score_items"]:
        sign = "+" if delta > 0 else ""
        score_lines.append(f"{name} {sign}{delta}")
    score_lines.append(f"总分 {chart.get('almanac_score', chart['score'])}")
    if chart["hard"]:
        score_lines.append("不宜原因：" + "；".join(chart["hard"]))
    score_lines.extend(chart["notes"])
    almanac_conclusion = chart.get("almanac_conclusion", chart["conclusion"])
    score_lines.append(f"结论：{almanac_conclusion}（{chart['event_cn']}）")
    best_name = chart["shi_label"]
    if chart.get("auto_time") and len(chart.get("best_hours") or []) > 1:
        best_name += "等"
    civil = chart["civil"]
    view = {
        "date": civil.isoformat(),
        "date_label": f"{civil.month}月{civil.day}日",
        "best": best_name,
        "best_clock": f"{chart['hour']:02d}:{chart['minute']:02d}",
        "score": chart["score"],
        "conclusion": chart["conclusion"],
        "pillars": f"{chart['year_gz']}  {chart['month_gz']}  {chart['day_gz']}  {chart['time_gz']}",
        "blocks": [
            {
                "title": "择时",
                "lines": [
                    f"{fate.clock_text(chart)}  {chart['shi_label']}（{chart['chosen']['span']}），{cross}",
                    *advice_lines(chart),
                ],
            },
            {
                "title": "四柱",
                "lines": [
                    f"排盘日 {chart['pan_date'].isoformat()}  农历 {chart['lunar_text']}",
                    f"{chart['year_gz']}  {chart['month_gz']}  {chart['day_gz']}  {chart['time_gz']}",
                    f"纳音 {chart['nayin']}  旬空 {chart['kong']}",
                    f"上一节 {chart['prev_jie']}",
                    f"下一节 {chart['next_jie']}",
                    f"主事 {chart['animal']}（{chart['person_zhi']}）  {chart['event_cn']}  {chart['house_text'] or '房屋未填'}",
                    f"十神（日主{chart['day_gan']}）年{chart['year_gan']}{year_god} 月{chart['month_gan']}{month_god} 时{chart['time_gan']}{time_god}",
                    f"藏干 年[{year_hide}] 月[{month_hide}] 日[{day_hide}] 时[{time_hide}]",
                    f"日主月令{chart['month_zhi']}{'得令' if chart['de_ling'] else '不得令'}，{chart['dishi_day']}",
                ],
            },
            {
                "title": "日课",
                "lines": [
                    f"{chart['day_shen']}（{chart['day_kind']}）",
                    f"建除{chart['zhixing']}：{fate.JIANCHU_INFO[chart['zhixing']]}",
                    f"二十八宿 {chart['xiu']}{chart['zheng']}（{chart['xiu_luck']}）",
                    f"{picked} {chart['chosen']['ganzhi']} {chart['chosen']['shen']}（{chart['chosen']['kind']}）",
                    "宜：" + "、".join(chart["day_yi"]),
                    "忌：" + "、".join(chart["day_ji"]),
                    "吉神：" + ("、".join(chart["ji_shen"]) if chart["ji_shen"] else "无"),
                    "凶煞：" + ("、".join(chart["xiong"]) if chart["xiong"] else "无"),
                    f"彭祖 {chart['pengzu']}",
                    f"日冲 {chart['day_chong']}  日煞 {chart['day_sha']}",
                ],
            },
            {"title": "神煞", "lines": shen_lines},
            {"title": "十二时辰", "lines": _hour_lines(chart)},
            {"title": "通书计分" if chart.get("use_bazi") else "计分", "lines": score_lines},
        ],
    }
    if chart.get("use_bazi"):
        view["blocks"].insert(0, {"title": "命主", "lines": chart["natal_lines"]})
        view["blocks"].insert(-1, {"title": "命理", "lines": chart["bazi_lines"]})
        for block in view["blocks"]:
            if block["title"] == "四柱":
                block["title"] = "日课四柱"
    show_almanac = bool(chart.get("show_almanac"))
    show_bazi = bool(chart.get("show_bazi"))
    almanac_conclusion = chart.get("almanac_conclusion", chart["conclusion"])
    if show_almanac and show_bazi:
        view["conclusion"] = _worse(almanac_conclusion, chart["conclusion"])
    view["almanac_score"] = chart.get("almanac_score", chart["score"]) if show_almanac else None
    view["almanac_conclusion"] = almanac_conclusion if show_almanac else None
    view["bazi_score"] = chart.get("bazi_score") if show_bazi else None
    view["bazi_conclusion"] = chart["conclusion"] if show_bazi else None
    return view


def _worse(left, right):
    rank = {"宜": 0, "宜改时": 1, "可备选": 2, "平": 3, "不宜": 4}
    if rank.get(left, 0) >= rank.get(right, 0):
        return left
    return right


def _flag(raw, key):
    value = raw.get(key, False)
    if isinstance(value, str):
        return value.strip().lower() in ("1", "true", "yes", "on")
    return bool(value)


def build_query(raw):
    if not isinstance(raw, dict):
        raise ValueError("请求格式不对")
    use_almanac = _flag(raw, "use_almanac")
    use_bazi = _flag(raw, "use_bazi")
    if not use_almanac and not use_bazi:
        if "method" in raw and "use_almanac" not in raw and "use_bazi" not in raw:
            method = str(raw.get("method", "")).strip()
            use_almanac = method == "almanac"
            use_bazi = method == "bazi"
    if not use_almanac and not use_bazi:
        raise ValueError("请勾选通书或八字")
    cleaned = normalize_query(raw, "bazi" if use_bazi else "almanac")
    if use_almanac and cleaned["zhushi_shengxiao"] not in fate.SHENGXIAO_TO_ZHI:
        raise ValueError("请选择生肖")
    natal = None
    if use_bazi:
        natal = fate_bazi.build_natal(cleaned)
        if not use_almanac:
            cleaned["zhushi_shengxiao"] = natal["animal"]
        if cleaned["g_day"]:
            target = date(int(cleaned["g_year"]), int(cleaned["g_month"]), int(cleaned["g_day"]))
            if target < natal["birth"]:
                raise ValueError("要排的日子早于出生")
    if cleaned["g_day"]:
        charts = [fate.analyze(cleaned)]
        span = "day"
    else:
        charts = fate.scan_month(cleaned, quiet=True)
        span = "month"
    if use_bazi:
        charts = [chart for chart in charts if chart["civil"] >= natal["birth"]]
        if not charts:
            raise ValueError("这个月都在出生之前")
        if use_almanac:
            charts = [fate_bazi.attach_both(chart, natal) for chart in charts]
            charts.sort(key=fate_bazi.total_rank)
        else:
            charts = [fate_bazi.finish(chart, natal) for chart in charts]
            charts.sort(key=fate_bazi.bazi_rank)
    else:
        charts.sort(key=fate.chart_rank)
    for chart in charts:
        chart["show_almanac"] = use_almanac
        chart["show_bazi"] = use_bazi
    items = [chart_view(chart) for chart in charts]
    best = items[0]
    rejected = sum(1 for item in items if item["conclusion"] == "不宜")
    if use_almanac and use_bazi:
        total = best["almanac_score"] + best["bazi_score"]
        core = f"通书 {best['almanac_score']} 分，八字 {best['bazi_score']} 分，合计 {total} 分"
        if span == "month":
            headline = (
                f"{charts[0]['month_scan']}共 {len(items)} 天，不宜 {rejected} 天。"
                f"总分最佳 {best['date_label']} {best['best']} {best['best_clock']}，{core}"
            )
        else:
            headline = f"{best['date_label']} {best['best']} {best['best_clock']}，{best['conclusion']}。{core}"
    elif use_bazi:
        if span == "month":
            headline = (
                f"{natal['brief']}。{charts[0]['month_scan']}共 {len(items)} 天，不宜 {rejected} 天。"
                f"命理最佳 {best['date_label']} {best['best']} {best['best_clock']}，{best['bazi_score']}分"
            )
        else:
            headline = (
                f"{natal['brief']}。{best['date_label']} {best['best']} {best['best_clock']}，"
                f"{best['bazi_conclusion']} {best['bazi_score']}分"
            )
    elif span == "month":
        headline = (
            f"{charts[0]['month_scan']}共 {len(items)} 天，不宜 {rejected} 天。"
            f"最佳 {best['date_label']} {best['best']} {best['best_clock']}，{best['almanac_score']}分"
        )
    else:
        headline = (
            f"{best['date_label']} {best['best']} {best['best_clock']}，"
            f"{best['almanac_conclusion']} {best['almanac_score']}分"
        )
    return {
        "use_almanac": use_almanac,
        "use_bazi": use_bazi,
        "mode": span,
        "headline": headline,
        "items": items,
    }
