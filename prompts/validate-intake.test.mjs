import test from 'node:test';
import assert from 'node:assert/strict';
import {validateIntake,intakeAction} from './validate-intake.mjs';
const assessment=()=>({categories:['cuts_or_wounds'],pain_score:2,urgency_rating:2,is_emergency:false,needs_more_information:false,follow_up_question:null,reason:'A small scrape with low reported pain.'});
test('supports multiple confirmed suggestions without ranking them',()=>{
  const x=assessment();x.categories.push('fracture_sprain_or_dislocation');
  assert.equal(intakeAction(validateIntake(x,2)),'confirm_categories');
});
test('low pain cannot structurally suppress a suspected emergency',()=>{
  const x={...assessment(),categories:['breathing_problems'],pain_score:1,urgency_rating:10,is_emergency:true,reason:'Reported severe breathing difficulty despite low pain.'};
  assert.equal(intakeAction(validateIntake(x,1)),'show_999');
  x.needs_more_information=true;assert.throws(()=>validateIntake(x,1));
});
test('insufficient information is not replaced with a reassuring score',()=>{
  const x={...assessment(),categories:['unknown'],pain_score:null,urgency_rating:null,is_emergency:null,needs_more_information:true,follow_up_question:'What symptoms are you experiencing?',reason:'No clear symptoms supplied.'};
  assert.equal(intakeAction(validateIntake(x,null)),'ask_follow_up');
  x.needs_more_information=false;assert.throws(()=>validateIntake(x,null));
});
test('rejects hallucinated pain, out-of-range urgency and ambiguous categories',()=>{
  for(const mutate of [x=>x.pain_score=3,x=>x.urgency_rating=11,x=>x.urgency_rating=0,x=>x.urgency_rating=4.5,x=>x.categories.push('unknown'),x=>x.categories.push('cuts_or_wounds')]) {
    const x=assessment();mutate(x);assert.throws(()=>validateIntake(x,2));
  }
});
test('high pain alone does not mandate an emergency flag',()=>{
  const x={...assessment(),pain_score:10,urgency_rating:8,reason:'High reported pain; no emergency warning signs identified in the supplied description.'};
  assert.equal(intakeAction(validateIntake(x,10)),'confirm_categories');
});
