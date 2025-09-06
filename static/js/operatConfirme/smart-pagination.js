// ================== PAGINATION INTELLIGENTE ==================

// Variables globales pour la pagination
let currentPage = 1;
let itemsPerPage = 10;
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
    // Détecter le type de page
    const isConfirmationPage = document.querySelector('#table-view') !== null;
    const isListeCommandesPage = document.querySelector('table.table-commandes') === null && document.querySelector('tbody') !== null;
    const isCommandesConfirmeesPage = document.querySelector('table.table-commandes') !== null;
    
    // S'assurer que tous les éléments sont visibles par défaut
    const allRows = document.querySelectorAll('tbody tr, .commande-card');
    allRows.forEach(row => {
        row.style.display = '';
    });
    
    // Collecter tous les éléments
    collectAllItems();
    
    // Vérifier s'il y a des éléments à paginer
    if (allItems.length === 0) {
        return;
    }
    
    // Créer les contrôles de pagination
    createPaginationControls();
    
    // Afficher la première page
    showPage(1);
}

// Collecter tous les éléments pour la pagination
function collectAllItems() {
    // Détecter le type de page et les sélecteurs appropriés
    const isConfirmationPage = document.querySelector('#table-view') !== null;
    const isListeCommandesPage = document.querySelector('table.table-commandes') === null && document.querySelector('tbody') !== null;
    const isCommandesConfirmeesPage = document.querySelector('table.table-commandes') !== null;
    
    let tableRows;
    if (isConfirmationPage) {
        tableRows = document.querySelectorAll('#table-view tbody tr, #grid-view .commande-card');
    } else {
        tableRows = document.querySelectorAll('tbody tr');
    }
    
    allItems = Array.from(tableRows).map(row => ({
        element: row,
        data: row.dataset
    }));
    
    totalItems = allItems.length;
    filteredItems = [...allItems];
    
}

// Créer les contrôles de pagination
function createPaginationControls() {
    // Vérifier si les contrôles existent déjà
    if (document.getElementById('paginationControls')) {
        return;
    }
    
    // Créer le conteneur de pagination
    const paginationContainer = document.createElement('div');
    paginationContainer.id = 'paginationControls';
    paginationContainer.className = 'flex items-center justify-between mt-6 px-6 py-4 bg-white rounded-xl shadow-md border';
    paginationContainer.style.borderColor = '#f7d9c4';
    
    // Informations sur les éléments
    const infoContainer = document.createElement('div');
    infoContainer.className = 'flex items-center text-sm';
    infoContainer.style.color = '#4B352A';
    infoContainer.innerHTML = `
        <i class="fas fa-info-circle mr-2" style="color: #6d4b3b;"></i>
        <span id="paginationInfo">Affichage de 1 à ${Math.min(itemsPerPage, totalItems)} sur ${totalItems} éléments</span>
    `;
    
    // Contrôles de pagination
    const controlsContainer = document.createElement('div');
    controlsContainer.className = 'flex items-center space-x-2';
    
    // Bouton précédent
    const prevButton = document.createElement('button');
    prevButton.id = 'prevButton';
    prevButton.className = 'px-4 py-2 text-sm font-medium rounded-lg transition-all duration-300 shadow-sm hover:shadow-md transform hover:scale-105 disabled:opacity-50 disabled:cursor-not-allowed disabled:transform-none';
    prevButton.style.backgroundColor = '#f7d9c4';
    prevButton.style.color = '#4B352A';
    prevButton.style.border = '1px solid #e5d5c8';
    prevButton.innerHTML = '<i class="fas fa-chevron-left mr-2"></i>Précédent';
    prevButton.onclick = () => showPage(currentPage - 1);
    
    // Numéros de page
    const pageNumbersContainer = document.createElement('div');
    pageNumbersContainer.id = 'pageNumbers';
    pageNumbersContainer.className = 'flex items-center space-x-1';
    
    // Bouton suivant
    const nextButton = document.createElement('button');
    nextButton.id = 'nextButton';
    nextButton.className = 'px-4 py-2 text-sm font-medium rounded-lg transition-all duration-300 shadow-sm hover:shadow-md transform hover:scale-105 disabled:opacity-50 disabled:cursor-not-allowed disabled:transform-none';
    nextButton.style.backgroundColor = '#f7d9c4';
    nextButton.style.color = '#4B352A';
    nextButton.style.border = '1px solid #e5d5c8';
    nextButton.innerHTML = 'Suivant<i class="fas fa-chevron-right ml-2"></i>';
    nextButton.onclick = () => showPage(currentPage + 1);
    
    // Sélecteur d'éléments par page
    const itemsPerPageSelect = document.createElement('select');
    itemsPerPageSelect.id = 'itemsPerPageSelect';
    itemsPerPageSelect.className = 'px-3 py-2 text-sm rounded-lg transition-all duration-300 focus:ring-2 focus:ring-opacity-50';
    itemsPerPageSelect.style.borderColor = '#f7d9c4';
    itemsPerPageSelect.style.backgroundColor = '#f7d9c4';
    itemsPerPageSelect.style.color = '#4B352A';
    itemsPerPageSelect.style.focusRingColor = '#6d4b3b';
    itemsPerPageSelect.innerHTML = `
        <option value="5">5 par page</option>
        <option value="10" selected>10 par page</option>
        <option value="20">20 par page</option>
        <option value="50">50 par page</option>
        <option value="100">100 par page</option>
    `;
    itemsPerPageSelect.onchange = (e) => {
        itemsPerPage = parseInt(e.target.value);
        currentPage = 1;
        showPage(1);
    };
    
    // Séparateur
    const separator = document.createElement('span');
    separator.className = 'mx-3';
    separator.style.color = '#e5d5c8';
    separator.innerHTML = '|';
    
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
    const table = document.querySelector('table') || document.querySelector('#table-view') || document.querySelector('#grid-view');
    if (table) {
        table.parentNode.insertBefore(paginationContainer, table.nextSibling);
    }
}

