import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import { createRequire } from 'node:module';
import { initializeNavigation, initializeEstimator, initializeRequestForm, initializeRemoteForm } from '../js/main.mjs';
const require=createRequire(import.meta.url);
const { JSDOM }=require('jsdom');
const flush=()=>new Promise(resolve=>setImmediate(resolve));

function page(name) {
  return new JSDOM(fs.readFileSync(new URL('../'+name,import.meta.url),'utf8'),{url:'https://hayathkargal.github.io/taskmetro-preview/'+name,pretendToBeVisual:true});
}
function task(form) {
  form.elements.namedItem('category').value='property';
  form.elements.namedItem('details').value='Check my apartment in Whitefield and share photos.';
}
function person(form) {
  form.elements.namedItem('name').value='Preview Tester';
  form.elements.namedItem('email').value='preview@example.com';
  form.elements.namedItem('agreeTerms').checked=true;
}
test('mobile navigation updates accessibility state and closes with Escape',()=>{
  const dom=page('index.html'),doc=dom.window.document;initializeNavigation(doc);
  const toggle=doc.querySelector('.nav-toggle');toggle.click();
  assert.equal(toggle.getAttribute('aria-expanded'),'true');
  doc.dispatchEvent(new dom.window.KeyboardEvent('keydown',{key:'Escape'}));
  assert.equal(toggle.getAttribute('aria-expanded'),'false');assert.equal(doc.activeElement,toggle);dom.window.close();
});
test('service selection is carried into the two-step form',()=>{
  const dom=page('request.html'),doc=dom.window.document;
  initializeRequestForm(doc,'?category=educational&urgency=48-hours');
  const form=doc.querySelector('form');
  assert.equal(form.elements.namedItem('category').value,'educational');
  assert.equal(form.elements.namedItem('urgency').value,'48-hours');
  assert.equal(form.querySelector('[data-step="2"]').hidden,true);dom.window.close();
});
test('incomplete task details prevent advancement; Back preserves values',()=>{
  const dom=page('request.html'),doc=dom.window.document;initializeRequestForm(doc,'');
  const form=doc.querySelector('form');form.querySelector('.step-next').click();
  assert.equal(form.querySelector('[data-step="1"]').hidden,false);
  task(form);form.querySelector('.step-next').click();
  assert.equal(form.querySelector('[data-step="2"]').hidden,false);
  form.querySelector('.step-back').click();
  assert.match(form.elements.namedItem('details').value,/Whitefield/);dom.window.close();
});
test('contact channel requires a usable phone number when needed',()=>{
  const dom=page('request.html'),doc=dom.window.document;const wizard=initializeRequestForm(doc,'');
  const form=doc.querySelector('form');task(form);person(form);
  const method=form.elements.namedItem('contactMethod');method.value='whatsapp';method.dispatchEvent(new dom.window.Event('change'));
  assert.equal(wizard.validate(),false);
  const phone=form.elements.namedItem('phone');phone.value='+91 98765 43210';phone.dispatchEvent(new dom.window.Event('input'));
  assert.equal(wizard.validate(),true);dom.window.close();
});
test('pricing calculator updates fractional-hour estimates',()=>{
  const dom=page('pricing.html'),doc=dom.window.document;initializeEstimator(doc);
  const hours=doc.querySelector('#estimate-hours');hours.value='1.5';hours.dispatchEvent(new dom.window.Event('change'));
  assert.match(doc.querySelector('#estimate-total').textContent,/572.5/);dom.window.close();
});
test('failed submission retains details, restores controls and never shows success',async()=>{
  const dom=page('request.html'),doc=dom.window.document;const wizard=initializeRequestForm(doc,'');
  const form=doc.querySelector('form');task(form);person(form);
  const original=globalThis.FormData;globalThis.FormData=dom.window.FormData;
  try{
    initializeRemoteForm(form,wizard,async()=>{throw {kind:'unknown'};});
    form.dispatchEvent(new dom.window.Event('submit',{cancelable:true}));await flush();
    assert.match(form.elements.namedItem('details').value,/Whitefield/);
    assert.equal(form.querySelector('[type="submit"]').disabled,false);
    assert.equal(form.querySelector('.form-status').classList.contains('success'),false);
    assert.match(form.querySelector('.form-status').textContent,/couldn’t confirm delivery/);
  }finally{globalThis.FormData=original;dom.window.close();}
});
test('double submission is suppressed and success requires positive confirmation',async()=>{
  const dom=page('request.html'),doc=dom.window.document;const wizard=initializeRequestForm(doc,'');
  const form=doc.querySelector('form');task(form);person(form);
  const original=globalThis.FormData;globalThis.FormData=dom.window.FormData;
  let calls=0,resolve;
  try{
    initializeRemoteForm(form,wizard,payload=>{calls++;assert.equal(payload.get('category'),'Property & utilities');return new Promise(done=>{resolve=done;});});
    form.dispatchEvent(new dom.window.Event('submit',{cancelable:true}));
    form.dispatchEvent(new dom.window.Event('submit',{cancelable:true}));
    assert.equal(calls,1);assert.equal(form.getAttribute('aria-busy'),'true');
    resolve(true);await flush();
    assert.equal(form.querySelector('.form-status').classList.contains('success'),true);
    assert.match(form.querySelector('.form-status').textContent,/booking is not confirmed/);
    form.querySelector('.new-request').click();
    assert.equal(form.querySelector('[data-step="1"]').hidden,false);
    assert.equal(form.querySelector('[data-step="2"]').hidden,true);
  }finally{globalThis.FormData=original;dom.window.close();}
});
test('invalid consent prevents any submission',()=>{
  const dom=page('request.html'),doc=dom.window.document;const wizard=initializeRequestForm(doc,'');
  const form=doc.querySelector('form');task(form);person(form);form.elements.namedItem('agreeTerms').checked=false;
  let calls=0;initializeRemoteForm(form,wizard,async()=>{calls++;});
  form.dispatchEvent(new dom.window.Event('submit',{cancelable:true}));assert.equal(calls,0);dom.window.close();
});
