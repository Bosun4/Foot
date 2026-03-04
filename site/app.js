function badge(label){
  if(label.includes("强推")) return `<span class="badge b-hot">${label}</span>`;
  if(label.includes("主推")) return `<span class="badge b-star">${label}</span>`;
  if(label.includes("可博")) return `<span class="badge b-ok">${label}</span>`;
  return `<span class="badge b-no">${label}</span>`;
}
async function main(){
  const themeBtn = document.getElementById("theme");
  const saved = localStorage.getItem("theme") || "dark";
  if(saved === "light") document.documentElement.classList.add("light");
  themeBtn.onclick = () => {
    document.documentElement.classList.toggle("light");
    localStorage.setItem("theme", document.documentElement.classList.contains("light") ? "light" : "dark");
  };

  const res = await fetch("data/picks.json", {cache:"no-store"});
  const data = await res.json();

  document.getElementById("meta").textContent =
    `更新时间(UTC)：${data.meta.generated_at_utc} ｜ Python ${data.meta.python} ｜ 赛季：${data.meta.seasons_used.join(", ")} ｜ 融合：PE ${data.meta.fusion.W_PE} + ML ${data.meta.fusion.W_ML}（ML=${data.meta.fusion.ml_enabled}）`;

  document.getElementById("k_fx").textContent = String(data.stats.fixtures ?? "-");
  document.getElementById("k_top").textContent = String(data.stats.top ?? "-");
  const bt = data.stats.backtest || {};
  document.getElementById("k_roi").textContent = ((bt.roi ?? 0)*100).toFixed(1) + "%";
  document.getElementById("k_hit").textContent = ((bt.hit_rate ?? 0)*100).toFixed(1) + "%";
  // additional cards
  document.getElementById("k_ev").textContent = ((bt.avg_ev ?? 0)*100).toFixed(1) + "%";
  document.getElementById("k_log").textContent = (bt.logloss != null) ? bt.logloss.toFixed(3) : "-";
  // fill stats table section
  document.getElementById("s_matches").textContent = bt.matches_used ?? "-";
  document.getElementById("s_bets").textContent = bt.bets ?? "-";
  document.getElementById("s_ev").textContent = ((bt.avg_ev ?? 0)*100).toFixed(1) + "%";
  document.getElementById("s_log").textContent = (bt.logloss != null) ? bt.logloss.toFixed(3) : "-";
  document.getElementById("s_roi").textContent = ((bt.roi ?? 0)*100).toFixed(1) + "%";
  document.getElementById("s_hit").textContent = ((bt.hit_rate ?? 0)*100).toFixed(1) + "%";

  const top = data.top_picks || [];
  const all = data.all || [];

  function renderModelProbs(x){
    const tpl = (tag, arr) => {
      if(!arr) return '';
      return `<div class="model">${tag}: ` +
             `${(arr[0]*100).toFixed(1)} / ${(arr[1]*100).toFixed(1)} / ${(arr[2]*100).toFixed(1)}%</div>`;
    };
    let out = `<div class="prob-block">`;
    out += tpl('PE', x.pe_p);
    out += tpl('ML', x.ml_p);
    out += tpl('BM', x.bm_p);
    out += `</div>`;
    return out;
  }

  document.querySelector("#top tbody").innerHTML = top.map(x => `
    <tr>
      <td>${x.date||""}</td>
      <td>${x.league||""}</td>
      <td>${x.home||""}</td>
      <td>${x.away||""}</td>
      <td>${badge(x.label||"-")} ${x.pick?(" · "+x.pick):""}</td>
      <td>${x.score ?? "-"}</td>
      <td>${x.ev ?? "-"}</td>
      <td>${x.kelly ?? "-"}</td>
      <td>${x.p_home?`${(x.p_home*100).toFixed(1)} / ${(x.p_draw*100).toFixed(1)} / ${(x.p_away*100).toFixed(1)}%`:"-"}</td>
      <td>${renderModelProbs(x) || "-"}</td>
      <td>${x.odds_win?`${x.odds_win} / ${x.odds_draw} / ${x.odds_lose} (${x.book||"-"})`:"-"}</td>
    </tr>
  `).join("");

  document.querySelector("#all tbody").innerHTML = all.map(x => `
    <tr>
      <td>${x.date||""}</td>
      <td>${x.league||""}</td>
      <td>${x.home||""}</td>
      <td>${x.away||""}</td>
      <td>${(x.xg_home!=null)?`${x.xg_home.toFixed(2)} / ${x.xg_away.toFixed(2)}`:"-"}</td>
      <td>${x.p_home?`${(x.p_home*100).toFixed(1)} / ${(x.p_draw*100).toFixed(1)} / ${(x.p_away*100).toFixed(1)}%`:"-"}</td>
      <td>${renderModelProbs(x) || ""}</td>
      <td>${x.most_likely_score||""}</td>
      <td>${badge(x.label||"-")}</td>
      <td title="${(x.why||"").replaceAll('"','')}">${x.why||""}</td>
    </tr>
  `).join("");
}
main().catch(e=>{ document.getElementById("meta").textContent="加载失败："+e; });

