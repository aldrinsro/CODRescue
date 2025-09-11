// ================== PAGINATION INTELLIGENTE (Superpreparation - Réutilisable) ==================
// Wrapped in IIFE to prevent variable conflicts when script is loaded multiple times
(function() {
  'use strict';

  // Variables d'état (scopées au module)
  let spCurrentPage = 1;
  let spItemsPerPage = 10;
  const SP_MAX_PER_PAGE = 100;
  let spAllItems = [];
  let spFilteredItems = [];

  // Initialisation (à appeler manuellement si besoin)
  function initSmartPaginationSuperprep(options) {
    const opts = options || {};
    const selector = opts.selector || 'tbody tr, .commande-card';
    const container = document.querySelector(opts.containerSelector || 'table, #table-view, #grid-view');
    if (!container) return;

    collectSuperprepItems(selector, !!opts.mixedViews);
    if (spAllItems.length === 0) return;

    const requestedPerPage = String(opts.defaultPerPage || '10');
    if (requestedPerPage === 'all') {
      spItemsPerPage = spAllItems.length;
    } else {
      const numeric = Number(requestedPerPage) || 10;
      spItemsPerPage = Math.min(numeric, SP_MAX_PER_PAGE);
    }
    spCurrentPage = 1;

    createSuperprepPaginationControls(container, opts.styles || {});
    spShowPage(1);
  }

  function collectSuperprepItems(selector, mixedViews) {
    const nodes = document.querySelectorAll(selector);
    spAllItems = Array.from(nodes).map(el => ({ element: el, data: el.dataset }));
    spFilteredItems = [...spAllItems];
  }

  function createSuperprepPaginationControls(anchorEl, styles) {
    if (document.getElementById('spPaginationControls')) return;

    const s = styles || {};
    const wrap = document.createElement('div');
    wrap.id = 'spPaginationControls';
    wrap.className = 'flex items-center justify-between mt-6 px-6 py-4 bg-white rounded-xl shadow-md border';
    if (s.borderColor) wrap.style.borderColor = s.borderColor;

    const info = document.createElement('div');
    info.className = 'flex items-center text-sm';
    info.style.color = s.textColor || '#374151';
    info.innerHTML = `<i class="fas fa-info-circle mr-2"></i>
      <span id="spPaginationInfo"></span>`;

    const ctrls = document.createElement('div');
    ctrls.className = 'flex items-center space-x-2';

    const prev = document.createElement('button');
    prev.id = 'spPrev';
    prev.className = 'px-4 py-2 text-sm font-medium rounded-lg transition-all duration-300 shadow-sm hover:shadow-md transform hover:scale-105 disabled:opacity-50 disabled:cursor-not-allowed disabled:transform-none';
    prev.style.backgroundColor = s.btnBg || '#f3f4f6';
    prev.style.color = s.btnText || '#374151';
    prev.style.border = `1px solid ${s.btnBorder || '#e5e7eb'}`;
    prev.innerHTML = '<i class="fas fa-chevron-left mr-2"></i>Précédent';
    prev.onclick = () => spShowPage(spCurrentPage - 1);

    const nums = document.createElement('div');
    nums.id = 'spPageNumbers';
    nums.className = 'flex items-center space-x-1';

    const next = document.createElement('button');
    next.id = 'spNext';
    next.className = 'px-4 py-2 text-sm font-medium rounded-lg transition-all duration-300 shadow-sm hover:shadow-md transform hover:scale-105 disabled:opacity-50 disabled:cursor-not-allowed disabled:transform-none';
    next.style.backgroundColor = s.btnBg || '#f3f4f6';
    next.style.color = s.btnText || '#374151';
    next.style.border = `1px solid ${s.btnBorder || '#e5e7eb'}`;
    next.innerHTML = 'Suivant<i class="fas fa-chevron-right ml-2"></i>';
    next.onclick = () => spShowPage(spCurrentPage + 1);

    const perPage = document.createElement('select');
    perPage.id = 'spItemsPerPage';
    perPage.className = 'px-3 py-2 text-sm rounded-lg transition-all duration-300 focus:ring-2 focus:ring-opacity-50';
    perPage.style.borderColor = s.selectBorder || '#e5e7eb';
    perPage.style.backgroundColor = s.selectBg || '#f9fafb';
    perPage.style.color = s.selectText || '#374151';
    perPage.innerHTML = `
      <option value="5">5 par page</option>
      <option value="10">10 par page</option>
      <option value="20">20 par page</option>
      <option value="50">50 par page</option>
      <option value="100">100 par page</option>
      <option value="all">Tous</option>
    `;
    // Déterminer la valeur affichée
    perPage.value = (spItemsPerPage >= spAllItems.length) ? 'all' : String(spItemsPerPage);
    perPage.onchange = (e) => {
      const val = String(e.target.value);
      if (val === 'all') {
        spItemsPerPage = spAllItems.length;
      } else {
        const numeric = parseInt(val, 10) || 10;
        spItemsPerPage = Math.min(numeric, SP_MAX_PER_PAGE);
      }
      spCurrentPage = 1;
      spShowPage(1);
    };

    const sep = document.createElement('span');
    sep.className = 'mx-3';
    sep.style.color = s.sepColor || '#d1d5db';
    sep.textContent = '|';

    ctrls.appendChild(prev);
    ctrls.appendChild(nums);
    ctrls.appendChild(next);
    ctrls.appendChild(sep);
    ctrls.appendChild(perPage);

    wrap.appendChild(info);
    wrap.appendChild(ctrls);

    anchorEl.parentNode.insertBefore(wrap, anchorEl.nextSibling);
  }

  function spRelocateControls(containerSelector) {
    const controls = document.getElementById('spPaginationControls');
    const anchorEl = typeof containerSelector === 'string' ? document.querySelector(containerSelector) : containerSelector;
    if (!controls || !anchorEl || !anchorEl.parentNode) return;
    anchorEl.parentNode.insertBefore(controls, anchorEl.nextSibling);
  }

  function spShowPage(page) {
    const total = Math.ceil(spFilteredItems.length / spItemsPerPage) || 1;
    if (page < 1) page = 1;
    if (page > total) page = total;
    spCurrentPage = page;

    spAllItems.forEach(it => { it.element.style.display = 'none'; });
    const start = (page - 1) * spItemsPerPage;
    const end = Math.min(start + spItemsPerPage, spFilteredItems.length);
    for (let i = start; i < end; i++) {
      if (spFilteredItems[i]) spFilteredItems[i].element.style.display = '';
    }
    spUpdateControls();
  }

  function spUpdateControls() {
    const totalPages = Math.ceil(spFilteredItems.length / spItemsPerPage) || 1;
    const start = spFilteredItems.length === 0 ? 0 : (spCurrentPage - 1) * spItemsPerPage + 1;
    const end = Math.min(spCurrentPage * spItemsPerPage, spFilteredItems.length);

    const info = document.getElementById('spPaginationInfo');
    if (info) info.textContent = spFilteredItems.length === 0 ? 'Aucun élément à afficher' : `Affichage de ${start} à ${end} sur ${spFilteredItems.length} éléments`;

    const prev = document.getElementById('spPrev');
    const next = document.getElementById('spNext');
    if (prev) prev.disabled = spCurrentPage === 1;
    if (next) next.disabled = spCurrentPage === totalPages || totalPages === 0;

    spRenderPageNumbers(totalPages);
  }

  function spRenderPageNumbers(totalPages) {
    const cont = document.getElementById('spPageNumbers');
    if (!cont) return;
    cont.innerHTML = '';
    if (totalPages <= 1) return;

    const maxVisible = 5;
    let start = Math.max(1, spCurrentPage - Math.floor(maxVisible / 2));
    let end = Math.min(totalPages, start + maxVisible - 1);
    if (end - start + 1 < maxVisible) start = Math.max(1, end - maxVisible + 1);

    if (start > 1) {
      cont.appendChild(spCreatePageBtn(1, spCurrentPage === 1));
      if (start > 2) cont.appendChild(spEllipsis());
    }
    for (let i = start; i <= end; i++) cont.appendChild(spCreatePageBtn(i, spCurrentPage === i));
    if (end < totalPages) {
      if (end < totalPages - 1) cont.appendChild(spEllipsis());
      cont.appendChild(spCreatePageBtn(totalPages, spCurrentPage === totalPages));
    }
  }

  function spCreatePageBtn(num, active) {
    const b = document.createElement('button');
    b.className = 'px-3 py-2 text-sm font-medium rounded-lg transition-all duration-300 shadow-sm hover:shadow-md transform hover:scale-105';
    if (active) {
      b.style.background = 'linear-gradient(135deg, #070F2B, #0b183a)';
      b.style.color = '#fff';
      b.style.border = '1px solid #070F2B';
    } else {
      b.style.backgroundColor = '#f3f4f6';
      b.style.color = '#374151';
      b.style.border = '1px solid #e5e7eb';
    }
    b.textContent = String(num);
    b.onclick = () => spShowPage(num);
    return b;
  }

  function spEllipsis() {
    const s = document.createElement('span');
    s.className = 'px-2 py-1';
    s.style.color = '#9ca3af';
    s.textContent = '...';
    return s;
  }

  // API publique pour intégration avec la recherche
  function spFilterItems(newList) {
    spFilteredItems = newList && Array.isArray(newList) ? newList : [...spAllItems];
    spCurrentPage = 1;
    spShowPage(1);
  }

  function spResetPagination() {
    spFilteredItems = [...spAllItems];
    spCurrentPage = 1;
    spShowPage(1);
  }

  function spUpdateTotalFromDom(selector) {
    collectSuperprepItems(selector || 'tbody tr, .commande-card');
    spUpdateControls();
  }

  // Exposer globalement
  window.SuperprepSmartPagination = {
    init: initSmartPaginationSuperprep,
    filterItems: spFilterItems,
    reset: spResetPagination,
    showPage: spShowPage,
    updateTotalFromDom: spUpdateTotalFromDom,
    getState: () => ({ currentPage: spCurrentPage, itemsPerPage: spItemsPerPage, total: spFilteredItems.length }),
    relocate: spRelocateControls
  };

  // Auto-init optionnel si attribut data-superprep-pagination présent
  document.addEventListener('DOMContentLoaded', function() {
    const auto = document.querySelector('[data-superprep-pagination]');
    if (auto) initSmartPaginationSuperprep({
      selector: auto.getAttribute('data-items-selector') || 'tbody tr, .commande-card',
      containerSelector: auto.getAttribute('data-container-selector') || 'table, #table-view, #grid-view',
      defaultPerPage: parseInt(auto.getAttribute('data-per-page') || '10', 10),
      mixedViews: auto.hasAttribute('data-mixed-views')
    });
  });

})();