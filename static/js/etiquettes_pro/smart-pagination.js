// ================== PAGINATION INTELLIGENTE POUR ÉTIQUETTES ==================

// Variables globales pour la pagination
let currentPage = 1;
let itemsPerPage = 12;  // 12 tickets par page par défaut (4 lignes de 3 cartes)
let totalItems = 0;
let allItems = [];
let filteredItems = [];

// Initialisation de la pagination
document.addEventListener('DOMContentLoaded', function() {
    // Délai pour s'assurer que tous les éléments sont chargés
    setTimeout(() => {
        initializePagination();
    }, 100);
});

// Initialiser la pagination
function initializePagination() {
    console.log('🔧 [PAGINATION-ÉTIQUETTES] Initialisation de la pagination intelligente');
    
    // Collecter tous les éléments
    collectAllItems();
    
    // Vérifier s'il y a des éléments à paginer
    if (allItems.length === 0) {
        console.log('⚠️ [PAGINATION-ÉTIQUETTES] Aucun élément trouvé pour la pagination');
        return;
    }
    
    console.log(`✅ [PAGINATION-ÉTIQUETTES] ${totalItems} éléments collectés`);
    
    // Créer les contrôles de pagination
    createPaginationControls();
    
    // Afficher la première page
    showPage(1);
}

// Collecter tous les éléments pour la pagination
function collectAllItems() {
    console.log('🔍 [PAGINATION-ÉTIQUETTES] Collecte des éléments...');
    
    // Sélecteur pour les cartes d'étiquettes
    const etiquetteCards = document.querySelectorAll('.etiquette-card');
    
    allItems = Array.from(etiquetteCards).map((card, index) => {
        return {
            element: card,
            index: index,
            reference: card.querySelector('.etiquette-reference')?.textContent?.trim() || '',
            template: card.querySelector('.etiquette-template')?.textContent?.trim() || '',
            statut: card.querySelector('.etiquette-statut')?.textContent?.trim() || '',
            date: card.querySelector('.etiquette-date')?.textContent?.trim() || '',
            commande: card.querySelector('.etiquette-commande')?.textContent?.trim() || '',
            client: card.querySelector('.etiquette-client')?.textContent?.trim() || ''
        };
    });
    
    totalItems = allItems.length;
    filteredItems = [...allItems];
    
    console.log(`📊 [PAGINATION-ÉTIQUETTES] ${totalItems} étiquettes collectées`);
}

