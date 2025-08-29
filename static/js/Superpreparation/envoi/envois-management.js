/**
 * Gestion des envois - Superpreparation
 * Fonctionnalités pour la création, clôture et export des envois
 */

// Toast notification system
function showToast(message, type = 'info', duration = 4000) {
    const toastContainer = document.getElementById('toastContainer');
    if (!toastContainer) {
        console.warn('Toast container not found');
        return;
    }
    
    const toast = document.createElement('div');
    toast.className = `toast ${type}`;
    
    const icon = {
        success: 'fas fa-check-circle',
        error: 'fas fa-exclamation-circle',
        info: 'fas fa-info-circle',
        warning: 'fas fa-exclamation-triangle'
    }[type];
    
    toast.innerHTML = `
        <div class="flex items-center">
            <i class="${icon} mr-3 text-lg"></i>
            <div class="flex-1">
                <p class="font-medium">${message}</p>
            </div>
            <button onclick="this.parentElement.parentElement.remove()" class="ml-3 text-gray-400 hover:text-gray-600">
                <i class="fas fa-times"></i>
            </button>
        </div>
    `;
    
    toastContainer.appendChild(toast);
    
    // Show animation
    setTimeout(() => toast.classList.add('show'), 100);
    
    // Auto remove
    setTimeout(() => {
        toast.classList.remove('show');
        setTimeout(() => toast.remove(), 300);
    }, duration);
}

// Utility function to get CSRF token from cookies
function getCookie(name) {
    const value = `; ${document.cookie}`;
    const parts = value.split(`; ${name}=`);
    if (parts.length === 2) return parts.pop().split(';').shift();
}

// Scroll to create section
function scrollToCreateSection() {
    const createSection = document.getElementById('createSection');
    if (createSection) {
        createSection.scrollIntoView({ 
            behavior: 'smooth',
            block: 'start'
        });
    }
}

// Variables pour la modale de confirmation
let pendingAction = null;
let pendingButton = null;
let pendingOriginalText = null;

// Custom confirmation modal
function showCustomConfirm(title, message, action, button, originalText, icon = 'question-circle', confirmText = 'Confirmer', isDanger = false) {
    const confirmTitle = document.getElementById('confirmTitle');
    const confirmMessage = document.getElementById('confirmMessage');
    const confirmIcon = document.querySelector('.custom-confirm-icon i');
    const confirmBtn = document.getElementById('confirmActionBtn');
    
    if (!confirmTitle || !confirmMessage || !confirmIcon || !confirmBtn) {
        console.error('Confirmation modal elements not found');
        return;
    }
    
    confirmTitle.textContent = title;
    confirmMessage.textContent = message;
    confirmIcon.className = `fas fa-${icon}`;
    
    confirmBtn.textContent = confirmText;
    confirmBtn.className = `custom-confirm-btn ${isDanger ? 'danger' : 'confirm'}`;
    confirmBtn.innerHTML = `<i class="fas fa-${isDanger ? 'exclamation-triangle' : 'check'}"></i>${confirmText}`;
    
    pendingAction = action;
    pendingButton = button;
    pendingOriginalText = originalText;
    
    const modal = document.getElementById('customConfirmModal');
    if (modal) {
        modal.classList.add('show');
        document.body.style.overflow = 'hidden';
    }
}

function closeCustomConfirm() {
    const modal = document.getElementById('customConfirmModal');
    if (modal) {
        modal.classList.remove('show');
        document.body.style.overflow = 'auto';
    }
    pendingAction = null;
    pendingButton = null;
    pendingOriginalText = null;
}

function executeConfirmedAction() {
    if (pendingAction) {
        pendingAction();
    }
    closeCustomConfirm();
}

