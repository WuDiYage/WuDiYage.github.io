const year = document.getElementById("g_year");
const month = document.getElementById("g_month");
const day = document.getElementById("g_day");
const time = document.getElementById("time");
const animal = document.getElementById("zhushi_shengxiao");
const eventType = document.getElementById("event_type");
const house = document.getElementById("house_dir");
const birthYear = document.getElementById("birth_year");
const birthMonth = document.getElementById("birth_month");
const birthDay = document.getElementById("birth_day");
const birthTime = document.getElementById("birth_time");
const gender = document.getElementById("gender");
const useAlmanac = document.getElementById("use-almanac");
const useBazi = document.getElementById("use-bazi");
const calc = document.getElementById("calc");
const formError = document.getElementById("form-error");
const result = document.getElementById("result");
const headline = document.getElementById("headline");
const list = document.getElementById("list");
const cols = document.getElementById("cols");
const openAll = document.getElementById("open-all");
const closeAll = document.getElementById("close-all");

const birthPlaceholder = document.createElement("option");
birthPlaceholder.value = "";
birthPlaceholder.textContent = "请选择";
birthTime.appendChild(birthPlaceholder);
for (const option of time.options) {
  if (!option.value) continue;
  birthTime.appendChild(new Option(option.textContent, option.value));
}

function showError(message) {
  formError.hidden = !message;
  formError.textContent = message || "";
}

function setAll(open) {
  list.querySelectorAll("details.slip").forEach((item) => {
    item.open = open;
  });
}

openAll.addEventListener("click", () => setAll(true));
closeAll.addEventListener("click", () => setAll(false));

function scoreCell(value, conclusion) {
  const span = document.createElement("span");
  span.className = "score";
  span.dataset.conclusion = conclusion;
  span.append(String(value));
  const small = document.createElement("small");
  small.textContent = conclusion;
  span.append(small);
  return span;
}

function render(payload) {
  const both = payload.use_almanac && payload.use_bazi;
  result.classList.toggle("scores-2", both);
  cols.replaceChildren();
  ["日期", "最佳"].forEach((label) => {
    const span = document.createElement("span");
    span.textContent = label;
    cols.appendChild(span);
  });
  if (payload.use_almanac) {
    const span = document.createElement("span");
    span.className = "score-head";
    span.textContent = "通书";
    cols.appendChild(span);
  }
  if (payload.use_bazi) {
    const span = document.createElement("span");
    span.className = "score-head";
    span.textContent = "八字";
    cols.appendChild(span);
  }
  headline.textContent = payload.headline;
  list.replaceChildren();
  payload.items.forEach((item) => {
    const slip = document.createElement("details");
    slip.className = "slip";
    slip.dataset.conclusion = item.conclusion;
    const summary = document.createElement("summary");
    const date = document.createElement("span");
    date.className = "date";
    date.textContent = item.date_label;
    const best = document.createElement("span");
    best.className = "best";
    best.textContent = `${item.best} ${item.best_clock}`;
    summary.append(date, best);
    if (payload.use_almanac) {
      summary.append(scoreCell(item.almanac_score, item.almanac_conclusion));
    }
    if (payload.use_bazi) {
      summary.append(scoreCell(item.bazi_score, item.bazi_conclusion));
    }
    const body = document.createElement("div");
    body.className = "body";
    item.blocks.forEach((block) => {
      const section = document.createElement("section");
      section.className = "block";
      const title = document.createElement("h2");
      title.textContent = block.title;
      section.appendChild(title);
      block.lines.forEach((line) => {
        const paragraph = document.createElement("p");
        paragraph.textContent = line;
        section.appendChild(paragraph);
      });
      body.appendChild(section);
    });
    slip.append(summary, body);
    list.appendChild(slip);
  });
  result.hidden = false;
  result.scrollIntoView({ behavior: "smooth", block: "start" });
}

calc.addEventListener("click", () => {
  showError("");
  calc.disabled = true;
  const previous = calc.textContent;
  calc.textContent = "排盘中";
  setTimeout(() => {
    try {
      const payload = window.Fate.buildQuery({
        use_almanac: useAlmanac.checked,
        use_bazi: useBazi.checked,
        g_year: year.value.trim(),
        g_month: month.value.trim(),
        g_day: day.value.trim(),
        time: time.value.trim(),
        zhushi_shengxiao: animal.value,
        event_type: eventType.value,
        house_dir: house.value.trim(),
        birth_year: birthYear.value.trim(),
        birth_month: birthMonth.value.trim(),
        birth_day: birthDay.value.trim(),
        birth_time: birthTime.value.trim(),
        gender: gender.value,
      });
      render(payload);
    } catch (error) {
      showError((error && error.message) ? error.message : "排盘失败");
    } finally {
      calc.disabled = false;
      calc.textContent = previous;
    }
  }, 30);
});
