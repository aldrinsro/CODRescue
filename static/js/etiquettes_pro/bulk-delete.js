/**
 * Gestionnaire de suppression multiple des étiquettes
 * Permet de supprimer plusieurs étiquettes sélectionnées en une seule action
 */

class BulkEtiquetteDeleter {
    constructor() {
        this.selectedEtiquettes = new Set();
        this.isDeleting = false;
        this.init();
    }

    init() {
        console.log('🗑️ [BULK-DELETE] Initialisation de la suppression multiple');
        this.attachEventListeners();
        this.updateUI();
    }

    attachEventListeners() {
        // Bouton de suppression en lot
        const bulkDeleteBtn = document.getElementById('bulk-delete-btn');
        if (bulkDeleteBtn) {
            bulkDeleteBtn.addEventListener('click', () => this.deleteSelected());
        }

        console.log('✅ [BULK-DELETE] Event listeners attachés');
    }

    updateUI() {
        const toolbar = document.getElementById('bulk-actions-toolbar');
        const bulkDeleteBtn = document.getElementById('bulk-delete-btn');

        // Les boutons restent toujours actifs
        if (bulkDeleteBtn) bulkDeleteBtn.disabled = false;
    }

    // Méthode pour synchroniser avec le gestionnaire de sélection
    syncWithBulkPrinter(bulkPrinter) {
        this.selectedEtiquettes = bulkPrinter.selectedEtiquettes;
        this.updateUI();
    }

    async deleteSelected() {
        if (this.isDeleting) {
            console.log('⚠️ [BULK-DELETE] Suppression déjà en cours');
            return;
        }

        if (this.selectedEtiquettes.size === 0) {
            this.showError('Aucune étiquette sélectionnée');
            return;
        }

        // Confirmation de suppression
        const confirmed = await this.showDeleteConfirmation();
        if (!confirmed) {
            return;
        }

        this.isDeleting = true;
        const bulkDeleteBtn = document.getElementById('bulk-delete-btn');
        const originalText = bulkDeleteBtn.innerHTML;
        
        try {
            bulkDeleteBtn.disabled = true;
            bulkDeleteBtn.innerHTML = '<i class="fas fa-spinner fa-spin mr-2"></i>Suppression...';

            console.log(`🗑️ [BULK-DELETE] Début de la suppression de ${this.selectedEtiquettes.size} étiquettes`);

            // Supprimer les étiquettes une par une
            const results = await this.deleteEtiquettes();
            
            // Afficher les résultats
            this.showDeleteResults(results);

            // Recharger la page pour mettre à jour l'affichage
            setTimeout(() => {
                window.location.reload();
            }, 2000);

            console.log('✅ [BULK-DELETE] Suppression multiple terminée');

        } catch (error) {
            console.error('❌ [BULK-DELETE] Erreur lors de la suppression multiple:', error);
            this.showError(`Erreur de suppression: ${error.message}`);
        } finally {
            this.isDeleting = false;
            bulkDeleteBtn.disabled = false;
            bulkDeleteBtn.innerHTML = originalText;
        }
    }

    async showDeleteConfirmation() {
        const count = this.selectedEtiquettes.size;
        const message = count === 1 
            ? 'Êtes-vous sûr de vouloir supprimer cette étiquette ?'
            : `Êtes-vous sûr de vouloir supprimer ces ${count} étiquettes ?`;
        
        return new Promise((resolve) => {
            // Créer une modal de confirmation personnalisée
            const modal = this.createConfirmationModal(message, resolve);
            document.body.appendChild(modal);
        });
    }

    createConfirmationModal(message, callback) {
        const modal = document.createElement('div');
        modal.className = 'fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50';
        modal.innerHTML = `
            <div class="bg-white rounded-lg p-6 max-w-md w-full mx-4">
                <div class="flex items-center mb-4">
                    <i class="fas fa-exclamation-triangle text-red-500 text-2xl mr-3"></i>
                    <h3 class="text-lg font-semibold text-gray-900">Confirmation de suppression</h3>
                </div>
                <p class="text-gray-600 mb-6">${message}</p>
                <p class="text-sm text-red-600 mb-6">
                    <i class="fas fa-info-circle mr-1"></i>
                    Cette action est irréversible.
                </p>
                <div class="flex justify-end space-x-3">
                    <button id="cancel-delete" class="px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-md hover:bg-gray-50">
                        Annuler
                    </button>
                    <button id="confirm-delete" class="px-4 py-2 text-sm font-medium text-white bg-red-600 border border-transparent rounded-md hover:bg-red-700">
                        <i class="fas fa-trash mr-1"></i>Supprimer
                    </button>
                </div>
            </div>
        `;

        // Event listeners pour les boutons
        modal.querySelector('#cancel-delete').addEventListener('click', () => {
            document.body.removeChild(modal);
            callback(false);
        });

        modal.querySelector('#confirm-delete').addEventListener('click', () => {
            document.body.removeChild(modal);
            callback(true);
        });

        // Fermer avec Escape
        const handleEscape = (e) => {
            if (e.key === 'Escape') {
                document.body.removeChild(modal);
                document.removeEventListener('keydown', handleEscape);
                callback(false);
            }
        };
        document.addEventListener('keydown', handleEscape);

        return modal;
    }

