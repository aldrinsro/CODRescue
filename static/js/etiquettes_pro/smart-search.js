// ================== RECHERCHE INTELLIGENTE POUR ÉTIQUETTES ==================

// Variables globales pour la recherche
let allEtiquettes = [];
let searchTimeout = null;
let currentSearchQuery = '';

// Initialisation de la recherche
document.addEventListener('DOMContentLoaded', function() {
    console.log('🔍 [RECHERCHE-ÉTIQUETTES] Initialisation de la recherche intelligente');
    
    // Délai pour s'assurer que tous les éléments sont chargés
    setTimeout(() => {
        initializeSearch();
    }, 200);
});

// Initialiser la recherche
function initializeSearch() {
    console.log('🔧 [RECHERCHE-ÉTIQUETTES] Initialisation du système de recherche');
    
    // Collecter toutes les étiquettes
    collectAllEtiquettes();
    
    // Créer l'interface de recherche
    createSearchInterface();
    
    // Attacher les event listeners
    attachSearchEventListeners();
    
    console.log(`✅ [RECHERCHE-ÉTIQUETTES] ${allEtiquettes.length} étiquettes indexées pour la recherche`);
}

// Collecter toutes les étiquettes
function collectAllEtiquettes() {
    console.log('📋 [RECHERCHE-ÉTIQUETTES] Collecte des étiquettes...');
    
    // Détecter le type d'éléments (cartes ou lignes de tableau)
    let etiquetteElements = document.querySelectorAll('.etiquette-card');
    let isTableMode = false;
    
    // Si pas de cartes, chercher des lignes de tableau
    if (etiquetteElements.length === 0) {
        etiquetteElements = document.querySelectorAll('.etiquette-row');
        isTableMode = true;
        console.log('📋 [RECHERCHE-ÉTIQUETTES] Mode tableau détecté');
    } else {
        console.log('📋 [RECHERCHE-ÉTIQUETTES] Mode cartes détecté');
    }
    
    allEtiquettes = Array.from(etiquetteElements).map((element, index) => {
        // Extraire les données de recherche
        const reference = (isTableMode 
            ? element.querySelector('.column-reference') 
            : element.querySelector('.etiquette-reference'))?.textContent?.trim() || '';
        const template = (isTableMode 
            ? element.querySelector('.column-template') 
            : element.querySelector('.etiquette-template'))?.textContent?.trim() || '';
        const statutElement = element.querySelector('.etiquette-statut');
        const statutDisplay = statutElement?.textContent?.trim() || '';
        
        // Extraire le statut réel depuis les classes CSS
        let statutReal = '';
        if (statutElement) {
            // Classes pour les cartes (mode carte)
            if (statutElement.classList.contains('confirmee')) {
                statutReal = 'ready';
            } else if (statutElement.classList.contains('terminee')) {
                statutReal = 'printed';
            } else if (statutElement.classList.contains('en-preparation')) {
                statutReal = 'draft';
            }
            // Classes pour les tableaux (mode tableau)
            else if (statutElement.classList.contains('bg-green-100')) {
                statutReal = 'ready';
            } else if (statutElement.classList.contains('bg-blue-100')) {
                statutReal = 'printed';
            } else if (statutElement.classList.contains('bg-yellow-100')) {
                statutReal = 'draft';
            }
                // Fallback: analyser le texte affiché
            else {
                const displayText = statutDisplay.toLowerCase();
                if (displayText.includes('prête') || displayText.includes('ready')) {
                    statutReal = 'ready';
                } else if (displayText.includes('imprimée') || displayText.includes('printed')) {
                    statutReal = 'printed';
                } else if (displayText.includes('brouillon') || displayText.includes('draft')) {
                    statutReal = 'draft';
                } else {
                    statutReal = displayText;
                }
            }
        }
        
        const date = (isTableMode 
            ? element.querySelector('.column-date') 
            : element.querySelector('.etiquette-date'))?.textContent?.trim() || '';
        const commande = (isTableMode 
            ? element.querySelector('.column-commande') 
            : element.querySelector('.etiquette-commande'))?.textContent?.trim() || '';
        const articles = element.querySelector('.etiquette-articles')?.textContent?.trim() || '';
        const client = element.querySelector('.etiquette-client')?.textContent?.trim() || '';
        
        // Extraire le numéro de commande complet (ex: "ycn-000006")
        let numeroCommande = '';
        if (commande) {
            // Chercher un pattern comme "ycn-000006" ou "Commande ycn-000006"
            const match = commande.match(/([a-z]+-\d+)/i);
            if (match) {
                numeroCommande = match[1].toLowerCase();
            }
        }
        
        // Extraire les références d'articles depuis le texte des articles
        let referencesArticles = [];
        if (articles) {
            // Chercher des patterns de références d'articles (ex: "ABC-123", "YZ456", etc.)
            const referenceMatches = articles.match(/([A-Z]{2,}-\d+|[A-Z]{2,}\d+)/g);
            if (referenceMatches) {
                referencesArticles = referenceMatches.map(ref => ref.toLowerCase());
            }
        }
        
        // Créer un texte de recherche unifié avec le numéro de commande, les articles et leurs références
        const searchText = `${reference} ${template} ${statutDisplay} ${date} ${commande} ${articles} ${client} ${numeroCommande} ${referencesArticles.join(' ')}`.toLowerCase();
        
        return {
            element: element,
            index: index,
            reference: reference,
            template: template,
            statut: statutReal, // Utiliser le statut réel
            statutDisplay: statutDisplay, // Garder l'affichage pour la recherche
            date: date,
            commande: commande,
            articles: articles,
            client: client,
            numeroCommande: numeroCommande, // Numéro de commande extrait
            referencesArticles: referencesArticles, // Références d'articles extraites
            searchText: searchText
        };
    });
    
    console.log(`📊 [RECHERCHE-ÉTIQUETTES] ${allEtiquettes.length} étiquettes collectées`);
    
    // Log des statuts pour débogage
    const statuts = allEtiquettes.map(e => ({ reference: e.reference, statut: e.statut, statutDisplay: e.statutDisplay }));
    console.log('🔍 [RECHERCHE-ÉTIQUETTES] Statuts extraits:', statuts);
    
    // Log des numéros de commande pour débogage
    const commandes = allEtiquettes.map(e => ({ reference: e.reference, commande: e.commande, numeroCommande: e.numeroCommande }));
    console.log('🛒 [RECHERCHE-ÉTIQUETTES] Numéros de commande extraits:', commandes);
    
    // Log des articles pour débogage
    const articles = allEtiquettes.map(e => ({ reference: e.reference, articles: e.articles }));
    console.log('📦 [RECHERCHE-ÉTIQUETTES] Articles extraits:', articles);
    
    // Log des références d'articles pour débogage
    const refsArticles = allEtiquettes.map(e => ({ reference: e.reference, referencesArticles: e.referencesArticles }));
    console.log('🏷️ [RECHERCHE-ÉTIQUETTES] Références d\'articles extraites:', refsArticles);
    
    // Log spécifique pour les brouillons
    const drafts = allEtiquettes.filter(e => e.statut === 'draft');
    console.log('📝 [RECHERCHE-ÉTIQUETTES] Étiquettes brouillon trouvées:', drafts);
}

