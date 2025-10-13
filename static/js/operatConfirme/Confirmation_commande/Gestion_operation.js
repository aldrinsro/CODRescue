// Fonction pour charger automatiquement la région, les frais et les délais
function chargerRegionEtFrais() {
    const villeSelect = document.getElementById('ville-select');
    const selectedOption = villeSelect.options[villeSelect.selectedIndex];
    
    if (selectedOption.value) {
        const region = selectedOption.getAttribute('data-region');
        const frais = selectedOption.getAttribute('data-frais');
        const delaiMin = selectedOption.getAttribute('data-delai-min');
        const delaiMax = selectedOption.getAttribute('data-delai-max');
        
        document.getElementById('region-display').value = region;
        document.getElementById('frais-display').value = frais + ' DH';
        document.getElementById('delai-display').value = delaiMin + ' - ' + delaiMax + ' jours';
        
        // Mettre à jour l'affichage des frais et recalculer le total
        mettreAJourAffichageFraisResume();
        mettreAJourTotalCommande();
        
        console.log(`🏙️ Ville changée: ${selectedOption.text}, Frais: ${frais} DH, Région: ${region}, Délai: ${delaiMin}-${delaiMax} jours`);
    } else {
        // Réinitialiser les champs si aucune ville n'est sélectionnée
        document.getElementById('region-display').value = '';
        document.getElementById('frais-display').value = '';
        document.getElementById('delai-display').value = '';
        
        // Mettre à jour l'affichage des frais et recalculer le total
        mettreAJourAffichageFraisResume();
        mettreAJourTotalCommande();
    }
}

// Fonction pour vérifier une section
function verifierSection(section) {
    const sectionElement = document.querySelector(`[onclick="verifierSection('${section}')"]`).closest('.verification-item');
    sectionElement.classList.add('verified');
}

// Fonction pour vérifier toutes les sections
function verifierTout() {
    const sections = document.querySelectorAll('.verification-item');
    sections.forEach(section => {
        section.classList.add('verified');
    });
}

// Variables globales pour la modale
let currentOperationType = '';
let currentOperationName = '';

// Fonction pour ouvrir la modale de commentaire
function openCommentModal(operationType, operationName) {
    console.log('Ouverture modale pour:', operationType, operationName);
    
    try {
        currentOperationType = operationType;
        currentOperationName = operationName;
        
        // Vérifier que la modale existe
        const modal = document.getElementById('commentModal');
        if (!modal) {
            console.error('Modale commentModal introuvable !');
            alert('Erreur : Modale de commentaire introuvable');
            return;
        }
        
        // Mettre à jour le titre de la modale
        const operationNameElement = document.getElementById('operationName');
        if (operationNameElement) {
            operationNameElement.textContent = operationName;
        }
        
        // Remplir la liste déroulante selon le type d'opération
        remplirListeCommentaires(operationType);
        
        // Charger le commentaire existant s'il y en a un
        const commentField = document.getElementById('comment_' + operationType);
        const select = document.getElementById('commentSelect');
        
        if (commentField && select) {
            select.value = commentField.value || '';
        }
        
        // Afficher la modale avec animation
        modal.style.display = 'flex';
        modal.classList.remove('hidden');
        modal.classList.add('flex');
        
        // Force le navigateur à reconnaître les changements
        modal.offsetHeight;
        
        console.log('Modale affichée avec succès');
        
        // Focus sur le select après un délai court
        setTimeout(() => {
            if (select) {
                select.focus();
            }
        }, 150);
        
    } catch (error) {
        console.error('Erreur lors de l\'ouverture de la modale:', error);
        alert('Erreur lors de l\'ouverture de la modale: ' + error.message);
    }
}

// Fonction pour fermer la modale
function closeCommentModal() {
    try {
        const modal = document.getElementById('commentModal');
        if (modal) {
            modal.style.display = 'none';
            modal.classList.add('hidden');
            modal.classList.remove('flex');
        }
        currentOperationType = '';
        currentOperationName = '';
        console.log('Modale fermée');
    } catch (error) {
        console.error('Erreur lors de la fermeture de la modale:', error);
    }
}

// Fonction pour sauvegarder le commentaire
function saveComment() {
    const select = document.getElementById('commentSelect');
    const commentText = (select ? select.value : '').trim();
    
    if (commentText) {
        // Sauvegarder dans le champ hidden
        document.getElementById('comment_' + currentOperationType).value = commentText;
        
        // Mettre à jour l'aperçu
        const previewElement = document.getElementById('preview_' + currentOperationType);
        previewElement.textContent = 'Commentaire: ' + (commentText.length > 50 ? commentText.substring(0, 50) + '...' : commentText);
        previewElement.classList.remove('hidden');
        
        // Cocher automatiquement l'opération si ce n'est pas déjà fait
        document.getElementById('op_' + currentOperationType).checked = true;
    } else {
        // Supprimer le commentaire et l'aperçu
        document.getElementById('comment_' + currentOperationType).value = '';
        document.getElementById('preview_' + currentOperationType).classList.add('hidden');
    }
    
    closeCommentModal();
}

// Variables globales pour le système de tableau
let operationCounter = 1;
let operationsTable = [];

// Variables globales pour le système en deux étapes
let typePrincipalSelectionne = '';

// Fonction pour ajouter une nouvelle opération dans le tableau
function ajouterNouvelleOperation() {
    // Afficher le sélecteur de type principal (Étape 1)
    document.getElementById('type-principal-selector').classList.remove('hidden');
}

