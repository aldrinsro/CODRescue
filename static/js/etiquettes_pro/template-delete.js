/**
 * Gestionnaire de suppression des templates d'étiquettes
 * Utilise la même logique que bulk-delete.js pour une expérience utilisateur cohérente
 */

class TemplateDeleter {
    constructor() {
        this.isDeleting = false;
        this.init();
    }

    init() {
        console.log('🗑️ [TEMPLATE-DELETE] Initialisation de la suppression des templates');
        this.attachEventListeners();
    }

    attachEventListeners() {
        // Attacher les event listeners à tous les boutons de suppression de templates
        const deleteButtons = document.querySelectorAll('.template-delete-btn');
        
        deleteButtons.forEach(button => {
            button.addEventListener('click', (e) => {
                e.preventDefault();
                const templateId = button.dataset.templateId;
                const templateName = button.dataset.templateName;
                this.deleteTemplate(templateId, templateName);
            });
        });

        console.log(`✅ [TEMPLATE-DELETE] ${deleteButtons.length} boutons de suppression attachés`);
    }

    async deleteTemplate(templateId, templateName) {
        if (this.isDeleting) {
            console.log('⚠️ [TEMPLATE-DELETE] Suppression déjà en cours');
            return;
        }

        // Confirmation de suppression
        const confirmed = await this.showDeleteConfirmation(templateName);
        if (!confirmed) {
            return;
        }

        this.isDeleting = true;
        
        try {
            console.log(`🗑️ [TEMPLATE-DELETE] Début de la suppression du template ${templateId}`);

            const response = await fetch(`/etiquettes-pro/templates/${templateId}/delete/`, {
                method: 'DELETE',
                headers: {
                    'X-Requested-With': 'XMLHttpRequest',
                    'Content-Type': 'application/json',
                    'X-CSRFToken': this.getCSRFToken()
                }
            });

            if (!response.ok) {
                if (response.status === 404) {
                    throw new Error('Template non trouvé');
                } else {
                    throw new Error(`Erreur HTTP ${response.status}`);
                }
            }

            const data = await response.json();
            
            if (data.success) {
                this.showSuccess(data.message);
                console.log(`✅ [TEMPLATE-DELETE] Template ${templateId} supprimé avec succès`);
                
                // Rediriger vers la liste des templates après suppression
                setTimeout(() => {
                    window.location.href = '/etiquettes-pro/templates/';
                }, 1500);
            } else {
                this.showError(data.error || 'Erreur inconnue');
                console.warn(`⚠️ [TEMPLATE-DELETE] Erreur lors de la suppression du template ${templateId}:`, data.error);
            }

        } catch (error) {
            console.error(`❌ [TEMPLATE-DELETE] Erreur pour le template ${templateId}:`, error);
            this.showError(`Erreur de suppression: ${error.message}`);
        } finally {
            this.isDeleting = false;
        }
    }

    async showDeleteConfirmation(templateName) {
        const message = `Êtes-vous sûr de vouloir supprimer le template "${templateName}" ?`;
        
        return new Promise((resolve) => {
            // Créer une modal de confirmation personnalisée (même style que bulk-delete.js)
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

    getCSRFToken() {
        const token = document.querySelector('[name=csrfmiddlewaretoken]')?.value;
        if (!token) {
            console.warn('⚠️ [TEMPLATE-DELETE] Token CSRF non trouvé');
        }
        return token || '';
    }

    showSuccess(message) {
        console.log('✅ [TEMPLATE-DELETE]', message);
        this.showToast(message, 'success');
    }

    showError(message) {
        console.error('❌ [TEMPLATE-DELETE]', message);
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

// Initialiser la suppression des templates quand le DOM est prêt
document.addEventListener('DOMContentLoaded', () => {
    if (document.querySelector('.template-delete-btn')) {
        window.templateDeleter = new TemplateDeleter();
        console.log('✅ [TEMPLATE-DELETE] Gestionnaire de suppression des templates initialisé');
    }
});

// API publique
window.TemplateDeleter = TemplateDeleter;