// Créer l'interface de recherche
function createSearchInterface() {
    // Vérifier si l'interface existe déjà
    if (document.getElementById('smartSearchContainer')) {
        return;
    }
    
    console.log('🎛️ [RECHERCHE-ÉTIQUETTES] Création de l\'interface de recherche');
    
    // Créer le conteneur de recherche avec le design uniforme
    const searchContainer = document.createElement('div');
    searchContainer.id = 'smartSearchContainer';
    searchContainer.className = 'bg-white rounded-xl shadow-lg border border-gray-200 mb-6';
    
    // En-tête de la carte avec le design uniforme
    const cardHeader = document.createElement('div');
    cardHeader.className = 'p-4 border-b border-gray-100';
    
    const title = document.createElement('h3');
    title.className = 'text-lg font-bold text-gray-800 flex items-center';
    title.innerHTML = '<i class="fas fa-search mr-3 text-gray-600"></i>Recherche Intelligente';
    
    cardHeader.appendChild(title);
    
    // Contenu de la carte
    const cardContent = document.createElement('div');
    cardContent.className = 'p-4';
    
    // Conteneur principal
    const mainContainer = document.createElement('div');
    mainContainer.className = 'flex flex-col md:flex-row gap-4 items-end';
    
    // Champ de recherche principal
    const searchInputContainer = document.createElement('div');
    searchInputContainer.className = 'flex-1';
    
    const searchInputLabel = document.createElement('label');
    searchInputLabel.className = 'block text-sm font-medium text-gray-700 mb-2';
    searchInputLabel.textContent = 'Rechercher';
    
    const searchInput = document.createElement('input');
    searchInput.type = 'text';
    searchInput.id = 'smartSearchInput';
    searchInput.className = 'theme-input w-full';
    searchInput.placeholder = 'Référence, template, statut, date, numéro commande (ex: ycn-000006), articles, référence article (ex: ABC-123), client...';
    
    searchInputContainer.appendChild(searchInputLabel);
    searchInputContainer.appendChild(searchInput);
    
    // Filtres rapides
    const filtersContainer = document.createElement('div');
    filtersContainer.className = 'flex flex-col md:flex-row gap-4';
    
    // Filtre par statut
    const statutContainer = document.createElement('div');
    statutContainer.className = 'flex-1';
    
    const statutLabel = document.createElement('label');
    statutLabel.className = 'block text-sm font-medium text-gray-700 mb-2';
    statutLabel.textContent = 'Statut';
    
    const statutFilter = document.createElement('select');
    statutFilter.id = 'statutFilter';
    statutFilter.className = 'theme-input w-full';
    statutFilter.innerHTML = `
        <option value="">Tous les statuts</option>
        <option value="draft">Brouillon</option>
        <option value="ready">Prête</option>
        <option value="printed">Imprimée</option>
    `;
    
    statutContainer.appendChild(statutLabel);
    statutContainer.appendChild(statutFilter);
    
    // Filtre par template
    const templateContainer = document.createElement('div');
    templateContainer.className = 'flex-1';
    
    const templateLabel = document.createElement('label');
    templateLabel.className = 'block text-sm font-medium text-gray-700 mb-2';
    templateLabel.textContent = 'Template';
    
    const templateFilter = document.createElement('select');
    templateFilter.id = 'templateFilter';
    templateFilter.className = 'theme-input w-full';
    templateFilter.innerHTML = '<option value="">Tous les templates</option>';
    
    // Collecter les templates uniques
    const uniqueTemplates = [...new Set(allEtiquettes.map(e => e.template))].filter(t => t);
    uniqueTemplates.forEach(template => {
        const option = document.createElement('option');
        option.value = template;
        option.textContent = template;
        templateFilter.appendChild(option);
    });
    
    templateContainer.appendChild(templateLabel);
    templateContainer.appendChild(templateFilter);
    
    // Bouton de réinitialisation
    const resetButton = document.createElement('button');
    resetButton.id = 'resetSearchButton';
    resetButton.className = 'px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-md hover:bg-gray-100 hover:border-gray-400 hover:text-gray-900 transition-colors flex items-center';
    resetButton.innerHTML = '<i class="fas fa-times mr-2"></i>Effacer';
    
    filtersContainer.appendChild(statutContainer);
    filtersContainer.appendChild(templateContainer);
    filtersContainer.appendChild(resetButton);
    
    // Résultats de recherche
    const resultsContainer = document.createElement('div');
    resultsContainer.id = 'searchResults';
    resultsContainer.className = 'mt-4 p-3 bg-gray-50 rounded-lg hidden';
    
    const resultsText = document.createElement('div');
    resultsText.id = 'searchResultsText';
    resultsText.className = 'text-sm text-gray-600';
    
    resultsContainer.appendChild(resultsText);
    
    // Assembler le conteneur
    mainContainer.appendChild(searchInputContainer);
    mainContainer.appendChild(filtersContainer);
    cardContent.appendChild(mainContainer);
    cardContent.appendChild(resultsContainer);
    
    searchContainer.appendChild(cardHeader);
    searchContainer.appendChild(cardContent);
    
    // Insérer après les statistiques, avec repositionnement et retries
    const insertAfterStats = (attempt = 0) => {
        const statsContainer = document.getElementById('stats-cards');
        if (statsContainer) {
            // Déplacer si déjà insérée ailleurs
            if (searchContainer.parentNode) {
                searchContainer.parentNode.removeChild(searchContainer);
            }
            statsContainer.parentNode.insertBefore(searchContainer, statsContainer.nextSibling);
            return;
        }
        if (attempt < 10) {
            setTimeout(() => insertAfterStats(attempt + 1), 200);
            return;
        }
        // Fallback : insérer après l'en-tête de la page
        const pageHeader = document.querySelector('.page-header');
        if (pageHeader) {
            if (searchContainer.parentNode) {
                searchContainer.parentNode.removeChild(searchContainer);
            }
            pageHeader.parentNode.insertBefore(searchContainer, pageHeader.nextSibling);
        }
    };

    insertAfterStats();
}

