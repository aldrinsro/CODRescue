
// ================== VALIDATION DES SECTIONS ==================





// Utils CSRF: récupérer le token depuis le cookie ou le DOM
function getCookie(name) {
    const cookieValue = document.cookie
        .split('; ')
        .find(row => row.startsWith(name + '='));
    return cookieValue ? decodeURIComponent(cookieValue.split('=')[1]) : null;
}

function getCsrfToken() {
    // 1) Essayer via un input de formulaire rendu par Django
    const input = document.querySelector('input[name="csrfmiddlewaretoken"]');
    if (input && input.value) return input.value;
    // 2) Essayer via une meta si présente
    const meta = document.querySelector('meta[name="csrf-token"]');
    if (meta && meta.content) return meta.content;
    // 3) Fallback cookie
    return getCookie('csrftoken');
}

function isJsonResponse(response) {
    const contentType = response.headers.get('Content-Type') || '';
    return contentType.includes('application/json');
}

// Fonction pour valider une section
function validerSection(sectionId, event) {
    const sectionElement = event.target.closest('.verification-item');
    const sectionName = getSectionName(sectionId);
    
    // Traitement spécifique pour les informations de livraison
    if (sectionId === 'informations-livraison') {
        sauvegarderInformationsLivraison(sectionElement, sectionName, event);
        return;
    }

    // Traitement spécifique pour les informations client
    if (sectionId === 'informations-client') {
        sauvegarderInformationsClient(sectionElement, sectionName, event);
        return;
    }

    // Animation de validation pour les autres sections
    sectionElement.classList.add('verified');

    // Afficher une notification de succès
    showToast(`✅ ${sectionName} validée avec succès !`, 'success');

    // Optionnel : Désactiver le bouton après validation
    const button = event.target;
    button.innerHTML = '<i class="fas fa-check-double mr-2"></i>Validé';
    button.disabled = true;
    button.style.background = '#6b7280';
    button.style.cursor = 'not-allowed';
    button.classList.add('cursor-not-allowed');


}

// Nouvelle fonction pour sauvegarder les informations client
function sauvegarderInformationsClient(sectionElement, sectionName, event) {
    const button = event.target;

    // Récupérer les données des champs
    const nom = document.querySelector('[name="client_nom"]').value.trim();
    const prenom = document.querySelector('[name="client_prenom"]').value.trim();
    const telephone = document.querySelector('[name="client_telephone"]').value.trim();

    // Simple validation côté client
    if (!nom || !telephone) {
        showToast('⚠️ Tous les champs client Nom, Téléphone sont obligatoires.', 'warning');
        return;
    }

    // Désactiver le bouton pendant la sauvegarde
    button.disabled = true;
    button.innerHTML = '<i class="fas fa-spinner fa-spin mr-2"></i>Sauvegarde...';

    // Préparer les données à envoyer
    const formData = new FormData();
    formData.append('action', 'save_client_info');
    formData.append('nom', nom);
    formData.append('prenom', prenom);
    formData.append('telephone', telephone);

    const url = `/operateur-confirme/commandes/${commandeId}/modifier/`;

    // Envoyer la requête AJAX
    fetch(url, {
        method: 'POST',
        body: formData,
        headers: {
            'X-Requested-With': 'XMLHttpRequest',
            'X-CSRFToken': getCsrfToken()
        },
        credentials: 'same-origin'
    })
    .then(async response => {
        if (!response.ok) {
            // Tente de lire la réponse texte (souvent une page HTML 403)
            const text = await response.text();
            throw new Error(`HTTP ${response.status} ${response.statusText}: ${text.slice(0, 200)}`);
        }
        if (!isJsonResponse(response)) {
            const text = await response.text();
            throw new Error(`Réponse non JSON du serveur: ${text.slice(0, 200)}`);
        }
        return response.json();
    })
    .then(data => {
        if (data.success) {
            // Animation de validation
            sectionElement.classList.add('verified');

            // Afficher une notification de succès
            showToast(`✅ ${sectionName} sauvegardée avec succès !`, 'success');

            // Mettre à jour le bouton
            button.innerHTML = '<i class="fas fa-check-double mr-2"></i>Validé';
            button.style.background = '#6b7280';
            button.style.cursor = 'not-allowed';
            button.classList.add('cursor-not-allowed');

            
        } else {
            // Erreur lors de la sauvegarde
            showToast(`❌ Erreur lors de la sauvegarde : ${data.error || 'Erreur inconnue'}`, 'error');

            // Réactiver le bouton
            button.disabled = false;
            button.innerHTML = '<i class="fas fa-user mr-2"></i>Valider les infos client';
        }
    })
    .catch(error => {
        console.error('Erreur lors de la sauvegarde des informations client:', error);
        showToast('❌ Erreur de connexion lors de la sauvegarde', 'error');

        // Réactiver le bouton
        button.disabled = false;
        button.innerHTML = '<i class="fas fa-check mr-2"></i>Valider les infos client';
    });
}

