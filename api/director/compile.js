const CONDITIONS = [
  {event_type:'GOAL_AREA_ATTACK_VERIFIED',minimum:1},
  {event_type:'PLAYER_CLUSTER_CANDIDATE',minimum:1},
  {event_type:'BALL_INVOLVEMENT_CANDIDATE',minimum:1},
];

function fallback(instruction){
  const text=instruction.toLowerCase();
  if(/attack|goal|replay|进攻|球门|回放/.test(text)) return {name:'Goal-area attack director',operator:'COMPOSITE_SEQUENCE',window_seconds:4,conditions:CONDITIONS,output:'DIRECTOR_REPLAY'};
  if(/converge|players|cluster|球员|聚集/.test(text)) return {name:'Player convergence',operator:'EVENT_MATCH',filter:{event_type:'PLAYER_CLUSTER_CANDIDATE'},output:'DIRECTOR_ALERT'};
  if(/ball|involve|足球|参与/.test(text)) return {name:'Ball involvement',operator:'EVENT_MATCH',filter:{event_type:'BALL_INVOLVEMENT_CANDIDATE'},output:'DIRECTOR_ALERT'};
  return null;
}

function valid(program){
  if(!program||!['COMPOSITE_SEQUENCE','EVENT_MATCH'].includes(program.operator))return false;
  if(program.operator==='COMPOSITE_SEQUENCE')return Array.isArray(program.conditions)&&CONDITIONS.every(required=>program.conditions.some(item=>item.event_type===required.event_type));
  return ['PLAYER_CLUSTER_CANDIDATE','BALL_INVOLVEMENT_CANDIDATE'].includes(program.filter?.event_type);
}

export default async function handler(request,response){
  if(request.method!=='POST')return response.status(405).json({error:'Method not allowed'});
  const instruction=String(request.body?.instruction||'').trim();
  if(!instruction)return response.status(400).json({error:'instruction is required'});
  const endpoint=process.env.FOUNDRY_ENDPOINT;
  const apiKey=process.env.FOUNDRY_API_KEY;
  const model=process.env.FOUNDRY_MODEL;
  if(!endpoint||!apiKey||!model){
    const program=fallback(instruction);
    return response.status(200).json(program?{status:'valid',original_instruction:instruction,program,provider:'deterministic-server-fallback'}:{status:'clarification_required',original_instruction:instruction,message:'Try asking for a goal-area attack, player convergence, or ball involvement.',provider:'deterministic-server-fallback'});
  }
  const system=`You compile editorial football-video briefs into JSON. Allowed events: GOAL_AREA_ATTACK_VERIFIED, PLAYER_CLUSTER_CANDIDATE, BALL_INVOLVEMENT_CANDIDATE. Allowed operators: COMPOSITE_SEQUENCE and EVENT_MATCH. For an attack or replay request, return all three conditions and output DIRECTOR_REPLAY. Never claim a shot or goal. Return {"program":{...}} only.`;
  try{
    const foundry=await fetch(endpoint,{method:'POST',headers:{'Content-Type':'application/json','api-key':apiKey,'Authorization':`Bearer ${apiKey}`},body:JSON.stringify({model,temperature:0,messages:[{role:'system',content:system},{role:'user',content:instruction}],response_format:{type:'json_object'}})});
    if(!foundry.ok)throw new Error(`Foundry ${foundry.status}`);
    const payload=await foundry.json();
    const parsed=JSON.parse(payload.choices?.[0]?.message?.content||'{}');
    const program=parsed.program||parsed;
    if(!valid(program))return response.status(422).json({status:'clarification_required',original_instruction:instruction,message:'Foundry output failed deterministic DSL validation.',provider:'microsoft-foundry'});
    return response.status(200).json({status:'valid',original_instruction:instruction,program,provider:'microsoft-foundry'});
  }catch(error){
    const program=fallback(instruction);
    return response.status(200).json(program?{status:'valid',original_instruction:instruction,program,provider:'deterministic-server-fallback',provider_error:error.message}:{status:'clarification_required',original_instruction:instruction,message:'The provider was unavailable and the safe fallback needs a supported brief.',provider:'deterministic-server-fallback'});
  }
}