// Attacher les event listeners
function attachSearchEventListeners() {
    const searchInput = document.getElementById('smartSearchInput');
    const statutFilter = document.getElementById('statutFilter');
    const templateFilter = document.getElementById('templateFilter');
    const resetButton = document.getElementById('resetSearchButton');
    
    // Recherche en temps réel
    if (searchInput) {
        searchInput.addEventListener('input', (e) => {
            currentSearchQuery = e.target.value;
            performSearch();
        });
    }
    
    // Filtres
    if (statutFilter) {
        statutFilter.addEventListener('change', performSearch);
    }
    
    if (templateFilter) {
        templateFilter.addEventListener('change', performSearch);
    }
    
    // Bouton de réinitialisation
    if (resetButton) {
        resetButton.addEventListener('click', resetSearch);
    }
    
    console.log('✅ [RECHERCHE-ÉTIQUETTES] Event listeners attachés');
}

// Effectuer la recherche
function performSearch() {
    // Annuler la recherche précédente si elle est en cours
    if (searchTimeout) {
        clearTimeout(searchTimeout);
    }
    
    // Délai pour éviter trop de recherches
    searchTimeout = setTimeout(() => {
        const searchQuery = currentSearchQuery.toLowerCase().trim();
        const statutFilter = document.getElementById('statutFilter')?.value || '';
        const templateFilter = document.getElementById('templateFilter')?.value || '';
        
        console.log('🔍 [RECHERCHE-ÉTIQUETTES] Recherche en cours...', {
            query: searchQuery,
            statut: statutFilter,
            template: templateFilter
        });
        
        // Filtrer les étiquettes
        const filteredEtiquettes = allEtiquettes.filter(etiquette => {
            // Recherche textuelle
            const matchesSearch = !searchQuery || etiquette.searchText.includes(searchQuery);
            
            // Filtre par statut
            const matchesStatut = !statutFilter || etiquette.statut.toLowerCase() === statutFilter.toLowerCase();
            
            // Filtre par template
            const matchesTemplate = !templateFilter || etiquette.template === templateFilter;
            
            // Log de débogage pour le statut
            if (statutFilter) {
                console.log(`🔍 [RECHERCHE-ÉTIQUETTES] Filtre statut: "${statutFilter}" vs "${etiquette.statut}" (${etiquette.reference}) = ${matchesStatut}`);
            }
            
            return matchesSearch && matchesStatut && matchesTemplate;
        });
        
        // Log spécifique pour le filtre draft
        if (statutFilter === 'draft') {
            console.log('📝 [RECHERCHE-ÉTIQUETTES] Filtre draft activé:');
            console.log('- Total étiquettes:', allEtiquettes.length);
            console.log('- Étiquettes draft trouvées:', allEtiquettes.filter(e => e.statut === 'draft').length);
            console.log('- Résultats filtrés:', filteredEtiquettes.length);
        }
        
        // Afficher les résultats
        displaySearchResults(filteredEtiquettes, searchQuery, statutFilter, templateFilter);
        
        // Intégration avec la pagination intelligente
        if (window.smartPaginationEtiquettes) {
            window.smartPaginationEtiquettes.filterItems(filteredEtiquettes);
        } else {
            // Fallback sans pagination
            showFilteredEtiquettes(filteredEtiquettes);
        }
        
    }, 300); // Délai de 300ms
}

