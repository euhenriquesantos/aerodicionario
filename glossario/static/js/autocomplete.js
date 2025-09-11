document.addEventListener('DOMContentLoaded', () => {
  const inputs = document.querySelectorAll('input[name="q"]');
  inputs.forEach((input) => {
    // container dropdown
    const wrap = document.createElement('div');
    wrap.style.position = 'relative';
    input.parentElement.insertBefore(wrap, input);
    wrap.appendChild(input);
    const list = document.createElement('div');
    list.className = 'ac-dropdown';
    list.setAttribute('role','listbox');
    list.style.cssText = 'position:absolute;left:0;right:0;top:100%;z-index:1000;background:#fff;border:1px solid rgba(0,0,0,.08);border-radius:12px;box-shadow:0 8px 24px rgba(16,24,40,.08);display:none;overflow:hidden;';
    wrap.appendChild(list);

    let controller = null;
    let cursor = -1;
    let items = [];

    const escapeHtml = (s) => s.replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;','\'':'&#39;'}[c]));
    const highlight = (text, q) => {
      const esc = escapeHtml(text);
      const re = new RegExp(q.replace(/[.*+?^${}()|[\]\\]/g,'\\$&'), 'ig');
      return esc.replace(re, (m)=>`<mark>${escapeHtml(m)}</mark>`);
    };

    const render = () => {
      list.innerHTML = '';
      items.forEach((it, idx) => {
        const a = document.createElement('a');
        a.href = `/dicionario/${it.slug}/`;
        const label = it.decod ? `${it.label} — ${it.decod}` : it.label;
        a.innerHTML = highlight(label, input.value.trim());
        a.setAttribute('role','option');
        a.id = `ac-item-${idx}`;
        a.style.cssText = 'display:block;padding:10px 12px;text-decoration:none;color:#0f172a;font-size:14px;';
        if (idx === cursor) a.style.background = '#eef7ff';
        list.appendChild(a);
      });
      list.style.display = items.length ? 'block' : 'none';
    };

    async function search() {
      const q = input.value.trim();
      if (q.length < 2) { items = []; render(); return; }
      try {
        if (controller) controller.abort();
        controller = new AbortController();
        const res = await fetch(`/api/autocomplete/?q=${encodeURIComponent(q)}`, { signal: controller.signal });
        const data = await res.json();
        items = data.results || [];
        cursor = -1; render();
      } catch (e) {/* ignore */}
    }

    input.addEventListener('input', search);
    input.setAttribute('aria-controls','ac-listbox');
    input.addEventListener('keydown', (e) => {
      if (!items.length) return;
      if (e.key === 'ArrowDown') { e.preventDefault(); cursor = Math.min(cursor + 1, items.length - 1); render(); }
      else if (e.key === 'ArrowUp') { e.preventDefault(); cursor = Math.max(cursor - 1, 0); render(); }
      else if (e.key === 'Enter' && cursor >= 0) { e.preventDefault(); window.location.href = `/dicionario/${items[cursor].slug}/`; }
      else if (e.key === 'Escape') { items = []; render(); }
      if (cursor >= 0) input.setAttribute('aria-activedescendant', `ac-item-${cursor}`);
    });

    document.addEventListener('click', (e) => {
      if (!wrap.contains(e.target)) { list.style.display = 'none'; }
    });
  });
});
