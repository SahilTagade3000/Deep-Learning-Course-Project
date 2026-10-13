'use strict';
const $ = id => document.getElementById(id);
const esc = value => String(value ?? '').replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const number = value => Number(value).toLocaleString('en-US');
const score = value => value == null ? '—' : (value * 100).toFixed(2);
const fixed = value => Number(value).toFixed(4);
const names = {overview:'Command Center',transactions:'Transaction Intelligence',risk:'Temporal Risk',warnings:'Early Warning Center',network:'Network Investigation',models:'Model Intelligence'};
const state = {page:'overview',period:42,speed:3,running:false,lastTick:0,updated:'Not started',selected:null,query:'',risk:'All',label:'All',offset:0,history:false,explore:false,level:0,increase:0,model:'Temporal GNN',result:null,meta:null,sequence:0,theme:'light'};
try { state.theme = localStorage.getItem('temporal-web-theme') || 'light'; } catch (_) {}
if (!['light','dark'].includes(state.theme)) state.theme='light';
document.documentElement.dataset.theme=state.theme;
const badge = name => `<span class="badge ${esc(name)}">${esc(name)}</span>`;
const metric = (label,value,note='',accent=false) => `<div class="metric ${accent?'accent':''}"><div class="metric-label">${esc(label)}</div><div class="metric-value">${esc(value)}</div><div class="metric-note">${esc(note)}</div></div>`;
const header = (title,subtitle,tag='OBSERVED TEST PERIODS') => `<div class="page-header"><div><div class="eyebrow">${esc(names[state.page])} / RESEARCH WORKSPACE</div><h1>${esc(title)}</h1><p class="subtitle">${esc(subtitle)}</p></div><span class="count-badge">${esc(tag)}</span></div>`;
const callout = (title,text) => `<div class="callout"><strong>${esc(title)}</strong><p>${esc(text)}</p></div>`;
const chartCard = (title,id,note='',large=false) => `<section class="card"><div class="card-head"><h2>${esc(title)}</h2></div><div id="${id}" class="chart ${large?'large':''}"></div>${note?`<p class="note">${esc(note)}</p>`:''}</section>`;
const refButton = row => `<button class="button link" data-tx="${row.id}">${esc(row.reference)}</button>`;
const table = (rows,columns) => rows.length ? `<div class="table-wrap"><table><thead><tr>${columns.map(c=>`<th>${esc(c[0])}</th>`).join('')}</tr></thead><tbody>${rows.map(row=>`<tr>${columns.map(c=>`<td>${c[1](row)}</td>`).join('')}</tr>`).join('')}</tbody></table></div>` : '<div class="empty">No matching records in the observed periods.</div>';
const txColumns = [['Transaction',refButton],['Period',r=>r.period],['Score / 100',r=>score(r.score)],['Review band',r=>badge(r.band)],['Recorded label',r=>esc(r.label)]];
const riskColumns = [['Period',r=>r.period],['Previous score',r=>score(r.previous)],['Population score',r=>score(r.mean)],['Change (points)',r=>r.change==null?'—':`${r.change>=0?'+':''}${score(r.change)}`],['Review level',r=>badge(r.level)],['Frozen flag',r=>r.warning?'Yes':'No']];

