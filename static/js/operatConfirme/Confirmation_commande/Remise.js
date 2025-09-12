/**
 * Module de gestion des remises pour la confirmation de commande
 * 
 * Fonctionnalités:
 * - Ouverture de modale pour sélectionner un prix de remise
 * - Affichage des prix disponibles (Remise 1-4, Liquidation)
 * - Application de la remise avec sauvegarde en base de données
 * - Mise à jour de l'interface utilisateur
 */

// Variables globales pour le contexte actuel
let currentPanierId = null;
let currentArticleRemise = null;

/**
 * Ouvre la modale de remise pour un article du panier
 * @param {number} panierId - ID du panier
 */
function ouvrirModalRemise(panierId) {
    console.log('🔄 Ouverture de la modale de remise pour panier ID:', panierId);
    
    currentPanierId = panierId;
    
    // Récupérer les données de l'article
    const articleCard = document.querySelector(`[data-article-id="${panierId}"]`);
    if (!articleCard) {
        console.error('❌ Article non trouvé pour l\'ID:', panierId);
        return;
    }
    
    // Parser les données de l'article avec gestion d'erreur
    let articleData;
    try {
        const articleDataStr = articleCard.getAttribute('data-article');
        console.log('📄 Données brutes de l\'article:', articleDataStr);
        
        // Le JSON semble déjà bien formaté avec des points pour les décimaux
        // Seulement nettoyer les espaces superflus si nécessaire
        const cleanDataStr = articleDataStr.trim();
            
        articleData = JSON.parse(cleanDataStr);
        console.log('✅ Données article parsées:', articleData);
        
    } catch (error) {
        console.error('❌ Erreur lors du traitement des données article:', error);
        console.error('❌ Données JSON brutes:', articleCard.getAttribute('data-article'));
        
        alert('Erreur lors du traitement des données de l\'article. Veuillez rafraîchir la page et réessayer.');
        return;
    }
    
    currentArticleRemise = articleData;
    afficherModalRemise(articleData);
}

/**
 * Affiche la modale avec les informations de l'article
 * @param {Object} articleData - Données de l'article
 */
function afficherModalRemise(articleData) {
    const modal = document.getElementById('modalPrixRemise');
    if (!modal) {
        console.error('❌ Modale de remise non trouvée');
        return;
    }
    
    // Remplir les informations de l'article dans la modale
    remplirInfosArticleModal(articleData);
    
    // Afficher les prix de remise disponibles
    afficherPrixRemises(articleData);
    
    // Afficher la modale
    modal.classList.remove('hidden');
    modal.style.display = 'flex';
    
    console.log('✅ Modale de remise affichée');
}

/**
 * Remplit les informations de l'article dans la modale
 * @param {Object} articleData - Données de l'article
 */
function remplirInfosArticleModal(articleData) {
    // Nom de l'article
    const nomElement = document.getElementById('modalArticleNom');
    if (nomElement) {
        nomElement.textContent = articleData.nom || 'Article sans nom';
    }
    
    // Référence
    const refElement = document.getElementById('modalArticleReference');
    if (refElement) {
        refElement.textContent = articleData.reference || 'N/A';
    }
    
    // Prix actuel
    const prixElement = document.getElementById('modalArticlePrixActuel');
    if (prixElement) {
        const prix = parseFloat(articleData.prix_actuel || articleData.prix_unitaire || 0);
        prixElement.textContent = prix.toFixed(2) + ' DH';
    }
    
    // Informations sur les variantes si disponibles
    const varianteElement = document.getElementById('modalArticleVariante');
    if (varianteElement) {
        let varianteText = '';
        if (articleData.pointure) varianteText += `Taille: ${articleData.pointure} `;
        if (articleData.couleur) varianteText += `Couleur: ${articleData.couleur}`;
        varianteElement.textContent = varianteText || 'Aucune variante';
    }
}

/**
 * Affiche les prix de remise disponibles dans la modale
 * @param {Object} articleData - Données de l'article
 */
