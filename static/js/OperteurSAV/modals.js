/**
 * Gestion des modales pour l'opérateur SAV
 * Ce fichier contient toutes les fonctions d'ouverture et fermeture des modales
 */

console.log('🔧 DEBUG: modals.js chargé');

// Variables globales pour les modales
let currentCommandeId = null;
let currentCommandeIdYz = null;
let currentCommandePayement = null;

/**
 * Ouvre la modale SAV avec l'état spécifié
 * @param {string} etat - L'état de la commande (Livrée, Retournée, etc.)
 * @param {number} commandeId - ID de la commande (optionnel pour compatibilité)
 */
function openSavModal(etat, commandeId = null) {
    console.log('🔧 DEBUG: openSavModal appelée avec etat:', etat, 'et commandeId:', commandeId);
    
    // Stocker les informations de la commande
    if (commandeId) {
        currentCommandeId = commandeId;
    } else {
        currentCommandeId = document.querySelector('[data-commande-id]')?.dataset.commandeId;
    }
    currentCommandeIdYz = document.querySelector('[data-commande-id-yz]')?.dataset.commandeIdYz;
    currentCommandePayement = document.querySelector('[data-commande-payement]')?.dataset.commandePayement;
    
    console.log('🔧 DEBUG: Variables stockées:', {
        currentCommandeId,
        currentCommandeIdYz,
        currentCommandePayement
    });
    
    // Mettre à jour le titre de la modale
    const modalTitle = document.getElementById('savModalTitle');
    if (modalTitle) {
        modalTitle.textContent = `Actions SAV - Commande ${currentCommandeIdYz}`;
    }
    
    // Mettre à jour le champ caché avec l'état
    const etatInput = document.getElementById('nouvel_etat_input');
    if (etatInput) {
        etatInput.value = etat;
        console.log('✅ État défini:', etat);
    } else {
        console.error('❌ Champ nouvel_etat_input non trouvé');
    }
    
    // Gestion de l'affichage conditionnel des champs selon l'état
    const dateReportDiv = document.getElementById('dateReportDiv');
    const dateLivraisonDiv = document.getElementById('dateLivraisonDiv');
    const dateReportInput = document.getElementById('date_report');
    const dateLivraisonInput = document.getElementById('date_livraison');
    
    // Masquer tous les champs de date par défaut
    if (dateReportDiv) dateReportDiv.classList.add('hidden');
    if (dateLivraisonDiv) dateLivraisonDiv.classList.add('hidden');
    if (dateReportInput) dateReportInput.removeAttribute('required');
    if (dateLivraisonInput) dateLivraisonInput.removeAttribute('required');
    
    // Afficher le champ approprié selon l'état
    if (etat === 'Reportée') {
        if (dateReportDiv) {
            dateReportDiv.classList.remove('hidden');
            console.log('✅ Champ date de report affiché');
        }
        if (dateReportInput) {
            dateReportInput.setAttribute('required', '');
        }
    } else if (etat === 'Livrée') {
        if (dateLivraisonDiv) {
            dateLivraisonDiv.classList.remove('hidden');
            console.log('✅ Champ date de livraison affiché');
        }
        if (dateLivraisonInput) {
            dateLivraisonInput.setAttribute('required', '');
            // Définir la date d'aujourd'hui par défaut
            const today = new Date().toISOString().split('T')[0];
            dateLivraisonInput.value = today;
        }
    }
    
    // Gestion de l'affichage des optgroups de commentaires
    const optgroupLivraison = document.querySelector('.optgroup-livraison');
    const optgroupProblemes = document.querySelector('.optgroup-problemes');
    const optgroupRetours = document.querySelector('.optgroup-retours');
    const optgroupCommunication = document.querySelector('.optgroup-communication');
    const optgroupAutres = document.querySelector('.optgroup-autres');
    
    // Masquer tous les optgroups par défaut
    [optgroupLivraison, optgroupProblemes, optgroupRetours, optgroupCommunication, optgroupAutres].forEach(optgroup => {
        if (optgroup) {
            optgroup.style.display = 'none';
        }
    });
    
    // Afficher les optgroups appropriés selon l'état
    if (etat === 'Livrée') {
        if (optgroupLivraison) {
            optgroupLivraison.style.display = 'block';
            console.log('✅ Options de livraison affichées');
        }
        if (optgroupAutres) {
            optgroupAutres.style.display = 'block';
        }
    } else if (etat === 'Retournée') {
        if (optgroupProblemes) {
            optgroupProblemes.style.display = 'block';
            console.log('✅ Options de problèmes affichées');
        }
        if (optgroupRetours) {
            optgroupRetours.style.display = 'block';
        }
        if (optgroupAutres) {
            optgroupAutres.style.display = 'block';
        }
    } else if (etat === 'Reportée') {
        if (optgroupCommunication) {
            optgroupCommunication.style.display = 'block';
            console.log('✅ Options de communication affichées');
        }
        if (optgroupAutres) {
            optgroupAutres.style.display = 'block';
        }
    } else {
        // Pour les autres états, afficher tous les optgroups
        [optgroupLivraison, optgroupProblemes, optgroupRetours, optgroupCommunication, optgroupAutres].forEach(optgroup => {
            if (optgroup) {
                optgroup.style.display = 'block';
            }
        });
    }
    
    // Réinitialiser la sélection du commentaire
    const commentaireSelect = document.getElementById('commentaire');
    if (commentaireSelect) {
        commentaireSelect.value = '';
    }
    
    // Afficher la modale
    const modal = document.getElementById('savModal');
    if (modal) {
        modal.classList.remove('hidden');
        console.log('✅ Modale SAV ouverte');
    } else {
        console.error('❌ Modale SAV non trouvée');
    }
}

/**
 * Soumet le formulaire SAV avec validation
 */
