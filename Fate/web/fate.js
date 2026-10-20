/*!
 * 正式择日 v4.0 —— 纯前端 JavaScript 版
 * 由 fate.py / fate_bazi.py / fate_api.py 翻译而来，
 * 历法、四柱、节气、二十八宿、建除、黄黑道、通书宜忌使用 lunar-javascript（寿星天文历）。
 * 这是传统通书择日，不是科学预测。
 * 对外暴露 window.Fate = { buildQuery }，与后端 /api/calc 返回结构一致。
 */
(function (global) {
  "use strict";

  // ---- 日期工具（对应 Python datetime.date） ----
  function pad2(n) { return String(n).padStart(2, "0"); }
  function pad4(n) { return String(n).padStart(4, "0"); }
  function mkDate(y, m, d) { return new Date(y, m - 1, d); }
  function iso(d) { return d.getFullYear() + "-" + pad2(d.getMonth() + 1) + "-" + pad2(d.getDate()); }
  function ordinal(d) { return Math.floor(d.getTime() / 86400000); }
  function addDays(d, n) { const r = new Date(d.getTime()); r.setDate(r.getDate() + n); return r; }
  function monthDays(y, m) { return new Date(y, m, 0).getDate(); }
  function diffDays(a, b) { return Math.round((a.getTime() - b.getTime()) / 86400000); }
  function pyList(arr) { return "[" + arr.map(function (x) { return "'" + x + "'"; }).join(", ") + "]"; }

  // ---- 天干地支 ----
  var TIAN_GAN = ["甲", "乙", "丙", "丁", "戊", "己", "庚", "辛", "壬", "癸"];
  var DI_ZHI = ["子", "丑", "寅", "卯", "辰", "巳", "午", "未", "申", "酉", "戌", "亥"];

  var SHENGXIAO_TO_ZHI = {
    "鼠": "子", "牛": "丑", "虎": "寅", "兔": "卯",
    "龙": "辰", "蛇": "巳", "马": "午", "羊": "未",
    "猴": "申", "鸡": "酉", "狗": "戌", "猪": "亥"
  };

  var CHONG = {
    "子": "午", "丑": "未", "寅": "申", "卯": "酉", "辰": "戌", "巳": "亥",
    "午": "子", "未": "丑", "申": "寅", "酉": "卯", "戌": "辰", "亥": "巳"
  };
  var HAI = {
    "子": "未", "丑": "午", "寅": "巳", "卯": "辰", "辰": "卯", "巳": "寅",
    "午": "丑", "未": "子", "申": "亥", "酉": "戌", "戌": "酉", "亥": "申"
  };
  var XING = {
    "子": ["卯"], "卯": ["子"],
    "寅": ["巳", "申"], "巳": ["寅", "申"], "申": ["寅", "巳"],
    "丑": ["未", "戌"], "未": ["丑", "戌"], "戌": ["丑", "未"],
    "辰": ["辰"], "午": ["午"], "酉": ["酉"], "亥": ["亥"]
  };
  var LIU_HE = {
    "子": "丑", "丑": "子", "寅": "亥", "亥": "寅", "卯": "戌", "戌": "卯",
    "辰": "酉", "酉": "辰", "巳": "申", "申": "巳", "午": "未", "未": "午"
  };
  var SAN_HE = {
    "申": ["申", "子", "辰"], "子": ["申", "子", "辰"], "辰": ["申", "子", "辰"],
    "亥": ["亥", "卯", "未"], "卯": ["亥", "卯", "未"], "未": ["亥", "卯", "未"],
    "寅": ["寅", "午", "戌"], "午": ["寅", "午", "戌"], "戌": ["寅", "午", "戌"],
    "巳": ["巳", "酉", "丑"], "酉": ["巳", "酉", "丑"], "丑": ["巳", "酉", "丑"]
  };

  // 驿马、咸池以三合局为准。
  var YI_MA = {};
  var XIAN_CHI = {};
  (function () {
    var horses = [["寅", ["申", "子", "辰"]], ["申", ["寅", "午", "戌"]],
                  ["亥", ["巳", "酉", "丑"]], ["巳", ["亥", "卯", "未"]]];
    var peaches = [["酉", ["申", "子", "辰"]], ["卯", ["寅", "午", "戌"]],
                   ["午", ["巳", "酉", "丑"]], ["子", ["亥", "卯", "未"]]];
    horses.forEach(function (p) { p[1].forEach(function (z) { YI_MA[z] = p[0]; }); });
    peaches.forEach(function (p) { p[1].forEach(function (z) { XIAN_CHI[z] = p[0]; }); });
  })();

  // 三煞：申子辰煞南，寅午戌煞北，亥卯未煞西，巳酉丑煞东。
  var SAN_SHA = {};
  (function () {
    var groups = [
      ["南", ["申", "子", "辰"], ["巳", "午", "未"]],
      ["北", ["寅", "午", "戌"], ["亥", "子", "丑"]],
      ["西", ["亥", "卯", "未"], ["申", "酉", "戌"]],
      ["东", ["巳", "酉", "丑"], ["寅", "卯", "辰"]]
    ];
    groups.forEach(function (g) { g[1].forEach(function (y) { SAN_SHA[y] = [g[0], g[2]]; }); });
  })();

  var ZHI_DIR = {
    "子": "北", "丑": "东北", "寅": "东北", "卯": "东",
    "辰": "东南", "巳": "东南", "午": "南", "未": "西南",
    "申": "西南", "酉": "西", "戌": "西北", "亥": "西北"
  };
  var DIR_KEYS = ["东北", "东南", "西南", "西北", "东", "南", "西", "北"];
  var BAGUA_DIR = {
    "坎": "北", "艮": "东北", "震": "东", "巽": "东南",
    "离": "南", "坤": "西南", "兑": "西", "乾": "西北"
  };

  // 天乙贵人按日干。
  var TIAN_YI = {
    "甲": ["丑", "未"], "戊": ["丑", "未"], "庚": ["丑", "未"],
    "乙": ["子", "申"], "己": ["子", "申"],
    "丙": ["亥", "酉"], "丁": ["亥", "酉"],
    "壬": ["卯", "巳"], "癸": ["卯", "巳"],
    "辛": ["午", "寅"]
  };

  // 五不遇时：时干克日干。
  var WU_BU_YU = {
    "甲": "庚", "乙": "辛", "丙": "壬", "丁": "癸", "戊": "甲",
    "己": "乙", "庚": "丙", "辛": "丁", "壬": "戊", "癸": "己"
  };

  var GAN_WUXING = {
    "甲": "木", "乙": "木", "丙": "火", "丁": "火", "戊": "土",
    "己": "土", "庚": "金", "辛": "金", "壬": "水", "癸": "水"
  };
  var ZHI_WUXING = {
    "寅": "木", "卯": "木", "巳": "火", "午": "火",
    "申": "金", "酉": "金", "亥": "水", "子": "水",
    "辰": "土", "戌": "土", "丑": "土", "未": "土"
  };

  var JIANCHU_INFO = {
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
    "闭": "宜守成收纳，忌开创外出"
  };
  var JIANCHU_SCORE = {
    "成": 8, "开": 8, "定": 5, "除": 2, "满": 2,
    "平": 0, "建": -2, "执": -2, "收": -2,
    "危": -6, "闭": -6, "破": -10
  };

  var BAD_XIU = {
    "marry": new Set(["心", "昴", "参", "鬼"]),
    "open": new Set(["虚", "危", "心", "参"]),
    "earth": new Set(["危"]),
    "travel": new Set()
  };
  var EVENT_WORD = { "marry": "嫁娶", "open": "开市", "earth": "动土", "travel": "出行" };
  var EVENT_CN = { "marry": "嫁娶", "open": "开市", "earth": "动土", "travel": "出行" };
  var SILI = new Set(["春分", "秋分", "夏至", "冬至"]);
  var SIJUE = new Set(["立春", "立夏", "立秋", "立冬"]);
  var DE_DI = new Set(["长生", "冠带", "临官", "帝旺"]);

  var SHICHEN_CLOCK = {
    "子": "00:30", "丑": "01:30", "寅": "03:30", "卯": "05:30",
    "辰": "07:30", "巳": "09:30", "午": "11:30", "未": "13:30",
    "申": "15:30", "酉": "17:30", "戌": "19:30", "亥": "21:30"
  };

  var CONCLUSION_RANK = { "宜": 0, "宜改时": 1, "可备选": 2, "平": 3, "不宜": 4 };

  // ---- 工具函数 ----
  function yn(flag) { return flag ? "是" : "否"; }

  function clockToShichen(hour) {
    if (hour === 23 || hour === 0) return ["子", hour === 23];
    var names = ["丑", "丑", "寅", "寅", "卯", "卯", "辰", "辰", "巳", "巳",
                 "午", "午", "未", "未", "申", "申", "酉", "酉", "戌", "戌", "亥", "亥"];
    return [names[hour - 1], false];
  }

  function shichenLabel(zhi, lateZi, hour) {
    if (zhi === "子" && lateZi) return "晚子时";
    if (zhi === "子" && hour === 0) return "早子时";
    return zhi + "时";
  }

  function parseClock(text) {
    var parts = String(text).trim().split(":");
    if (parts.length !== 2) throw new Error("时间须写成 HH:MM，例如 11:30 或 23:05");
    var hour = parseInt(parts[0], 10);
    var minute = parseInt(parts[1], 10);
    if (!(hour >= 0 && hour <= 23 && minute >= 0 && minute <= 59)) {
      throw new Error("时间超出 00:00-23:59");
    }
    return [hour, minute];
  }

  function parseHouse(text) {
    text = String(text).trim();
    if (text.indexOf("朝") < 0 || text.indexOf("坐") !== 0) return [null, null];
    var rest = text.slice(1);
    var idx = rest.indexOf("朝");
    var sitText = rest.slice(0, idx);
    var faceText = rest.slice(idx + 1);
    function cut(token) {
      for (var i = 0; i < DIR_KEYS.length; i++) {
        if (token.indexOf(DIR_KEYS[i]) === 0) return DIR_KEYS[i];
      }
      return null;
    }
    return [cut(sitText), cut(faceText)];
  }

  function baguaToDir(name) { return BAGUA_DIR[name] || name; }

  function hongshaZhi(lunarMonth) {
    var month = Math.abs(parseInt(lunarMonth, 10));
    if ([1, 4, 7, 10].indexOf(month) >= 0) return "酉";
    if ([2, 5, 8, 11].indexOf(month) >= 0) return "巳";
    if ([3, 6, 9, 12].indexOf(month) >= 0) return "丑";
    return null;
  }

  function isXing(dayZhi, otherZhi) { return XING[dayZhi].indexOf(otherZhi) >= 0; }

  function eveTerm(almanac, panDate) {
    var term = almanac.getNextJieQi();
    var solar = term.getSolar();
    var termDay = mkDate(solar.getYear(), solar.getMonth(), solar.getDay());
    if (diffDays(termDay, panDate) !== 1) return null;
    var name = term.getName();
    if (SILI.has(name)) return ["四离", name];
    if (SIJUE.has(name)) return ["四绝", name];
    return null;
  }

  function solarOf(day, hour, minute) {
    return Solar.fromYmdHms(day.getFullYear(), day.getMonth() + 1, day.getDate(), hour, minute, 0);
  }

  function jieText(jie) {
    var solar = jie.getSolar();
    return jie.getName() + "（" + solar.toYmdHms() + "）";
  }

  function collectHours(almanac) {
    var rows = [];
    almanac.getTimes().forEach(function (item) {
      if (item.getMinHm() === "23:00") return;
      var zhi = item.getZhi();
      var span = zhi === "子" ? "前一日23:00-当日00:59" : (item.getMinHm() + "-" + item.getMaxHm());
      rows.push({
        gan: item.getGan(),
        zhi: zhi,
        ganzhi: item.getGanZhi(),
        span: span,
        shen: item.getTianShen(),
        luck: item.getTianShenLuck(),
        kind: item.getTianShenType(),
        yi: Array.prototype.slice.call(item.getYi()),
        ji: Array.prototype.slice.call(item.getJi())
      });
    });
    return rows;
  }

  function hideText(gans, gods) {
    return gans.map(function (gan, i) { return gan + gods[i]; }).join("、");
  }

  function addScore(bucket, name, delta) {
    if (delta) bucket.push([name, delta]);
  }

  function clockText(chart) {
    return iso(chart.civil) + " " + pad2(chart.hour) + ":" + pad2(chart.minute);
  }

  function hourAdjustments(dayGan, personZhi, word, event, kong, yiMa, xianChi, item, label) {
    var items = [];
    var bad = [];
    if (item.yi.indexOf(word) >= 0) items.push([label + "宜" + word, 8]);
    if (item.ji.indexOf(word) >= 0) { items.push([label + "忌" + word, -10]); bad.push("忌" + word); }
    if (item.kind === "黄道") {
      items.push(["时值" + item.shen + "（黄道）", 8]);
    } else {
      items.push(["时值" + item.shen + "（黑道）", -6]);
      bad.push("黑道");
    }
    if (TIAN_YI[dayGan].indexOf(item.zhi) >= 0) items.push(["时支临天乙贵人", 8]);
    if (CHONG[item.zhi] === personZhi) { items.push(["时支冲主事", -8]); bad.push("冲主事"); }
    if (item.gan === WU_BU_YU[dayGan]) { items.push(["五不遇时", -12]); bad.push("五不遇时"); }
    if (kong.indexOf(item.zhi) >= 0) { items.push(["时落旬空", -4]); bad.push("旬空"); }
    if (event === "marry" && item.zhi === xianChi) items.push(["时支咸池桃花", 4]);
    if ((event === "open" || event === "travel") && item.zhi === yiMa) items.push(["时支驿马", 6]);
    return [items, bad];
  }

  function rankHours(chart) {
    var dayBase = chart.score - chart.hour_delta;
    var rows = [];
    chart.hours.forEach(function (item) {
      var r = hourAdjustments(chart.day_gan, chart.person_zhi, chart.word, chart.event,
        chart.kong, chart.yi_ma, chart.xian_chi, item, "本时辰");
      var parts = r[0], bad = r[1];
      var delta = parts.reduce(function (s, p) { return s + p[1]; }, 0);
      rows.push({
        span: item.span, zhi: item.zhi, ganzhi: item.ganzhi, shen: item.shen, kind: item.kind,
        delta: delta, total: dayBase + delta, bad: bad, yi_event: item.yi.indexOf(chart.word) >= 0
      });
    });
    rows.sort(function (a, b) {
      if (b.total !== a.total) return b.total - a.total;
      return DI_ZHI.indexOf(a.zhi) - DI_ZHI.indexOf(b.zhi);
    });
    return rows;
  }

  function pickBest(ranking) {
    var clean = ranking.filter(function (row) { return row.bad.length === 0; });
    var pool = clean.length ? clean : ranking;
    var bestTotal = Math.max.apply(null, pool.map(function (row) { return row.total; }));
    var tied = pool.filter(function (row) { return row.total === bestTotal; });
    tied.sort(function (a, b) { return DI_ZHI.indexOf(a.zhi) - DI_ZHI.indexOf(b.zhi); });
    return tied;
  }

  function chooseDayHours(raw) {
    var probeRaw = Object.assign({}, raw);
    probeRaw.time = "12:00";
    delete probeRaw._auto_time;
    var probe = analyze(probeRaw);
    var ranking = rankHours(probe);
    var best = pickBest(ranking);
    var pickedRaw = Object.assign({}, raw);
    pickedRaw.time = SHICHEN_CLOCK[best[0].zhi];
    pickedRaw._auto_time = "yes";
    var chart = analyze(pickedRaw);
    chart.auto_time = true;
    chart.hour_ranking = ranking;
    chart.best_hours = best;
    chart.bad_hours = ranking.filter(function (row) { return row.bad.length > 0; })
      .sort(function (a, b) { return DI_ZHI.indexOf(a.zhi) - DI_ZHI.indexOf(b.zhi); });
    chart.has_clean_hour = ranking.some(function (row) { return row.bad.length === 0; });
    return chart;
  }

  function analyze(raw) {
    if (String(raw.time == null ? "" : raw.time).trim() === "") {
      return chooseDayHours(raw);
    }
    var hourLabel = raw._auto_time === "yes" ? "选用时辰" : "所填时辰";
    var year = parseInt(raw.g_year, 10);
    var month = parseInt(raw.g_month, 10);
    var dayNum = parseInt(raw.g_day, 10);
    var civil = mkDate(year, month, dayNum);
    var clock = parseClock(raw.time);
    var hour = clock[0], minute = clock[1];
    var sc = clockToShichen(hour);
    var shiZhi = sc[0], lateZi = sc[1];
    var animal = String(raw.zhushi_shengxiao).trim();
    if (!SHENGXIAO_TO_ZHI[animal]) throw new Error("无法识别生肖「" + animal + "」");
    var event = String(raw.event_type).trim();
    if (!EVENT_WORD[event]) throw new Error("event_type 只能是 marry、open、earth、travel");
    var houseText = String(raw.house_dir == null ? "" : raw.house_dir).trim();
    var ph = parseHouse(houseText);
    var sitDir = ph[0], faceDir = ph[1];
    var personZhi = SHENGXIAO_TO_ZHI[animal];
    var word = EVENT_WORD[event];
    var panDate = lateZi ? addDays(civil, 1) : civil;

    var exact = solarOf(civil, hour, minute).getLunar();
    var eight = exact.getEightChar();
    eight.setSect(1);
    var almanac = solarOf(panDate, 12, 0).getLunar();

    var dayGan = eight.getDayGan();
    var dayZhi = eight.getDayZhi();
    var monthZhi = eight.getMonthZhi();
    var yearZhi = eight.getYearZhi();
    var timeGan = eight.getTimeGan();
    var timeZhi = eight.getTimeZhi();
    if (timeZhi !== shiZhi) throw new Error("时辰换算与排盘不一致：" + shiZhi + " / " + timeZhi);
    if ((dayGan + dayZhi) !== almanac.getDayInGanZhi()) throw new Error("晚子时日柱与次日日课不一致");

    var hours = collectHours(almanac);
    var chosen = hours.find(function (item) { return item.zhi === shiZhi; });
    var dayYi = Array.prototype.slice.call(almanac.getDayYi());
    var dayJi = Array.prototype.slice.call(almanac.getDayJi());
    var jiShen = Array.prototype.slice.call(almanac.getDayJiShen());
    var xiong = Array.prototype.slice.call(almanac.getDayXiongSha());
    var xiu = almanac.getXiu();
    var xiuLuck = almanac.getXiuLuck();
    var zhixing = almanac.getZhiXing();
    var dayKind = almanac.getDayTianShenType();
    var lunarMonth = almanac.getMonth();
    var hongsha = hongshaZhi(lunarMonth);
    var termEve = eveTerm(almanac, panDate);
    var sha = SAN_SHA[yearZhi];
    var shaDir = sha[0], shaBranches = sha[1];
    var taiSuiDir = ZHI_DIR[yearZhi];
    var suiPo = CHONG[yearZhi];
    var yuePo = CHONG[monthZhi];

    var inDayYi = dayYi.indexOf(word) >= 0;
    var inDayJi = dayJi.indexOf(word) >= 0;
    var inHourJi = chosen.ji.indexOf(word) >= 0;
    var wuBuYu = timeGan === WU_BU_YU[dayGan];
    var isHongsha = dayZhi === hongsha;
    var isYuepo = dayZhi === yuePo;
    var isSuipo = dayZhi === suiPo;
    var inSansha = shaBranches.indexOf(dayZhi) >= 0;
    var chongPerson = CHONG[dayZhi] === personZhi;
    var xingPerson = isXing(dayZhi, personZhi);
    var haiPerson = HAI[dayZhi] === personZhi;
    var hePerson = LIU_HE[dayZhi] === personZhi;
    var sanhePerson = SAN_HE[dayZhi].indexOf(personZhi) >= 0 && personZhi !== dayZhi;
    var hourChong = CHONG[timeZhi] === personZhi;
    var guiRen = TIAN_YI[dayGan];
    var deLing = ZHI_WUXING[monthZhi] === GAN_WUXING[dayGan];
    var dishiDay = eight.getDayDiShi();
    var deDi = DE_DI.has(dishiDay);
    var kong = Array.prototype.slice.call(eight.getDayXunKong());
    var xiDir = baguaToDir(almanac.getDayPositionXi());
    var caiDir = baguaToDir(almanac.getDayPositionCai());
    var fuDir = baguaToDir(almanac.getDayPositionFu());
    var faceXi = faceDir != null && faceDir === xiDir;
    var faceCai = faceDir != null && faceDir === caiDir;
    var sitTaisui = sitDir != null && sitDir === taiSuiDir;
    var sitSuipo = sitDir != null && sitDir === ZHI_DIR[suiPo];
    var sitSansha = sitDir != null && sitDir === shaDir;

    var scoreItems = [];
    var hard = [];
    var notes = [];

    addScore(scoreItems, "通书日宜" + word, inDayYi ? 18 : 0);
    addScore(scoreItems, "通书日忌" + word, inDayJi ? -22 : 0);
    addScore(scoreItems, "日值" + almanac.getDayTianShen() + "（" + dayKind + "）", dayKind === "黄道" ? 8 : -6);
    addScore(scoreItems, "建除" + zhixing, JIANCHU_SCORE[zhixing]);
    addScore(scoreItems, "二十八宿" + xiu + "（" + xiuLuck + "）", xiuLuck === "吉" ? 6 : -6);
    if (jiShen.indexOf("天德") >= 0) addScore(scoreItems, "天德", 8);
    if (jiShen.indexOf("月德") >= 0) addScore(scoreItems, "月德", 8);
    if (jiShen.indexOf("天德合") >= 0) addScore(scoreItems, "天德合", 5);
    if (jiShen.indexOf("月德合") >= 0) addScore(scoreItems, "月德合", 5);
    addScore(scoreItems, "日主得令", deLing ? 4 : 0);
    addScore(scoreItems, "日主" + dishiDay, deDi ? 4 : 0);
    addScore(scoreItems, "与主事六合", hePerson ? 6 : 0);
    addScore(scoreItems, "与主事三合", sanhePerson ? 4 : 0);
    addScore(scoreItems, "冲主事生肖", chongPerson ? -16 : 0);
    addScore(scoreItems, "刑主事生肖", xingPerson ? -8 : 0);
    addScore(scoreItems, "害主事生肖", haiPerson ? -6 : 0);
    addScore(scoreItems, "岁破", isSuipo ? -20 : 0);
    addScore(scoreItems, "月破", isYuepo ? -20 : 0);
    addScore(scoreItems, "三煞", inSansha ? -12 : 0);
    addScore(scoreItems, "红沙", isHongsha ? -16 : 0);
    if (termEve) addScore(scoreItems, termEve[0], -18);
    if (event === "marry" && faceXi) addScore(scoreItems, "房屋朝向合喜神", 4);
    if (event === "open" && faceCai) addScore(scoreItems, "房屋朝向合财神", 4);
    if (event === "earth" && sitTaisui) addScore(scoreItems, "坐山犯太岁", -15);
    if (event === "earth" && sitSuipo) addScore(scoreItems, "坐山犯岁破", -12);
    if (event === "earth" && sitSansha) addScore(scoreItems, "坐山犯三煞", -15);

    if (inDayJi) hard.push("通书日忌" + word);
    if (isSuipo) hard.push("岁破（太岁" + yearZhi + "，岁破在" + suiPo + "）");
    if (isYuepo) hard.push("月破（月令" + monthZhi + "，月破在" + yuePo + "）");
    if (isHongsha && (event === "marry" || event === "travel")) hard.push("红沙日（本月红沙在" + hongsha + "）");
    if (termEve && (event === "marry" || event === "open" || event === "earth")) hard.push(termEve[0] + "（次日" + termEve[1] + "）");
    if (chongPerson && event === "marry") hard.push("日支" + dayZhi + "冲主事" + animal + "（" + personZhi + "）");
    if (BAD_XIU[event].has(xiu)) hard.push("二十八宿" + xiu + "为" + EVENT_CN[event] + "忌宿");
    if (event === "earth" && inSansha) hard.push("日支" + dayZhi + "落三煞（" + shaDir + "，" + shaBranches.join("、") + "）");
    if (event === "earth" && sitTaisui) hard.push("坐山" + sitDir + "犯太岁（" + taiSuiDir + "）");
    if (event === "earth" && sitSansha) hard.push("坐山" + sitDir + "犯三煞（" + shaDir + "）");
    if (isHongsha && event === "earth") notes.push("红沙日，地支" + hongsha + "，动土宜再避");
    if (sitDir == null || faceDir == null) notes.push("房屋坐向未按「坐某朝某」识别，方位合参未计入");
    if (hard.length === 0) {
      if (hourChong) notes.push(hourLabel + "冲主事生肖，可改用其他黄道时");
      if (wuBuYu) notes.push(hourLabel + "为五不遇时，大事宜改时");
      if (inHourJi && !inDayJi) notes.push("日课未忌" + word + "，但" + hourLabel + "忌" + word);
    }

    var hr = hourAdjustments(dayGan, personZhi, word, event, kong, YI_MA[dayZhi], XIAN_CHI[dayZhi], chosen, hourLabel);
    var hourItems = hr[0];
    hourItems.forEach(function (p) { addScore(scoreItems, p[0], p[1]); });
    var score = scoreItems.reduce(function (s, p) { return s + p[1]; }, 0);
    var conclusion;
    if (hard.length > 0) {
      conclusion = "不宜";
    } else if (inDayYi && (inHourJi || wuBuYu || hourChong)) {
      conclusion = "宜改时";
    } else if (inDayYi && chosen.kind === "黄道") {
      conclusion = "宜";
    } else if (inDayYi || score >= 12) {
      conclusion = "可备选";
    } else {
      conclusion = "平";
    }

    var goodHours = [];
    hours.forEach(function (item) {
      if (item.kind !== "黄道") return;
      if (item.gan === WU_BU_YU[dayGan]) return;
      if (item.ji.indexOf(word) >= 0) return;
      goodHours.push(item);
    });

    return {
      civil: civil,
      hour: hour,
      minute: minute,
      late_zi: lateZi,
      shi_zhi: shiZhi,
      shi_label: shichenLabel(shiZhi, lateZi, hour),
      pan_date: panDate,
      animal: animal,
      person_zhi: personZhi,
      event: event,
      event_cn: EVENT_CN[event],
      word: word,
      house_text: houseText,
      sit_dir: sitDir,
      face_dir: faceDir,
      year_gz: eight.getYear(),
      month_gz: eight.getMonth(),
      day_gz: eight.getDay(),
      time_gz: eight.getTime(),
      day_gan: dayGan,
      day_zhi: dayZhi,
      month_zhi: monthZhi,
      year_zhi: yearZhi,
      year_gan: eight.getYearGan(),
      month_gan: eight.getMonthGan(),
      time_gan: timeGan,
      nayin: eight.getDayNaYin(),
      kong: kong,
      dishi_day: dishiDay,
      shishen: [eight.getYearShiShenGan(), eight.getMonthShiShenGan(), eight.getTimeShiShenGan()],
      hide: [
        hideText(eight.getYearHideGan(), eight.getYearShiShenZhi()),
        hideText(eight.getMonthHideGan(), eight.getMonthShiShenZhi()),
        hideText(eight.getDayHideGan(), eight.getDayShiShenZhi()),
        hideText(eight.getTimeHideGan(), eight.getTimeShiShenZhi())
      ],
      lunar_text: almanac.toString(),
      lunar_month: lunarMonth,
      prev_jie: jieText(exact.getPrevJie()),
      next_jie: jieText(exact.getNextJie()),
      xiu: xiu,
      xiu_luck: xiuLuck,
      zheng: almanac.getZheng(),
      zhixing: zhixing,
      day_shen: almanac.getDayTianShen(),
      day_kind: dayKind,
      day_yi: dayYi,
      day_ji: dayJi,
      ji_shen: jiShen,
      xiong: xiong,
      pengzu: almanac.getPengZuGan() + "；" + almanac.getPengZuZhi(),
      day_chong: almanac.getDayChong() + "（" + almanac.getDayChongShengXiao() + "）",
      day_sha: almanac.getDaySha(),
      xi_text: almanac.getDayPositionXiDesc() + "（" + xiDir + "）",
      cai_text: almanac.getDayPositionCaiDesc() + "（" + caiDir + "）",
      fu_text: almanac.getDayPositionFuDesc() + "（" + fuDir + "）",
      gui_ren: guiRen.join("、"),
      yi_ma: YI_MA[dayZhi],
      xian_chi: XIAN_CHI[dayZhi],
      sha_dir: shaDir,
      sha_branches: shaBranches,
      tai_sui_dir: taiSuiDir,
      sui_po: suiPo,
      yue_po: yuePo,
      hongsha: hongsha,
      is_hongsha: isHongsha,
      term_eve: termEve,
      de_ling: deLing,
      chosen: chosen,
      hours: hours,
      good_hours: goodHours,
      chong_person: chongPerson,
      xing_person: xingPerson,
      hai_person: haiPerson,
      he_person: hePerson,
      sanhe_person: sanhePerson,
      score_items: scoreItems,
      score: score,
      hour_delta: hourItems.reduce(function (s, p) { return s + p[1]; }, 0),
      auto_time: raw._auto_time === "yes",
      hard: hard,
      notes: notes,
      conclusion: conclusion
    };
  }

  function chartRank(chart) {
    var r = CONCLUSION_RANK[chart.conclusion];
    if (r == null) r = 9;
    return [r, -chart.score, ordinal(chart.civil)];
  }

  function scanMonth(raw) {
    var year = parseInt(raw.g_year, 10);
    var month = parseInt(raw.g_month, 10);
    if (month < 1 || month > 12) throw new Error("月份须在 1 到 12");
    var last = monthDays(year, month);
    var label = year + "年" + month + "月";
    var charts = [];
    for (var day = 1; day <= last; day++) {
      var dayRaw = Object.assign({}, raw);
      dayRaw.g_day = String(day);
      var chart;
      try {
        chart = analyze(dayRaw);
      } catch (exc) {
        throw new Error(year + "-" + pad2(month) + "-" + pad2(day) + "：" + exc.message);
      }
      chart.month_scan = label;
      charts.push(chart);
    }
    return charts;
  }

  // ---- 八字（对应 fate_bazi.py） ----
  var STEMS = "甲乙丙丁戊己庚辛壬癸";
  var ELEMENTS = ["木", "木", "火", "火", "土", "土", "金", "金", "水", "水"];
  var HIDE = {
    "子": ["癸"],
    "丑": ["己", "癸", "辛"],
    "寅": ["甲", "丙", "戊"],
    "卯": ["乙"],
    "辰": ["戊", "乙", "癸"],
    "巳": ["丙", "庚", "戊"],
    "午": ["丁", "己"],
    "未": ["己", "丁", "乙"],
    "申": ["庚", "壬", "戊"],
    "酉": ["辛"],
    "戌": ["戊", "辛", "丁"],
    "亥": ["壬", "甲"]
  };
  var YIN = new Set(["正印", "偏印"]);
  var BI = new Set(["比肩", "劫财"]);
  var SHI = new Set(["食神", "伤官"]);
  var CAI = new Set(["正财", "偏财"]);
  var GUAN = new Set(["正官", "七杀"]);
  var HELP = new Set(["正印", "偏印", "比肩", "劫财"]);
  var DRAIN = new Set(["食神", "伤官", "正财", "偏财", "正官", "七杀"]);
  var ZHENG = new Set(["正印", "食神", "正官", "正财"]);
  var PIAN = new Set(["七杀", "劫财", "伤官"]);
  var GOD_ORDER = ["正印", "偏印", "比肩", "劫财", "食神", "伤官", "正财", "偏财", "正官", "七杀"];
  var ZHI_ANIMAL = {};
  Object.keys(SHENGXIAO_TO_ZHI).forEach(function (animalKey) {
    ZHI_ANIMAL[SHENGXIAO_TO_ZHI[animalKey]] = animalKey;
  });

  var GENERATES = { "木": "火", "火": "土", "土": "金", "金": "水", "水": "木" };
  var CONTROLS = { "木": "土", "土": "水", "水": "火", "火": "金", "金": "木" };

  function tenGod(dayGan, otherGan) {
    var di = STEMS.indexOf(dayGan);
    var oi = STEMS.indexOf(otherGan);
    var de = ELEMENTS[di];
    var oe = ELEMENTS[oi];
    var same = (di % 2) === (oi % 2);
    if (de === oe) return same ? "比肩" : "劫财";
    if (GENERATES[oe] === de) return same ? "偏印" : "正印";
    if (GENERATES[de] === oe) return same ? "食神" : "伤官";
    if (CONTROLS[oe] === de) return same ? "七杀" : "正官";
    return same ? "偏财" : "正财";
  }

  function baziAdd(lines, total, name, delta) {
    if (!delta) return total;
    lines.push(name + " " + (delta > 0 ? "+" : "") + delta);
    return total + delta;
  }

  function stemWeight(god) { return HELP.has(god) ? 1 : -1; }

  function hiddenTotal(zhi, weights, dayGan) {
    var total = 0, detail = [];
    HIDE[zhi].forEach(function (gan, index) {
      var god = tenGod(dayGan, gan);
      var delta = weights[index] * stemWeight(god);
      total += delta;
      detail.push(gan + god);
    });
    return [total, detail];
  }

  function preference(band) {
    if (band === "身旺") return [DRAIN, HELP];
    if (band === "身弱") return [HELP, DRAIN];
    return [ZHENG, PIAN];
  }

  function dayun(eight, genderCode, year) {
    var yun = eight.getYun(genderCode, 1);
    var start = yun.getStartSolar();
    var startText = pad4(start.getYear()) + "-" + pad2(start.getMonth()) + "-" + pad2(start.getDay());
    var chosen = null;
    yun.getDaYun().forEach(function (item) {
      if (chosen == null && item.getStartYear() <= year && year <= item.getEndYear()) chosen = item;
    });
    return {
      forward: yun.isForward(),
      start_text: startText,
      ganzhi: chosen ? chosen.getGanZhi() : "",
      start_year: chosen ? chosen.getStartYear() : 0,
      end_year: chosen ? chosen.getEndYear() : 0
    };
  }

  function buildNatal(raw) {
    var birth = mkDate(parseInt(raw.birth_year, 10), parseInt(raw.birth_month, 10), parseInt(raw.birth_day, 10));
    var clock = parseClock(raw.birth_time);
    var hour = clock[0], minute = clock[1];
    var solar = solarOf(birth, hour, minute);
    var eight = solar.getLunar().getEightChar();
    eight.setSect(1);
    var dayGan = eight.getDayGan();
    var dayZhi = eight.getDayZhi();
    var yearZhi = eight.getYearZhi();
    var monthZhi = eight.getMonthZhi();
    var timeZhi = eight.getTimeZhi();
    var sc = clockToShichen(hour);
    var shiZhi = sc[0], late = sc[1];

    var strength = 0;
    var monthMain = HIDE[monthZhi][0];
    var monthGod = tenGod(dayGan, monthMain);
    strength += hiddenTotal(monthZhi, [10, 4, 2], dayGan)[0];
    [eight.getYearGan(), eight.getMonthGan(), eight.getTimeGan()].forEach(function (gan) {
      strength += 4 * stemWeight(tenGod(dayGan, gan));
    });
    strength += hiddenTotal(yearZhi, [4, 2, 1], dayGan)[0];
    strength += hiddenTotal(dayZhi, [8, 3, 1], dayGan)[0];
    strength += hiddenTotal(timeZhi, [4, 2, 1], dayGan)[0];

    var band;
    if (strength >= 8) band = "身旺";
    else if (strength <= -8) band = "身弱";
    else band = "中和";
    var pref = preference(band);
    var xi = pref[0], ji = pref[1];
    var command = HELP.has(monthGod) ? "得令" : "失令";

    var gender = raw.gender;
    var genderCode = gender === "男" ? 1 : 0;
    var luck = dayun(eight, genderCode, parseInt(raw.g_year, 10));
    var direction = luck.forward ? "顺行" : "逆行";
    var animal = ZHI_ANIMAL[yearZhi];
    var gods = [
      tenGod(dayGan, eight.getYearGan()),
      tenGod(dayGan, eight.getMonthGan()),
      tenGod(dayGan, eight.getTimeGan()),
      tenGod(dayGan, monthMain),
      tenGod(dayGan, HIDE[yearZhi][0]),
      tenGod(dayGan, HIDE[dayZhi][0]),
      tenGod(dayGan, HIDE[timeZhi][0])
    ];

    var lines = [
      gender + "命，公历 " + iso(birth) + " " + pad2(hour) + ":" + pad2(minute)
    ];
    if (late) lines.push("出生在晚子时，日柱按次日");
    else if (shiZhi === "子") lines.push("出生在早子时，日柱按当日");
    lines.push("八字 " + eight.getYear() + "  " + eight.getMonth() + "  " + eight.getDay() + "  " + eight.getTime());
    lines.push(
      "日主" + dayGan + ELEMENTS[STEMS.indexOf(dayGan)] + "，" + band +
      "（旺衰分 " + (strength >= 0 ? "+" : "") + strength + "，月令本气" + monthMain + "为" + monthGod + "，" + command + "）"
    );
    lines.push("喜用 " + GOD_ORDER.filter(function (n) { return xi.has(n); }).join("、"));
    lines.push("忌神 " + GOD_ORDER.filter(function (n) { return ji.has(n); }).join("、"));
    if (luck.ganzhi) {
      var luckGod = tenGod(dayGan, luck.ganzhi[0]);
      var side = xi.has(luckGod) ? "喜用" : "忌神";
      lines.push(
        "大运" + direction + "，" + luck.ganzhi + "（" + luck.start_year + "-" + luck.end_year + "），" +
        "运干" + luck.ganzhi[0] + luckGod + "，属" + side + "。起运 " + luck.start_text
      );
    } else {
      lines.push("大运未起，起运 " + luck.start_text);
    }
    lines.push("年支" + yearZhi + "（" + animal + "）。冲年支仍按这个生肖，另外单看冲日支");
    lines.push("取用是扶抑：身旺喜克泄耗，身弱喜印比，中和取正印、食神、正官、正财。通书大忌不会改成宜。");
    return {
      birth: birth,
      gender: gender,
      animal: animal,
      day_gan: dayGan,
      day_zhi: dayZhi,
      year_zhi: yearZhi,
      kong: Array.prototype.slice.call(eight.getDayXunKong()),
      xi: xi,
      ji: ji,
      band: band,
      has_shang: gods.indexOf("伤官") >= 0,
      lines: lines,
      brief: gender + "命" + dayGan + ELEMENTS[STEMS.indexOf(dayGan)] + band
    };
  }

  function godDelta(natal, god, weight) {
    if (natal.xi.has(god)) return weight;
    if (natal.ji.has(god)) return -weight;
    return 0;
  }

  function hourPoints(natal, chart, item) {
    var lines = [];
    var total = 0;
    var hourGod = tenGod(natal.day_gan, item.gan);
    var branchGod = tenGod(natal.day_gan, HIDE[item.zhi][0]);
    total = baziAdd(lines, total, item.zhi + "时干" + item.gan + hourGod, godDelta(natal, hourGod, 4));
    total = baziAdd(lines, total, item.zhi + "时支本气" + HIDE[item.zhi][0] + branchGod, godDelta(natal, branchGod, 3));
    if (CHONG[item.zhi] === natal.year_zhi) total = baziAdd(lines, total, "时支冲命主年支", -8);
    if (item.zhi === natal.year_zhi) total = baziAdd(lines, total, "时支临命主年支", 2);
    if (item.zhi === natal.day_zhi) total = baziAdd(lines, total, "时支临命主日支", 3);
    if (isXing(item.zhi, natal.day_zhi)) total = baziAdd(lines, total, "时支刑命主日支", -6);
    if (HAI[item.zhi] === natal.day_zhi) total = baziAdd(lines, total, "时支害命主日支", -5);
    if (natal.kong.indexOf(item.zhi) >= 0) total = baziAdd(lines, total, "时支落命主旬空", -4);
    if (natal.xi.size && natal.ji.size) {
      var strong = natal.xi.has(hourGod) && natal.xi.has(branchGod);
      var weak = natal.ji.has(hourGod) && natal.ji.has(branchGod);
      if (strong) total = baziAdd(lines, total, "时干支皆为喜用", 6);
      if (weak) total = baziAdd(lines, total, "时干支皆为忌神", -6);
    }
    var event = chart.event;
    if (event === "marry" && natal.gender === "男" && CAI.has(hourGod)) {
      var gain = natal.xi.has(hourGod) ? 6 : 2;
      total = baziAdd(lines, total, "男命时干妻星" + hourGod, gain);
    }
    if (event === "marry" && natal.gender === "女") {
      if (hourGod === "正官") {
        var gain2 = natal.xi.has(hourGod) ? 6 : 2;
        total = baziAdd(lines, total, "女命时干正官", gain2);
      } else if (hourGod === "七杀") {
        total = baziAdd(lines, total, "女命时干七杀", natal.xi.has(hourGod) ? 4 : -6);
      }
      if (natal.has_shang && hourGod === "正官") total = baziAdd(lines, total, "女命伤官见官", -8);
    }
    if (event === "open" && (CAI.has(hourGod) || SHI.has(hourGod)) && natal.xi.has(hourGod)) {
      total = baziAdd(lines, total, "开市时干" + hourGod, 3);
    }
    if (event === "travel" && item.zhi === YI_MA[natal.year_zhi]) total = baziAdd(lines, total, "时支为命主年马", 6);
    if (event === "earth" && (YIN.has(hourGod) || BI.has(hourGod)) && natal.xi.has(hourGod)) {
      total = baziAdd(lines, total, "动土时干" + hourGod, 3);
    }
    return [total, lines];
  }

  function preferredZhi(chart, natal) {
    var ranking = rankHours(chart);
    var scored = [];
    ranking.forEach(function (row) {
      var item = chart.hours.find(function (h) { return h.zhi === row.zhi; });
      var points = hourPoints(natal, chart, item)[0];
      scored.push([points, row]);
    });
    var clean = scored.filter(function (it) { return it[1].bad.length === 0; });
    var pool = clean.length ? clean : scored;
    pool.sort(function (a, b) {
      if (b[0] !== a[0]) return b[0] - a[0];
      if (b[1].total !== a[1].total) return b[1].total - a[1].total;
      return DI_ZHI.indexOf(a[1].zhi) - DI_ZHI.indexOf(b[1].zhi);
    });
    return pool[0][1].zhi;
  }

  function markHours(chart, natal) {
    var ranking = rankHours(chart);
    var scored = [];
    ranking.forEach(function (row) {
      var item = chart.hours.find(function (h) { return h.zhi === row.zhi; });
      var points = hourPoints(natal, chart, item)[0];
      scored.push([points, row]);
    });
    var clean = scored.filter(function (it) { return it[1].bad.length === 0; });
    var pool = clean.length ? clean : scored;
    var top = Math.max.apply(null, pool.map(function (it) { return it[0]; }));
    var best = pool.filter(function (it) { return it[0] === top; }).map(function (it) { return it[1]; });
    best.sort(function (a, b) { return DI_ZHI.indexOf(a.zhi) - DI_ZHI.indexOf(b.zhi); });
    chart.hour_ranking = ranking;
    chart.best_hours = best;
    chart.bad_hours = ranking.filter(function (row) { return row.bad.length > 0; })
      .sort(function (a, b) { return DI_ZHI.indexOf(a.zhi) - DI_ZHI.indexOf(b.zhi); });
    chart.has_clean_hour = ranking.some(function (row) { return row.bad.length === 0; });
  }

  function rerun(chart, natal, zhi, monthLabel, animal) {
    var raw = {
      g_year: String(chart.civil.getFullYear()),
      g_month: String(chart.civil.getMonth() + 1),
      g_day: String(chart.civil.getDate()),
      time: SHICHEN_CLOCK[zhi],
      zhushi_shengxiao: animal || natal.animal,
      event_type: chart.event,
      house_dir: chart.house_text,
      _auto_time: "yes"
    };
    var fresh = analyze(raw);
    if (monthLabel) fresh.month_scan = monthLabel;
    return fresh;
  }

  function dayPoints(chart, natal) {
    var lines = [];
    var total = 0;
    var hard = [];
    var dayGod = tenGod(natal.day_gan, chart.day_gan);
    var branchGod = tenGod(natal.day_gan, HIDE[chart.day_zhi][0]);
    var yearGod = tenGod(natal.day_gan, chart.year_gan);
    var monthGod = tenGod(natal.day_gan, chart.month_gan);
    total = baziAdd(lines, total, "流年" + chart.year_gan + yearGod, godDelta(natal, yearGod, 3));
    total = baziAdd(lines, total, "流月" + chart.month_gan + monthGod, godDelta(natal, monthGod, 3));
    total = baziAdd(lines, total, "日干" + chart.day_gan + dayGod, godDelta(natal, dayGod, 10));
    total = baziAdd(lines, total, "日支" + chart.day_zhi + branchGod, godDelta(natal, branchGod, 8));
    if (CHONG[chart.day_zhi] === natal.day_zhi) {
      total = baziAdd(lines, total, "日支冲命主日柱", -16);
      hard.push("日支" + chart.day_zhi + "冲命主日柱" + natal.day_zhi);
    }
    if (isXing(chart.day_zhi, natal.day_zhi)) total = baziAdd(lines, total, "日支刑命主日支", -8);
    if (HAI[chart.day_zhi] === natal.day_zhi) total = baziAdd(lines, total, "日支害命主日支", -6);
    if (LIU_HE[chart.day_zhi] === natal.day_zhi) total = baziAdd(lines, total, "日支六合命主日支", 6);
    if (SAN_HE[chart.day_zhi].indexOf(natal.day_zhi) >= 0 && natal.day_zhi !== chart.day_zhi) {
      total = baziAdd(lines, total, "日支三合命主日支", 4);
    }
    if (CHONG[chart.day_zhi] === natal.year_zhi) total = baziAdd(lines, total, "日支冲命主年支", -8);
    if (natal.kong.indexOf(chart.day_zhi) >= 0) total = baziAdd(lines, total, "日支落命主旬空", -6);

    var event = chart.event;
    if (event === "marry" && natal.gender === "男" && CAI.has(dayGod)) {
      var gain = natal.xi.has(dayGod) ? 6 : 2;
      total = baziAdd(lines, total, "男命日干妻星" + dayGod, gain);
    }
    if (event === "marry" && natal.gender === "女") {
      if (dayGod === "正官") {
        var gain2 = natal.xi.has(dayGod) ? 6 : 2;
        total = baziAdd(lines, total, "女命日干正官", gain2);
      } else if (dayGod === "七杀") {
        total = baziAdd(lines, total, "女命日干七杀", natal.xi.has(dayGod) ? 4 : -6);
      }
      if (natal.has_shang && dayGod === "正官") total = baziAdd(lines, total, "女命伤官见官", -8);
    }
    if (event === "open" && (CAI.has(dayGod) || SHI.has(dayGod)) && natal.xi.has(dayGod)) {
      total = baziAdd(lines, total, "开市日干" + dayGod, 4);
    }
    if (event === "travel" && chart.day_zhi === YI_MA[natal.year_zhi]) total = baziAdd(lines, total, "日支为命主年马", 6);
    if (event === "earth" && GUAN.has(dayGod) && natal.ji.has(dayGod)) total = baziAdd(lines, total, "身弱见官杀，不宜动土", -4);
    return [total, lines, hard];
  }

  function verdict(almanacConclusion, baziScore, baziHard) {
    if (almanacConclusion === "不宜" || baziHard.length > 0) return "不宜";
    if (almanacConclusion === "宜改时") return baziScore >= 0 ? "宜改时" : "平";
    if (baziScore >= 12 && almanacConclusion === "宜") return "宜";
    if (baziScore >= 12 || (baziScore >= 0 && almanacConclusion === "宜")) return "可备选";
    return "平";
  }

  function applyBazi(chart, natal) {
    var almanacScore = chart.score;
    var almanacConclusion = chart.conclusion;
    var chosen = chart.hours.find(function (hour) { return hour.zhi === chart.shi_zhi; });
    var dp = dayPoints(chart, natal);
    var dayTotal = dp[0], dayLines = dp[1], hard = dp[2];
    var hp = hourPoints(natal, chart, chosen);
    var hourTotal = hp[0], hourLines = hp[1];
    var total = dayTotal + hourTotal;
    var conclusion = verdict(almanacConclusion, total, hard);
    var lines = dayLines.concat(hourLines, ["命理分 " + total]);
    if (hard.length) lines.push("命理不宜：" + hard.join("；"));
    lines.push("结论：" + conclusion);
    chart.use_bazi = true;
    chart.natal_lines = natal.lines;
    chart.bazi_lines = lines;
    chart.bazi_score = total;
    chart.almanac_score = almanacScore;
    chart.almanac_conclusion = almanacConclusion;
    chart.score = total;
    chart.conclusion = conclusion;
    return chart;
  }

  function finish(chart, natal) {
    var label = chart.month_scan;
    if (chart.auto_time) {
      var zhi = preferredZhi(chart, natal);
      if (zhi !== chart.shi_zhi) chart = rerun(chart, natal, zhi, label);
      markHours(chart, natal);
    }
    return applyBazi(chart, natal);
  }

  function baziRank(chart) {
    var r = CONCLUSION_RANK[chart.conclusion];
    if (r == null) r = 9;
    return [r, -chart.bazi_score, -chart.almanac_score, ordinal(chart.civil)];
  }

  function combinedRows(chart, natal) {
    var ranking = rankHours(chart);
    var dayTotal = dayPoints(chart, natal)[0];
    var rows = [];
    ranking.forEach(function (row) {
      var item = chart.hours.find(function (h) { return h.zhi === row.zhi; });
      var points = hourPoints(natal, chart, item)[0];
      rows.push([row.total + dayTotal + points, row]);
    });
    return [ranking, rows];
  }

  function combinedZhi(chart, natal) {
    var rows = combinedRows(chart, natal)[1];
    var clean = rows.filter(function (it) { return it[1].bad.length === 0; });
    var pool = clean.length ? clean : rows;
    pool.sort(function (a, b) {
      if (b[0] !== a[0]) return b[0] - a[0];
      if (b[1].total !== a[1].total) return b[1].total - a[1].total;
      return DI_ZHI.indexOf(a[1].zhi) - DI_ZHI.indexOf(b[1].zhi);
    });
    return pool[0][1].zhi;
  }

  function markCombined(chart, natal) {
    var cr = combinedRows(chart, natal);
    var ranking = cr[0], rows = cr[1];
    var clean = rows.filter(function (it) { return it[1].bad.length === 0; });
    var pool = clean.length ? clean : rows;
    var top = Math.max.apply(null, pool.map(function (it) { return it[0]; }));
    var best = pool.filter(function (it) { return it[0] === top; }).map(function (it) { return it[1]; });
    best.sort(function (a, b) { return DI_ZHI.indexOf(a.zhi) - DI_ZHI.indexOf(b.zhi); });
    chart.hour_ranking = ranking;
    chart.best_hours = best;
    chart.bad_hours = ranking.filter(function (row) { return row.bad.length > 0; })
      .sort(function (a, b) { return DI_ZHI.indexOf(a.zhi) - DI_ZHI.indexOf(b.zhi); });
    chart.has_clean_hour = ranking.some(function (row) { return row.bad.length === 0; });
  }

  function attachBoth(chart, natal) {
    var label = chart.month_scan;
    if (chart.auto_time) {
      var zhi = combinedZhi(chart, natal);
      if (zhi !== chart.shi_zhi) chart = rerun(chart, natal, zhi, label, chart.animal);
      markCombined(chart, natal);
    }
    chart = applyBazi(chart, natal);
    chart.total_score = chart.almanac_score + chart.bazi_score;
    return chart;
  }

  function totalRank(chart) {
    var blocked = chart.conclusion === "不宜";
    return [blocked, -chart.total_score, ordinal(chart.civil)];
  }

  function adviceLines(chart) {
    if (!chart.auto_time) return [];
    var lines = [];
    if (chart.hard.length) lines.push("本日有日课禁忌，换时辰不能把这一天变成宜日。");
    else if (!chart.has_clean_hour) lines.push("当天没有无禁忌的时辰，下面是扣分最少的一档。");
    var title;
    if (chart.hard.length) title = "当日时辰里相对最好";
    else if (!chart.has_clean_hour) title = "相对最佳时间";
    else title = "最佳时间";
    if (chart.best_hours.length > 1) title += "（并列）";
    lines.push(title + "：");
    chart.best_hours.forEach(function (row) {
      var event = row.yi_event ? "宜" + chart.word : "未写明宜" + chart.word;
      lines.push(row.span + " " + row.zhi + "时 " + row.ganzhi + " " + row.shen + row.kind + " " + event);
    });
    var bestSet = chart.best_hours.map(function (row) { return row.zhi; });
    var badSet = chart.bad_hours.map(function (row) { return row.zhi; });
    var usable = chart.hour_ranking.filter(function (row) {
      return bestSet.indexOf(row.zhi) < 0 && badSet.indexOf(row.zhi) < 0;
    });
    usable.sort(function (a, b) { return DI_ZHI.indexOf(a.zhi) - DI_ZHI.indexOf(b.zhi); });
    if (usable.length) {
      var usableTitle = chart.hard.length ? "其余时辰没有单独的不佳项" : "其余可用，但不如最佳";
      var brief = usable.map(function (row) { return row.span + " " + row.zhi + "时" + row.shen; }).join("、");
      lines.push(usableTitle + "：" + brief);
    }
    if (chart.bad_hours.length) {
      lines.push("不佳时间：");
      chart.bad_hours.forEach(function (row) {
        lines.push(row.span + " " + row.zhi + "时 " + row.ganzhi + " " + row.shen + row.kind + "：" + row.bad.join("、"));
      });
    } else {
      lines.push("不佳时间：无");
    }
    return lines;
  }

  function hourLines(chart) {
    var lines = [];
    chart.hours.forEach(function (item) {
      var mark;
      if (chart.auto_time) {
        var bestZhi = chart.best_hours.map(function (row) { return row.zhi; });
        var badZhi = chart.bad_hours.map(function (row) { return row.zhi; });
        if (bestZhi.indexOf(item.zhi) >= 0) mark = "最佳";
        else if (badZhi.indexOf(item.zhi) >= 0) mark = "不佳";
        else mark = "";
      } else {
        mark = item.zhi === chart.shi_zhi ? "所填" : "";
      }
      var eventMark = "";
      if (item.yi.indexOf(chart.word) >= 0) eventMark = "宜" + chart.word;
      else if (item.ji.indexOf(chart.word) >= 0) eventMark = "忌" + chart.word;
      var bits = [item.span, item.ganzhi, item.shen + item.kind];
      if (eventMark) bits.push(eventMark);
      if (mark) bits.push(mark);
      lines.push(bits.join("  "));
    });
    if (!chart.auto_time) {
      if (chart.good_hours.length) {
        var brief = chart.good_hours.map(function (item) { return item.span + item.zhi + "时" + item.shen; }).join("、");
        if (chart.hard.length) lines.push("对照黄道时（日课已不宜，改时辰去不掉禁忌）：" + brief);
        else lines.push("可考虑的黄道时：" + brief);
      } else {
        lines.push("本日没有同时满足黄道、非五不遇、不忌" + chart.word + "的时辰");
      }
    }
    return lines;
  }

  function chartView(chart) {
    var cross = chart.late_zi ? "晚子时，日柱与日课按次日" : "不跨日";
    if (chart.shi_zhi === "子" && !chart.late_zi) cross = "早子时，日柱按当日";
    var picked = chart.auto_time ? "选用时辰" : "所填时辰";
    var shishen = chart.shishen;
    var yearGod = shishen[0], monthGod = shishen[1], timeGod = shishen[2];
    var hide = chart.hide;
    var yearHide = hide[0], monthHide = hide[1], dayHide = hide[2], timeHide = hide[3];
    var yuepoToday = chart.day_zhi === chart.yue_po ? "是" : "否";
    var suipoToday = chart.day_zhi === chart.sui_po ? "是" : "否";
    var relation = "冲" + yn(chart.chong_person) + "  " +
      "刑" + yn(chart.xing_person) + "  " +
      "害" + yn(chart.hai_person) + "  " +
      "六合" + yn(chart.he_person) + "  " +
      "三合" + yn(chart.sanhe_person);
    var shenLines = [
      "喜神 " + chart.xi_text + "  财神 " + chart.cai_text + "  福神 " + chart.fu_text,
      "天乙贵人 " + chart.gui_ren + "  驿马 " + chart.yi_ma + "  桃花 " + chart.xian_chi,
      "太岁" + chart.year_zhi + "在" + chart.tai_sui_dir + "，岁破" + chart.sui_po + "在" + ZHI_DIR[chart.sui_po],
      "三煞在" + chart.sha_dir + "（" + chart.sha_branches.join("、") + "）",
      "月破 " + chart.yue_po + "（本日" + yuepoToday + "）  岁破 " + chart.sui_po + "（本日" + suipoToday + "）",
      "红沙 " + chart.hongsha + "（本日" + yn(chart.is_hongsha) + "）",
      chart.term_eve ? (chart.term_eve[0] + "：次日交" + chart.term_eve[1]) : "四离四绝：不是",
      "与主事 " + relation
    ];
    if (chart.sit_dir) shenLines.push("坐山" + chart.sit_dir + "，朝向" + chart.face_dir);
    var scoreLines = [];
    chart.score_items.forEach(function (p) {
      var name = p[0], delta = p[1];
      var sign = delta > 0 ? "+" : "";
      scoreLines.push(name + " " + sign + delta);
    });
    scoreLines.push("总分 " + (chart.almanac_score != null ? chart.almanac_score : chart.score));
    if (chart.hard.length) scoreLines.push("不宜原因：" + chart.hard.join("；"));
    scoreLines = scoreLines.concat(chart.notes);

    var almanacConclusion = chart.almanac_conclusion != null ? chart.almanac_conclusion : chart.conclusion;
    scoreLines.push("结论：" + almanacConclusion + "（" + chart.event_cn + "）");
    var bestName = chart.shi_label;
    if (chart.auto_time && (chart.best_hours || []).length > 1) bestName += "等";
    var civil = chart.civil;
    var view = {
      date: iso(civil),
      date_label: (civil.getMonth() + 1) + "月" + civil.getDate() + "日",
      best: bestName,
      best_clock: pad2(chart.hour) + ":" + pad2(chart.minute),
      score: chart.score,
      conclusion: chart.conclusion,
      pillars: chart.year_gz + "  " + chart.month_gz + "  " + chart.day_gz + "  " + chart.time_gz,
      blocks: [
        {
          title: "择时",
          lines: [clockText(chart) + "  " + chart.shi_label + "（" + chart.chosen.span + "），" + cross].concat(adviceLines(chart))
        },
        {
          title: "四柱",
          lines: [
            "排盘日 " + iso(chart.pan_date) + "  农历 " + chart.lunar_text,
            chart.year_gz + "  " + chart.month_gz + "  " + chart.day_gz + "  " + chart.time_gz,
            "纳音 " + chart.nayin + "  旬空 " + pyList(chart.kong),
            "上一节 " + chart.prev_jie,
            "下一节 " + chart.next_jie,
            "主事 " + chart.animal + "（" + chart.person_zhi + "）  " + chart.event_cn + "  " + (chart.house_text || "房屋未填"),
            "十神（日主" + chart.day_gan + "）年" + chart.year_gan + yearGod + " 月" + chart.month_gan + monthGod + " 时" + chart.time_gan + timeGod,
            "藏干 年[" + yearHide + "] 月[" + monthHide + "] 日[" + dayHide + "] 时[" + timeHide + "]",
            "日主月令" + chart.month_zhi + (chart.de_ling ? "得令" : "不得令") + "，" + chart.dishi_day
          ]
        },
        {
          title: "日课",
          lines: [
            chart.day_shen + "（" + chart.day_kind + "）",
            "建除" + chart.zhixing + "：" + JIANCHU_INFO[chart.zhixing],
            "二十八宿 " + chart.xiu + chart.zheng + "（" + chart.xiu_luck + "）",
            picked + " " + chart.chosen.ganzhi + " " + chart.chosen.shen + "（" + chart.chosen.kind + "）",
            "宜：" + chart.day_yi.join("、"),
            "忌：" + chart.day_ji.join("、"),
            "吉神：" + (chart.ji_shen.length ? chart.ji_shen.join("、") : "无"),
            "凶煞：" + (chart.xiong.length ? chart.xiong.join("、") : "无"),
            "彭祖 " + chart.pengzu,
            "日冲 " + chart.day_chong + "  日煞 " + chart.day_sha
          ]
        },
        { title: "神煞", lines: shenLines },
        { title: "十二时辰", lines: hourLines(chart) },
        { title: chart.use_bazi ? "通书计分" : "计分", lines: scoreLines }
      ]
    };
    if (chart.use_bazi) {
      view.blocks.unshift({ title: "命主", lines: chart.natal_lines });
      view.blocks.splice(view.blocks.length - 1, 0, { title: "命理", lines: chart.bazi_lines });
      view.blocks.forEach(function (block) {
        if (block.title === "四柱") block.title = "日课四柱";
      });
    }
    var showAlmanac = !!chart.show_almanac;
    var showBazi = !!chart.show_bazi;
    almanacConclusion = chart.almanac_conclusion != null ? chart.almanac_conclusion : chart.conclusion;
    if (showAlmanac && showBazi) {
      view.conclusion = worse(almanacConclusion, chart.conclusion);
    }
    view.almanac_score = showAlmanac ? (chart.almanac_score != null ? chart.almanac_score : chart.score) : null;
    view.almanac_conclusion = showAlmanac ? almanacConclusion : null;
    view.bazi_score = showBazi ? (chart.bazi_score != null ? chart.bazi_score : null) : null;
    view.bazi_conclusion = showBazi ? chart.conclusion : null;
    return view;
  }

  function worse(left, right) {
    var rank = { "宜": 0, "宜改时": 1, "可备选": 2, "平": 3, "不宜": 4 };
    if ((rank[left] || 0) >= (rank[right] || 0)) return left;
    return right;
  }

  function flag(raw, key) {
    var value = raw[key];
    if (value == null) value = false;
    if (typeof value === "string") {
      return ["1", "true", "yes", "on"].indexOf(value.trim().toLowerCase()) >= 0;
    }
    return !!value;
  }

  function calendarDate(yearText, monthText, dayText, dayRequired, dayLabel) {
    if (!yearText || !monthText || (dayRequired && !dayText)) throw new Error("请填写" + dayLabel);
    var year = parseInt(yearText, 10);
    var month = parseInt(monthText, 10);
    var day = dayText ? parseInt(dayText, 10) : 0;
    if (isNaN(year) || isNaN(month) || (dayText && isNaN(day))) throw new Error("年和月、日要填数字");
    if (!(year >= 1900 && year <= 2100)) throw new Error("年份请填 1900 到 2100");
    if (!(month >= 1 && month <= 12)) throw new Error("月份要在 1 到 12");
    if (dayText) {
      var probe = mkDate(year, month, day);
      if (probe.getFullYear() !== year || probe.getMonth() + 1 !== month || probe.getDate() !== day) {
        throw new Error("这一天在公历里不存在");
      }
    }
    return [year, month, dayText ? String(day) : ""];
  }

  function normalizeQuery(raw, method) {
    if (method == null) method = "almanac";
    if (typeof raw !== "object" || raw == null) throw new Error("请求格式不对");
    var fields = ["g_year", "g_month", "g_day", "time", "zhushi_shengxiao", "event_type", "house_dir"];
    var out = {};
    fields.forEach(function (key) {
      out[key] = String(raw[key] == null ? "" : raw[key]).trim();
    });
    var cd = calendarDate(out.g_year, out.g_month, out.g_day, false, "公历年和公历月");
    var year = cd[0], month = cd[1], dayText = cd[2];
    out.g_year = String(year);
    out.g_month = String(month);
    out.g_day = dayText;
    if (out.time) {
      var clock;
      try { clock = parseClock(out.time); }
      catch (exc) { throw new Error("时间请写成 24 小时制，例如 11:30"); }
      out.time = pad2(clock[0]) + ":" + pad2(clock[1]);
    }
    if (!EVENT_WORD[out.event_type]) throw new Error("请选择事项");
    if (!out.house_dir) throw new Error("请填写房屋坐向，例如坐北朝南");
    if (method === "almanac") {
      if (!SHENGXIAO_TO_ZHI[out.zhushi_shengxiao]) throw new Error("请选择生肖");
      return out;
    }
    var birthFields = ["birth_year", "birth_month", "birth_day", "birth_time", "gender"];
    birthFields.forEach(function (key) {
      out[key] = String(raw[key] == null ? "" : raw[key]).trim();
    });
    var bcd = calendarDate(out.birth_year, out.birth_month, out.birth_day, true, "出生年月日");
    out.birth_year = String(bcd[0]);
    out.birth_month = String(bcd[1]);
    out.birth_day = bcd[2];
    if (!out.birth_time) throw new Error("请选择出生时间");
    var bclock;
    try { bclock = parseClock(out.birth_time); }
    catch (exc) { throw new Error("出生时间请写成 24 小时制，例如 10:30"); }
    out.birth_time = pad2(bclock[0]) + ":" + pad2(bclock[1]);
    if (out.gender !== "男" && out.gender !== "女") throw new Error("请选择性别");
    return out;
  }

  function sortByKey(arr, keyFn) {
    arr.sort(function (a, b) {
      var ka = keyFn(a), kb = keyFn(b);
      var n = Math.max(ka.length, kb.length);
      for (var i = 0; i < n; i++) {
        var va = ka[i], vb = kb[i];
        if (va === vb) continue;
        if (typeof va === "boolean") return (va ? 1 : 0) - (vb ? 1 : 0);
        return va - vb;
      }
      return 0;
    });
    return arr;
  }

  function buildQuery(raw) {
    if (typeof raw !== "object" || raw == null) throw new Error("请求格式不对");
    var useAlmanac = flag(raw, "use_almanac");
    var useBazi = flag(raw, "use_bazi");
    if (!useAlmanac && !useBazi) {
      if (("method" in raw) && !("use_almanac" in raw) && !("use_bazi" in raw)) {
        var method = String(raw.method == null ? "" : raw.method).trim();
        useAlmanac = method === "almanac";
        useBazi = method === "bazi";
      }
    }
    if (!useAlmanac && !useBazi) throw new Error("请勾选通书或八字");
    var cleaned = normalizeQuery(raw, useBazi ? "bazi" : "almanac");
    if (useAlmanac && !SHENGXIAO_TO_ZHI[cleaned.zhushi_shengxiao]) throw new Error("请选择生肖");
    var natal = null;
    if (useBazi) {
      natal = buildNatal(cleaned);
      if (!useAlmanac) cleaned.zhushi_shengxiao = natal.animal;
      if (cleaned.g_day) {
        var target = mkDate(parseInt(cleaned.g_year, 10), parseInt(cleaned.g_month, 10), parseInt(cleaned.g_day, 10));
        if (target.getTime() < natal.birth.getTime()) throw new Error("要排的日子早于出生");
      }
    }
    var charts, span;
    if (cleaned.g_day) {
      charts = [analyze(cleaned)];
      span = "day";
    } else {
      charts = scanMonth(cleaned);
      span = "month";
    }
    if (useBazi) {
      charts = charts.filter(function (chart) { return chart.civil.getTime() >= natal.birth.getTime(); });
      if (!charts.length) throw new Error("这个月都在出生之前");
      if (useAlmanac) {
        charts = charts.map(function (chart) { return attachBoth(chart, natal); });
        sortByKey(charts, totalRank);
      } else {
        charts = charts.map(function (chart) { return finish(chart, natal); });
        sortByKey(charts, baziRank);
      }
    } else {
      sortByKey(charts, chartRank);
    }
    charts.forEach(function (chart) {
      chart.show_almanac = useAlmanac;
      chart.show_bazi = useBazi;
    });
    var items = charts.map(chartView);
    var best = items[0];
    var rejected = items.filter(function (item) { return item.conclusion === "不宜"; }).length;
    var headline;
    if (useAlmanac && useBazi) {
      var total = best.almanac_score + best.bazi_score;
      var core = "通书 " + best.almanac_score + " 分，八字 " + best.bazi_score + " 分，合计 " + total + " 分";
      if (span === "month") {
        headline = charts[0].month_scan + "共 " + items.length + " 天，不宜 " + rejected + " 天。总分最佳 " + best.date_label + " " + best.best + " " + best.best_clock + "，" + core;
      } else {
        headline = best.date_label + " " + best.best + " " + best.best_clock + "，" + best.conclusion + "。" + core;
      }
    } else if (useBazi) {
      if (span === "month") {
        headline = natal.brief + "。" + charts[0].month_scan + "共 " + items.length + " 天，不宜 " + rejected + " 天。命理最佳 " + best.date_label + " " + best.best + " " + best.best_clock + "，" + best.bazi_score + "分";
      } else {
        headline = natal.brief + "。" + best.date_label + " " + best.best + " " + best.best_clock + "，" + best.bazi_conclusion + " " + best.bazi_score + "分";
      }
    } else if (span === "month") {
      headline = charts[0].month_scan + "共 " + items.length + " 天，不宜 " + rejected + " 天。最佳 " + best.date_label + " " + best.best + " " + best.best_clock + "，" + best.almanac_score + "分";
    } else {
      headline = best.date_label + " " + best.best + " " + best.best_clock + "，" + best.almanac_conclusion + " " + best.almanac_score + "分";
    }
    return {
      use_almanac: useAlmanac,
      use_bazi: useBazi,
      mode: span,
      headline: headline,
      items: items
    };
  }

  global.Fate = {
    buildQuery: buildQuery,
    analyze: analyze,
    scanMonth: scanMonth
  };

})(window);
















