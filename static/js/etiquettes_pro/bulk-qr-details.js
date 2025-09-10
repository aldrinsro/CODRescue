/**
 * Script pour l'impression multiple des codes QR avec détails
 * Gère la sélection et l'impression des codes QR avec détails pour plusieurs étiquettes
 */

class BulkQRDetailsPrinter {
    constructor() {
        this.selectedEtiquettes = new Set();
        this.init();
    }

    init() {
        console.log('🚀 [BULK-QR-DETAILS] Initialisation...');
        
        // Attendre que le DOM soit chargé
        if (document.readyState === 'loading') {
            document.addEventListener('DOMContentLoaded', () => this.setupEventListeners());
        } else {
            this.setupEventListeners();
        }
    }

    setupEventListeners() {
        console.log('🔧 [BULK-QR-DETAILS] Configuration des événements...');
        
        // Bouton d'impression multiple des codes QR avec détails
        const bulkQRDetailsBtn = document.getElementById('bulk-qr-details-btn');
        if (bulkQRDetailsBtn) {
            bulkQRDetailsBtn.addEventListener('click', () => this.printSelectedQRDetails());
            console.log('✅ [BULK-QR-DETAILS] Bouton d\'impression multiple configuré');
        } else {
            console.warn('⚠️ [BULK-QR-DETAILS] Bouton bulk-qr-details-btn non trouvé');
        }

        // Écouter les changements de sélection
        this.observeSelectionChanges();
        
        // Mettre à jour l'interface initiale
        this.updateUI();
    }

    observeSelectionChanges() {
        // Observer les changements dans les checkboxes
        const checkboxes = document.querySelectorAll('input[type="checkbox"][data-etiquette-id]');
        checkboxes.forEach(checkbox => {
            checkbox.addEventListener('change', () => {
                this.handleCheckboxChange(checkbox);
            });
        });

        // Observer les boutons de sélection globale
        const selectAllBtn = document.getElementById('select-all-btn');
        const deselectAllBtn = document.getElementById('deselect-all-btn');
        
        if (selectAllBtn) {
            selectAllBtn.addEventListener('click', () => this.selectAll());
        }
        
        if (deselectAllBtn) {
            deselectAllBtn.addEventListener('click', () => this.deselectAll());
        }
    }

    handleCheckboxChange(checkbox) {
        const etiquetteId = checkbox.dataset.etiquetteId;
        
        if (checkbox.checked) {
            this.selectedEtiquettes.add(etiquetteId);
        } else {
            this.selectedEtiquettes.delete(etiquetteId);
        }
        
        this.updateUI();
        console.log(`📋 [BULK-QR-DETAILS] Sélection mise à jour: ${this.selectedEtiquettes.size} étiquettes`);
    }

    selectAll() {
        console.log('📋 [BULK-QR-DETAILS] Sélection de toutes les étiquettes...');
        
        const checkboxes = document.querySelectorAll('input[type="checkbox"][data-etiquette-id]');
        checkboxes.forEach(checkbox => {
            checkbox.checked = true;
            this.selectedEtiquettes.add(checkbox.dataset.etiquetteId);
        });
        
        this.updateUI();
    }

    deselectAll() {
        console.log('📋 [BULK-QR-DETAILS] Désélection de toutes les étiquettes...');
        
        const checkboxes = document.querySelectorAll('input[type="checkbox"][data-etiquette-id]');
        checkboxes.forEach(checkbox => {
            checkbox.checked = false;
        });
        
        this.selectedEtiquettes.clear();
        this.updateUI();
    }

    updateUI() {
        const bulkQRDetailsBtn = document.getElementById('bulk-qr-details-btn');
        const toolbar = document.querySelector('.bulk-actions-toolbar');
        
        if (bulkQRDetailsBtn) {
            if (this.selectedEtiquettes.size > 0) {
                bulkQRDetailsBtn.disabled = false;
                bulkQRDetailsBtn.classList.remove('opacity-50', 'cursor-not-allowed');
                bulkQRDetailsBtn.classList.add('hover:bg-green-700');
            } else {
                bulkQRDetailsBtn.disabled = false; // Toujours actif selon les nouvelles règles
                bulkQRDetailsBtn.classList.remove('opacity-50', 'cursor-not-allowed');
                bulkQRDetailsBtn.classList.add('hover:bg-green-700');
            }
        }
        
        if (toolbar) {
            toolbar.classList.remove('hidden');
        }
        
        // Mettre à jour le compteur de sélection
        const counter = document.querySelector('.selection-counter');
        if (counter) {
            counter.textContent = `${this.selectedEtiquettes.size} étiquette(s) sélectionnée(s)`;
        }
    }