// Fonction pour choisir le type principal d'opération (Étape 1)
function choisirTypePrincipal(typePrincipal) {
    typePrincipalSelectionne = typePrincipal;
    
    // Cacher le sélecteur de type principal
    document.getElementById('type-principal-selector').classList.add('hidden');
    
    // Pour WhatsApp, afficher les sous-options
    if (typePrincipal === 'WHATSAPP') {
        // Afficher les opérations spécifiques selon le type choisi
        afficherOperationsSpecifiques(typePrincipal);
        
        // Afficher le sélecteur d'opération (Étape 2)
        document.getElementById('operation-selector').classList.remove('hidden');
    } else {
        // Pour APPEL et SMS, aller directement à la sélection
        console.log(`⚡ Sélection directe pour ${typePrincipal} (pas de sous-menu)`);
        
        if (typePrincipal === 'APPEL') {
            selectionnerTypeOperation('APPEL', 'Appel', 'bg-blue-100 text-blue-800');
        } else if (typePrincipal === 'SMS') {
            selectionnerTypeOperation('ENVOI_SMS', 'Envoi de SMS', 'bg-green-100 text-green-800');
        }
    }
}

// Fonction pour afficher les opérations spécifiques selon le type (uniquement pour WhatsApp)
function afficherOperationsSpecifiques(typePrincipal) {
    const operationsList = document.getElementById('operations-list');
    let operationsHTML = '';
    
    // Cette fonction ne gère maintenant que WhatsApp
    if (typePrincipal === 'WHATSAPP') {
        operationsHTML = `
            <button type="button" onclick="selectionnerTypeOperation('Appel Whatsapp', 'Appel WhatsApp', 'bg-emerald-100 text-emerald-800')" 
                    class="p-2 text-xs rounded-lg border hover:bg-gray-50 transition-colors">
                <span class="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-emerald-100 text-emerald-800">
                    <i class="fab fa-whatsapp mr-1"></i>Appel WhatsApp
                </span>
            </button>
            <button type="button" onclick="selectionnerTypeOperation('Message Whatsapp', 'Message WhatsApp', 'bg-emerald-200 text-emerald-900')" 
                    class="p-2 text-xs rounded-lg border hover:bg-gray-50 transition-colors">
                <span class="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-emerald-200 text-emerald-900">
                    <i class="fas fa-message mr-1"></i>Message WhatsApp
                </span>
            </button>
            <button type="button" onclick="selectionnerTypeOperation('Vocal Whatsapp', 'Vocal WhatsApp', 'bg-teal-100 text-teal-800')" 
                    class="p-2 text-xs rounded-lg border hover:bg-gray-50 transition-colors">
                <span class="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-teal-100 text-teal-800">
                    <i class="fas fa-microphone mr-1"></i>Vocal WhatsApp
                </span>
            </button>
        `;
    } else {
        console.warn(`⚠️ afficherOperationsSpecifiques() appelée pour un type non-WhatsApp: ${typePrincipal}`);
    }
    
    operationsList.innerHTML = operationsHTML;
}

// Fonction pour retourner au choix du type principal
function retourTypePrincipal() {
    // Cacher le sélecteur d'opération
    document.getElementById('operation-selector').classList.add('hidden');
    
    // Afficher à nouveau le sélecteur de type principal
    document.getElementById('type-principal-selector').classList.remove('hidden');
    
    // Réinitialiser la sélection
    typePrincipalSelectionne = '';
}

// Fonction pour annuler la sélection d'opération
function annulerSelectionOperation() {
    // Cacher tous les sélecteurs
    document.getElementById('type-principal-selector').classList.add('hidden');
    document.getElementById('operation-selector').classList.add('hidden');
    
    // Réinitialiser la sélection
    typePrincipalSelectionne = '';
}

// Fonction pour sélectionner un type d'opération
function selectionnerTypeOperation(typeOperation, nomOperation, classeCouleur) {
    // Cacher tous les sélecteurs
    document.getElementById('type-principal-selector').classList.add('hidden');
    document.getElementById('operation-selector').classList.add('hidden');
    
    // Générer un ID unique pour les nouvelles opérations
    const operationId = 'NEW-' + operationCounter.toString().padStart(3, '0');
    operationCounter++;
    
    // Date/heure actuelle
    const maintenant = new Date();
    const dateOperation = maintenant.toLocaleDateString('fr-FR') + ' ' + 
                         maintenant.toLocaleTimeString('fr-FR', {hour: '2-digit', minute: '2-digit'});
    
    // Ajouter le type principal au nom pour plus de clarté
    const nomComplet = `${typePrincipalSelectionne} - ${nomOperation}`;
    
    // Créer l'objet opération
    const nouvelleOperation = {
        id: operationId,
        type: typeOperation,
        nom: nomComplet,
        classe: classeCouleur,
        date: dateOperation,
        commentaire: '',
        typePrincipal: typePrincipalSelectionne
    };
    
    // Ajouter à la liste
    operationsTable.push(nouvelleOperation);
    
    // Mettre à jour l'affichage du tableau
    mettreAJourTableauOperations();
    
    // Réinitialiser la sélection
    typePrincipalSelectionne = '';
    
    console.log(`✅ Opération ajoutée: ${typeOperation} (${nomComplet})`);
    console.log('🗃️ Types d\'opérations valides en base:', ['APPEL', 'Appel Whatsapp', 'Message Whatsapp', 'Vocal Whatsapp', 'ENVOI_SMS']);
    
    // Ouvrir immédiatement la modale de commentaire
    setTimeout(() => {
        ouvrirModaleCommentaireTableau(operationId, nomComplet);
    }, 100);
}

