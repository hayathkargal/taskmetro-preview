import test from 'node:test';
import assert from 'node:assert/strict';
import { estimateServiceFee, requestSelection, localDate, sendSubmission } from '../js/booking.mjs';

test('fee estimate uses published pricing and 30-minute increments', () => {
  assert.deepEqual(estimateServiceFee(1,199,249),{hours:1,runner:249,total:448});
  assert.deepEqual(estimateServiceFee(1.5,199,249),{hours:1.5,runner:373.5,total:572.5});
  assert.deepEqual(estimateServiceFee(.6,199,249),{hours:1,runner:249,total:448});
  assert.deepEqual(estimateServiceFee(.5,199,249),{hours:.5,runner:124.5,total:323.5});
});
test('invalid or unlimited estimates are rejected', () => {
  for(const value of ['',0,-1,NaN,Infinity,25,'<script>']) assert.throws(()=>estimateServiceFee(value,199,249));
});
test('only known service and urgency parameters are accepted', () => {
  assert.deepEqual(requestSelection('?category=property&urgency=same-day',['property']),{category:'property',urgency:'same-day'});
  assert.deepEqual(requestSelection('?category=%3Cscript%3E&urgency=now',['property']),{category:'',urgency:'flexible'});
});
test('local date does not use UTC day boundaries', () => {
  assert.equal(localDate(new Date(2026,10,3,0,5)),'2026-11-03');
});
test('positive delivery confirmation requires HTTP success and success=true', async () => {
  let calls=0;
  const result=await sendSubmission(new FormData(),{fetcher:async(url,options)=>{
    calls++; assert.equal(url,'https://api.web3forms.com/submit');assert.equal(options.method,'POST');
    return {ok:true,json:async()=>({success:true})};
  }});
  assert.equal(result,true);assert.equal(calls,1);
});
test('provider rejection is never reported as success', async () => {
  await assert.rejects(sendSubmission(new FormData(),{fetcher:async()=>({ok:true,json:async()=>({success:false})})}),{kind:'rejected'});
});
test('rate limiting has a specific outcome', async () => {
  await assert.rejects(sendSubmission(new FormData(),{fetcher:async()=>({ok:false,status:429})}),{kind:'throttled'});
});
test('an invalid response is treated as uncertain delivery', async () => {
  await assert.rejects(sendSubmission(new FormData(),{fetcher:async()=>({ok:true,json:async()=>{throw new Error('bad JSON');}})}),{kind:'unknown'});
});
test('a network error does not automatically retry', async () => {
  let calls=0;
  await assert.rejects(sendSubmission(new FormData(),{fetcher:async()=>{calls++;throw new Error('network');}}),{kind:'unknown'});
  assert.equal(calls,1);
});
test('a slow submission is aborted without an automatic retry', async () => {
  let calls=0;
  await assert.rejects(sendSubmission(new FormData(),{timeoutMs:5,fetcher:async(url,{signal})=>{
    calls++;return new Promise((resolve,reject)=>signal.addEventListener('abort',()=>reject(new Error('aborted')),{once:true}));
  }}),{kind:'unknown'});
  assert.equal(calls,1);
});
