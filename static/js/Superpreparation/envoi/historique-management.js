// Toast notification system
function showToast(message, type = 'info', duration = 4000) {
    const toastContainer = document.getElementById('toastContainer');
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

function getCookie(name) {
    const value = `; ${document.cookie}`;
    const parts = value.split(`; ${name}=`);
    if (parts.length === 2) return parts.pop().split(';').shift();
}

// Fonction pour exporter les commandes d'un envoi clôturé en Excel
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

// Fonction pour visualiser les commandes d'un envoi
function visualiserCommandesEnvoi(envoiId, numeroEnvoi) {
    console.log('visualiserCommandesEnvoi appelée avec:', { envoiId, numeroEnvoi });
    
    showToast('Chargement des commandes...', 'info');
    
    fetch(`/Superpreparation/envois/${envoiId}/commandes-historique/`)
        .then(response => {
            console.log('Réponse reçue:', response);
            if (!response.ok) {
                throw new Error(`Erreur HTTP: ${response.status}`);
            }
            return response.json();
        })
        .then(data => {
            console.log('Commandes reçues:', data.commandes);
            showCommandesModal(data, numeroEnvoi);
        })
        .catch(error => {
            console.error('Erreur lors du chargement des commandes:', error);
            showToast('Erreur lors du chargement des commandes', 'error');
        });
}

// Fonction pour afficher la modal des commandes
function showCommandesModal(data, numeroEnvoi) {
    console.log('showCommandesModal appelée avec:', data);
    
    const modal = document.getElementById('commandesModal');
    const modalTitle = document.getElementById('modalTitle');
    const modalBody = document.getElementById('commandesModalBody');
    
    // Afficher les informations de l'envoi dans le titre
    let titleText = `Commandes de l'envoi ${numeroEnvoi}`;

    
    modalTitle.textContent = titleText;
    modalBody.innerHTML = generateCommandesHTML(data.commandes, data.envoi);
    
    modal.classList.add('show');
    document.body.style.overflow = 'hidden';
}

// Fonction pour fermer la modal des commandes
function closeCommandesModal() {
    const modal = document.getElementById('commandesModal');
    modal.classList.remove('show');
    document.body.style.overflow = 'auto';
}

// Fonction pour générer le HTML des commandes
function generateCommandesHTML(commandes, envoiInfo = null) {
    console.log('generateCommandesHTML appelée avec:', commandes);
    console.log('Type de commandes:', typeof commandes);
    console.log('Longueur de commandes:', commandes.length);
    
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
    
    // Calculer les statistiques
    const totalCommandes = commandes.length;
    const totalValeur = calculateTotalValue(commandes);
    
    // Compter les états
    const etatsCount = {};
    commandes.forEach(commande => {
        const etat = commande.etat_actuel?.libelle || 'Inconnu';
        etatsCount[etat] = (etatsCount[etat] || 0) + 1;
    });
    
    let statsHTML = `
        <div class="commandes-stats">
            <div class="commande-stat">
                <div class="commande-stat-value">${totalCommandes}</div>
                <div class="commande-stat-label">Total commandes</div>
            </div>
            <div class="commande-stat">
                <div class="commande-stat-value">${totalValeur.toFixed(2)} DHS</div>
                <div class="commande-stat-label">Valeur totale</div>
            </div>
    `;
    
    // Ajouter les informations de l'envoi si disponibles
    if (envoiInfo) {
        statsHTML += `
            <div class="commande-stat">
                <div class="commande-stat-value">${envoiInfo.region || 'N/A'}</div>
                <div class="commande-stat-label">Région</div>
            </div>
        `;
        if (envoiInfo.date_creation) {
            statsHTML += `
                <div class="commande-stat">
                    <div class="commande-stat-value">${envoiInfo.date_creation}</div>
                    <div class="commande-stat-label">Date création</div>
                </div>
            `;
        }
        if (envoiInfo.date_cloture) {
            statsHTML += `
                <div class="commande-stat">
                    <div class="commande-stat-value">${envoiInfo.date_cloture}</div>
                    <div class="commande-stat-label">Date clôture</div>
                </div>
            `;
        }
    }
    

    
    statsHTML += '</div>';
    
    // Générer le tableau des commandes
    let tableHTML = `
        <div class="commandes-table">
            <div class="commandes-table-header">
                <div>N° Commande</div>
                <div>Client</div>
                <div>Téléphone</div>
                <div>Ville</div>
                <div>Prix</div>
                <div>Articles</div>
            </div>
    `;
    
    commandes.forEach(commande => {
        const statusClass = getStatusClass(commande.etat_actuel?.libelle);
        const statusIcon = getStatusIcon(commande.etat_actuel?.libelle);
        
        let articlesHTML = '';
        if (commande.paniers_data && commande.paniers_data.length > 0) {
            articlesHTML = '<div class="articles-list">';
            commande.paniers_data.forEach(panier => {
                articlesHTML += `
                    <div class="article-item">
                        <div class="article-name">${panier.article.nom}</div>
                        <div class="variante-info">
                            ${panier.variante ? `<span class="variante-ref">${panier.variante.reference_variante}</span>` : ''}
                            ${panier.variante?.couleur ? `<span class="variante-color">${panier.variante.couleur}</span>` : ''}
                            ${panier.variante?.pointure ? `<span class="variante-size">${panier.variante.pointure}</span>` : ''}
                            <span class="article-qty">${panier.quantite}</span>
                        </div>
                    </div>
                `;
            });
            articlesHTML += '</div>';
        }
        
        tableHTML += `
            <div class="commande-row">
                <div>${commande.num_cmd}</div>
                <div>${commande.client?.nom || 'N/A'}</div>
                <div>${commande.client?.numero_tel || 'N/A'}</div>
                <div>${commande.ville?.nom_ville || 'N/A'}</div>
                <div>${(commande.total_cmd || 0).toFixed(2)} Dhs</div>
                <div>${articlesHTML}</div>
            </div>
        `;
    });
    
    tableHTML += '</div>';
    
    console.log('HTML généré:', statsHTML + tableHTML);
    return statsHTML + tableHTML;
}

// Fonction pour calculer la valeur totale
function calculateTotalValue(commandes) {
    return commandes.reduce((total, commande) => {
        return total + (commande.total_cmd || 0);
    }, 0);
}

// Fonction pour obtenir la classe CSS de l'état
function getStatusClass(etat) {
    if (!etat) return 'autre';
    
    const etatLower = etat.toLowerCase();
    if (etatLower.includes('préparée') || etatLower.includes('preparee')) return 'preparee';
    if (etatLower.includes('confirmée') || etatLower.includes('confirmee')) return 'confirmee';
    if (etatLower.includes('livrée') || etatLower.includes('livree')) return 'livree';
    if (etatLower.includes('retournée') || etatLower.includes('retournee')) return 'retournee';
    return 'autre';
}

// Fonction pour obtenir l'icône de l'état
function getStatusIcon(etat) {
    if (!etat) return 'fas fa-question-circle';
    
    const etatLower = etat.toLowerCase();
    if (etatLower.includes('préparée') || etatLower.includes('preparee')) return 'fas fa-box';
    if (etatLower.includes('confirmée') || etatLower.includes('confirmee')) return 'fas fa-check-circle';
    if (etatLower.includes('livrée') || etatLower.includes('livree')) return 'fas fa-truck';
    if (etatLower.includes('retournée') || etatLower.includes('retournee')) return 'fas fa-undo';
    return 'fas fa-question-circle';
}

// Quick actions functions
function refreshPage() {
    showToast('Actualisation de la page...', 'info');
    setTimeout(() => window.location.reload(), 1000);
}

function scrollToTop() {
    window.scrollTo({
        top: 0,
        behavior: 'smooth'
    });
    showToast('Retour en haut de page', 'info');
}

// Fonction showKeyboardShortcuts supprimée (plus de toast ni d'affichage)

function resetFilters() {
    window.location.href = "/Superpreparation/envois/historique/";
}

// Auto-refresh functionality
let autoRefreshInterval;

function startAutoRefresh() {
    autoRefreshInterval = setInterval(() => {
        showToast('Actualisation automatique des données...', 'info', 2000);
        setTimeout(() => window.location.reload(), 2000);
    }, 600000); // Refresh every 10 minutes
}

function stopAutoRefresh() {
    if (autoRefreshInterval) {
        clearInterval(autoRefreshInterval);
    }
}

// Variables pour les filtres
let selectedPeriode = '';
let selectedRegion = '';

// Fonctions pour les modales de filtres
function openFilterModal(type) {
    const modal = document.getElementById(type + 'Modal');
    modal.classList.add('show');
    document.body.style.overflow = 'hidden';
}

function closeFilterModal(type) {
    const modal = document.getElementById(type + 'Modal');
    modal.classList.remove('show');
    document.body.style.overflow = 'auto';
}

function selectFilterOption(element, type) {
    // Retirer la sélection de tous les autres options
    const options = element.parentElement.querySelectorAll('.filter-option');
    options.forEach(option => option.classList.remove('selected'));
    
    // Ajouter la sélection à l'option cliquée
    element.classList.add('selected');
    
    // Stocker la valeur sélectionnée
    if (type === 'periode') {
        selectedPeriode = element.dataset.value;
    } else if (type === 'region') {
        selectedRegion = element.dataset.value;
    }
}

function applyFilter(type) {
    // Construire l'URL avec les paramètres
    let url = "/Superpreparation/envois/historique/?";
    let params = [];
    
    if (selectedPeriode) {
        params.push('periode=' + selectedPeriode);
    }
    if (selectedRegion) {
        params.push('region=' + selectedRegion);
    }
    
    url += params.join('&');
    
    // Fermer la modale
    closeFilterModal(type);
    
    // Rediriger vers la nouvelle URL
    showToast('Application des filtres...', 'info');
    setTimeout(() => {
        window.location.href = url;
    }, 500);
}

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    // Initialize filter values from URL parameters
    const urlParams = new URLSearchParams(window.location.search);
    selectedPeriode = urlParams.get('periode') || '';
    selectedRegion = urlParams.get('region') || '';
    
    startAutoRefresh();
    
    // Welcome toast supprimé

    // Show filter status
    const hasFilters = selectedPeriode || selectedRegion;
    if (hasFilters) {
        setTimeout(() => {
            showToast('Filtres actifs détectés', 'warning', 3000);
        }, 2000);
    }
    
    // Fermer les modales en cliquant à l'extérieur
    document.querySelectorAll('.filter-modal').forEach(modal => {
        modal.addEventListener('click', function(e) {
            if (e.target === this) {
                this.classList.remove('show');
                document.body.style.overflow = 'auto';
            }
        });
    });
    
    // Fermer la modal des commandes en cliquant à l'extérieur
    const commandesModal = document.getElementById('commandesModal');
    if (commandesModal) {
        commandesModal.addEventListener('click', function(e) {
            if (e.target === this) {
                closeCommandesModal();
            }
        });
    }
    
    // Show scroll to top button when scrolling down
    window.addEventListener('scroll', function() {
        const scrollToTopBtn = document.querySelector('.quick-action-btn:nth-child(2)');
        if (scrollToTopBtn) {
            if (window.scrollY > 300) {
                scrollToTopBtn.style.opacity = '1';
                scrollToTopBtn.style.transform = 'scale(1)';
            } else {
                scrollToTopBtn.style.opacity = '0.7';
                scrollToTopBtn.style.transform = 'scale(0.9)';
            }
        }
    });
});

