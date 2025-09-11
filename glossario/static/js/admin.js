// Melhorias simples de UX no admin
document.addEventListener('DOMContentLoaded', () => {
  // Clique na linha abre a edição
  document.querySelectorAll('.change-list .result-list tbody tr').forEach((tr) => {
    const link = tr.querySelector('th a');
    if (!link) return;
    tr.style.cursor = 'pointer';
    tr.addEventListener('click', (e) => {
      // Evita conflito com checkbox/links internos
      if (e.target.tagName.toLowerCase() === 'a' || e.target.type === 'checkbox' || e.target.closest('a')) return;
      window.location.href = link.getAttribute('href');
    });
  });

  // Fix de cabeçalho sticky em tabelas longas
  const header = document.querySelector('.change-list .results');
  if (header) header.style.position = 'relative';

  // Atalhos na moderação: A aprova, R rejeita, N próximo
  if (location.pathname.includes('/admin/glossario/suggestion/moderar')) {
    document.addEventListener('keydown', (e) => {
      if (e.target.tagName.toLowerCase() === 'input' || e.target.tagName.toLowerCase() === 'textarea') return;
      if (e.key.toLowerCase() === 'a') {
        const form = document.querySelector('form');
        if (form) { const btn = form.querySelector('button[name="action"][value="approve"]'); if (btn) btn.click(); }
      }
      if (e.key.toLowerCase() === 'r') {
        const form = document.querySelector('form');
        if (form) { const btn = form.querySelector('button[name="action"][value="reject"]'); if (btn) btn.click(); }
      }
      if (e.key.toLowerCase() === 'n') {
        location.href = location.href;
      }
    });
  }
});
