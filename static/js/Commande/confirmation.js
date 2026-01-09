/**
 * ================== CONFIRMATION COMMANDE - MODULE GLOBAL ==================
 *
 * Module reutilisable pour la confirmation et validation des commandes
 *
 * Fonctionnalites:
 * - Validation des champs obligatoires avant confirmation
 * - Verification du stock en temps reel
 * - Gestion des stocks insuffisants
 * - Annulation de commande avec motif
 * - Lancement du processus de confirmation
 * - Notifications utilisateur
 *
 * Etats de commande geres:
 * - Affectee -> En cours (lancerConfirmation)
 * - En cours -> Confirmee (confirmerCommande)
 * - En cours -> Annulee (annulerCommande)
 *
 * Utilisation:
 * 1. Inclure ce fichier dans votre template
 * 2. S'assurer qu'un bouton appelle confirmerCommande()
 * 3. Modal stockInsuffisantModal doit exister pour gerer les ruptures
 *
 * Dependances:
 * - Backend endpoint: /operateur-confirme/commandes/{id}/confirmer-ajax/
 * - Backend endpoint: /operateur-confirme/commandes/{id}/lancer-confirmation/
 * - Backend endpoint: /operateur-confirme/commandes/{id}/annuler-confirmation/
 *
 * @version 2.0 - Version globale reutilisable
 * @author YZ-RESCUE
 */
console.log('✅ confirmation.js (GLOBAL) charge - Version 2.0');

// Fonction pour confirmer la commande
function confirmerCommande() {
    // Vérifier que les sections essentielles sont remplies
    const nomClient = document.querySelector('[name="client_nom"]')?.value?.trim();
    const telephoneClient = document.querySelector('[name="client_telephone"]')?.value?.trim();
    const villeId = document.querySelector('[name="ville_livraison"]')?.value;
    const adresse = document.querySelector('[name="adresse_livraison"]')?.value?.trim();
    
    // Vérifications essentielles
    if (!nomClient) {
        showNotification('⚠️ Veuillez renseigner le nom ', 'error');
        return;
    }
    
    if (!telephoneClient) {
        showNotification('⚠️ Veuillez renseigner le numéro de téléphone du client', 'error');
        return;
    }
        
    if (!villeId) {
        showNotification('⚠️ Veuillez sélectionner une ville de livraison', 'error');
        return;
    }
    
    // Vérifier que la région est bien remplie (automatiquement quand on sélectionne une ville)
    const regionDisplay = document.getElementById('region-display')?.value?.trim();
    if (!regionDisplay || regionDisplay === '') {
        showNotification('⚠️ La région n\'est pas définie. Veuillez re-sélectionner une ville de livraison', 'error');
        return;
    }
    
    if (!adresse) {
        showNotification('⚠️ Veuillez renseigner l\'adresse de livraison', 'error');
        return;
    }
    
    // Vérifier qu'il y a au moins un article dans la commande
    const articles = document.querySelectorAll('.article-card');
    if (articles.length === 0) {
        showNotification('⚠️ La commande doit contenir au moins un article', 'error');
        return;
    }
                
    console.log('✅ Toutes les vérifications passées, confirmation immédiate...');
    // Lancer directement la confirmation immédiate
    proceedWithConfirmation();
    return;
}

