// ================== RECHERCHE INTELLIGENTE ==================

// Variables globales pour la recherche
let searchTimeout = null;
let allCommandes = [];

// Initialisation de la recherche
document.addEventListener('DOMContentLoaded', function() {
    const searchInput = document.getElementById('searchInput');
    const clearSearchBtn = document.getElementById('clearSearchBtn');
    
    if (searchInput) {
        // Collecter toutes les commandes pour la recherche
        collectAllCommandes();
        
        // Événement de recherche en temps réel
        searchInput.addEventListener('input', function() {
            const query = this.value.trim();
            
            // Afficher/masquer le bouton de suppression
            if (query.length > 0) {
                clearSearchBtn.classList.remove('hidden');
            } else {
                clearSearchBtn.classList.add('hidden');
            }
            
            // Recherche avec debouncing
            clearTimeout(searchTimeout);
            searchTimeout = setTimeout(() => {
                performSearch(query);
            }, 300);
        });
        
        // Raccourci clavier pour focus
        document.addEventListener('keydown', function(e) {
            if ((e.ctrlKey || e.metaKey) && e.key === 'k') {
                e.preventDefault();
                searchInput.focus();
                searchInput.select();
            }
        });
    }
    
    if (clearSearchBtn) {
        clearSearchBtn.addEventListener('click', clearSearch);
    }
});

// Collecter toutes les commandes pour la recherche
function collectAllCommandes() {
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
    
    allCommandes = Array.from(tableRows).map(row => {
        if (row.classList.contains('commande-card')) {
            // Carte de grille (page confirmation)
            return {
                element: row,
                id_yz: row.querySelector('.commande-numero')?.textContent?.trim() || '',
                numero_externe: row.querySelector('.numero-externe')?.textContent?.trim() || '',
                client: row.querySelector('.client-nom')?.textContent?.trim() || '',
                telephone: row.querySelector('.client-telephone')?.textContent?.trim() || '',
                ville_client: row.querySelector('.ville-client')?.textContent?.trim() || '',
                ville_region: row.querySelector('.ville-livraison')?.textContent?.trim() || '',
                date: row.querySelector('.date-commande')?.textContent?.trim() || '',
                total: row.querySelector('.total-commande')?.textContent?.trim() || '',
                etat: row.querySelector('.etat-commande')?.textContent?.trim() || '',
                data: row.dataset
            };
        } else {
            // Ligne de tableau - Adapter selon la page
            const cells = row.querySelectorAll('td');
            
            if (isCommandesConfirmeesPage) {
                // Page "Mes confirmées" - Structure: ID YZ, N° Externe, Client, Téléphone, Ville Client, Ville & Région, Panier, Total, Date Confirmation, Opération, Actions
                return {
                    element: row,
                    id_yz: cells[0]?.textContent?.trim() || '',
                    numero_externe: cells[1]?.textContent?.trim() || '',
                    client: cells[2]?.textContent?.trim() || '',
                    telephone: cells[3]?.textContent?.trim() || '',
                    ville_client: cells[4]?.textContent?.trim() || '',
                    ville_region: cells[5]?.textContent?.trim() || '',
                    date: cells[8]?.textContent?.trim() || '', // Date Confirmation
                    total: cells[7]?.textContent?.trim() || '',
                    etat: cells[9]?.textContent?.trim() || '', // Opération
                    data: row.dataset
                };
            } else if (isListeCommandesPage) {
                // Page "Mes commandes" - Structure: ID YZ (avec N° externe), Client, Téléphone, Ville Client, Ville & Région, Date, Total, État, Panier, Actions
                return {
                    element: row,
                    id_yz: cells[0]?.textContent?.trim() || '',
                    numero_externe: '', // N° externe inclus dans ID YZ
                    client: cells[1]?.textContent?.trim() || '',
                    telephone: cells[2]?.textContent?.trim() || '',
                    ville_client: cells[3]?.textContent?.trim() || '',
                    ville_region: cells[4]?.textContent?.trim() || '',
                    date: cells[5]?.textContent?.trim() || '',
                    total: cells[6]?.textContent?.trim() || '',
                    etat: cells[7]?.textContent?.trim() || '',
                    data: row.dataset
                };
            } else {
                // Page "Lancer les Confirmations" - Structure: ID YZ, N° Externe, Client, Téléphone, Ville Client, Ville & Région, Date, Total, État, Actions
                return {
                    element: row,
                    id_yz: cells[0]?.textContent?.trim() || '',
                    numero_externe: cells[1]?.textContent?.trim() || '',
                    client: cells[2]?.textContent?.trim() || '',
                    telephone: cells[3]?.textContent?.trim() || '',
                    ville_client: cells[4]?.textContent?.trim() || '',
                    ville_region: cells[5]?.textContent?.trim() || '',
                    date: cells[6]?.textContent?.trim() || '',
                    total: cells[7]?.textContent?.trim() || '',
                    etat: cells[8]?.textContent?.trim() || '',
                    data: row.dataset
                };
            }
        }
    });
}