function afficherPrixRemises(articleData) {
    const container = document.getElementById('listePrixRemises');
    if (!container) {
        console.error('❌ Container des prix de remise non trouvé');
        return;
    }
    
    // Vider le container
    container.innerHTML = '';
    
    const prixUnitaire = parseFloat(articleData.prix_unitaire || 0);
    const prixActuel = parseFloat(articleData.prix_actuel || articleData.prix_unitaire || 0);
    
    // Array des prix de remise avec leurs labels
    const prixRemises = [
        { 
            label: 'Prix Remise 1', 
            prix: parseFloat(articleData.prix_remise_1 || 0), 
            key: 'prix_remise_1',
            badge: 'Remise 1',
            couleur: 'bg-green-100 text-green-800 border-green-300',
            requiresValue: true // Nécessite une valeur configurée
        },
        { 
            label: 'Prix Remise 2', 
            prix: parseFloat(articleData.prix_remise_2 || 0), 
            key: 'prix_remise_2',
            badge: 'Remise 2',
            couleur: 'bg-blue-100 text-blue-800 border-blue-300',
            requiresValue: true
        },
        { 
            label: 'Prix Remise 3', 
            prix: parseFloat(articleData.prix_remise_3 || 0), 
            key: 'prix_remise_3',
            badge: 'Remise 3',
            couleur: 'bg-purple-100 text-purple-800 border-purple-300',
            requiresValue: true
        },
        { 
            label: 'Prix Remise 4', 
            prix: parseFloat(articleData.prix_remise_4 || 0), 
            key: 'prix_remise_4',
            badge: 'Remise 4',
            couleur: 'bg-orange-100 text-orange-800 border-orange-300',
            requiresValue: true
        },
        { 
            label: 'Prix Liquidation', 
            prix: parseFloat(articleData.Prix_liquidation || prixActuel), // Utiliser le prix actuel si non configuré
            key: 'liquidation', // Changer la clé pour être cohérent
            badge: 'Liquidation',
            couleur: 'bg-red-100 text-red-800 border-red-300',
            requiresValue: false, // Toujours afficher l'option liquidation
            description: articleData.Prix_liquidation && articleData.Prix_liquidation > 0 ? 
                'Prix configuré' : 'Cliquer pour personnaliser',
            isPersonalizable: articleData.Prix_liquidation ? false : true // Permettre personnalisation si pas configuré
        }
    ];
    
    // Filtrer les prix valides selon leurs critères
    const prixValides = prixRemises.filter(item => {
        if (item.requiresValue) {
            return item.prix > 0; // Les remises doivent avoir une valeur configurée
        } else {
            return true; // Toujours inclure les options spéciales comme liquidation
        }
    });
    
    if (prixValides.length === 0) {
        container.innerHTML = `
            <div class="text-center py-8">
                <div class="text-gray-400 mb-4">
                    <i class="fas fa-exclamation-triangle text-4xl"></i>
                </div>
                <div>
                    <p class="text-sm">Cet article n'a pas de prix de remise définis dans le système.</p>
                    <p class="text-sm mt-1">Contactez l'administrateur pour configurer des prix de remise.</p>
                </div>
            </div>
        `;
        return;
    }
    
    // Créer les boutons pour chaque prix valide
    prixValides.forEach(item => {
        const economie = prixActuel - item.prix;
        const pourcentageEconomie = ((economie / prixActuel) * 100).toFixed(1);
        
        const buttonHtml = `
            <div class="border-2 rounded-lg p-4 hover:shadow-md transition-all cursor-pointer ${item.couleur}"
                 onclick="selectionnerPrixRemise('${item.key}', ${item.prix}, ${item.isPersonalizable || false})"
                <div class="flex justify-between items-center">
                    <div class="flex-1">
                        <div class="flex items-center space-x-2 mb-2">
                            <span class="px-2 py-1 bg-white rounded-full text-xs font-semibold ${item.couleur.replace('bg-', 'text-').replace('-100', '-700')}">
                                ${item.badge}
                            </span>
                            ${item.description ? `<span class="text-xs text-gray-500">(${item.description})</span>` : ''}
                        </div>
                        <div class="text-lg font-bold">${item.prix.toFixed(2)} DH</div>
                        <div class="text-sm">
                            ${economie >= 0 ? 
                                `Économie: ${economie.toFixed(2)} DH (${pourcentageEconomie}%)` : 
                                `Augmentation: ${Math.abs(economie).toFixed(2)} DH`
                            }
                        </div>
                    </div>
                    <div class="text-right">
                        <i class="fas fa-arrow-right text-lg"></i>
                    </div>
                </div>
            </div>
        `;
        
        container.innerHTML += buttonHtml;
    });
}

