import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
const schema=JSON.parse(readFileSync(new URL('./gemini-intake.schema.json',import.meta.url),'utf8'));
const categories=new Set(schema.properties.categories.items.enum);
const score=value=>value===null || (Number.isInteger(value) && value>=1 && value<=10);

// Structural/cross-field validation only. This does not validate medical accuracy.
export function validateIntake(result, suppliedPainScore) {
  assert(score(suppliedPainScore),'Input pain_score must be an integer 1-10 or null');
  assert(result && typeof result==='object' && !Array.isArray(result),'Expected a JSON object');
  assert.deepEqual(Object.keys(result).sort(),schema.required.slice().sort(),'Unexpected/missing fields');
  assert(Array.isArray(result.categories) && result.categories.length>=1 && result.categories.length<=8);
  assert(result.categories.every(c=>categories.has(c)),'Unsupported category');
  assert.equal(new Set(result.categories).size,result.categories.length,'Duplicate category');
  assert(!result.categories.includes('unknown') || result.categories.length===1,'Unknown cannot accompany a known category');
  assert(score(result.pain_score) && score(result.urgency_rating),'Scores must be integers 1-10 or null');
  assert.equal(result.pain_score,suppliedPainScore,'Gemini must not change or invent the pain score');
  assert(result.is_emergency===null || typeof result.is_emergency==='boolean');
  assert.equal(typeof result.needs_more_information,'boolean');
  assert(typeof result.reason==='string' && result.reason.trim().length && result.reason.length<=400);
  if(result.is_emergency===true) {
    assert.equal(result.urgency_rating,10,'Suspected emergency uses demo rating 10');
    assert.equal(result.needs_more_information,false,'Do not delay emergency action for follow-up');
    assert.equal(result.follow_up_question,null);
  } else {
    const missing=result.urgency_rating===null || result.is_emergency===null || result.categories[0]==='unknown';
    assert.equal(result.needs_more_information,missing,'Incomplete result must request clarification');
    if(missing) assert(typeof result.follow_up_question==='string' && result.follow_up_question.trim().length && result.follow_up_question.length<=240);
    else assert.equal(result.follow_up_question,null);
  }
  return result;
}

export function intakeAction(validatedResult) {
  if(validatedResult.is_emergency===true) return 'show_999';
  if(validatedResult.needs_more_information) return 'ask_follow_up';
  return 'confirm_categories';
}