// Effectuer la recherche
function performSearch(query) {
    if (!query) {
        showAllCommandes();
        updateFilteredCount(allCommandes.length);
        return;
    }
    
    const searchTerm = query.toLowerCase();
    const filteredCommandes = allCommandes.filter(commande => {
        return commande.id_yz.toLowerCase().includes(searchTerm) ||
               commande.numero_externe.toLowerCase().includes(searchTerm) ||
               commande.client.toLowerCase().includes(searchTerm) ||
               commande.telephone.toLowerCase().includes(searchTerm) ||
               commande.ville_client.toLowerCase().includes(searchTerm) ||
               commande.ville_region.toLowerCase().includes(searchTerm) ||
               commande.date.toLowerCase().includes(searchTerm) ||
               commande.total.toLowerCase().includes(searchTerm) ||
               commande.etat.toLowerCase().includes(searchTerm);
    });
    
    // Masquer toutes les commandes
    allCommandes.forEach(commande => {
        commande.element.style.display = 'none';
    });
    
    // Intégration avec la pagination intelligente
    if (window.smartPagination) {
        window.smartPagination.filterItems(filteredCommandes);
    } else {
        // Afficher seulement les commandes filtrées (fallback)
        filteredCommandes.forEach(commande => {
            commande.element.style.display = '';
        });
    }
    
    updateFilteredCount(filteredCommandes.length);
    
    // Animation pour les résultats
    if (filteredCommandes.length > 0) {
        filteredCommandes.forEach((commande, index) => {
            setTimeout(() => {
                commande.element.style.opacity = '0';
                commande.element.style.transform = 'translateY(10px)';
                commande.element.style.transition = 'all 0.3s ease';
                
                setTimeout(() => {
                    commande.element.style.opacity = '1';
                    commande.element.style.transform = 'translateY(0)';
                }, 50);
            }, index * 50);
        });
    }
}

// Afficher toutes les commandes
function showAllCommandes() {
    // Intégration avec la pagination intelligente
    if (window.smartPagination) {
        window.smartPagination.resetPagination();
    } else {
        // Fallback sans pagination
        allCommandes.forEach(commande => {
            commande.element.style.display = '';
            commande.element.style.opacity = '1';
            commande.element.style.transform = 'translateY(0)';
        });
    }
}

// Effacer la recherche
function clearSearch() {
    const searchInput = document.getElementById('searchInput');
    const clearSearchBtn = document.getElementById('clearSearchBtn');
    
    if (searchInput) {
        searchInput.value = '';
        searchInput.focus();
    }
    
    if (clearSearchBtn) {
        clearSearchBtn.classList.add('hidden');
    }
    
    showAllCommandes();
    updateFilteredCount(allCommandes.length);
}

// Mettre à jour le compteur filtré
function updateFilteredCount(count) {
    const filteredCountElement = document.getElementById('filteredCount');
    if (filteredCountElement) {
        filteredCountElement.textContent = count;
        
        // Animation du compteur
        filteredCountElement.style.transform = 'scale(1.1)';
        filteredCountElement.style.transition = 'transform 0.2s ease';
        
        setTimeout(() => {
            filteredCountElement.style.transform = 'scale(1)';
        }, 200);
    }
}

// Recollecter les commandes lors du changement de vue
function switchToTable() {
    // Code existant pour basculer vers la vue tableau
    document.getElementById('table-view').classList.remove('hidden');
    document.getElementById('grid-view').classList.add('hidden');
    document.getElementById('btn-table').classList.add('btn-confirm');
    document.getElementById('btn-table').classList.remove('bg-gray-300', 'text-gray-700');
    document.getElementById('btn-grid').classList.remove('btn-confirm');
    document.getElementById('btn-grid').classList.add('bg-gray-300', 'text-gray-700');
    
    // Recollecter les commandes après le changement de vue
    setTimeout(() => {
        collectAllCommandes();
        const searchInput = document.getElementById('searchInput');
        if (searchInput && searchInput.value.trim()) {
            performSearch(searchInput.value.trim());
        }
    }, 100);
}

function switchToGrid() {
    // Code existant pour basculer vers la vue grille
    document.getElementById('table-view').classList.add('hidden');
    document.getElementById('grid-view').classList.remove('hidden');
    document.getElementById('btn-grid').classList.add('btn-confirm');
    document.getElementById('btn-grid').classList.remove('bg-gray-300', 'text-gray-700');
    document.getElementById('btn-table').classList.remove('btn-confirm');
    document.getElementById('btn-table').classList.add('bg-gray-300', 'text-gray-700');
    
    // Recollecter les commandes après le changement de vue
    setTimeout(() => {
        collectAllCommandes();
        const searchInput = document.getElementById('searchInput');
        if (searchInput && searchInput.value.trim()) {
            performSearch(searchInput.value.trim());
        }
    }, 100);
}
