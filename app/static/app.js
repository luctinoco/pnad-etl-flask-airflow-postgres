let graficosStats = null;

document.addEventListener("DOMContentLoaded", () => {
  setupTabs();
  loadData();
});

function setupTabs() {
  document.getElementById("tab-freq").addEventListener("click", () => showTab("freq"));
  document.getElementById("tab-rede").addEventListener("click", () => showTab("rede"));
  document.getElementById("tab-stats").addEventListener("click", () => showTab("stats"));
  showTab("freq");
}

function showTab(tab) {
  document.getElementById("freqEscolaDiv").style.display = (tab === "freq" ? "" : "none");
  document.getElementById("redeEnsinoDiv").style.display = (tab === "rede" ? "" : "none");
  document.getElementById("statsDiv").style.display = (tab === "stats" ? "" : "none");
  document.getElementById("tab-freq").classList.toggle("active", tab === "freq");
  document.getElementById("tab-rede").classList.toggle("active", tab === "rede");
  document.getElementById("tab-stats").classList.toggle("active", tab === "stats");
  if(tab === "stats") renderStats();
}

async function loadData() {
  try {
    const res = await fetch(`/api/analise-descritiva`);
    if (!res.ok) throw new Error(`API retornou status ${res.status}`);
    const data = await res.json();

    if (!data.frequencia_escolar_uf?.length || !data.rede_ensino?.length) {
      throw new Error("Dados ausentes da API.");
    }
    graficosStats = data.graficos_stats || null;

    drawStackedBarChart(
      "freqEscolaChart",
      data.frequencia_escolar_uf,
      "uf",
      "frequenta",
      "percentual",
      "Frequência Escolar por UF (Sim / Não)"
    );

    drawPieChart(
      "redeEnsinoChart",
      data.rede_ensino,
      "rede",
      "percentual",
      "Rede de Ensino"
    );

  } catch (err) {
    console.error("❌ Erro ao carregar dados:", err);
    alert("Erro ao carregar dados. Veja o console.");
  }
}

function drawStackedBarChart(canvasId, rows, xKey, stackKey, valueKey, title) {
  const ctx = document.getElementById(canvasId)?.getContext("2d");
  if (!ctx) return;

  if (window[canvasId] && typeof window[canvasId].destroy === "function") {
    window[canvasId].destroy();
  }

  // Agrupar por UF e status de frequência
  const grouped = {};
  rows.forEach((row) => {
    const x = row[xKey];
    const group = row[stackKey];
    if (!grouped[group]) grouped[group] = {};
    grouped[group][x] = (row[valueKey] * 100).toFixed(1);
  });

  const ufs = [...new Set(rows.map((r) => r[xKey]))].sort();
  const stacks = Object.keys(grouped);
  const colors = ["#4CAF50", "#F44336", "#FFC107"]; // Sim, Não, Ignorado

  const datasets = stacks.map((stackName, i) => ({
    label: stackName,
    data: ufs.map((uf) => grouped[stackName]?.[uf] || 0),
    backgroundColor: colors[i % colors.length],
    maxBarThickness: 42
  }));

  window[canvasId] = new Chart(ctx, {
    type: "bar",
    data: {
      labels: ufs,
      datasets,
    },
    options: {
      responsive: true,
      maintainAspectRatio: false, // IMPORTANTE: ocupa toda a área definida pela CSS
      plugins: {
        title: { display: true, text: title },
        tooltip: {
          callbacks: {
            label: (ctx) => `${ctx.dataset.label}: ${ctx.raw}%`,
          },
        },
        legend: { position: "bottom" },
      },
      scales: {
        x: { stacked: true },
        y: {
          stacked: true,
          beginAtZero: true,
          ticks: { callback: (v) => v + "%" },
        },
      },
    },
  });
}

function drawPieChart(canvasId, rows, labelKey, valueKey, title) {
  const ctx = document.getElementById(canvasId)?.getContext("2d");
  if (!ctx) return;

  if (window[canvasId] && typeof window[canvasId].destroy === "function") {
    window[canvasId].destroy();
  }

  const labels = rows.map((r) => r[labelKey]);
  const values = rows.map((r) => (r[valueKey] * 100).toFixed(1));
  const colors = ["#2196F3", "#FF9800", "#9C27B0"];

  window[canvasId] = new Chart(ctx, {
    type: "pie",
    data: {
      labels,
      datasets: [{ data: values, backgroundColor: colors }],
    },
    options: {
      responsive: true,
      maintainAspectRatio: false, // IMPORTANTE: ocupa toda a área definida pela CSS
      plugins: {
        title: { display: true, text: title },
        legend: { position: "bottom" },
        tooltip: {
          callbacks: {
            label: (ctx) => `${labels[ctx.dataIndex]}: ${values[ctx.dataIndex]}%`,
          },
        },
      },
    },
  });
}

function renderStats() {
  const div = document.getElementById("statsDiv");
  if (!graficosStats) {
    div.innerHTML = "<b>Sem dados estatísticos disponíveis.</b>";
    return;
  }
  const freq = graficosStats.frequencia_escolar || {};
  const rede = graficosStats.rede_ensino || {};

  div.innerHTML = `
    <table>
      <caption>Resumo Estatístico — Frequência Escolar por UF</caption>
      <tr><th>UF com maior frequência escolar</th><td>${freq.uf_maior_freq || '-'}</td><td>${freq.maior_freq_percent || '-'}%</td></tr>
      <tr><th>UF com menor frequência escolar</th><td>${freq.uf_menor_freq || '-'}</td><td>${freq.menor_freq_percent || '-'}%</td></tr>
      <tr><th>Média nacional de frequência escolar</th><td colspan=2>${freq.media_percent || '-'}%</td></tr>
      <tr><th>Desvio padrão entre UFs</th><td colspan=2>${freq.desvio_padrao || '-'}</td></tr>
    </table>
    <table>
      <caption>Resumo Estatístico — Rede de Ensino (apenas quem frequenta escola)</caption>
      <tr><th>Total respondentes</th><td colspan=2>${rede.total_respondentes || '-'}</td></tr>
      ${Object.keys(rede.resumo||{}).map(k => `
        <tr><th>${k}</th>
        <td>${rede.resumo[k].percentual}%</td>
        <td>${rede.resumo[k].total} alunos</td></tr>
      `).join("")}
    </table>
  `;
}