async function renderJCZQ(){
  try{
    const res = await fetch("data/jczq.json", {cache:"no-store"});
    const data = await res.json();
    const tb = document.querySelector("#jczq tbody");
    if(!tb) return;
    const ms = data.matches || [];
    if(ms.length === 0){
      tb.innerHTML = `<tr><td colspan="8">暂无数据（${data.meta?.error || "可能接口未配置/不可访问"}）</td></tr>`;
      return;
    }
    tb.innerHTML = ms.slice(0,200).map(m=>`
      <tr>
        <td>${m.league||""}</td>
        <td>${m.time||""}</td>
        <td>${m.home||""}</td>
        <td>${m.away||""}</td>
        <td>${m.odds_win ?? "-"}</td>
        <td>${m.odds_draw ?? "-"}</td>
        <td>${m.odds_lose ?? "-"}</td>
        <td>${m.handicap ?? "-"}</td>
      </tr>
    `).join("");
  }catch(e){
    const tb = document.querySelector("#jczq tbody");
    if(tb) tb.innerHTML = `<tr><td colspan="8">加载失败：${e}</td></tr>`;
  }
}

// simple sortable tables implementation
function makeSortable(id){
  const table = document.getElementById(id);
  if(!table) return;
  const headers = table.querySelectorAll('th');
  headers.forEach((th,idx)=>{
    th.style.cursor='pointer';
    th.addEventListener('click',()=>{
      const tbody = table.tBodies[0];
      const rows = Array.from(tbody.rows);
      const cmp = (a,b)=>{
        const va = a.cells[idx].textContent.trim();
        const vb = b.cells[idx].textContent.trim();
        const na = parseFloat(va.replace(/[^\
0-9\.\-]/g,''));
        const nb = parseFloat(vb.replace(/[^
0-9\.\-]/g,''));
        if(!isNaN(na) && !isNaN(nb)) return na - nb;
        return va.localeCompare(vb);
      };
      rows.sort(cmp);
      if(th.dataset.sorted==='asc'){
        rows.reverse();
        th.dataset.sorted='desc';
      } else {
        th.dataset.sorted='asc';
      }
      rows.forEach(r=>tbody.appendChild(r));
    });
  });
}

main().then(()=>{
  makeSortable('top');
  makeSortable('all');
});

renderJCZQ();