async function api(path,options={}) {
  const response=await fetch('/api'+path,options);
  const data=await response.json();
  if(!response.ok) {
    const detail=typeof data.detail==='string'?data.detail:'Check the selected reference, period or input values.';
    throw new Error(detail);
  }
  return data;
}
function css(name){return getComputedStyle(document.documentElement).getPropertyValue(name).trim();}
function palette(){return {Low:css('--accent'),Watch:css('--gold'),High:css('--orange'),Critical:css('--red')};}
function layout(extra={}) {
  return {paper_bgcolor:css('--panel'),plot_bgcolor:css('--panel'),font:{family:'Segoe UI, sans-serif',color:css('--muted'),size:11},margin:{l:46,r:18,t:24,b:48},autosize:true,
    xaxis:{gridcolor:css('--line'),zeroline:false},yaxis:{gridcolor:css('--line'),zeroline:false},
    legend:{orientation:'h',y:-.22,x:0},hoverlabel:{bgcolor:css('--panel'),font:{color:css('--ink')}},...extra};
}
function plot(id,traces,extra={}) {
  if(!$(id)) return;
  return Plotly.newPlot(id,traces,layout(extra),{responsive:true,displaylogo:false,scrollZoom:false,modeBarButtonsToRemove:['lasso2d','select2d']}).catch(error=>{toast('A chart could not render: '+error.message);});
}
function trajectory(id,rows,threshold=true) {
  const shapes=threshold?[{type:'line',xref:'paper',x0:0,x1:1,y0:state.meta.rule.risk_threshold*100,y1:state.meta.rule.risk_threshold*100,line:{color:css('--gold'),dash:'dot',width:1}}]:[];
  if(rows[0]?.period<42) shapes.push({type:'line',x0:41.5,x1:41.5,yref:'paper',y0:0,y1:1,line:{color:css('--muted'),dash:'dash',width:1}});
  plot(id,[{x:rows.map(r=>r.period),y:rows.map(r=>r.mean*100),type:'scatter',mode:'lines+markers',name:'Population score',line:{color:css('--accent'),width:2.5},marker:{size:6},fill:'tozeroy',fillcolor:state.theme==='light'?'rgba(13,115,102,.05)':'rgba(118,212,191,.07)',hovertemplate:'Period %{x}<br>Population score %{y:.2f} / 100<extra></extra>'}],
    {shapes,xaxis:{...layout().xaxis,title:{text:'Monitoring Period'},dtick:rows.length<10?1:5,...(rows[0]?.period>=42?{range:[41.7,49.3]}:{})},yaxis:{...layout().yaxis,title:{text:'Model score / 100'},rangemode:'tozero'}});
}
function stop(){state.running=false;updateControls();}
function selectTransaction(id,page=state.page){stop();state.selected=Number(id);state.result=null;state.page=page;render();}
function bindReferences(page){document.querySelectorAll('[data-tx]').forEach(button=>button.onclick=()=>selectTransaction(button.dataset.tx,page));}
function updateControls(){
  $('period').value=state.period;
  $('start').textContent=state.running?'Replaying…':'Start replay';
  $('start').disabled=state.running;
  $('pause').disabled=!state.running;
  $('replay-status').textContent=`${state.running?'Active':state.period===49?'Complete':'Paused'} · Period ${state.period} of 49 · Updated: ${state.updated}`;
  $('replay-dot').classList.toggle('active',state.running);
  $('replay-progress').style.width=`${(state.period-41)/8*100}%`;
  $('theme-toggle').textContent=state.theme==='light'?'Dark theme':'Light theme';
  $('breadcrumb').textContent=names[state.page];
  document.querySelectorAll('.nav').forEach(button=>{const active=button.dataset.page===state.page;button.classList.toggle('active',active);button.setAttribute('aria-current',active?'page':'false');});
}
function toast(message){$('toast').textContent=message;$('toast').style.display='block';clearTimeout(toast.timer);toast.timer=setTimeout(()=>$('toast').style.display='none',4500);}