// Fonction pour mettre à jour l'affichage du tableau
function mettreAJourTableauOperations() {
    const tbody = document.getElementById('operations-table-body');
    
    if (operationsTable.length === 0) {
        tbody.innerHTML = `
            <tr>
                <td colspan="4" class="px-4 py-8 text-center text-gray-500">
                    <i class="fas fa-inbox text-2xl mb-2"></i>
                    <div>Aucune opération ajoutée</div>
                    <div class="text-xs">Cliquez sur "Ajouter une opération" pour commencer</div>
                </td>
            </tr>
        `;
        return;
    }
    
    tbody.innerHTML = operationsTable.map(operation => {
        // Déterminer l'icône selon le type principal
        let iconeType = 'fas fa-cogs';
        let couleurType = 'text-gray-600';
        
        if (operation.typePrincipal === 'APPEL') {
            iconeType = 'fas fa-phone';
            couleurType = 'text-blue-600';
        } else if (operation.typePrincipal === 'SMS') {
            iconeType = 'fas fa-sms';
            couleurType = 'text-green-600';
        } else if (operation.typePrincipal === 'WHATSAPP') {
            iconeType = 'fab fa-whatsapp';
            couleurType = 'text-emerald-600';
        }
        
        return `
        <tr class="hover:bg-gray-50 transition-colors">
            <td class="px-4 py-3 text-sm font-medium text-gray-900">
                <span class="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-blue-100 text-blue-800">
                    <i class="fas fa-hashtag mr-1" style="font-size: 8px;"></i>${operation.id}
                </span>
            </td>
            <td class="px-4 py-3 text-sm">
                <div class="flex items-center space-x-2">
                    <i class="${iconeType} ${couleurType}" title="${operation.typePrincipal || 'Type non défini'}"></i>
                    <span class="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium ${operation.classe}">
                        ${operation.nom}
                    </span>
                </div>
            </td>
            <td class="px-4 py-3 text-sm text-gray-600">
                <i class="fas fa-clock mr-1"></i>${operation.date}
            </td>
            <td class="px-4 py-3 text-sm">
                                <div class="flex items-center justify-center">
                        <button type="button" onclick="ouvrirModaleCommentaireTableau('${operation.id}', '${operation.nom}')" 
                                class="px-3 py-2 bg-blue-500 hover:bg-blue-600 text-white text-sm rounded-lg transition-colors flex items-center">
                            <i class="fas fa-edit mr-1"></i>
                            Modifier
                        </button>
                </div>
                ${operation.commentaire ? `
                    <div class="mt-1 text-xs text-gray-600 italic flex items-center">
                        <i class="fas fa-check-circle text-green-500 mr-1"></i>
                        "${operation.commentaire.length > 50 ? operation.commentaire.substring(0, 50) + '...' : operation.commentaire}"
                    </div>
                ` : '<div class="mt-1 text-xs text-red-500 flex items-center"><i class="fas fa-exclamation-circle mr-1"></i>Commentaire requis</div>'}
            </td>
        </tr>
        `;
    }).join('');
}

// Fonction pour ouvrir la modale de commentaire spécifique au tableau
function ouvrirModaleCommentaireTableau(operationId, nomOperation) {
    currentOperationType = operationId; // Réutiliser la variable globale
    currentOperationName = nomOperation;
    
    // Trouver l'opération dans le tableau
    const operation = operationsTable.find(op => op.id === operationId);
    
    // Mettre à jour le titre de la modale
    document.getElementById('operationName').textContent = nomOperation + ' (' + operationId + ')';
    
    // Remplir la liste déroulante selon le type d'opération
    if (operation) {
        remplirListeCommentaires(operation.type);
    }
    
    // Charger le commentaire existant
    const select = document.getElementById('commentSelect');
    select.value = operation ? operation.commentaire : '';
    
    // Afficher la modale
    const modal = document.getElementById('commentModal');
    if (modal) {
        modal.style.display = 'flex';
        modal.classList.remove('hidden');
        modal.classList.add('flex');
    } else {
        console.error('❌ Modale commentModal introuvable lors de l\'affichage');
    }
    
    // Focus sur le select
    setTimeout(() => {
        select.focus();
    }, 150);
}