// Afficher les résultats de recherche
function displaySearchResults(filteredEtiquettes, searchQuery, statutFilter, templateFilter) {
    const resultsContainer = document.getElementById('searchResults');
    const resultsText = document.getElementById('searchResultsText');
    
    if (!resultsContainer || !resultsText) return;
    
    const totalResults = filteredEtiquettes.length;
    const totalItems = allEtiquettes.length;
    
    // Construire le texte des résultats
    let resultsMessage = '';
    
    if (totalResults === 0) {
        resultsMessage = '❌ Aucune étiquette trouvée';
        resultsContainer.className = 'mt-4 p-3 bg-red-50 border border-red-200 rounded-lg';
    } else if (totalResults === totalItems) {
        resultsMessage = `✅ Toutes les étiquettes affichées (${totalResults})`;
        resultsContainer.className = 'mt-4 p-3 bg-green-50 border border-green-200 rounded-lg';
    } else {
        resultsMessage = `🔍 ${totalResults} étiquette(s) trouvée(s) sur ${totalItems}`;
        resultsContainer.className = 'mt-4 p-3 bg-gray-50 border border-gray-200 rounded-lg';
    }
    
    // Ajouter les détails des filtres
    const filterDetails = [];
    if (searchQuery) filterDetails.push(`Recherche: "${searchQuery}"`);
    if (statutFilter) filterDetails.push(`Statut: ${statutFilter}`);
    if (templateFilter) filterDetails.push(`Template: ${templateFilter}`);
    
    if (filterDetails.length > 0) {
        resultsMessage += `<br><small class="text-gray-500">Filtres: ${filterDetails.join(', ')}</small>`;
    }
    
    resultsText.innerHTML = resultsMessage;
    resultsContainer.classList.remove('hidden');
    
    console.log(`📊 [RECHERCHE-ÉTIQUETTES] ${totalResults} résultats affichés`);
}