// Créer un envoi pour une région
function creerEnvoiRegion(regionId, regionNom) {
    const button = event.target;
    const originalText = button.innerHTML;
    
    showCustomConfirm(
        'Créer un envoi',
        `Êtes-vous sûr de vouloir créer un envoi pour la région ${regionNom} ?`,
        () => {
            button.disabled = true;
            button.innerHTML = '<div class="loading-spinner mr-2"></div>Création...';

            const csrfToken = getCookie('csrftoken');
            
            fetch('/Superpreparation/envois/creer-region/', {
                method: 'POST',
                headers: {
                    'X-CSRFToken': csrfToken,
                },
                body: new URLSearchParams({
                    'region_id': regionId
                })
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    showToast('Envoi créé avec succès !', 'success');
                    setTimeout(() => window.location.reload(), 1500);
                } else {
                    showToast('Erreur lors de la création de l\'envoi: ' + data.error, 'error');
                    button.disabled = false;
                    button.innerHTML = originalText;
                }
            })
            .catch(error => {
                console.error('Erreur:', error);
                showToast('Erreur lors de la création de l\'envoi', 'error');
                button.disabled = false;
                button.innerHTML = originalText;
            });
        },
        button,
        originalText,
        'plus-circle',
        'Créer l\'envoi'
    );
}

// Clôturer un envoi
function cloturerEnvoi(envoiId, numeroEnvoi) {
    const button = event.target;
    const originalText = button.innerHTML;
    
    showCustomConfirm(
        'Clôturer l\'envoi',
        `Êtes-vous sûr de vouloir clôturer l'envoi ${numeroEnvoi} ? Cette action est irréversible.`,
        () => {
            button.disabled = true;
            button.innerHTML = '<div class="loading-spinner mr-2"></div>Clôture...';

            const csrfToken = getCookie('csrftoken');
            
            fetch('/Superpreparation/envois/cloturer/', {
                method: 'POST',
                headers: {
                    'X-CSRFToken': csrfToken,
                },
                body: new URLSearchParams({
                    'envoi_id': envoiId
                })
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    showToast('Envoi clôturé avec succès !', 'success');
                    setTimeout(() => window.location.reload(), 1500);
                } else {
                    showToast('Erreur lors de la clôture de l\'envoi: ' + data.error, 'error');
                    button.disabled = false;
                    button.innerHTML = originalText;
                }
            })
            .catch(error => {
                console.error('Erreur:', error);
                showToast('Erreur lors de la clôture de l\'envoi', 'error');
                button.disabled = false;
                button.innerHTML = originalText;
            });
        },
        button,
        originalText,
        'check-circle',
        'Clôturer l\'envoi',
        true
    );
}

// Exporter un envoi en Excel
function exporterEnvoiExcel(envoiId, numeroEnvoi) {
    const button = event.target;
    const originalText = button.innerHTML;
    button.disabled = true;
    button.innerHTML = '<div class="loading-spinner mr-2"></div>Génération...';

    showToast('Génération du fichier Excel en cours...', 'info');

    fetch(`/Superpreparation/envois/${envoiId}/export-excel/`)
        .then(response => {
            if (!response.ok) {
                throw new Error(`Erreur HTTP: ${response.status}`);
            }
            return response.blob();
        })
        .then(blob => {
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = `Envoi_${numeroEnvoi}_Commandes.xlsx`;
            document.body.appendChild(a);
            a.click();
            window.URL.revokeObjectURL(url);
            document.body.removeChild(a);

            showToast('Fichier Excel téléchargé avec succès !', 'success');
            button.disabled = false;
            button.innerHTML = originalText;
        })
        .catch(error => {
            console.error('Erreur lors de l\'export:', error);
            showToast('Erreur lors de la génération du fichier Excel', 'error');
            button.disabled = false;
            button.innerHTML = originalText;
        });
}