// Fonction pour sauvegarder le commentaire (modifiée pour le tableau)
function saveComment() {
    const commentText = document.getElementById('commentSelect').value.trim();
    
    if (!commentText) {
        alert('Vous devez sélectionner une conclusion pour enregistrer l\'opération !');
        return;
    }
    
    console.log(`💾 DEBUG: Sauvegarde du commentaire: "${commentText}" pour ${currentOperationType}`);
    
    // Trouver et mettre à jour l'opération dans le tableau
    const operation = operationsTable.find(op => op.id === currentOperationType);
    if (operation) {
        const ancienCommentaire = operation.commentaire;
        operation.commentaire = commentText;
        
        console.log(`🔍 DEBUG: Opération trouvée: ${operation.id}, fromDatabase: ${operation.fromDatabase}`);
        console.log(`📝 DEBUG: Commentaire ancien: "${ancienCommentaire}" → nouveau: "${commentText}"`);
        
        // NOUVEAU: Sauvegarder TOUTES les opérations immédiatement en base de données
        if (operation.fromDatabase) {
            // Opération existante : utiliser update_operation
            console.log(`🔄 DEBUG: Sauvegarde d'une opération existante (DB)`);
            sauvegarderOperationExistante(operation, commentText);
        } else {
            // Nouvelle opération : créer en base de données immédiatement
            console.log(`🆕 DEBUG: Sauvegarde d'une nouvelle opération`);
            sauvegarderNouvelleOperation(operation, commentText);
        }
        
        // Mettre à jour l'affichage
        mettreAJourTableauOperations();
    }
    
    closeCommentModal();
}
// Fonction pour sauvegarder immédiatement une opération existante en base de données
function sauvegarderOperationExistante(operation, nouveauCommentaire) {
    console.log(`🔄 DEBUG: Sauvegarde immédiate de l'opération ${operation.id} en base de données...`);
    console.log(`📝 DEBUG: Nouveau commentaire à sauvegarder: "${nouveauCommentaire}"`);
    
    // Extraire l'ID numérique de l'opération (ex: "DB-51" -> "51")
    const operationDbId = operation.id.replace('DB-', '');
    console.log(`🔢 DEBUG: ID numérique extrait: ${operationDbId}`);
    
    const formData = new FormData();
    
    // Ajouter le token CSRF
    const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]');
    if (csrfToken) {
        formData.append('csrfmiddlewaretoken', csrfToken.value);
        console.log(`🔐 DEBUG: Token CSRF ajouté: ${csrfToken.value.substring(0, 10)}...`);
    } else {
        console.error('❌ DEBUG: Token CSRF introuvable !');
    }
    
    // Ajouter l'action spécifique pour modifier une opération existante
    formData.append('action', 'update_operation');
    formData.append('operation_id', operationDbId);
    formData.append('nouveau_commentaire', nouveauCommentaire);
    formData.append('commande_id', '{{ commande.id }}');
    
    // Debug des données envoyées
    console.log('📦 DEBUG: Données envoyées au serveur:');
    for (let [key, value] of formData.entries()) {
        console.log(`   - ${key}: ${value}`);
    }
    
    // Envoyer via AJAX
    fetch('{% url "operatConfirme:modifier_commande" commande.id %}', {
        method: 'POST',
        body: formData,
        headers: {
            'X-Requested-With': 'XMLHttpRequest',
        }
    })
    .then(response => {
        console.log(`🌐 DEBUG: Réponse reçue, status: ${response.status}`);
        return response.json();
    })
    .then(data => {
        console.log('📬 DEBUG: Données de réponse:', data);
        
        if (data.success) {
            console.log('✅ DEBUG: Opération mise à jour en base de données avec succès');
            console.log(`📋 DEBUG: Ancien commentaire: "${data.ancien_commentaire}"`);
            console.log(`📝 DEBUG: Nouveau commentaire: "${data.nouveau_commentaire}"`);
            
            if (data.debug_info) {
                console.log(`🔍 DEBUG: Vérification en base: "${data.debug_info.verification_conclusion}"`);
                console.log(`📊 DEBUG: Total opérations: ${data.debug_info.total_operations}`);
            }
            
            showNotification(`✅ Opération "${operation.nom}" mise à jour en base de données`, 'success');
            
            // Recharger les opérations depuis la base de données pour refléter les changements
            rechargerOperationsDepuisBase();
            } else {
            console.error('❌ DEBUG: Erreur lors de la mise à jour:', data.error);
            showNotification('❌ Erreur lors de la sauvegarde: ' + data.error, 'error');
        }
    })
    .catch(error => {
        console.error('❌ DEBUG: Erreur de connexion:', error);
        showNotification('❌ Erreur de connexion lors de la sauvegarde', 'error');
    });
}

// Fonction pour sauvegarder immédiatement une nouvelle opération en base de données
function sauvegarderNouvelleOperation(operation, commentaire) {
    console.log(`🆕 DEBUG: Création immédiate d'une nouvelle opération en base de données...`);
    console.log(`📝 DEBUG: Type: ${operation.type}, Commentaire: "${commentaire}"`);
    
    const formData = new FormData();
    
    // Ajouter le token CSRF
    const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]');
    if (csrfToken) {
        formData.append('csrfmiddlewaretoken', csrfToken.value);
        console.log(`🔐 DEBUG: Token CSRF ajouté`);
    } else {
        console.error('❌ DEBUG: Token CSRF introuvable !');
    }
    
    // Ajouter l'action pour créer une nouvelle opération
    formData.append('action', 'create_operation');
    formData.append('type_operation', operation.type);
    formData.append('commentaire', commentaire);
    formData.append('commande_id', '{{ commande.id }}');
    
    // Debug des données envoyées
    console.log('📦 DEBUG: Données envoyées pour création opération:');
    for (let [key, value] of formData.entries()) {
        console.log(`   - ${key}: ${value}`);
    }
    
    // Envoyer via AJAX
    fetch('{% url "operatConfirme:modifier_commande" commande.id %}', {
        method: 'POST',
        body: formData,
        headers: {
            'X-Requested-With': 'XMLHttpRequest',
        }
    })
    .then(response => {
        console.log(`🌐 DEBUG: Réponse création reçue, status: ${response.status}`);
        return response.json();
    })
    .then(data => {
        console.log('📬 DEBUG: Données de réponse création:', data);
        
        if (data.success) {
            console.log('✅ DEBUG: Nouvelle opération créée en base de données avec succès');
            console.log(`🔢 DEBUG: Nouvel ID en base: ${data.operation_id}`);
            
            // Transformer l'opération locale en opération de base de données
            operation.id = `DB-${data.operation_id}`;
            operation.fromDatabase = true;
            
            console.log(`🔄 DEBUG: Opération transformée: ${operation.id} (fromDatabase: true)`);
            
            showNotification(`✅ Opération "${operation.nom}" créée et sauvegardée en base de données`, 'success');
            
            // Recharger les opérations depuis la base de données pour refléter les changements
            rechargerOperationsDepuisBase();
        } else {
            console.error('❌ DEBUG: Erreur lors de la création:', data.error);
            showNotification('❌ Erreur lors de la création: ' + data.error, 'error');
        }
    })
    .catch(error => {
        console.error('❌ DEBUG: Erreur de connexion lors de la création:', error);
        showNotification('❌ Erreur de connexion lors de la création', 'error');
    });
}