function soumettreFormulaireSav() {
    console.log('🔧 DEBUG: soumettreFormulaireSav appelée');
    
    const form = document.getElementById('savForm');
    if (!form) {
        console.error('❌ Formulaire SAV non trouvé');
        alert('❌ Erreur: Formulaire non trouvé');
        return;
    }
    
    // Validation du formulaire SAV
    const commentaire = document.getElementById('commentaire').value.trim();
    if (commentaire === '') {
        alert('⚠️ Le commentaire est obligatoire');
        return;
    }
    
    // Si "Autre motif" est sélectionné, vérifier le commentaire personnalisé
    if (commentaire === 'Autre motif - voir détails') {
        const commentaireCustom = document.getElementById('commentaireCustom');
        if (!commentaireCustom || !commentaireCustom.value.trim()) {
            alert('⚠️ Le commentaire personnalisé est obligatoire pour "Autre motif"');
            return;
        }
    }
    
    // Vérifier que l'ID de la commande est disponible
    if (!currentCommandeId) {
        alert('❌ Erreur: Impossible de déterminer l\'ID de la commande');
        return;
    }
    
    // Préparer les données du formulaire
    const formData = new FormData(form);
    
    // Si un commentaire personnalisé est fourni, l'ajouter
    const commentaireCustom = document.getElementById('commentaireCustom');
    if (commentaireCustom && commentaireCustom.value.trim()) {
        formData.set('commentaire', commentaireCustom.value.trim());
    }
    
    // Définir l'URL de soumission
    const actionUrl = `/operateur-logistique/commande/${currentCommandeId}/changer-etat-sav/`;
    console.log('🔧 DEBUG: URL de soumission:', actionUrl);
    console.log('🔧 DEBUG: currentCommandeId:', currentCommandeId);
    console.log('🔧 DEBUG: FormData contents:', Array.from(formData.entries()));
    
    // Afficher un indicateur de chargement
    const confirmBtn = document.getElementById('confirmSavBtn');
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
    console.log('🔧 DEBUG: Token CSRF trouvé:', csrfToken.value.substring(0, 20) + '...');
    
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
        console.log('🔧 DEBUG: Response URL:', response.url);
        console.log('🔧 DEBUG: Response headers:', {
            'content-type': response.headers.get('content-type'),
            'location': response.headers.get('location')
        });
        
        // Vérifier si c'est une redirection
        if (response.redirected) {
            console.log('🔧 DEBUG: Redirection détectée vers:', response.url);
        }
        
        // Vérifier le Content-Type
        const contentType = response.headers.get('content-type') || '';
        if (!contentType.includes('application/json')) {
            console.log('❌ ERREUR: Réponse non-JSON détectée. Content-Type:', contentType);
            
            if (response.url.includes('login') || response.url.includes('auth')) {
                throw new Error('Session expirée. Veuillez vous reconnecter.');
            }
            
            if (response.status === 404) {
                throw new Error('URL non trouvée (404). Vérifiez l\'URL de l\'API.');
            }
            
            if (response.status === 403) {
                throw new Error('Accès interdit (403). Vérifiez vos permissions.');
            }
            
            if (response.status === 405) {
                throw new Error('Méthode non autorisée (405). L\'endpoint n\'accepte peut-être pas POST.');
            }
        }
        
        if (!response.ok) {
            throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        }
        
        return response.text(); // Récupérer la réponse en tant que texte d'abord
    })
    .then(responseText => {
        console.log('🔧 DEBUG: Response text:', responseText);
        
        try {
            const data = JSON.parse(responseText);
            
            if (data.success) {
                alert(`✅ ${data.message}`);
                // Fermer les modales
                fermerModalSav();
                fermerModalActionsSav();
                // Recharger la page pour voir les changements
                window.location.reload();
            } else {
                alert(`❌ Erreur: ${data.error || 'Erreur inconnue'}`);
            }
        } catch (jsonError) {
            console.error('❌ Erreur de parsing JSON:', jsonError);
            console.error('❌ Réponse reçue:', responseText.substring(0, 500)); // Afficher les 500 premiers caractères
            alert(`❌ Erreur: Réponse serveur invalide. Vérifiez la console pour plus de détails.`);
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
            confirmBtn.innerHTML = 'Confirmer la mise à jour';
        }
    });
}

/**
 * Ferme la modale SAV et réinitialise les variables
 */
function fermerModalSav() {
    console.log('🔧 DEBUG: fermerModalSav appelée');
    
    const modal = document.getElementById('savModal');
    if (modal) {
        modal.classList.add('hidden');
        console.log('✅ Modale SAV fermée');
    }
    
    // Réinitialiser les variables
    currentCommandeId = null;
    currentCommandeIdYz = null;
    currentCommandePayement = null;
    
    // Réinitialiser le formulaire
    const form = document.getElementById('savForm');
    if (form) {
        form.reset();
    }
    
    // Masquer le champ de commentaire personnalisé
    const commentairePersonnalise = document.getElementById('commentairePersonnalise');
    if (commentairePersonnalise) {
        commentairePersonnalise.classList.add('hidden');
    }
    
    // Masquer et réinitialiser les champs de date
    const dateReportDiv = document.getElementById('dateReportDiv');
    const dateLivraisonDiv = document.getElementById('dateLivraisonDiv');
    const dateReportInput = document.getElementById('date_report');
    const dateLivraisonInput = document.getElementById('date_livraison');
    
    if (dateReportDiv) dateReportDiv.classList.add('hidden');
    if (dateLivraisonDiv) dateLivraisonDiv.classList.add('hidden');
    if (dateReportInput) {
        dateReportInput.value = '';
        dateReportInput.removeAttribute('required');
    }
    if (dateLivraisonInput) {
        dateLivraisonInput.value = '';
        dateLivraisonInput.removeAttribute('required');
    }
    
    // Réinitialiser l'affichage des optgroups de commentaires
    const optgroups = document.querySelectorAll('#commentaire optgroup');
    optgroups.forEach(optgroup => {
        if (optgroup) {
            optgroup.style.display = 'none';
        }
    });
    
    // Réinitialiser la sélection du commentaire
    const commentaireSelect = document.getElementById('commentaire');
    if (commentaireSelect) {
        commentaireSelect.value = '';
    }
}

/**
 * Ferme la modale de calculs
 */
function fermerModalCalculs() {
    const modal = document.getElementById('calculsModal');
    if (modal) {
        modal.classList.add('hidden');
    }
}

/**
 * Ferme la modale de valeur totale
 */
function fermerModalValeurTotale() {
    const modal = document.getElementById('valeurTotaleModal');
    if (modal) {
        modal.classList.add('hidden');
    }
}

/**
 * Ferme la modale de frais de livraison
 */
function fermerModalFraisLivraison() {
    const modal = document.getElementById('fraisLivraisonModal');
    if (modal) {
        modal.classList.add('hidden');
    }
}

/**
 * Ouvre la modale de renvoi
 */
function openRenvoyerModal() {
    const modal = document.getElementById('renvoyerModal');
    if (modal) {
        modal.classList.remove('hidden');
    }
}