// 加载预测表与图表示例
async function loadPredictions(){
  try{
    const res = await fetch('/data/predictions.json', {cache:'no-store'});
    const data = await res.json();

    // DataTables 渲染
    if(window.$ && $.fn && $.fn.DataTable){
      const columns = [
        {title:'日期', data:'date'},
        {title:'联赛', data:'league'},
        {title:'主队', data:'主队'},
        {title:'客队', data:'客队'},
        {title:'xG主', data:'xG主', render: d => (d==null?'-':d.toFixed(2))},
        {title:'xG客', data:'xG客', render: d => (d==null?'-':d.toFixed(2))},
        {title:'胜率', data:'p_home', render: d => (d==null?'-':(d*100).toFixed(1)+'%')},
        {title:'平率', data:'p_draw', render: d => (d==null?'-':(d*100).toFixed(1)+'%')},
        {title:'负率', data:'p_away', render: d => (d==null?'-':(d*100).toFixed(1)+'%')},
        {title:'预测', data:'pred', defaultContent:''}
      ];
      if($.fn.DataTable.isDataTable('#fullTable')){
        const dt = $('#fullTable').DataTable();
        dt.clear(); dt.rows.add(data); dt.draw();
      } else {
        $('#fullTable').DataTable({ data: data, columns: columns, pageLength: 25, order:[[0,'desc']], responsive: true });
      }
    } else {
      // 简单回退：直接写入表格 body（如果存在）
      const tb = document.querySelector('#fullTable tbody');
      if(tb){
        tb.innerHTML = data.map(d=>`<tr>
          <td>${d.date||''}</td>
          <td>${d.league||''}</td>
          <td>${d.主队||''}</td>
          <td>${d.客队||''}</td>
          <td>${d.xG主!=null?d.xG主.toFixed(2):'-'}</td>
          <td>${d.xG客!=null?d.xG客.toFixed(2):'-'}</td>
          <td>${d.p_home?((d.p_home*100).toFixed(1)+'%'):'-'}</td>
          <td>${d.p_draw?((d.p_draw*100).toFixed(1)+'%'):'-'}</td>
          <td>${d.p_away?((d.p_away*100).toFixed(1)+'%'):'-'}</td>
          <td>${d.pred||''}</td>
        </tr>`).join('');
      }
    }

    // Chart.js 示例：xG 对比
    const canvas = document.getElementById('predChart');
    if(canvas && window.Chart){
      const ctx = canvas.getContext('2d');
      if(window._predChartInstance) window._predChartInstance.destroy();
      window._predChartInstance = new Chart(ctx, {
        type: 'bar',
        data: {
          labels: data.map(d=> (d.主队||'') + ' vs ' + (d.客队||'')),
          datasets: [
            { label: 'xG主', data: data.map(d=> d.xG主 || 0), backgroundColor: 'rgba(54,162,235,0.6)' },
            { label: 'xG客', data: data.map(d=> d.xG客 || 0), backgroundColor: 'rgba(255,99,132,0.6)' }
          ]
        },
        options: { responsive: true, scales: { y: { beginAtZero: true } } }
      });
    }
  }catch(e){
    console.error('loadPredictions error', e);
    const el = document.getElementById('predError'); if(el) el.textContent = '加载预测数据失败：'+e;
  }
}

// Top Picks 同理，渲染到 #topPicksTable 和 #topPicksChart（如果存在）
async function loadTopPicks(){
  try{
    const res = await fetch('/data/top_picks.json', {cache:'no-store'});
    const data = await res.json();
    if(window.$ && $.fn && $.fn.DataTable){
      const cols = [
        {title:'日期', data:'date'},
        {title:'联赛', data:'league'},
        {title:'主队', data:'home'},
        {title:'客队', data:'away'},
        {title:'建议', data:'pick'},
        {title:'标签', data:'label'}
      ];
      if($.fn.DataTable.isDataTable('#topPicksTable')){
        const dt = $('#topPicksTable').DataTable(); dt.clear(); dt.rows.add(data); dt.draw();
      } else {
        $('#topPicksTable').DataTable({ data: data, columns: cols, pageLength: 25, order:[[0,'desc']] });
      }
    } else {
      const tb = document.querySelector('#topPicksTable tbody');
      if(tb) tb.innerHTML = data.map(d=>`<tr><td>${d.date||''}</td><td>${d.league||''}</td><td>${d.home||''}</td><td>${d.away||''}</td><td>${d.pick||''}</td><td>${d.label||''}</td></tr>`).join('');
    }

    const canvas = document.getElementById('topPicksChart');
    if(canvas && window.Chart){
      const ctx = canvas.getContext('2d');
      if(window._topPicksChart) window._topPicksChart.destroy();
      window._topPicksChart = new Chart(ctx, {
        type: 'bar',
        data: {
          labels: data.slice(0,20).map(d=> (d.home||'') + ' vs ' + (d.away||'')),
          datasets: [{ label: 'EV (示例)', data: data.slice(0,20).map(d=> d.ev || 0), backgroundColor: 'rgba(75,192,192,0.6)' }]
        },
        options: { responsive: true, scales: { y: { beginAtZero: true } } }
      });
    }
  }catch(e){
    console.error('loadTopPicks error', e);
  }
}

// 调用
loadPredictions();
loadTopPicks();