// Visualiser les commandes d'un envoi
function visualiserCommandesEnvoi(envoiId, numeroEnvoi, regionNom) {
    const button = event.target;
    const originalText = button.innerHTML;
    button.disabled = true;
    button.innerHTML = '<div class="loading-spinner mr-2"></div>Chargement...';

    showToast('Chargement des commandes...', 'info');

    // Récupérer le token CSRF
    const csrfToken = getCookie('csrftoken');
    
    fetch(`/Superpreparation/envois/${envoiId}/commandes/`, {
        method: 'GET',
        headers: {
            'X-CSRFToken': csrfToken,
            'X-Requested-With': 'XMLHttpRequest'
        }
    })
    .then(response => {
        if (!response.ok) {
            throw new Error(`Erreur HTTP: ${response.status}`);
        }
        return response.json();
    })
    .then(data => {
        console.log('Réponse reçue:', data);
        if (data.success) {
            console.log('Commandes reçues:', data.commandes);
            console.log('Nombre de commandes:', data.commandes ? data.commandes.length : 0);
            showCommandesModal(data.commandes, numeroEnvoi, regionNom);
            showToast('Commandes chargées avec succès !', 'success');
        } else {
            showToast('Erreur lors du chargement des commandes: ' + data.error, 'error');
        }
        button.disabled = false;
        button.innerHTML = originalText;
    })
    .catch(error => {
        console.error('Erreur lors du chargement des commandes:', error);
        showToast('Erreur lors du chargement des commandes', 'error');
        button.disabled = false;
        button.innerHTML = originalText;
    });
}

// Afficher le modal des commandes
function showCommandesModal(commandes, numeroEnvoi, regionNom) {
    console.log('showCommandesModal appelée avec:', { commandes, numeroEnvoi, regionNom });
    
    // Créer le modal s'il n'existe pas
    let modal = document.getElementById('commandesModal');
    if (!modal) {
        modal = createCommandesModal();
        document.body.appendChild(modal);
    }

    // Mettre à jour le contenu du modal
    const modalTitle = modal.querySelector('#commandesModalTitle');
    const modalContent = modal.querySelector('#commandesModalContent');
    
    if (modalTitle) {
        modalTitle.textContent = `Commandes de l'envoi ${numeroEnvoi}`;
    }
    
    if (modalContent) {
        const html = generateCommandesHTML(commandes, regionNom);
        console.log('HTML généré:', html);
        modalContent.innerHTML = html;
    }

    // Afficher le modal
    modal.classList.add('show');
    document.body.style.overflow = 'hidden';
}

// Créer le modal des commandes
function createCommandesModal() {
    const modal = document.createElement('div');
    modal.id = 'commandesModal';
    modal.className = 'commandes-modal';
    modal.innerHTML = `
        <div class="commandes-modal-content">
            <div class="commandes-modal-header">
                <div class="commandes-modal-icon">
                    <i class="fas fa-list-alt"></i>
                </div>
                <div class="commandes-modal-title" id="commandesModalTitle">Commandes de l'envoi</div>
                <button class="commandes-modal-close" onclick="closeCommandesModal()">
                    <i class="fas fa-times"></i>
                </button>
            </div>
            
            <div class="commandes-modal-body" id="commandesModalContent">
                <!-- Le contenu sera généré dynamiquement -->
            </div>
            
            <div class="commandes-modal-footer">
                <button class="commandes-modal-btn secondary" onclick="closeCommandesModal()">
                    <i class="fas fa-times"></i>
                    Fermer
                </button>
            </div>
        </div>
    `;
    
    // Event listener pour fermer en cliquant à l'extérieur
    modal.addEventListener('click', function(e) {
        if (e.target === this) {
            closeCommandesModal();
        }
    });
    
    return modal;
}

// Fermer le modal des commandes
function closeCommandesModal() {
    const modal = document.getElementById('commandesModal');
    if (modal) {
        modal.classList.remove('show');
        document.body.style.overflow = 'auto';
    }
}

