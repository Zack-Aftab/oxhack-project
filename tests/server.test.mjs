import test from 'node:test';
import assert from 'node:assert/strict';
import { once } from 'node:events';
import { createApp } from '../server.mjs';

const result = pain => ({ categories:['cuts_or_wounds'], pain_score:pain, urgency_rating:4, is_emergency:false, needs_more_information:false, follow_up_question:null, reason:'Reported wound and pain.' });
async function serve(t, generateContent, extra={}) {
  const app=await createApp({generateContent,logger:{error(){}},...extra});
  const server=app.listen(0,'127.0.0.1');await once(server,'listening');
  t.after(()=>new Promise(resolve=>{server.close(resolve);server.closeAllConnections();}));
  return `http://127.0.0.1:${server.address().port}`;
}
function form(pain='7') { const f=new FormData();f.append('symptoms','I cut my elbow.');f.append('pain_score',pain);return f; }

test('serves the page and carries two text fields through the real HTTP route',async t=>{
  let request;
  const url=await serve(t,async r=>{request=r;return {text:JSON.stringify(result(7))};});
  assert.match(await (await fetch(url)).text(),/id="pain"/);
  const r=await fetch(`${url}/classify`,{method:'POST',body:form()});assert.equal(r.status,200);
  const data=await r.json();assert.equal(data.urgencyRating,4);assert.equal(data.painScore,7);assert.equal(data.action,'confirm_categories');assert.equal(data.requiresConfirmation,true);
  assert.equal(JSON.parse(request.contents[0].parts[0].text.split('\n').slice(1).join('\n')).pain_score,7);
  assert(request.config.responseJsonSchema.required.includes('urgency_rating'));
  assert.equal(r.headers.get('cache-control'),'no-store');
});
test('accepts image, description and pain in one multipart request',async t=>{
  let request;const url=await serve(t,async r=>{request=r;return {text:JSON.stringify(result(7))};});
  const f=form();const png=Buffer.from('iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwMCAO+aKc8AAAAASUVORK5CYII=','base64');
  f.append('image',new Blob([png],{type:'image/png'}),'example.png');
  const r=await fetch(`${url}/classify`,{method:'POST',body:f});assert.equal(r.status,200);assert.equal(request.contents[0].parts[1].inlineData.mimeType,'image/png');
});
test('emergency response takes precedence over confirmation even at low pain',async t=>{
  const url=await serve(t,async()=>({text:JSON.stringify({...result(1),categories:['breathing_problems'],urgency_rating:10,is_emergency:true})}));
  const data=await (await fetch(`${url}/classify`,{method:'POST',body:form('1')})).json();
  assert.equal(data.action,'show_999');assert.equal(data.requiresConfirmation,false);assert.match(data.emergencyMessage,/Call 999/);
});
test('insufficient information returns a question and no invented score',async t=>{
  const url=await serve(t,async()=>({text:JSON.stringify({...result(null),categories:['unknown'],urgency_rating:null,is_emergency:null,needs_more_information:true,follow_up_question:'What symptoms are you experiencing?'})}));
  const data=await (await fetch(`${url}/classify`,{method:'POST',body:form('')})).json();assert.equal(data.action,'ask_follow_up');assert.equal(data.urgencyRating,null);
});
test('rejects invalid pain and mismatched image bytes before calling Gemini',async t=>{
  let calls=0;const url=await serve(t,async()=>{calls++;return {text:JSON.stringify(result(7))};});
  for(const value of ['0','11','3.5','not-a-number']) assert.equal((await fetch(`${url}/classify`,{method:'POST',body:form(value)})).status,400);
  const f=form();f.append('image',new Blob(['not a PNG'],{type:'image/png'}),'fake.png');
  assert.equal((await fetch(`${url}/classify`,{method:'POST',body:f})).status,400);assert.equal(calls,0);
});
test('oversized uploads are rejected without an upstream request',async t=>{
  let calls=0;const url=await serve(t,async()=>{calls++;});
  const f=form();f.append('image',new Blob([new Uint8Array(3*1024*1024+1)],{type:'image/png'}),'large.png');
  assert.equal((await fetch(`${url}/classify`,{method:'POST',body:f})).status,400);assert.equal(calls,0);
});
test('invalid Gemini output never becomes a low score or false emergency assessment',async t=>{
  const url=await serve(t,async()=>({text:JSON.stringify(result(3))}));
  const r=await fetch(`${url}/classify`,{method:'POST',body:form('7')});assert.equal(r.status,502);
  const data=await r.json();assert.equal(data.assessmentAvailable,false);assert.equal(Object.hasOwn(data,'isEmergency'),false);
});
test('timeout aborts the request and yields an unavailable assessment',async t=>{
  let signal;const url=await serve(t,r=>{signal=r.config.abortSignal;return new Promise(()=>{});},{timeoutMs:20});
  const r=await fetch(`${url}/classify`,{method:'POST',body:form()});assert.equal(r.status,504);assert.equal(signal.aborted,true);
});
test('provider failure does not log or return its potentially sensitive message',async t=>{
  const logs=[];const url=await serve(t,async()=>{throw new Error('secret-key and patient symptoms must not leak');},{logger:{error(...args){logs.push(args);}}});
  const r=await fetch(`${url}/classify`,{method:'POST',body:form()});assert.equal(r.status,502);
  assert.doesNotMatch(await r.text(),/secret-key|patient symptoms/);assert.doesNotMatch(JSON.stringify(logs),/secret-key|patient symptoms/);
});