// Types d'opérations valides selon la base de données
const TYPES_OPERATIONS_VALIDES = ['APPEL', 'Appel Whatsapp', 'Message Whatsapp', 'Vocal Whatsapp', 'ENVOI_SMS'];

// Variable globale pour stocker les commentaires chargés depuis l'API
let COMMENTAIRES_PREDEFINIES = {};

// Charger les commentaires depuis l'API Django au démarrage
function chargerCommentairesDisponibles() {
    console.log('🔄 Chargement des commentaires depuis l\'API Django...');
    
    fetch('{% url "operatConfirme:api_commentaires_disponibles" %}')
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                COMMENTAIRES_PREDEFINIES = data.commentaires;
                console.log('✅ Commentaires chargés depuis la base de données:', COMMENTAIRES_PREDEFINIES);
                
                // Afficher le nombre de commentaires par type d'opération
                Object.keys(COMMENTAIRES_PREDEFINIES).forEach(type => {
                    console.log(`📝 ${type}: ${COMMENTAIRES_PREDEFINIES[type].length} commentaires disponibles`);
                });
            } else {
                console.error('❌ Erreur lors du chargement des commentaires:', data.error);
                // Utiliser un fallback en cas d'erreur
                utiliserCommentairesFallback();
            }
        })
        .catch(error => {
            console.error('❌ Erreur de connexion à l\'API commentaires:', error);
            // Utiliser un fallback en cas d'erreur
            utiliserCommentairesFallback();
        });
}

// Fonction de fallback en cas d'erreur de chargement des commentaires
function utiliserCommentairesFallback() {
    console.warn('⚠️ Utilisation des commentaires de fallback');
    COMMENTAIRES_PREDEFINIES = {
        'APPEL': [
            { value: 'Client contacté avec succès', label: 'Client contacté avec succès' }
        ],
        'ENVOI_SMS': [
            { value: 'SMS envoyé avec succès', label: 'SMS envoyé avec succès' }
        ],
        'Appel Whatsapp': [
            { value: 'Appel WhatsApp réussi', label: 'Appel WhatsApp réussi' }
        ],
        'Message Whatsapp': [
            { value: 'Message WhatsApp envoyé', label: 'Message WhatsApp envoyé' }
        ],
        'Vocal Whatsapp': [
            { value: 'Message vocal envoyé', label: 'Message vocal envoyé' }
        ]
    };
}

// Fonction pour recharger les opérations depuis la base de données via AJAX
function rechargerOperationsDepuisBase() {
    console.log('🔄 DEBUG: Rechargement des opérations depuis la base de données...');
    console.log(`📊 DEBUG: État actuel du tableau: ${operationsTable.length} opération(s)`);
    
    // Faire une requête AJAX pour récupérer les opérations mises à jour
    fetch(`{% url 'operatConfirme:api_operations_commande' commande.id %}`, {
        method: 'GET',
        headers: {
            'X-Requested-With': 'XMLHttpRequest',
            'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]')?.value || '',
        },
        credentials: 'same-origin'
    })
    .then(response => {
        console.log(`🌐 DEBUG: Réponse API reçue, status: ${response.status}`);
        if (!response.ok) {
            throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        }
        return response.json();
    })
    .then(data => {
        console.log('📬 DEBUG: Données API reçues:', data);
        
        if (data.success) {
            console.log(`🔄 DEBUG: ${data.operations.length} opération(s) rechargée(s) depuis la base`);
            
            // Séparer les nouvelles opérations des existantes (celles qui ne sont pas encore en base)
            const nouvellesOperations = operationsTable.filter(op => !op.fromDatabase);
            console.log(`📝 DEBUG: ${nouvellesOperations.length} nouvelle(s) opération(s) locale(s) conservée(s)`);
            
            // Remplacer les opérations existantes par les données fraîches de la base
            const operationsFromDatabase = data.operations.map(op => {
                console.log(`🔍 DEBUG: Opération de la base DB-${op.id}: "${op.conclusion}"`);
                return {
                    id: `DB-${op.id}`,
                    type: op.type_operation,
                    nom: op.nom_display,
                    classe: op.classe_css,
                    date: op.date_operation,
                    commentaire: op.conclusion,
                    typePrincipal: op.type_principal,
                    fromDatabase: true
                };
            });
            
            // Debug avant recombination
            console.log('📋 DEBUG: Comparaison avant/après recombination:');
            console.log('   - Ancien tableau operationsTable:', operationsTable);
            console.log('   - Nouvelles opérations de la base:', operationsFromDatabase);
            console.log('   - Nouvelles opérations locales conservées:', nouvellesOperations);
            
            // Recombiner : opérations de base + nouvelles opérations
            operationsTable = [...operationsFromDatabase, ...nouvellesOperations];
            
            console.log(`📊 DEBUG: Tableau final: ${operationsTable.length} opération(s) total`);
            console.log('   - Depuis la base:', operationsFromDatabase.length);
            console.log('   - Nouvelles locales:', nouvellesOperations.length);
            console.log('📋 DEBUG: Nouveau tableau operationsTable:', operationsTable);
            
            // Mettre à jour l'affichage
            mettreAJourTableauOperations();
            
            console.log('✅ DEBUG: Tableau des opérations mis à jour avec les données fraîches de la base');
            showNotification('🔄 Tableau rechargé depuis la base de données', 'info');
        } else {
            console.error('❌ DEBUG: Erreur lors du rechargement:', data.error);
            showNotification('❌ Erreur lors du rechargement: ' + (data.error || 'Erreur inconnue'), 'error');
        }
    })
    .catch(error => {
        console.error('❌ DEBUG: Erreur de connexion:', error);
        showNotification('❌ Erreur lors du rechargement des opérations: ' + (error.message || 'Erreur de connexion'), 'error');
        
        // Continuer avec les opérations locales uniquement
        console.log('⚠️ Continuez avec les opérations locales uniquement en raison de l\'erreur réseau');
        mettreAJourTableauOperations();
    });
}



