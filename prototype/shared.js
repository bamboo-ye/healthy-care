(() => {
'use strict';
  const paths = {
    heart:'M20.8 4.6a5.5 5.5 0 0 0-7.8 0L12 5.7l-1.1-1.1a5.5 5.5 0 0 0-7.8 7.8L12 21l8.8-8.6a5.5 5.5 0 0 0 0-7.8M3 12h5l2-4 4 8 2-4h5',
    home:'m3 10 9-7 9 7M5 9v11h14V9M9 20v-7h6v7',
    calendar:'M5 5h14a2 2 0 0 1 2 2v12a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V7a2 2 0 0 1 2-2M7 3v4M17 3v4M3 11h18M8 15h2M14 15h2',
    pill:'m5 19 14-14M8 3a6 6 0 0 1 9 0l4 4a6 6 0 0 1 0 9l-5 5a6 6 0 0 1-9 0l-4-4a6 6 0 0 1 0-9z',
    signal:'M3 12h4l3-8 4 16 3-8h4',
    shield:'m12 3 8 3v6c0 5-8 9-8 9s-8-4-8-9V6zM8 12l3 3 5-6',
    plus:'M12 5v14M5 12h14',
    arrow:'M4 12h16m-6-6 6 6-6 6',
    leaf:'M20 3C9 2 2 7 4 15c1 5 9 7 13 1 3-4 2-8 3-13ZM4 21 17 7M9 15v-5m3 3h5',
    skin:'M7 4h10l4 8-4 8H7l-4-8zM9 9h.1M15 9h.1M9 15h.1M15 15h.1M12 12h.1',
    book:'M4 4h6l2 2 2-2h6v15h-6l-2 2-2-2H4zM12 6v15',
    chat:'M21 11a9 9 0 0 1-9 9H4l-2 2V11a9 9 0 0 1 19 0ZM7 10h10M7 14h6',
    cart:'M3 3h2l3 13h10l3-9H6M9 21h.1M17 21h.1',
    upload:'M12 16V3m-5 5 5-5 5 5M4 15v6h16v-6',
    download:'M12 3v13m-5-5 5 5 5-5M4 17v4h16v-4',
    check:'m5 12 4 4 10-10',
    info:'M12 11v6M12 7h.1M21 12a9 9 0 1 1-18 0 9 9 0 0 1 18 0',
    chart:'M4 3v17h17M8 15v-4M13 15V7M18 15V4',
    database:'M20 6c0 2-4 3-8 3S4 8 4 6s4-3 8-3 8 1 8 3ZM4 6v12c0 2 4 3 8 3s8-1 8-3V6M4 12c0 2 4 3 8 3s8-1 8-3',
    flow:'M5 3h14v5H5zM3 16h6v5H3zM15 16h6v5h-6zM12 8v4M6 16v-4h12v4',
    people:'M9 10a4 4 0 1 0 0-8 4 4 0 0 0 0 8ZM2 21v-3a7 7 0 0 1 14 0v3M17 3a4 4 0 0 1 0 8M22 21v-3a6 6 0 0 0-3-5',
    clock:'M12 7v5l4 2M21 12a9 9 0 1 1-18 0 9 9 0 0 1 18 0',
    warning:'m12 3 10 18H2zM12 9v5M12 17h.1',
    user:'M16 7a4 4 0 1 1-8 0 4 4 0 0 1 8 0ZM4 21v-3a8 8 0 0 1 16 0v3',
    camera:'M3 6h5l2-3h4l2 3h5v15H3zM16 13a4 4 0 1 1-8 0 4 4 0 0 1 8 0'
  };
  const icon = name => `<svg class="icon" viewBox="0 0 24 24" aria-hidden="true"><path d="${paths[name] || paths.info}"/></svg>`;
  const esc = value => String(value ?? '').replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));

window.HealthUI = { icon, esc };
})();