/**
 * Ferme la modale de renvoi
 */
function closeRenvoyerModal() {
    const modal = document.getElementById('renvoyerModal');
    if (modal) {
        modal.classList.add('hidden');
    }
}

/**
 * Ouvre la modale de livraison partielle
 * @param {number} commandeId - ID de la commande (optionnel pour compatibilité)
 */
function ouvrirModalLivraisonPartielle(commandeId = null) {
    console.log('🔧 DEBUG: ouvrirModalLivraisonPartielle appelée avec commandeId:', commandeId);
    
    const modal = document.getElementById('livraisonPartielleModal');
    if (modal) {
        modal.classList.remove('hidden');
        console.log('✅ Modale de livraison partielle ouverte');
        
        // Si on a un ID de commande, charger les articles via AJAX
        if (commandeId) {
            chargerArticlesCommande(commandeId);
        } else {
            // Mode compatibilité - initialiser avec les articles présents dans le DOM
            initialiserModalLivraisonPartielle();
        }
    } else {
        console.error('❌ Modale de livraison partielle non trouvée');
    }
}

/**
 * Ferme la modale de livraison partielle
 */
function fermerModalLivraisonPartielle() {
    console.log('🔧 DEBUG: fermerModalLivraisonPartielle appelée');
    
    const modal = document.getElementById('livraisonPartielleModal');
    if (modal) {
        modal.classList.add('hidden');
        console.log('✅ Modale de livraison partielle fermée');
        
        // Réinitialiser le formulaire
        const form = document.getElementById('livraisonPartielleForm');
        if (form) {
            form.reset();
        }
        
        // Réinitialiser les sections
        document.getElementById('articlesARenvoyerContainer').innerHTML = '';
        document.getElementById('aucunArticleRenvoyer').style.display = 'block';
        
        // Réinitialiser le résumé
        document.getElementById('totalArticlesLivres').textContent = '0';
        document.getElementById('totalArticlesRenvoyes').textContent = '0';
        document.getElementById('totalValeurLivree').textContent = '0.00 DH';
    }
}

/**
 * Ferme la modale SAV défectueux
 */
function fermerModalSavDefectueux() {
    const modal = document.getElementById('savDefectueuxModal');
    if (modal) {
        modal.classList.add('hidden');
    }
}

/**
 * Affiche la modale de valeur totale
 */
function afficherModalValeurTotale() {
    const modal = document.getElementById('valeurTotaleModal');
    if (modal) {
        modal.classList.remove('hidden');
    }
}

/**
 * Affiche la modale de frais de livraison
 */
function afficherModalFraisLivraison() {
    const modal = document.getElementById('fraisLivraisonModal');
    if (modal) {
        modal.classList.remove('hidden');
    }
}

/**
 * Affiche la modale de calculs
 */
function afficherModalCalculs() {
    const modal = document.getElementById('calculsModal');
    if (modal) {
        modal.classList.remove('hidden');
    }
}

/**
 * Ouvre la modale d'actions SAV (nouveau modal avec grille d'actions)
 * @param {number} commandeId - ID de la commande
 * @param {string} commandeIdYz - ID YZ de la commande
 */
function ouvrirModalActionsSav(commandeId = null, commandeIdYz = null) {
    console.log('🔧 DEBUG: ouvrirModalActionsSav appelée avec:', { commandeId, commandeIdYz });
    
    // Stocker les informations de la commande
    if (commandeId && commandeIdYz) {
        currentCommandeId = commandeId;
        currentCommandeIdYz = commandeIdYz;
    } else {
        currentCommandeId = document.querySelector('[data-commande-id]')?.dataset.commandeId;
        currentCommandeIdYz = document.querySelector('[data-commande-id-yz]')?.dataset.commandeIdYz;
    }
    currentCommandePayement = document.querySelector('[data-commande-payement]')?.dataset.commandePayement;
    
    console.log('🔧 DEBUG: Variables stockées pour modal actions:', {
        currentCommandeId,
        currentCommandeIdYz,
        currentCommandePayement
    });
    
    // Mettre à jour l'affichage de l'ID de commande
    const commandeIdDisplay = document.getElementById('commandeIdDisplay');
    if (commandeIdDisplay) {
        commandeIdDisplay.textContent = currentCommandeIdYz || currentCommandeId;
    }
    
    // Afficher la modale
    const modal = document.getElementById('savActionsModal');
    if (modal) {
        modal.classList.remove('hidden');
        console.log('✅ Modale d\'actions SAV ouverte');
    } else {
        console.error('❌ Modale d\'actions SAV non trouvée');
    }
}

/**
 * Ferme la modale d'actions SAV
 */
function fermerModalActionsSav() {
    console.log('🔧 DEBUG: fermerModalActionsSav appelée');
    
    const modal = document.getElementById('savActionsModal');
    if (modal) {
        modal.classList.add('hidden');
        console.log('✅ Modale d\'actions SAV fermée');
    }
    
    // Réinitialiser les variables
    currentCommandeId = null;
    currentCommandeIdYz = null;
    currentCommandePayement = null;
}

/**
 * Ouvre le modal SAV spécifique depuis le modal d'actions
 * @param {string} etat - L'état de la commande
 */
function ouvrirSavDepuisActions(etat) {
    console.log('🔧 DEBUG: ouvrirSavDepuisActions appelée avec etat:', etat);
    
    // Fermer le modal d'actions d'abord
    fermerModalActionsSav();
    
    // Petit délai pour permettre la fermeture propre
    setTimeout(() => {
        if (etat === 'Livrée Partiellement') {
            ouvrirModalLivraisonPartielle();
        } else {
            openSavModal(etat);
        }
    }, 100);
}

/**
 * Ouvre le modal de livraison partielle depuis le modal d'actions
 */
function ouvrirLivraisonPartielleDepuisActions() {
    console.log('🔧 DEBUG: ouvrirLivraisonPartielleDepuisActions appelée');
    
    // Récupérer l'ID de la commande depuis les variables globales
    const commandeId = currentCommandeId;
    
    // Fermer le modal d'actions d'abord
    fermerModalActionsSav();
    
    // Petit délai pour permettre la fermeture propre
    setTimeout(() => {
        ouvrirModalLivraisonPartielle(commandeId);
    }, 100);
}

/**
 * Charge les articles d'une commande via AJAX pour le modal de livraison partielle
 * @param {number} commandeId - ID de la commande
 */