/**
 * Sélectionne et applique un prix de remise
 * @param {string} typeRemise - Type de remise (ex: 'prix_remise_1')
 * @param {number} nouveauPrix - Nouveau prix à appliquer
 * @param {boolean} isPersonalizable - Si le prix peut être personnalisé
 */
function selectionnerPrixRemise(typeRemise, nouveauPrix, isPersonalizable = false) {
    console.log('🔄 Sélection prix remise:', typeRemise, nouveauPrix, 'personnalisable:', isPersonalizable);
    
    if (!currentPanierId || !currentArticleRemise) {
        console.error('❌ Données manquantes pour appliquer la remise');
        return;
    }
    
    // Si personnalisable, demander à l'utilisateur de saisir le prix
    if (isPersonalizable) {
        const prixSaisi = prompt(`Saisissez le prix de liquidation personnalisé pour "${currentArticleRemise.nom}":\n\nPrix actuel: ${nouveauPrix.toFixed(2)} DH`, nouveauPrix.toFixed(2));
        
        if (prixSaisi === null) {
            return; // Annulé par l'utilisateur
        }
        
        const prixPersonnalise = parseFloat(prixSaisi);
        if (isNaN(prixPersonnalise) || prixPersonnalise <= 0) {
            alert('Prix invalide. Veuillez saisir un nombre positif.');
            return;
        }
        
        nouveauPrix = prixPersonnalise;
        console.log('💡 Prix personnalisé saisi:', nouveauPrix);
    }
    
    const prixOriginal = parseFloat(currentArticleRemise.prix_actuel || currentArticleRemise.prix_unitaire || 0);
    const economie = prixOriginal - nouveauPrix;
    
    // Confirmation de l'application de la remise
    const confirmMessage = `Voulez-vous appliquer cette remise sur le prix actuel ?\n\n` +
                          `Article: ${currentArticleRemise.nom}\n` +
                          `Prix actuel: ${prixOriginal.toFixed(2)} DH\n` +
                          `➜ Nouveau prix unitaire: ${nouveauPrix.toFixed(2)} DH\n` +
                          `💰 ${economie >= 0 ? 'Économie' : 'Augmentation'} par unité: ${Math.abs(economie).toFixed(2)} DH\n\n` +
                          `Le prix actuel sera remplacé par le prix remisé.` +
                          (isPersonalizable ? '\n\n🔧 Prix personnalisé appliqué.' : '');
    
    if (confirm(confirmMessage)) {
        appliquerPrixRemise(typeRemise, nouveauPrix, economie);
    }
}

/**
 * Applique effectivement le prix de remise à l'article
 * @param {string} typeRemise - Type de remise
 * @param {number} nouveauPrix - Nouveau prix
 * @param {number} economie - Montant de l'économie
 */
