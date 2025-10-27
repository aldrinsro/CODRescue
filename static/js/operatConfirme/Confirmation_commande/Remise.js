/**
 * Gestion des remises sur les paniers
 * Permet d'appliquer, retirer et pr�visualiser des remises personnalis�es
 */

/**
 * Ouvre le modal de remise pour un panier sp�cifique
 * @param {number} panierId - ID du panier
 */
function ouvrirModalRemise(panierId) {
    const modal = document.getElementById('remiseModal');
    const panierIdInput = document.getElementById('remisePanierId');
    const typeRemiseSelect = document.getElementById('typeRemise');
    const valeurRemiseInput = document.getElementById('valeurRemise');
    const raisonRemiseInput = document.getElementById('raisonRemise');
    const previewContainer = document.getElementById('remisePreview');

    // R�initialiser le formulaire
    panierIdInput.value = panierId;
    typeRemiseSelect.value = 'POURCENTAGE';
    valeurRemiseInput.value = '';
    raisonRemiseInput.value = '';
    previewContainer.style.display = 'none';

    // Trouver les informations du panier
    const panierCard = document.querySelector(`[data-article-id="${panierId}"]`);
    if (panierCard) {
        const articleData = JSON.parse(panierCard.getAttribute('data-article'));
        const articleNom = articleData.nom || 'Article inconnu';
        document.getElementById('remiseArticleNom').textContent = articleNom;

        // R�cup�rer le sous-total actuel
        const sousTotalElement = document.getElementById(`sous-total-${panierId}`);
        if (sousTotalElement) {
            const sousTotalText = sousTotalElement.textContent.replace(/[^\d.,]/g, '').replace(',', '.');
            document.getElementById('remiseSousTotalActuel').textContent = parseFloat(sousTotalText).toFixed(2);
        }
    }

    // Afficher le modal
    modal.style.display = 'flex';
}

/**
 * Ferme le modal de remise
 */
function fermerModalRemise() {
    const modal = document.getElementById('remiseModal');
    modal.style.display = 'none';
}

/**
 * Calcule et affiche un aper�u de la remise en temps r�el
 */
function calculerApercu() {
    const panierId = document.getElementById('remisePanierId').value;
    const typeRemise = document.getElementById('typeRemise').value;
    const valeurRemise = document.getElementById('valeurRemise').value;
    const previewContainer = document.getElementById('remisePreview');

    // V�rifier que la valeur est saisie
    if (!valeurRemise || parseFloat(valeurRemise) <= 0) {
        previewContainer.style.display = 'none';
        return;
    }

    // Construire l'URL avec les param�tres
    const url = `/operateur-confirme/calculer-remise-preview/${panierId}/?type_remise=${typeRemise}&valeur_remise=${valeurRemise}`;

    // Afficher un indicateur de chargement
    previewContainer.innerHTML = '<div class="text-center"><i class="fas fa-spinner fa-spin"></i> Calcul en cours...</div>';
    previewContainer.style.display = 'block';

    // Appeler l'API de preview
    fetch(url, {
        method: 'GET',
        headers: {
            'X-Requested-With': 'XMLHttpRequest',
        }
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            // Afficher l'aper�u d�taill�
            previewContainer.innerHTML = `
                <div class="bg-blue-50 border border-blue-200 rounded-lg p-4 space-y-2">
                    <h4 class="font-semibold text-blue-800 flex items-center">
                        <i class="fas fa-calculator mr-2"></i>Aper�u de la remise
                    </h4>
                    <div class="grid grid-cols-2 gap-2 text-sm">
                        <div class="text-gray-600">Sous-total actuel:</div>
                        <div class="font-medium text-right">${data.data.sous_total_actuel.toFixed(2)} DH</div>

                        <div class="text-red-600 font-medium">Montant remise:</div>
                        <div class="font-bold text-red-600 text-right">- ${data.data.montant_remise_calcule.toFixed(2)} DH</div>

                        <div class="text-gray-600">Pourcentage:</div>
                        <div class="font-medium text-right">${data.data.pourcentage_reduction.toFixed(2)} %</div>

                        <div class="text-green-600 font-bold text-lg pt-2 border-t border-blue-200">Nouveau sous-total:</div>
                        <div class="font-bold text-green-600 text-lg text-right pt-2 border-t border-blue-200">${data.data.sous_total_apres_remise.toFixed(2)} DH</div>
                    </div>
                </div>
            `;
            previewContainer.style.display = 'block';
        } else {
            previewContainer.innerHTML = `
                <div class="bg-red-50 border border-red-200 rounded-lg p-3 text-red-700 text-sm">
                    <i class="fas fa-exclamation-triangle mr-2"></i>${data.error}
                </div>
            `;
            previewContainer.style.display = 'block';
        }
    })
    .catch(error => {
        console.error('Erreur lors du calcul de l\'aper�u:', error);
        previewContainer.innerHTML = `
            <div class="bg-red-50 border border-red-200 rounded-lg p-3 text-red-700 text-sm">
                <i class="fas fa-exclamation-triangle mr-2"></i>Erreur de connexion
            </div>
        `;
        previewContainer.style.display = 'block';
    });
}