    async deleteEtiquettes() {
        const results = {
            success: [],
            errors: []
        };

        const etiquetteIds = Array.from(this.selectedEtiquettes);

        for (const etiquetteId of etiquetteIds) {
            try {
                console.log(`🗑️ [BULK-DELETE] Suppression de l'étiquette ${etiquetteId}`);
                
                const response = await fetch(`/etiquettes-pro/etiquettes/${etiquetteId}/delete/`, {
                    method: 'DELETE',
                    headers: {
                        'X-Requested-With': 'XMLHttpRequest',
                        'Content-Type': 'application/json',
                        'X-CSRFToken': this.getCSRFToken()
                    }
                });

                if (!response.ok) {
                    if (response.status === 404) {
                        console.warn(`⚠️ [BULK-DELETE] Étiquette ${etiquetteId} non trouvée`);
                        results.errors.push({
                            id: etiquetteId,
                            error: 'Étiquette non trouvée'
                        });
                        continue;
                    } else {
                        throw new Error(`Erreur HTTP ${response.status} pour l'étiquette ${etiquetteId}`);
                    }
                }

                const data = await response.json();
                
                if (data.success) {
                    results.success.push({
                        id: etiquetteId,
                        reference: data.reference || etiquetteId
                    });
                    console.log(`✅ [BULK-DELETE] Étiquette ${etiquetteId} supprimée avec succès`);
                } else {
                    results.errors.push({
                        id: etiquetteId,
                        error: data.error || 'Erreur inconnue'
                    });
                    console.warn(`⚠️ [BULK-DELETE] Erreur lors de la suppression de l'étiquette ${etiquetteId}:`, data.error);
                }

            } catch (error) {
                console.error(`❌ [BULK-DELETE] Erreur pour l'étiquette ${etiquetteId}:`, error);
                results.errors.push({
                    id: etiquetteId,
                    error: error.message
                });
            }
        }

        return results;
    }

    showDeleteResults(results) {
        const successCount = results.success.length;
        const errorCount = results.errors.length;

        if (successCount > 0 && errorCount === 0) {
            // Toutes les suppressions ont réussi
            this.showSuccess(`${successCount} étiquette(s) supprimée(s) avec succès`);
        } else if (successCount > 0 && errorCount > 0) {
            // Suppressions partielles
            this.showWarning(`${successCount} étiquette(s) supprimée(s), ${errorCount} erreur(s)`);
        } else if (errorCount > 0) {
            // Toutes les suppressions ont échoué
            this.showError(`Aucune étiquette supprimée. ${errorCount} erreur(s)`);
        }

        // Log des erreurs détaillées
        if (errorCount > 0) {
            console.error('❌ [BULK-DELETE] Erreurs détaillées:', results.errors);
        }
    }

    getCSRFToken() {
        const token = document.querySelector('[name=csrfmiddlewaretoken]')?.value;
        if (!token) {
            console.warn('⚠️ [BULK-DELETE] Token CSRF non trouvé');
        }
        return token || '';
    }

    showSuccess(message) {
        console.log('✅ [BULK-DELETE]', message);
        this.showToast(message, 'success');
    }

    showWarning(message) {
        console.warn('⚠️ [BULK-DELETE]', message);
        this.showToast(message, 'warning');
    }

    showError(message) {
        console.error('❌ [BULK-DELETE]', message);
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

// Initialiser la suppression multiple quand le DOM est prêt
document.addEventListener('DOMContentLoaded', () => {
    if (document.querySelector('.etiquette-checkbox')) {
        window.bulkEtiquetteDeleter = new BulkEtiquetteDeleter();
        console.log('✅ [BULK-DELETE] Gestionnaire de suppression multiple initialisé');
        
        // Synchroniser avec le gestionnaire d'impression si disponible
        if (window.bulkEtiquettePrinter) {
            // Observer les changements de sélection
            const originalUpdateUI = window.bulkEtiquettePrinter.updateUI;
            window.bulkEtiquettePrinter.updateUI = function() {
                originalUpdateUI.call(this);
                if (window.bulkEtiquetteDeleter) {
                    window.bulkEtiquetteDeleter.syncWithBulkPrinter(this);
                }
            };
        }
    }
});

// API publique
window.BulkEtiquetteDeleter = BulkEtiquetteDeleter;