function appliquerPrixRemise(typeRemise, nouveauPrix, economie) {
    console.log('🔄 Envoi requête AJAX:', {
        url: window.location.href,
        action: 'apply_remise',
        panier_id: currentPanierId,
        type_remise: typeRemise,
        nouveau_prix: nouveauPrix
    });
    
    // Vérifier le token CSRF
    const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]');
    if (!csrfToken) {
        console.error('❌ Token CSRF non trouvé');
        alert('Erreur: Token CSRF non trouvé. Veuillez rafraîchir la page.');
        return;
    }
    
    console.log('🔐 Token CSRF trouvé:', csrfToken.value.substring(0, 10) + '...');
    
    // Envoyer la requête AJAX pour sauvegarder en base de données
    fetch(window.location.href, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/x-www-form-urlencoded',
            'X-Requested-With': 'XMLHttpRequest',
            'X-CSRFToken': csrfToken.value
        },
        body: new URLSearchParams({
            'action': 'apply_remise',
            'panier_id': currentPanierId,
            'type_remise': typeRemise,
            'nouveau_prix': nouveauPrix
        })

    })
    .then(response => {
        console.log('📡 Réponse reçue:', response.status, response.statusText);
        console.log('📄 Content-Type:', response.headers.get('content-type'));
        
        // Vérifier si la réponse est bien du JSON
        const contentType = response.headers.get('content-type');
        if (!contentType || !contentType.includes('application/json')) {
            // Si ce n'est pas du JSON, lire comme texte pour voir l'erreur
            return response.text().then(text => {
                console.error('❌ Réponse HTML reçue au lieu de JSON:', text.substring(0, 500));
                throw new Error('Le serveur a retourné du HTML au lieu de JSON. Vérifiez les logs Django.');
            });
        }
        
        return response.json();
    })
    .then(data => {
        if (!data.success) {
            throw new Error(data.error || 'Erreur lors de l\'application de la remise');
        }
        console.log('✅ Remise sauvegardée en base:', data);
        
        // Utiliser les données du serveur pour les valeurs exactes
        const nouveauPrixServer = data.nouveau_prix;
        const economieServer = data.economie;
        
        // Continuer avec la logique d'affichage
        updateUIAfterRemise(typeRemise, nouveauPrixServer, economieServer, data);
    })
    .catch(error => {
        console.error('❌ Erreur AJAX remise:', error);
        console.error('❌ Type d\'erreur:', typeof error);
        console.error('❌ Message d\'erreur:', error.message);
        console.error('❌ Stack trace:', error.stack);
        
        let errorMessage = 'Erreur inconnue';
        if (error && error.message) {
            errorMessage = error.message;
        } else if (typeof error === 'string') {
            errorMessage = error;
        } else {
            errorMessage = 'Erreur lors de la communication avec le serveur';
        }
        
        alert('Erreur lors de la sauvegarde de la remise:\n' + errorMessage);
    });
}

/**
 * Met à jour l'affichage spécifique du panier avec remise appliquée
 * @param {number} panierId - ID du panier
 * @param {Object} serverData - Données retournées par le serveur
 */
function updatePanierDisplay(panierId, serverData) {
    try {
        // Mettre à jour le prix unitaire affiché
        const prixUnitaireElement = document.querySelector(`[data-article-id="${panierId}"] .prix-unitaire`);
        if (prixUnitaireElement) {
            prixUnitaireElement.textContent = `${serverData.nouveau_prix.toFixed(2)} DH`;
        }
        
        // Mettre à jour le sous-total
        const sousTotalElement = document.getElementById(`sous-total-${panierId}`);
        if (sousTotalElement) {
            sousTotalElement.textContent = `${serverData.nouveau_sous_total.toFixed(2)} DH`;
        }
        
        // Ajouter un badge "remise appliquée"
        const articleCard = document.querySelector(`[data-article-id="${panierId}"]`);
        if (articleCard) {
            // Supprimer l'ancien badge s'il existe
            const existingBadge = articleCard.querySelector('.badge-remise');
            if (existingBadge) {
                existingBadge.remove();
            }
            
            // Ajouter le nouveau badge
            const badge = document.createElement('span');
            badge.className = 'badge-remise inline-flex items-center px-2 py-1 bg-purple-100 text-purple-700 rounded-full text-xs font-semibold';
            badge.innerHTML = '<i class="fas fa-percent mr-1"></i>Remise appliquée';
            
            const titleElement = articleCard.querySelector('.article-title');
            if (titleElement) {
                titleElement.appendChild(badge);
            }
        }
        
        // Mettre à jour le total de la commande
        if (serverData.nouveau_total_commande) {
            const totalElement = document.getElementById('total-commande');
            if (totalElement) {
                totalElement.textContent = `${serverData.nouveau_total_commande.toFixed(2)} DH`;
            }
        }
        
        console.log('✅ Affichage du panier mis à jour sans rechargement');
        
    } catch (error) {
        console.error('❌ Erreur lors de la mise à jour de l\'affichage:', error);
        // En cas d'erreur, faire un rechargement
        setTimeout(() => {
            window.location.reload(true);
        }, 1000);
    }
}