async function overview(token) {
  const data=await api(`/overview?period=${state.period}`);if(token!==state.sequence)return;
  const k=data.kpis,last=data.risk.at(-1);
  $('view').innerHTML=header('Transaction Risk Intelligence','Graph relationships and temporal context, brought together in one investigation workspace.')+
    `<div class="metrics">${metric('Dataset coverage',number(k.total),'All exported transactions')}${metric('Transactions replayed',number(k.processed),`Test periods 42–${state.period}`,true)}${metric('High-risk predictions',number(k.high),'At the frozen model threshold')}${metric('Escalation flags',number(k.alerts),'Frozen population rule')}${metric('Temporal GNN · test F1',fixed(k.f1),'Full labelled test benchmark')}</div>`+
    `<div class="grid two">${chartCard('Population risk trajectory','overview-risk','Dotted line: frozen population level condition. Both level and increase conditions are needed for an escalation flag.')}${chartCard('Transaction review distribution','overview-distribution','Display bands organize uncalibrated scores. They are not additional trained classes.')}</div>`+
    `<div class="grid two"><section class="card"><div class="card-head"><h2>Priority investigation queue</h2><small>Highest scores · Period ${state.period}</small></div>${table(data.queue,txColumns)}<p class="note">Click a reference to investigate its model score and network.</p></section><section class="card"><div class="card-head"><h2>Current population context</h2>${badge(last.level)}</div><div class="detail-label">Population score / 100</div><div class="detail-value">${score(last.mean)}</div><div class="detail-label">One-period change · score points</div><div class="detail-value">${last.change>=0?'+':''}${score(last.change)}</div>${callout('Observed escalation',last.warning?'Both frozen conditions are met.':'No frozen escalation flag for this period. Individual high-scoring records remain visible for review.')}<div class="section-label">Recorded labels · replayed records</div>${table(Object.entries(data.labels).map(([label,count])=>({label,count})),[['Label',r=>esc(r.label)],['Transactions',r=>number(r.count)]])}</section></div>`+
    `<details><summary>Dataset activity and interpretation</summary>${chartCard('Observed transaction volume','overview-activity')}<p class="note">Replay uses complete historical snapshots. It does not imply a within-period transaction arrival order.</p></details>`;
  trajectory('overview-risk',data.risk);
  plot('overview-distribution',[{type:'pie',labels:Object.keys(data.bands),values:Object.values(data.bands),hole:.76,sort:false,textinfo:'none',marker:{colors:Object.values(palette())},hovertemplate:'%{label}: %{value:,}<extra></extra>'}],
    {margin:{l:15,r:15,t:15,b:36},legend:{orientation:'h',y:-.08,x:.1},annotations:[{x:.5,y:.5,showarrow:false,text:`<b>${number(k.processed)}</b><br>transactions`,font:{size:17,color:css('--ink')}}]});
  plot('overview-activity',[{type:'bar',x:data.risk.map(r=>r.period),y:data.risk.map(r=>r.transactions),marker:{color:css('--blue')},hovertemplate:'Period %{x}<br>%{y:,} transactions<extra></extra>'}],{xaxis:{...layout().xaxis,title:{text:'Monitoring Period'},dtick:1},yaxis:{...layout().yaxis,title:{text:'Transactions'}}});
  bindReferences('transactions');
  // Plotly needs a resize after a collapsed technical section becomes visible.
  document.querySelector('details').ontoggle=()=>{const graph=$('overview-activity');if(graph&&graph.offsetParent)Plotly.Plots.resize(graph);};
}