function chargerArticlesCommande(commandeId) {
    console.log('🔧 DEBUG: chargerArticlesCommande appelée avec commandeId:', commandeId);
    
    // Afficher un indicateur de chargement
    const container = document.getElementById('articlesALivrerContainer');
    if (container) {
        container.innerHTML = `
            <div class="col-span-full text-center py-8">
                <i class="fas fa-spinner fa-spin text-2xl text-blue-500 mb-2"></i>
                <p class="text-gray-600">Chargement des articles...</p>
            </div>
        `;
    }
    
    // Construire l'URL pour récupérer les articles de la commande (endpoint existant)
    const url = `/operateur-logistique/api/commande/${commandeId}/panier/`;
    
    fetch(url, {
        method: 'GET',
        headers: {
            'X-Requested-With': 'XMLHttpRequest',
            'Content-Type': 'application/json',
        }
    })
    .then(response => {
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        return response.json();
    })
    .then(data => {
        console.log('✅ Articles récupérés:', data);
        
        // Stocker les données globalement pour utilisation par les autres fonctions
        window.currentPaniersData = data.paniers || data.articles || [];
        
        // Stocker les données de la commande
        if (data.commande) {
            currentCommandeId = data.commande.id;
            currentCommandeIdYz = data.commande.id_yz;
        }
        
        // Mettre à jour le titre du modal
        const titleElement = document.querySelector('#livraisonPartielleModal h3');
        if (titleElement && data.commande) {
            titleElement.innerHTML = `
                <i class="fas fa-box-open mr-3 text-blue-600"></i>
                Livraison Partielle - Commande ${data.commande.id_yz}
            `;
        }
        
        // Générer le HTML des articles
        genererArticlesHTML(data.paniers || data.articles || [], data.commande);
        
        // Mettre à jour l'action du formulaire
        const form = document.getElementById('livraisonPartielleForm');
        if (form && data.commande) {
            form.action = `/operateur-logistique/commande/${data.commande.id}/livraison-partielle/`;
        }
        
        // Initialiser les événements
        initialiserModalLivraisonPartielle();
        
    })
    .catch(error => {
        console.error('❌ Erreur lors du chargement des articles:', error);
        
        // Solution de fallback : utiliser les données du DOM si disponibles
        const commandeRow = document.querySelector(`[data-commande-id="${commandeId}"]`);
        if (commandeRow) {
            const commandeIdYz = commandeRow.dataset.commandeIdYz || '';
            
            container.innerHTML = `
                <div class="col-span-full text-center py-8">
                    <i class="fas fa-info-circle text-2xl text-blue-500 mb-4"></i>
                    <h4 class="text-lg font-semibold text-gray-900 mb-2">Chargement impossible</h4>
                    <p class="text-gray-600 mb-4">
                        Impossible de charger les articles dynamiquement.<br>
                        Veuillez utiliser la page de détails de la commande pour la livraison partielle.
                    </p>
                    <div class="flex justify-center space-x-4">
                        <a href="/operateur-logistique/commande/${commandeId}/" 
                           class="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors">
                            <i class="fas fa-external-link-alt mr-2"></i>
                            Ouvrir les détails
                        </a>
                        <button onclick="fermerModalLivraisonPartielle()" 
                                class="px-4 py-2 bg-gray-500 text-white rounded-lg hover:bg-gray-600 transition-colors">
                            Fermer
                        </button>
                    </div>
                </div>
            `;
        } else {
            container.innerHTML = `
                <div class="col-span-full text-center py-8">
                    <i class="fas fa-exclamation-triangle text-2xl text-red-500 mb-2"></i>
                    <p class="text-red-600">Erreur lors du chargement des articles</p>
                    <button onclick="fermerModalLivraisonPartielle()" class="mt-2 px-4 py-2 bg-gray-500 text-white rounded">
                        Fermer
                    </button>
                </div>
            `;
        }
    });
}

/**
 * Génère le HTML des articles pour le modal de livraison partielle
 * @param {Array} paniers - Liste des paniers de la commande (format API existante)
 * @param {Object} commande - Données de la commande
 */
