let commandeActuelle = null;

// Fonction de notification toast moderne
function showNotification(type, message, duration = 5000) {
    const container = document.getElementById('notificationContainer');
    
    // Créer la notification
    const notification = document.createElement('div');
    notification.className = `notification notification-${type} transform transition-all duration-300 ease-in-out translate-x-full opacity-0`;
    
    // Icônes selon le type
    const icons = {
        success: 'fas fa-check-circle',
        error: 'fas fa-exclamation-circle',
        warning: 'fas fa-exclamation-triangle',
        info: 'fas fa-info-circle'
    };
    
    // Couleurs selon le type
    const colors = {
        success: 'bg-green-500 border-green-600',
        error: 'bg-red-500 border-red-600',
        warning: 'bg-yellow-500 border-yellow-600',
        info: 'bg-blue-500 border-blue-600'
    };
    
    // Contenu de la notification
    notification.innerHTML = `
        <div class="flex items-center p-4 rounded-lg shadow-lg border-l-4 ${colors[type]} text-white min-w-80 max-w-md">
            <div class="flex-shrink-0">
                <i class="${icons[type]} text-xl"></i>
            </div>
            <div class="ml-3 flex-1">
                <p class="text-sm font-medium">${message}</p>
            </div>
            <div class="ml-3 flex-shrink-0">
                <button onclick="this.parentElement.parentElement.remove()" class="text-white hover:text-gray-200 transition-colors">
                    <i class="fas fa-times"></i>
                </button>
            </div>
        </div>
    `;
    
    // Ajouter à la page
    container.appendChild(notification);
    
    // Animation d'entrée
    setTimeout(() => {
        notification.classList.remove('translate-x-full', 'opacity-0');
    }, 100);
    
    // Suppression automatique
    setTimeout(() => {
        if (notification.parentElement) {
            notification.classList.add('translate-x-full', 'opacity-0');
            setTimeout(() => {
                if (notification.parentElement) {
                    notification.remove();
                }
            }, 300);
        }
    }, duration);
    
    // Suppression manuelle au clic
    notification.addEventListener('click', (e) => {
        if (e.target.closest('button')) return;
        notification.classList.add('translate-x-full', 'opacity-0');
        setTimeout(() => {
            if (notification.parentElement) {
                notification.remove();
            }
        }, 300);
    });
}

function ouvrirModalTraitement(commandeId, idYz, numCmd) {
    commandeActuelle = commandeId;
    
    // Mettre à jour l'ID de la commande dans la modale
    const commandeDisplay = numCmd || `YZ-${idYz}`;
    document.getElementById('modalCommandeId').textContent = commandeDisplay;
    
    // Réinitialiser le formulaire
    document.getElementById('commentaireTraitement').value = '';
    document.getElementById('stockBon').checked = true;
    
    // Afficher la modale
    document.getElementById('modalTraitement').classList.remove('hidden');
}

function fermerModalTraitement() {
    document.getElementById('modalTraitement').classList.add('hidden');
    commandeActuelle = null;
}

function confirmerTraitement() {
    if (!commandeActuelle) {
        showNotification('error', 'Erreur: Aucune commande sélectionnée');
        return;
    }
    
    const commentaire = document.getElementById('commentaireTraitement').value.trim();
    if (!commentaire) {
        showNotification('warning', 'Veuillez saisir un commentaire de traitement');
        return;
    }
    
    // Récupérer les valeurs
    const etatStock = document.querySelector('input[name="etat_stock"]:checked').value;
    const commandeId = document.getElementById('modalCommandeId').textContent;
    
    // Remplir la modale de confirmation
    document.getElementById('confirmationCommandeId').textContent = commandeId;
    document.getElementById('confirmationEtatStock').textContent = getEtatStockLabel(etatStock);
    document.getElementById('confirmationCommentaire').textContent = commentaire;
    
    // Masquer la modale de traitement et afficher la modale de confirmation
    document.getElementById('modalTraitement').classList.add('hidden');
    document.getElementById('modalConfirmation').classList.remove('hidden');
}

function fermerModalConfirmation() {
    document.getElementById('modalConfirmation').classList.add('hidden');
    // Remontrer la modale de traitement
    document.getElementById('modalTraitement').classList.remove('hidden');
}

function executerTraitement() {
    // Récupérer les valeurs depuis la modale de traitement
    const commentaire = document.getElementById('commentaireTraitement').value.trim();
    const etatStock = document.querySelector('input[name="etat_stock"]:checked').value;
    const typeTraitement = 'repreparer';
    
    // Fermer la modale de confirmation
    fermerModalConfirmation();
    
    // Appeler l'API pour traiter la commande
    traiterCommandeRetournee(typeTraitement, etatStock, commentaire);
}

function getEtatStockLabel(etat) {
    switch(etat) {
        case 'bon':
            return 'Produits en bon état (stock réincrémenté)';
        case 'defectueux':
            return 'Produits défectueux (stock non réincrémenté)';
        default:
            return etat;
    }
}

function traiterCommandeRetournee(typeTraitement, etatStock, commentaire) {
    const url = `/Superpreparation/api/traiter-commande-retournee/${commandeActuelle}/`;
    
    // Récupérer le token CSRF depuis le template
    const csrfToken = document.querySelector('meta[name="csrf-token"]').getAttribute('content');
    
    fetch(url, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': csrfToken,
        },
        body: JSON.stringify({
            type_traitement: typeTraitement,
            etat_stock: etatStock,
            commentaire: commentaire
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            // Construire le message de succès avec les détails
            let messageSuccess = data.message;
            if (data.etat_actuel) {
                messageSuccess += `\nÉtat actuel: ${data.etat_actuel}`;
            }
            if (data.date_confirmation) {
                messageSuccess += `\nDate de confirmation: ${data.date_confirmation}`;
            }
            
            showNotification('success', messageSuccess, 5000);
            fermerModalTraitement();
            // Recharger la page pour mettre à jour la liste
            setTimeout(() => {
                location.reload();
            }, 2000);
        } else {
            showNotification('error', `Erreur lors du traitement: ${data.message}`, 6000);
        }
    })
    .catch(error => {
        console.error('Erreur:', error);
        showNotification('error', 'Erreur de réseau lors du traitement. Veuillez réessayer.', 6000);
    });
}

// Initialisation des événements au chargement du DOM
document.addEventListener('DOMContentLoaded', function() {
    // Fermer la modale en cliquant à l'extérieur
    const modalTraitement = document.getElementById('modalTraitement');
    if (modalTraitement) {
        modalTraitement.addEventListener('click', function(e) {
            if (e.target === this) {
                fermerModalTraitement();
            }
        });
    }

    // Fermer la modale de confirmation en cliquant à l'extérieur
    const modalConfirmation = document.getElementById('modalConfirmation');
    if (modalConfirmation) {
        modalConfirmation.addEventListener('click', function(e) {
            if (e.target === this) {
                fermerModalConfirmation();
            }
        });
    }

    // Fermer la modale avec la touche Escape
    document.addEventListener('keydown', function(e) {
        if (e.key === 'Escape') {
            fermerModalTraitement();
            fermerModalConfirmation();
        }
    });
});