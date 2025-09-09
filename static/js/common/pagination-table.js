// Pagination de tableau réutilisable - Basée sur la pagination du dashboard
// API: window.createSmartTablePagination(options)
// options: { tableSelector, rowSelector, perPageOptions:number[], defaultPerPage:number }

(function() {
  function createSmartTablePagination(options) {
    const table = document.querySelector(options.tableSelector || 'table');
    if (!table) {
      console.error('❌ [PAGINATION] Tableau introuvable:', options.tableSelector);
      return null;
    }

    const rowSelector = options.rowSelector || 'tbody tr';
    const perPageOptions = options.perPageOptions || [10, 12, 25, 50, 100];
    let itemsPerPage = options.defaultPerPage || perPageOptions[0] || 10;

    let allRows = [];
    let filteredRows = [];
    let currentPage = 1;
    let totalItems = 0;

    function collectRows() {
      const rows = table.querySelectorAll(rowSelector);
      allRows = Array.from(rows).map((el, idx) => ({ element: el, index: idx }));
      filteredRows = [...allRows];
      totalItems = allRows.length;
      console.log(`📋 [PAGINATION] ${totalItems} lignes collectées avec le sélecteur "${rowSelector}"`);
    }

    function createControls() {
      // Vérifier si les contrôles existent déjà
      if (document.getElementById('smartTablePaginationControls')) {
        return;
      }

      console.log('🎛️ [PAGINATION] Création des contrôles de pagination');

      // Créer le conteneur de pagination avec le thème uniforme
      const paginationContainer = document.createElement('div');
      paginationContainer.id = 'smartTablePaginationControls';
      paginationContainer.className = 'flex items-center justify-between mt-6 px-6 py-4 bg-white rounded-xl shadow-lg border border-gray-200';

      // Informations sur les éléments
      const infoContainer = document.createElement('div');
      infoContainer.className = 'flex items-center text-sm text-gray-600';
      infoContainer.innerHTML = `
        <i class="fas fa-info-circle mr-2 text-gray-500"></i>
        <span id="smartTablePaginationInfo">Affichage de 1 à ${Math.min(itemsPerPage, totalItems)} sur ${totalItems} éléments</span>
      `;

      // Contrôles de pagination
      const controlsContainer = document.createElement('div');
      controlsContainer.className = 'flex items-center space-x-2';

      // Bouton précédent
      const prevButton = document.createElement('button');
      prevButton.id = 'smartTablePrevPage';
      prevButton.className = 'px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-md hover:bg-gray-100 hover:border-gray-400 hover:text-gray-900 disabled:opacity-50 disabled:cursor-not-allowed transition-colors';
      prevButton.innerHTML = '<i class="fas fa-chevron-left mr-1"></i>Précédent';
      prevButton.addEventListener('click', () => {
        if (currentPage > 1) {
          showPage(currentPage - 1);
        }
      });

      // Numéros de page
      const pageNumbersContainer = document.createElement('div');
      pageNumbersContainer.id = 'smartTablePageNumbers';
      pageNumbersContainer.className = 'flex items-center space-x-1';

      // Bouton suivant
      const nextButton = document.createElement('button');
      nextButton.id = 'smartTableNextPage';
      nextButton.className = 'px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-md hover:bg-gray-100 hover:border-gray-400 hover:text-gray-900 disabled:opacity-50 disabled:cursor-not-allowed transition-colors';
      nextButton.innerHTML = 'Suivant<i class="fas fa-chevron-right ml-1"></i>';
      nextButton.addEventListener('click', () => {
        const totalPages = Math.ceil(filteredRows.length / itemsPerPage);
        if (currentPage < totalPages) {
          showPage(currentPage + 1);
        }
      });

      // Séparateur
      const separator = document.createElement('div');
      separator.className = 'mx-2 text-gray-400';
      separator.innerHTML = '|';

      // Sélecteur d'éléments par page
      const itemsPerPageSelect = document.createElement('select');
      itemsPerPageSelect.id = 'smartTableItemsPerPageSelect';
      itemsPerPageSelect.className = 'theme-input text-sm';
      itemsPerPageSelect.innerHTML = perPageOptions.map(v => 
        `<option value="${v}" ${v === itemsPerPage ? 'selected' : ''}>${v} par page</option>`
      ).join('');
      itemsPerPageSelect.addEventListener('change', (e) => {
        itemsPerPage = parseInt(e.target.value);
        currentPage = 1;
        showPage(1);
      });

      // Assembler les contrôles
      controlsContainer.appendChild(prevButton);
      controlsContainer.appendChild(pageNumbersContainer);
      controlsContainer.appendChild(nextButton);
      controlsContainer.appendChild(separator);
      controlsContainer.appendChild(itemsPerPageSelect);

      // Assembler le conteneur principal
      paginationContainer.appendChild(infoContainer);
      paginationContainer.appendChild(controlsContainer);

      // Insérer après le tableau
      const tableContainer = table.closest('div');
      if (tableContainer && tableContainer.parentNode) {
        tableContainer.parentNode.insertBefore(paginationContainer, tableContainer.nextSibling);
        console.log('✅ [PAGINATION] Contrôles de pagination insérés');
      } else if (table.parentNode) {
        table.parentNode.insertBefore(paginationContainer, table.nextSibling);
        console.log('✅ [PAGINATION] Contrôles de pagination insérés (fallback)');
      } else {
        console.error('❌ [PAGINATION] Impossible d\'insérer les contrôles: tableau introuvable');
      }
    }

    function showPage(page) {
      const totalPages = Math.ceil(filteredRows.length / itemsPerPage);
      
      if (page < 1 || page > totalPages) {
        return;
      }
      
      currentPage = page;
      
      console.log(`📄 [PAGINATION] Affichage de la page ${page}/${totalPages}`);
      
      // Masquer toutes les lignes
      allRows.forEach(row => {
        row.element.style.display = 'none';
        row.element.style.opacity = '0';
        row.element.style.transform = 'translateY(20px)';
      });
      
      // Calculer les indices de début et fin
      const startIndex = (page - 1) * itemsPerPage;
      const endIndex = Math.min(startIndex + itemsPerPage, filteredRows.length);
      
      // Afficher les lignes de la page courante
      for (let i = startIndex; i < endIndex; i++) {
        const row = filteredRows[i];
        row.element.style.display = '';
        row.element.style.opacity = '1';
        row.element.style.transform = 'translateY(0)';
      }
      
      // Mettre à jour les contrôles
      updateControls();
    }

    function updateControls() {
      const totalPages = Math.ceil(filteredRows.length / itemsPerPage);
      const startIndex = (currentPage - 1) * itemsPerPage + 1;
      const endIndex = Math.min(currentPage * itemsPerPage, filteredRows.length);

      // Mettre à jour les informations
      const info = document.getElementById('smartTablePaginationInfo');
      if (info) {
        info.textContent = filteredRows.length === 0
          ? 'Aucun élément à afficher'
          : `Affichage de ${startIndex} à ${endIndex} sur ${filteredRows.length} éléments`;
      }

      // Mettre à jour les boutons de navigation
      const prevButton = document.getElementById('smartTablePrevPage');
      const nextButton = document.getElementById('smartTableNextPage');
      
      if (prevButton) {
        prevButton.disabled = currentPage <= 1;
      }
      if (nextButton) {
        nextButton.disabled = currentPage >= totalPages;
      }

      // Mettre à jour les numéros de page
      updatePageNumbers(totalPages);

      console.log(`📊 [PAGINATION] ${startIndex}-${endIndex} sur ${filteredRows.length} éléments (page ${currentPage}/${totalPages})`);
    }

    function updatePageNumbers(totalPages) {
      const pageNumbersContainer = document.getElementById('smartTablePageNumbers');
      if (!pageNumbersContainer) return;

      pageNumbersContainer.innerHTML = '';

      if (totalPages <= 1) return;

      const maxVisiblePages = 5;
      let startPage = Math.max(1, currentPage - Math.floor(maxVisiblePages / 2));
      let endPage = Math.min(totalPages, startPage + maxVisiblePages - 1);

      if (endPage - startPage + 1 < maxVisiblePages) {
        startPage = Math.max(1, endPage - maxVisiblePages + 1);
      }

      // Bouton première page
      if (startPage > 1) {
        const firstPageBtn = createPageButton(1, '1');
        pageNumbersContainer.appendChild(firstPageBtn);
        
        if (startPage > 2) {
          pageNumbersContainer.appendChild(createEllipsis());
        }
      }

      // Pages visibles
      for (let i = startPage; i <= endPage; i++) {
        const pageBtn = createPageButton(i, i.toString());
        if (i === currentPage) {
          pageBtn.className = 'px-3 py-1 text-sm font-medium rounded-md transition-colors bg-gray-800 text-white border border-gray-800';
        }
        pageNumbersContainer.appendChild(pageBtn);
      }

      // Bouton dernière page
      if (endPage < totalPages) {
        if (endPage < totalPages - 1) {
          pageNumbersContainer.appendChild(createEllipsis());
        }
        
        const lastPageBtn = createPageButton(totalPages, totalPages.toString());
        pageNumbersContainer.appendChild(lastPageBtn);
      }
    }

    function createPageButton(pageNum, text) {
      const button = document.createElement('button');
      button.className = 'px-3 py-1 text-sm font-medium rounded-md transition-colors text-gray-700 bg-white border border-gray-300 hover:bg-gray-50 hover:border-gray-400';
      button.textContent = text;
      button.addEventListener('click', () => showPage(pageNum));
      return button;
    }

    function createEllipsis() {
      const ellipsis = document.createElement('span');
      ellipsis.className = 'px-2 text-gray-500';
      ellipsis.textContent = '...';
      return ellipsis;
    }

    function recomputeFilteredFromDOM() {
      // Si des filtres client ont masqué des lignes, se baser sur la visibilité
      filteredRows = allRows.filter(r => r.element.style.display !== 'none');
      // Si toutes les lignes sont masquées (ex. état initial), retomber sur toutes
      if (filteredRows.length === 0) filteredRows = [...allRows];
    }

    function init() {
      collectRows();
      if (allRows.length === 0) {
        console.warn('⚠️ [PAGINATION] Aucune ligne trouvée');
        return null;
      }
      createControls();
      showPage(1);
      console.log(`✅ [PAGINATION] Initialisée: ${allRows.length} éléments, ${itemsPerPage} par page`);
      
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
      itemsPerPage = n; 
      currentPage = 1; 
      showPage(1);
    }

    const api = {
      init,
      showPage,
      setItemsPerPage,
      refresh: () => { collectRows(); showPage(1); },
      getStats: () => ({
        currentPage,
        totalPages: Math.ceil(filteredRows.length / itemsPerPage),
        itemsPerPage,
        totalItems: allRows.length,
        filteredItems: filteredRows.length,
        startIndex: (currentPage - 1) * itemsPerPage + 1,
        endIndex: Math.min(currentPage * itemsPerPage, filteredRows.length)
      })
    };

    const instance = init();
    if (instance) { 
      window.smartTablePagination = api; 
    }
    return instance;
  }

  window.createSmartTablePagination = createSmartTablePagination;
})();