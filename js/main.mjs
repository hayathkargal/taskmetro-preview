import { estimateServiceFee, localDate, requestSelection, sendSubmission } from './booking.mjs';
import { SITE } from './site-config.mjs';

const money = new Intl.NumberFormat('en-IN', { style: 'currency', currency: 'INR', maximumFractionDigits: 2, minimumFractionDigits: 0 });

export function initializeNavigation(doc = document) {
  const header = doc.querySelector('.site-header');
  const toggle = doc.querySelector('.nav-toggle');
  const nav = doc.querySelector('#site-navigation');
  if (!header || !toggle || !nav) return;
  header.classList.add('enhanced-nav');
  toggle.hidden = false;
  function close(restoreFocus = false) {
    nav.classList.remove('is-open');
    toggle.setAttribute('aria-expanded', 'false');
    toggle.setAttribute('aria-label', 'Open navigation');
    if (restoreFocus) toggle.focus();
  }
  toggle.addEventListener('click', () => {
    const open = toggle.getAttribute('aria-expanded') !== 'true';
    nav.classList.toggle('is-open', open);
    toggle.setAttribute('aria-expanded', String(open));
    toggle.setAttribute('aria-label', open ? 'Close navigation' : 'Open navigation');
  });
  nav.addEventListener('click', event => { if (event.target.closest('a')) close(); });
  doc.addEventListener('click', event => { if (!header.contains(event.target)) close(); });
  doc.addEventListener('keydown', event => { if (event.key === 'Escape' && toggle.getAttribute('aria-expanded') === 'true') close(true); });
  doc.addEventListener('focusin', event => { if (!header.contains(event.target)) close(); });
}

export function initializeEstimator(doc = document) {
  const form = doc.querySelector('#estimate-form');
  if (!form) return;
  const input = form.querySelector('[name="hours"]');
  function update() {
    const estimate = estimateServiceFee(input.value, SITE.baseFee, SITE.hourlyRate);
    doc.querySelector('#estimate-total').textContent = money.format(estimate.total);
    doc.querySelector('#estimate-breakdown').textContent = `${money.format(SITE.baseFee)} base fee + ${money.format(estimate.runner)} for ${estimate.hours} ${estimate.hours === 1 ? 'hour' : 'hours'}`;
  }
  input.addEventListener('change', update);
  form.addEventListener('submit', event => { event.preventDefault(); update(); });
  update();
}

function firstInvalid(container) {
  return Array.from(container.querySelectorAll('input, select, textarea')).find(field => !field.disabled && !field.checkValidity());
}

export function initializeRequestForm(doc = document, search = window.location.search) {
  const form = doc.querySelector('#request-form');
  if (!form) return null;
  const steps = [...form.querySelectorAll('[data-step]')];
  const progress = doc.querySelector('.form-progress');
  const category = form.elements.namedItem('category');
  const urgency = form.elements.namedItem('urgency');
  const selection = requestSelection(search, SITE.categories);
  category.value = selection.category;
  urgency.value = selection.urgency;
  form.elements.namedItem('date').min = localDate();
  const phone = form.elements.namedItem('phone');
  const method = form.elements.namedItem('contactMethod');
  const summary = doc.querySelector('#request-summary');
  function updateContact() {
    phone.required = method.value !== 'email';
    doc.querySelector('#phone-optional').hidden = phone.required;
    const digits = phone.value.replace(/\D/g, '');
    phone.setCustomValidity(phone.value && (digits.length < 7 || digits.length > 15) ? 'Enter a phone number with its country code (7–15 digits).' : '');
  }
  method.addEventListener('change', updateContact);
  phone.addEventListener('input', updateContact);
  function updateSummary() {
    const chosen = category.options[category.selectedIndex]?.text || 'Your task';
    const when = urgency.options[urgency.selectedIndex]?.text || 'Flexible';
    summary.textContent = `${chosen} · ${when} · We’ll confirm the scope and quote with you.`;
  }
  function showStep(number, focus = true) {
    steps.forEach(step => { step.hidden = Number(step.dataset.step) !== number; });
    progress.querySelectorAll('[data-progress]').forEach(item => {
      if (Number(item.dataset.progress) === number) item.setAttribute('aria-current', 'step');
      else item.removeAttribute('aria-current');
    });
    updateSummary();
    if (focus) {
      const legend = steps[number - 1].querySelector('legend');
      legend.tabIndex = -1;
      legend.focus();
    }
  }
  form.querySelector('.step-next').hidden = false;
  form.querySelector('.step-back').hidden = false;
  progress.hidden = false;
  form.noValidate = true;
  form.querySelector('.step-next').addEventListener('click', () => {
    const invalid = firstInvalid(steps[0]);
    if (invalid) invalid.reportValidity();
    else showStep(2);
  });
  form.querySelector('.step-back').addEventListener('click', () => showStep(1));
  // Enter in a first-step single-line control advances; it never sends the request.
  form.addEventListener('keydown', event => {
    if (event.key === 'Enter' && !event.isComposing && !steps[0].hidden && event.target.tagName === 'INPUT') {
      event.preventDefault();
      form.querySelector('.step-next').click();
    }
  });
  updateContact();
  showStep(1, false);
  return {
    validate() {
      updateContact();
      const invalid = firstInvalid(form);
      if (invalid) {
        showStep(Number(invalid.closest('[data-step]').dataset.step), false);
        invalid.reportValidity();
        return false;
      }
      return true;
    },
    reset() { progress.hidden = false; updateContact(); showStep(1); },
    complete() { progress.hidden = true; }
  };
}

