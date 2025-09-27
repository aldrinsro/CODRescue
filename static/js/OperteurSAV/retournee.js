
/**
 * Ouvre la modale de retour complet
 * @param {number} commandeId - ID de la commande (optionnel pour compatibilité)
 */
function ouvrirModalRetourComplet(commandeId = null) {
    console.log('🔧 DEBUG: ouvrirModalRetourComplet appelée avec commandeId:', commandeId);

    // Stocker les informations de la commande
    if (commandeId) {
        currentCommandeId = commandeId;
    } else {
        currentCommandeId = document.querySelector('[data-commande-id]')?.dataset.commandeId;
    }
    currentCommandeIdYz = document.querySelector('[data-commande-id-yz]')?.dataset.commandeIdYz;

    console.log('🔧 DEBUG: Variables stockées pour retour complet:', {
        currentCommandeId,
        currentCommandeIdYz
    });

    // Mettre à jour le titre de la modale
    const modalTitle = document.getElementById('retourCompletModalTitle');
    if (modalTitle) {
        modalTitle.textContent = `Retour Complet - Commande ${currentCommandeIdYz}`;
    }

    // Afficher la modale
    const modal = document.getElementById('retourCompletModal');
    if (modal) {
        modal.classList.remove('hidden');
        console.log('✅ Modale de retour complet ouverte');
    } else {
        console.error('❌ Modale de retour complet non trouvée');
    }
}

/**
 * Ferme la modale de retour complet
 */
function fermerModalRetourComplet() {
    console.log('🔧 DEBUG: fermerModalRetourComplet appelée');

    const modal = document.getElementById('retourCompletModal');
    if (modal) {
        modal.classList.add('hidden');
        console.log('✅ Modale de retour complet fermée');
    }

    // Réinitialiser le formulaire
    const form = document.getElementById('retourCompletForm');
    if (form) {
        form.reset();
    }

    // Réinitialiser les variables
    currentCommandeId = null;
    currentCommandeIdYz = null;
}

/**
 * Soumet le formulaire de retour complet
 */
function soumettreRetourComplet() {
    console.log('🔧 DEBUG: soumettreRetourComplet appelée');

    const form = document.getElementById('retourCompletForm');
    if (!form) {
        console.error('❌ Formulaire de retour complet non trouvé');
        alert('❌ Erreur: Formulaire non trouvé');
        return;
    }

    // Validation du commentaire
    const commentaire = document.getElementById('commentaireRetour').value.trim();
    if (commentaire === '') {
        alert('⚠️ Le commentaire est obligatoire');
        return;
    }

    // Vérifier que l'ID de la commande est disponible
    if (!currentCommandeId) {
        alert('❌ Erreur: Impossible de déterminer l\'ID de la commande');
        return;
    }

    // Préparer les données du formulaire
    const formData = new FormData(form);

    // Définir l'URL de soumission
    const actionUrl = `/operateur-logistique/commandes/${currentCommandeId}/retourne`;
    console.log('🔧 DEBUG: URL de soumission:', actionUrl);

    // Afficher un indicateur de chargement
    const confirmBtn = document.getElementById('confirmRetourCompletBtn');
    if (confirmBtn) {
        confirmBtn.disabled = true;
        confirmBtn.innerHTML = '<i class="fas fa-spinner fa-spin mr-2"></i>Traitement...';
    }

    // Vérifier le token CSRF
    const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]');
    if (!csrfToken) {
        alert('❌ Erreur: Token CSRF non trouvé');
        return;
    }

    fetch(actionUrl, {
        method: 'POST',
        headers: {
            'X-CSRFToken': csrfToken.value,
            'Content-Type': 'application/x-www-form-urlencoded',
        },
        body: new URLSearchParams(formData)
    })
    .then(response => {
        console.log('🔧 DEBUG: Response status:', response.status);

        if (!response.ok) {
            throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        }

        return response.json();
    })
    .then(data => {
        if (data.success) {
            alert(`✅ ${data.message}`);
            // Fermer la modale
            fermerModalRetourComplet();
            // Recharger la page pour voir les changements
            window.location.reload();
        } else {
            alert(`❌ Erreur: ${data.error || 'Erreur inconnue'}`);
        }
    })
    .catch(error => {
        console.error('❌ Erreur lors de la soumission:', error);
        alert(`❌ Une erreur est survenue: ${error.message}`);
    })
    .finally(() => {
        // Restaurer le bouton
        if (confirmBtn) {
            confirmBtn.disabled = false;
            confirmBtn.innerHTML = 'Confirmer le Retour Complet';
        }
    });
}