// Générer le HTML pour la liste des commandes
function generateCommandesHTML(commandes, regionNom) {
    console.log('generateCommandesHTML appelée avec:', commandes);
    console.log('Type de commandes:', typeof commandes);
    console.log('Longueur de commandes:', commandes ? commandes.length : 'undefined');
    
    if (!commandes || commandes.length === 0) {
        console.log('Aucune commande trouvée, affichage du message vide');
        return `
            <div class="empty-commandes">
                <div class="empty-commandes-icon">
                    <i class="fas fa-box-open"></i>
                </div>
                <h3 class="text-lg font-medium text-gray-800 mb-2">Aucune commande trouvée</h3>
                <p class="text-gray-600">Il n'y a actuellement aucune commande dans cet envoi.</p>
            </div>
        `;
    }

    let html = `
        <div class="commandes-info">
            <div class="commandes-stats">
                <div class="stat-item">
                    <i class="fas fa-map-marker-alt text-blue-600"></i>
                    <span class="stat-label">Région:</span>
                    <span class="stat-value">${regionNom}</span>
                </div>
                <div class="stat-item">
                    <i class="fas fa-box text-green-600"></i>
                    <span class="stat-label">Total commandes:</span>
                    <span class="stat-value">${commandes.length}</span>
                </div>
                <div class="stat-item">
                    <i class="fas fa-money-bill-wave text-purple-600"></i>
                    <span class="stat-label">Valeur totale:</span>
                    <span class="stat-value">${calculateTotalValue(commandes)} DH</span>
                </div>
            </div>
        </div>
        
        <div class="commandes-list">
            <div class="commandes-table-header">
                <div class="header-cell">ID YZ</div>
                <div class="header-cell">Client</div>
                <div class="header-cell">Téléphone</div>
                <div class="header-cell">Ville</div>
                <div class="header-cell">Articles</div>
                <div class="header-cell">Prix</div>
                <div class="header-cell">État</div>
            </div>
            
            <div class="commandes-table-body">
    `;

    commandes.forEach(commande => {
        // Générer le HTML pour les articles/variantes
        let articlesHtml = '';
        if (commande.paniers && commande.paniers.length > 0) {
            commande.paniers.forEach(panier => {
                articlesHtml += `
                    <div class="article-item">
                        <div class="article-name">${panier.article?.nom || 'N/A'}</div>
                        ${panier.variante ? `
                            <div class="variante-info">
                                <span class="variante-ref">${panier.variante.reference_variante || 'N/A'}</span>
                                ${panier.variante.couleur ? `<span class="variante-color">${panier.variante.couleur}</span>` : ''}
                                ${panier.variante.pointure ? `<span class="variante-size">${panier.variante.pointure}</span>` : ''}
                            </div>
                        ` : ''}
                        <div class="article-qty">Qté: ${panier.quantite}</div>
                    </div>
                `;
            });
        } else {
            articlesHtml = '<span class="text-gray-500">Aucun article</span>';
        }

        html += `
            <div class="commande-row">
                <div class="commande-cell">
                    <span class="commande-id">${commande.id_yz || 'N/A'}</span>
                </div>
                <div class="commande-cell">
                    <div class="client-info">
                        <span class="client-name">${commande.client?.nom || 'N/A'} ${commande.client?.prenom || ''}</span>
                        <span class="client-email">${commande.client?.email || ''}</span>
                    </div>
                </div>
                <div class="commande-cell">
                    <span class="client-phone">${commande.client?.numero_tel || 'N/A'}</span>
                </div>
                <div class="commande-cell">
                    <span class="commande-ville">${commande.ville?.nom_ville || 'N/A'}</span>
                </div>
                <div class="commande-cell">
                    <div class="articles-list">
                        ${articlesHtml}
                    </div>
                </div>
                <div class="commande-cell">
                    <span class="commande-total">${commande.total_cmd || 0} DH</span>
                </div>
                <div class="commande-cell">
                    <span class="commande-status ${getStatusClass(commande.etat_actuel)}">
                        <i class="fas ${getStatusIcon(commande.etat_actuel)}"></i>
                        ${commande.etat_actuel?.enum_etat?.libelle || 'N/A'}
                    </span>
                </div>
            </div>
        `;
    });

    html += `
            </div>
        </div>
    `;

    return html;
}

// Calculer la valeur totale des commandes
function calculateTotalValue(commandes) {
    return commandes.reduce((total, commande) => {
        return total + (parseFloat(commande.total_cmd) || 0);
    }, 0).toFixed(2);
}

// Obtenir la classe CSS pour le statut
function getStatusClass(etatActuel) {
    if (!etatActuel) return 'status-unknown';
    
    const libelle = etatActuel.enum_etat?.libelle?.toLowerCase() || '';
    
    switch (libelle) {
        case 'confirmée':
            return 'status-confirmee';
        case 'préparée':
            return 'status-preparee';
        case 'à imprimer':
        case 'en préparation':
            return 'status-preparation';
        default:
            return 'status-unknown';
    }
}