function genererArticlesHTML(paniers, commande) {
    console.log('🔧 DEBUG: genererArticlesHTML appelée avec', paniers.length, 'paniers');
    
    const container = document.getElementById('articlesALivrerContainer');
    if (!container) {
        console.error('❌ Container articlesALivrerContainer non trouvé');
        return;
    }
    
    // Vider le container
    container.innerHTML = '';
    
    // Générer le HTML pour chaque article/panier
    paniers.forEach(panier => {
        const articleDiv = document.createElement('div');
        articleDiv.className = 'article-livraison-card bg-white rounded-lg border border-green-300 p-4 hover:border-green-400 transition-colors';
        articleDiv.dataset.panierId = panier.id; // L'API retourne id pour le panier
        articleDiv.dataset.articleId = panier.article_id || '';
        articleDiv.dataset.varianteId = '';  // Pas de variante_id dans l'API actuelle
        articleDiv.dataset.articleNom = panier.nom;
        // Utiliser prix_actuel (string) converti en float, avec fallback sur prix_unitaire
        const prixActuel = parseFloat(panier.prix_actuel || panier.prix_unitaire || 0);
        console.log(`🔧 DEBUG: Article ${panier.nom}, prix_actuel: ${panier.prix_actuel}, prix_unitaire: ${panier.prix_unitaire}, prix final: ${prixActuel}`);
        articleDiv.dataset.articlePrix = prixActuel.toFixed(2);
        articleDiv.dataset.sousTotal = panier.sous_total;
        articleDiv.dataset.quantiteMax = panier.quantite;
        
        // Construire les informations de variante depuis les champs directs
        let varianteInfo = '';
        const varianteParts = [];
        if (panier.couleur) varianteParts.push(panier.couleur);
        if (panier.pointure) varianteParts.push(panier.pointure);
        
        if (varianteParts.length > 0) {
            varianteInfo = ' - ' + varianteParts.join(' / ');
        }
        
        // Détails de la variante pour l'affichage
        let varianteDetails = '';
        if (panier.couleur) varianteDetails += `Couleur: ${panier.couleur}<br>`;
        if (panier.pointure) varianteDetails += `Pointure: ${panier.pointure}<br>`;
        
        articleDiv.innerHTML = `
            <div class="flex items-start space-x-3">
                <input type="checkbox" 
                       id="livrer_${panier.id}" 
                       class="article-livrer-checkbox h-5 w-5 text-green-600 focus:ring-green-500 border-gray-300 rounded mt-1"
                       data-panier-id="${panier.id}"
                       checked>
                <div class="flex-1">
                    <label for="livrer_${panier.id}" class="cursor-pointer">
                        <div class="font-medium text-gray-900">
                            ${panier.nom}${varianteInfo}
                        </div>
                        <div class="text-sm text-gray-500">
                            ${panier.reference ? `Réf: ${panier.reference}<br>` : ''}
                            ${varianteDetails}
                            <div class="flex justify-between items-center mt-1">
                                <span>Prix unitaire: ${prixActuel.toFixed(2)} DH</span>
                                <span class="font-medium text-blue-600">Sous-total: ${parseFloat(panier.sous_total).toFixed(2)} DH</span>
                            </div>
                        </div>
                    </label>
                    <div class="mt-3">
                        <label class="block text-xs font-medium text-gray-700 mb-1">
                            Quantité à livrer:
                        </label>
                        <input type="number" 
                               min="1" 
                               max="${panier.quantite}" 
                               value="${panier.quantite}"
                               class="quantite-livrer-input w-full px-2 py-1 text-sm border border-gray-300 rounded focus:ring-2 focus:ring-green-500 focus:border-green-500"
                               data-panier-id="${panier.id}">
                        <div class="text-xs text-gray-500 mt-1">
                            Max: ${panier.quantite}
                        </div>
                    </div>
                </div>
            </div>
        `;
        
        container.appendChild(articleDiv);
    });
    
    // Mettre à jour le total de la commande dans le résumé
    const totalCommandeElement = document.getElementById('totalCommandeLivraison');
    if (totalCommandeElement && commande) {
        totalCommandeElement.textContent = `${parseFloat(commande.total_cmd || 0).toFixed(2)} DH`;
        totalCommandeElement.dataset.totalCommande = parseFloat(commande.total_cmd || 0).toFixed(2);
    }
    
    console.log('✅ HTML des paniers généré avec succès -', paniers.length, 'articles');
}
  
  /**
   * Calcule le total avec frais de livraison
   */
  function calculerTotalAvecLivraison() {
      try {
          // Somme des sous-totaux présents dans le DOM + frais de livraison éventuels
          const totalElement = document.getElementById('total-commande');
          if (!totalElement) return;

          // Récupérer la somme des sous-totaux affichés des articles
          let totalArticlesCalcule = 0;
          document.querySelectorAll('.article-card .text-lg.font-bold').forEach(stEl => {
              const txt = (stEl.textContent || stEl.innerText || '').replace(' DH', '').replace(',', '.').trim();
              const val = parseFloat(txt);
              if (!isNaN(val) && isFinite(val)) {
                  totalArticlesCalcule += val;
              }
          });

          // Frais de livraison via data-attributes
          const inclureFrais = (totalElement.dataset.inclureFrais || 'false') === 'true';
          const fraisLivraison = parseFloat(totalElement.dataset.fraisLivraison || '0') || 0;
          const articlesCount = parseInt(totalElement.dataset.articlesCount || '0') || 0;

          // Règle: si plusieurs articles, on utilise toujours la logique DB d'inclusion frais
          const totalFinal = inclureFrais ? (totalArticlesCalcule + fraisLivraison) : totalArticlesCalcule;
          totalElement.textContent = totalFinal.toFixed(2) + ' DH';
          
      } catch (error) {
          console.error('❌ Erreur dans calculerTotalAvecLivraison:', error);
      }
  }

  
  /**
 * Initialise la modale de livraison partielle
 */
function initialiserModalLivraisonPartielle() {
    console.log('🔧 DEBUG: initialiserModalLivraisonPartielle appelée');

    // Initialiser la date de livraison avec la date d'aujourd'hui
    const dateLivraisonInput = document.getElementById('dateLivraisonPartielle');
    if (dateLivraisonInput) {
        const today = new Date();
        const formattedDate = today.toISOString().split('T')[0];
        dateLivraisonInput.value = formattedDate;
        dateLivraisonInput.max = formattedDate; // Empêcher de sélectionner une date future
        console.log('✅ Date de livraison initialisée à:', formattedDate);
    }

    // Réinitialiser tous les checkboxes à "coché" par défaut
    document.querySelectorAll('.article-livrer-checkbox').forEach(checkbox => {
        checkbox.checked = true;
    });

    // Réinitialiser toutes les quantités à la quantité maximale
    document.querySelectorAll('.quantite-livrer-input').forEach(input => {
        const maxQuantite = parseInt(input.dataset.panierId ?
            document.querySelector(`[data-panier-id="${input.dataset.panierId}"]`).dataset.quantiteMax :
            input.max);
        input.value = maxQuantite;
    });

    // Mettre à jour l'affichage initial
    mettreAJourSectionArticlesRenvoyes([]);
    mettreAJourResumeLivraisonPartielle();

    // Binder les événements (une seule fois)
    document.querySelectorAll('.article-livrer-checkbox').forEach(cb => {
        cb.removeEventListener('change', handleCheckboxChangeUnified);
        cb.addEventListener('change', handleCheckboxChangeUnified);
    });
    document.querySelectorAll('.quantite-livrer-input').forEach(inp => {
        inp.removeEventListener('input', mettreAJourResumeLivraisonPartielle);
        inp.addEventListener('input', mettreAJourResumeLivraisonPartielle);
        inp.removeEventListener('change', mettreAJourResumeLivraisonPartielle);
        inp.addEventListener('change', mettreAJourResumeLivraisonPartielle);
    });

    // Binder la soumission du formulaire une seule fois
    const livraisonPartielleForm = document.getElementById('livraisonPartielleForm');
    if (livraisonPartielleForm && !livraisonPartielleForm.dataset.bound) {
        livraisonPartielleForm.addEventListener('submit', submitLivraisonPartielleUnified);
        livraisonPartielleForm.dataset.bound = 'true';
    }
    
    console.log('✅ Modale de livraison partielle initialisée');
}