// Afficher une page spécifique
function showPage(page) {
    const totalPages = Math.ceil(filteredItems.length / itemsPerPage);
    
    // Valider la page
    if (page < 1) page = 1;
    if (page > totalPages) page = totalPages;
    
    currentPage = page;
    
    // Masquer tous les éléments
    allItems.forEach(item => {
        item.element.style.display = 'none';
    });
    
    // Calculer les indices de début et fin
    const startIndex = (page - 1) * itemsPerPage;
    const endIndex = Math.min(startIndex + itemsPerPage, filteredItems.length);
    
    // Afficher les éléments de la page actuelle
    for (let i = startIndex; i < endIndex; i++) {
        if (filteredItems[i]) {
            filteredItems[i].element.style.display = '';
        }
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
            infoElement.textContent = 'Aucun élément à afficher';
        } else {
            infoElement.textContent = `Affichage de ${startIndex} à ${endIndex} sur ${filteredItems.length} éléments`;
        }
    }
    
    // Mettre à jour les boutons précédent/suivant
    const prevButton = document.getElementById('prevButton');
    const nextButton = document.getElementById('nextButton');
    
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
    
    // Logique d'affichage des numéros de page
    const maxVisiblePages = 5;
    let startPage = Math.max(1, currentPage - Math.floor(maxVisiblePages / 2));
    let endPage = Math.min(totalPages, startPage + maxVisiblePages - 1);
    
    // Ajuster si on est près de la fin
    if (endPage - startPage + 1 < maxVisiblePages) {
        startPage = Math.max(1, endPage - maxVisiblePages + 1);
    }
    
    // Bouton première page
    if (startPage > 1) {
        const firstButton = createPageButton(1, currentPage === 1);
        pageNumbersContainer.appendChild(firstButton);
        
        if (startPage > 2) {
            const ellipsis = document.createElement('span');
            ellipsis.className = 'px-2 py-1';
            ellipsis.style.color = '#6d4b3b';
            ellipsis.textContent = '...';
            pageNumbersContainer.appendChild(ellipsis);
        }
    }
    
    // Numéros de page
    for (let i = startPage; i <= endPage; i++) {
        const pageButton = createPageButton(i, currentPage === i);
        pageNumbersContainer.appendChild(pageButton);
    }
    
    // Bouton dernière page
    if (endPage < totalPages) {
        if (endPage < totalPages - 1) {
            const ellipsis = document.createElement('span');
            ellipsis.className = 'px-2 py-1';
            ellipsis.style.color = '#6d4b3b';
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
    button.className = 'px-3 py-2 text-sm font-medium rounded-lg transition-all duration-300 shadow-sm hover:shadow-md transform hover:scale-105';
    
    if (isActive) {
        button.style.background = 'linear-gradient(135deg, #4B352A, #6d4b3b)';
        button.style.color = 'white';
        button.style.border = '1px solid #4B352A';
    } else {
        button.style.backgroundColor = '#f7d9c4';
        button.style.color = '#4B352A';
        button.style.border = '1px solid #e5d5c8';
    }
    
    button.textContent = pageNumber;
    button.onclick = () => showPage(pageNumber);
    return button;
}

// Animer l'apparition des éléments de la page
function animatePageItems(startIndex, endIndex) {
    for (let i = startIndex; i < endIndex; i++) {
        if (filteredItems[i]) {
            const element = filteredItems[i].element;
            element.style.opacity = '0';
            element.style.transform = 'translateY(20px)';
            element.style.transition = 'all 0.3s ease';
            
            setTimeout(() => {
                element.style.opacity = '1';
                element.style.transform = 'translateY(0)';
            }, (i - startIndex) * 50);
        }
    }
}

// Fonction pour filtrer les éléments (utilisée par la recherche)
function filterItems(filteredData) {
    filteredItems = filteredData || allItems;
    currentPage = 1;
    showPage(1);
}

// Fonction pour réinitialiser la pagination
function resetPagination() {
    filteredItems = [...allItems];
    currentPage = 1;
    showPage(1);
}

// Fonction pour mettre à jour le nombre total d'éléments
function updateTotalItems(newTotal) {
    totalItems = newTotal;
    updatePaginationControls();
}

// Exposer les fonctions globalement pour l'intégration avec la recherche
window.smartPagination = {
    filterItems,
    resetPagination,
    updateTotalItems,
    showPage,
    getCurrentPage: () => currentPage,
    getItemsPerPage: () => itemsPerPage,
    getTotalItems: () => totalItems
};
