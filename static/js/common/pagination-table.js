// Pagination de tableau réutilisable
// API: window.createSmartTablePagination(options)
// options: { tableSelector, rowSelector, perPageOptions:number[], defaultPerPage:number }

(function() {
  function createSmartTablePagination(options) {
    const table = document.querySelector(options.tableSelector || 'table');
    if (!table) return null;

    const rowSelector = options.rowSelector || 'tbody tr';
    const perPageOptions = options.perPageOptions || [10, 12, 25, 50, 100];
    let itemsPerPage = options.defaultPerPage || perPageOptions[0] || 10;

    let allRows = [];
    let filteredRows = [];
    let currentPage = 1;

    function collectRows() {
      const rows = table.querySelectorAll(rowSelector);
      allRows = Array.from(rows).map((el, idx) => ({ element: el, index: idx }));
      filteredRows = [...allRows];
    }

    function createControls() {
      if (document.getElementById('smartTablePaginationControls')) return;

      const container = document.createElement('div');
      container.id = 'smartTablePaginationControls';
      container.className = 'flex items-center justify-between mt-4 px-4 py-3 bg-white rounded-xl shadow border border-gray-200';

      const info = document.createElement('div');
      info.className = 'text-sm text-gray-600';
      info.innerHTML = '<i class="fas fa-info-circle mr-2 text-gray-500"></i><span id="smartTablePaginationInfo"></span>';

      const controls = document.createElement('div');
      controls.className = 'flex items-center space-x-2';

      const prev = document.createElement('button');
      prev.className = 'px-3 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-md hover:bg-gray-100 disabled:opacity-50 disabled:cursor-not-allowed';
      prev.innerHTML = '<i class="fas fa-chevron-left mr-1"></i>Précédent';
      prev.addEventListener('click', () => { if (currentPage > 1) showPage(currentPage - 1); });

      const pages = document.createElement('div');
      pages.id = 'smartTablePageNumbers';
      pages.className = 'flex items-center space-x-1';

      const next = document.createElement('button');
      next.className = 'px-3 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-md hover:bg-gray-100 disabled:opacity-50 disabled:cursor-not-allowed';
      next.innerHTML = 'Suivant<i class="fas fa-chevron-right ml-1"></i>';
      next.addEventListener('click', () => {
        const totalPages = Math.ceil(filteredRows.length / itemsPerPage);
        if (currentPage < totalPages) showPage(currentPage + 1);
      });

      const sep = document.createElement('div');
      sep.className = 'mx-2 text-gray-400';
      sep.textContent = '|';

      const select = document.createElement('select');
      select.className = 'theme-input text-sm';
      select.innerHTML = perPageOptions.map(v => `<option value="${v}" ${v===itemsPerPage?'selected':''}>${v} par page</option>`).join('');
      select.addEventListener('change', e => { itemsPerPage = parseInt(e.target.value); currentPage = 1; showPage(1); });

      controls.appendChild(prev);
      controls.appendChild(pages);
      controls.appendChild(next);
      controls.appendChild(sep);
      controls.appendChild(select);

      container.appendChild(info);
      container.appendChild(controls);

      const afterNode = table.closest('div') || table;
      if (afterNode && afterNode.parentNode) {
        afterNode.parentNode.insertBefore(container, afterNode.nextSibling);
      }
    }

    function recomputeFilteredFromDOM() {
      // Si des filtres client ont masqué des lignes, se baser sur la visibilité
      filteredRows = allRows.filter(r => r.element.style.display !== 'none');
      // Si toutes les lignes sont masquées (ex. état initial), retomber sur toutes
      if (filteredRows.length === 0) filteredRows = [...allRows];
    }

    function showPage(page) {
      recomputeFilteredFromDOM();
      const totalPages = Math.ceil(filteredRows.length / itemsPerPage);
      if (page < 1 || page > totalPages) return;
      currentPage = page;

      allRows.forEach(r => { r.element.style.display = 'none'; });
      const start = (page - 1) * itemsPerPage;
      const end = Math.min(start + itemsPerPage, filteredRows.length);
      for (let i = start; i < end; i++) {
        filteredRows[i].element.style.display = '';
      }
      updateControls();
    }

    function updateControls() {
      recomputeFilteredFromDOM();
      const totalPages = Math.ceil(filteredRows.length / itemsPerPage);
      const startIndex = (currentPage - 1) * itemsPerPage + 1;
      const endIndex = Math.min(currentPage * itemsPerPage, filteredRows.length);

      const info = document.getElementById('smartTablePaginationInfo');
      if (info) {
        info.textContent = filteredRows.length === 0
          ? 'Aucun élément à afficher'
          : `Affichage de ${startIndex} à ${endIndex} sur ${filteredRows.length} éléments`;
      }

      const pageNums = document.getElementById('smartTablePageNumbers');
      if (pageNums) {
        pageNums.innerHTML = '';
        if (totalPages > 1) {
          const maxVisible = 5;
          let s = Math.max(1, currentPage - Math.floor(maxVisible / 2));
          let e = Math.min(totalPages, s + maxVisible - 1);
          if (e - s + 1 < maxVisible) s = Math.max(1, e - maxVisible + 1);
          if (s > 1) { pageNums.appendChild(pageBtn(1, currentPage===1)); if (s>2) pageNums.appendChild(ellipsis()); }
          for (let i=s;i<=e;i++) pageNums.appendChild(pageBtn(i, currentPage===i));
          if (e < totalPages) { if (e<totalPages-1) pageNums.appendChild(ellipsis()); pageNums.appendChild(pageBtn(totalPages, currentPage===totalPages)); }
        }
      }
    }

    function pageBtn(n, active) {
      const b = document.createElement('button');
      b.className = `px-3 py-1 text-sm font-medium rounded-md ${active ? 'bg-gray-800 text-white border border-gray-800' : 'text-gray-700 bg-white border border-gray-300 hover:bg-gray-50 hover:border-gray-400'}`;
      b.textContent = n;
      b.addEventListener('click', () => showPage(n));
      return b;
    }

    function ellipsis() {
      const s = document.createElement('span');
      s.className = 'px-2 text-gray-500';
      s.textContent = '...';
      return s;
    }

    function init() {
      collectRows();
      if (allRows.length === 0) return null;
      createControls();
      showPage(1);
      // Observer les changements de lignes (AJAX / rerender)
      const tbody = table.querySelector('tbody');
      if (tbody && window.MutationObserver) {
        const observer = new MutationObserver(() => {
          collectRows();
          showPage(1);
        });
        observer.observe(tbody, { childList: true });
      }
      return api;
    }

    function setItemsPerPage(n) {
      itemsPerPage = n; currentPage = 1; showPage(1);
    }

    const api = {
      init,
      showPage,
      setItemsPerPage,
      refresh: () => { collectRows(); showPage(1); },
      getStats: () => ({ currentPage, totalPages: Math.ceil(filteredRows.length / itemsPerPage), itemsPerPage, totalItems: allRows.length, filteredItems: filteredRows.length })
    };

    const instance = init();
    if (instance) { window.smartTablePagination = api; }
    return instance;
  }

  window.createSmartTablePagination = createSmartTablePagination;
})();

console.log('✅ [SMART TABLE PAGINATION] Module chargé');


