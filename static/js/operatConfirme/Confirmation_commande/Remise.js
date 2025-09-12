/**
 * Gestion des remises pour la confirmation de commande
 * Affiche une modale avec les diff�rents prix de remise disponibles pour un article
 */

let currentArticleRemise = null;
let currentPanierId = null;

/**
 * Ouvre la modale des prix de remise pour un article
 * @param {number} panierId - ID du panier
 */
function ouvrirModalRemise(panierId) {
    console.log('= DEBUG: ouvrirModalRemise appel�e pour panier:', panierId);
    
    currentPanierId = panierId ;
    
    // R�cup�rer les donn�es de l'article depuis le DOM
    const articleCard = document.querySelector(`[data-article-id="${panierId}"]`);
    if (!articleCard) {
        console.error('L Impossible de trouver l\'article avec l\'ID:', panierId);
        return;
    }
    
    try {
        const articleData = JSON.parse(articleCard.dataset.article);
        currentArticleRemise = articleData;
        
        console.log('=' DEBUG: Donn�es article r�cup�r�es:', articleData);
        
        // Remplir les informations de base de l'article
        remplirInformationsArticle(articleData);
        
        // Afficher les prix de remise disponibles
        afficherPrixRemises(articleData);
        
        // Afficher la modale
        const modal = document.getElementById('modalPrixRemise');
        if (modal) {
            modal.classList.remove('hidden');
            console.log(' Modale des prix de remise ouverte');
        } else {
            console.error('L Modale des prix de remise non trouv�e');
        }
        
    } catch (error) {
        console.error('L Erreur lors du parsing des donn�es article:', error);
        alert('Erreur lors du chargement des donn�es de l\'article');
    }
}

/**
 * Remplit les informations de base de l'article dans la modale
 * @param {Object} articleData - Donn�es de l'article
 */
function remplirInformationsArticle(articleData) {
    // Nom de l'article
    const nomElement = document.getElementById('articleNomRemise');
    if (nomElement) {
        nomElement.textContent = articleData.nom || 'Article sans nom';
    }
    
    // R�f�rence de l'article
    const refElement = document.getElementById('articleRefRemise');
    if (refElement) {
        refElement.textContent = articleData.reference || 'R�f. non disponible';
    }
    
    // Prix unitaire actuel
    const prixActuelElement = document.getElementById('prixUnitaireActuel');
    if (prixActuelElement) {
        const prixActuel = parseFloat(articleData.prix_actuel || articleData.prix_unitaire || 0);
        prixActuelElement.textContent = prixActuel.toFixed(2) + ' DH';
    }
    
    // Cat�gorie
    const categorieElement = document.getElementById('articleCategorieRemise');
    if (categorieElement) {
        categorieElement.textContent = articleData.categorie || 'Cat�gorie non d�finie';
    }
    
    // Variante (couleur et pointure)
    const varianteElement = document.getElementById('articleVarianteRemise');
    if (varianteElement) {
        const couleur = articleData.couleur || '';
        const pointure = articleData.pointure || '';
        let varianteText = 'Standard';
        
        if (couleur || pointure) {
            varianteText = [couleur, pointure].filter(Boolean).join(' / ');
        }
        varianteElement.textContent = varianteText;
    }
}

/**
 * Affiche les prix de remise disponibles dans la modale
 * @param {Object} articleData - Donn�es de l'article
 */
function afficherPrixRemises(articleData) {
    const container = document.getElementById('listePrixRemises');
    if (!container) {
        console.error('L Container des prix de remise non trouv�');
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
            couleur: 'bg-green-100 text-green-800 border-green-300'
        },
        { 
            label: 'Prix Remise 2', 
            prix: parseFloat(articleData.prix_remise_2 || 0), 
            key: 'prix_remise_2',
            badge: 'Remise 2',
            couleur: 'bg-blue-100 text-blue-800 border-blue-300'
        },
        { 
            label: 'Prix Remise 3', 
            prix: parseFloat(articleData.prix_remise_3 || 0), 
            key: 'prix_remise_3',
            badge: 'Remise 3',
            couleur: 'bg-purple-100 text-purple-800 border-purple-300'
        },
        { 
            label: 'Prix Remise 4', 
            prix: parseFloat(articleData.prix_remise_4 || 0), 
            key: 'prix_remise_4',
            badge: 'Remise 4',
            couleur: 'bg-red-100 text-red-800 border-red-300'
        }
    ];
    
    // Prix liquidation si disponible
    const prixLiquidation = parseFloat(articleData.Prix_liquidation || 0);
    if (prixLiquidation > 0) {
        prixRemises.push({
            label: 'Prix Liquidation',
            prix: prixLiquidation,
            key: 'Prix_liquidation',
            badge: 'Liquidation',
            couleur: 'bg-orange-100 text-orange-800 border-orange-300'
        });
    }
    
    let hasPrixRemise = false;
    
    // G�n�rer les cartes pour chaque prix de remise disponible
    prixRemises.forEach(remise => {
        if (remise.prix > 0) {
            hasPrixRemise = true;
            const economie = prixActuel - remise.prix;
            const pourcentageEconomie = prixActuel > 0 ? ((economie / prixActuel) * 100) : 0;
            
            const cardHTML = `
                <div class="prix-remise-card border-2 ${remise.couleur} rounded-lg p-4 cursor-pointer hover:shadow-md transition-all duration-200" 
                     onclick="selectionnerPrixRemise('${remise.key}', ${remise.prix})">
                    <div class="flex items-center justify-between mb-3">
                        <div class="flex items-center space-x-2">
                            <span class="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium ${remise.couleur}">
                                <i class="fas fa-tag mr-1"></i>${remise.badge}
                            </span>
                            <span class="text-sm font-medium text-gray-700">${remise.label}</span>
                        </div>
                        <div class="text-right">
                            <div class="text-lg font-bold text-gray-900">${remise.prix.toFixed(2)} DH</div>
                            ${economie > 0 ? `<div class="text-xs text-green-600">-${economie.toFixed(2)} DH (${pourcentageEconomie.toFixed(1)}%)</div>` : ''}
                        </div>
                    </div>
                    
                    <div class="flex items-center justify-between text-sm text-gray-600">
                        <span>Prix original: ${prixActuel.toFixed(2)} DH</span>
                        ${economie > 0 ? 
                            `<span class="text-green-600 font-medium">�conomie: ${economie.toFixed(2)} DH</span>` : 
                            `<span class="text-red-600 font-medium">Pas d'�conomie</span>`
                        }
                    </div>
                    
                    <div class="mt-3 flex justify-center">
                        <button type="button" 
                                class="px-4 py-2 ${remise.couleur.replace('100', '500').replace('800', 'white')} rounded-lg hover:${remise.couleur.replace('100', '600')} transition-colors text-sm font-medium">
                            <i class="fas fa-check mr-1"></i>Appliquer cette remise
                        </button>
                    </div>
                </div>
            `;
            container.insertAdjacentHTML('beforeend', cardHTML);
        }
    });
    
    // Si aucun prix de remise n'est disponible
    if (!hasPrixRemise) {
        container.innerHTML = `
            <div class="text-center py-8">
                <div class="flex flex-col items-center space-y-4">
                    <div class="w-16 h-16 bg-gray-100 rounded-full flex items-center justify-center">
                        <i class="fas fa-info-circle text-gray-400 text-2xl"></i>
                    </div>
                    <div class="text-gray-600">
                        <h4 class="text-lg font-medium mb-2">Aucun prix de remise configur�</h4>
                        <p class="text-sm">Cet article n'a pas de prix de remise d�finis dans le syst�me.</p>
                        <p class="text-sm mt-1">Contactez l'administrateur pour configurer des prix de remise.</p>
                    </div>
                </div>
            </div>
        `;
    }
}

/**
 * S�lectionne et applique un prix de remise
 * @param {string} typeRemise - Type de remise (ex: 'prix_remise_1')
 * @param {number} nouveauPrix - Nouveau prix � appliquer
 */
function selectionnerPrixRemise(typeRemise, nouveauPrix) {
    console.log('=' DEBUG: S�lection prix remise:', typeRemise, nouveauPrix);
    
    if (!currentPanierId || !currentArticleRemise) {
        console.error('L Donn�es manquantes pour appliquer la remise');
        return;
    }
    
    const prixOriginal = parseFloat(currentArticleRemise.prix_actuel || currentArticleRemise.prix_unitaire || 0);
    const economie = prixOriginal - nouveauPrix;
    
    // Confirmation de l'application de la remise
    const confirmMessage = `Voulez-vous appliquer cette remise ?\n\n` +
                          `Article: ${currentArticleRemise.nom}\n` +
                          `Prix original: ${prixOriginal.toFixed(2)} DH\n` +
                          `Nouveau prix: ${nouveauPrix.toFixed(2)} DH\n` +
                          `�conomie: ${economie.toFixed(2)} DH`;
    
    if (confirm(confirmMessage)) {
        appliquerPrixRemise(typeRemise, nouveauPrix, economie);
    }
}

/**
 * Applique effectivement le prix de remise � l'article
 * @param {string} typeRemise - Type de remise
 * @param {number} nouveauPrix - Nouveau prix
 * @param {number} economie - Montant de l'�conomie
 */
function appliquerPrixRemise(typeRemise, nouveauPrix, economie) {
    try {
        // Mettre � jour l'affichage du prix
        const prixElement = document.getElementById(`prix-unitaire-${currentPanierId}`);
        const labelElement = document.getElementById(`prix-libelle-${currentPanierId}`);
        
        if (prixElement) {
            prixElement.textContent = nouveauPrix.toFixed(2) + ' DH';
            prixElement.className = 'font-medium text-purple-600';
        }
        
        if (labelElement) {
            const labelTexte = typeRemise.replace('prix_remise_', 'Remise ').replace('Prix_liquidation', 'Liquidation');
            labelElement.textContent = `${labelTexte} (-${economie.toFixed(2)} DH)`;
            labelElement.className = 'text-xs text-purple-600 mt-1';
        }
        
        // Ajouter un indicateur visuel de remise
        const articleCard = document.querySelector(`[data-article-id="${currentPanierId}"]`);
        if (articleCard) {
            let remiseIndicator = articleCard.querySelector('.remise-indicator');
            if (!remiseIndicator) {
                remiseIndicator = document.createElement('div');
                remiseIndicator.className = 'remise-indicator absolute -top-2 -right-2 bg-purple-500 text-white text-xs px-2 py-1 rounded-full shadow-md z-10';
                remiseIndicator.innerHTML = '<i class="fas fa-percent"></i>';
                articleCard.style.position = 'relative';
                articleCard.appendChild(remiseIndicator);
            }
            
            // Mettre � jour le texte de l'indicateur
            const remiseNum = typeRemise.replace('prix_remise_', '').replace('Prix_liquidation', 'L');
            remiseIndicator.innerHTML = `<i class="fas fa-percent mr-1"></i>R${remiseNum}`;
        }
        
        // Recalculer le sous-total
        const quantiteInput = document.getElementById(`quantite-${currentPanierId}`);
        if (quantiteInput) {
            const quantite = parseInt(quantiteInput.value) || 1;
            const nouveauSousTotal = nouveauPrix * quantite;
            const sousTotalElement = document.getElementById(`sous-total-${currentPanierId}`);
            if (sousTotalElement) {
                sousTotalElement.textContent = nouveauSousTotal.toFixed(2) + ' DH';
            }
        }
        
        // Fermer la modale
        fermerModalPrixRemise();
        
        // Recalculer le total de la commande si la fonction existe
        if (typeof recalculerTotalCommande === 'function') {
            recalculerTotalCommande();
        }
        
        // Notification de succ�s
        alert(`Prix de remise appliqu� avec succ�s !\n�conomie: ${economie.toFixed(2)} DH`);
        
        console.log(' Prix de remise appliqu� avec succ�s');
        
    } catch (error) {
        console.error('L Erreur lors de l\'application du prix de remise:', error);
        alert('Erreur lors de l\'application de la remise');
    }
}

/**
 * Ferme la modale des prix de remise
 */
function fermerModalPrixRemise() {
    const modal = document.getElementById('modalPrixRemise');
    if (modal) {
        modal.classList.add('hidden');
    }
    
    // R�initialiser les variables
    currentArticleRemise = null;
    currentPanierId = null;
    
    console.log(' Modale des prix de remise ferm�e');
}

// Gestion des �v�nements globaux
document.addEventListener('DOMContentLoaded', function() {
    console.log('=' Script Remise.js charg�');
    
    // Gestion du clic en dehors de la modale
    document.addEventListener('click', function(event) {
        const modal = document.getElementById('modalPrixRemise');
        if (modal && event.target === modal) {
            fermerModalPrixRemise();
        }
    });
    
    // Gestion de la touche �chap
    document.addEventListener('keydown', function(event) {
        if (event.key === 'Escape') {
            const modal = document.getElementById('modalPrixRemise');
            if (modal && !modal.classList.contains('hidden')) {
                fermerModalPrixRemise();
            }
        }
    });
});

// Export des fonctions pour utilisation globale
window.ouvrirModalRemise = ouvrirModalRemise;
window.fermerModalPrixRemise = fermerModalPrixRemise;
window.selectionnerPrixRemise = selectionnerPrixRemise;