// Fonction pour valider un type d'opération
function validerTypeOperation(typeOperation) {
    const isValid = TYPES_OPERATIONS_VALIDES.includes(typeOperation);
    if (!isValid) {
        console.warn(`⚠️ Type d'opération invalide: "${typeOperation}"`);
        console.log('✅ Types valides:', TYPES_OPERATIONS_VALIDES);
    }
    return isValid;
}

// Fonction pour remplir la liste déroulante de commentaires selon le type d'opération
function remplirListeCommentaires(typeOperation) {
    const select = document.getElementById('commentSelect');
    
    // Réinitialiser la liste
    select.innerHTML = '<option value="">-- Sélectionnez une conclusion --</option>';
    
    // Déterminer le type d'opération à utiliser pour chercher les commentaires
    let typeOperationKey = typeOperation;
    
    // Si c'est un ID d'opération du tableau, extraire le vrai type
    if (typeOperation.startsWith('OP-')) {
        const operation = operationsTable.find(op => op.id === typeOperation);
        if (operation) {
            typeOperationKey = operation.type;
        }
    }
    
    console.log(`📝 Remplissage commentaires pour: ${typeOperationKey}`);
    
    // Remplir avec les commentaires prédéfinis depuis l'API
    const commentaires = COMMENTAIRES_PREDEFINIES[typeOperationKey];
    if (commentaires && commentaires.length > 0) {
        commentaires.forEach(commentaireObj => {
            const option = document.createElement('option');
            // Utiliser la structure {value, label} depuis l'API
            option.value = commentaireObj.value;
            option.textContent = commentaireObj.label;
            select.appendChild(option);
        });
        
        console.log(`✅ ${commentaires.length} commentaires ajoutés pour ${typeOperationKey}`);
    } else {
        console.warn(`⚠️ Aucun commentaire prédéfini trouvé pour: ${typeOperationKey}`);
        
        // Ajouter une option générique si aucun commentaire prédéfini
        const option = document.createElement('option');
        option.value = 'Opération effectuée avec succès';
        option.textContent = 'Opération effectuée avec succès';
        select.appendChild(option);
    }
}

// Fonction pour créer les champs cachés du formulaire
function creerChampsFormulaire() {
 
    
    // Supprimer les anciens champs
    const anciensChampsOperations = document.querySelectorAll('input[name="operations[]"]');
    const anciensChampsCommentaires = document.querySelectorAll('input[name^="comment_"]');
    
    anciensChampsOperations.forEach(input => input.remove());
    anciensChampsCommentaires.forEach(input => input.remove());
    
    // Vérifier que le formulaire existe
    const form = document.getElementById('modification-form');
    if (!form) {
        return;
    }
    
    let champsCreesOperations = 0;
    let champsCreesCommentaires = 0;
    
    // Créer les nouveaux champs pour chaque opération (sauf celles déjà en base)
    operationsTable.forEach((operation, index) => {
        // Ignorer les opérations déjà sauvegardées en base de données
        if (operation.fromDatabase) {
            console.log(`⏭️ Opération ${index + 1} ignorée (déjà en base): ${operation.type}`);
            return;
        }
        
        if (operation.commentaire && operation.commentaire.trim()) {
            // Valider le type d'opération
            if (!validerTypeOperation(operation.type)) {
                return;
            }
            
          
            
            // Champ pour le type d'opération
            const inputType = document.createElement('input');
            inputType.type = 'hidden';
            inputType.name = 'operations[]';
            inputType.value = operation.type;
            form.appendChild(inputType);
            champsCreesOperations++;
            
            // Champ pour le commentaire
            const inputComment = document.createElement('input');
            inputComment.type = 'hidden';
            inputComment.name = 'comment_' + operation.type;
            inputComment.value = operation.commentaire;
            form.appendChild(inputComment);
            champsCreesCommentaires++;
            
        } else {
            console.warn(`⚠️ Opération ${index + 1} ignorée (pas de commentaire): ${operation.type}`);
        }
    });
    
    console.log(`✅ ${champsCreesOperations} champs d'opérations créés`);
    console.log(`✅ ${champsCreesCommentaires} champs de commentaires créés`);
    
    // Afficher un résumé des données qui seront envoyées
    if (champsCreesOperations > 0) {
        console.log('📤 Données d\'opérations qui seront envoyées au serveur:');
        const operationsValues = Array.from(document.querySelectorAll('input[name="operations[]"]')).map(input => input.value);
        const commentairesValues = Array.from(document.querySelectorAll('input[name^="comment_"]')).map(input => `${input.name}: "${input.value}"`);
        
        console.log('  - Opérations:', operationsValues);
        console.log('  - Commentaires:', commentairesValues);
    }
}