/**
 * Met à jour l'interface après application de la remise
 */
function updateUIAfterRemise(typeRemise, nouveauPrix, economie, serverData) {
    try {
        // Fermer la modale
        fermerModalRemise();
        
        // Afficher une notification de succès
        const notification = document.createElement('div');
        notification.className = 'fixed top-4 right-4 bg-green-500 text-white px-4 py-2 rounded-lg shadow-lg z-50';
        notification.innerHTML = `
            <div class="flex items-center">
                <i class="fas fa-percent mr-2"></i>
                <span>Prix remisé appliqué avec succès!</span>
            </div>
        `;
        document.body.appendChild(notification);
        
        // Supprimer la notification après 3 secondes
        setTimeout(() => {
            if (notification.parentNode) {
                notification.parentNode.removeChild(notification);
            }
        }, 3000);
        
        // Marquer le panier comme ayant une remise appliquée
        marquerPanierAvecRemise(currentPanierId);
        
        // Mettre à jour l'affichage du panier spécifique sans recharger toute la page
        updatePanierDisplay(currentPanierId, serverData);
        
        // Optionnel: Recharger la page après un délai si nécessaire
        // setTimeout(() => {
        //     window.location.reload(true);
        // }, 1500);
        
    } catch (error) {
        console.error('❌ Erreur lors de l\'application du prix de remise:', error);
        alert('Erreur lors de l\'application de la remise');
    }
}

/**
 * Marque un panier comme ayant une remise appliquée (pour éviter les recalculs JS)
 * @param {number} panierId - ID du panier
 */
function marquerPanierAvecRemise(panierId) {
    const articleCard = document.querySelector(`[data-article-id="${panierId}"]`);
    if (articleCard) {
        articleCard.setAttribute('data-remise-appliquee', 'true');
        console.log(`✅ Panier ${panierId} marqué comme ayant une remise appliquée`);
    }
}

/**
 * Vérifie si un panier a une remise appliquée
 * @param {number} panierId - ID du panier
 * @returns {boolean} - True si une remise est appliquée
 */
function panierARemiseAppliquee(panierId) {
    const articleCard = document.querySelector(`[data-article-id="${panierId}"]`);
    return articleCard && articleCard.getAttribute('data-remise-appliquee') === 'true';
}

/**
 * Ferme la modale des prix de remise
 */
function fermerModalRemise() {
    const modal = document.getElementById('modalPrixRemise');
    if (modal) {
        modal.classList.add('hidden');
        modal.style.display = 'none';
        
        // Réinitialiser les variables globales
        currentPanierId = null;
        currentArticleRemise = null;
        
        console.log('✅ Modale de remise fermée');
    }
}

/**
 * Gestionnaire d'événement pour fermer la modale en cliquant à l'extérieur
 */
document.addEventListener('DOMContentLoaded', function() {
    const modal = document.getElementById('modalPrixRemise');
    if (modal) {
        modal.addEventListener('click', function(e) {
            if (e.target === modal) {
                fermerModalRemise();
            }
        });
    }
});

// Export des fonctions pour utilisation globale
window.ouvrirModalRemise = ouvrirModalRemise;
window.fermerModalRemise = fermerModalRemise;
window.selectionnerPrixRemise = selectionnerPrixRemise;
window.marquerPanierAvecRemise = marquerPanierAvecRemise;
window.panierARemiseAppliquee = panierARemiseAppliquee;