// Fonction pour procéder à la confirmation
function proceedWithConfirmation() {
    // Afficher une notification de traitement en cours
    const message = '⏳ Confirmation en cours... (vérification du stock)';
    showNotification(message, 'info');
    
    // Récupérer les informations de livraison du formulaire
    const villeSelect = document.getElementById('ville-select');
    const adresseTextarea = document.querySelector('textarea[name="adresse_livraison"]');
    
    const villeId = villeSelect ? villeSelect.value : '';
    const adresse = adresseTextarea ? adresseTextarea.value.trim() : '';
    
    console.log('🏙️ DEBUG: Données de livraison à envoyer:', {
        ville_livraison: villeId,
        adresse_livraison: adresse
    });
    
    // Confirmer la commande avec les informations de livraison
    const commandeId = getCommandeId();
    fetch(`/operateur-confirme/commandes/${commandeId}/confirmer-ajax/`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value
        },
        body: JSON.stringify({
            'commentaire': 'Commande confirmée après vérification complète',
            'ville_livraison': villeId,
            'adresse_livraison': adresse
        })
    })
    .then(response => response.json())
    .then(data => {
        console.log('📬 DEBUG: Réponse de confirmation reçue:', data);
        
        if (data.success) {
            // Message de succès avec détails du stock
            let successMessage = '✅ Commande confirmée avec succès !';
            
            if (data.articles_decrémentes && data.articles_decrémentes > 0) {
                successMessage += `\n📦 ${data.articles_decrémentes} article(s) décrémenté(s) du stock.`;
                
                // Log détaillé des modifications de stock
                if (data.details_stock && data.details_stock.length > 0) {
                    console.log('📊 DEBUG: Détails de la décrémentation du stock:');
                    data.details_stock.forEach((item, index) => {
                        console.log(`   Article ${index + 1}: ${item.article}`);
                        console.log(`      - Stock: ${item.ancien_stock} → ${item.nouveau_stock} (-${item.quantite_decrémententée})`);
                    });
                }
            }
            
            showNotification(successMessage, 'success');
            
            // Rediriger après un court délai pour voir la notification
            setTimeout(() => {
                window.location.href = '/operateur-confirme/confirmation/';
            }, 1000); // 1 seconde pour voir la notification
            
        } else {
            // Gestion des erreurs de stock insuffisant
            console.error('❌ DEBUG: Erreur de confirmation:', data.message);
            
            if (data.stock_insuffisant && data.stock_insuffisant.length > 0) {
                // Préparer les données pour le modal de stock insuffisant
                window.stockInsuffisantData = data.stock_insuffisant;
                showStockInsuffisantModal();
            } else {
                showNotification('❌ Erreur lors de la confirmation : ' + data.message, 'error');
            }
        }
    })
    .catch(error => {
        console.error('❌ DEBUG: Erreur de connexion:', error);
        showNotification('❌ Une erreur de connexion est survenue : ' + error.message, 'error');
    });
}

// Fonction pour afficher le modal de stock insuffisant
function showStockInsuffisantModal() {
    // Remplir le contenu du modal avec les données de stock
    const stockList = document.getElementById('stockInsuffisantList');
    if (stockList && window.stockInsuffisantData) {
        stockList.innerHTML = '';
        window.stockInsuffisantData.forEach(item => {
            const li = document.createElement('li');
            li.className = 'flex justify-between items-center py-2 px-3 bg-red-50 rounded-lg border border-red-200';
            li.innerHTML = `
                <div class="flex items-center space-x-3">
                    <div class="w-2 h-2 bg-red-500 rounded-full"></div>
                    <span class="font-medium text-gray-900">${item.article}</span>
                </div>
                <div class="text-sm text-red-600">
                    <span class="font-medium">Stock: ${item.stock_actuel}</span> | 
                    <span class="font-medium">Demandé: ${item.quantite_demandee}</span>
                </div>
            `;
            stockList.appendChild(li);
        });
    }
    
    const modal = document.getElementById('stockInsuffisantModal');
    if (modal) {
        modal.classList.remove('hidden');
        modal.classList.add('flex');
    }
}

// Fonction pour masquer le modal de stock insuffisant
function hideStockInsuffisantModal() {
    const modal = document.getElementById('stockInsuffisantModal');
    if (modal) {
        modal.classList.add('hidden');
        modal.classList.remove('flex');
    }
}