// Fonction pour vérifier qu'au moins une opération est dans le tableau avant la soumission
function verifierOperationsSelectionnees() {
    console.log('🔍 Vérification des opérations avant sauvegarde...');
    console.log('📊 Opérations dans le tableau:', operationsTable);
    
    const operationsAvecCommentaire = operationsTable.filter(op => op.commentaire && op.commentaire.trim());
    
    // Permettre la sauvegarde sans opérations (pour sauvegarder juste les infos de commande/articles)
    if (operationsTable.length === 0) {
        console.log('ℹ️ Aucune opération ajoutée - sauvegarde des informations de commande uniquement');
        showNotification('💾 Sauvegarde des informations de commande', 'success');
        return true;
    }
    
    const operationsSansCommentaire = operationsTable.filter(op => !op.commentaire || !op.commentaire.trim());
    if (operationsSansCommentaire.length > 0) {
        alert(`❌ COMMENTAIRES OBLIGATOIRES MANQUANTS\n\nLes opérations suivantes nécessitent un commentaire :\n• ${operationsSansCommentaire.map(op => op.nom + ' (' + op.id + ')').join('\n• ')}\n\nVeuillez ajouter des commentaires pour toutes les opérations ou les supprimer du tableau.`);
        return false;
    }
    
    // Créer les champs du formulaire avant la soumission
    console.log('📋 Création des champs cachés pour les opérations...');
    creerChampsFormulaire();
    
    // Vérifier que les champs ont bien été créés
    const operationsFields = document.querySelectorAll('input[name="operations[]"]');
    const commentFields = document.querySelectorAll('input[name^="comment_"]');
    
    console.log(`✅ ${operationsFields.length} champs d'opérations créés`);
    console.log(`✅ ${commentFields.length} champs de commentaires créés`);
    
    if (operationsAvecCommentaire.length > 0) {
        showNotification(`💾 Sauvegarde : ${operationsAvecCommentaire.length} opération(s) avec commentaires`, 'success');
    }
    
    return true;
}

