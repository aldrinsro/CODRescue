/**
 * Module de gestion des remises pour la confirmation de commande
 * 
 * Fonctionnalités:
 * - Ouverture de modale pour sélectionner un prix de remise
 * - Affichage des prix disponibles (Remise 1-4)
 * - Application de la remise avec sauvegarde en base de données
 * - Mise à jour de l'interface utilisateur
 */

// Protection contre les chargements multiples
if (window.remiseModuleLoaded) {
    console.log('🔄 Remise.js déjà chargé, évitement du doublon');
} else {
    window.remiseModuleLoaded = true;

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

    // PROTECTION PRIORITAIRE: Vérifier si le bouton de remise est activé
    const btnRemise = document.getElementById(`btn-remise-${panierId}`);
    if (btnRemise && btnRemise.disabled) {
        console.warn('⚠️ Tentative d\'ouverture de modale sur un panier avec remise non activée');
        alert('Vous devez d\'abord activer la remise avec le bouton vert "Activer remise" avant de pouvoir appliquer une remise.');
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

        // Vérifier si l'article est en phase LIQUIDATION ou en promotion
        if (articleData.phase === 'LIQUIDATION') {
            console.warn('⚠️ Tentative d\'ouverture de modale remise sur un article en liquidation');
            alert('Les articles en liquidation ne peuvent pas avoir de remise appliquée.');
            return;
        }

        if (articleData.has_promo_active) {
            console.warn('⚠️ Tentative d\'ouverture de modale remise sur un article en promotion');
            alert('Les articles en promotion ne peuvent pas avoir de remise appliquée.');
            return;
        }

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
        }
    ];
    
    // Filtrer les prix valides selon leurs critères
    const prixValides = prixRemises.filter(item => {
        if (item.requiresValue) {
            return item.prix > 0; // Les remises doivent avoir une valeur configurée
        } else {
            return true; // Inclure les options sans validation de valeur
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
        const prixSaisi = prompt(`Saisissez le prix de remise personnalisé pour "${currentArticleRemise.nom}":\n\nPrix actuel: ${nouveauPrix.toFixed(2)} DH`, nouveauPrix.toFixed(2));
        
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
                          (isPersonalizable ? '\n\n🔧 Prix de remise personnalisé appliqué.' : '');
    
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
 * Recharge la section des articles pour mettre à jour l'affichage
 */
function rechargerSectionArticles() {
    console.log('🔄 Rechargement de la section articles...');
    
    // Récupérer l'ID de la commande depuis l'URL ou une variable globale
    const currentUrl = window.location.pathname;
    const commandeIdMatch = currentUrl.match(/\/commandes\/(\d+)\//);
    
    if (!commandeIdMatch) {
        console.error('❌ Impossible de trouver l\'ID de la commande dans l\'URL');
        return;
    }
    
    const commandeId = commandeIdMatch[1];
    const url = `/operateur-confirme/api/commande/${commandeId}/rafraichir-articles/`;
    
    console.log('🌐 URL de rechargement:', url);
    
    fetch(url, {
        method: 'GET',
        headers: {
            'X-Requested-With': 'XMLHttpRequest',
        }
    })
    .then(response => {
        if (!response.ok) {
            throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        }
        return response.json();
    })
    .then(data => {
        if (!data.success) {
            throw new Error(data.error || 'Erreur lors du rechargement');
        }
        
        console.log('✅ Section articles rechargée avec succès');
        
        // Trouver le conteneur des articles et le remplacer
        const articlesContainer = document.getElementById('articles-container');
        if (articlesContainer) {
            articlesContainer.innerHTML = data.html;
            
            // Mettre à jour le compteur d'articles
            const articlesCountElement = document.getElementById('articles-count');
            if (articlesCountElement) {
                articlesCountElement.textContent = data.articles_count;
            }
            
            // Mettre à jour le total de la commande 
            const totalCommandeElements = document.querySelectorAll('[id*="total_commande"], [id*="total-commande"]');
            totalCommandeElements.forEach(element => {
                element.textContent = `${data.total_commande.toFixed(2)} DH`;
            });
            
            console.log('✅ Affichage mis à jour avec les nouvelles données');
        } else {
            console.error('❌ Conteneur des articles non trouvé');
            // Fallback : recharger la page
            window.location.reload();
        }
    })
    .catch(error => {
        console.error('❌ Erreur lors du rechargement de la section:', error);
        // En cas d'erreur, recharger la page entière
        console.log('🔄 Fallback: rechargement de la page entière');
        window.location.reload();
    });
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
        
        // Recharger la section des articles au lieu de mettre à jour manuellement
        setTimeout(() => {
            rechargerSectionArticles();
        }, 500); // Petit délai pour que la notification soit visible
        
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

/**
 * Fonction pour activer la remise d'un panier
 * @param {number} panierId - ID du panier
 */
function activerRemise(panierId) {
    console.log('🔄 Activation de la remise pour panier ID:', panierId);
    
    // Vérifier si l'article est en phase LIQUIDATION
    const articleCard = document.querySelector(`[data-article-id="${panierId}"]`);
    if (!articleCard) {
        console.error('❌ Article non trouvé pour l\'ID:', panierId);
        alert('Erreur: Article non trouvé.');
        return;
    }
    
    try {
        const articleData = JSON.parse(articleCard.getAttribute('data-article'));
        if (articleData.phase === 'LIQUIDATION') {
            console.warn('⚠️ Tentative d\'activation de remise sur un article en liquidation');
            alert('Les articles en liquidation ne peuvent pas avoir de remise appliquée.');
            return;
        }
        
        if (articleData.has_promo_active) {
            console.warn('⚠️ Tentative d\'activation de remise sur un article en promotion');
            alert('Les articles en promotion ne peuvent pas avoir de remise appliquée.');
            return;
        }
    } catch (error) {
        console.error('❌ Erreur lors de la lecture des données article:', error);
    }
    
    // Vérifier le token CSRF
    const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]');
    if (!csrfToken) {
        console.error('❌ Token CSRF non trouvé');
        alert('Erreur: Token CSRF non trouvé. Veuillez rafraîchir la page.');
        return;
    }
    
    // Confirmation avant activation
    if (!confirm('Voulez-vous activer la remise pour cet article ?')) {
        return;
    }
    
    // Désactiver le bouton pendant la requête
    const button = document.getElementById(`btn-activer-remise-${panierId}`);
    if (button) {
        button.disabled = true;
        button.innerHTML = '<i class="fas fa-spinner fa-spin mr-1"></i>Activation...';
    }
    
    // Construire l'URL et l'afficher - Correction du préfixe URL
    const currentUrl = window.location.href;
    const baseUrl = window.location.origin;
    const url = `${baseUrl}/operateur-confirme/api/panier/${panierId}/activer-remise/`;
    
    console.log('🌐 URL de la requête:', url);
    console.log('🔑 Token CSRF:', csrfToken.value.substring(0, 10) + '...');
    console.log('🔍 Current URL:', currentUrl);
    console.log('🔍 Base URL:', baseUrl);
    
    // Test simple : vérifier si l'URL existe avant de faire la requête
    console.log('🧪 Test: Vérification de l\'existence de l\'URL...');
    
    // Envoyer la requête AJAX
    fetch(url, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/x-www-form-urlencoded',
            'X-Requested-With': 'XMLHttpRequest',
            'X-CSRFToken': csrfToken.value
        }
    })
    .then(response => {
        console.log('📡 Réponse reçue:', response.status, response.statusText);
        console.log('📡 Headers:', response.headers);
        console.log('📡 Response OK:', response.ok);
        
        if (!response.ok) {
            throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        }
        
        // Vérifier le type de contenu
        const contentType = response.headers.get('content-type');
        console.log('📡 Content-Type:', contentType);
        
        if (!contentType || !contentType.includes('application/json')) {
            return response.text().then(text => {
                console.error('❌ Réponse non-JSON reçue:', text.substring(0, 500));
                throw new Error('Le serveur a retourné du HTML au lieu de JSON');
            });
        }
        
        return response.json();
    })
    .then(data => {
        if (!data.success) {
            throw new Error(data.message || 'Erreur lors de l\'activation de la remise');
        }
        
        console.log('✅ Remise activée avec succès:', data);
        
        // Masquer le bouton d'activation
        if (button) {
            button.style.display = 'none';
        }
        
        // Activer le bouton de remise
        const btnRemise = document.getElementById(`btn-remise-${panierId}`);
        if (btnRemise) {
            btnRemise.disabled = false;
            btnRemise.classList.remove('opacity-50', 'cursor-not-allowed');
        }
        
        // Afficher le badge "remise appliquée"
        const articleTitle = document.querySelector(`[data-article-id="${panierId}"] .article-title`);
        if (articleTitle) {
            const existingBadge = articleTitle.querySelector('.badge-remise');
            if (!existingBadge) {
                const badge = document.createElement('span');
                badge.className = 'badge-remise inline-flex items-center px-2 py-0.5 bg-purple-100 text-purple-700 rounded-full text-xs font-medium ml-2';
                badge.innerHTML = '<i class="fas fa-percent mr-1"></i>Remise appliquée';
                articleTitle.appendChild(badge);
            }
        }
        
        // Mettre à jour l'affichage des prix si les données sont disponibles
        if (data.prix_unitaire && data.nouveau_sous_total) {
            // Mettre à jour le prix unitaire
            const prixUnitaireElement = document.getElementById(`prix-unitaire-${panierId}`);
            if (prixUnitaireElement) {
                prixUnitaireElement.textContent = `${data.prix_unitaire.toFixed(2)} DH`;
                prixUnitaireElement.className = 'font-medium text-purple-600';
            }
            
            // Mettre à jour le libellé du prix
            const prixLibelleElement = document.getElementById(`prix-libelle-${panierId}`);
            if (prixLibelleElement) {
                prixLibelleElement.innerHTML = '<i class="fas fa-percent mr-1"></i>Prix remise 1 appliquée';
                prixLibelleElement.className = 'text-xs text-purple-600 mt-1';
            }
            
            // Mettre à jour le sous-total
            const sousTotalElement = document.getElementById(`sous-total-${panierId}`);
            if (sousTotalElement) {
                sousTotalElement.textContent = `${data.nouveau_sous_total.toFixed(2)} DH`;
            }
        }
        
        // Notification de succès
        const notification = document.createElement('div');
        notification.className = 'fixed top-4 right-4 bg-green-500 text-white px-4 py-2 rounded-lg shadow-lg z-50';
        notification.innerHTML = `
            <div class="flex items-center">
                <i class="fas fa-check mr-2"></i>
                <span>Remise activée avec succès!</span>
            </div>
        `;
        document.body.appendChild(notification);
        
        setTimeout(() => {
            if (notification.parentNode) {
                notification.parentNode.removeChild(notification);
            }
        }, 3000);
        
    })
    .catch(error => {
        console.error('❌ Erreur lors de l\'activation de la remise:', error);
        
        // Réactiver le bouton en cas d'erreur
        if (button) {
            button.disabled = false;
            button.innerHTML = '<i class="fas fa-check mr-1"></i>Activer remise';
        }
        
        alert('Erreur lors de l\'activation de la remise:\n' + error.message);
    });
}

/**
 * Fonction pour désactiver la remise d'un panier
 * @param {number} panierId - ID du panier
 */
function desactiverRemise(panierId) {
    console.log('🔄 Désactivation de la remise pour panier ID:', panierId);
    
    // Vérifier le token CSRF
    const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]');
    if (!csrfToken) {
        console.error('❌ Token CSRF non trouvé');
        alert('Erreur: Token CSRF non trouvé. Veuillez rafraîchir la page.');
        return;
    }
    
    // Confirmation avant désactivation
    if (!confirm('Voulez-vous désactiver la remise pour cet article ?\n\nCela remettra le bouton "Remise" à l\'état désactivé.')) {
        return;
    }
    
    // Désactiver le bouton pendant la requête
    const button = document.getElementById(`btn-desactiver-remise-${panierId}`);
    if (button) {
        button.disabled = true;
        button.innerHTML = '<i class="fas fa-spinner fa-spin mr-1"></i>Désactivation...';
    }
    
    // Envoyer la requête AJAX
    fetch(`/operateur-confirme/api/panier/${panierId}/desactiver-remise/`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/x-www-form-urlencoded',
            'X-Requested-With': 'XMLHttpRequest',
            'X-CSRFToken': csrfToken.value
        }
    })
    .then(response => {
        console.log('📡 Réponse reçue:', response.status, response.statusText);
        return response.json();
    })
    .then(data => {
        if (!data.success) {
            throw new Error(data.message || 'Erreur lors de la désactivation de la remise');
        }
        
        console.log('✅ Remise désactivée avec succès:', data);
        
        // Masquer le bouton de désactivation
        if (button) {
            button.style.display = 'none';
        }
        
        // Afficher le bouton d'activation
        const articleTitle = document.querySelector(`[data-article-id="${panierId}"] .article-title`);
        if (articleTitle) {
            const existingActivateBtn = articleTitle.querySelector(`#btn-activer-remise-${panierId}`);
            if (!existingActivateBtn) {
                const activateBtn = document.createElement('button');
                activateBtn.type = 'button';
                activateBtn.id = `btn-activer-remise-${panierId}`;
                activateBtn.className = 'inline-flex items-center px-2 py-0.5 bg-green-100 text-green-700 rounded-full text-xs font-medium ml-2 hover:bg-green-200 transition-colors';
                activateBtn.title = 'Activer la remise';
                activateBtn.onclick = () => activerRemise(panierId);
                activateBtn.innerHTML = '<i class="fas fa-check mr-1"></i>Activer remise';
                
                // Insérer après le badge variante s'il existe, sinon après le nom
                const varianteBadge = articleTitle.querySelector('span[class*="bg-blue-100"]');
                if (varianteBadge) {
                    varianteBadge.parentNode.insertBefore(activateBtn, varianteBadge.nextSibling);
                } else {
                    articleTitle.appendChild(activateBtn);
                }
            }
        }
        
        // Désactiver le bouton de remise
        const btnRemise = document.getElementById(`btn-remise-${panierId}`);
        if (btnRemise) {
            btnRemise.disabled = true;
            btnRemise.classList.add('opacity-50', 'cursor-not-allowed');
        }
        
        // Supprimer le badge "remise appliquée"
        const badge = document.querySelector(`[data-article-id="${panierId}"] .badge-remise`);
        if (badge) {
            badge.remove();
        }
        
        // Mettre à jour l'affichage des prix si les données sont disponibles
        if (data.prix_unitaire && data.nouveau_sous_total) {
            // Restaurer le prix unitaire normal
            const prixUnitaireElement = document.getElementById(`prix-unitaire-${panierId}`);
            if (prixUnitaireElement) {
                prixUnitaireElement.textContent = `${data.prix_unitaire.toFixed(2)} DH`;
                prixUnitaireElement.className = 'font-medium text-gray-600';
            }
            
            // Restaurer le libellé du prix normal
            const prixLibelleElement = document.getElementById(`prix-libelle-${panierId}`);
            if (prixLibelleElement) {
                prixLibelleElement.innerHTML = '<i class="fas fa-tag mr-1"></i>Prix normal';
                prixLibelleElement.className = 'text-xs text-gray-600 mt-1';
            }
            
            // Mettre à jour le sous-total
            const sousTotalElement = document.getElementById(`sous-total-${panierId}`);
            if (sousTotalElement) {
                sousTotalElement.textContent = `${data.nouveau_sous_total.toFixed(2)} DH`;
            }
        }
        
        // Notification de succès
        const notification = document.createElement('div');
        notification.className = 'fixed top-4 right-4 bg-orange-500 text-white px-4 py-2 rounded-lg shadow-lg z-50';
        notification.innerHTML = `
            <div class="flex items-center">
                <i class="fas fa-times mr-2"></i>
                <span>Remise désactivée avec succès!</span>
            </div>
        `;
        document.body.appendChild(notification);
        
        setTimeout(() => {
            if (notification.parentNode) {
                notification.parentNode.removeChild(notification);
            }
        }, 3000);
        
    })
    .catch(error => {
        console.error('❌ Erreur lors de la désactivation de la remise:', error);
        
        // Réactiver le bouton en cas d'erreur
        if (button) {
            button.disabled = false;
            button.innerHTML = '<i class="fas fa-times mr-1"></i>Désactiver remise';
        }
        
        alert('Erreur lors de la désactivation de la remise:\n' + error.message);
    });
}

// Export des fonctions pour utilisation globale (avec debug)
window.ouvrirModalRemise = ouvrirModalRemise;
window.fermerModalRemise = fermerModalRemise;
window.selectionnerPrixRemise = selectionnerPrixRemise;
window.marquerPanierAvecRemise = marquerPanierAvecRemise;
window.panierARemiseAppliquee = panierARemiseAppliquee;
window.activerRemise = activerRemise;
window.desactiverRemise = desactiverRemise;

// Debug pour vérifier que les fonctions sont bien exportées
console.log('✅ Remise.js chargé avec succès');
console.log('🔧 Fonctions exportées:', {
    activerRemise: typeof window.activerRemise,
    desactiverRemise: typeof window.desactiverRemise,
    ouvrirModalRemise: typeof window.ouvrirModalRemise
});

// Assurer que les fonctions sont disponibles même en cas de problème d'ordre
if (typeof window.activerRemise === 'undefined') {
    console.error('❌ activerRemise non définie - problème d\'ordre de chargement');
}

} // Fin de la protection contre les chargements multiples