function filterMarkup(pool){return `<div class="filters"><div class="field"><label for="tx-search">Transaction Reference</label><input id="tx-search" value="${esc(state.query)}" placeholder="Search TX-73160850"></div><div class="field"><label for="risk-filter">Review band</label><select id="risk-filter">${['All','Low','Watch','High','Critical'].map(v=>`<option ${state.risk===v?'selected':''}>${v}</option>`).join('')}</select></div><div class="field"><label for="label-filter">Recorded label</label><select id="label-filter">${['All','Licit','Illicit','Unlabelled'].map(v=>`<option ${state.label===v?'selected':''}>${v}</option>`).join('')}</select></div><button class="button" id="apply-search">Search</button></div><div class="inline-actions"><span class="note">Real demonstration cases:</span>${pool.demos.map(d=>`<button class="button ghost small" data-tx="${d.id}">${esc(d.name)}</button>`).join('')}</div>`;}
function bindFilters(){
  $('apply-search').onclick=()=>{stop();state.query=$('tx-search').value;state.risk=$('risk-filter').value;state.label=$('label-filter').value;state.offset=0;state.selected=null;render();};
  $('tx-search').onkeydown=e=>{if(e.key==='Enter')$('apply-search').click();};
}
async function investigation(token,networkPage=false){
  const params=new URLSearchParams({period:state.period,query:state.query,risk:state.risk,label:state.label,offset:state.offset,limit:10});
  const pool=await api('/transactions?'+params);if(token!==state.sequence)return;
  let id=state.selected||pool.rows[0]?.id;
  let detail=null,graph=null;
  if(id){
    try{detail=await api(`/transactions/${id}?period=${state.period}`);}
    catch(error){if(state.selected&&pool.rows[0]){id=pool.rows[0].id;detail=await api(`/transactions/${id}?period=${state.period}`);state.result=null;}else throw error;}
    if(networkPage)graph=await api(`/network/${id}?period=${state.period}`);
  }
  if(token!==state.sequence)return;state.selected=id||null;
  let body=header(names[state.page],networkPage?'Explore actual directed relationships around an anonymous transaction.':'Investigate a real transaction and run the saved Temporal GNN on its complete snapshot.')+
    `<section class="card"><div class="card-head"><h2>Choose a transaction</h2><small>Observed periods 42–${state.period}</small></div>${filterMarkup(pool)}${table(pool.rows,txColumns)}<div class="pagination"><span>${number(pool.total)} matches · Showing ${pool.rows.length?state.offset+1:0}–${Math.min(state.offset+10,pool.total)}</span><div><button class="button ghost small" id="previous" ${state.offset===0?'disabled':''}>Previous</button><button class="button ghost small" id="next" ${state.offset+10>=pool.total?'disabled':''}>Next</button></div></div></section>`;
  if(detail){
    const r=detail.record,verified=state.result?.id===id?state.result:null;
    if(networkPage){
      body+=`<div class="section-label">Investigating ${esc(r.reference)} · Period ${r.period}</div><div class="grid investigation">${chartCard('Transaction neighbourhood','network-chart','Larger outlined node: selected transaction. Arrows show original direction. Click a node to investigate it.',true)}<section class="card"><h2>${esc(r.reference)}</h2><div class="detail-label">Network Connections · full neighbourhood</div><div class="detail-value">${number(graph.connections)}</div><div class="detail-label">High-risk neighbours · full neighbourhood</div><div class="detail-value">${number(graph.high_neighbours)}</div><div class="detail-label">Displayed network size</div><div class="detail-value">${graph.displayed_nodes} nodes</div><div class="detail-label">Average neighbour score / 100</div><div class="detail-value">${score(graph.neighbour_mean)}</div>${callout('A focused investigation view','The visual includes at most 30 neighbours. Model inference uses the complete undirected snapshot. Connections do not establish shared ownership or criminal activity.')}</section></div>`;
    }else{
      body+=`<div class="section-label">Transaction assessment</div><section class="card"><div class="card-head"><h2>${esc(r.reference)}</h2>${badge(r.band)}</div><div class="split-detail"><div id="transaction-gauge" class="chart gauge"></div><div><p class="subheading">${verified?'Verified CPU inference':'Saved Kaggle model score'}</p><h3>${r.flagged?'Flagged for review':'Below review threshold'}</h3><div class="detail-grid"><div><div class="detail-label">Monitoring Period</div><div class="detail-value">${r.period}</div></div><div><div class="detail-label">Network Connections</div><div class="detail-value">${detail.connections}</div></div><div><div class="detail-label">Recorded label</div><div class="detail-value">${esc(r.label)}</div></div><div><div class="detail-label">Decision threshold / 100</div><div class="detail-value">${score(detail.threshold)}</div></div></div><div class="inline-actions" style="margin-top:18px"><button id="analyze" class="button primary">Run model analysis</button><button class="button" id="open-network">Investigate network</button></div><p class="note" id="analysis-status" style="margin-top:10px">${verified?`Verified ${number(verified.snapshot_nodes)} snapshot nodes on CPU · ${verified.elapsed_seconds.toFixed(2)}s · max score difference ${verified.maximum_snapshot_difference.toExponential(2)}`:'Analyze runs the original GCN + GRU with the saved scaler and previous graph context.'}</p></div></div>${callout('Observed risk indicators',`${detail.high_neighbours} of ${detail.connections} direct neighbours exceed the model threshold. The population score changed ${detail.population_change>=0?'+':''}${score(detail.population_change)} points in this period. These indicators are not causal feature explanations.`)}<details><summary>Advanced Model Information</summary><pre>${esc(JSON.stringify({...detail.technical,raw_features:undefined,exported_score:r.score,incoming_connections:detail.incoming,outgoing_connections:detail.outgoing,...(verified||{})},null,2))}</pre><details><summary>165 anonymized numerical model inputs</summary><pre>${esc(JSON.stringify(detail.technical.raw_features,null,2))}</pre></details></details></section>`;
    }
  }
  $('view').innerHTML=body;
  bindReferences();bindFilters();
  $('previous').onclick=()=>{state.offset=Math.max(0,state.offset-10);render();};
  $('next').onclick=()=>{state.offset+=10;render();};
  if(!detail)return;
  if(networkPage){drawNetwork(graph);}else{
    drawGauge(state.result?.id===id?state.result.score:detail.record.score,detail.threshold);
    $('open-network').onclick=()=>selectTransaction(id,'network');
    $('analyze').onclick=async()=>{
      stop();const button=$('analyze'),status=$('analysis-status');button.disabled=true;button.textContent='Analyzing snapshot…';status.textContent='Running verified CPU inference… The first request also loads the saved model.';
      try{const result=await api(`/transactions/${id}/analyze?period=${state.period}`,{method:'POST'});state.result=result;if(state.page==='transactions'&&state.selected===id)await render();}
      catch(error){if(status.isConnected)status.textContent=error.message;toast(error.message);}
      finally{if(button.isConnected){button.disabled=false;button.textContent='Run model analysis';}}
    };
  }
}
function drawGauge(value,threshold){
  const band=value>=.9?'Critical':value>=threshold?'High':value>=threshold*.5?'Watch':'Low';
  plot('transaction-gauge',[{type:'indicator',mode:'gauge+number',value:value*100,number:{suffix:' / 100',font:{size:31,color:css('--ink')}},gauge:{axis:{range:[0,100],tickvals:[0,50,100]},bar:{color:palette()[band]},bgcolor:css('--soft'),borderwidth:0,steps:[{range:[0,threshold*100],color:css('--accent-soft')},{range:[threshold*100,100],color:css('--soft')}],threshold:{value:threshold*100,line:{color:css('--ink'),width:2}}}}],{margin:{l:36,r:36,t:30,b:22}});
}
function drawNetwork(graph){
  const lookup=Object.fromEntries(graph.nodes.map(n=>[n.id,n])),x=[],y=[],annotations=[];
  graph.edges.forEach(edge=>{const a=lookup[edge.source],b=lookup[edge.target];x.push(a.x,b.x,null);y.push(a.y,b.y,null);if(a.id!==b.id)annotations.push({x:b.x*.88+a.x*.12,y:b.y*.88+a.y*.12,ax:b.x*.68+a.x*.32,ay:b.y*.68+a.y*.32,xref:'x',yref:'y',axref:'x',ayref:'y',text:'',showarrow:true,arrowhead:2,arrowwidth:1,arrowsize:.75,arrowcolor:css('--muted')});});
  const colors=palette(),traces=[{type:'scatter',mode:'lines',x,y,line:{color:css('--line'),width:1.5},hoverinfo:'skip',showlegend:false}];
  Object.keys(colors).forEach(band=>{const nodes=graph.nodes.filter(n=>n.band===band);traces.push({type:'scatter',mode:'markers',name:band,x:nodes.map(n=>n.x),y:nodes.map(n=>n.y),customdata:nodes.map(n=>[n.id,n.reference,n.score*100,n.label]),marker:{size:nodes.map(n=>n.selected?28:15),color:colors[band],line:{width:nodes.map(n=>n.selected?3:1),color:css('--ink')}},hovertemplate:'%{customdata[1]}<br>Score %{customdata[2]:.2f} / 100<br>Recorded label: %{customdata[3]}<extra></extra>'});});
  const centre=graph.nodes.find(n=>n.selected);annotations.push({x:centre.x,y:centre.y,text:centre.reference,yshift:27,showarrow:false,font:{color:css('--ink'),size:11}});
  plot('network-chart',traces,{annotations,dragmode:'pan',margin:{l:15,r:15,t:15,b:40},xaxis:{visible:false},yaxis:{visible:false,scaleanchor:'x',scaleratio:1},legend:{orientation:'h',y:-.06,x:0}});
  $('network-chart').on('plotly_click',event=>{const value=event.points[0]?.customdata;if(value)selectTransaction(value[0],'network');});
}