/**
 * Applique la remise sur le panier
 */
function appliquerRemise() {
    const panierId = document.getElementById('remisePanierId').value;
    const typeRemise = document.getElementById('typeRemise').value;
    const valeurRemise = document.getElementById('valeurRemise').value;
    const raisonRemise = document.getElementById('raisonRemise').value;
    const btnAppliquer = document.querySelector('#remiseModal button[onclick="appliquerRemise()"]');

    // Validation
    if (!valeurRemise || parseFloat(valeurRemise) <= 0) {
        showNotification('Veuillez saisir une valeur de remise valide', 'error');
        return;
    }

    // D�sactiver le bouton pendant le traitement
    btnAppliquer.disabled = true;
    btnAppliquer.innerHTML = '<i class="fas fa-spinner fa-spin mr-2"></i>Application...';

    // Pr�parer les donn�es
    const formData = {
        type_remise: typeRemise,
        valeur_remise: parseFloat(valeurRemise),
        raison_remise: raisonRemise
    };

    // R�cup�rer le CSRF token
    const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]').value;

    // Appeler l'API
    fetch(`/operateur-confirme/appliquer-remise/${panierId}/`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': csrfToken,
            'X-Requested-With': 'XMLHttpRequest',
        },
        body: JSON.stringify(formData)
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            showNotification(data.message, 'success');

            // Fermer le modal
            fermerModalRemise();

            // Mettre � jour l'interface
            mettreAJourAffichageRemise(panierId, data.data);

            // Recalculer le total de la commande
            mettreAJourTotalCommande();

        } else {
            showNotification(data.error || 'Erreur lors de l\'application de la remise', 'error');
        }
    })
    .catch(error => {
        console.error('Erreur:', error);
        showNotification('Erreur de connexion', 'error');
    })
    .finally(() => {
        // R�activer le bouton
        btnAppliquer.disabled = false;
        btnAppliquer.innerHTML = '<i class="fas fa-check mr-2"></i>Appliquer la remise';
    });
}

/**
 * Retire une remise appliqu�e sur un panier
 * @param {number} panierId - ID du panier
 */
function retirerRemise(panierId) {
    if (!confirm('�tes-vous s�r de vouloir retirer cette remise ?')) {
        return;
    }

    // R�cup�rer le CSRF token
    const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]').value;

    // Appeler l'API
    fetch(`/operateur-confirme/retirer-remise/${panierId}/`, {
        method: 'POST',
        headers: {
            'X-CSRFToken': csrfToken,
            'X-Requested-With': 'XMLHttpRequest',
        }
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            showNotification(data.message, 'success');

            // Supprimer l'affichage de la remise
            supprimerAffichageRemise(panierId);

            // Mettre � jour le sous-total
            const sousTotalElement = document.getElementById(`sous-total-${panierId}`);
            if (sousTotalElement) {
                sousTotalElement.textContent = `${data.data.sous_total_restaure.toFixed(2)} DH`;
            }

            // Recalculer le total de la commande
            mettreAJourTotalCommande();

        } else {
            showNotification(data.error || 'Erreur lors du retrait de la remise', 'error');
        }
    })
    .catch(error => {
        console.error('Erreur:', error);
        showNotification('Erreur de connexion', 'error');
    });
}

/**
 * Met � jour l'affichage de la remise dans l'interface
 * @param {number} panierId - ID du panier
 * @param {Object} data - Donn�es de la remise
 */