// Fonction pour sauvegarder les informations de livraison
function sauvegarderInformationsLivraison(sectionElement, sectionName, event) {
    const button = event.target;
    
    // Récupérer les données de livraison
    const villeSelect = document.querySelector('select[name="ville_livraison"]');
    const adresseTextarea = document.querySelector('textarea[name="adresse_livraison"]');
    
    const villeId = villeSelect ? villeSelect.value : '';
    const adresse = adresseTextarea ? adresseTextarea.value.trim() : '';
    
    // Validation simple côté client
    if (!villeId) {
        showToast('⚠️ Veuillez sélectionner une ville de livraison.', 'warning');
        return;
    }
    if (!adresse || adresse === '' || adresse === 'N/A') {
        showToast('⚠️ Le champ Adresse doit être renseigné.', 'warning');
        return;
    }
    
    // Désactiver le bouton pendant la sauvegarde
    button.disabled = true;
    button.innerHTML = '<i class="fas fa-spinner fa-spin mr-2"></i>Sauvegarde...';
    
    // Préparer les données à envoyer (ville + adresse)
    const formData = new FormData();
    formData.append('action', 'save_livraison');
    formData.append('ville_livraison', villeId);
    formData.append('adresse_livraison', adresse);


    const urlLivraison = `/operateur-confirme/commandes/${commandeId}/modifier/`;
    
    // Envoyer la requête AJAX
    fetch(urlLivraison, {
        method: 'POST',
        body: formData,
        headers: {
            'X-Requested-With': 'XMLHttpRequest',
            'X-CSRFToken': getCsrfToken()
        },
        credentials: 'same-origin'
    })
    .then(async response => {
        if (!response.ok) {
            const text = await response.text();
            throw new Error(`HTTP ${response.status} ${response.statusText}: ${text.slice(0, 200)}`);
        }
        if (!isJsonResponse(response)) {
            const text = await response.text();
            throw new Error(`Réponse non JSON du serveur: ${text.slice(0, 200)}`);
        }
        return response.json();
    })
    .then(data => {
        if (data.success) {
            // Animation de validation
            sectionElement.classList.add('verified');
            
            // Mettre à jour les champs affichés si des données sont retournées
            if (data.ville_nom) {
                const regionDisplay = document.getElementById('region-display');
                if (regionDisplay && data.region_nom) {
                    regionDisplay.value = data.region_nom;
                }
                
                const fraisDisplay = document.getElementById('frais-display');
                if (fraisDisplay && data.frais_livraison !== null) {
                    fraisDisplay.value = `${data.frais_livraison} DH`;
                }
                
                // Mettre à jour le total avec les nouveaux calculs du serveur
                if (data.nouveau_total !== undefined) {
                    const totalElement = document.getElementById('total-commande');
                    if (totalElement) {
                        totalElement.textContent = `${data.nouveau_total.toFixed(2)} DH`;
                    }
                }
                
                // Mettre à jour le sous-total des articles
                if (data.sous_total_articles !== undefined) {
                    const sousTotalElement = document.getElementById('sous-total-articles');
                    if (sousTotalElement) {
                        sousTotalElement.textContent = `${data.sous_total_articles.toFixed(2)} DH`;
                    }
                }
            }
            
            // Afficher une notification de succès avec le message du serveur
            showToast(`✅ ${data.message}`, 'success');
            
            // Mettre à jour le bouton
            button.innerHTML = '<i class="fas fa-check-double mr-2"></i>Validé';
            button.style.background = '#6b7280';
            button.style.cursor = 'not-allowed';
            button.classList.add('cursor-not-allowed');
            
           
        } else {
            // Erreur lors de la sauvegarde
            showToast(`❌ Erreur lors de la sauvegarde : ${data.error || 'Erreur inconnue'}`, 'error');
            
            // Réactiver le bouton
            button.disabled = false;
            button.innerHTML = '<i class="fas fa-truck mr-2"></i>Valider la livraison';
        }
    })
    .catch(error => {
        console.error('Erreur lors de la sauvegarde des informations de livraison:', error);
        showToast('❌ Erreur de connexion lors de la sauvegarde', 'error');
        
        // Réactiver le bouton
        button.disabled = false;
        button.innerHTML = '<i class="fas fa-truck mr-2"></i>Valider la livraison';
    });
}

// Fonction pour obtenir le nom de la section
function getSectionName(sectionId) {
    const sectionNames = {
        'informations-commande': 'Section Informations Commande',
        'informations-client': 'Section Informations Client',
        'informations-livraison': 'Section Informations Livraison',
        'gestion-operations': 'Section Gestion des Opérations',
        'articles-commande': 'Section Articles de la Commande'
    };
    return sectionNames[sectionId] || 'Section';
}

// Fonction pour afficher les notifications toast
function showToast(message, type = 'info', duration = 3000) {
    // Créer l'élément toast
    const toast = document.createElement('div');
    toast.className = `fixed top-4 right-4 z-50 px-6 py-4 rounded-lg shadow-lg text-white font-medium transition-all duration-300 transform translate-x-full`;
    
    // Définir les couleurs selon le type
    const colors = {
        'success': 'bg-green-600',
        'error': 'bg-red-600',
        'warning': 'bg-yellow-600',
        'info': 'bg-blue-600'
    };
    
    toast.classList.add(colors[type] || colors['info']);
    toast.innerHTML = message;
    
    // Ajouter au DOM
    document.body.appendChild(toast);
    
    // Animation d'entrée
    setTimeout(() => {
        toast.classList.remove('translate-x-full');
    }, 100);
    
    // Animation de sortie et suppression
    setTimeout(() => {
        toast.classList.add('translate-x-full');
        setTimeout(() => {
            if (toast.parentNode) {
                toast.parentNode.removeChild(toast);
            }
        }, 300);
    }, duration);
}