export function initializeRemoteForm(form, wizard = null, sender = sendSubmission) {
  const status = form.querySelector('.form-status');
  const submit = form.querySelector('[type="submit"]');
  let sending = false;
  let completed = false;
  const originalText = submit.innerHTML;
  form.addEventListener('submit', async event => {
    event.preventDefault();
    if (sending || completed) return;
    if (wizard ? !wizard.validate() : !form.reportValidity()) return;
    const payload = new FormData(form);
    for (const name of ['category', 'urgency', 'contactMethod']) {
      const select = form.elements.namedItem(name);
      if (select) payload.set(name, select.options[select.selectedIndex].text);
    }
    // Capture values before disabling controls; never persist contact details in storage.
    const controls = [...form.querySelectorAll('input, select, textarea, button')];
    const disabled = controls.map(control => control.disabled);
    controls.forEach(control => { control.disabled = true; });
    sending = true;
    status.classList.remove('success');
    status.textContent = 'Sending your request…';
    form.setAttribute('aria-busy', 'true');
    submit.textContent = 'Sending…';
    try {
      await sender(payload);
      completed = true;
      form.reset();
      const hidden = [...form.querySelectorAll('fieldset, .field, .field-grid, .checkbox-label, .form-actions, button[type="submit"]')];
      hidden.forEach(element => { element.hidden = true; });
      wizard?.complete();
      status.textContent = form.dataset.success;
      status.classList.add('success');
      const another = form.ownerDocument.createElement('button');
      another.type = 'button'; another.className = 'button button-secondary new-request'; another.textContent = 'Start another enquiry';
      another.addEventListener('click', () => {
        completed = false;
        hidden.forEach(element => { element.hidden = false; });
        wizard?.reset();
        status.textContent = ''; status.classList.remove('success'); another.remove();
        if (!wizard) form.querySelector('input[autocomplete="name"]').focus();
      });
      form.append(another);
    } catch (error) {
      status.textContent = error.kind === 'unknown'
        ? 'We couldn’t confirm delivery. Your details are still here. Please contact support@taskmetro.com or WhatsApp +91 93535 22929 before resubmitting, to avoid duplicate requests.'
        : error.kind === 'throttled'
          ? 'The form service is receiving too many requests. Your details are still here. Please try later or contact us on WhatsApp.'
          : 'The form service could not accept this request. Your details are still here. Please contact support@taskmetro.com or WhatsApp +91 93535 22929.';
    } finally {
      controls.forEach((control, index) => { control.disabled = disabled[index]; });
      submit.innerHTML = originalText;
      form.removeAttribute('aria-busy');
      sending = false;
      status.focus();
    }
  });
}

if (typeof document !== 'undefined') {
  document.querySelectorAll('[data-year]').forEach(element => { element.textContent = String(new Date().getFullYear()); });
  initializeNavigation();
  initializeEstimator();
  const wizard = initializeRequestForm();
  document.querySelectorAll('[data-remote-form]').forEach(form => initializeRemoteForm(form, form.id === 'request-form' ? wizard : null));
}