async function riskPage(token){
  const data=await api(`/risk?period=${state.period}&history=${state.history}`);if(token!==state.sequence)return;
  const row=data.rows.at(-1),relative=row.previous>0?(row.change/row.previous*100).toFixed(1)+'%':'—';
  $('view').innerHTML=header('Temporal Risk Intelligence','Track how the observed transaction population changes across monitoring periods.')+
    `<div class="metrics">${metric('Current population score',score(row.mean),'Uncalibrated score / 100',true)}${metric('Previous population score',score(row.previous),'Immediately preceding period')}${metric('Score change',`${row.change>=0?'+':''}${score(row.change)}`,'Score points')}${metric('Relative change',relative,'Compared with previous mean')}${metric('Current review level',row.level,'Frozen population conditions')}</div>`+
    `<section class="card"><div class="card-head"><h2>Population score across time</h2><label class="check"><input type="checkbox" id="include-history" ${state.history?'checked':''}> Include earlier context</label></div><div id="temporal-chart" class="chart large"></div><div class="period-feed">${data.rows.filter(r=>r.period>=42).map(r=>`<div class="period-chip">Period ${r.period}<b>${score(r.mean)}</b>${badge(r.level)}</div>`).join('')}</div><p class="note">Earlier context includes training periods 1–34 and validation periods 35–41. Periods 42–49 are held-out test observations.</p></section>`+
    callout('A population trajectory','Each period contains different transactions. The GRU carries a graph-level summary forward; the curve is not one transaction’s history or an unseen-future forecast.')+
    `<section class="card"><h2>Period details</h2>${table(data.rows.filter(r=>r.period>=42),riskColumns)}</section>`;
  trajectory('temporal-chart',data.rows);
  $('include-history').onchange=e=>{state.history=e.target.checked;render();};
}