// Afficher les étiquettes filtrées (fallback sans pagination)
function showFilteredEtiquettes(filteredEtiquettes) {
    // Masquer toutes les étiquettes
    allEtiquettes.forEach(etiquette => {
        etiquette.element.style.display = 'none';
    });
    
    // Afficher seulement les étiquettes filtrées
    filteredEtiquettes.forEach(etiquette => {
        etiquette.element.style.display = '';
        etiquette.element.style.opacity = '1';
        etiquette.element.style.transform = 'translateY(0)';
    });
}

// Réinitialiser la recherche
function resetSearch() {
    console.log('🔄 [RECHERCHE-ÉTIQUETTES] Réinitialisation de la recherche');
    
    // Réinitialiser les champs
    const searchInput = document.getElementById('smartSearchInput');
    const statutFilter = document.getElementById('statutFilter');
    const templateFilter = document.getElementById('templateFilter');
    const resultsContainer = document.getElementById('searchResults');
    
    if (searchInput) searchInput.value = '';
    if (statutFilter) statutFilter.value = '';
    if (templateFilter) templateFilter.value = '';
    if (resultsContainer) resultsContainer.classList.add('hidden');
    
    currentSearchQuery = '';
    
    // Réinitialiser la pagination
    if (window.smartPaginationEtiquettes) {
        window.smartPaginationEtiquettes.resetPagination();
    } else {
        // Fallback sans pagination
        showFilteredEtiquettes(allEtiquettes);
    }
}

// Fonction pour obtenir les statistiques de recherche
function getSearchStats() {
    return {
        totalEtiquettes: allEtiquettes.length,
        currentQuery: currentSearchQuery,
        hasActiveFilters: currentSearchQuery || 
                         document.getElementById('statutFilter')?.value || 
                         document.getElementById('templateFilter')?.value
    };
}

// API publique pour la recherche intelligente
window.smartSearchEtiquettes = {
    init: initializeSearch,
    search: performSearch,
    reset: resetSearch,
    getStats: getSearchStats,
    getFilteredItems: () => allEtiquettes.filter(etiquette => {
        const searchQuery = currentSearchQuery.toLowerCase().trim();
        const statutFilter = document.getElementById('statutFilter')?.value || '';
        const templateFilter = document.getElementById('templateFilter')?.value || '';
        
        const matchesSearch = !searchQuery || etiquette.searchText.includes(searchQuery);
        const matchesStatut = !statutFilter || etiquette.statut.toLowerCase().includes(statutFilter.toLowerCase());
        const matchesTemplate = !templateFilter || etiquette.template === templateFilter;
        
        return matchesSearch && matchesStatut && matchesTemplate;
    })
};

console.log('✅ [RECHERCHE-ÉTIQUETTES] Module de recherche intelligente chargé');
