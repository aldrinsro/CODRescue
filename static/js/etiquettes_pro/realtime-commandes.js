/**
 * Système de gestion en temps réel des commandes avec paniers
 * Affiche dynamiquement les commandes qui ont des paniers et permet la génération d'étiquettes
 */

class RealtimeCommandesManager {
    constructor() {
        this.commandes = [];
        this.refreshInterval = null;
        this.countdownInterval = null;
        this.isGenerating = false;
        this.refreshIntervalSeconds = 30;
        this.countdownSeconds = 30;
        this.init();
    }

    init() {
        console.log('🚀 [REALTIME-COMMANDES] Initialisation du gestionnaire de commandes en temps réel');
        this.attachEventListeners();
        this.loadCommandes();
        this.startAutoRefresh();
    }

    attachEventListeners() {
        // Bouton d'actualisation
        const refreshBtn = document.getElementById('refresh-commandes');
        if (refreshBtn) {
            refreshBtn.addEventListener('click', () => {
                this.loadCommandes(true);
            });
        }

        // Bouton de génération de toutes les étiquettes
        const generateBtn = document.getElementById('generate-all-etiquettes');
        if (generateBtn) {
            generateBtn.addEventListener('click', () => {
                this.generateAllEtiquettes();
            });
        }
    }

    async loadCommandes(showLoading = false) {
        try {
            if (showLoading) {
                this.showLoading();
            }

            console.log('🔄 [REALTIME-COMMANDES] Chargement des commandes avec paniers...');
            
            const controller = new AbortController();
            const timeoutId = setTimeout(() => controller.abort(), 10000); // Timeout de 10 secondes
            
            const response = await fetch('/etiquettes-pro/api/commandes-with-paniers/', {
                method: 'GET',
                headers: {
                    'X-CSRFToken': this.getCSRFToken(),
                    'Content-Type': 'application/json',
                },
                signal: controller.signal
            });

            clearTimeout(timeoutId);

            if (!response.ok) {
                const errorData = await response.json().catch(() => ({}));
                throw new Error(errorData.error || `Erreur HTTP: ${response.status}`);
            }

            const data = await response.json();
            console.log('✅ [REALTIME-COMMANDES] Commandes chargées:', data);

            this.commandes = data.commandes || [];
            this.updateUI();
            this.updateCount();

        } catch (error) {
            if (error.name === 'AbortError') {
                console.warn('⚠️ [REALTIME-COMMANDES] Requête annulée (timeout)');
                this.showError('Timeout lors du chargement des commandes');
            } else {
                console.error('❌ [REALTIME-COMMANDES] Erreur lors du chargement:', error);
                this.showError(`Erreur lors du chargement des commandes: ${error.message}`);
            }
        }
    }

    updateUI() {
        const commandesList = document.getElementById('commandes-list');
        const noCommandes = document.getElementById('no-commandes');
        const loading = document.getElementById('commandes-loading');

        console.log('🔄 [REALTIME-COMMANDES] updateUI - Nombre de commandes:', this.commandes.length);
        console.log('🔄 [REALTIME-COMMANDES] Éléments trouvés:', {
            commandesList: !!commandesList,
            noCommandes: !!noCommandes,
            loading: !!loading
        });

        // Masquer le loading
        if (loading) {
            loading.classList.add('hidden');
        }

        if (this.commandes.length === 0) {
            // Aucune commande sans étiquette
            console.log('✅ [REALTIME-COMMANDES] Aucune commande - Affichage du message "Toutes les commandes ont des étiquettes"');
            if (commandesList) {
                commandesList.classList.add('hidden');
            }
            if (noCommandes) {
                noCommandes.classList.remove('hidden');
                console.log('✅ [REALTIME-COMMANDES] Message "no-commandes" affiché');
            }
        } else {
            // Afficher les commandes
            console.log('📋 [REALTIME-COMMANDES] Commandes disponibles - Masquage du message');
            if (noCommandes) {
                noCommandes.classList.add('hidden');
                console.log('✅ [REALTIME-COMMANDES] Message "no-commandes" masqué');
            }
            if (commandesList) {
                commandesList.classList.remove('hidden');
                commandesList.innerHTML = this.generateCommandesHTML();
            }
        }
    }

