import './styles.css';
import licensedRun from '../public/licensed/pexels-15448993/events.json';

const MATCH = {
  home: { id: 'east', name: 'East United', short: 'EAS', color: '#d6ff4b' },
  away: { id: 'north', name: 'North City', short: 'NOR', color: '#8ad7ff' },
};

const events = [
  ['e01', 12, 'PASS', 'north', 18, 52, 'N. Vale', 'complete'],
  ['e02', 38, 'PRESSURE', 'east', 52, 39, 'M. Sol', 'applied'],
  ['e03', 64, 'POSSESSION_RECOVERY', 'east', 71, 24, 'A. Reid', 'won'],
  ['e04', 70, 'PASS', 'east', 78, 37, 'A. Reid', 'complete'],
  ['e05', 78, 'SHOT', 'east', 88, 46, 'J. Ito', 'saved'],
  ['e06', 122, 'TACKLE', 'north', 45, 66, 'K. Moss', 'won'],
  ['e07', 151, 'POSSESSION_RECOVERY', 'east', 76, 71, 'M. Sol', 'won'],
  ['e08', 164, 'PASS', 'east', 82, 62, 'M. Sol', 'complete'],
  ['e09', 171, 'SHOT', 'east', 91, 55, 'Player 7', 'blocked'],
  ['e10', 205, 'PRESSURE', 'east', 69, 30, 'A. Reid', 'applied'],
  ['e11', 231, 'POSSESSION_LOSS', 'north', 73, 46, 'N. Vale', 'lost'],
  ['e12', 232, 'POSSESSION_RECOVERY', 'east', 73, 46, 'A. Reid', 'won'],
  ['e13', 241, 'PASS', 'east', 84, 50, 'A. Reid', 'complete'],
  ['e14', 244, 'SHOT', 'east', 93, 49, 'Player 7', 'goal'],
  ['e15', 244, 'GOAL', 'east', 100, 50, 'Player 7', 'goal'],
  ['e16', 281, 'PASS', 'north', 42, 24, 'K. Moss', 'complete'],
  ['e17', 306, 'PRESSURE', 'north', 61, 58, 'N. Vale', 'applied'],
  ['e18', 329, 'SHOT', 'north', 89, 43, 'N. Vale', 'wide'],
  ['e19', 378, 'SUBSTITUTION', 'east', null, null, 'L. Chen', 'on'],
  ['e20', 421, 'POSSESSION_RECOVERY', 'north', 75, 65, 'K. Moss', 'won'],
].map(([id,time,type,team,x,y,player,outcome]) => ({id,time,type,team,x,y,player,outcome}));

const templates = [
  'Alert me when East United wins possession in the attacking third three times within five minutes.',
  'Follow every shot involving Player 7.',
  'Tell me when East United recovers possession and takes a shot within 15 seconds.',
  'Notify me when there are at least three shots in five minutes.',
  'Tell me when the left-back is leaving too much space behind him.'
];

const realTemplates = [
  'Find a high-tempo passage with rapid ball travel and repeated player involvement.',
  'Show every rapid ball-movement candidate.',
  'Notify me when ball-contact confidence is at least 80%.',
];

const realEvents = licensedRun.events.map(event => {
  const contact = event.type === 'BALL_CONTACT_CANDIDATE';
  const evidence = event.evidence;
  return {
    id:event.id, time:event.timestamp_seconds, type:event.type, frame:event.frame,
    confidence:event.confidence, status:event.status, real:true, evidence,
    player:contact && evidence.nearest_player_track_id ? `Track P${evidence.nearest_player_track_id}` : 'Tracked ball',
    evidenceText:contact
      ? `Ball track ${evidence.ball_detection_track_id} · nearest player P${evidence.nearest_player_track_id} · ${evidence.supporting_frames.length} supporting frames`
      : `Frames ${evidence.start_frame}–${evidence.end_frame} · displacement ${evidence.normalized_displacement} · threshold ${evidence.threshold}`,
  };
});

const REAL_SCENES = [
  {id:'pexels-15448993', sequence:'PUBLIC DEMO', title:'Licensed match tracking', story:'A real match clip is tracked frame by frame, then all 10 candidates are replayed through the Director rule engine.', video:'/licensed/pexels-15448993/tracked.mp4', ball:'73.7%', tracks:'3,183', events:10, licensed:true, duration:18, moments:realEvents.map(event=>({time:event.time,type:event.type.replaceAll('_',' '),confidence:event.confidence,evidence:event.evidenceText}))},
  {id:'snmot-101', sequence:'SNMOT-101', title:'Goal threat', story:'Rapid progression produces a shot-level threat.', video:'/demo-scenes/snmot-101.mp4', ball:1, tracks:'11 : 8', events:16, moments:[
    {time:7.64,type:'RAPID PROGRESSION',confidence:.74,evidence:'Ball track 1 · frames 167–192 · displacement 0.1678'},
    {time:23.96,type:'SHOT CANDIDATE',confidence:.70,evidence:'Ball track 1 · frames 595–600 · speed 0.0751'},
  ]},
  {id:'snmot-068', sequence:'SNMOT-068', title:'Fast transition', story:'The phase opens into a rapid end-to-end transition.', video:'/demo-scenes/snmot-068.mp4', ball:8, tracks:'11 : 9', events:17, moments:[
    {time:1.00,type:'RAPID PROGRESSION',confidence:.80,evidence:'Ball track 8 · frames 1–26 · displacement 0.2545'},
    {time:4.64,type:'PRESSURE CANDIDATE',confidence:.74,evidence:'Possessor P11 · opponents P5 + P6 · 7 supporting frames'},
  ]},
  {id:'snmot-099', sequence:'SNMOT-099', title:'Pressure → turnover', story:'Sustained pressure is followed by a stable possession change.', video:'/demo-scenes/snmot-099.mp4', ball:5, tracks:'10 : 7', events:10, moments:[
    {time:19.80,type:'PRESSURE CANDIDATE',confidence:.74,evidence:'Possessor P20 · opponents P21 + P24 · 7 supporting frames'},
    {time:20.08,type:'POSSESSION CHANGE',confidence:.85,evidence:'Team A → Team B · nearest P21 · stable for 17 frames'},
  ]},
];

const state = {
  time: 0, speed: 2, playing: false, timer: null, cursor: 0, score: [0,0],
  mode: 'casual', selectedInsight: null, compile: null, compiling: false,
  programs: [], insights: [], processed: [], language:'en', overlay:false, demo:false, page:'home', view:'vision', realScene:'pexels-15448993',
  realCursor:0, realLastTime:0, replayUntil:null,
};