// Obtenir l'icône pour le statut
function getStatusIcon(etatActuel) {
    if (!etatActuel) return 'fa-question-circle';
    
    const libelle = etatActuel.enum_etat?.libelle?.toLowerCase() || '';
    
    switch (libelle) {
        case 'confirmée':
            return 'fa-check-circle';
        case 'préparée':
            return 'fa-box';
        case 'à imprimer':
            return 'fa-print';
        case 'en préparation':
            return 'fa-cogs';
        default:
            return 'fa-question-circle';
    }
}

// Auto-refresh functionality
let autoRefreshInterval;

function startAutoRefresh() {
    autoRefreshInterval = setInterval(() => {
        // Only refresh if there are active shipments
        const activeShipments = document.querySelectorAll('.envoi-card.en-cours');
        if (activeShipments.length > 0) {
            showToast('Actualisation automatique des données...', 'info', 2000);
            setTimeout(() => window.location.reload(), 2000);
        }
    }, 300000); // Refresh every 5 minutes
}

function stopAutoRefresh() {
    if (autoRefreshInterval) {
        clearInterval(autoRefreshInterval);
    }
}

// Initialize the envois management system
function initEnvoisManagement() {
    console.log('🚀 Initialisation du système de gestion des envois...');
    
    // Start auto-refresh
    startAutoRefresh();
    
    // Show welcome message
    setTimeout(() => {
        showToast('Bienvenue dans la gestion des envois !', 'info', 3000);
    }, 1000);
    
    // Setup event listeners
    setupEventListeners();
    
    console.log('✅ Système de gestion des envois initialisé');
}

// Setup all event listeners
function setupEventListeners() {
    // Custom confirmation modal event listeners
    const customConfirmModal = document.getElementById('customConfirmModal');
    if (customConfirmModal) {
        // Fermer la modale en cliquant à l'extérieur
        customConfirmModal.addEventListener('click', function(e) {
            if (e.target === this) {
                closeCustomConfirm();
            }
        });
    }
    
    // Keyboard shortcuts
    document.addEventListener('keydown', function(e) {
        if (e.ctrlKey || e.metaKey) {
            switch(e.key) {
                case 'r':
                    e.preventDefault();
                    window.location.reload();
                    showToast('Page actualisée !', 'info');
                    break;
                case 'n':
                    e.preventDefault();
                    scrollToCreateSection();
                    showToast('Navigation vers la création d\'envois', 'info');
                    break;
            }
        } else if (e.key === 'Escape') {
            // Fermer la modale de confirmation si elle est ouverte
            const modal = document.getElementById('customConfirmModal');
            if (modal && modal.classList.contains('show')) {
                closeCustomConfirm();
            }
        }
    });
    
    // User activity monitoring for auto-refresh
    let userActivityTimeout;
    document.addEventListener('mousemove', function() {
        clearTimeout(userActivityTimeout);
        userActivityTimeout = setTimeout(stopAutoRefresh, 60000); // Stop after 1 minute of inactivity
    });
}

// Export functions for global access
window.showToast = showToast;
window.getCookie = getCookie;
window.scrollToCreateSection = scrollToCreateSection;
window.showCustomConfirm = showCustomConfirm;
window.closeCustomConfirm = closeCustomConfirm;
window.executeConfirmedAction = executeConfirmedAction;
window.creerEnvoiRegion = creerEnvoiRegion;
window.cloturerEnvoi = cloturerEnvoi;
window.exporterEnvoiExcel = exporterEnvoiExcel;
window.visualiserCommandesEnvoi = visualiserCommandesEnvoi;
window.showCommandesModal = showCommandesModal;
window.closeCommandesModal = closeCommandesModal;
window.startAutoRefresh = startAutoRefresh;
window.stopAutoRefresh = stopAutoRefresh;
window.initEnvoisManagement = initEnvoisManagement;

// Auto-initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    initEnvoisManagement();
});