function mettreAJourAffichageRemise(panierId, data) {
    const panierCard = document.querySelector(`[data-article-id="${panierId}"]`);
    if (!panierCard) return;

    // Mettre � jour le sous-total
    const sousTotalElement = document.getElementById(`sous-total-${panierId}`);
    if (sousTotalElement) {
        sousTotalElement.textContent = `${data.nouveau_sous_total.toFixed(2)} DH`;
    }

    // Chercher ou cr�er le conteneur de remise
    let remiseContainer = panierCard.querySelector('.remise-info-container');
    if (!remiseContainer) {
        // Cr�er le conteneur apr�s le sous-total
        const sousTotalDiv = panierCard.querySelector(`#sous-total-${panierId}`).parentElement;
        remiseContainer = document.createElement('div');
        remiseContainer.className = 'remise-info-container mt-2';
        sousTotalDiv.appendChild(remiseContainer);
    }

    // Afficher les informations de la remise
    remiseContainer.innerHTML = `
        <div class="bg-green-50 border-l-4 border-green-500 p-2 text-xs">
            <div class="flex items-center justify-between mb-1">
                <span class="text-green-700 font-semibold">
                    <i class="fas fa-tag mr-1"></i>Remise
                    ${data.type_remise === 'POURCENTAGE' ? `${data.valeur_remise}%` : ''}
                </span>
                <button type="button" onclick="retirerRemise(${panierId})"
                        class="text-red-500 hover:text-red-700 text-xs"
                        title="Retirer la remise">
                    <i class="fas fa-times"></i>
                </button>
            </div>
            <div class="text-gray-700">
                <span class="line-through text-gray-500">${data.sous_total_original.toFixed(2)} DH</span>
                <strong class="text-red-600 ml-2">- ${data.montant_remise.toFixed(2)} DH</strong>
            </div>
        </div>
    `;

    // Modifier le bouton "Appliquer remise" en "Modifier remise" si n�cessaire
    const btnRemise = panierCard.querySelector('.btn-appliquer-remise');
    if (btnRemise) {
        btnRemise.remove(); // On retire le bouton car on a maintenant le bouton "Retirer"
    }
}

/**
 * Supprime l'affichage de la remise de l'interface
 * @param {number} panierId - ID du panier
 */
function supprimerAffichageRemise(panierId) {
    const panierCard = document.querySelector(`[data-article-id="${panierId}"]`);
    if (!panierCard) return;

    // Supprimer le conteneur de remise
    const remiseContainer = panierCard.querySelector('.remise-info-container');
    if (remiseContainer) {
        remiseContainer.remove();
    }
}

/**
 * Met � jour le total de la commande (fonction existante, � adapter si n�cessaire)
 */
function mettreAJourTotalCommande() {
    // Cette fonction devrait d�j� exister dans le code
    // Elle recalcule le total en additionnant tous les sous-totaux
    let total = 0;

    // Parcourir tous les sous-totaux
    document.querySelectorAll('[id^="sous-total-"]').forEach(element => {
        const montant = parseFloat(element.textContent.replace(/[^\d.,]/g, '').replace(',', '.'));
        if (!isNaN(montant)) {
            total += montant;
        }
    });

    // Ajouter les frais de livraison si activ�s
    const fraisElement = document.getElementById('frais-livraison-montant');
    if (fraisElement && fraisElement.style.display !== 'none') {
        const frais = parseFloat(fraisElement.textContent.replace(/[^\d.,]/g, '').replace(',', '.'));
        if (!isNaN(frais)) {
            total += frais;
        }
    }

    // Mettre � jour l'affichage du total
    const totalElements = [
        document.getElementById('total_commande_haut_page'),
        document.querySelector('[data-total-commande]'),
        document.getElementById('total-commande')
    ];

    totalElements.forEach(element => {
        if (element) {
            element.textContent = `${total.toFixed(2)} DH`;
        }
    });
}

// Fonction utilitaire pour afficher les notifications (si elle n'existe pas d�j�)
if (typeof showNotification !== 'function') {
    function showNotification(message, type = 'info') {
        const notification = document.createElement('div');
        notification.className = `fixed top-4 right-4 z-50 p-4 rounded-lg shadow-lg max-w-sm transition-all duration-300 transform translate-x-full`;

        if (type === 'success') {
            notification.className += ' bg-green-100 border border-green-400 text-green-700';
        } else if (type === 'error') {
            notification.className += ' bg-red-100 border border-red-400 text-red-700';
        } else {
            notification.className += ' bg-blue-100 border border-blue-400 text-blue-700';
        }

        notification.innerHTML = `
            <div class="flex items-center">
                <i class="fas fa-${type === 'success' ? 'check-circle' : type === 'error' ? 'exclamation-circle' : 'info-circle'} mr-2"></i>
                <span>${message}</span>
            </div>
        `;

        document.body.appendChild(notification);

        setTimeout(() => {
            notification.classList.remove('translate-x-full');
        }, 100);

        setTimeout(() => {
            notification.classList.add('translate-x-full');
            setTimeout(() => {
                document.body.removeChild(notification);
            }, 300);
        }, 3000);
    }
}

// Alias pour compatibilite
function afficherModalRemise(panierId) {
    const modal = document.getElementById('remiseModal');
    if (!modal) {
        console.error('Modale de remise non trouvée');
        return;
    }
    ouvrirModalRemise(panierId);
}