async function warningsPage(token){
  const query=state.explore?`&level=${state.level/100}&increase=${state.increase/100}`:'';
  const data=await api(`/warnings?period=${state.period}${query}`);if(token!==state.sequence)return;
  $('view').innerHTML=header('Early Warning Center','Review observed population escalation against the experiment’s frozen conditions.')+
    `<div class="metrics">${metric('Frozen escalation flags',data.alerts.length,`Replayed test periods 42–${state.period}`,true)}${metric('Population level condition',score(data.rule.risk_threshold),'Score / 100')}${metric('Increase condition','+'+score(data.rule.escalation_threshold),'Score points')}${metric('Periods reviewed',data.frozen.length,'Complete observed snapshots')}${metric('Historical triggers',data.historical.length,'Earlier-period examples')}</div>`+
    callout('Two conditions must hold','A frozen escalation flag requires both a sufficiently high population mean and a sufficiently large increase. Watch meets the increase condition only; High meets the level condition only; Critical meets both.')+
    `<section class="card"><div class="card-head"><h2>Frozen monitoring feed</h2><span class="count-badge">ORIGINAL EXPERIMENT</span></div>${data.alerts.length?'': '<p class="subtitle">No frozen escalation flags in the replayed test periods. Individual high-scoring transactions may still require review.</p>'}${table([...data.frozen].reverse(),riskColumns)}</section>`+
    `<div class="grid equal" style="margin-top:18px"><section class="card"><h2>Explore alternative thresholds</h2><p class="subheading">Compare an experimental rule while retaining the frozen results above.</p><label class="check"><input id="explore-toggle" type="checkbox" ${state.explore?'checked':''}> Enable exploratory rule</label><div class="filters"><div class="field"><label for="level-input">Population score / 100</label><input id="level-input" type="number" min="0" max="100" step="0.1" value="${state.level.toFixed(2)}" ${state.explore?'':'disabled'}></div><div class="field"><label for="increase-input">Increase · score points</label><input id="increase-input" type="number" min="0" max="100" step="0.1" value="${state.increase.toFixed(2)}" ${state.explore?'':'disabled'}></div><button class="button" id="apply-rule" ${state.explore?'':'disabled'}>Compare</button></div>${data.exploratory?table(data.exploratory,[['Period',r=>r.period],['Exploratory level',r=>badge(r.level)],['Exploratory flag',r=>r.exploratory_warning?'Yes':'No'],['Frozen flag',r=>r.warning?'Yes':'No']]):'<p class="note">Exploratory flags never change the model threshold, exported scores or benchmark.</p>'}</section><section class="card"><h2>Actual historical example</h2><p class="subheading">Earlier-period rule triggers, separate from held-out test results.</p><div class="field"><label for="historical-case">Choose a recorded trigger</label><select id="historical-case">${data.historical.map(r=>`<option value="${r.period}">Period ${r.period} · ${esc(r.split)}</option>`).join('')}</select></div><div id="historical-detail"></div><p class="note">These descriptive signals have no evaluated warning lead time or future-event labels.</p></section></div>`;
  $('explore-toggle').onchange=e=>{state.explore=e.target.checked;render();};
  $('apply-rule').onclick=()=>{const level=Number($('level-input').value),increase=Number($('increase-input').value);if(!Number.isFinite(level)||!Number.isFinite(increase)||level<0||level>100||increase<0||increase>100){toast('Enter thresholds between 0 and 100.');return;}state.level=level;state.increase=increase;render();};
  const historical=()=>{const row=data.historical.find(r=>r.period===Number($('historical-case').value));$('historical-detail').innerHTML=row?callout(`Period ${row.period} · ${row.split}`,`Population score ${score(row.mean)} / 100; increase +${score(row.change)} points. This example comes from earlier-period predictions.`):'<p class="note">No historical trigger is available.</p>';};
  $('historical-case').onchange=historical;historical();
}