    async printSelectedQRDetails() {
        console.log('🖨️ [BULK-QR-DETAILS] Début de l\'impression multiple des codes QR avec détails...');
        
        if (this.selectedEtiquettes.size === 0) {
            this.showError('Veuillez sélectionner au moins une étiquette pour imprimer les codes QR avec détails.');
            return;
        }

        try {
            // Afficher un indicateur de chargement
            this.showLoading('Génération des codes QR avec détails...');

            // Préparer les données
            const formData = new FormData();
            this.selectedEtiquettes.forEach(id => {
                formData.append('etiquette_ids[]', id);
            });

            // Envoyer la requête
            const response = await fetch('/etiquettes-pro/bulk-print-qr-codes-details/', {
                method: 'POST',
                body: formData,
                headers: {
                    'X-CSRFToken': this.getCSRFToken(),
                },
            });

            if (!response.ok) {
                throw new Error(`Erreur HTTP: ${response.status}`);
            }

            // Vérifier si c'est une réponse JSON (erreur) ou HTML (succès)
            const contentType = response.headers.get('content-type');
            if (contentType && contentType.includes('application/json')) {
                const result = await response.json();
                if (!result.success) {
                    throw new Error(result.error || 'Erreur lors de la génération des codes QR');
                }
            }

            // Ouvrir la page d'impression dans une nouvelle fenêtre
            const printWindow = window.open('', '_blank');
            const htmlContent = await response.text();
            printWindow.document.write(htmlContent);
            printWindow.document.close();

            // Attendre que les images se chargent puis imprimer
            printWindow.addEventListener('load', () => {
                setTimeout(() => {
                    printWindow.print();
                }, 1000);
            });

            this.showSuccess(`${this.selectedEtiquettes.size} étiquette(s) sélectionnée(s) pour l'impression des codes QR avec détails.`);

        } catch (error) {
            console.error('❌ [BULK-QR-DETAILS] Erreur:', error);
            this.showError(`Erreur lors de l'impression des codes QR avec détails: ${error.message}`);
        } finally {
            this.hideLoading();
        }
    }

    getCSRFToken() {
        const token = document.querySelector('[name=csrfmiddlewaretoken]');
        return token ? token.value : '';
    }

    showLoading(message) {
        // Créer ou mettre à jour l'indicateur de chargement
        let loadingDiv = document.getElementById('bulk-qr-details-loading');
        if (!loadingDiv) {
            loadingDiv = document.createElement('div');
            loadingDiv.id = 'bulk-qr-details-loading';
            loadingDiv.className = 'fixed top-4 right-4 bg-green-500 text-white px-4 py-2 rounded-lg shadow-lg z-50';
            document.body.appendChild(loadingDiv);
        }
        loadingDiv.innerHTML = `<i class="fas fa-spinner fa-spin mr-2"></i>${message}`;
        loadingDiv.style.display = 'block';
    }

    hideLoading() {
        const loadingDiv = document.getElementById('bulk-qr-details-loading');
        if (loadingDiv) {
            loadingDiv.style.display = 'none';
        }
    }

    showSuccess(message) {
        this.showToast(message, 'success');
    }

    showError(message) {
        this.showToast(message, 'error');
    }

    showToast(message, type = 'info') {
        // Créer le conteneur de toast s'il n'existe pas
        let toastContainer = document.getElementById('toastContainer');
        if (!toastContainer) {
            toastContainer = document.createElement('div');
            toastContainer.id = 'toastContainer';
            toastContainer.className = 'fixed top-4 right-4 z-50';
            document.body.appendChild(toastContainer);
        }

        const toast = document.createElement('div');
        const bgColor = type === 'success' ? 'bg-green-500' : 
                       type === 'error' ? 'bg-red-500' : 
                       type === 'warning' ? 'bg-yellow-500' : 'bg-blue-500';
        
        toast.className = `${bgColor} text-white px-6 py-3 rounded-lg shadow-lg mb-2 max-w-md opacity-0 transform transition-all duration-300 ease-in-out`;
        
        const icon = type === 'success' ? 'fa-check-circle' : 
                    type === 'error' ? 'fa-exclamation-circle' : 
                    type === 'warning' ? 'fa-exclamation-triangle' : 'fa-info-circle';
        
        toast.innerHTML = `
            <div class="flex items-center space-x-2">
                <i class="fas ${icon} mr-2"></i>
                <span class="text-sm font-medium">${message}</span>
            </div>
        `;
        
        toastContainer.appendChild(toast);
        
        // Animation d'entrée
        requestAnimationFrame(() => {
            toast.classList.remove('opacity-0');
            toast.classList.add('opacity-100');
        });
        
        // Suppression automatique
        setTimeout(() => {
            toast.classList.remove('opacity-100');
            toast.classList.add('opacity-0');
            setTimeout(() => {
                if (toast.parentNode) {
                    toast.parentNode.removeChild(toast);
                }
            }, 300);
        }, 5000);
    }
}

// Initialiser automatiquement
document.addEventListener('DOMContentLoaded', function() {
    if (typeof window.bulkQRDetailsPrinter === 'undefined') {
        window.bulkQRDetailsPrinter = new BulkQRDetailsPrinter();
        console.log('✅ [BULK-QR-DETAILS] Module d\'impression multiple des codes QR avec détails initialisé');
    }
});

// Exposer la classe globalement
window.BulkQRDetailsPrinter = BulkQRDetailsPrinter;
