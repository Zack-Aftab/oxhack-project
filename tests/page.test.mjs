import test from 'node:test';
import assert from 'node:assert/strict';
import { readFile } from 'node:fs/promises';
import { JSDOM } from 'jsdom';
const html=await readFile(new URL('../public/index.html',import.meta.url),'utf8');
const normal=()=>({suggestedCategories:['cuts_or_wounds'],requiresConfirmation:true,painScore:7,urgencyRating:5,isEmergency:false,needsMoreInformation:false,followUpQuestion:null,reason:'Reported wound.',action:'confirm_categories',emergencyMessage:null});
function page(t,payload,{failure=false}={}) {
  const requests=[];
  const dom=new JSDOM(html,{url:'http://localhost:3000',runScripts:'dangerously',beforeParse(window){
    window.AbortSignal.timeout=()=>new window.AbortController().signal;
    window.fetch=async(url,request)=>{requests.push(request);if(failure) throw new Error('Network unavailable');return {ok:true,json:async()=>payload};};
  }});
  t.after(()=>dom.window.close());
  const d=dom.window.document;const get=id=>d.getElementById(id);
  get('symptoms').value='I cut my elbow.';get('pain').value='7';
  return {get,window:dom.window,requests};
}
async function settled(predicate) {for(let n=0;n<100;n++){if(predicate())return;await new Promise(resolve=>setTimeout(resolve,1));}assert.fail('Page did not reach expected state');}

test('page submits selected pain, displays urgency and invalidates the result after input changes',async t=>{
  const {get,window,requests}=page(t,normal());get('analyse').click();
  await settled(()=>!get('assessment').hidden);
  assert.equal(requests[0].body.get('pain_score'),'7');assert.equal(get('urgencyResult').textContent,'5/10');
  assert.equal(get('confirm').disabled,false);get('confirm').click();assert.match(get('confirmation').textContent,/Cuts or wounds/);
  get('pain').value='8';get('pain').dispatchEvent(new window.Event('change'));assert.equal(get('assessment').hidden,true);assert.equal(get('confirmation').textContent,'');
});
test('emergency blocks confirmation and stays visible until explicitly starting a new example',async t=>{
  const payload={...normal(),requiresConfirmation:false,urgencyRating:10,isEmergency:true,action:'show_999',emergencyMessage:'Untrusted message ignored'};
  const {get,window}=page(t,payload);get('analyse').click();await settled(()=>!get('emergency').hidden);
  assert.equal(get('confirm').disabled,true);assert.equal(get('analyse').disabled,true);assert.match(get('emergency').textContent,/Call 999/);assert.doesNotMatch(get('emergency').textContent,/Untrusted/);
  get('symptoms').value='Changed';get('symptoms').dispatchEvent(new window.Event('input'));assert.equal(get('emergency').hidden,false);assert.equal(get('confirm').disabled,true);
  get('reset').click();assert.equal(get('emergency').hidden,true);assert.equal(get('symptoms').value,'');assert.equal(get('pain').value,'');assert.equal(get('analyse').disabled,false);
});
test('unknown input shows clarification without a made-up urgency number',async t=>{
  const payload={...normal(),suggestedCategories:['unknown'],requiresConfirmation:false,urgencyRating:null,isEmergency:null,needsMoreInformation:true,followUpQuestion:'What symptoms do you have?',action:'ask_follow_up'};
  const {get}=page(t,payload);get('analyse').click();await settled(()=>!get('assessment').hidden);
  assert.equal(get('urgencyResult').textContent,'Not enough information');assert.match(get('followUp').textContent,/What symptoms/);assert.equal(get('confirm').disabled,true);
});
test('network errors leave assessment unavailable instead of showing a safe-looking result',async t=>{
  const {get}=page(t,normal(),{failure:true});get('analyse').click();await settled(()=>get('status').textContent.includes('Network unavailable'));
  assert.equal(get('assessment').hidden,true);assert.match(get('status').textContent,/unassessed/);
});
test('model explanations are inserted as text, not executable HTML',async t=>{
  const payload={...normal(),reason:'<img src=x onerror="alert(1)">'};
  const {get}=page(t,payload);get('analyse').click();await settled(()=>!get('assessment').hidden);
  assert.equal(get('reason').textContent,payload.reason);assert.equal(get('reason').querySelector('img'),null);
});
