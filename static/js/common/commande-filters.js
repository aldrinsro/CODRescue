/**
 * ========================================
 * SYSTÈME DE FILTRES GLOBAUX POUR COMMANDES
 * ========================================
 *
 * Ce fichier gère la logique JavaScript des filtres de commandes côté client.
 * Il fonctionne avec le template 'common/commande-filters.html'
 *
 * Fonctionnalités :
 * - Recherche intelligente en temps réel
 * - Filtres avancés (client, téléphone, ville, dates, montant, etc.)
 * - Affichage/masquage des panneaux de filtres
 * - Application et effacement des filtres
 * - Comptage des résultats filtrés
 *
 * Utilisation :
 * 1. Inclure ce fichier JS dans votre template
 * 2. Inclure le template 'common/commande-filters.html'
 * 3. Appeler initCommandeFilters() au chargement de la page
 *
 * @version 1.0.0
 * @author YZ-Rescue Team
 */

// Variables globales
let filterTimeout;
const FILTER_DELAY = 300; // Délai en ms avant d'appliquer les filtres

/**
 * Initialise le système de filtres de commandes
 * @param {Object} options - Options de configuration
 */
function initCommandeFilters(options = {}) {
    const defaults = {
        tableSelector: '#cmdTable tbody tr',
        searchDelay: 300,
        debug: false
    };

    const settings = { ...defaults, ...options };

    if (settings.debug) {
        console.log('[Commande Filters] Initialisation avec options:', settings);
    }

    // Initialiser la recherche intelligente
    initSmartSearch(settings);

    // Initialiser les filtres avancés
    initAdvancedFilters(settings);
}

/**
 * Initialise la barre de recherche intelligente
 */
function initSmartSearch(settings) {
    const searchInput = document.getElementById('smartSearch');

    if (!searchInput) {
        console.warn('[Commande Filters] Champ de recherche "smartSearch" non trouvé');
        return;
    }

    searchInput.addEventListener('input', function() {
        clearTimeout(filterTimeout);
        filterTimeout = setTimeout(() => {
            const query = this.value.toLowerCase().trim();
            filterTableRows(query, settings);
        }, settings.searchDelay);
    });

    // Restaurer la recherche depuis l'URL
    const urlParams = new URLSearchParams(window.location.search);
    const searchParam = urlParams.get('search');
    if (searchParam) {
        searchInput.value = searchParam;
        filterTableRows(searchParam.toLowerCase(), settings);
    }
}

/**
 * Filtre les lignes du tableau selon la recherche
 */
function filterTableRows(query, settings) {
    const rows = document.querySelectorAll(settings.tableSelector);
    let visibleCount = 0;

    rows.forEach(row => {
        const text = row.textContent.toLowerCase();
        const isVisible = text.includes(query);

        row.style.display = isVisible ? '' : 'none';

        if (isVisible) visibleCount++;
    });

    updateSearchResults(visibleCount, query);
}

/**
 * Met à jour l'affichage des résultats de recherche
 */
function updateSearchResults(count, query) {
    const resultsDiv = document.getElementById('searchResults');
    const countSpan = document.getElementById('resultCount');

    if (!resultsDiv || !countSpan) return;

    countSpan.textContent = count;

    if (query) {
        resultsDiv.classList.remove('hidden');
    } else {
        resultsDiv.classList.add('hidden');
    }
}

/**
 * Efface la recherche intelligente
 */
function clearSmartSearch() {
    const searchInput = document.getElementById('smartSearch');
    if (searchInput) {
        searchInput.value = '';
        searchInput.dispatchEvent(new Event('input'));
    }

    // Effacer le paramètre de recherche de l'URL
    const url = new URL(window.location);
    url.searchParams.delete('search');
    window.history.replaceState({}, '', url);

    updateSearchResults(0, '');
}

/**
 * Bascule l'affichage des filtres avancés
 */
function toggleAdvancedSearch() {
    const advancedSearch = document.getElementById('advancedSearch');

    if (!advancedSearch) {
        console.warn('[Commande Filters] Panneau de filtres avancés non trouvé');
        return;
    }

    advancedSearch.classList.toggle('hidden');
}

/**
 * Initialise les filtres avancés
 */
function initAdvancedFilters(settings) {
    // Restaurer les valeurs des filtres depuis l'URL
    const urlParams = new URLSearchParams(window.location.search);

    // Liste des filtres à restaurer
    const filters = [
        'filter_id_yz',
        'filter_num_cmd',
        'filter_client',
        'filter_phone',
        'filter_email',
        'filter_ville_client',
        'filter_ville_region',
        'filter_adresse',
        'filter_date_commande',
        'filter_date_confirmation',
        'filter_date_affectation',
        'filter_date_preparation',
        'filter_date_livraison',
        'filter_total_min',
        'filter_total_max',
        'filter_etat',
        'filter_operateur'
    ];

    filters.forEach(filterName => {
        const value = urlParams.get(filterName);
        if (value) {
            const inputId = filterName.replace('filter_', 'filter').replace(/_([a-z])/g, (g) => g[1].toUpperCase());
            // Convertir snake_case en camelCase pour les IDs
            // Ex: filter_id_yz -> filterIdYz
            const camelCaseId = 'filter' + filterName.substring(7).split('_').map((word, index) => {
                if (index === 0) return word.charAt(0).toUpperCase() + word.slice(1);
                return word.charAt(0).toUpperCase() + word.slice(1);
            }).join('');

            const input = document.getElementById(camelCaseId);
            if (input) {
                input.value = value;
            }
        }
    });
}

