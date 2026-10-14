(() => {
  "use strict";

  const input = document.getElementById("player-input");
  const list = document.getElementById("player-options");
  const note = document.getElementById("search-note");
  const result = document.getElementById("result");
  const svgNS = "http://www.w3.org/2000/svg";
  const reduceMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;

  let data = null;
  let players = [];
  const byId = new Map();
  let options = [];
  let active = -1;

  // ---------- formatting ----------

  const norm = (s) => s.normalize("NFD").replace(/[̀-ͯ]/g, "").toLowerCase().trim();
  const esc = (s) => String(s).replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
  const millions = (v) => (v / 1e6).toFixed(1);
  const euros = (v) => `€${millions(v)}m`;
  const seasonLabel = (s) => `${s}/${String(s + 1).slice(-2)}`;
  const shortSeason = (s) => `${String(s).slice(-2)}/${String(s + 1).slice(-2)}`;
  const count = (n) => n.toLocaleString("en-GB");

  // ---------- data ----------

  fetch("data/players.json")
    .then((response) => {
      if (!response.ok) throw new Error(`HTTP ${response.status}`);
      return response.json();
    })
    .then(init)
    .catch((err) => {
      result.innerHTML = `<p class="status error">Couldn't load the player data (${esc(err.message)}).
        If you opened this file straight from your computer, serve the folder instead:
        <code>python3 -m http.server --directory docs</code></p>`;
    });

  function init(json) {
    data = json;
    const f = Object.fromEntries(json.season_fields.map((name, i) => [name, i]));
    players = json.players.map((p) => {
      const seasons = p.seasons.map((row) => ({
        season: row[f.season], age: row[f.age], games: row[f.games], minutes: row[f.minutes],
        goals: row[f.goals], assists: row[f.assists], market: row[f.market_value],
        model: row[f.predicted], unseen: row[f.is_test],
      }));
      const key = norm(p.name);
      return { ...p, seasons, key, words: key.split(/[\s-]+/), latest: seasons[seasons.length - 1] };
    });
    players.forEach((p) => byId.set(p.id, p));

    fillMetrics(json.metrics);
    renderEffects(json.effects);
    renderScatter();

    input.disabled = false;
    input.placeholder = "Try Saka, Haaland or Rice";
    route(false);
  }

  function fillMetrics(m) {
    const values = {
      player_seasons: count(m.player_seasons),
      test_seasons: count(m.test_seasons),
      median_error: euros(m.median_error),
      mean_error: euros(m.mean_error),
    };
    document.querySelectorAll("[data-metric]").forEach((el) => {
      const value = values[el.dataset.metric];
      if (value) el.textContent = value;
    });
  }

  // ---------- search ----------

  // Lower score = better match: exact name, a whole word, the start of a word, anywhere in the name
  function matchScore(p, q) {
    if (p.key === q) return 0;
    if (p.words.includes(q)) return 1;
    if (p.words.some((w) => w.startsWith(q))) return 2;
    if (p.key.includes(q)) return 3;
    return null;
  }

  function search(query) {
    const q = norm(query);
    if (!q) return [];
    return players
      .map((p) => ({ p, score: matchScore(p, q) }))
      .filter((m) => m.score !== null)
      .sort((a, b) => a.score - b.score || b.p.latest.season - a.p.latest.season || a.p.name.localeCompare(b.p.name))
      .slice(0, 8)
      .map((m) => m.p);
  }

  // Edits needed to turn a into b; swapping two neighbouring letters ("Halaand") counts as one
  function editDistance(a, b) {
    const d = Array.from({ length: a.length + 1 }, (_, i) => [i, ...Array(b.length).fill(0)]);
    for (let j = 1; j <= b.length; j++) d[0][j] = j;
    for (let i = 1; i <= a.length; i++) {
      for (let j = 1; j <= b.length; j++) {
        const cost = a[i - 1] === b[j - 1] ? 0 : 1;
        d[i][j] = Math.min(d[i - 1][j] + 1, d[i][j - 1] + 1, d[i - 1][j - 1] + cost);
        if (i > 1 && j > 1 && a[i - 1] === b[j - 2] && a[i - 2] === b[j - 1]) {
          d[i][j] = Math.min(d[i][j], d[i - 2][j - 2] + 1);
        }
      }
    }
    return d[a.length][b.length];
  }

  // For typos like "Bukayo Sakaa" or "Halaand": the closest full name or surname
  function closestPlayer(query) {
    const q = norm(query);
    let best = null;
    let bestDistance = Infinity;
    for (const p of players) {
      const candidates = [p.key, p.words[p.words.length - 1]];
      for (const c of candidates) {
        const d = editDistance(q, c);
        if (d < bestDistance) { best = p; bestDistance = d; }
      }
    }
    return bestDistance <= Math.max(1, Math.floor(q.length / 3)) ? best : null;
  }

  function spanLabel(p) {
    const first = p.seasons[0].season;
    const last = p.latest.season;
    return first === last ? shortSeason(first) : `${shortSeason(first)} – ${shortSeason(last)}`;
  }

  function showOptions(query) {
    options = search(query);
    active = options.length ? 0 : -1;
    note.textContent = "";

    if (!norm(query)) {
      closeOptions();
      return;
    }
    if (!options.length) {
      closeOptions();
      const guess = closestPlayer(query);
      if (guess) {
        note.innerHTML = `No exact match. Did you mean <button type="button" data-id="${guess.id}">${esc(guess.name)}</button>?`;
      } else {
        note.textContent = `No Premier League outfield player with 900+ minutes in a season matches “${query.trim()}”.`;
      }
      return;
    }

    list.innerHTML = options.map((p, i) => `
      <li class="option" role="option" id="opt-${i}" data-index="${i}" aria-selected="${i === active}">
        <span class="option-name">${esc(p.name)}</span>
        <span class="option-meta">${esc(p.position)} · ${spanLabel(p)}</span>
      </li>`).join("");
    list.hidden = false;
    input.setAttribute("aria-expanded", "true");
    input.setAttribute("aria-activedescendant", "opt-0");
  }

  function closeOptions() {
    list.hidden = true;
    list.innerHTML = "";
    input.setAttribute("aria-expanded", "false");
    input.removeAttribute("aria-activedescendant");
  }

  function setActive(i) {
    if (!options.length) return;
    active = (i + options.length) % options.length;
    list.querySelectorAll(".option").forEach((el, j) => el.setAttribute("aria-selected", String(j === active)));
    const el = document.getElementById(`opt-${active}`);
    input.setAttribute("aria-activedescendant", el.id);
    el.scrollIntoView({ block: "nearest" });
  }

  function choose(p) {
    closeOptions();
    note.textContent = "";
    input.value = p.name;
    if (location.hash === `#p=${p.id}`) route(true);
    else location.hash = `p=${p.id}`;
  }

  input.addEventListener("input", () => showOptions(input.value));
  input.addEventListener("focus", () => { if (input.value) showOptions(input.value); });
  input.addEventListener("keydown", (e) => {
    if (e.key === "ArrowDown") { e.preventDefault(); if (list.hidden) showOptions(input.value); else setActive(active + 1); }
    else if (e.key === "ArrowUp") { e.preventDefault(); setActive(active - 1); }
    else if (e.key === "Enter") {
      e.preventDefault();
      if (options[active]) choose(options[active]);
      else {
        const guess = note.querySelector("button");
        if (guess) choose(byId.get(Number(guess.dataset.id)));
      }
    } else if (e.key === "Escape") {
      if (!list.hidden) closeOptions();
      else { input.value = ""; note.textContent = ""; }
    }
  });
  input.addEventListener("blur", () => setTimeout(closeOptions, 120));

  // mousedown, not click, so the choice lands before the input loses focus
  list.addEventListener("mousedown", (e) => {
    const el = e.target.closest(".option");
    if (!el) return;
    e.preventDefault();
    choose(options[Number(el.dataset.index)]);
  });
  note.addEventListener("click", (e) => {
    const button = e.target.closest("button[data-id]");
    if (button) choose(byId.get(Number(button.dataset.id)));
  });

  // ---------- routing: #p=<player id> ----------

  function route(scroll) {
    const match = location.hash.match(/^#p=(\d+)$/);
    if (match && byId.has(Number(match[1]))) {
      const p = byId.get(Number(match[1]));
      input.value = p.name;
      note.textContent = "";
      renderPlayer(p);
      if (scroll) result.scrollIntoView({ behavior: reduceMotion ? "auto" : "smooth" });
    } else if (!location.hash || location.hash === "#" || location.hash === "#search" || match) {
      renderDisagreements();
    }
    // Section links (#findings, #method…) leave the current result alone
  }

  window.addEventListener("hashchange", () => { if (data) route(true); });

  // ---------- empty state: biggest disagreements this season ----------

  function renderDisagreements() {
    const season = data.metrics.last_season;
    const current = players.filter((p) => p.latest.season === season);
    const gap = (p) => p.latest.model - p.latest.market;
    const under = [...current].sort((a, b) => gap(a) - gap(b)).slice(0, 6);
    const over = [...current].sort((a, b) => gap(b) - gap(a)).slice(0, 6);
    const item = (p) => `
      <li><a href="#p=${p.id}">
        <span class="d-name">${esc(p.name)}</span>
        <span class="d-figs">${euros(p.latest.market)} · <span class="m">${euros(p.latest.model)}</span></span>
      </a></li>`;

    result.innerHTML = `
      <div class="result-enter">
        <h2>Biggest disagreements, ${seasonLabel(season)}</h2>
        <p class="disagree-intro">Where the market and the model are furthest apart this season.
          Transfermarkt's value first, the <span style="color:var(--model)">model's</span> second.
          Pick a player, or search above.</p>
        <div class="disagree">
          <div><h3>Market rates higher</h3><ol>${under.map(item).join("")}</ol></div>
          <div><h3>Model rates higher</h3><ol>${over.map(item).join("")}</ol></div>
        </div>
      </div>`;
  }

  // ---------- a player ----------

  function renderPlayer(p) {
    const s = p.latest;
    const gap = s.model - s.market;
    const share = Math.abs(gap) / s.market;
    let verdict;
    if (share < 0.1) {
      verdict = `The model agrees with the market to within 10%.`;
    } else if (gap < 0) {
      verdict = `The model prices him <strong class="under">${euros(-gap)} below</strong> the market.`;
    } else {
      verdict = `The model prices him <strong class="over">${euros(gap)} above</strong> the market.`;
    }
    const unseen = p.seasons.some((x) => x.unseen);

    result.innerHTML = `
      <article class="result-enter" aria-labelledby="player-name">
        <div class="player-head">
          <h2 class="player-name" id="player-name">${esc(p.name)}</h2>
          <span class="player-meta">${esc(p.position)} · ${p.seasons.length} PL season${p.seasons.length > 1 ? "s" : ""} in the data</span>
        </div>

        <div class="scoreline" aria-label="${seasonLabel(s.season)}: Transfermarkt ${euros(s.market)}, model ${euros(s.model)}">
          <div class="side">
            <span class="side-label">Transfermarkt</span>
            <span class="figure">€${millions(s.market)}<span class="unit">m</span></span>
          </div>
          <span class="dash" aria-hidden="true">–</span>
          <div class="side model">
            <span class="side-label">Model</span>
            <span class="figure">€${millions(s.model)}<span class="unit">m</span></span>
          </div>
        </div>
        <p class="verdict">${seasonLabel(s.season)}: ${verdict}
          Age ${s.age}, ${s.games} games, ${count(s.minutes)} minutes, ${s.goals} goals, ${s.assists} assists.</p>

        <div class="chart-block">
          <div class="chart-head">
            <span class="chart-title">Value by season</span>
            <span class="legend"><span class="key">Transfermarkt</span><span class="key model">Model</span></span>
          </div>
          ${p.seasons.length > 1 ? playerChart(p) : `<p class="ledger-note">Only one season in the data, so there's no line to draw.</p>`}
        </div>

        <div class="table-scroll">
          <table class="ledger">
            <thead><tr><th scope="col">Season</th><th scope="col">Age</th><th scope="col">Games</th><th scope="col">Goals</th>
              <th scope="col">Assists</th><th scope="col">Transfermarkt</th><th scope="col">Model</th><th scope="col">Gap</th></tr></thead>
            <tbody>${p.seasons.map((x) => {
              const g = x.model - x.market;
              return `<tr>
                <td>${seasonLabel(x.season)}${x.unseen ? '<span class="unseen">unseen</span>' : ""}</td>
                <td>${x.age}</td><td>${x.games}</td><td>${x.goals}</td><td>${x.assists}</td>
                <td>${euros(x.market)}</td><td class="pred">${euros(x.model)}</td>
                <td class="${g < 0 ? "gap-under" : "gap-over"}">${g < 0 ? "−" : "+"}${euros(Math.abs(g))}</td>
              </tr>`;
            }).join("")}</tbody>
          </table>
        </div>
        <p class="ledger-note">${unseen
          ? "Seasons marked unseen were held back from training, so those predictions are a genuine test."
          : "All of this player's seasons were used in training."}
          <a href="#search" id="back-to-list">Back to the biggest disagreements</a></p>
      </article>`;

    document.getElementById("back-to-list").addEventListener("click", (e) => {
      e.preventDefault();
      history.pushState("", "", location.pathname + location.search);
      input.value = "";
      renderDisagreements();
      input.focus();
    });
  }

  function niceStep(max) {
    const steps = [5, 10, 20, 25, 50, 100, 200, 250, 500];
    return steps.find((s) => max / s <= 5) || 1000;
  }

  function playerChart(p) {
    // A narrower canvas on phones keeps the axis text a readable size once the SVG is scaled down
    const W = window.innerWidth < 600 ? 400 : 760, H = 280, L = 56, R = 28, T = 16, B = 36;
    const values = p.seasons.flatMap((x) => [x.market, x.model]).map((v) => v / 1e6);
    const step = niceStep(Math.max(...values));
    const top = Math.ceil(Math.max(...values) / step) * step;
    const n = p.seasons.length;
    const x = (i) => L + (i * (W - L - R)) / (n - 1);
    const y = (v) => T + (H - T - B) * (1 - v / 1e6 / top);
    const path = (key) => p.seasons.map((s, i) => `${i ? "L" : "M"}${x(i).toFixed(1)},${y(s[key]).toFixed(1)}`).join("");

    let grid = "";
    for (let v = 0; v <= top; v += step) {
      const yy = T + (H - T - B) * (1 - v / top);
      grid += `<line x1="${L}" x2="${W - R}" y1="${yy}" y2="${yy}"/><text x="${L - 8}" y="${yy + 4}" text-anchor="end">€${v}m</text>`;
    }
    const labels = p.seasons.map((s, i) => `<text x="${x(i)}" y="${H - 10}" text-anchor="middle">${shortSeason(s.season)}</text>`).join("");
    const dots = p.seasons.map((s, i) => `
      <circle class="dot-market" cx="${x(i)}" cy="${y(s.market)}" r="4"><title>${seasonLabel(s.season)} Transfermarkt ${euros(s.market)}</title></circle>
      <circle class="dot-model" cx="${x(i)}" cy="${y(s.model)}" r="4.5"><title>${seasonLabel(s.season)} model ${euros(s.model)}</title></circle>`).join("");

    return `<svg viewBox="0 0 ${W} ${H}" role="img" aria-label="Transfermarkt value and model prediction for each season, shown in the table below">
      <g class="grid">${grid}</g>${labels}
      <path class="line-market" d="${path("market")}"/>
      <path class="line-model" d="${path("model")}"/>${dots}</svg>`;
  }

  // ---------- findings: feature effects ----------

  function renderEffects(effects) {
    const labels = {
      position_Midfield: "Midfielder (vs forward)", position_Defender: "Defender (vs forward)",
      season: "One season later", assists: "+1 assist", goals: "+1 goal",
      minutes: "+90 minutes", height_in_cm: "+1 cm taller", games: "+1 game, same minutes",
      age: "One year older",
    };
    const rows = Object.entries(effects).sort((a, b) => b[1] - a[1]);
    const lo = Math.min(0, ...rows.map((r) => r[1])) - 6;
    const hi = Math.max(...rows.map((r) => r[1])) + 8;
    const pos = (v) => ((v - lo) / (hi - lo)) * 100;

    document.getElementById("effects").innerHTML = rows.map(([name, v]) => {
      const left = pos(Math.min(0, v));
      const width = Math.abs(pos(v) - pos(0));
      const label = v >= 0 ? `left:calc(${pos(v)}% + 6px)` : `right:calc(${100 - pos(v)}% + 6px)`;
      return `<span class="eff-label">${labels[name] || name}</span>
        <span class="eff-track">
          <span class="eff-axis" style="left:${pos(0)}%"></span>
          <span class="eff-bar${v < 0 ? " neg" : ""}" style="left:${left}%;width:${width}%"></span>
          <span class="eff-value" style="${label}">${v > 0 ? "+" : v < 0 ? "−" : ""}${Math.abs(v).toFixed(1)}%</span>
        </span>`;
    }).join("");
  }

  // ---------- accuracy: unseen seasons, predicted vs actual ----------

  function renderScatter() {
    const W = 560, H = 560, L = 64, R = 16, T = 16, B = 56;
    const lo = Math.log10(3e5), hi = Math.log10(3e8);
    const clamp = (v) => Math.min(Math.max(Math.log10(v), lo), hi);
    const x = (v) => L + ((clamp(v) - lo) / (hi - lo)) * (W - L - R);
    const y = (v) => T + (1 - (clamp(v) - lo) / (hi - lo)) * (H - T - B);

    const svg = document.createElementNS(svgNS, "svg");
    svg.setAttribute("viewBox", `0 0 ${W} ${H}`);
    svg.setAttribute("role", "img");
    svg.setAttribute("aria-label", "Scatter of predicted against actual value for unseen player-seasons. Cheap players sit above the diagonal, expensive players below it.");

    let html = "";
    for (const v of [1e6, 1e7, 1e8]) {
      html += `<g class="grid"><line x1="${x(v)}" x2="${x(v)}" y1="${T}" y2="${H - B}"/><line x1="${L}" x2="${W - R}" y1="${y(v)}" y2="${y(v)}"/></g>
        <text x="${x(v)}" y="${H - B + 20}" text-anchor="middle">€${v / 1e6}m</text>
        <text x="${L - 8}" y="${y(v) + 4}" text-anchor="end">€${v / 1e6}m</text>`;
    }
    html += `<line class="diag" x1="${x(3e5)}" y1="${y(3e5)}" x2="${x(3e8)}" y2="${y(3e8)}"/>
      <text class="zone" x="${L + 12}" y="${T + 22}">Model over-values</text>
      <text class="zone" x="${W - R - 12}" y="${H - B - 12}" text-anchor="end">Model under-values</text>
      <text x="${(L + W - R) / 2}" y="${H - 12}" text-anchor="middle">Transfermarkt value</text>
      <text x="16" y="${(T + H - B) / 2}" text-anchor="middle" transform="rotate(-90 16 ${(T + H - B) / 2})">Model's prediction</text>`;

    // Dots link to the player; tabindex -1 so 847 dots don't swamp keyboard navigation (search covers it)
    for (const p of players) {
      for (const s of p.seasons) {
        if (!s.unseen) continue;
        html += `<a class="pt-link" href="#p=${p.id}" tabindex="-1"><circle class="pt" cx="${x(s.market).toFixed(1)}" cy="${y(s.model).toFixed(1)}" r="3.2">
          <title>${esc(p.name)}, ${seasonLabel(s.season)}: Transfermarkt ${euros(s.market)}, model ${euros(s.model)}</title></circle></a>`;
      }
    }
    svg.innerHTML = html;
    document.getElementById("scatter").appendChild(svg);
  }
})();