// ========== Logique unifiée de Livraison Partielle (réutilisable) ==========
function handleCheckboxChangeUnified() {
    const input = document.querySelector(`.quantite-livrer-input[data-panier-id="${this.dataset.panierId}"]`);
    if (input) {
        input.disabled = !this.checked;
        if (!this.checked) {
            const card = document.querySelector(`.article-livraison-card[data-panier-id="${this.dataset.panierId}"]`);
            const max = parseInt(card?.dataset.quantiteMax || input.max || '0');
            input.value = max;
        }
    }
    mettreAJourResumeLivraisonPartielle();
}

function mettreAJourResumeLivraisonPartielle() {
    const articlesLivres = [];
    const articlesRenvoyes = [];
    let totalLivres = 0;
    let totalRenvoyes = 0;
    let totalValeurLivree = 0;
    
    // Récupérer les informations sur les frais de livraison
    const totalCommandeElement = document.getElementById('totalCommandeLivraison');
    const fraisLivraison = parseFloat(totalCommandeElement?.dataset.fraisLivraison || '0') || 0;
    const inclureFrais = totalCommandeElement?.dataset.inclureFrais === 'true';

    const cards = document.querySelectorAll('.article-card');
    console.log(`🔧 DEBUG: Trouvé ${cards.length} cartes d'articles`);
    
    if (cards.length === 0) {
        console.error('❌ Aucune carte d\'article trouvée avec la classe .article-card');
        return;
    }
    
    cards.forEach(card => {
        const panierId = parseInt(card.dataset.panierId);
        
        // Récupérer les données directement depuis les attributs data-* du DOM
        const nom = card.dataset.articleNom || '';
        const articleId = parseInt(card.dataset.articleId) || 0;
        const varianteId = card.dataset.varianteId ? parseInt(card.dataset.varianteId) : null;
        const prixUnitaire = parseFloat(card.dataset.prixUnitaire) || 0;
        const prixActuel = parseFloat(card.dataset.prixActuel) || prixUnitaire;
        const quantiteMax = parseInt(card.dataset.quantiteMax) || 0;
        const isUpsell = card.dataset.isUpsell === 'true';
        const compteur = parseInt(card.dataset.compteur) || 0;
        
        console.log(`🔧 DEBUG: Panier ${panierId}, Article: ${nom}, Prix unitaire: ${prixUnitaire}, Prix actuel: ${prixActuel}`);
        
        const checkbox = card.querySelector('.article-livrer-checkbox');
        const input = card.querySelector('.quantite-livrer-input');
        const quantiteLivree = checkbox?.checked ? (parseInt(input?.value || '0') || 0) : 0;
        const quantiteRenvoyee = quantiteMax - quantiteLivree;
        
        console.log(`🔧 DEBUG: Article ${nom} - Checkbox cochée: ${checkbox?.checked}, Quantité: ${input?.value}, Quantité livrée: ${quantiteLivree}`);

        // NOUVELLE LOGIQUE: Un panier ne peut être que dans UNE seule liste
        // Si quantité livrée > 0, il va dans articlesLivres SEULEMENT
        // Le backend calculera automatiquement la quantité restante
        
        if (quantiteLivree > 0) {
            articlesLivres.push({ 
                panier_id: panierId, 
                article_id: articleId, 
                variante_id: varianteId, 
                quantite: quantiteLivree, 
                nom: nom, 
                prix_unitaire: prixUnitaire, 
                prix_actuel: prixActuel,
                is_upsell: isUpsell,
                compteur: compteur
            });
            totalLivres += quantiteLivree;
            totalValeurLivree += quantiteLivree * prixActuel;
            
            console.log(`✅ Panier ${panierId} ajouté à articlesLivres avec quantité ${quantiteLivree}`);
        } 
        // Si quantité livrée = 0, alors TOUT le panier est retourné
        else if (quantiteMax > 0) {
            articlesRenvoyes.push({ 
                panier_id: panierId, 
                article_id: articleId, 
                variante_id: varianteId, 
                quantite: quantiteMax, // Toute la quantité est retournée
                nom: nom, 
                prix_unitaire: prixUnitaire, 
                prix_actuel: prixActuel,
                is_upsell: isUpsell,
                compteur: compteur
            });
            totalRenvoyes += quantiteMax;
            
            console.log(`✅ Panier ${panierId} ajouté à articlesRenvoyes avec quantité ${quantiteMax} (entièrement retourné)`);
        }
    });

    const livresInput = document.getElementById('articlesLivresJsonInput');
    const renvoyesInput = document.getElementById('articlesRetournesJsonInput');
    
    console.log(`🔧 DEBUG: ${articlesLivres.length} articles à livrer, ${articlesRenvoyes.length} articles à retourner`);
    console.log('🔧 DEBUG: Articles livrés:', articlesLivres);
    console.log('🔧 DEBUG: Articles renvoyés:', articlesRenvoyes);
    
    if (livresInput) {
        livresInput.value = JSON.stringify(articlesLivres);
        console.log('🔧 DEBUG: Champ articlesLivresJsonInput rempli:', livresInput.value);
    } else {
        console.error('❌ Champ articlesLivresJsonInput non trouvé');
    }
    
    if (renvoyesInput) {
        renvoyesInput.value = JSON.stringify(articlesRenvoyes);
        console.log('🔧 DEBUG: Champ articlesRetournesJsonInput rempli:', renvoyesInput.value);
    } else {
        console.error('❌ Champ articlesRetournesJsonInput non trouvé');
    }

    const aucunDiv = document.getElementById('aucunArticleRenvoyer');
    if (aucunDiv) {
        if (totalRenvoyes > 0) aucunDiv.classList.add('hidden'); else aucunDiv.classList.remove('hidden');
    }

    // Calculer les valeurs avec frais de livraison si applicable
    const totalValeurLivreeAvecFrais = inclureFrais ? (totalValeurLivree + fraisLivraison) : totalValeurLivree;
    
    const totalLivresEl = document.getElementById('totalArticlesLivres');
    const totalRenvoyesEl = document.getElementById('totalArticlesRenvoyes');
    const totalValeurEl = document.getElementById('totalValeurLivree');
    if (totalLivresEl) totalLivresEl.textContent = totalLivres;
    if (totalRenvoyesEl) totalRenvoyesEl.textContent = totalRenvoyes;
    if (totalValeurEl) totalValeurEl.textContent = `${totalValeurLivreeAvecFrais.toFixed(2)} DH`;
    
    // Mettre à jour le pourcentage de livraison
    const totalCommandeOriginal = parseFloat(totalCommandeElement?.dataset.totalCommande || '0') || 0;
    const pourcentageLivraison = totalCommandeOriginal > 0 ? (totalValeurLivreeAvecFrais / totalCommandeOriginal * 100) : 0;
    
    const pourcentageEl = document.getElementById('pourcentageLivraison');
    const barreProgresEl = document.getElementById('barreProgresLivraison');
    if (pourcentageEl) pourcentageEl.textContent = `${pourcentageLivraison.toFixed(1)}%`;
    if (barreProgresEl) barreProgresEl.style.width = `${Math.min(pourcentageLivraison, 100)}%`;
    
    console.log(`🔧 DEBUG: Total valeur livrée: ${totalValeurLivree} DH${inclureFrais ? ` + Frais: ${fraisLivraison} DH = ${totalValeurLivreeAvecFrais} DH` : ''}`);
    console.log(`🔧 DEBUG: Pourcentage de livraison: ${pourcentageLivraison.toFixed(1)}%`);

    mettreAJourSectionArticlesRenvoyes(articlesRenvoyes);
}

