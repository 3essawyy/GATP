// GATP inspector: collect interactive elements from the live DOM (T-007, ADR-006).
// Runs inside the page via page.evaluate(). Read-only: it never clicks, types or changes
// the DOM. Elements are kept in window.__gatpEls so Python can later check that a locator
// points at exactly this element.
(scope) => {
  const INTERACTIVE = [
    'a[href]', 'button', 'input:not([type="hidden"])', 'select', 'textarea', 'summary',
    '[role="button"]', '[role="link"]', '[role="checkbox"]', '[role="radio"]',
    '[role="textbox"]', '[role="combobox"]', '[role="searchbox"]', '[role="switch"]',
    '[role="tab"]', '[role="menuitem"]', '[role="option"]', '[contenteditable="true"]',
    '[onclick]', '[tabindex]:not([tabindex="-1"])',
  ].join(',');
  const ATTRS = ['id', 'name', 'type', 'data-testid', 'placeholder', 'href', 'aria-label',
    'aria-labelledby', 'title', 'role', 'value', 'for', 'required', 'disabled', 'class',
    'onclick', 'data-draft', 'inputmode', 'autocomplete'];
  const clean = (s) => (s || '').replace(/\s+/g, ' ').trim();
  const short = (s, n = 200) => { const t = clean(s); return t.length > n ? t.slice(0, n) + '…' : t; };

  function implicitRole(el) {
    const explicit = el.getAttribute('role');
    if (explicit) return explicit.split(/\s+/)[0];
    const tag = el.tagName.toLowerCase();
    const type = (el.getAttribute('type') || 'text').toLowerCase();
    if (tag === 'a') return el.hasAttribute('href') ? 'link' : '';
    if (tag === 'button' || tag === 'summary') return 'button';
    if (tag === 'select') return el.multiple || el.size > 1 ? 'listbox' : 'combobox';
    if (tag === 'textarea') return 'textbox';
    if (tag === 'input') {
      if (['button', 'submit', 'reset', 'image'].includes(type)) return 'button';
      if (type === 'checkbox') return 'checkbox';
      if (type === 'radio') return 'radio';
      if (type === 'range') return 'slider';
      if (type === 'number') return 'spinbutton';
      if (type === 'search') return el.hasAttribute('list') ? 'combobox' : 'searchbox';
      if (['text', 'email', 'tel', 'url', ''].includes(type)) return el.hasAttribute('list') ? 'combobox' : 'textbox';
      return ''; // password, date, color, file … have no ARIA role
    }
    return '';
  }

  function labelText(el) {
    if (el.labels && el.labels.length) return clean([...el.labels].map((l) => l.innerText || l.textContent).join(' '));
    return '';
  }

  // Simplified accessible-name computation. The live count check in Python verifies it:
  // a wrong name simply yields an unusable role locator.
  function accessibleName(el) {
    const by = el.getAttribute('aria-labelledby');
    if (by) {
      const t = by.split(/\s+/).map((id) => document.getElementById(id)).filter(Boolean)
        .map((n) => n.textContent).join(' ');
      if (clean(t)) return clean(t);
    }
    if (clean(el.getAttribute('aria-label'))) return clean(el.getAttribute('aria-label'));
    const tag = el.tagName.toLowerCase();
    const type = (el.getAttribute('type') || '').toLowerCase();
    if (['input', 'select', 'textarea'].includes(tag)) {
      const l = labelText(el);
      if (l) return l;
      if (tag === 'input' && ['button', 'submit', 'reset'].includes(type)) {
        return clean(el.value) || (type === 'submit' ? 'Submit' : type === 'reset' ? 'Reset' : '');
      }
      if (clean(el.getAttribute('title'))) return clean(el.getAttribute('title'));
      return clean(el.getAttribute('placeholder'));
    }
    const text = clean(el.innerText || el.textContent);
    if (text) return text;
    return clean(el.getAttribute('title'));
  }

  function domPath(el) {
    const parts = [];
    let node = el;
    while (node && node.nodeType === 1 && node !== document.documentElement) {
      let part = node.tagName.toLowerCase();
      if (node.id) { parts.unshift(`${part}#${CSS.escape(node.id)}`); break; }
      const parent = node.parentElement;
      if (parent) {
        const same = [...parent.children].filter((c) => c.tagName === node.tagName);
        if (same.length > 1) part += `:nth-of-type(${same.indexOf(node) + 1})`;
      }
      parts.unshift(part);
      node = parent;
    }
    return parts.join(' > ');
  }

  function nearbyText(el) {
    const out = [];
    const add = (t) => { t = short(t, 80); if (t && !out.includes(t) && out.length < 5) out.push(t); };
    const field = el.closest('.field, fieldset, label, li, td, th, p, div');
    if (field) for (const n of field.querySelectorAll('label, legend, .error, span, small')) if (n !== el) add(n.textContent);
    let prev = el.previousElementSibling;
    for (let i = 0; prev && i < 2; i++, prev = prev.previousElementSibling) add(prev.textContent);
    const heading = el.closest('main, section, form, body')?.querySelector('h1, h2, h3');
    if (heading) add(heading.textContent);
    return out;
  }

  const within = (el, sels) => sels.some((s) => { try { return !!el.closest(s); } catch { return false; } });
  const include = (scope && scope.include) || [];
  const exclude = (scope && scope.exclude) || [];
  const all = [...document.querySelectorAll(INTERACTIVE)].filter((el) =>
    (include.length === 0 || within(el, include)) && !within(el, exclude));
  window.__gatpEls = all;

  const formIndex = new Map();
  return all.map((el, i) => {
    const attrs = {};
    for (const a of ATTRS) if (el.hasAttribute(a)) attrs[a] = short(el.getAttribute(a), 300);
    const rect = el.getBoundingClientRect();
    const style = getComputedStyle(el);
    const visible = rect.width > 0 && rect.height > 0 && style.visibility !== 'hidden' && style.display !== 'none';
    const form = el.closest('form');
    const formKey = form ? (form.id || domPath(form)) : '';
    const role = implicitRole(el);
    const k = `${formKey}|${role}|${el.tagName}`;
    const indexInForm = formIndex.get(k) || 0;
    formIndex.set(k, indexInForm + 1);
    return {
      index: i,
      tag: el.tagName.toLowerCase(),
      role,
      name: short(accessibleName(el)),
      text: short(el.innerText || el.textContent),
      label: labelText(el),
      attributes: attrs,
      dom_path: domPath(el),
      start_tag: el.outerHTML.split('>')[0] + '>',
      bbox: { x: Math.round(rect.x + scrollX), y: Math.round(rect.y + scrollY), width: Math.round(rect.width), height: Math.round(rect.height) },
      visible,
      enabled: !el.disabled && el.getAttribute('aria-disabled') !== 'true',
      nearby_text: nearbyText(el),
      form: formKey,
      index_in_form: indexInForm,
    };
  });
}