// Créer les contrôles de pagination
function createPaginationControls() {
    // Vérifier si les contrôles existent déjà
    if (document.getElementById('paginationControls')) {
        return;
    }
    
    console.log('🎛️ [PAGINATION-ÉTIQUETTES] Création des contrôles de pagination');
    
    // Créer le conteneur de pagination avec le thème uniforme
    const paginationContainer = document.createElement('div');
    paginationContainer.id = 'paginationControls';
    paginationContainer.className = 'flex items-center justify-between mt-6 px-6 py-4 bg-white rounded-xl shadow-lg border border-gray-200';
    
    // Informations sur les éléments
    const infoContainer = document.createElement('div');
    infoContainer.className = 'flex items-center text-sm text-gray-600';
    infoContainer.innerHTML = `
        <i class="fas fa-info-circle mr-2 text-gray-500"></i>
        <span id="paginationInfo">Affichage de 1 à ${Math.min(itemsPerPage, totalItems)} sur ${totalItems} étiquettes</span>
    `;
    
    // Contrôles de pagination
    const controlsContainer = document.createElement('div');
    controlsContainer.className = 'flex items-center space-x-2';
    
    // Bouton précédent
    const prevButton = document.createElement('button');
    prevButton.id = 'prevPage';
    prevButton.className = 'px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-md hover:bg-gray-100 hover:border-gray-400 hover:text-gray-900 disabled:opacity-50 disabled:cursor-not-allowed transition-colors';
    prevButton.innerHTML = '<i class="fas fa-chevron-left mr-1"></i>Précédent';
    prevButton.addEventListener('click', () => {
        if (currentPage > 1) {
            showPage(currentPage - 1);
        }
    });
    
    // Numéros de page
    const pageNumbersContainer = document.createElement('div');
    pageNumbersContainer.id = 'pageNumbers';
    pageNumbersContainer.className = 'flex items-center space-x-1';
    
    // Bouton suivant
    const nextButton = document.createElement('button');
    nextButton.id = 'nextPage';
    nextButton.className = 'px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-md hover:bg-gray-100 hover:border-gray-400 hover:text-gray-900 disabled:opacity-50 disabled:cursor-not-allowed transition-colors';
    nextButton.innerHTML = 'Suivant<i class="fas fa-chevron-right ml-1"></i>';
    nextButton.addEventListener('click', () => {
        const totalPages = Math.ceil(filteredItems.length / itemsPerPage);
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
    itemsPerPageSelect.id = 'itemsPerPageSelect';
    itemsPerPageSelect.className = 'theme-input text-sm';
    itemsPerPageSelect.innerHTML = `
        <option value="6">6 par page</option>
        <option value="9">9 par page</option>
        <option value="12" selected>12 par page</option>
        <option value="15">15 par page</option>
        <option value="18">18 par page</option>
        <option value="21">21 par page</option>
        <option value="24">24 par page</option>
    `;
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
    
    // Insérer après le conteneur des étiquettes
    const etiquettesContainer = document.querySelector('.etiquettes-grid') || document.querySelector('.grid') || document.querySelector('#etiquettes-container');
    if (etiquettesContainer) {
        etiquettesContainer.parentNode.insertBefore(paginationContainer, etiquettesContainer.nextSibling);
        console.log('✅ [PAGINATION-ÉTIQUETTES] Contrôles de pagination insérés');
    } else {
        console.error('❌ [PAGINATION-ÉTIQUETTES] Conteneur des étiquettes non trouvé');
    }
}

// Afficher une page spécifique
function showPage(page) {
    const totalPages = Math.ceil(filteredItems.length / itemsPerPage);
    
    if (page < 1 || page > totalPages) {
        return;
    }
    
    currentPage = page;
    
    console.log(`📄 [PAGINATION-ÉTIQUETTES] Affichage de la page ${page}/${totalPages}`);
    
    // Masquer tous les éléments
    allItems.forEach(item => {
        item.element.style.display = 'none';
        item.element.style.opacity = '0';
        item.element.style.transform = 'translateY(20px)';
    });
    
    // Calculer les indices de début et fin
    const startIndex = (page - 1) * itemsPerPage;
    const endIndex = Math.min(startIndex + itemsPerPage, filteredItems.length);
    
    // Afficher les éléments de la page courante
    for (let i = startIndex; i < endIndex; i++) {
        const item = filteredItems[i];
        item.element.style.display = '';
        item.element.style.opacity = '1';
        item.element.style.transform = 'translateY(0)';
    }
    
    // Mettre à jour les contrôles
    updatePaginationControls();
    
    // Animation d'apparition
    animatePageItems(startIndex, endIndex);
}

// Mettre à jour les contrôles de pagination
function updatePaginationControls() {
    const totalPages = Math.ceil(filteredItems.length / itemsPerPage);
    const startIndex = (currentPage - 1) * itemsPerPage + 1;
    const endIndex = Math.min(currentPage * itemsPerPage, filteredItems.length);
    
    // Mettre à jour les informations
    const infoElement = document.getElementById('paginationInfo');
    if (infoElement) {
        if (filteredItems.length === 0) {
            infoElement.textContent = 'Aucune étiquette à afficher';
        } else {
            infoElement.textContent = `Affichage de ${startIndex} à ${endIndex} sur ${filteredItems.length} étiquettes`;
        }
    }
    
    // Mettre à jour les boutons précédent/suivant
    const prevButton = document.getElementById('prevPage');
    const nextButton = document.getElementById('nextPage');
    
    if (prevButton) {
        prevButton.disabled = currentPage === 1;
    }
    if (nextButton) {
        nextButton.disabled = currentPage === totalPages || totalPages === 0;
    }
    
    // Mettre à jour les numéros de page
    updatePageNumbers(totalPages);
}

// Mettre à jour les numéros de page
function updatePageNumbers(totalPages) {
    const pageNumbersContainer = document.getElementById('pageNumbers');
    if (!pageNumbersContainer) return;
    
    pageNumbersContainer.innerHTML = '';
    
    if (totalPages <= 1) return;
    
    // Logique de pagination intelligente
    const maxVisiblePages = 5;
    let startPage = Math.max(1, currentPage - Math.floor(maxVisiblePages / 2));
    let endPage = Math.min(totalPages, startPage + maxVisiblePages - 1);
    
    // Ajuster si on est proche de la fin
    if (endPage - startPage + 1 < maxVisiblePages) {
        startPage = Math.max(1, endPage - maxVisiblePages + 1);
    }
    
    // Bouton première page
    if (startPage > 1) {
        const firstButton = createPageButton(1, currentPage === 1);
        pageNumbersContainer.appendChild(firstButton);
        
        if (startPage > 2) {
            const ellipsis = document.createElement('span');
            ellipsis.className = 'px-2 py-1 text-gray-500';
            ellipsis.textContent = '...';
            pageNumbersContainer.appendChild(ellipsis);
        }
    }
    
    // Pages visibles
    for (let i = startPage; i <= endPage; i++) {
        const pageButton = createPageButton(i, currentPage === i);
        pageNumbersContainer.appendChild(pageButton);
    }
    
    // Bouton dernière page
    if (endPage < totalPages) {
        if (endPage < totalPages - 1) {
            const ellipsis = document.createElement('span');
            ellipsis.className = 'px-2 py-1 text-gray-500';
            ellipsis.textContent = '...';
            pageNumbersContainer.appendChild(ellipsis);
        }
        
        const lastButton = createPageButton(totalPages, currentPage === totalPages);
        pageNumbersContainer.appendChild(lastButton);
    }
}

// Créer un bouton de page
function createPageButton(pageNumber, isActive) {
    const button = document.createElement('button');
    button.className = `px-3 py-1 text-sm font-medium rounded-md transition-colors ${
        isActive 
            ? 'bg-gray-800 text-white border border-gray-800' 
            : 'text-gray-700 bg-white border border-gray-300 hover:bg-gray-50 hover:border-gray-400'
    }`;
    button.textContent = pageNumber;
    button.addEventListener('click', () => showPage(pageNumber));
    return button;
}

// Animation des éléments de la page
function animatePageItems(startIndex, endIndex) {
    const itemsToAnimate = filteredItems.slice(startIndex, endIndex);
    
    itemsToAnimate.forEach((item, index) => {
        setTimeout(() => {
            item.element.style.transition = 'all 0.3s ease-out';
            item.element.style.opacity = '1';
            item.element.style.transform = 'translateY(0)';
        }, index * 50); // Délai progressif
    });
}

// Filtrer les éléments
function filterItems(filteredData) {
    console.log('🔍 [PAGINATION-ÉTIQUETTES] Filtrage des éléments');
    filteredItems = filteredData || allItems;
    currentPage = 1;
    showPage(1);
}

// Fonction pour réinitialiser la pagination
function resetPagination() {
    console.log('🔄 [PAGINATION-ÉTIQUETTES] Réinitialisation de la pagination');
    filteredItems = [...allItems];
    currentPage = 1;
    showPage(1);
}

// Fonction pour obtenir les éléments filtrés
function getFilteredItems() {
    return filteredItems;
}

// Fonction pour obtenir les statistiques
function getPaginationStats() {
    return {
        currentPage: currentPage,
        totalPages: Math.ceil(filteredItems.length / itemsPerPage),
        itemsPerPage: itemsPerPage,
        totalItems: totalItems,
        filteredItems: filteredItems.length,
        startIndex: (currentPage - 1) * itemsPerPage + 1,
        endIndex: Math.min(currentPage * itemsPerPage, filteredItems.length)
    };
}

// API publique pour la pagination intelligente
window.smartPaginationEtiquettes = {
    init: initializePagination,
    showPage: showPage,
    filterItems: filterItems,
    resetPagination: resetPagination,
    getFilteredItems: getFilteredItems,
    getStats: getPaginationStats,
    setItemsPerPage: (newItemsPerPage) => {
        itemsPerPage = newItemsPerPage;
        currentPage = 1;
        showPage(1);
    }
};

console.log('✅ [PAGINATION-ÉTIQUETTES] Module de pagination intelligente chargé');
