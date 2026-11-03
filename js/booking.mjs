/** Pure booking rules, shared by the UI and the unit tests. */
export function estimateServiceFee(hours, baseFee, hourlyRate) {
  const time = Number(hours);
  if (!Number.isFinite(time) || time <= 0 || time > 24) throw new RangeError('Choose between 0 and 24 hours.');
  if (![baseFee, hourlyRate].every(value => Number.isFinite(value) && value >= 0)) throw new RangeError('Invalid pricing configuration.');
  const halfHours = Math.ceil(time * 2);
  const runnerPaise = Math.round(hourlyRate * 100) * halfHours / 2;
  const totalPaise = Math.round(baseFee * 100) + runnerPaise;
  return { hours: halfHours / 2, runner: runnerPaise / 100, total: totalPaise / 100 };
}

export function requestSelection(search, categories) {
  const params = new URLSearchParams(search);
  const category = params.get('category');
  const urgency = params.get('urgency');
  return {
    category: categories.includes(category) ? category : '',
    urgency: ['flexible', '48-hours', 'same-day'].includes(urgency) ? urgency : 'flexible'
  };
}

export function localDate(date = new Date()) {
  return `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, '0')}-${String(date.getDate()).padStart(2, '0')}`;
}

export class SubmissionError extends Error {
  constructor(kind) {
    super(kind);
    this.name = 'SubmissionError';
    this.kind = kind;
  }
}

/** One attempt only: a timeout or network error can follow a successful delivery. */
export async function sendSubmission(payload, { fetcher = globalThis.fetch, timeoutMs = 15000 } = {}) {
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), timeoutMs);
  try {
    const response = await fetcher('https://api.web3forms.com/submit', {
      method: 'POST', body: payload, signal: controller.signal, headers: { Accept: 'application/json' }
    });
    if (!response.ok) throw new SubmissionError(response.status === 429 ? 'throttled' : 'rejected');
    const result = await response.json();
    if (result.success !== true) throw new SubmissionError('rejected');
    return true;
  } catch (error) {
    if (error instanceof SubmissionError) throw error;
    throw new SubmissionError('unknown');
  } finally {
    clearTimeout(timer);
  }
}