function mettreAJourSectionArticlesRenvoyes(articlesRenvoyes = []) {
    const container = document.getElementById('articlesARenvoyerContainer');
    const aucunArticleDiv = document.getElementById('aucunArticleRenvoyer');
    if (!container) return;

    container.innerHTML = '';
    if (!articlesRenvoyes || articlesRenvoyes.length === 0) {
        if (aucunArticleDiv) aucunArticleDiv.classList.remove('hidden');
        return;
    }
    if (aucunArticleDiv) aucunArticleDiv.classList.add('hidden');

    articlesRenvoyes.forEach(article => {
        // Utiliser directement le prix actuel calculé
        const prixAff = parseFloat(article.prix_actuel) || parseFloat(article.prix_unitaire) || 0;
        const valeurTotale = (parseFloat(article.quantite || 0) * prixAff);
        
        console.log(`🔧 DEBUG Article retourné: ${article.nom}, prix_actuel: ${article.prix_actuel}, prix_unitaire: ${article.prix_unitaire}, prix utilisé: ${prixAff}`);
        
        const articleCard = document.createElement('div');
        articleCard.className = 'article-renvoi-card bg-white rounded-lg border border-orange-300 p-4';
        articleCard.dataset.articleId = article.article_id;
        articleCard.dataset.varianteId = article.variante_id || '';
        articleCard.dataset.panierId = article.panier_id;
        articleCard.innerHTML = `
            <div class="flex items-start space-x-3">
                <div class="flex-shrink-0">
                    <i class="fas fa-undo text-orange-600 text-lg mt-1"></i>
                </div>
                <div class="flex-1">
                    <div class="font-medium text-gray-900">
                        ${article.nom || ''}
                        ${article.is_upsell && article.compteur > 0 ? 
                            `<span class="inline-flex items-center px-1.5 py-0.5 rounded text-xs font-medium bg-orange-100 text-orange-700 ml-2">
                                <i class="fas fa-arrow-up mr-1"></i>Upsell Niv.${article.compteur}
                            </span>` : ''}
                    </div>
                    ${article.variante_id ? `<div class="text-xs text-gray-500 mt-1">Variante ID: ${article.variante_id}</div>` : ''}
                    <div class="text-sm text-gray-500 mt-2">
                        <div class="flex justify-between items-center mb-1">
                            <span>Quantité à retourner:</span>
                            <span class="font-semibold text-orange-600">${article.quantite || 0}</span>
                        </div>
                        <div class="flex justify-between items-center mb-1">
                            <span>Prix unitaire:</span>
                            <span class="font-medium text-gray-900">
                                ${prixAff.toFixed(2)} DH
                                ${article.is_upsell && article.compteur > 0 ? 
                                    `<small class="text-green-600 ml-1">(Prix upsell)</small>` : ''}
                                ${prixAff === 0 ? 
                                    `<small class="text-red-600 ml-1">⚠️ ERREUR: Prix = 0</small>` : ''}
                            </span>
                        </div>
                        <div class="flex justify-between items-center pt-1 border-t border-orange-200">
                            <span class="font-medium">Valeur totale retournée:</span>
                            <span class="font-bold text-orange-700 text-lg">${valeurTotale.toFixed(2)} DH</span>
                        </div>
                    </div>
                    <div class="mt-2 text-xs text-orange-600 bg-orange-100 px-2 py-1 rounded-md">
                        <i class="fas fa-info-circle mr-1"></i>
                        Article retourné aux opérateurs de préparation
                        ${article.is_upsell && article.compteur > 0 ?
                            ` • ${article.compteur >= 4 ? 'Prix Gros' : `Prix upsell ${article.compteur + 1}`} appliqué` : ''}
                    </div>
                </div>
            </div>`;
        container.appendChild(articleCard);
    });
}

function submitLivraisonPartielleUnified(e) {
    e.preventDefault();
    
    // S'assurer que les JSON sont à jour
    mettreAJourResumeLivraisonPartielle();
    
    // Vérifier qu'il y a au moins un article à livrer
    const articlesLivresInput = document.getElementById('articlesLivresJsonInput');
    const articlesRenvoyesInput = document.getElementById('articlesRetournesJsonInput');
    
    if (!articlesLivresInput || !articlesRenvoyesInput) {
        alert('❌ Erreur: Champs de données manquants');
        return;
    }
    
    let articlesLivres = [];
    let articlesRenvoyes = [];
    
    try {
        articlesLivres = JSON.parse(articlesLivresInput.value || '[]');
        articlesRenvoyes = JSON.parse(articlesRenvoyesInput.value || '[]');
    } catch (error) {
        console.error('❌ Erreur de parsing JSON:', error);
        alert('❌ Erreur: Données invalides');
        return;
    }
    
    console.log(`🔧 DEBUG: Articles à livrer: ${articlesLivres.length}, Articles à retourner: ${articlesRenvoyes.length}`);
    console.log('🔧 DEBUG: Articles livrés:', articlesLivres);
    console.log('🔧 DEBUG: Articles renvoyés:', articlesRenvoyes);
    
    if (articlesLivres.length === 0) {
        alert('❌ Erreur: Aucun article à livrer spécifié. Veuillez sélectionner au moins un article.');
        return;
    }
    
    const form = e.currentTarget;
    const submitBtn = document.getElementById('confirmerLivraisonPartielleBtn');
    if (submitBtn) {
        submitBtn.disabled = true;
        submitBtn.innerHTML = '<i class="fas fa-spinner fa-spin mr-2"></i>Traitement...';
    }
    
    const formData = new FormData(form);
    fetch(form.action, { method: 'POST', body: formData })
        .then(r => r.json())
        .then(data => {
            if (data.success) {
                // Affichage simple, laisser la page gérer la confirmation/modale existante si présente
                console.log('✅ Livraison partielle OK');
                location.reload();
            } else {
                alert('❌ Erreur: ' + (data.error || 'Inconnue'));
                if (submitBtn) { submitBtn.disabled = false; submitBtn.innerHTML = '<i class="fas fa-check mr-2"></i>Confirmer la Livraison Partielle'; }
            }
        })
        .catch(err => {
            console.error(err);
            alert('❌ Erreur réseau');
            if (submitBtn) { submitBtn.disabled = false; submitBtn.innerHTML = '<i class="fas fa-check mr-2"></i>Confirmer la Livraison Partielle'; }
        });
}

