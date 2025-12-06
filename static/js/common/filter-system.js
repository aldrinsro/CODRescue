/**
 * =====================================================
 * SYSTÈME DE FILTRES AVANCÉS GLOBAL - YZ-RESCUE
 * =====================================================
 *
 * Système de filtrage réutilisable pour toutes les pages de l'application.
 * Permet de filtrer dynamiquement les lignes d'un tableau selon plusieurs critères.
 *
 * @version 1.0.0
 * @author YZ-Rescue Team
 * @date 2025-11-19
 *
 * UTILISATION:
 * -----------
 * 1. Inclure le template: {% include 'common/advanced-filters.html' with filter_config=config %}
 * 2. Inclure ce fichier JS: <script src="{% static 'js/common/filter-system.js' %}"></script>
 * 3. Initialiser: const filterSystem = new AdvancedFilterSystem({ rowSelector: '.commande-row' });
 *
 * CONFIGURATION:
 * -------------
 * Les filtres sont configurés via data-attributes sur les inputs:
 * - data-field: nom du data-attribute sur les lignes du tableau
 * - data-filter-type: type de filtre (text, number, date, min, max)
 *
 * EXEMPLE DE LIGNE FILTRABLE:
 * <tr class="filterable-row" data-id-yz="212268" data-client="John Doe" data-total="500">
 */

class AdvancedFilterSystem {
    constructor(config = {}) {
        // Configuration
        this.rowSelector = config.rowSelector || '.filterable-row';
        this.panelId = config.panelId || 'advancedFilters';
        this.resultsId = config.resultsId || 'filterResults';
        this.badgeId = config.badgeId || 'filterBadge';

        // Éléments DOM
        this.panel = document.getElementById(this.panelId);
        this.resultsDiv = document.getElementById(this.resultsId);
        this.badge = document.getElementById(this.badgeId);
        this.rows = document.querySelectorAll(this.rowSelector);

        // État des filtres
        this.activeFilters = {};
        this.filterInputs = [];

        // Initialisation
        this.init();
    }

    /**
     * Initialisation du système
     */
    init() {
        if (!this.panel) {
            console.warn('⚠️ Panneau de filtres non trouvé (#' + this.panelId + ')');
            return;
        }

        if (this.rows.length === 0) {
            console.warn('⚠️ Aucune ligne filtrable trouvée (' + this.rowSelector + ')');
            return;
        }

        // Récupérer tous les inputs de filtre
        this.filterInputs = this.panel.querySelectorAll('input, select');

        // Fermer le panneau en cliquant à l'extérieur
        this.setupClickOutside();

        // Support des touches clavier
        this.setupKeyboardShortcuts();

        console.log(`✅ Système de filtres initialisé - ${this.rows.length} lignes filtrables`);
    }

    /**
     * Ferme le panneau en cliquant à l'extérieur
     */
    setupClickOutside() {
        document.addEventListener('click', (e) => {
            const btn = document.getElementById('advancedFiltersBtn');
            if (!this.panel.contains(e.target) && !btn?.contains(e.target)) {
                this.closePanel();
            }
        });
    }

    /**
     * Configure les raccourcis clavier
     */
    setupKeyboardShortcuts() {
        document.addEventListener('keydown', (e) => {
            // Échap pour fermer
            if (e.key === 'Escape' && !this.panel.classList.contains('hidden')) {
                this.closePanel();
            }

            // Entrée pour appliquer les filtres
            if (e.key === 'Enter' && !this.panel.classList.contains('hidden')) {
                e.preventDefault();
                this.applyFilters();
            }
        });
    }

    /**
     * Bascule l'affichage du panneau
     */
    togglePanel() {
        const isHidden = this.panel.classList.contains('hidden');
        const btn = document.getElementById('advancedFiltersBtn');

        if (isHidden) {
            this.panel.classList.remove('hidden');
            btn?.setAttribute('aria-expanded', 'true');
            // Focus sur le premier input
            const firstInput = this.panel.querySelector('input, select');
            firstInput?.focus();
        } else {
            this.closePanel();
        }
    }