async function modelsPage(token){
  const [data,detail]=await Promise.all([api('/models'),api('/models/'+encodeURIComponent(state.model))]);if(token!==state.sequence)return;
  const metricColumns=[['Model',r=>esc(r.model)],['Accuracy',r=>fixed(r.accuracy)],['Precision',r=>fixed(r.precision)],['Recall',r=>fixed(r.recall)],['F1',r=>fixed(r.f1)],['ROC AUC',r=>fixed(r.roc_auc)],['Average Precision',r=>fixed(r.average_precision)],['Threshold',r=>r.threshold.toFixed(2)]];
  $('view').innerHTML=header('Model Intelligence','Inspect the actual test results, training histories and architecture.','FULL FROZEN TEST BENCHMARK')+
    `<div class="grid two">${chartCard('Frozen test comparison','model-comparison')}<section class="card"><h2>Read the evidence</h2><div class="detail-label">Highest test Average Precision</div><div class="detail-value">${esc(data.winner)}</div><div class="detail-label">Temporal versus reset-history AP difference</div><div class="detail-value">${data.temporal_control_ap_difference>=0?'+':''}${data.temporal_control_ap_difference.toFixed(6)}</div>${callout('Evaluation scope',`${number(data.labelled_test)} labelled test transactions, including ${number(data.illicit_test)} illicit records. Unknown labels are excluded. These single-seed results do not establish statistical significance.`)}<a class="button ghost small" href="/api/download/metrics">Download test results · CSV</a></section></div>`+
    `<section class="card"><div class="card-head"><h2>Measured results</h2><small>Unaffected by the replay cursor</small></div>${table(data.metrics,metricColumns)}</section>`+
    `<div class="filters"><div class="field" style="max-width:300px"><label for="model-select">Inspect evaluation and training history</label><select id="model-select">${state.meta.models.map(name=>`<option ${state.model===name?'selected':''}>${esc(name)}</option>`).join('')}</select></div></div>`+
    `<div class="grid equal">${chartCard('Precision–recall','model-pr','AP is Average Precision, not trapezoidal PR-AUC.')}${chartCard('ROC','model-roc')}</div><div class="grid equal">${chartCard('Frozen confusion matrix','model-confusion')}${chartCard('Recorded training and validation loss','model-history','Neural loss is class-weighted; XGBoost log loss is unweighted.')}</div>`+
    `<section class="card"><h2>Temporal GNN architecture</h2><div class="architecture">${['Transaction graph','2 × GCN','Node embeddings + graph mean','GRU context','Node + temporal embedding','Risk score','Population review rule'].map((name,i)=>`${i?'<i>→</i>':''}<span>${esc(name)}</span>`).join('')}</div><p class="note">The GRU summarizes graph-level context. The node embedding and updated context jointly produce each transaction’s score. The separately frozen rule monitors aggregated scores.</p>${table(Object.entries(data.dimensions).map(([component,size])=>({component,size})),[['Component',r=>esc(r.component)],['Dimension',r=>r.size]])}</section>`;
  plot('model-comparison',[{type:'bar',name:'Average Precision',x:data.metrics.map(r=>r.model),y:data.metrics.map(r=>r.average_precision),marker:{color:css('--accent')}},{type:'bar',name:'F1',x:data.metrics.map(r=>r.model),y:data.metrics.map(r=>r.f1),marker:{color:css('--blue')}}],{yaxis:{...layout().yaxis,range:[0,1],title:{text:'Score'}},margin:{l:40,r:15,t:15,b:73}});
  plot('model-pr',[{type:'scatter',x:detail.recall,y:detail.precision,mode:'lines',line:{color:css('--accent')},name:state.model}],{xaxis:{...layout().xaxis,title:{text:'Recall'},range:[0,1]},yaxis:{...layout().yaxis,title:{text:'Precision'},range:[0,1.05]},shapes:[{type:'line',xref:'paper',x0:0,x1:1,y0:detail.prevalence,y1:detail.prevalence,line:{dash:'dot',color:css('--gold')}}]});
  plot('model-roc',[{type:'scatter',x:detail.fpr,y:detail.tpr,mode:'lines',line:{color:css('--accent')},name:state.model},{type:'scatter',x:[0,1],y:[0,1],mode:'lines',line:{dash:'dot',color:css('--muted')},name:'Chance'}],{xaxis:{...layout().xaxis,title:{text:'False positive rate'},range:[0,1]},yaxis:{...layout().yaxis,title:{text:'True positive rate'},range:[0,1.05]}});
  plot('model-confusion',[{type:'heatmap',z:detail.confusion,x:['Predicted licit','Predicted illicit'],y:['Recorded licit','Recorded illicit'],text:detail.confusion,texttemplate:'%{text}',showscale:false,colorscale:[[0,state.theme==='light'?'#edf5f2':'#1b3238'],[1,'#258b77']]}],{margin:{l:110,r:20,t:10,b:50},yaxis:{autorange:'reversed'}});
  const x=state.model==='XGBoost'?'round':'epoch',train=state.model==='XGBoost'?'train_logloss':'train_loss',val=state.model==='XGBoost'?'validation_logloss':'validation_loss';
  plot('model-history',[{type:'scatter',x:detail.history.map(r=>r[x]),y:detail.history.map(r=>r[train]),mode:'lines',name:'Training',line:{color:css('--accent')}},{type:'scatter',x:detail.history.map(r=>r[x]),y:detail.history.map(r=>r[val]),mode:'lines',name:'Validation',line:{color:css('--orange')}}],{xaxis:{...layout().xaxis,title:{text:x==='round'?'Round':'Epoch'}},yaxis:{...layout().yaxis,title:{text:'Loss'}}});
  $('model-select').onchange=e=>{state.model=e.target.value;render();};
}