// Exposer les fonctions (si besoin sur d'autres pages)
window.ouvrirModalLivraisonPartielle = ouvrirModalLivraisonPartielle;
window.fermerModalLivraisonPartielle = fermerModalLivraisonPartielle;
window.initialiserModalLivraisonPartielle = initialiserModalLivraisonPartielle;
window.ouvrirModalRetourComplet = ouvrirModalRetourComplet;
window.fermerModalRetourComplet = fermerModalRetourComplet;
window.soumettreRetourComplet = soumettreRetourComplet;

// Gestion des événements clavier pour fermer les modales avec Échap
document.addEventListener('keydown', function(event) {
    if (event.key === 'Escape') {
        // Fermer la modale SAV si elle est ouverte
        const savModal = document.getElementById('savModal');
        if (savModal && !savModal.classList.contains('hidden')) {
            fermerModalSav();
        }
        
        // Fermer la modale de livraison partielle si elle est ouverte
        const livraisonModal = document.getElementById('livraisonPartielleModal');
        if (livraisonModal && !livraisonModal.classList.contains('hidden')) {
            fermerModalLivraisonPartielle();
        }
        
        // Fermer la modale de renvoi si elle est ouverte
        const renvoyerModal = document.getElementById('renvoyerModal');
        if (renvoyerModal && !renvoyerModal.classList.contains('hidden')) {
            closeRenvoyerModal();
        }
        
        // Fermer la modale SAV défectueux si elle est ouverte
        const savDefectueuxModal = document.getElementById('savDefectueuxModal');
        if (savDefectueuxModal && !savDefectueuxModal.classList.contains('hidden')) {
            fermerModalSavDefectueux();
        }
        
        // Fermer la modale de valeur totale si elle est ouverte
        const valeurTotaleModal = document.getElementById('valeurTotaleModal');
        if (valeurTotaleModal && !valeurTotaleModal.classList.contains('hidden')) {
            fermerModalValeurTotale();
        }
        
        // Fermer la modale de frais de livraison si elle est ouverte
        const fraisLivraisonModal = document.getElementById('fraisLivraisonModal');
        if (fraisLivraisonModal && !fraisLivraisonModal.classList.contains('hidden')) {
            fermerModalFraisLivraison();
        }
        
        // Fermer la modale de calculs si elle est ouverte
        const calculsModal = document.getElementById('calculsModal');
        if (calculsModal && !calculsModal.classList.contains('hidden')) {
            fermerModalCalculs();
        }
        
        // Fermer la modale d'actions SAV si elle est ouverte
        const savActionsModal = document.getElementById('savActionsModal');
        if (savActionsModal && !savActionsModal.classList.contains('hidden')) {
            fermerModalActionsSav();
        }

        // Fermer la modale de retour complet si elle est ouverte
        const retourCompletModal = document.getElementById('retourCompletModal');
        if (retourCompletModal && !retourCompletModal.classList.contains('hidden')) {
            fermerModalRetourComplet();
        }
    }
});

// Gestion des clics en dehors des modales pour les fermer
document.addEventListener('click', function(event) {
    // Modale SAV
    const savModal = document.getElementById('savModal');
    if (savModal && !savModal.classList.contains('hidden')) {
        if (event.target === savModal) {
            fermerModalSav();
        }
    }
    
    // Modale de livraison partielle
    const livraisonModal = document.getElementById('livraisonPartielleModal');
    if (livraisonModal && !livraisonModal.classList.contains('hidden')) {
        if (event.target === livraisonModal) {
            fermerModalLivraisonPartielle();
        }
    }
    
    // Modale de renvoi
    const renvoyerModal = document.getElementById('renvoyerModal');
    if (renvoyerModal && !renvoyerModal.classList.contains('hidden')) {
        if (event.target === renvoyerModal) {
            closeRenvoyerModal();
        }
    }
    
    // Modale SAV défectueux
    const savDefectueuxModal = document.getElementById('savDefectueuxModal');
    if (savDefectueuxModal && !savDefectueuxModal.classList.contains('hidden')) {
        if (event.target === savDefectueuxModal) {
            fermerModalSavDefectueux();
        }
    }
    
    // Modale de valeur totale
    const valeurTotaleModal = document.getElementById('valeurTotaleModal');
    if (valeurTotaleModal && !valeurTotaleModal.classList.contains('hidden')) {
        if (event.target === valeurTotaleModal) {
            fermerModalValeurTotale();
        }
    }
    
    // Modale de frais de livraison
    const fraisLivraisonModal = document.getElementById('fraisLivraisonModal');
    if (fraisLivraisonModal && !fraisLivraisonModal.classList.contains('hidden')) {
        if (event.target === fraisLivraisonModal) {
            fermerModalFraisLivraison();
        }
    }
    
    // Modale de calculs
    const calculsModal = document.getElementById('calculsModal');
    if (calculsModal && !calculsModal.classList.contains('hidden')) {
        if (event.target === calculsModal) {
            fermerModalCalculs();
        }
    }
    
    // Modale d'actions SAV
    const savActionsModal = document.getElementById('savActionsModal');
    if (savActionsModal && !savActionsModal.classList.contains('hidden')) {
        if (event.target === savActionsModal) {
            fermerModalActionsSav();
        }
    }

    // Modale de retour complet
    const retourCompletModal = document.getElementById('retourCompletModal');
    if (retourCompletModal && !retourCompletModal.classList.contains('hidden')) {
        if (event.target === retourCompletModal) {
            fermerModalRetourComplet();
        }
    }
});