/**
 * Applique les filtres avancés
 */
function applyFilters() {
    const url = new URL(window.location);
    const params = new URLSearchParams(url.search);

    // Mappage des IDs de champs vers les noms de paramètres
    const filterMapping = {
        'filterIdYz': 'filter_id_yz',
        'filterNumCmd': 'filter_num_cmd',
        'filterClient': 'filter_client',
        'filterPhone': 'filter_phone',
        'filterEmail': 'filter_email',
        'filterVilleClient': 'filter_ville_client',
        'filterVilleRegion': 'filter_ville_region',
        'filterAdresse': 'filter_adresse',
        'filterDateCommande': 'filter_date_commande',
        'filterDateConfirmation': 'filter_date_confirmation',
        'filterDateAffectation': 'filter_date_affectation',
        'filterDatePreparation': 'filter_date_preparation',
        'filterDateLivraison': 'filter_date_livraison',
        'filterTotalMin': 'filter_total_min',
        'filterTotalMax': 'filter_total_max',
        'filterEtat': 'filter_etat',
        'filterOperateur': 'filter_operateur'
    };

    // Construire les paramètres de l'URL
    Object.entries(filterMapping).forEach(([inputId, paramName]) => {
        const input = document.getElementById(inputId);
        if (input && input.value.trim()) {
            params.set(paramName, input.value.trim());
        } else {
            params.delete(paramName);
        }
    });

    // Conserver la recherche globale si elle existe
    const searchInput = document.getElementById('smartSearch');
    if (searchInput && searchInput.value.trim()) {
        params.set('search', searchInput.value.trim());
    }

    // Rediriger vers l'URL avec les filtres
    url.search = params.toString();
    window.location.href = url.toString();
}

/**
 * Efface tous les filtres avancés
 */
function clearFilters() {
    // Effacer les champs de filtres
    const filterInputs = document.querySelectorAll('#advancedSearch input');
    filterInputs.forEach(input => {
        input.value = '';
    });

    // Rediriger vers l'URL sans paramètres de filtre
    const url = new URL(window.location);
    const params = new URLSearchParams();

    // Conserver uniquement les paramètres non liés aux filtres (ex: page, items_per_page)
    const preserveParams = ['page', 'items_per_page'];
    url.searchParams.forEach((value, key) => {
        if (preserveParams.includes(key)) {
            params.set(key, value);
        }
    });

    url.search = params.toString();
    window.location.href = url.toString();
}

/**
 * Compte les filtres actifs
 */
function countActiveFilters() {
    const urlParams = new URLSearchParams(window.location.search);
    let count = 0;

    const filterParams = [
        'search',
        'filter_id_yz',
        'filter_num_cmd',
        'filter_client',
        'filter_phone',
        'filter_email',
        'filter_ville_client',
        'filter_ville_region',
        'filter_adresse',
        'filter_date_commande',
        'filter_date_confirmation',
        'filter_date_affectation',
        'filter_date_preparation',
        'filter_date_livraison',
        'filter_total_min',
        'filter_total_max',
        'filter_etat',
        'filter_operateur'
    ];

    filterParams.forEach(param => {
        if (urlParams.has(param) && urlParams.get(param)) {
            count++;
        }
    });

    return count;
}

/**
 * Affiche le badge du nombre de filtres actifs
 */
function displayActiveFiltersBadge() {
    const count = countActiveFilters();
    const filterBtn = document.querySelector('button[onclick="toggleAdvancedSearch()"]');

    if (!filterBtn) return;

    // Créer ou mettre à jour le badge
    let badge = filterBtn.querySelector('.filter-badge');

    if (count > 0) {
        if (!badge) {
            badge = document.createElement('span');
            badge.className = 'filter-badge ml-2 px-2 py-0.5 bg-red-500 text-white text-xs rounded-full font-bold';
            filterBtn.appendChild(badge);
        }
        badge.textContent = count;
    } else if (badge) {
        badge.remove();
    }
}

// Initialisation automatique au chargement de la page
document.addEventListener('DOMContentLoaded', function() {
    // Vérifier si le composant de filtres est présent sur la page
    if (document.getElementById('smartSearch') || document.getElementById('advancedSearch')) {
        initCommandeFilters({
            debug: false // Passer à true pour activer les logs de débogage
        });
        displayActiveFiltersBadge();
    }
});