    /**
     * Ferme le panneau
     */
    closePanel() {
        this.panel.classList.add('hidden');
        const btn = document.getElementById('advancedFiltersBtn');
        btn?.setAttribute('aria-expanded', 'false');
    }

    /**
     * Applique les filtres
     */
    applyFilters() {
        // Récupérer les valeurs des filtres
        this.activeFilters = {};
        let activeCount = 0;

        this.filterInputs.forEach(input => {
            const value = input.value.trim();
            if (value !== '') {
                const field = input.dataset.field;
                const filterType = input.dataset.filterType || 'text';

                this.activeFilters[input.id] = {
                    value: value,
                    field: field,
                    type: filterType
                };
                activeCount++;
            }
        });

        // Appliquer les filtres sur les lignes
        const matchCount = this.filterRows();

        // Mettre à jour l'interface
        this.updateUI(matchCount, activeCount);

        // Fermer le panneau
        this.closePanel();

        console.log(`🎯 Filtres appliqués - ${activeCount} filtre(s) actif(s) - ${matchCount} résultat(s)`);
    }

    /**
     * Filtre les lignes du tableau
     * @returns {number} Nombre de lignes correspondantes
     */
    filterRows() {
        let matchCount = 0;

        this.rows.forEach(row => {
            const matches = this.checkRowMatches(row);

            if (matches) {
                row.style.display = '';
                row.classList.add('filter-match');
                matchCount++;
            } else {
                row.style.display = 'none';
                row.classList.remove('filter-match');
            }
        });

        return matchCount;
    }

    /**
     * Vérifie si une ligne correspond aux filtres
     * @param {HTMLElement} row Ligne à vérifier
     * @returns {boolean} true si la ligne correspond
     */
    checkRowMatches(row) {
        // Parcourir tous les filtres actifs
        for (const [filterId, filter] of Object.entries(this.activeFilters)) {
            const rowValue = this.getRowValue(row, filter.field);

            if (!this.matchesFilter(rowValue, filter)) {
                return false; // Ne correspond pas à ce filtre
            }
        }

        return true; // Correspond à tous les filtres
    }

    /**
     * Récupère la valeur d'un champ dans une ligne
     * @param {HTMLElement} row Ligne du tableau
     * @param {string} field Nom du champ
     * @returns {string} Valeur du champ
     */
    getRowValue(row, field) {
        // Convertir camelCase en kebab-case pour data-attributes
        const dataAttr = 'data-' + field.replace(/([A-Z])/g, '-$1').toLowerCase();
        return row.getAttribute(dataAttr) || '';
    }

    /**
     * Vérifie si une valeur correspond à un filtre
     * @param {string} rowValue Valeur de la ligne
     * @param {Object} filter Configuration du filtre
     * @returns {boolean} true si correspond
     */
    matchesFilter(rowValue, filter) {
        const filterValue = filter.value;
        const filterType = filter.type;

        switch (filterType) {
            case 'text':
            case 'email':
                // Recherche insensible à la casse
                return rowValue.toLowerCase().includes(filterValue.toLowerCase());

            case 'number':
                // Comparaison exacte
                return parseFloat(rowValue) === parseFloat(filterValue);

            case 'min':
                // Valeur >= minimum
                return parseFloat(rowValue) >= parseFloat(filterValue);

            case 'max':
                // Valeur <= maximum
                return parseFloat(rowValue) <= parseFloat(filterValue);

            case 'date':
                // Comparaison de dates (format flexible)
                return this.compareDates(rowValue, filterValue);

            default:
                // Par défaut, recherche exacte
                return rowValue === filterValue;
        }
    }

    /**
     * Compare deux dates (supporte plusieurs formats)
     * @param {string} dateStr1 Date de la ligne (peut être dd/mm/yyyy)
     * @param {string} dateStr2 Date du filtre (yyyy-mm-dd)
     * @returns {boolean} true si même jour
     */
    compareDates(dateStr1, dateStr2) {
        if (!dateStr1 || !dateStr2) return false;

        try {
            // Convertir la date de la ligne (dd/mm/yyyy → Date)
            let date1;
            if (dateStr1.includes('/')) {
                const [day, month, year] = dateStr1.split('/');
                date1 = new Date(year, month - 1, day);
            } else {
                date1 = new Date(dateStr1);
            }

            // Date du filtre (yyyy-mm-dd)
            const date2 = new Date(dateStr2);

            // Comparer uniquement la date (ignorer l'heure)
            return date1.toDateString() === date2.toDateString();
        } catch (e) {
            console.warn('⚠️ Erreur de comparaison de dates:', dateStr1, dateStr2);
            return false;
        }
    }

