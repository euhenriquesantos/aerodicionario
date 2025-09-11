document.addEventListener('DOMContentLoaded', () => {
  const overlay = document.createElement('div');
  overlay.style.cssText = 'position:fixed;inset:0;background:rgba(0,0,0,.8);display:none;align-items:center;justify-content:center;z-index:1050;';
  const img = document.createElement('img');
  img.style.cssText = 'max-width:90vw;max-height:90vh;border-radius:10px;box-shadow:0 20px 60px rgba(0,0,0,.5)';
  const prev = document.createElement('button');
  const next = document.createElement('button');
  const close = document.createElement('button');
  [prev, next, close].forEach(b => { b.style.cssText = 'position:absolute;border:0;background:rgba(255,255,255,.15);color:#fff;padding:8px 12px;border-radius:8px;cursor:pointer'; });
  prev.textContent = '◀'; next.textContent = '▶'; close.textContent = '✕';
  prev.style.left='12px'; next.style.right='12px'; close.style.top='12px'; close.style.right='12px';
  const counter = document.createElement('div');
  counter.style.cssText = 'position:absolute;bottom:12px;left:12px;color:#fff;background:rgba(0,0,0,.35);padding:4px 8px;border-radius:8px;font-weight:600;';
  const strip = document.createElement('div');
  strip.style.cssText = 'position:absolute;bottom:12px;right:12px;display:flex;gap:6px;max-width:60vw;overflow:auto;padding:6px;background:rgba(255,255,255,.08);border-radius:8px;';
  overlay.appendChild(img); overlay.appendChild(prev); overlay.appendChild(next); overlay.appendChild(close); overlay.appendChild(counter); overlay.appendChild(strip);
  document.body.appendChild(overlay);
  function hide(){ overlay.style.display='none'; document.removeEventListener('keydown', onKey); }
  close.addEventListener('click', hide); overlay.addEventListener('click', (e)=>{ if(e.target===overlay) hide(); });

  let imgs = []; let idx = -1;
  function show(i){ if(i<0||i>=imgs.length) return; idx=i; img.src = imgs[idx].currentSrc || imgs[idx].src; overlay.style.display='flex'; counter.textContent = `${idx+1}/${imgs.length}`; highlightThumb(); }
  function onKey(e){ if(e.key==='Escape') hide(); if(e.key==='ArrowLeft') show(Math.max(0, idx-1)); if(e.key==='ArrowRight') show(Math.min(imgs.length-1, idx+1)); }
  prev.addEventListener('click', ()=> show(Math.max(0, idx-1))); next.addEventListener('click', ()=> show(Math.min(imgs.length-1, idx+1)));

  const candidates = document.querySelectorAll('.media-embed img, .carousel .carousel-item img');
  candidates.forEach((el, i) => { el.dataset.lbIndex = i; el.style.cursor='zoom-in'; });
  imgs = Array.from(candidates);
  function buildStrip(){
    strip.innerHTML = '';
    imgs.forEach((el,i)=>{
      const t = document.createElement('img');
      t.src = el.currentSrc || el.src;
      t.style.cssText='height:48px;border-radius:6px;cursor:pointer;opacity:.7;border:2px solid transparent;';
      t.addEventListener('click', ()=> show(i));
      strip.appendChild(t);
    });
  }
  function highlightThumb(){
    Array.from(strip.children).forEach((t, i)=>{ t.style.opacity = i===idx? '1':'0.7'; t.style.borderColor = i===idx? '#fff':'transparent'; });
  }
  buildStrip();
  imgs.forEach((el)=> el.addEventListener('click', ()=> { show(parseInt(el.dataset.lbIndex,10)); document.addEventListener('keydown', onKey); }));
});