// Stop auto-refresh when user is inactive
let userActivityTimeout;
document.addEventListener('mousemove', function() {
    clearTimeout(userActivityTimeout);
    userActivityTimeout = setTimeout(stopAutoRefresh, 60000); // Stop after 1 minute of inactivity
});

// Keyboard shortcuts
document.addEventListener('keydown', function(e) {
    if (e.ctrlKey || e.metaKey) {
        switch(e.key) {
            case 'r':
                e.preventDefault();
                refreshPage();
                break;
            case 'f':
                e.preventDefault();
                const periodeSelect = document.querySelector('select[name="periode"]');
                if (periodeSelect) {
                    periodeSelect.focus();
                }
                break;
            case 'n':
                e.preventDefault();
                window.location.href = "/Superpreparation/envois/";
                showToast('Navigation vers les envois actifs', 'info');
                break;
        }
    } else if (e.key === 'Escape') {
        // Close any open modals or tooltips
        const tooltips = document.querySelectorAll('.tooltip:hover');
        tooltips.forEach(tooltip => tooltip.blur());
        
        // Close filter modals
        document.querySelectorAll('.filter-modal.show').forEach(modal => {
            modal.classList.remove('show');
            document.body.style.overflow = 'auto';
        });
        
        // Close commandes modal
        closeCommandesModal();
    }
});