    generateCommandesHTML() {
        const html = this.commandes.map(commande => `
            <div class="commande-card bg-gray-50 border border-gray-200 rounded-lg p-4 hover:shadow-md transition-shadow">
                <div class="flex items-center justify-between">
                    <div class="flex-1">
                        <div class="flex items-center space-x-3 mb-2">
                            <h3 class="font-semibold text-gray-800">Commande #${commande.num_cmd}</h3>
                            <span class="px-2 py-1 bg-blue-100 text-blue-800 text-xs font-medium rounded-full">
                                ${commande.total_articles} article(s)
                            </span>
                        </div>
                        <div class="text-sm text-gray-600 space-y-1">
                            <div><i class="fas fa-user mr-2"></i><strong>Client:</strong> ${commande.client_nom}</div>
                            ${commande.client_telephone ? `<div><i class="fas fa-phone mr-2"></i><strong>Tél:</strong> ${commande.client_telephone}</div>` : ''}
                            ${commande.ville_init ? `<div><i class="fas fa-map-marker-alt mr-2"></i><strong>Ville:</strong> ${commande.ville_init}</div>` : ''}
                            <div><i class="fas fa-calendar mr-2"></i><strong>Date:</strong> ${commande.date_creation}</div>
                        </div>
                    </div>
                    <div class="flex items-center space-x-2">
                        <button class="generate-single-etiquette-btn theme-button-primary text-sm" data-commande-id="${commande.id}">
                            <i class="fas fa-magic mr-1"></i>Générer Étiquette
                        </button>
                    </div>
                </div>
            </div>
        `).join('');

        // Attacher les événements aux boutons de génération individuelle après le rendu
        setTimeout(() => {
            this.attachSingleGenerateEvents();
        }, 100);

        return html;
    }

    attachSingleGenerateEvents() {
        const generateBtns = document.querySelectorAll('.generate-single-etiquette-btn');
        generateBtns.forEach(btn => {
            // Supprimer les anciens événements pour éviter les doublons
            btn.removeEventListener('click', this.handleSingleGenerateClick);
            
            // Ajouter le nouvel événement
            btn.addEventListener('click', this.handleSingleGenerateClick.bind(this));
        });
    }

    handleSingleGenerateClick(e) {
        e.preventDefault();
        e.stopPropagation();
        
        const button = e.target.closest('.generate-single-etiquette-btn');
        if (!button || button.disabled) {
            return;
        }
        
        const commandeId = button.dataset.commandeId;
        if (!commandeId) {
            console.error('❌ [REALTIME-COMMANDES] ID de commande manquant');
            this.showError('ID de commande manquant');
            return;
        }
        
        this.generateSingleEtiquette(commandeId);
    }

    updateCount() {
        const countElement = document.getElementById('commandes-count');
        const generateBtn = document.getElementById('generate-all-etiquettes');
        
        if (countElement) {
            countElement.textContent = this.commandes.length;
        }
        
        if (generateBtn) {
            generateBtn.disabled = this.commandes.length === 0 || this.isGenerating;
        }
    }

    async generateAllEtiquettes() {
        if (this.isGenerating || this.commandes.length === 0) {
            return;
        }

        this.isGenerating = true;
        this.updateGenerateButton(true);

        try {
            console.log('🔄 [REALTIME-COMMANDES] Génération de toutes les étiquettes...');
            
            const controller = new AbortController();
            const timeoutId = setTimeout(() => controller.abort(), 30000); // Timeout de 30 secondes pour la génération
            
            const response = await fetch('/etiquettes-pro/generate-etiquettes-manually/', {
                method: 'POST',
                headers: {
                    'X-CSRFToken': this.getCSRFToken(),
                    'Content-Type': 'application/json',
                },
                signal: controller.signal
            });

            clearTimeout(timeoutId);

            if (!response.ok) {
                const errorData = await response.json().catch(() => ({}));
                throw new Error(errorData.error || `Erreur HTTP: ${response.status}`);
            }

            const data = await response.json();
            console.log('✅ [REALTIME-COMMANDES] Génération terminée:', data);

            if (data.success) {
                this.showSuccess(data.message);
                // Recharger les commandes après génération
                setTimeout(() => {
                    this.loadCommandes();
                }, 1000);
            } else {
                this.showError(data.error || 'Erreur lors de la génération');
            }

        } catch (error) {
            if (error.name === 'AbortError') {
                console.warn('⚠️ [REALTIME-COMMANDES] Génération annulée (timeout)');
                this.showError('Timeout lors de la génération des étiquettes');
            } else {
                console.error('❌ [REALTIME-COMMANDES] Erreur lors de la génération:', error);
                this.showError(`Erreur lors de la génération des étiquettes: ${error.message}`);
            }
        } finally {
            this.isGenerating = false;
            this.updateGenerateButton(false);
        }
    }