    /**
     * Met à jour l'interface utilisateur
     * @param {number} matchCount Nombre de résultats
     * @param {number} activeCount Nombre de filtres actifs
     */
    updateUI(matchCount, activeCount) {
        // Mettre à jour le compteur de résultats
        const countEl = document.getElementById('filterResultCount');
        if (countEl) {
            countEl.textContent = matchCount;
        }

        // Afficher/masquer l'indicateur de résultats
        if (this.resultsDiv) {
            if (activeCount > 0) {
                this.resultsDiv.classList.remove('hidden');

                // Afficher les filtres actifs
                const activeFiltersText = document.getElementById('activeFiltersText');
                if (activeFiltersText) {
                    activeFiltersText.textContent = `(${activeCount} filtre(s) actif(s))`;
                }
            } else {
                this.resultsDiv.classList.add('hidden');
            }
        }

        // Mettre à jour le badge sur le bouton
        if (this.badge) {
            if (activeCount > 0) {
                this.badge.textContent = activeCount;
                this.badge.classList.remove('hidden');
            } else {
                this.badge.classList.add('hidden');
            }
        }
    }

    /**
     * Efface tous les filtres
     */
    clearFilters() {
        // Effacer tous les inputs
        this.filterInputs.forEach(input => {
            input.value = '';
        });

        // Réinitialiser l'état
        this.activeFilters = {};

        // Afficher toutes les lignes
        this.rows.forEach(row => {
            row.style.display = '';
            row.classList.remove('filter-match');
        });

        // Mettre à jour l'interface
        this.updateUI(this.rows.length, 0);

        console.log('🧹 Filtres effacés');
    }

    /**
     * Retourne le nombre de lignes visibles
     * @returns {number}
     */
    getVisibleRowsCount() {
        return Array.from(this.rows).filter(row => row.style.display !== 'none').length;
    }

    /**
     * Retourne les filtres actifs
     * @returns {Object}
     */
    getActiveFilters() {
        return { ...this.activeFilters };
    }
}

// ==========================================
// FONCTIONS GLOBALES (appelées depuis HTML)
// ==========================================

let globalFilterSystem;

/**
 * Initialise le système de filtres
 * @param {Object} config Configuration optionnelle
 */
function initFilterSystem(config = {}) {
    globalFilterSystem = new AdvancedFilterSystem(config);
    return globalFilterSystem;
}

/**
 * Bascule l'affichage du panneau de filtres
 */
function toggleAdvancedFilters() {
    if (globalFilterSystem) {
        globalFilterSystem.togglePanel();
    } else {
        console.error('❌ Système de filtres non initialisé. Appelez initFilterSystem() d\'abord.');
    }
}

/**
 * Applique les filtres
 */
function applyAdvancedFilters() {
    if (globalFilterSystem) {
        globalFilterSystem.applyFilters();
    } else {
        console.error('❌ Système de filtres non initialisé.');
    }
}

/**
 * Efface tous les filtres
 */
function clearAdvancedFilters() {
    if (globalFilterSystem) {
        globalFilterSystem.clearFilters();
    } else {
        console.error('❌ Système de filtres non initialisé.');
    }
}

// ==========================================
// AUTO-INITIALISATION (optionnel)
// ==========================================

// Auto-initialiser si les éléments sont présents
document.addEventListener('DOMContentLoaded', function() {
    if (document.getElementById('advancedFilters') && document.querySelectorAll('.filterable-row').length > 0) {
        console.log('🚀 Auto-initialisation du système de filtres...');
        initFilterSystem();
    }
});

// Exposer pour usage externe
window.AdvancedFilterSystem = AdvancedFilterSystem;
window.initFilterSystem = initFilterSystem;
window.globalFilterSystem = globalFilterSystem;