// Fonction pour afficher des notifications
function showNotification(message, type = 'info', duration = 3000) {
    try {
        const notification = document.createElement('div');
        
        // Déterminer les couleurs selon le type
        let bgColor = 'bg-blue-500'; // info par défaut
        if (type === 'success') bgColor = 'bg-green-500';
        else if (type === 'error') bgColor = 'bg-red-500';
        else if (type === 'warning') bgColor = 'bg-yellow-500';
        
        notification.className = `fixed top-4 right-4 px-4 py-2 rounded-lg text-white text-sm z-50 transition-all duration-300 ${bgColor} max-w-sm`;
        
        // Permettre les retours à la ligne dans les notifications
        notification.style.whiteSpace = 'pre-line';
        notification.textContent = message;
        
        document.body.appendChild(notification);
        
        // Durée d'affichage variable selon le type et la longueur du message
        let displayDuration = duration; // Utiliser la durée passée en paramètre
        if (type === 'success' && message.includes('décrémenté')) {
            displayDuration = 5000; // 5 secondes pour les messages de stock
        } else if (type === 'error') {
            displayDuration = 6000; // 6 secondes pour les erreurs
        }
        
        // Supprimer après la durée déterminée avec vérifications de sécurité
        setTimeout(() => {
            try {
                if (notification && notification.parentNode) {
                    notification.style.opacity = '0';
                    setTimeout(() => {
                        try {
                            if (notification && notification.parentNode) {
                                document.body.removeChild(notification);
                            }
                        } catch (error) {
                            console.warn('⚠️ Erreur lors de la suppression de la notification:', error);
                        }
                    }, 300);
                }
            } catch (error) {
                console.warn('⚠️ Erreur lors de la modification de l\'opacité de la notification:', error);
            }
        }, displayDuration);
    } catch (error) {
        console.error('❌ Erreur lors de la création de la notification:', error);
        // Fallback vers une alerte simple
        alert(message);
    }
}

// Fonction pour lancer la confirmation (change l'état de Affectée à En cours)
function lancerConfirmation() {
    const commandeId = getCommandeId();
    fetch(`/operateur-confirme/commandes/${commandeId}/lancer-confirmation/`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value
        }
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            showNotification('Confirmation lancée avec succès !', 'success');
            // Recharger la page pour voir les changements
            setTimeout(() => {
                location.reload();
            }, 1500);
        } else {
            alert('Erreur lors du lancement : ' + data.message);
        }
    })
    .catch(error => {
        console.error('Erreur:', error);
        alert('Une erreur est survenue lors du lancement de la confirmation.');
    });
}