const isLocalPreview = ['localhost', '127.0.0.1'].includes(window.location.hostname);
const API_BASE = import.meta.env.VITE_API_BASE_URL || (isLocalPreview ? 'http://127.0.0.1:8000' : '');

function fmt(sec) { const whole=Math.floor(sec);return `${String(Math.floor(whole/60)).padStart(2,'0')}:${String(whole%60).padStart(2,'0')}`; }
function team(id) { return id === 'east' ? MATCH.home : MATCH.away; }
function esc(s='') { return String(s).replace(/[&<>'"]/g, c=>({'&':'&amp;','<':'&lt;','>':'&gt;',"'":'&#39;','"':'&quot;'}[c])); }
function region(e) { return e.x == null ? '—' : e.x >= 66.7 ? 'Attacking third' : e.x <= 33.3 ? 'Defensive third' : 'Middle third'; }

function compileIntent(text) {
  const lower = text.toLowerCase();
  const unsupported = /left.?back|space behind|formation|offside line/.test(lower);
  if (unsupported) return { status:'unsupported', reason:'This request needs continuous player-position data, which is not present in the observable event stream.', suggestion:templates[0] };
  const teamId = lower.includes('north') ? 'north' : 'east';
  if (/recover|wins possession/.test(lower) && /shot/.test(lower)) return {
    status:'valid', name:'Recovery → shot sequence', kind:'sequence', team:teamId, gap:15,
    summary:`${team(teamId).name} recovers possession, then shoots within 15 seconds`,
    json:{operator:'ORDERED_SEQUENCE',team_id:teamId,events:['POSSESSION_RECOVERY','SHOT'],sequence_max_gap_seconds:15}
  };
  if (/shot/.test(lower) && /player 7/.test(lower)) return {
    status:'valid', name:'Player 7 shot watch', kind:'player_shot', player:'Player 7',
    summary:'Trigger on every shot involving Player 7',
    json:{operator:'EVENT_MATCH',event_type:'SHOT',player_id:'player_7'}
  };
  if (/shot/.test(lower) && /(three|3|at least)/.test(lower)) return {
    status:'valid', name:'Shot surge', kind:'count', eventType:'SHOT', threshold:3, window:300,
    summary:'3 shots by either team inside a rolling 5-minute window',
    json:{operator:'COUNT_THRESHOLD',filter:{event_type:'SHOT'},window_seconds:300,threshold:3}
  };
  if (/recover|wins possession/.test(lower)) return {
    status:'valid', name:'High recoveries', kind:'count', eventType:'POSSESSION_RECOVERY', team:teamId, region:'ATTACKING_THIRD', threshold:3, window:300,
    summary:`${team(teamId).name}: 3 attacking-third recoveries inside 5 minutes`,
    json:{operator:'COUNT_THRESHOLD',filter:{event_type:'POSSESSION_RECOVERY',team_id:teamId,pitch_region:'ATTACKING_THIRD'},window_seconds:300,threshold:3}
  };
  return { status:'clarify', reason:'I could not map that request to the supported event fields.', suggestion:templates[1] };
}

function compileRealIntent(text) {
  const lower=text.toLowerCase();
  if (/tempo|passage|involvement|story|节奏|片段/.test(lower)) return {
    status:'valid', name:'High-tempo passage director', kind:'real_story', window:6, contactThreshold:2, movementThreshold:1,
    summary:'Select a passage containing rapid ball travel and repeated player involvement', provider:'real-cv-deterministic-adapter',
    json:{operator:'COMPOSITE_WINDOW',window_seconds:6,conditions:[{event_type:'BALL_CONTACT_CANDIDATE',minimum:2},{event_type:'RAPID_BALL_MOVEMENT_CANDIDATE',minimum:1}],output:'DIRECTOR_MOMENT',source:'licensed_cv_run'}
  };
  if (/rapid|fast|movement|移动|快速/.test(lower)) return {
    status:'valid', name:'Rapid ball movement', kind:'real_event', eventType:'RAPID_BALL_MOVEMENT_CANDIDATE',
    summary:'Trigger on every evidence-linked rapid ball-movement candidate', provider:'real-cv-deterministic-adapter',
    json:{operator:'EVENT_MATCH',filter:{event_type:'RAPID_BALL_MOVEMENT_CANDIDATE',status:'candidate'},source:'licensed_cv_run'}
  };
  if (/confidence|80|置信/.test(lower)) return {
    status:'valid', name:'High-confidence ball contact', kind:'real_confidence', eventType:'BALL_CONTACT_CANDIDATE', threshold:.8,
    summary:'Ball-contact candidate with confidence ≥ 80%', provider:'real-cv-deterministic-adapter',
    json:{operator:'CONFIDENCE_THRESHOLD',filter:{event_type:'BALL_CONTACT_CANDIDATE'},threshold:.8,source:'licensed_cv_run'}
  };
  return {
    status:'valid', name:'Repeated ball involvement', kind:'real_count', eventType:'BALL_CONTACT_CANDIDATE', threshold:2, window:10,
    summary:'2 ball-contact candidates inside a rolling 10-second window', provider:'real-cv-deterministic-adapter',
    json:{operator:'COUNT_THRESHOLD',filter:{event_type:'BALL_CONTACT_CANDIDATE',status:'candidate'},window_seconds:10,threshold:2,source:'licensed_cv_run'}
  };
}

function normalizeApiProgram(payload, original) {
  if (payload.status !== 'valid') return {
    status: payload.status === 'unsupported' ? 'unsupported' : 'clarify',
    reason: payload.message,
    suggestion: payload.suggested_instruction,
    original,
    provider: payload.provider,
  };
  const p = payload.program;
  const base = {status:'valid', name:p.name, original, json:p, provider:payload.provider};
  if (p.operator === 'ORDERED_SEQUENCE') return {...base, kind:'sequence', team:p.sequence[0].team_id, gap:p.sequence_max_gap_seconds, summary:`${team(p.sequence[0].team_id).name} recovers possession, then shoots within ${p.sequence_max_gap_seconds} seconds`};
  if (p.operator === 'EVENT_MATCH') return {...base, kind:'player_shot', player:'Player 7', summary:'Trigger on every shot involving Player 7'};
  return {...base, kind:'count', eventType:p.filter.event_type, team:p.filter.team_id, region:p.filter.pitch_region, threshold:p.threshold, window:p.window_seconds, summary:p.filter.event_type==='SHOT' ? `${p.threshold} shots by either team inside a rolling ${p.window_seconds/60}-minute window` : `${team(p.filter.team_id).name}: ${p.threshold} attacking-third recoveries inside ${p.window_seconds/60} minutes`};
}

async function compileWithProvider(text) {
  if (state.view === 'vision') return {...compileRealIntent(text), original:text};
  if (!API_BASE) return {...compileIntent(text), original:text, provider:'browser-safe-fallback'};
  const controller = new AbortController();
  const timeout = setTimeout(()=>controller.abort(), 2500);
  try {
    const response = await fetch(`${API_BASE}/api/director/compile`, {
      method:'POST', headers:{'Content-Type':'application/json'},
      body:JSON.stringify({instruction:text, match_id:'match_demo_01'}), signal:controller.signal,
    });
    if (!response.ok) throw new Error(`API ${response.status}`);
    return normalizeApiProgram(await response.json(), text);
  } catch (_) {
    return {...compileIntent(text), original:text, provider:'browser-safe-fallback'};
  } finally { clearTimeout(timeout); }
}

function defaultRealProgram(){const c=compileRealIntent(realTemplates[0]);return {...c,id:'real_ball_contact_monitor',version:1,active:true,lastTrigger:null,conditionActive:false}}

function resetRealRun() {
  state.time=0; state.realCursor=0; state.realLastTime=0; state.processed=[]; state.insights=[]; state.selectedInsight=null;
  state.programs.forEach(p=>{p.lastTrigger=null;p.conditionActive=false});
}

function emitRealInsight(p,evidence,values) {
  const title=p.kind==='real_story'?'High-tempo passage selected':p.kind==='real_event'?'Rapid ball movement detected':p.kind==='real_confidence'?'High-confidence ball contact':'Repeated ball involvement detected';
  const casual=p.kind==='real_story'
    ? `Director selected this passage because rapid ball travel was followed by repeated player involvement. It is ready as a replay or commentary cue.`
    : p.kind==='real_event'
    ? `The tracked ball moved rapidly across ${values.frames} frames. The moment is linked directly to the CV run.`
    : p.kind==='real_confidence'
      ? `A player-ball proximity pattern crossed the ${Math.round(p.threshold*100)}% confidence threshold.`
      : `${values.count} ball-contact candidates occurred inside ${values.window} seconds. This is a candidate pattern, not asserted ground truth.`;
  const analyst=p.kind==='real_story'
    ? `COMPOSITE_WINDOW: contacts=${values.contacts}, rapid_movements=${values.movements}, window=${values.window}s. Semantic label is evidence-bounded.`
    : p.kind==='real_event'
    ? `RAPID_BALL_MOVEMENT_CANDIDATE: displacement=${values.displacement}, threshold=${values.threshold}, frames=${values.frames}.`
    : p.kind==='real_confidence'
      ? `BALL_CONTACT_CANDIDATE: confidence=${Math.round(values.confidence*100)}%, threshold=${Math.round(p.threshold*100)}%.`
      : `COUNT(BALL_CONTACT_CANDIDATE)=${values.count} in rolling ${values.window}s; threshold=${p.threshold}.`;
  const clipStart=Math.max(0,evidence[0].time-1),clipEnd=Math.min(18,evidence[evidence.length-1].time+2);
  state.insights.unshift({id:`real_ins_${evidence[evidence.length-1].id}`,time:state.time,programId:p.id,title,casual,analyst,evidence,values,clipStart,clipEnd,verified:true,candidate:true,directorMoment:p.kind==='real_story'});
  state.selectedInsight=state.insights[0].id;
}

function evaluateReal(event) {
  state.programs.filter(p=>p.active).forEach(p=>{
    if(p.kind==='real_story'){
      const evidence=state.processed.filter(item=>item.time>=event.time-p.window);
      const contacts=evidence.filter(item=>item.type==='BALL_CONTACT_CANDIDATE').length;
      const movements=evidence.filter(item=>item.type==='RAPID_BALL_MOVEMENT_CANDIDATE').length;
      if(contacts>=p.contactThreshold&&movements>=p.movementThreshold&&!p.conditionActive){p.conditionActive=true;emitRealInsight(p,evidence,{contacts,movements,window:p.window})}
      if(contacts<p.contactThreshold||movements<p.movementThreshold)p.conditionActive=false;
    }
    if(p.kind==='real_event'&&event.type===p.eventType) emitRealInsight(p,[event],{frames:event.evidence.end_frame-event.evidence.start_frame,displacement:event.evidence.normalized_displacement,threshold:event.evidence.threshold});
    if(p.kind==='real_confidence'&&event.type===p.eventType&&event.confidence>=p.threshold) emitRealInsight(p,[event],{confidence:event.confidence,threshold:p.threshold});
    if(p.kind==='real_count'){
      const evidence=state.processed.filter(item=>item.type===p.eventType&&item.time>=event.time-p.window);
      if(evidence.length>=p.threshold&&!p.conditionActive){p.conditionActive=true;emitRealInsight(p,evidence,{count:evidence.length,window:p.window})}
      if(evidence.length<p.threshold)p.conditionActive=false;
    }
  });
}

function processRealUntil(currentTime) {
  let changed=false;
  if(state.replayUntil!==null){if(currentTime<=state.replayUntil)return false;state.replayUntil=null;state.realLastTime=currentTime;return false}
  if(currentTime+.3<state.realLastTime){resetRealRun();changed=true}
  state.time=currentTime;state.realLastTime=currentTime;
  while(state.realCursor<realEvents.length&&realEvents[state.realCursor].time<=currentTime+.05){const event=realEvents[state.realCursor++];state.processed.push(event);evaluateReal(event);changed=true}
  return changed;
}

function matchesFilter(e,p) {
  if (p.eventType && e.type !== p.eventType) return false;
  if (p.team && e.team !== p.team) return false;
  if (p.player && e.player !== p.player) return false;
  if (p.region === 'ATTACKING_THIRD' && !(e.x >= 66.7)) return false;
  return true;
}

function emitInsight(p, evidence, values) {
  const last = p.lastTrigger || -999;
  if (state.time-last < 35) return;
  p.lastTrigger = state.time;
  const subject = p.team ? team(p.team).name : (p.player || 'Both teams');
  let title = p.kind === 'sequence' ? 'Rapid transition detected' : p.kind === 'player_shot' ? `${p.player} takes a shot` : p.eventType === 'SHOT' ? 'The match is opening up' : 'High press is producing turnovers';
  let casual = p.kind === 'sequence' ? `${subject} turned a regain into a shot almost immediately — a sign their counter-press is creating danger.` : p.kind === 'player_shot' ? `${p.player} found a shooting window. This is exactly the moment you asked to follow.` : p.eventType === 'SHOT' ? `Three attempts arrived in a short spell. The game has shifted into a more open, end-to-end phase.` : `${subject} has won the ball high three times in five minutes. Their pressure is now disrupting the opposition build-up.`;
  let analyst = p.kind === 'sequence' ? `${subject}: recovery-to-shot transition completed in ${values.gap}s (limit ${p.gap}s).` : p.kind === 'player_shot' ? `${p.player}: SHOT at (${evidence[0].x}, ${evidence[0].y}), outcome=${evidence[0].outcome}.` : `${values.count} qualifying ${p.eventType.toLowerCase().replaceAll('_',' ')} events in ${p.window}s; threshold=${p.threshold}.`;
  state.insights.unshift({ id:`ins_${state.insights.length+1}`, time:state.time, programId:p.id, title, casual, analyst, evidence, values, verified:true });
  state.selectedInsight = state.insights[0].id;
}

function evaluate(e) {
  state.programs.filter(p=>p.active).forEach(p=>{
    if (p.kind === 'player_shot' && matchesFilter(e,p)) emitInsight(p,[e],{event:e.type,outcome:e.outcome});
    if (p.kind === 'count') {
      const evidence = state.processed.filter(x=>x.time >= state.time-p.window && matchesFilter(x,p));
      if (evidence.length >= p.threshold && !p.conditionActive) { p.conditionActive=true; emitInsight(p,evidence,{count:evidence.length,window:p.window}); }
      if (evidence.length < p.threshold) p.conditionActive=false;
    }
    if (p.kind === 'sequence' && e.type === 'SHOT' && e.team === p.team) {
      const prior = [...state.processed].reverse().find(x=>x.team===p.team && x.type==='POSSESSION_RECOVERY' && e.time-x.time<=p.gap);
      if (prior) emitInsight(p,[prior,e],{gap:e.time-prior.time});
    }
  });
}

function processUntil() {
  while (state.cursor < events.length && events[state.cursor].time <= state.time) {
    const e = events[state.cursor++]; state.processed.push(e);
    if (e.type==='GOAL') state.score[e.team==='east'?0:1]++;
    evaluate(e);
  }
}

function reset() { state.time=0; state.cursor=0; state.score=[0,0]; state.processed=[]; state.insights=[]; state.selectedInsight=null; state.programs.forEach(p=>{p.lastTrigger=null;p.conditionActive=false}); render(); }
function tick() { state.time += state.speed; processUntil(); if(state.time>=450){state.playing=false;state.demo=false;clearInterval(state.timer)} render(); }
function togglePlay() { state.playing=!state.playing; clearInterval(state.timer); if(state.playing) state.timer=setInterval(tick,500); render(); }

function eventLabel(e) { return e.type.replaceAll('_',' ').toLowerCase(); }
function renderPitch() {
  const recent = state.processed.slice(-7);
  return `<div class="pitch" aria-label="Text alternative: event locations on a football pitch">
    <div class="half"></div><div class="circle"></div><div class="box left"></div><div class="box right"></div>
    ${recent.filter(e=>e.x!=null).map((e,i)=>`<button class="event-dot ${e.team}" style="left:${e.x}%;top:${e.y}%;--delay:${i}" title="${esc(e.player)} · ${eventLabel(e)}" aria-label="${esc(e.player)} ${eventLabel(e)} at ${fmt(e.time)}"><span>${e.type==='SHOT'?'↗':e.type==='GOAL'?'★':'•'}</span></button>`).join('')}
  </div>`;
}

function renderVision() {
  const moment=state.insights.find(item=>item.directorMoment);
  return `<div class="vision-stage real-feed" aria-label="Real licensed football video processed by YOLO and ByteTrack">
    <video id="studio-real-video" src="/licensed/pexels-15448993/tracked.mp4" autoplay muted loop playsinline preload="auto"></video>
    <div class="vision-vignette"></div>
    <div class="vision-hud top-left"><span><i></i> DIRECTOR IS WATCHING</span><b>REAL VIDEO</b></div>
    <div class="vision-hud top-right"><b>LIVE ANALYSIS</b><b>LICENSED FOOTAGE</b></div>
    <div class="vision-event"><span>${state.processed.length} MOMENT SIGNALS SEEN</span><b>${state.insights.length?'REPLAY READY':'LOOKING FOR YOUR BRIEF'}</b></div>
    ${moment?`<div class="moment-callout"><span>✓ MOMENT FOUND</span><strong>Worth a replay</strong><p>Fast ball movement + repeated player involvement</p><button id="replay-moment">PLAY THE MOMENT ↺</button></div>`:''}
    <div class="vision-disclosure">REAL MATCH FOOTAGE · 3,183 PERSON DETECTIONS · 795 BALL FRAMES · LUIS QUINTERO / PEXELS</div>
  </div>`;
}

function sourcePipeline() {
  return `<div class="source-pipeline">
    <div><span>01</span><b>WATCHES THE VIDEO</b><small>Real licensed match footage</small></div><i>→</i>
    <div><span>02</span><b>UNDERSTANDS MOVEMENT</b><small>Tracks players and ball</small></div><i>→</i>
    <div class="live"><span>03</span><b>FINDS THE STORY</b><small>Your brief runs live</small></div><i>→</i>
    <div><span>04</span><b>PREPARES THE REPLAY</b><small>Clip + commentary + proof</small></div>
  </div>`;
}

function programCard(p) { return `<article class="program-card ${p.active?'active':''}">
  <div class="program-top"><span class="status-dot"></span><div><strong>${esc(p.name)}</strong><small>v${p.version} · ${p.active?'Monitoring live':'Paused'}</small></div><button class="icon-btn toggle-program" data-id="${p.id}">${p.active?'Ⅱ':'▶'}</button></div>
  <p>${esc(p.summary)}</p><div class="program-actions"><button class="text-btn inspect-program" data-id="${p.id}">View program</button><button class="text-btn delete-program" data-id="${p.id}">Delete</button></div>
 </article>`; }

function translatedInsight(i) {
  if(i.candidate&&state.language==='zh') return i.directorMoment
    ? {title:'已选中高节奏比赛片段',text:'导演系统发现快速球移动后连续出现球员参与，因此将这一段选为可用于回放和解说的关键片段。'}
    : {title:i.title==='Repeated ball involvement detected'?'检测到连续触球候选':'检测到快速球移动',text:i.casual};
  if(i.candidate&&state.language==='es') return i.directorMoment
    ? {title:'Pasaje de alta intensidad seleccionado',text:'Director seleccionó este tramo porque el movimiento rápido del balón fue seguido por participación repetida de jugadores.'}
    : {title:i.title==='Repeated ball involvement detected'?'Participación repetida del balón detectada':'Movimiento rápido del balón detectado',text:i.casual};
  if(state.language==='zh') return {title:i.title==='High press is producing turnovers'?'高位压迫正在制造转换':i.title==='Rapid transition detected'?'发现快速攻防转换':i.title.includes('takes a shot')?'关键球员完成射门':'比赛正在变得开放', text:i.title==='High press is producing turnovers'?'东部联队在五分钟内三次于前场夺回球权，他们的压迫已经开始破坏对手的组织。':i.title==='Rapid transition detected'?'夺回球权后立刻形成射门——反抢正在持续制造威胁。':i.casual};
  if(state.language==='es') return {title:i.title==='High press is producing turnovers'?'La presión alta genera transiciones':i.title==='Rapid transition detected'?'Transición rápida detectada':i.title.includes('takes a shot')?'Disparo del jugador clave':'El partido se abre', text:i.title==='High press is producing turnovers'?'East United recuperó el balón tres veces en campo rival. Su presión ya está alterando la salida del oponente.':i.title==='Rapid transition detected'?'La recuperación se convirtió inmediatamente en disparo: la contrapresión está creando peligro.':i.casual};
  return {title:i.title,text:state.mode==='casual'?i.casual:i.analyst};
}

function insightCard(i) { const copy=translatedInsight(i); return `<button class="insight-card ${state.selectedInsight===i.id?'selected':''}" data-id="${i.id}">
  <span class="insight-time">${fmt(i.time)}</span><div><strong>${esc(copy.title)}</strong><p>${esc(copy.text)}</p><small><span class="verified">✓ ${i.candidate?'Evidence-linked candidate':'Verified'}</span> · ${i.evidence.length} source event${i.evidence.length===1?'':'s'}</small></div>
 </button>`; }

function evidencePanel() {
  const i=state.insights.find(x=>x.id===state.selectedInsight);
  if(!i) return `<div class="empty-evidence"><span>◎</span><h3>Director is watching</h3><p>When a moment matches your brief, the replay and explanation will appear here automatically.</p></div>`;
  const p=state.programs.find(x=>x.id===i.programId);
  return `<div class="evidence-head human-result"><div><span class="eyebrow">DIRECTOR FOUND A MOMENT</span><h3>${esc(translatedInsight(i).title)}</h3><p>${esc(translatedInsight(i).text)}</p></div></div>
  ${i.directorMoment?`<div class="director-treatment"><span>READY TO USE</span><strong>A ${Math.round(i.clipEnd-i.clipStart)}-second replay with commentary</strong><p>Selected from ${i.clipStart.toFixed(2)}s to ${i.clipEnd.toFixed(2)}s</p><button id="replay-moment">▶ PLAY KEY MOMENT</button></div>`:''}
  <button class="broadcast-btn" id="show-broadcast">CREATE LIVE GRAPHIC <span>↗</span></button>
  <details class="technical-proof"><summary>Why did Director choose this?</summary><p>${esc(p?.summary||'')}</p><code>${esc(JSON.stringify(i.values))}</code><div class="evidence-events">${i.evidence.map(e=>`<div><span>${e.real?`${e.time.toFixed(2)}s`:fmt(e.time)}</span><strong>${eventLabel(e)}</strong><small>${e.real?esc(`${e.evidenceText} · confidence ${Math.round(e.confidence*100)}%`):`${esc(e.player)} · ${region(e)} · (${e.x??'—'}, ${e.y??'—'})`}</small></div>`).join('')}</div></details>`;
}

function demoStep(){return state.view==='vision'?(state.time<1.5?0:state.time<2.45?1:state.insights.length?3:2):(state.time<64?0:state.time<151?1:state.time<232?2:3)}
function demoRail(){const steps=['Brief the AI','Watch the match','Detect the pattern','Explain the moment'];return `<div class="demo-rail"><span>LIVE DEMO</span>${steps.map((s,i)=>`<div class="${demoStep()>=i?'done':''} ${demoStep()===i?'now':''}"><i>${demoStep()>i?'✓':i+1}</i>${s}</div>`).join('')}<button id="exit-demo">EXIT</button></div>`}
function broadcastOverlay(){const i=state.insights.find(x=>x.id===state.selectedInsight)||state.insights[0];if(!state.overlay||!i)return'';const c=translatedInsight(i);return `<div class="broadcast" role="dialog" aria-label="Broadcast overlay preview"><button id="close-broadcast">×</button><div class="broadcast-top"><span><i></i> DIRECTOR LIVE</span><b>${i.candidate?'REAL CV FEED':`${MATCH.home.short} ${state.score[0]} — ${state.score[1]} ${MATCH.away.short}`}</b><time>${fmt(state.time)}</time></div><div class="broadcast-stage"><span class="broadcast-kicker">${i.directorMoment?'AUTO-SELECTED REPLAY':'AI MATCH INTELLIGENCE'}</span><h2>${esc(c.title)}</h2><p>${esc(c.text)}</p><div class="broadcast-proof"><span>✓ ${i.candidate?'EVIDENCE-LINKED':'VERIFIED'}</span><b>${i.evidence.length} EVENT${i.evidence.length===1?'':'S'} ANALYSED</b><em>DIRECTOR/OS</em></div></div><div class="broadcast-caption">READY FOR LIVE PRODUCTION · 16:9 SAFE AREA · ${state.language.toUpperCase()}</div></div>`}

function landingPage(){return `
 <div class="landing">
  <header class="landing-nav"><a class="brand" href="#"><span class="brand-mark"><i></i><i></i><i></i></span><span>DIRECTOR<span class="brand-muted">/OS</span></span></a><div><span class="prototype-pill">LIVE PROTOTYPE</span><button id="open-studio" class="nav-studio">OPEN STUDIO <span>↗</span></button></div></header>
  <main class="landing-main">
   <section class="landing-hero">
    <div class="landing-copy"><span class="kicker">AN AI DIRECTOR FOR EVERY VIEWER</span><h1>Tell us what matters.<br><em>We find the moment.</em></h1><p>Director watches a real football video, finds the passage that matches your request, and prepares a replay with commentary—automatically.</p><div class="landing-actions"><button id="run-demo" class="primary-cta"><span>▶</span> SEE A REAL EXAMPLE</button><button id="open-real-lab" class="secondary-cta">HOW THE VIDEO WAS ANALYSED →</button></div><small>REAL LICENSED VIDEO · AUTOMATIC MOMENT SELECTION · EXPLAINABLE RESULTS</small></div>
    <div class="story-card" aria-label="How Director finds a replay-worthy moment"><div class="story-head"><span><i></i> ONE SIMPLE BRIEF</span><b>REAL VIDEO</b></div><div class="fan-question"><span>YOU ASK</span><p>“Find a high-tempo passage worth replaying.”</p></div><div class="story-flow"><div><i>1</i><span>Watches the video</span></div><b>→</b><div><i>2</i><span>Finds the pattern</span></div><b>→</b><div class="active"><i>3</i><span>Prepares the replay</span></div></div><div class="answer-card"><span class="verified-mark">✓ MOMENT FOUND</span><h2>Here is the replay.</h2><p>Rapid ball movement was followed by repeated player involvement.</p><div class="evidence-dots"><span>6-second clip</span><span>Commentary ready</span><span>Evidence attached</span></div></div></div>
   </section>
   <section class="value-strip"><span>YOUR BRIEF</span><b>→</b><span>DIRECTOR WATCHES</span><b>→</b><span>KEY MOMENT FOUND</span><b>→</b><span>REPLAY READY</span></section>
   <section class="landing-proof"><div><span class="proof-num">01</span><h3>Say what you want</h3><p>Ask for a high-tempo passage, rapid movement, or another supported pattern.</p></div><div><span class="proof-num">02</span><h3>Get the moment</h3><p>Director selects the exact clip and explains in plain language what it observed.</p></div><div><span class="proof-num">03</span><h3>Use it instantly</h3><p>Replay it, change language, or turn it into a live broadcast graphic.</p></div></section>
   <section class="landing-final"><span>BUILT FOR THE MICROSOFT × PREMIER LEAGUE HACKATHON</span><h2>Football intelligence should feel personal.<br><em>And prove every word.</em></h2><button id="run-demo" class="primary-cta"><span>▶</span> SEE IT IN ACTION</button></section>
  </main><footer class="landing-footer"><span>DIRECTOR/OS · AGENTIC MATCH INTELLIGENCE</span><span>REAL LICENSED VIDEO · EVIDENCE-LINKED OUTPUT</span></footer>
 </div>`}

function realLabPage(){const selected=REAL_SCENES[0];return `
 <div class="real-lab">
  <header><button id="back-home" class="brand"><span class="brand-mark"><i></i><i></i><i></i></span><span>DIRECTOR<span class="brand-muted">/OS</span></span></button><nav><span class="lab-pill"><i></i> REAL VISION LAB</span><button id="open-studio" class="nav-studio">OPEN LIVE STUDIO ↗</button></nav></header>
  <main class="lab-main">
   <section class="lab-head"><div><span class="kicker">REAL FRAMES · REAL TRACKS · EXPLAINABLE CANDIDATES</span><h1>Real footage.<br><em>Evidence on every frame.</em></h1></div><p>This public scene runs genuine YOLO + ByteTrack on Pexels-licensed footage. All 10 timestamped candidates are now replayed into the same rule engine used by the live studio.</p></section>
   <section class="scene-tabs"><div class="scene-tab on"><span>${selected.sequence}</span><strong>${selected.title}</strong><small>${selected.events} public candidates · playable</small></div><div class="run-route"><span>01 REAL VIDEO</span><b>→</b><span>02 10 CV EVENTS</span><b>→</b><span>03 RULE ENGINE</span><b>→</b><span>04 EXPLAINED OUTPUT</span></div></section>
   <section class="lab-grid">
    <div class="real-player panel"><div class="panel-label"><span>01</span><strong>${selected.title.toUpperCase()}</strong><small>${selected.licensed?'Pexels licensed public asset · Luis Quintero':`${selected.sequence} · authorized local research asset`}</small></div><div class="video-shell"><video id="real-video" controls playsinline preload="metadata" src="${selected.video}"></video><div class="video-missing" id="video-missing"><span>LOCAL ASSET REQUIRED</span><strong>Research footage is intentionally excluded from the public repository.</strong><p>Select “Licensed match tracking” for the public playable scene.</p></div></div><div class="real-timeline">${selected.moments.map(moment=>`<button class="moment-jump" data-time="${moment.time}"><i style="left:${moment.time/(selected.duration||30)*100}%"></i><span>${moment.time.toFixed(2)}s</span><strong>${moment.type}</strong></button>`).join('')}</div></div>
    <aside class="lab-proof panel"><div class="panel-label"><span>02</span><strong>RUN EVIDENCE</strong><small>Not model theatre</small></div><div class="lab-story"><span>DIRECTOR STORY</span><h2>${selected.story}</h2><p id="live-proof">Play the clip or select a detected moment.</p></div><div class="run-metrics"><div><span>${selected.licensed?'BALL COVERAGE':'BALL TRACK'}</span><strong>${selected.ball}</strong></div><div><span>${selected.licensed?'PERSON BOXES':'TEAM CLUSTERS'}</span><strong>${selected.tracks}</strong></div><div><span>CANDIDATES</span><strong>${selected.events}</strong></div></div><div class="moment-list">${selected.moments.map((moment,index)=>`<button class="proof-moment" data-index="${index}" data-time="${moment.time}"><time>${moment.time.toFixed(2)}s</time><div><strong>${moment.type}</strong><p>${moment.evidence}</p></div><span>${Math.round(moment.confidence*100)}%</span></button>`).join('')}</div><div class="candidate-note">CANDIDATE ≠ GROUND TRUTH<br><span>Low-confidence semantic outputs are labelled or withheld.</span></div>${selected.licensed?'<a class="asset-credit" href="https://www.pexels.com/video/football-players-kicking-the-ball-during-a-match-15448993/" target="_blank" rel="noreferrer">VIDEO: LUIS QUINTERO / PEXELS ↗</a>':''}</aside>
   </section>
  </main><footer><span>Pexels licensed public demo · complete replayable pipeline</span><span>LICENSE RECORDED · OUTPUTS LABELLED · EVIDENCE PUBLIC</span></footer>
 </div>`}

function appHtml() { const last=state.processed[state.processed.length-1]; const vision=state.view==='vision'; const availableTemplates=vision?realTemplates:templates; return `
 ${state.demo?demoRail():''}${broadcastOverlay()}
 <header><button id="back-home" class="brand"><span class="brand-mark"><i></i><i></i><i></i></span><span>DIRECTOR<span class="brand-muted">/OS</span></span></button><nav><button class="demo-btn" id="open-real-lab">VIEW CV EVIDENCE</button><button class="demo-btn" id="run-demo">▶ RUN DEMO</button><select id="language" aria-label="Commentary language"><option value="en" ${state.language==='en'?'selected':''}>EN</option><option value="zh" ${state.language==='zh'?'selected':''}>中文</option><option value="es" ${state.language==='es'?'selected':''}>ES</option></select><span class="live-pill"><i></i> ${vision?'REAL VIDEO PLAYING':'EVENT SIMULATION LIVE'}</span><div class="mode-switch"><button class="mode ${state.mode==='casual'?'on':''}" data-mode="casual">Fan view</button><button class="mode ${state.mode==='analyst'?'on':''}" data-mode="analyst">Analyst view</button></div></nav></header>
 <main>
  <section class="hero">
   <div><span class="kicker">YOUR AI MATCH DIRECTOR</span><h1>Ask once.<br><em>Get the moment.</em></h1></div>
   <p>Director is watching the real video below. When it finds a passage matching your brief, it prepares the replay and commentary for you.</p>
   <div class="hero-stat"><strong>${state.insights.length?'✓':'•'}</strong><span>${state.insights.length?'MOMENT':'WATCHING'}<br>${state.insights.length?'FOUND':'LIVE'}</span></div>
  </section>
  <section class="stage panel">
   <div class="panel-label"><span>01</span><strong>${vision?'WATCH THE MATCH':'TACTICAL SANDBOX'}</strong><div class="view-switch"><button class="view-mode ${state.view==='vision'?'on':''}" data-view="vision">REAL VIDEO</button><button class="view-mode ${state.view==='map'?'on':''}" data-view="map">TACTICAL MAP</button></div><small>${vision?'Director is analysing this video as it plays':'Optional synthetic event replay'}</small></div>
   ${vision?'<div class="scoreboard cv-scoreboard"><div class="club home"><span class="crest">▶</span><div><strong>Real football video</strong><small>LICENSED PUBLIC DEMO</small></div></div><div class="score"><b>Director is watching</b><span>FINDING THE MOMENT YOU ASKED FOR</span></div><div class="club away"><div><strong>18-second example</strong><small>AUTOMATIC REPLAY SELECTION</small></div><span class="crest blue">AI</span></div></div>':`<div class="scoreboard"><div class="club home"><span class="crest">EU</span><div><strong>${MATCH.home.name}</strong><small>HOME</small></div></div><div class="score"><b>${state.score[0]} – ${state.score[1]}</b><span>${fmt(state.time)} · DEMO MATCH</span></div><div class="club away"><div><strong>${MATCH.away.name}</strong><small>AWAY</small></div><span class="crest blue">NC</span></div></div>`}
   ${state.view==='vision'?renderVision():renderPitch()}
   ${sourcePipeline()}
   ${vision?`<div class="cv-actions"><button id="toggle-cv-video">Ⅱ</button><span><b>${state.insights.length?'KEY MOMENT FOUND':last?'DIRECTOR NOTICED A SIGNAL':'DIRECTOR IS WATCHING'}</b> ${state.insights.length?'A replay matching your brief is ready below.':last?'It is combining movement over time before choosing a replay.':'Keep watching—the result will appear automatically.'}</span><button id="open-real-lab">SEE TECHNICAL PROOF →</button></div>`:`<div class="transport"><button id="reset">↺</button><button id="play" class="play">${state.playing?'Ⅱ':'▶'}</button><div class="timeline"><i style="width:${state.time/4.5}%"></i>${events.map(e=>`<span style="left:${e.time/4.5}%"></span>`).join('')}</div><select id="speed"><option ${state.speed===1?'selected':''}>1</option><option ${state.speed===2?'selected':''}>2</option><option ${state.speed===4?'selected':''}>4</option><option value="8" ${state.speed===8?'selected':''}>8</option></select><span>×</span></div><div class="ticker"><span>LATEST EVENT</span><strong>${last?`${fmt(last.time)} · ${team(last.team).short} · ${eventLabel(last)} · ${last.player}`:'Waiting for kick-off'}</strong></div>`}
  </section>
  <section class="director panel">
   <div class="panel-label"><span>02</span><strong>YOUR BRIEF</strong><small>Tell Director what is worth finding</small></div>
   <div class="director-intro"><div><h2>What moment do you want?</h2><p>Write it normally. Director will watch the video and bring back the matching passage.</p></div><span class="engine"><i></i> WATCHING</span></div>
   <form id="director-form"><div class="prompt-shell"><span class="prompt-mark">↳</span><textarea id="intent" rows="3" placeholder="e.g. Alert me when two ball contacts occur…">${esc(state.compile?.original||availableTemplates[0])}</textarea><button type="submit" ${state.compiling?'disabled':''}>${state.compiling?'<span class="spinner"></span> VALIDATING':'CREATE MONITOR <span>→</span>'}</button></div><div class="example-row"><span>Try:</span>${availableTemplates.slice(1,4).map((t,i)=>`<button type="button" class="example-chip" data-text="${esc(t)}">${vision?['Rapid movement','80% confidence'][i]:['Player watch','Fast transitions','Shot surge'][i]}</button>`).join('')}<small>⌘ ENTER</small></div></form>
   ${state.compile?compileCard(state.compile):''}
   <div class="subhead"><h3>What Director is looking for</h3><span>${state.programs.filter(p=>p.active).length?'ACTIVE':'NOT STARTED'}</span></div>
   <div class="program-list">${state.programs.length?state.programs.map(programCard).join(''):'<div class="empty-small">Compile a direction to start monitoring the match.</div>'}</div>
  </section>
  <section class="feed panel"><div class="panel-label"><span>03</span><strong>DIRECTOR'S PICKS</strong><small>The moments matching your brief</small></div><div class="section-title"><div><h2>${state.insights.length?'A moment is ready.':'Watching for your moment…'}</h2><p>${state.insights.length?'Select it to replay, explain or publish.':'The result will appear automatically—no button needed.'}</p></div><span class="count-badge">${String(state.insights.length).padStart(2,'0')}</span></div><div class="feed-list">${state.insights.length?state.insights.map(insightCard).join(''):'<div class="empty-small tall"><span>◎</span><strong>Director is watching</strong><p>Keep the video playing. A matching moment will appear here.</p></div>'}</div></section>
  <aside class="evidence panel"><div class="panel-label"><span>04</span><strong>USE THIS MOMENT</strong><small>Replay, explain or publish</small></div>${evidencePanel()}</aside>
 </main><footer><span>Powered by deterministic event reasoning</span><span>${vision?'REAL LICENSED VIDEO · REAL INFERENCE · CANDIDATES LABELLED':'SYNTHETIC EVENT DATA · EXPLAINABLE BY DESIGN'}</span></footer>`; }

function compileCard(c) {
 if(c.status!=='valid') return `<div class="compile-card error"><span>${c.status==='unsupported'?'Unsupported with current data':'Needs clarification'}</span><p>${esc(c.reason)}</p><button class="use-suggestion" data-text="${esc(c.suggestion)}">Use supported alternative</button></div>`;
 return `<div class="compile-card"><div class="compile-check">✓</div><div class="compile-copy"><span>READY TO MONITOR</span><strong>${esc(c.name)}</strong><p>${esc(c.summary)}</p><details><summary>View how this works</summary><pre>${esc(JSON.stringify(c.json,null,2))}</pre></details></div><button id="activate">START MONITORING <span>→</span></button></div>`;
}

function enterRealStudio(demo=false){clearInterval(state.timer);state.page='studio';state.view='vision';state.demo=demo;state.playing=false;state.compile=null;state.programs=[defaultRealProgram()];resetRealRun();render();window.scrollTo(0,0)}
function switchDataView(view){clearInterval(state.timer);state.view=view;state.demo=false;state.compile=null;if(view==='vision'){state.programs=[defaultRealProgram()];resetRealRun()}else{state.programs=[];state.time=0;state.cursor=0;state.score=[0,0];state.processed=[];state.insights=[];state.selectedInsight=null}render()}

function bind() {
 document.querySelector('#play')?.addEventListener('click',togglePlay);
 document.querySelector('#reset')?.addEventListener('click',reset);
 document.querySelector('#speed')?.addEventListener('change',e=>{state.speed=Number(e.target.value)});
 document.querySelector('#toggle-cv-video')?.addEventListener('click',e=>{const video=document.querySelector('#studio-real-video');if(!video)return;if(video.paused){video.play().catch(()=>{});e.currentTarget.textContent='Ⅱ'}else{video.pause();e.currentTarget.textContent='▶'}});
 document.querySelectorAll('.view-mode').forEach(b=>b.addEventListener('click',()=>switchDataView(b.dataset.view)));
 document.querySelectorAll('.mode').forEach(b=>b.addEventListener('click',()=>{state.mode=b.dataset.mode;render()}));
 document.querySelector('#director-form')?.addEventListener('submit',async e=>{e.preventDefault();const text=document.querySelector('#intent').value.trim();state.compiling=true;state.compile={original:text};render();state.compile=await compileWithProvider(text);state.compiling=false;render()});
 document.querySelector('#intent')?.addEventListener('keydown',e=>{if((e.metaKey||e.ctrlKey)&&e.key==='Enter')document.querySelector('#director-form').requestSubmit()});
 document.querySelector('#activate')?.addEventListener('click',()=>{const c=state.compile;state.programs.unshift({...c,id:`prog_${Date.now()}`,version:1,active:true,lastTrigger:null,conditionActive:false});state.compile=null;render()});
 document.querySelectorAll('.toggle-program').forEach(b=>b.addEventListener('click',()=>{const p=state.programs.find(x=>x.id===b.dataset.id);p.active=!p.active;render()}));
 document.querySelectorAll('.delete-program').forEach(b=>b.addEventListener('click',()=>{state.programs=state.programs.filter(x=>x.id!==b.dataset.id);render()}));
 document.querySelectorAll('.inspect-program').forEach(b=>b.addEventListener('click',()=>{const p=state.programs.find(x=>x.id===b.dataset.id);state.compile={...p,original:p.summary,status:'valid'};render()}));
 document.querySelectorAll('.insight-card').forEach(b=>b.addEventListener('click',()=>{state.selectedInsight=b.dataset.id;render()}));
 document.querySelectorAll('.use-suggestion').forEach(b=>b.addEventListener('click',()=>{state.compile={...(state.view==='vision'?compileRealIntent(b.dataset.text):compileIntent(b.dataset.text)),original:b.dataset.text};render()}));
 document.querySelectorAll('.example-chip').forEach(b=>b.addEventListener('click',()=>{const input=document.querySelector('#intent');input.value=b.dataset.text;input.focus()}));
 document.querySelector('#language')?.addEventListener('change',e=>{state.language=e.target.value;render()});
 document.querySelector('#show-broadcast')?.addEventListener('click',()=>{state.overlay=true;render()});
 document.querySelectorAll('#replay-moment').forEach(button=>button.addEventListener('click',()=>{const insight=state.insights.find(item=>item.id===state.selectedInsight);const video=document.querySelector('#studio-real-video');if(insight&&video){state.replayUntil=insight.clipEnd;video.currentTime=insight.clipStart;video.play().catch(()=>{})}}));
 document.querySelector('#close-broadcast')?.addEventListener('click',()=>{state.overlay=false;render()});
 document.querySelectorAll('#run-demo').forEach(b=>b.addEventListener('click',()=>enterRealStudio(true)));
 document.querySelectorAll('#open-studio').forEach(b=>b.addEventListener('click',()=>enterRealStudio(false)));
 document.querySelectorAll('#open-real-lab').forEach(b=>b.addEventListener('click',()=>{state.page='lab';state.realScene=REAL_SCENES[0].id;render();window.scrollTo(0,0)}));
 document.querySelectorAll('.scene-tab[data-scene]').forEach(b=>b.addEventListener('click',()=>{state.realScene=b.dataset.scene;render()}));
 const realVideo=document.querySelector('#real-video');
 if(realVideo){const missing=document.querySelector('#video-missing');realVideo.addEventListener('loadeddata',()=>missing?.classList.add('hidden'));realVideo.addEventListener('error',()=>missing?.classList.remove('hidden'));realVideo.addEventListener('timeupdate',()=>{const scene=REAL_SCENES.find(item=>item.id===state.realScene)||REAL_SCENES[0];const near=[...scene.moments].reverse().find(item=>item.time<=realVideo.currentTime+.15);const proof=document.querySelector('#live-proof');if(near&&proof)proof.innerHTML=`<b>${near.type}</b><br>${near.evidence} · confidence ${Math.round(near.confidence*100)}%`;});}
 const studioVideo=document.querySelector('#studio-real-video');
 if(studioVideo)studioVideo.addEventListener('timeupdate',()=>{if(processRealUntil(studioVideo.currentTime))render()});
 document.querySelectorAll('.moment-jump,.proof-moment').forEach(b=>b.addEventListener('click',()=>{if(realVideo){realVideo.currentTime=Number(b.dataset.time);realVideo.play().catch(()=>{});}}));
 document.querySelector('#back-home')?.addEventListener('click',()=>{clearInterval(state.timer);state.playing=false;state.demo=false;state.overlay=false;state.page='home';render();window.scrollTo(0,0)});
 document.querySelector('#exit-demo')?.addEventListener('click',()=>{state.demo=false;render()});
 document.addEventListener('keydown',e=>{if(e.key==='Escape'&&state.overlay){state.overlay=false;render()}},{once:true});
}
function render(){
 const priorVideo=document.querySelector('#studio-real-video');
 const priorTime=priorVideo?.currentTime||0;
 const priorPlaying=Boolean(priorVideo&&!priorVideo.paused);
 document.querySelector('#app').innerHTML=state.page==='home'?landingPage():state.page==='lab'?realLabPage():appHtml();
 bind();
 const video=document.querySelector('#studio-real-video');
 if(video){video.currentTime=priorTime;if(priorPlaying||!priorVideo)video.play().catch(()=>{});}
}
render();