// Fermer la modale avec Escape
document.addEventListener('keydown', function(event) {
    if (event.key === 'Escape') {
        closeCommentModal();
    }
});
// Vérification et initialisation au chargement de la page
document.addEventListener('DOMContentLoaded', function() {
    console.log('🚀 Page chargée, initialisation du système...');
    
    try {
        // Vérifier que la modale existe
        const modal = document.getElementById('commentModal');
        if (!modal) {
            console.error('❌ Modale commentModal introuvable !');
            } else {
            console.log('✅ Modale commentModal trouvée');
            
            // Fermer la modale en cliquant à l'extérieur
            modal.addEventListener('click', function(event) {
                if (event.target === this) {
                    closeCommentModal();
                }
            });
        }
        
        // Vérifier les éléments de la modale
        const operationNameElement = document.getElementById('operationName');
        const commentSelectEl = document.getElementById('commentSelect');
        
        if (!operationNameElement) {
            console.warn('⚠️ Élément operationName introuvable');
        } else {
            console.log('✅ Élément operationName trouvé');
        }
        
        if (!commentSelectEl) {
            console.warn('⚠️ Select commentSelect introuvable');
        } else {
            console.log('✅ Select commentSelect trouvé');
        }
        
        // Vérifier les éléments du nouveau système
        const typePrincipalSelector = document.getElementById('type-principal-selector');
        const operationSelector = document.getElementById('operation-selector');
        const operationsList = document.getElementById('operations-list');
        const operationsTableBody = document.getElementById('operations-table-body');
        
        if (typePrincipalSelector) {
            console.log('✅ Sélecteur de type principal trouvé');
        } else {
            console.warn('⚠️ Sélecteur de type principal introuvable');
        }
        
        if (operationSelector) {
            console.log('✅ Sélecteur d\'opération trouvé');
        } else {
            console.warn('⚠️ Sélecteur d\'opération introuvable');
        }
        
        if (operationsList) {
            console.log('✅ Liste des opérations trouvée');
        } else {
            console.warn('⚠️ Liste des opérations introuvable');
        }
        
        if (operationsTableBody) {
            console.log('✅ Corps du tableau des opérations trouvé');
        } else {
            console.warn('⚠️ Corps du tableau des opérations introuvable');
        }
        
        console.log('✅ Système de modales initialisé avec succès');
        
        // Initialiser le tableau des opérations avec vérification
        if (typeof mettreAJourTableauOperations === 'function') {
            mettreAJourTableauOperations();
            console.log('✅ Tableau des opérations initialisé');
        } else {
            console.error('❌ Fonction mettreAJourTableauOperations introuvable');
        }
        
        
        // Fonction pour vérifier les stocks des articles
        window.verifierStocks = function() {
            console.log('📊 Vérification des stocks:');
            
            if (!articlesDisponibles || articlesDisponibles.length === 0) {
                console.log('❌ Aucun article chargé. Chargement...');
                chargerArticlesDisponibles();
                setTimeout(() => verifierStocks(), 1000);
                return;
            }
            
            console.log(`📦 ${articlesDisponibles.length} articles chargés`);
            
            // Afficher les articles avec stock > 0
            const articlesAvecStock = articlesDisponibles.filter(a => a.qte_disponible > 0);
            console.log(`✅ ${articlesAvecStock.length} articles avec stock > 0:`);
            articlesAvecStock.slice(0, 5).forEach((article, i) => {
                console.log(`   ${i+1}. ${article.nom} (ID: ${article.id}): Stock = ${article.qte_disponible}`);
            });
            
            // Afficher les articles sans stock
            const articlesSansStock = articlesDisponibles.filter(a => !a.qte_disponible || a.qte_disponible === 0);
            console.log(`❌ ${articlesSansStock.length} articles avec stock = 0:`);
            articlesSansStock.slice(0, 5).forEach((article, i) => {
                console.log(`   ${i+1}. ${article.nom} (ID: ${article.id}): Stock = ${article.qte_disponible}`);
            });
            
            // Vérifier l'affichage dans le DOM
            const articleCards = document.querySelectorAll('.article-card');
            console.log(`🔍 ${articleCards.length} cartes d'articles dans le DOM`);
            
            articleCards.forEach((card, i) => {
                const stockBadge = card.querySelector('.bg-green-100.text-green-700');
                const stockText = stockBadge ? stockBadge.textContent.trim() : 'Non trouvé';
                const articleData = JSON.parse(card.dataset.article || '{}');
                
                console.log(`   Article ${i+1}: ${articleData.nom || 'Sans nom'}`);
                console.log(`      - Stock affiché: ${stockText}`);
                console.log(`      - Stock dans data: ${articleData.qte_disponible}`);
            });
            
            return {
                total: articlesDisponibles.length,
                avecStock: articlesAvecStock.length,
                sansStock: articlesSansStock.length
            };
        };
        
        // Fonction pour tester le système de filtrage
        window.testFiltrage = function() {
            console.log('🧪 Test du système de filtrage...');
            console.log('📊 Articles disponibles:', articlesDisponibles ? articlesDisponibles.length : 'Non chargés');
            
            if (!articlesDisponibles || articlesDisponibles.length === 0) {
                console.log('❌ Aucun article chargé. Chargement...');
                chargerArticlesDisponibles();
                return;
            }
            
            // Tester chaque type de filtre
            const types = ['all', 'promo', 'liquidation', 'test', 'upsell'];
            types.forEach(type => {
                const count = compterArticlesParType(type);
                console.log(`📊 ${type.toUpperCase()}: ${count} article(s)`);
            });
            
            // Afficher quelques exemples d'articles par type
            console.log('\n📋 Exemples d\'articles par type:');
            
            const promosExemples = articlesDisponibles.filter(a => a.has_promo_active).slice(0, 2);
            console.log('🔥 PROMO:', promosExemples.map(a => `${a.nom} (${a.has_promo_active})`));
            
            const liquidationExemples = articlesDisponibles.filter(a => a.phase === 'LIQUIDATION').slice(0, 2);
            console.log('🏷️ LIQUIDATION:', liquidationExemples.map(a => `${a.nom} (${a.phase})`));
            
            const testExemples = articlesDisponibles.filter(a => a.phase === 'EN_TEST').slice(0, 2);
            console.log('🧪 TEST:', testExemples.map(a => `${a.nom} (${a.phase})`));
            
            const upsellExemples = articlesDisponibles.filter(a => a.isUpsell).slice(0, 2);
            console.log('⬆️ UPSELL:', upsellExemples.map(a => `${a.nom} (${a.isUpsell})`));
            
            // Tester un filtrage
            console.log('\n🔍 Test de filtrage par PROMO...');
            filtrerArticles('promo');
        };
        
        // Fonction pour tester manuellement l'API des articles
        window.testApiArticles = function() {
            console.log('🧪 Test manuel de l\'API des articles...');
            
            const apiUrl = '{% url "operatConfirme:api_articles_disponibles" %}';
            const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]');
            
            console.log('📋 Informations de test:');
            console.log('- URL:', apiUrl);
            console.log('- CSRF Token présent:', csrfToken ? 'OUI' : 'NON');
            console.log('- Utilisateur connecté:', '{{ user.username }}');
            console.log('- Type d\'utilisateur:', '{{ user.profil_operateur.type_operateur|default:"Non défini" }}');
            
            if (!csrfToken) {
                console.error('❌ Token CSRF manquant');
                return;
            }
            
            fetch(apiUrl, {
                method: 'GET',
                headers: {
                    'X-CSRFToken': csrfToken.value,
                    'X-Requested-With': 'XMLHttpRequest',
                },
                credentials: 'same-origin',
            })
            .then(response => {
                console.log('📡 Statut de la réponse:', response.status, response.statusText);
                console.log('📋 Headers de réponse:', Object.fromEntries(response.headers.entries()));
                
                if (!response.ok) {
                    return response.text().then(text => {
                        console.error('❌ Réponse d\'erreur:', text);
                        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
                    });
                }
                
                return response.json();
            })
            .then(data => {
                console.log('✅ Données reçues:', data);
                
                // Gestion des deux formats possibles (tableau direct ou objet avec propriété articles)
                let articles = [];
                if (Array.isArray(data)) {
                    articles = data;
                    console.log(`📦 ${articles.length} article(s) trouvé(s) (format tableau)`);
                } else if (data.success && data.articles) {
                    articles = data.articles;
                    console.log(`📦 ${articles.length} article(s) trouvé(s) (format objet)`);
                } else {
                    console.warn('⚠️ Format de données inattendu:', data);
                    return;
                }
                
                // Afficher les informations des articles
                articles.forEach((article, index) => {
                        console.log(`   Article ${index + 1}:`, {
                            id: article.id,
                            nom: article.nom,
                            reference: article.reference,
                            prix: article.prix_actuel,
                            pointure: article.pointure,
                            couleur: article.couleur,
                            stock: article.qte_disponible
                        });
                    });
            })
            .catch(error => {
                console.error('❌ Erreur lors du test:', error);
            });
        };
        

        // Afficher le nombre de commentaires par type
        console.log('📝 COMMENTAIRES PRÉDÉFINIS:');
        Object.keys(COMMENTAIRES_PREDEFINIES).forEach(type => {
            console.log(`   - ${type}: ${COMMENTAIRES_PREDEFINIES[type].length} options`);
        });
        
        console.log('📋 Système complet initialisé avec succès');
        
       
    } catch (error) {
        console.error('❌ Erreur lors de l\'initialisation:', error);
    }
});



// Fonction pour changer l'opération (ancienne fonction - gardée pour compatibilité)
function changerOperation() {
    // Cette fonction n'est plus utilisée avec le nouveau système
    console.log('Fonction changerOperation() appelée - système d\'opérations individuelles actif');
    
    // Cette fonction est désactivée dans le nouveau système de tableau
    console.log('⚠️ Fonction désactivée - utilisez le système de tableau à la place');
}