    async generateSingleEtiquette(commandeId) {
        try {
            console.log('🔄 [REALTIME-COMMANDES] Génération d\'étiquette pour commande:', commandeId);
            
            // Désactiver le bouton pendant la génération
            const button = document.querySelector(`[data-commande-id="${commandeId}"]`);
            if (button) {
                button.disabled = true;
                button.innerHTML = '<i class="fas fa-spinner fa-spin mr-1"></i>Génération...';
            }
            
            const controller = new AbortController();
            const timeoutId = setTimeout(() => controller.abort(), 15000); // Timeout de 15 secondes pour la génération individuelle
            
            const response = await fetch('/etiquettes-pro/generate-etiquettes-manually/', {
                method: 'POST',
                headers: {
                    'X-CSRFToken': this.getCSRFToken(),
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ commande_id: parseInt(commandeId) }),
                signal: controller.signal
            });

            clearTimeout(timeoutId);

            if (!response.ok) {
                const errorData = await response.json().catch(() => ({}));
                throw new Error(errorData.error || `Erreur HTTP: ${response.status}`);
            }

            const data = await response.json();
            console.log('✅ [REALTIME-COMMANDES] Génération individuelle terminée:', data);

            if (data.success) {
                this.showSuccess(`Étiquette générée avec succès pour la commande ${commandeId}`);
                // Recharger les commandes après génération
                setTimeout(() => {
                    this.loadCommandes();
                }, 1000);
            } else {
                this.showError(data.error || 'Erreur lors de la génération');
            }

        } catch (error) {
            if (error.name === 'AbortError') {
                console.warn('⚠️ [REALTIME-COMMANDES] Génération individuelle annulée (timeout)');
                this.showError('Timeout lors de la génération de l\'étiquette');
            } else {
                console.error('❌ [REALTIME-COMMANDES] Erreur lors de la génération individuelle:', error);
                this.showError(`Erreur lors de la génération de l'étiquette: ${error.message}`);
            }
        } finally {
            // Réactiver le bouton
            const button = document.querySelector(`[data-commande-id="${commandeId}"]`);
            if (button) {
                button.disabled = false;
                button.innerHTML = '<i class="fas fa-magic mr-1"></i>Générer Étiquette';
            }
        }
    }

    updateGenerateButton(isGenerating) {
        const generateBtn = document.getElementById('generate-all-etiquettes');
        if (generateBtn) {
            if (isGenerating) {
                generateBtn.innerHTML = '<i class="fas fa-spinner fa-spin mr-1"></i>Génération...';
                generateBtn.disabled = true;
            } else {
                generateBtn.innerHTML = '<i class="fas fa-magic mr-1"></i>Générer Toutes les Étiquettes';
                generateBtn.disabled = this.commandes.length === 0;
            }
        }
    }

    showLoading() {
        const loading = document.getElementById('commandes-loading');
        const commandesList = document.getElementById('commandes-list');
        const noCommandes = document.getElementById('no-commandes');
        
        if (loading) loading.classList.remove('hidden');
        if (commandesList) commandesList.classList.add('hidden');
        if (noCommandes) noCommandes.classList.add('hidden');
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

    startAutoRefresh() {
        // Actualisation automatique toutes les 30 secondes
        this.refreshInterval = setInterval(() => {
            this.loadCommandes();
            this.countdownSeconds = this.refreshIntervalSeconds;
        }, this.refreshIntervalSeconds * 1000);
        
        // Démarrer le compteur
        this.startCountdown();
        
        console.log(`🔄 [REALTIME-COMMANDES] Actualisation automatique activée (${this.refreshIntervalSeconds}s)`);
    }

    startCountdown() {
        this.countdownInterval = setInterval(() => {
            this.countdownSeconds--;
            this.updateCountdownDisplay();
            
            if (this.countdownSeconds <= 0) {
                this.countdownSeconds = this.refreshIntervalSeconds;
            }
        }, 1000);
    }

    updateCountdownDisplay() {
        const indicator = document.getElementById('auto-refresh-indicator');
        if (indicator) {
            const span = indicator.querySelector('span');
            if (span) {
                span.textContent = `Auto-actualisation: ${this.countdownSeconds}s`;
            }
        }
    }

    stopAutoRefresh() {
        if (this.refreshInterval) {
            clearInterval(this.refreshInterval);
            this.refreshInterval = null;
        }
        if (this.countdownInterval) {
            clearInterval(this.countdownInterval);
            this.countdownInterval = null;
        }
        console.log('⏹️ [REALTIME-COMMANDES] Actualisation automatique arrêtée');
    }

    getCSRFToken() {
        const token = document.querySelector('[name=csrfmiddlewaretoken]');
        return token ? token.value : '';
    }

    destroy() {
        this.stopAutoRefresh();
        console.log('🗑️ [REALTIME-COMMANDES] Gestionnaire détruit');
    }
}

// API publique
window.RealtimeCommandesManager = RealtimeCommandesManager;

// Auto-initialisation
document.addEventListener('DOMContentLoaded', function() {
    console.log('🚀 [REALTIME-COMMANDES] DOM chargé - Recherche du conteneur commandes-container');
    const container = document.getElementById('commandes-container');
    if (container) {
        console.log('✅ [REALTIME-COMMANDES] Conteneur trouvé - Initialisation du gestionnaire');
        window.realtimeCommandesManager = new RealtimeCommandesManager();
    } else {
        console.warn('⚠️ [REALTIME-COMMANDES] Conteneur commandes-container non trouvé');
    }
});
