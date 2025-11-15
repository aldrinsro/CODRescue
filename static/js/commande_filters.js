/**
 * Gestion globale des filtres pour les pages de commandes
 * Ce fichier initialise les event listeners pour la soumission automatique des filtres
 *
 * Usage: Inclure ce script dans les pages qui utilisent le partial _filters.html
 * <script src="{% static 'js/commande_filters.js' %}"></script>
 */

(function() {
    'use strict';

    /**
     * Initialise les filtres de commandes avec soumission automatique
     */
    function initCommandeFilters() {
        const dateFilterSelect = document.getElementById('dateFilterSelect');
        const customDateRange = document.getElementById('customDateRange');
        const filterForm = document.querySelector('form[method="get"]');

        // Gestion du filtre de date personnalisé
        if (dateFilterSelect && customDateRange) {
            dateFilterSelect.addEventListener('change', function() {
                if (this.value === 'custom') {
                    customDateRange.classList.remove('hidden');
                    // Ne pas soumettre le formulaire, attendre que l'utilisateur sélectionne les dates
                } else {
                    customDateRange.classList.add('hidden');
                    // Soumettre le formulaire pour appliquer ou réinitialiser le filtre
                    if (filterForm) {
                        filterForm.submit();
                    }
                }
            });
        }

        // Gestion du filtre de synchronisation personnalisé
        const syncFilter = document.getElementById('syncFilter');
        const customSyncDate = document.getElementById('customSyncDate');

        if (syncFilter && customSyncDate) {
            syncFilter.addEventListener('change', function() {
                if (this.value === 'custom_date') {
                    customSyncDate.classList.remove('hidden');
                    // Ne pas soumettre, attendre la sélection de date
                } else {
                    customSyncDate.classList.add('hidden');
                    // Soumettre le formulaire pour appliquer le filtre
                    if (filterForm) {
                        filterForm.submit();
                    }
                }
            });
        }

        // Soumettre le formulaire quand l'utilisateur change les dates personnalisées
        const dateStartInput = document.querySelector('input[name="date_start"]');
        const dateEndInput = document.querySelector('input[name="date_end"]');

        if (dateStartInput && dateEndInput && filterForm) {
            dateStartInput.addEventListener('change', function() {
                // Si les deux dates sont remplies, soumettre
                if (this.value && dateEndInput.value) {
                    filterForm.submit();
                }
            });

            dateEndInput.addEventListener('change', function() {
                // Si les deux dates sont remplies, soumettre
                if (this.value && dateStartInput.value) {
                    filterForm.submit();
                }
            });
        }

        // Soumettre le formulaire quand l'utilisateur change la date de sync personnalisée
        if (customSyncDate && filterForm) {
            customSyncDate.addEventListener('change', function() {
                if (this.value) {
                    filterForm.submit();
                }
            });
        }

        // Soumettre le formulaire quand le tri change
        const orderBySelect = document.querySelector('select[name="order_by"]');
        if (orderBySelect && filterForm) {
            orderBySelect.addEventListener('change', function() {
                filterForm.submit();
            });
        }
    }

    // Initialiser au chargement du DOM
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', initCommandeFilters);
    } else {
        // DOM déjà chargé
        initCommandeFilters();
    }

    // Exposer la fonction globalement si besoin
    window.initCommandeFilters = initCommandeFilters;

})();