async function render(){
  const token=++state.sequence;updateControls();
  $('view').setAttribute('aria-busy','true');
  if(!$('view').children.length)$('view').innerHTML='<div class="loading">Loading the verified experiment…</div>';
  try{
    if(!state.meta)return;
    const handlers={overview,transactions:t=>investigation(t,false),risk:riskPage,warnings:warningsPage,network:t=>investigation(t,true),models:modelsPage};
    await handlers[state.page](token);
  }catch(error){if(token===state.sequence){$('view').innerHTML=`<div class="error"><h2>This view could not load</h2><p>${esc(error.message)}</p><button id="retry" class="button">Try again</button></div>`;$('retry').onclick=render;}}
  finally{if(token===state.sequence)$('view').setAttribute('aria-busy','false');}
}
function changePeriod(period){state.period=period;state.offset=0;state.updated=new Date().toLocaleTimeString();render();}
document.querySelectorAll('.nav').forEach(button=>button.onclick=()=>{state.page=button.dataset.page;render();});
for(let period=42;period<=49;period++)$('period').add(new Option(String(period),String(period)));
$('period').onchange=e=>{stop();changePeriod(Number(e.target.value));};
$('speed').onchange=e=>{state.speed=Number(e.target.value);state.lastTick=performance.now();};
$('start').onclick=()=>{if(state.period===49){state.selected=null;state.result=null;changePeriod(42);}state.running=true;state.lastTick=performance.now();updateControls();};
$('pause').onclick=stop;
$('reset').onclick=()=>{stop();state.selected=null;state.result=null;changePeriod(42);};
$('theme-toggle').onclick=()=>{state.theme=state.theme==='light'?'dark':'light';document.documentElement.dataset.theme=state.theme;try{localStorage.setItem('temporal-web-theme',state.theme);}catch(_){}render();};
setInterval(()=>{if(state.running&&performance.now()-state.lastTick>=state.speed*1000){state.lastTick=performance.now();if(state.period<49)changePeriod(state.period+1);if(state.period===49)stop();}},250);
async function boot(){
  try{state.meta=await api('/meta');state.level=state.meta.rule.risk_threshold*100;state.increase=state.meta.rule.escalation_threshold*100;$('model-status').textContent='MODEL READY · CPU';$('connection').textContent=`${state.meta.manifest_files} artifacts verified`;await render();}
  catch(error){$('connection').textContent='Connection unavailable';$('view').innerHTML=`<div class="error"><h2>Connect to your local model server</h2><p>${esc(error.message)}</p><p>Keep the VS Code server terminal running and open its printed localhost address.</p><button id="retry" class="button">Reconnect</button></div>`;$('retry').onclick=boot;}
}
updateControls();boot();