// Fonction pour annuler définitivement la commande (En cours de confirmation -> Annulée)
function annulerCommande() {
    // Créer et afficher la modal d'annulation
    const modal = document.createElement('div');
    modal.className = 'fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50';
    modal.innerHTML = `
        <div class="bg-white rounded-xl p-6 max-w-md w-full mx-4 shadow-2xl">
            <div class="flex items-center mb-4">
                <div class="flex-shrink-0">
                    <i class="fas fa-exclamation-triangle text-red-500 text-2xl"></i>
                </div>
                <div class="ml-3">
                    <h3 class="text-lg font-bold text-gray-900">Annuler la commande</h3>
                    <p class="text-sm text-gray-600">Cette action est irréversible</p>
                </div>
            </div>
            
            <div class="mb-4">
                <label for="motifAnnulationSelect" class="block text-sm font-semibold mb-2 text-gray-700">
                    Motif d'annulation <span class="text-red-500">*</span>
                </label>
                <select id="motifAnnulationSelect" 
                        class="w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-red-500 focus:border-transparent mb-3" 
                        required>
                    <option value="">Sélectionner un motif...</option>
                    <option value="Doublon confirmé">Doublon confirmé</option>
                    <option value="Numéro tel incorrect">Numéro tel incorrect</option>
                    <option value="Numéro de téléphone injoignable">Numéro de téléphone injoignable</option>
                    <option value="Client non intéressé">Client non intéressé</option>
                    <option value="Adresse erronée">Adresse erronée</option>
                    <option value="Erreur de saisie">Erreur de saisie</option>
                    <option value="Autre">Autre (préciser ci-dessous)</option>
                </select>
                
                <div id="motifPersonnaliseDiv" style="display: none;">
                    <label for="motifAnnulation" class="block text-sm font-medium mb-2 text-gray-700">
                        Motif personnalisé
                    </label>
                    <textarea id="motifAnnulation" rows="2" 
                            class="w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-red-500 focus:border-transparent" 
                            placeholder="Précisez le motif..."></textarea>
                </div>
                
                <p class="text-xs text-gray-500 mt-1">Le motif est obligatoire et sera visible dans l'historique</p>
            </div>
            
            <div class="flex justify-end space-x-3">
                <button type="button" id="btnAnnulerModal" 
                        class="px-4 py-2 bg-gray-300 text-gray-700 rounded-lg hover:bg-gray-400 transition-colors">
                    Annuler
                </button>
                <button type="button" id="btnConfirmerAnnulation" 
                        class="px-4 py-2 bg-red-500 text-white rounded-lg hover:bg-red-600 transition-colors">
                    <i class="fas fa-ban mr-1"></i>Confirmer l'annulation
                </button>
            </div>
        </div>
    `;
    
    document.body.appendChild(modal);
    
    // Focus sur le select
    const motifSelect = document.getElementById('motifAnnulationSelect');
    const motifInput = document.getElementById('motifAnnulation');
    const motifPersonnaliseDiv = document.getElementById('motifPersonnaliseDiv');
    
    motifSelect.focus();
    
    // Gérer l'affichage du champ personnalisé
    motifSelect.addEventListener('change', function() {
        if (this.value === 'Autre') {
            motifPersonnaliseDiv.style.display = 'block';
            motifInput.focus();
        } else {
            motifPersonnaliseDiv.style.display = 'none';
            motifInput.value = '';
        }
    });
    
    // Fermer la modal
    document.getElementById('btnAnnulerModal').addEventListener('click', function() {
        document.body.removeChild(modal);
    });
    
    // Confirmer l'annulation
    document.getElementById('btnConfirmerAnnulation').addEventListener('click', function() {
        let motif = '';
        
        if (motifSelect.value === 'Autre') {
            motif = motifInput.value.trim();
            if (!motif) {
                motifInput.classList.add('border-red-500');
                motifInput.focus();
                return;
            }
        } else {
            motif = motifSelect.value;
            if (!motif) {
                motifSelect.classList.add('border-red-500');
                motifSelect.focus();
                return;
            }
        }
        
        // Envoyer la requête d'annulation
        const commandeId = getCommandeId();
        fetch(`/operateur-confirme/commandes/${commandeId}/annuler-confirmation/`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value
            },
            body: JSON.stringify({
                motif: motif
            })
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                showNotification('Commande annulée avec succès !', 'success');
                // Rediriger vers la liste des commandes confirmées après un court délai
                setTimeout(() => {
                    window.location.href = '/operateur-confirme/commandes-confirmees/';
                }, 1500);
            } else {
                alert('Erreur lors de l\'annulation : ' + data.message);
            }
        })
        .catch(error => {
            console.error('Erreur:', error);
            alert('Une erreur est survenue lors de l\'annulation de la commande.');
        })
        .finally(() => {
            document.body.removeChild(modal);
        });
    });
    
    // Fermer en cliquant à l'extérieur
    modal.addEventListener('click', function(e) {
        if (e.target === modal) {
            document.body.removeChild(modal);
        }
    });
}

// Exposer au scope global pour les onclick HTML
if (typeof window !== 'undefined') {
  window.confirmerCommande = confirmerCommande;
  window.annulerCommande = annulerCommande;
  window.lancerConfirmation = lancerConfirmation;
}