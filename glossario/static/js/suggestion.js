document.addEventListener('DOMContentLoaded', () => {
  const input = document.querySelector('input[type="file"][name="imagens"]');
  const preview = document.getElementById('preview-imagens');
  if (!input || !preview) return;
  input.addEventListener('change', () => {
    preview.innerHTML = '';
    const files = Array.from(input.files || []);
    files.forEach((file) => {
      if (!file.type.startsWith('image/')) return;
      const reader = new FileReader();
      reader.onload = (e) => {
        const img = document.createElement('img');
        img.src = e.target.result;
        img.alt = file.name;
        img.style.maxWidth = '120px';
        img.style.maxHeight = '90px';
        img.style.borderRadius = '8px';
        img.style.boxShadow = '0 4px 12px rgba(0,0,0,.15)';
        preview.appendChild(img);
      };
      reader.readAsDataURL(file);
    });
  });
});

