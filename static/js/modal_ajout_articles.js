/**
 * Modal réutilisable pour l'ajout d'articles
 * Compatible avec toutes les interfaces (création, modification, etc.)
 */

console.log('🚀 Fichier modal_ajout_articles.js chargé avec succès');

// Variables globales pour la gestion des articles
let articleCounter = 0;
let articlesDisponibles = [];
let articlesAffiches = []; // Articles actuellement affichés (peut être filtré)
let ligneSelectionnee = null;

// Variables globales pour le modal des variantes
let articleSelectionne = null;
let quantiteInitiale = 1;
let variantesSelectionnees = new Map(); // Map pour stocker les variantes sélectionnées

// ================== FONCTIONS PRINCIPALES DU MODAL ==================

/**
 * Fonction pour ouvrir le modal d'ajout d'articles
 */
function ouvrirModalAjouterArticle(event) {
    // Empêcher la soumission du formulaire
    if (event) {
        event.preventDefault();
        event.stopPropagation();
    }
    
    console.log('🎯 Fonction ouvrirModalAjouterArticle appelée');
    console.log('🎯 Ouverture du modal ajout article');
    console.log('🔧 Fonction définie correctement');
    
    // Afficher le modal d'abord
    const modal = document.getElementById('articleModal');
    if (modal) {
        // Supprimer la classe hidden et forcer l'affichage
        modal.classList.remove('hidden');
        modal.style.display = 'flex';
        modal.style.visibility = 'visible';
        modal.style.opacity = '1';
        console.log('✅ Modal affiché');
    } else {
        console.error('❌ Modal non trouvé');
        return;
    }

    // Charger les articles disponibles
    try {
        chargerArticlesDisponibles();
    } catch (error) {
        console.error('❌ Erreur lors du chargement des articles:', error);
        // Le modal reste ouvert même si le chargement échoue
    }
}

/**
 * Fonction pour fermer le modal d'ajout d'articles
 */
function fermerModalAjouterArticle(event) {
    // Empêcher la soumission du formulaire
    if (event) {
        event.preventDefault();
        event.stopPropagation();
    }

    console.log('🎯 Fermeture du modal ajout article');

    const modal = document.getElementById('articleModal');
    if (modal) {
        modal.classList.add('hidden');
        modal.style.display = 'none';
        modal.style.visibility = 'hidden';
        modal.style.opacity = '0';
        console.log('✅ Modal fermé');
    }

    // Réinitialiser les variables
    ligneSelectionnee = null;
    articlesDisponibles = [];
    articlesAffiches = [];
}

/**
 * Fonction pour charger les articles disponibles depuis le JSON
 */
function chargerArticlesDisponibles() {
    console.log('📡 Chargement des articles disponibles');
    
    try {
        // Récupérer les données JSON des articles
        const articlesScript = document.getElementById('articles-data');
        if (!articlesScript) {
            console.error('❌ Script des articles non trouvé');
            afficherErreurArticles('Données des articles non disponibles');
            return;
        }
        
        const articlesData = JSON.parse(articlesScript.textContent);
        console.log('📊 Articles reçus:', articlesData.length);
        
        if (Array.isArray(articlesData) && articlesData.length > 0) {
            articlesDisponibles = articlesData;
            afficherArticles(articlesData);
            mettreAJourCompteurs();
        } else {
            console.warn('⚠️ Aucun article disponible');
            afficherErreurArticles('Aucun article disponible');
        }
    } catch (error) {
        console.error('❌ Erreur lors du chargement des articles:', error);
        afficherErreurArticles('Erreur lors du chargement des articles');
    }
}

/**
 * Fonction pour afficher les articles dans le tableau
 */
function afficherArticles(articles) {
    console.log('📋 Affichage de', articles.length, 'articles');

    // Stocker les articles affichés pour référence lors de la sélection
    articlesAffiches = articles;

    const tbody = document.getElementById('articlesTableBody');
    if (!tbody) {
        console.error('❌ Corps du tableau non trouvé');
        return;
    }
    
    if (articles.length === 0) {
        tbody.innerHTML = `
            <tr>
                <td colspan="4" class="px-4 py-8 text-center text-gray-500">
                    <div class="flex flex-col items-center">
                        <i class="fas fa-box-open text-3xl text-gray-300 mb-2"></i>
                        <p>Aucun article disponible</p>
                    </div>
                </td>
            </tr>
        `;
        return;
    }
    
    let html = '';
    articles.forEach((article, index) => {
        // Pour l'instant, on assume que tous les articles peuvent avoir des variantes
        // L'endpoint gérera le cas où il n'y en a pas
        const hasVariantes = true; // article.has_variantes || false;

        // Calculer le stock total (somme des stocks de toutes les variantes)
        const stockTotal = article.stock_total || article.qte_disponible || 0;
        const stockInfo = getStockInfo(stockTotal);
        const prix = article.prix_unitaire || 0;

        // Log détaillé pour déboguer
        console.log(`📊 Article[${index}]: ID=${article.id}, Nom=${article.nom}, Stock=${stockTotal}`);

        // Générer les badges
        let badges = '';
        if (article.has_promo_active) badges += '<span class="inline-flex items-center px-1.5 py-0.5 rounded-full text-xs font-medium bg-red-100 text-red-800 mr-1">🔥 PROMO</span>';
        if (article.phase === 'LIQUIDATION') badges += '<span class="inline-flex items-center px-1.5 py-0.5 rounded-full text-xs font-medium bg-orange-100 text-orange-800 mr-1">🏷️ LIQUIDATION</span>';
        if (article.phase === 'EN_TEST') badges += '<span class="inline-flex items-center px-1.5 py-0.5 rounded-full text-xs font-medium bg-blue-100 text-blue-800 mr-1">🧪 TEST</span>';
        if (article.isUpsell) badges += '<span class="inline-flex items-center px-1.5 py-0.5 rounded-full text-xs font-medium bg-green-100 text-green-800 mr-1">⬆️ UPSELL</span>';
        
        html += `
            <tr class="hover:bg-gray-50 cursor-pointer" onclick="selectionnerArticle(${index})" data-article-id="${article.id}">
                <td class="px-2 py-3">
                    <div class="flex items-center space-x-3">
                        <div class="w-10 h-10 rounded-lg overflow-hidden bg-gray-100 border border-gray-200 shadow-sm flex-shrink-0">
                            ${article.image_url ?
                                `<img src="${article.image_url}" alt="Image de ${article.nom}" class="w-full h-full object-cover" onerror="this.style.display='none'; this.nextElementSibling.style.display='flex';" onload="this.nextElementSibling.style.display='none';">` :
                                ''
                            }
                            <div class="w-full h-full flex items-center justify-center text-gray-400 ${article.image_url ? 'hidden' : ''}">
                                <i class="fas fa-image text-sm"></i>
                            </div>
                        </div>
                        <div class="min-w-0 flex-1">
                            <div class="text-sm font-medium text-gray-900 truncate">${article.nom}</div>
                            <div class="text-xs text-gray-500 truncate">${article.reference}</div>
                            <div class="mt-1 flex flex-wrap gap-1">${badges}</div>
                        </div>
                    </div>
                </td>
                <td class="px-1 py-3 text-center">
                    <div class="text-sm font-semibold text-gray-900">${prix.toFixed(2)} DH</div>
                </td>
                <td class="px-1 py-3 text-center">
                    <span class="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium ${stockInfo.class}">
                        ${stockInfo.text}
                    </span>
                </td>
                <td class="px-1 py-3 text-center">
                    <button data-article-id="${article.id}"
                            data-article-nom="${article.nom}"
                            onclick="event.preventDefault(); event.stopPropagation(); console.log('🔘 Clic bouton - Article ID:', ${article.id}, 'Nom:', '${article.nom}'); ${hasVariantes ? `ouvrirModalVariantesParId(${article.id})` : `ajouterArticleAuPanierParId(${article.id})`}"
                            class="inline-flex items-center px-3 py-1.5 rounded-full text-xs font-medium transition-colors ${hasVariantes ? 'bg-purple-100 text-purple-700 hover:bg-purple-200' : 'bg-green-100 text-green-700 hover:bg-green-200'}">
                        ${hasVariantes ? '🎨 Variantes' : '➕ Ajouter'}
                    </button>
                </td>
            </tr>
        `;
    });
    
    tbody.innerHTML = html;
    console.log('✅ Articles affichés dans le tableau');
}

/**
 * Fonction pour obtenir les informations de stock
 */
function getStockInfo(stock) {
    if (stock <= 0) {
        return { class: 'bg-red-100 text-red-800', text: 'Rupture' };
    } else if (stock < 5) {
        return { class: 'bg-orange-100 text-orange-800', text: `${stock} unité${stock > 1 ? 's' : ''}` };
    } else {
        return { class: 'bg-green-100 text-green-800', text: `${stock} unité${stock > 1 ? 's' : ''}` };
    }
}

/**
 * Fonction pour sélectionner un article dans le tableau
 */
function selectionnerArticle(index) {
    console.log('🎯 Sélection de l\'article:', index);

    // Désélectionner la ligne précédente
    if (ligneSelectionnee !== null) {
        const previousRow = document.querySelector(`#articlesTableBody tr:nth-child(${ligneSelectionnee + 1})`);
        if (previousRow) {
            previousRow.classList.remove('bg-blue-50', 'border-blue-200');
            previousRow.classList.add('hover:bg-gray-50');
        }
    }

    // Sélectionner la nouvelle ligne
    const currentRow = document.querySelector(`#articlesTableBody tr:nth-child(${index + 1})`);
    if (currentRow) {
        currentRow.classList.add('bg-blue-50', 'border-blue-200');
        currentRow.classList.remove('hover:bg-gray-50');
        ligneSelectionnee = index;
        // Utiliser articlesAffiches pour tenir compte des filtres/recherches
        if (articlesAffiches && articlesAffiches[index]) {
            console.log('✅ Article sélectionné:', articlesAffiches[index].nom);
        }
    }
}

/**
 * Fonction pour ajouter un article au panier (sans variantes)
 */
function ajouterArticleAuPanier(articleData, quantiteInitiale = 1) {
    console.log('📦 MODIF TEST - Ajout article au panier:', articleData.nom);
    
    // Créer un ID unique pour cet article
    const articleId = `article-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;
    
    // Créer la carte d'article
    const articleCard = document.createElement('div');
    articleCard.className = 'bg-white border border-gray-200 rounded-lg p-3 sm:p-4 shadow-sm hover:shadow-md transition-shadow';
    articleCard.id = articleId;
    articleCard.setAttribute('data-article-id', articleData.id);
    articleCard.setAttribute('data-variante-id', ''); // Pas de variante pour les articles simples
    
    // Calculer le sous-total
    const prix = articleData.prix_unitaire || 0;
    const quantite = quantiteInitiale;
    const sousTotal = (prix * quantite).toFixed(2);
    
    // Générer les badges
    let badges = '';
    if (articleData.has_promo_active) badges += '<span class="inline-flex items-center px-1.5 py-0.5 rounded-full text-xs font-medium bg-red-100 text-red-800 mr-1">🔥 PROMO</span>';
    if (articleData.phase === 'LIQUIDATION') badges += '<span class="inline-flex items-center px-1.5 py-0.5 rounded-full text-xs font-medium bg-orange-100 text-orange-800 mr-1">🏷️ LIQUIDATION</span>';
    if (articleData.phase === 'EN_TEST') badges += '<span class="inline-flex items-center px-1.5 py-0.5 rounded-full text-xs font-medium bg-blue-100 text-blue-800 mr-1">🧪 TEST</span>';
    if (articleData.isUpsell) badges += '<span class="inline-flex items-center px-1.5 py-0.5 rounded-full text-xs font-medium bg-green-100 text-green-800 mr-1">⬆️ UPSELL</span>';
    
    articleCard.innerHTML = `
        <div class="flex items-start justify-between">
            <div class="flex-1 min-w-0">
                <div class="flex items-start space-x-3">
                    <!-- Image de l'article -->
                    <div class="flex-shrink-0">
                        <div class="w-12 h-12 sm:w-16 sm:h-16 rounded-lg overflow-hidden bg-gray-100 border border-gray-200 shadow-sm">
                            ${articleData.image_url ? 
                                `<img src="${articleData.image_url}" alt="Image de ${articleData.nom}" class="w-full h-full object-cover" onerror="this.style.display='none'; this.nextElementSibling.style.display='flex';" onload="this.nextElementSibling.style.display='none';">` : 
                                ''
                            }
                            <div class="w-full h-full flex items-center justify-center text-gray-400 ${articleData.image_url ? 'hidden' : ''}">
                                <i class="fas fa-image text-sm"></i>
                            </div>
                        </div>
                    </div>
                    
                    <!-- Informations de l'article -->
                    <div class="flex-1 min-w-0">
                        <h4 class="text-sm sm:text-base font-medium text-gray-900 truncate">${articleData.nom}</h4>
                        <p class="text-xs sm:text-sm text-gray-500 truncate">${articleData.reference}</p>
                        <div class="mt-1 flex flex-wrap gap-1">${badges}</div>
                        <div class="mt-2 flex items-center space-x-4">
                            <div class="text-xs sm:text-sm text-gray-600">
                                <span class="font-medium">Prix:</span> ${prix.toFixed(2)} DH
                            </div>
                            <div class="text-xs sm:text-sm text-gray-600">
                                <span class="font-medium">Quantité:</span> 
                                <input type="number" min="1" value="${quantite}" 
                                       class="w-16 px-2 py-1 text-xs border border-gray-300 rounded focus:ring-1 focus:ring-blue-500 focus:border-blue-500"
                                       onchange="mettreAJourQuantiteArticle('${articleId}', this.value)">
                            </div>
                        </div>
                    </div>
                </div>
            </div>
            
            <!-- Actions -->
            <div class="flex flex-col items-end space-y-2">
                <div class="text-lg font-bold text-green-600">${sousTotal} DH</div>
                <button type="button" onclick="supprimerArticleDuPanier(this)" 
                        class="px-2 py-1 bg-red-500 hover:bg-red-600 text-white rounded text-xs transition-colors">
                    <i class="fas fa-trash mr-1"></i>Supprimer
                </button>
            </div>
        </div>
    `;
    
    // Ajouter au conteneur des articles
    const articlesContainer = document.getElementById('articles-container');
    if (articlesContainer) {
        articlesContainer.appendChild(articleCard);
        
        // Recalculer le total
        if (typeof calculerTotal === 'function') {
            calculerTotal();
        }
        
        console.log('✅ Article ajouté au panier:', articleId);
    } else {
        console.error('❌ Conteneur des articles non trouvé');
    }
}

/**
 * Fonction pour mettre à jour la quantité d'un article
 */
function mettreAJourQuantiteArticle(articleId, nouvelleQuantite) {
    const articleCard = document.getElementById(articleId);
    if (!articleCard) return;
    
    const quantite = parseInt(nouvelleQuantite) || 1;
    const prixElement = articleCard.querySelector('.text-xs.sm\\:text-sm.text-gray-600');
    if (prixElement) {
        const prixText = prixElement.textContent;
        const prix = parseFloat(prixText.match(/Prix:\s*([\d.]+)/)[1]);
        const sousTotal = (prix * quantite).toFixed(2);
        
        // Mettre à jour l'affichage du sous-total
        const sousTotalElement = articleCard.querySelector('.text-lg.font-bold');
        if (sousTotalElement) {
            sousTotalElement.textContent = `${sousTotal} DH`;
        }
        
        // Recalculer le total
        if (typeof calculerTotal === 'function') {
            calculerTotal();
        }
    }
}

/**
 * Fonction pour supprimer un article du panier
 */
function supprimerArticleDuPanier(button) {
    const articleCard = button.closest('.bg-white.border');
    if (articleCard) {
        articleCard.remove();

        // Recalculer les prix upsells après suppression
        recalculerPrixUpsells();

        // Recalculer le total
        if (typeof calculerTotal === 'function') {
            calculerTotal();
        }

        console.log('✅ Article supprimé du panier');
    }
}

// ================== FONCTIONS DU MODAL DES VARIANTES ==================

/**
 * Fonction pour ouvrir le modal de sélection des variantes par ID
 */
function ouvrirModalVariantesParId(articleId) {
    // Empêcher la soumission du formulaire
    if (event) {
        event.preventDefault();
        event.stopPropagation();
    }

    console.log('🎯 Ouverture modal variantes par ID:', articleId, 'Type:', typeof articleId);
    console.log('🔍 Articles disponibles:', articlesDisponibles.length);
    console.log('🔍 Premiers IDs des articles disponibles:', articlesDisponibles.slice(0, 5).map(a => ({ id: a.id, nom: a.nom, type: typeof a.id })));

    // Chercher l'article dans articlesDisponibles par son ID
    // Convertir les IDs en nombres pour assurer la comparaison
    const article = articlesDisponibles.find(a => parseInt(a.id) === parseInt(articleId));

    if (!article) {
        console.error('❌ Article non trouvé avec l\'ID:', articleId);
        console.error('❌ IDs disponibles:', articlesDisponibles.map(a => a.id));
        showNotification('❌ Erreur: article introuvable (ID: ' + articleId + ')', 'error');
        return;
    }

    console.log('✅ Article trouvé:', article);
    console.log('📋 Détails article:', {
        id: article.id,
        nom: article.nom,
        reference: article.reference,
        has_variantes: article.has_variantes
    });
    console.log('🆔 ID de l\'article qui sera envoyé au serveur:', article.id);

    ouvrirModalVariantes(article, 1);
}

/**
 * Fonction pour ajouter un article au panier par ID
 */
function ajouterArticleAuPanierParId(articleId) {
    // Empêcher la soumission du formulaire
    if (event) {
        event.preventDefault();
        event.stopPropagation();
    }

    console.log('🎯 Ajout article au panier par ID:', articleId);

    // Chercher l'article dans articlesDisponibles par son ID
    const article = articlesDisponibles.find(a => a.id === articleId);

    if (!article) {
        console.error('❌ Article non trouvé avec l\'ID:', articleId);
        showNotification('❌ Erreur: article introuvable', 'error');
        return;
    }

    ajouterArticleAuPanier(article, 1);
}

/**
 * Fonction pour ouvrir le modal de sélection des variantes par index (LEGACY - conservé pour compatibilité)
 */
function ouvrirModalVariantesParIndex(index) {
    console.warn('⚠️ ouvrirModalVariantesParIndex est obsolète, utilisez ouvrirModalVariantesParId');

    if (!articlesAffiches || index >= articlesAffiches.length) {
        console.error('❌ Index d\'article invalide:', index);
        return;
    }

    const article = articlesAffiches[index];
    ouvrirModalVariantes(article, 1);
}

/**
 * Fonction pour ajouter un article au panier par index (LEGACY - conservé pour compatibilité)
 */
function ajouterArticleAuPanierParIndex(index) {
    console.warn('⚠️ ajouterArticleAuPanierParIndex est obsolète, utilisez ajouterArticleAuPanierParId');

    if (!articlesAffiches || index >= articlesAffiches.length) {
        console.error('❌ Index d\'article invalide:', index);
        return;
    }

    const article = articlesAffiches[index];
    ajouterArticleAuPanier(article, 1);
}

/**
 * Fonction pour ouvrir le modal de sélection des variantes
 */
function ouvrirModalVariantes(articleData, quantite = 1) {
    console.log('🎯 Ouverture modal variantes:', { articleData, quantite });
    
    articleSelectionne = articleData;
    quantiteInitiale = quantite;
    
    // Réinitialiser la sélection des variantes
    variantesSelectionnees.clear();
    
    // Afficher le modal
    const modal = document.getElementById('variantModal');
    if (modal) {
        // Ajouter un event listener pour déboguer les clics sur le modal
        modal.addEventListener('click', function(e) {
            console.log('🖱️ Clic sur le modal:', e.target, e.target.onclick);
        });
    }
    const articleNom = document.getElementById('articleNom');
    const articleReference = document.getElementById('articleReference');
    
    console.log('🔍 Éléments du modal trouvés:', {
        modal: !!modal,
        articleNom: !!articleNom,
        articleReference: !!articleReference
    });
    
    if (!modal || !articleNom || !articleReference) {
        console.error('❌ Éléments du modal non trouvés');
        return;
    }
    
    // Mettre à jour les informations de l'article
    articleNom.textContent = articleData.nom || 'Article sans nom';
    articleReference.textContent = `Réf: ${articleData.reference || 'N/A'} - Prix: ${articleData.prix_unitaire} DH`;
    
    // Afficher le modal
    modal.classList.remove('hidden');
    modal.style.display = 'flex';
    modal.style.visibility = 'visible';
    modal.style.opacity = '1';
    
    console.log('✅ Modal des variantes affiché');
    
    // Charger les variantes
    chargerVariantesArticle(articleData.id);
}

/**
 * Fonction pour charger les variantes d'un article via AJAX
 */
function chargerVariantesArticle(articleId) {
    console.log('📡 Chargement des variantes pour l\'article ID:', articleId, 'Type:', typeof articleId);
    console.log('🔍 Article sélectionné actuellement:', articleSelectionne);

    // Masquer les informations des variantes sélectionnées
    const selectedVariantsInfo = document.getElementById('selectedVariantsInfo');
    const clearSelectionBtn = document.getElementById('clearSelectionBtn');
    const addSelectedVariantsBtn = document.getElementById('addSelectedVariantsBtn');

    if (selectedVariantsInfo) selectedVariantsInfo.classList.add('hidden');
    if (clearSelectionBtn) clearSelectionBtn.classList.add('hidden');
    if (addSelectedVariantsBtn) addSelectedVariantsBtn.classList.add('hidden');

    // Afficher le loading
    const variantsTableContainer = document.getElementById('variantsTableContainer');
    if (variantsTableContainer) {
        variantsTableContainer.innerHTML = `
            <div class="flex items-center justify-center py-8">
                <div class="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
                <span class="ml-3 text-gray-600">Chargement des variantes...</span>
            </div>
        `;
    }

    // Récupérer le token CSRF
    const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]');
    if (!csrfToken) {
        console.error('❌ Token CSRF manquant');
        afficherErreurVariantes('Token CSRF manquant');
        return;
    }

    // URL pour récupérer les variantes
    const url = `/operateur-confirme/get-article-variants/${articleId}/`;
    console.log('🌐 URL de l\'appel AJAX:', url);
    console.log('🌐 Article dont on cherche les variantes:', {
        id: articleId,
        nom: articleSelectionne?.nom,
        reference: articleSelectionne?.reference
    });
    
    // Appel AJAX
    fetch(url, {
        method: 'GET',
        headers: {
            'X-CSRFToken': csrfToken.value,
            'X-Requested-With': 'XMLHttpRequest',
        },
        credentials: 'same-origin',
    })
    .then(response => {
        console.log('📡 Statut de la réponse variantes:', response.status);
        if (!response.ok) {
            throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        }
        return response.json();
    })
    .then(data => {
        console.log('📊 Réponse complète du serveur:', data);
        console.log('📊 Article retourné par le serveur:', data.article);
        console.log('📊 Nombre de variantes reçues:', data.variants?.length);
        console.log('📊 Première variante:', data.variants?.[0]);

        if (data.success && data.variants) {
            // Vérifier que l'article retourné correspond bien à celui demandé
            if (articleSelectionne && data.article && parseInt(data.article.id) !== parseInt(articleSelectionne.id)) {
                console.error('⚠️ ATTENTION: L\'article retourné ne correspond pas à l\'article sélectionné !');
                console.error('⚠️ Article sélectionné:', articleSelectionne.id, articleSelectionne.nom);
                console.error('⚠️ Article retourné:', data.article.id, data.article.nom);
            } else {
                console.log('✅ Vérification OK: l\'article retourné correspond bien à l\'article sélectionné');
            }

            afficherVariantes(data.variants);
        } else {
            throw new Error(data.error || 'Erreur inconnue');
        }
    })
    .catch(error => {
        console.error('❌ Erreur lors du chargement des variantes:', error);
        afficherErreurVariantes(error.message);
    });
}

/**
 * Fonction pour afficher les variantes dans un tableau croisé
 */
function afficherVariantes(variantes) {
    console.log('📋 Affichage de', variantes.length, 'variantes');
    
    const variantsTableContainer = document.getElementById('variantsTableContainer');
    if (!variantsTableContainer) {
        console.error('❌ Conteneur des variantes non trouvé');
        return;
    }
    
    if (variantes.length === 0) {
        variantsTableContainer.innerHTML = `
            <div class="text-center py-6 sm:py-8 text-gray-500">
                <i class="fas fa-info-circle text-3xl sm:text-4xl mb-3 sm:mb-4 text-blue-500"></i>
                <p class="text-base sm:text-lg">Aucune variante disponible pour cet article</p>
            </div>
        `;
        return;
    }
    
    // Créer un tableau croisé des variantes
    const couleurs = [...new Set(variantes.map(v => v.couleur).filter(Boolean))];
    const pointures = [...new Set(variantes.map(v => v.pointure).filter(Boolean))];
    
    let tableHTML = `
        <table class="min-w-full border border-gray-200 rounded-lg overflow-hidden">
            <thead class="bg-gray-50">
                <tr>
                    <th class="px-4 py-3 text-left text-sm font-semibold text-gray-700 border-b border-gray-200">Couleur/Pointure</th>
    `;
    
    // En-têtes des pointures
    pointures.forEach(pointure => {
        tableHTML += `<th class="px-4 py-3 text-center text-sm font-semibold text-gray-700 border-b border-gray-200">${pointure}</th>`;
    });
    
    tableHTML += `
                </tr>
            </thead>
            <tbody>
    `;
    
    // Lignes des couleurs
    couleurs.forEach(couleur => {
        tableHTML += `<tr class="border-b border-gray-100">
            <td class="px-4 py-3 text-sm font-medium text-gray-900 bg-gray-50">${couleur}</td>`;
        
        pointures.forEach(pointure => {
            const variante = variantes.find(v => v.couleur === couleur && v.pointure === pointure);
            if (variante) {
                const stockInfo = getStockInfo(variante.stock);
                tableHTML += `
                    <td class="px-4 py-3 text-center border-l border-gray-100">
                        <div class="space-y-2">
                            <div class="text-lg font-bold text-green-600">${variante.prix_actuel?.toFixed(2) || '0.00'} DH</div>
                            <div class="px-2 py-1 rounded-full text-xs font-semibold ${stockInfo.class}">
                                ${stockInfo.text}
                            </div>
                            <label class="flex items-center justify-center cursor-pointer ${variante.stock <= 0 ? 'opacity-50 cursor-not-allowed' : ''}">
                                <input type="checkbox" 
                                       class="w-5 h-5 text-blue-600 bg-gray-100 border-gray-300 rounded focus:ring-blue-500 focus:ring-2 ${variante.stock <= 0 ? 'disabled' : ''}"
                                       data-variante='${JSON.stringify(variante).replace(/'/g, "\\'")}'
                                       onchange="gererSelectionVariante(this, '${variante.id}')"
                                       ${variante.stock <= 0 ? 'disabled' : ''}>
                                
                            </label>
                        </div>
                    </td>
                `;
            } else {
                tableHTML += '<td class="px-4 py-3 text-center border-l border-gray-100 text-gray-400">-</td>';
            }
        });
        
        tableHTML += '</tr>';
    });
    
    tableHTML += `
            </tbody>
        </table>
    `;
    
    variantsTableContainer.innerHTML = tableHTML;
}

/**
 * Fonction pour gérer la sélection d'une variante
 */
function gererSelectionVariante(checkbox, varianteId) {
    const varianteData = JSON.parse(checkbox.dataset.variante);
    
    if (checkbox.checked) {
        variantesSelectionnees.set(varianteId, varianteData);
        console.log('✅ Variante sélectionnée:', varianteData);
    } else {
        variantesSelectionnees.delete(varianteId);
        console.log('❌ Variante désélectionnée:', varianteData);
    }
    
    mettreAJourAffichageVariantesSelectionnees();
}

/**
 * Fonction pour mettre à jour l'affichage des variantes sélectionnées
 */
function mettreAJourAffichageVariantesSelectionnees() {
    const selectedVariantsInfo = document.getElementById('selectedVariantsInfo');
    const selectedVariantsDetails = document.getElementById('selectedVariantsDetails');
    const clearSelectionBtn = document.getElementById('clearSelectionBtn');
    const addSelectedVariantsBtn = document.getElementById('addSelectedVariantsBtn');
    
    if (variantesSelectionnees.size === 0) {
        selectedVariantsInfo.classList.add('hidden');
        clearSelectionBtn.classList.add('hidden');
        addSelectedVariantsBtn.classList.add('hidden');
        return;
    }
    
    selectedVariantsInfo.classList.remove('hidden');
    clearSelectionBtn.classList.remove('hidden');
    addSelectedVariantsBtn.classList.remove('hidden');
    
    let detailsHTML = '';
    variantesSelectionnees.forEach((variante, id) => {
        detailsHTML += `
            <div class="bg-white border border-gray-200 rounded-lg p-3 mb-2 shadow-sm">
                <div class="flex justify-between items-start">
                    <div class="flex-1">
                        <div class="text-sm font-semibold text-gray-900">${variante.couleur} - ${variante.pointure}</div>
                        <div class="text-xs text-gray-500 mt-1">
                            Prix: <span class="font-medium text-green-600">${variante.prix_actuel?.toFixed(2) || '0.00'} DH</span> | Stock: <span class="font-medium">${variante.stock || 0} en stock</span>
                        </div>
                    </div>
                    <button onclick="retirerVarianteSelectionnee('${id}')" 
                            class="ml-2 text-red-500 hover:text-red-700 text-sm p-1 rounded-full hover:bg-red-50 transition-colors">
                        <i class="fas fa-times"></i>
                    </button>
                </div>
            </div>
        `;
    });
    
    selectedVariantsDetails.innerHTML = detailsHTML;
    addSelectedVariantsBtn.innerHTML = `Ajouter ${variantesSelectionnees.size} variante(s)`;
}

/**
 * Fonction pour retirer une variante de la sélection
 */
function retirerVarianteSelectionnee(varianteId) {
    variantesSelectionnees.delete(varianteId);
    mettreAJourAffichageVariantesSelectionnees();
    
    // Décocher la checkbox correspondante
    const checkbox = document.querySelector(`input[data-variante*='"id":"${varianteId}"']`);
    if (checkbox) {
        checkbox.checked = false;
    }
    
    showNotification('✅ Variante retirée de la sélection', 'success');
}

/**
 * Fonction pour fermer le modal des variantes
 */
function fermerModalVariantes(event) {
    // Empêcher la soumission du formulaire
    if (event) {
        event.preventDefault();
        event.stopPropagation();
    }
    console.log('🚪 Fermeture du modal des variantes appelée depuis:', new Error().stack);
    
    const modal = document.getElementById('variantModal');
    if (modal) {
        modal.classList.add('hidden');
        modal.style.display = 'none';
        modal.style.visibility = 'hidden';
        modal.style.opacity = '0';
        console.log('✅ Modal fermé avec succès');
    } else {
        console.error('❌ Modal non trouvé lors de la fermeture');
    }
    
    articleSelectionne = null;
    quantiteInitiale = 1;
    variantesSelectionnees.clear();
}

/**
 * Fonction pour afficher une erreur dans le modal des variantes
 */
function afficherErreurVariantes(message) {
    const variantsTableContainer = document.getElementById('variantsTableContainer');
    if (variantsTableContainer) {
        variantsTableContainer.innerHTML = `
            <div class="text-center py-6 sm:py-8 text-red-500">
                <i class="fas fa-exclamation-triangle text-3xl sm:text-4xl mb-3 sm:mb-4 text-red-500"></i>
                <p class="text-base sm:text-lg">${message || 'Erreur lors du chargement des variantes'}</p>
            </div>
        `;
    }
}

/**
 * Fonction pour effacer la sélection des variantes
 */
function effacerSelectionVariantes(event) {
    // Empêcher la soumission du formulaire
    if (event) {
        event.preventDefault();
        event.stopPropagation();
    }
    const checkboxes = document.querySelectorAll('#variantsTableContainer input[type="checkbox"]');
    checkboxes.forEach(checkbox => {
        checkbox.checked = false;
    });
    
    variantesSelectionnees.clear();
    mettreAJourAffichageVariantesSelectionnees();
    showNotification('✅ Sélection des variantes effacée', 'success');
}

/**
 * Fonction pour ajouter les variantes sélectionnées au panier
 */
function ajouterVariantesSelectionnees(event) {
    // Empêcher la soumission du formulaire
    if (event) {
        event.preventDefault();
        event.stopPropagation();
    }
    
    console.log('📦 Ajout des variantes sélectionnées au panier:', variantesSelectionnees.size);
    console.log('🔍 Article sélectionné:', articleSelectionne);
    console.log('🔍 Variantes sélectionnées:', variantesSelectionnees);
    
    // Vérifier l'état du modal avant l'ajout
    const modal = document.getElementById('variantModal');
    console.log('🔍 État du modal avant ajout:', {
        exists: !!modal,
        hidden: modal ? modal.classList.contains('hidden') : 'N/A',
        display: modal ? modal.style.display : 'N/A'
    });
    
    if (variantesSelectionnees.size === 0) {
        showNotification('⚠️ Aucune variante sélectionnée', 'warning');
        return;
    }
    
    if (!articleSelectionne) {
        console.error('❌ Aucun article sélectionné');
        showNotification('❌ Erreur: aucun article sélectionné', 'error');
        return;
    }
    
    let ajoutees = 0;
    let erreurs = 0;
    
    try {
        variantesSelectionnees.forEach((variante, id) => {
            try {
                console.log('🔄 Ajout de la variante:', variante);
                ajouterVarianteAuPanier(articleSelectionne, variante, 1);
                ajoutees++;
                console.log('✅ Variante ajoutée avec succès');
            } catch (error) {
                console.error('❌ Erreur lors de l\'ajout de la variante:', error);
                console.error('❌ Stack trace:', error.stack);
                erreurs++;
            }
        });
        
        // Afficher le résultat
        if (ajoutees > 0) {
            showNotification(`✅ ${ajoutees} variante(s) ajoutée(s) au panier`, 'success');
        }
        
        if (erreurs > 0) {
            showNotification(`⚠️ ${erreurs} variante(s) n'ont pas pu être ajoutées`, 'warning');
        }
        
        // Ne fermer les modals que si au moins une variante a été ajoutée avec succès
        if (ajoutees > 0) {
            console.log('🎯 Variantes ajoutées avec succès, fermeture des modals');
            fermerModalVariantes();
            fermerModalAjouterArticle();
            showNotification(`✅ ${ajoutees} variante(s) ajoutée(s) au panier avec succès !`, 'success');
        } else {
            console.log('⚠️ Aucune variante ajoutée, le modal reste ouvert');
            showNotification('❌ Aucune variante n\'a pu être ajoutée au panier', 'error');
        }
        
        // Vérifier l'état du modal après l'ajout
        console.log('🔍 État du modal après ajout:', {
            exists: !!modal,
            hidden: modal ? modal.classList.contains('hidden') : 'N/A',
            display: modal ? modal.style.display : 'N/A'
        });
        
    } catch (error) {
        console.error('❌ Erreur générale lors de l\'ajout des variantes:', error);
        showNotification('❌ Erreur lors de l\'ajout des variantes', 'error');
    }
}

/**
 * Fonction pour ajouter une variante au panier (à adapter selon l'interface)
 */
function ajouterVarianteAuPanier(articleData, variante, quantiteInitiale = 1) {
    // Cette fonction doit être adaptée selon l'interface qui utilise le modal
    console.log('📦 Ajout variante au panier:', {
        article: articleData.nom,
        variante: variante,
        quantite: quantiteInitiale
    });
    
    // Si une fonction spécifique existe, l'utiliser
    if (typeof ajouterVarianteAuPanierAdmin === 'function') {
        ajouterVarianteAuPanierAdmin(articleData, variante, quantiteInitiale);
    } else if (typeof ajouterVarianteAuPanierConfirmation === 'function') {
        ajouterVarianteAuPanierConfirmation(articleData, variante, quantiteInitiale);
    } else {
        // Fonction par défaut - créer directement la variante dans le panier
        console.log('⚠️ Aucune fonction spécifique trouvée, utilisation de la fonction par défaut');
        ajouterVarianteAuPanierConfirmation(articleData, variante, quantiteInitiale);
    }
}

/**
 * Fonction pour vérifier si une variante existe déjà dans le panier
 */
function varianteExisteDansLePanier(varianteId) {
    const articlesContainer = document.getElementById('articles-container');
    if (!articlesContainer) {
        return false;
    }

    const variantes = articlesContainer.querySelectorAll('[data-variante-id]');
    for (let element of variantes) {
        if (element.getAttribute('data-variante-id') === varianteId.toString()) {
            return element; // Retourner l'élément s'il existe
        }
    }
    return false;
}

/**
 * Fonction pour incrémenter la quantité d'une variante existante
 */
function incrementerQuantiteVarianteExistante(varianteElement) {
    const quantiteInput = varianteElement.querySelector('input[type="number"]');
    if (quantiteInput) {
        const nouvelleQuantite = parseInt(quantiteInput.value) + 1;
        quantiteInput.value = nouvelleQuantite;

        // Déclencher l'événement de changement pour recalculer le total
        const changeEvent = new Event('change', { bubbles: true });
        quantiteInput.dispatchEvent(changeEvent);

        return true;
    }
    return false;
}

/**
 * Fonction pour ajouter une variante au panier (spécifique à la page de création)
 */
function ajouterVarianteAuPanierConfirmation(articleData, variante, quantiteInitiale = 1) {
    console.log('📦 Ajout variante au panier (confirmation):', {
        article: articleData.nom,
        variante: variante,
        quantite: quantiteInitiale
    });

    console.log('🔍 Vérification des éléments DOM...');

    try {
        // Vérifier que les données sont valides
        if (!articleData || !variante) {
            throw new Error('Données d\'article ou de variante manquantes');
        }

        // Vérifier si la variante existe déjà dans le panier
        const varianteExistante = varianteExisteDansLePanier(variante.id);
        if (varianteExistante) {
            // La variante existe déjà, incrémenter sa quantité
            if (incrementerQuantiteVarianteExistante(varianteExistante)) {
                console.log('✅ Quantité de la variante mise à jour');
                showNotification(`✅ Quantité mise à jour pour ${articleData.nom} (${variante.couleur} - ${variante.pointure})`, 'success');
                // Recalculer les prix upsells après modification de quantité
                recalculerPrixUpsells();
                return;
            } else {
                showNotification(`⚠️ Impossible de mettre à jour la quantité pour ${articleData.nom} (${variante.couleur} - ${variante.pointure})`, 'warning');
                return;
            }
        }

        // Calculer le compteur AVANT d'ajouter le nouvel article
        const compteurAvant = calculerCompteurUpsell();
        console.log(`📊 Compteur avant ajout: ${compteurAvant}`);

        // Calculer le compteur APRÈS l'ajout (si c'est un article upsell)
        const estUpsell = articleData.isUpsell === true || articleData.isUpsell === 'true';
        const compteurApres = estUpsell ? compteurAvant + quantiteInitiale : compteurAvant;
        console.log(`📊 Compteur après ajout: ${compteurApres}, Article est upsell: ${estUpsell}`);

        // Déterminer le prix selon le compteur
        const prixInfo = getPrixSelonCompteur(articleData, compteurApres);
        console.log(`💰 Prix déterminé: ${prixInfo.prix} DH (${prixInfo.libelle})`);

        // Utiliser le prix de la variante si disponible, sinon utiliser le prix calculé
        const prix = variante.prix_actuel || prixInfo.prix;
        const quantite = quantiteInitiale;
        const sousTotal = (prix * quantite).toFixed(2);

        // Créer un ID unique pour cette variante
        const varianteId = `variante-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;

        // Créer la carte d'article
        const articleCard = document.createElement('div');
        articleCard.className = 'bg-white border border-gray-200 rounded-lg p-3 sm:p-4 shadow-sm hover:shadow-md transition-shadow';
        articleCard.id = varianteId;
        articleCard.setAttribute('data-article-id', articleData.id);
        articleCard.setAttribute('data-variante-id', variante.id);

        // Stocker toutes les données de l'article pour le recalcul ultérieur
        const articleDataComplet = {
            id: articleData.id,
            nom: articleData.nom,
            reference: articleData.reference,
            prix_unitaire: articleData.prix_unitaire,
            prix_actuel: articleData.prix_actuel,
            prix_upsell_2: articleData.prix_upsell_2 || 0,
            prix_upsell_3: articleData.prix_upsell_3 || 0,
            prix_upsell_4: articleData.prix_upsell_4 || 0,
            prix_gros: articleData.prix_gros || 0,
            Prix_liquidation: articleData.Prix_liquidation || 0,
            isUpsell: articleData.isUpsell,
            phase: articleData.phase,
            has_promo_active: articleData.has_promo_active,
            variante_id: variante.id,
            couleur: variante.couleur,
            pointure: variante.pointure
        };

        articleCard.setAttribute('data-article', JSON.stringify(articleDataComplet));

        // Générer les badges
        let badges = '';
        if (articleData.has_promo_active) badges += '<span class="inline-flex items-center px-1.5 py-0.5 rounded-full text-xs font-medium bg-red-100 text-red-800 mr-1">🔥 PROMO</span>';
        if (articleData.phase === 'LIQUIDATION') badges += '<span class="inline-flex items-center px-1.5 py-0.5 rounded-full text-xs font-medium bg-orange-100 text-orange-800 mr-1">🏷️ LIQUIDATION</span>';
        if (articleData.phase === 'EN_TEST') badges += '<span class="inline-flex items-center px-1.5 py-0.5 rounded-full text-xs font-medium bg-blue-100 text-blue-800 mr-1">🧪 TEST</span>';
        if (articleData.isUpsell) badges += '<span class="inline-flex items-center px-1.5 py-0.5 rounded-full text-xs font-medium bg-green-100 text-green-800 mr-1">⬆️ UPSELL</span>';

        // Badge spécifique à la variante
        badges += `<span class="inline-flex items-center px-1.5 py-0.5 rounded-full text-xs font-medium bg-purple-100 text-purple-800 mr-1">🎨 ${variante.couleur || 'N/A'}</span>`;
        badges += `<span class="inline-flex items-center px-1.5 py-0.5 rounded-full text-xs font-medium bg-indigo-100 text-indigo-800 mr-1">📏 ${variante.pointure || 'N/A'}</span>`;

        articleCard.innerHTML = `
            <div class="flex items-start justify-between">
                <div class="flex-1 min-w-0">
                    <div class="flex items-start space-x-3">
                        <!-- Image de l'article -->
                        <div class="flex-shrink-0">
                            <div class="w-12 h-12 sm:w-16 sm:h-16 rounded-lg overflow-hidden bg-gray-100 border border-gray-200 shadow-sm">
                                ${articleData.image_url ?
                                    `<img src="${articleData.image_url}" alt="Image de ${articleData.nom}" class="w-full h-full object-cover" onerror="this.style.display='none'; this.nextElementSibling.style.display='flex';" onload="this.nextElementSibling.style.display='none';">` :
                                    ''
                                }
                                <div class="w-full h-full flex items-center justify-center text-gray-400 ${articleData.image_url ? 'hidden' : ''}">
                                    <i class="fas fa-image text-sm"></i>
                                </div>
                            </div>
                        </div>

                        <!-- Informations de l'article -->
                        <div class="flex-1 min-w-0">
                            <h4 class="text-sm sm:text-base font-medium text-gray-900 truncate">${articleData.nom}</h4>
                            <p class="text-xs sm:text-sm text-gray-500 truncate">${articleData.reference}</p>
                            <div class="mt-1 flex flex-wrap gap-1">${badges}</div>
                            <div class="mt-2 flex items-center space-x-4">
                                <div class="text-xs sm:text-sm text-gray-600">
                                    <span class="font-medium">Prix:</span> ${prix.toFixed(2)} DH
                                </div>
                                <div class="text-xs sm:text-sm text-gray-600">
                                    <span class="font-medium">Quantité:</span>
                                    <input type="number" min="1" value="${quantite}"
                                           class="w-16 px-2 py-1 text-xs border border-gray-300 rounded focus:ring-1 focus:ring-blue-500 focus:border-blue-500"
                                           onchange="mettreAJourQuantiteVariante('${varianteId}', this.value)">
                                </div>
                            </div>
                        </div>
                    </div>
                </div>

                <!-- Actions -->
                <div class="flex flex-col items-end space-y-2">
                    <div class="text-lg font-bold text-green-600">${sousTotal} DH</div>
                    <button type="button" onclick="supprimerArticleDuPanier(this)"
                            class="px-2 py-1 bg-red-500 hover:bg-red-600 text-white rounded text-xs transition-colors">
                        <i class="fas fa-trash mr-1"></i>Supprimer
                    </button>
                </div>
            </div>
        `;

        // Ajouter au conteneur des articles
        console.log('🔍 Recherche du conteneur articles-container...');
        const articlesContainer = document.getElementById('articles-container');
        console.log('🔍 Conteneur trouvé:', !!articlesContainer);

        if (articlesContainer) {
            console.log('🔄 Ajout de la carte au conteneur...');
            articlesContainer.appendChild(articleCard);
            console.log('✅ Carte ajoutée au conteneur');

            // Recalculer les prix upsells de TOUS les articles si nécessaire
            console.log('🔄 Recalcul des prix upsells...');
            recalculerPrixUpsells();

            // Recalculer le total
            console.log('🔄 Vérification de la fonction calculerTotal...');
            if (typeof calculerTotal === 'function') {
                console.log('🔄 Appel de calculerTotal...');
                calculerTotal();
                console.log('✅ calculerTotal appelé');
            } else {
                console.warn('⚠️ Fonction calculerTotal non trouvée');
            }

            console.log('✅ Variante ajoutée au panier:', varianteId);
        } else {
            console.error('❌ Conteneur des articles non trouvé');
            throw new Error('Conteneur des articles non trouvé');
        }

    } catch (error) {
        console.error('❌ Erreur dans ajouterVarianteAuPanierConfirmation:', error);
        console.error('❌ Stack trace:', error.stack);
        throw error; // Re-lancer l'erreur pour qu'elle soit gérée par la fonction appelante
    }
}

/**
 * Fonction pour générer les champs cachés du panier avant soumission
 * @param {HTMLFormElement} formElement - Le formulaire cible (optionnel, utilise le premier formulaire par défaut)
 */
function genererChampsCachesPanier(formElement = null) {
    console.log('🔧 Génération des champs cachés du panier...');

    // Déterminer le formulaire à utiliser
    let targetForm = formElement;
    if (!targetForm) {
        // Chercher le formulaire panierForm en priorité, sinon le premier formulaire
        targetForm = document.getElementById('panierForm') || document.querySelector('form');
    }

    if (!targetForm) {
        console.error('❌ Aucun formulaire trouvé');
        return;
    }

    console.log('📋 Formulaire cible:', targetForm.id || 'formulaire sans ID');

    // Supprimer les anciens champs cachés dans ce formulaire
    const anciensChamps = targetForm.querySelectorAll('input[name^="article_"], input[name^="variante_"], input[name^="quantite_"]');
    anciensChamps.forEach(champ => {
        console.log('🗑️ Suppression ancien champ:', champ.name);
        champ.remove();
    });

    const articlesContainer = document.getElementById('articles-container');
    if (!articlesContainer) {
        console.warn('⚠️ Conteneur des articles non trouvé');
        return;
    }

    const articles = articlesContainer.querySelectorAll('[id^="article-"], [id^="variante-"]');
    console.log('📦 Articles trouvés dans le panier:', articles.length);

    let compteur = 0;
    articles.forEach(article => {
        try {
            // Extraire les données de l'article
            const articleId = article.getAttribute('data-article-id');
            const varianteId = article.getAttribute('data-variante-id');
            const quantiteInput = article.querySelector('input[type="number"]');
            const quantite = quantiteInput ? quantiteInput.value : 1;

            if (articleId) {
                // Créer les champs cachés
                const champArticle = document.createElement('input');
                champArticle.type = 'hidden';
                champArticle.name = `article_${compteur}`;
                champArticle.value = articleId;
                targetForm.appendChild(champArticle);

                if (varianteId) {
                    const champVariante = document.createElement('input');
                    champVariante.type = 'hidden';
                    champVariante.name = `variante_${compteur}`;
                    champVariante.value = varianteId;
                    targetForm.appendChild(champVariante);
                }

                const champQuantite = document.createElement('input');
                champQuantite.type = 'hidden';
                champQuantite.name = `quantite_${compteur}`;
                champQuantite.value = quantite;
                targetForm.appendChild(champQuantite);

                console.log(`✅ Champ ${compteur}: article=${articleId}, variante=${varianteId || 'none'}, quantite=${quantite}`);
                compteur++;
            }
        } catch (error) {
            console.error('❌ Erreur lors de la génération du champ:', error);
        }
    });

    console.log(`🎯 ${compteur} champs cachés générés pour le panier`);
}

/**
 * Fonction pour mettre à jour la quantité d'une variante
 */
function mettreAJourQuantiteVariante(varianteId, nouvelleQuantite) {
    console.log('🔄 Mise à jour quantité variante:', varianteId, 'nouvelle quantité:', nouvelleQuantite);

    const articleCard = document.getElementById(varianteId);
    if (!articleCard) {
        console.error('❌ Carte d\'article non trouvée:', varianteId);
        return;
    }

    const quantite = parseInt(nouvelleQuantite) || 1;
    console.log('📊 Quantité parsée:', quantite);

    // Trouver le prix dans la structure HTML actuelle
    const prixText = articleCard.querySelector('.text-xs.sm\\:text-sm.text-gray-600, .text-green-600');
    if (prixText) {
        // Extraire le prix du texte "Prix: 549.00 DH"
        const prixMatch = prixText.textContent.match(/Prix:\s*([\d.]+)/);
        if (prixMatch) {
            const prix = parseFloat(prixMatch[1]);
            const sousTotal = prix * quantite;

            console.log('💰 Calcul:', prix, 'x', quantite, '=', formaterMontant(sousTotal));

            // Mettre à jour l'affichage du sous-total
            const sousTotalElement = articleCard.querySelector('.text-lg.font-bold');
            if (sousTotalElement) {
                sousTotalElement.textContent = `${formaterMontant(sousTotal)} DH`;
                console.log('✅ Sous-total mis à jour:', formaterMontant(sousTotal));
            } else {
                console.error('❌ Élément sous-total non trouvé');
            }

            // Recalculer les prix upsells après modification de quantité
            recalculerPrixUpsells();

            // Recalculer le total
            if (typeof calculerTotal === 'function') {
                calculerTotal();
                console.log('✅ Total recalculé');
            } else {
                console.warn('⚠️ Fonction calculerTotal non trouvée');
            }
        } else {
            console.error('❌ Impossible d\'extraire le prix du texte:', prixText.textContent);
        }
    } else {
        console.error('❌ Élément prix non trouvé dans la carte');
        console.log('🔍 Structure de la carte:', articleCard.innerHTML);
    }
}

// ================== FONCTIONS DE RECHERCHE ET FILTRAGE ==================

/**
 * Fonction pour rechercher des articles
 */
function rechercherArticles(termeRecherche = null) {
    // Empêcher la soumission du formulaire
    if (event) {
        event.preventDefault();
        event.stopPropagation();
    }
    
    // Si aucun terme n'est fourni, récupérer depuis le champ
    if (termeRecherche === null) {
        const searchInput = document.getElementById('recherche-article-input');
        if (!searchInput) {
            console.error('❌ Champ de recherche non trouvé');
            return;
        }
        termeRecherche = searchInput.value.toLowerCase().trim();
    } else {
        termeRecherche = termeRecherche.toLowerCase().trim();
    }
    
    console.log('🔍 Recherche:', termeRecherche);
    
    if (!termeRecherche) {
        afficherArticles(articlesDisponibles);
        return;
    }
    
    const articlesFiltres = articlesDisponibles.filter(article => 
        article.nom.toLowerCase().includes(termeRecherche) ||
        article.reference.toLowerCase().includes(termeRecherche) ||
        (article.description && article.description.toLowerCase().includes(termeRecherche))
    );
    
    console.log('📊 Articles filtrés:', articlesFiltres.length);
    afficherArticles(articlesFiltres);
}

/**
 * Fonction pour mettre à jour les compteurs des badges de filtrage
 */
function mettreAJourCompteurs() {
    if (!articlesDisponibles || articlesDisponibles.length === 0) {
        return;
    }
    
    // Compter les articles par type
    const compteurs = {
        all: articlesDisponibles.length,
        promo: articlesDisponibles.filter(article => article.has_promo_active).length,
        liquidation: articlesDisponibles.filter(article => article.phase === 'LIQUIDATION').length,
        test: articlesDisponibles.filter(article => article.phase === 'EN_TEST').length,
        upsell: articlesDisponibles.filter(article => article.isUpsell).length
    };
    
    // Mettre à jour les compteurs dans le DOM
    Object.keys(compteurs).forEach(type => {
        const countElement = document.getElementById(`count-${type}`);
        if (countElement) {
            countElement.textContent = compteurs[type];
        }
    });
    
    console.log('📊 Compteurs mis à jour:', compteurs);
}

/**
 * Fonction pour calculer le total de la commande
 */
function calculerTotal() {
    console.log('🧮 Calcul du total de la commande');
    
    const articlesContainer = document.getElementById('articles-container');
    if (!articlesContainer) {
        console.warn('⚠️ Conteneur des articles non trouvé');
        return;
    }
    
    let total = 0;
    const articles = articlesContainer.querySelectorAll('[id^="article-"], [id^="variante-"]');
    
    console.log('🔍 Articles trouvés:', articles.length);
    
    articles.forEach((article, index) => {
        // Chercher le sous-total (prix x quantité) dans la carte
        const sousTotalElement = article.querySelector('.text-lg.font-bold');
        if (sousTotalElement) {
            const prixText = sousTotalElement.textContent.replace(' DH', '').trim();
            const prix = parseFloat(prixText);
            if (!isNaN(prix)) {
                total += prix;
                console.log(`📊 Article ${index + 1}: ${prix} DH`);
            } else {
                console.warn('⚠️ Prix invalide pour l\'article:', prixText);
            }
        } else {
            console.warn('⚠️ Élément sous-total non trouvé pour l\'article:', article.id);
        }
    });
    
    // Ajouter les frais de livraison si activés
    const fraisLivraisonField = document.getElementById('frais_livraison');
    const fraisLivraisonActif = document.getElementById('frais_livraison_actif');
    let fraisLivraison = 0;

    // Vérifier si les frais de livraison sont activés
    const fraisActifs = fraisLivraisonActif && fraisLivraisonActif.value === 'true';

    if (fraisActifs && fraisLivraisonField && fraisLivraisonField.value) {
        fraisLivraison = parserMontant(fraisLivraisonField.value);
        console.log('🚚 Frais de livraison activés:', formaterMontant(fraisLivraison), 'DH');
    } else if (!fraisActifs) {
        console.log('🚫 Frais de livraison désactivés');
    }
    
    // Calculer le total final (articles + frais de livraison)
    const totalFinal = total + fraisLivraison;
    
    // Mettre à jour le champ total
    const totalField = document.getElementById('total_cmd');
    if (totalField) {
        totalField.value = formaterMontant(totalFinal);
        console.log('✅ Champ total mis à jour:', formaterMontant(totalFinal), 'DH');
    } else {
        console.warn('⚠️ Champ total non trouvé');
    }
    
    console.log('💰 Calcul final:', {
        totalArticles: formaterMontant(total) + ' DH',
        fraisLivraison: formaterMontant(fraisLivraison) + ' DH',
        totalFinal: formaterMontant(totalFinal) + ' DH'
    });
}

/**
 * Fonction pour filtrer les articles par type
 */
function filtrerArticles(type, event) {
    // Empêcher la soumission du formulaire
    if (event) {
        event.preventDefault();
        event.stopPropagation();
    }
    
    console.log('🎯 Filtrage par type:', type);
    
    let articlesFiltres = articlesDisponibles;
    
    if (type !== 'all') {
        articlesFiltres = articlesDisponibles.filter(article => {
            switch (type) {
                case 'promo':
                    return article.has_promo_active;
                case 'liquidation':
                    return article.phase === 'LIQUIDATION';
                case 'test':
                    return article.phase === 'EN_TEST';
                case 'upsell':
                    return article.isUpsell;
                default:
                    return true;
            }
        });
    }
    
    console.log('📊 Articles filtrés:', articlesFiltres.length);
    afficherArticles(articlesFiltres);
}

/**
 * Fonction pour afficher une erreur dans le tableau des articles
 */
function afficherErreurArticles(message) {
    const tbody = document.getElementById('articlesTableBody');
    if (tbody) {
        tbody.innerHTML = `
            <tr>
                <td colspan="4" class="px-4 py-8 text-center text-red-500">
                    <div class="flex flex-col items-center">
                        <i class="fas fa-exclamation-triangle text-3xl text-red-300 mb-2"></i>
                        <p>${message}</p>
                    </div>
                </td>
            </tr>
        `;
    }
}

// ================== GESTION DES PRIX UPSELLS ==================

/**
 * Calcule le compteur d'articles upsell dans le panier
 * Le compteur représente le nombre total d'unités d'articles upsell
 */
function calculerCompteurUpsell() {
    const articlesContainer = document.getElementById('articles-container');
    if (!articlesContainer) {
        return 0;
    }

    let totalUpsell = 0;
    const articles = articlesContainer.querySelectorAll('[data-article-id]');

    articles.forEach(article => {
        try {
            const articleDataStr = article.getAttribute('data-article');
            if (!articleDataStr) return;

            const articleData = JSON.parse(articleDataStr);

            // Vérifier si l'article est un upsell
            if (articleData.isUpsell === true || articleData.isUpsell === 'true') {
                // Récupérer la quantité
                const quantiteInput = article.querySelector('input[type="number"]');
                const quantite = quantiteInput ? parseInt(quantiteInput.value) || 1 : 1;

                totalUpsell += quantite;
                console.log(`📊 Article upsell: ${articleData.nom}, Qté: ${quantite}, Total actuel: ${totalUpsell}`);
            }
        } catch (error) {
            console.error('❌ Erreur lors du calcul du compteur pour un article:', error);
        }
    });

    console.log(`🎯 Compteur upsell total: ${totalUpsell}`);
    return totalUpsell;
}

/**
 * Détermine le prix applicable selon l'article et le compteur upsell
 * Respecte les priorités: Promotion > Liquidation > Test > Upsell > Normal
 */
function getPrixSelonCompteur(articleData, compteur) {
    console.log(`💰 Calcul prix pour: ${articleData.nom}, Compteur: ${compteur}, isUpsell: ${articleData.isUpsell}`);

    // PRIORITÉ 1: Promotion active
    if (articleData.has_promo_active === true || articleData.has_promo_active === 'true') {
        console.log('🔥 Prix promotion appliqué');
        return {
            prix: articleData.prix_actuel || articleData.prix_unitaire,
            libelle: 'Prix promotion',
            couleur: 'text-red-600',
            type: 'promotion'
        };
    }

    // PRIORITÉ 2: Phase liquidation
    if (articleData.phase === 'LIQUIDATION') {
        console.log('🏷️ Prix liquidation appliqué');
        return {
            prix: articleData.Prix_liquidation || articleData.prix_actuel || articleData.prix_unitaire,
            libelle: 'Prix liquidation',
            couleur: 'text-orange-600',
            type: 'liquidation'
        };
    }

    // PRIORITÉ 3: Phase test
    if (articleData.phase === 'EN_TEST') {
        console.log('🧪 Prix test appliqué');
        return {
            prix: articleData.prix_actuel || articleData.prix_unitaire,
            libelle: 'Prix test',
            couleur: 'text-blue-600',
            type: 'test'
        };
    }

    // PRIORITÉ 4: Article upsell avec compteur
    if ((articleData.isUpsell === true || articleData.isUpsell === 'true') && compteur > 0) {
        let prixUpsell = null;
        let niveau = 0;

        if (compteur === 1 && articleData.prix_upsell_2 && articleData.prix_upsell_2 > 0) {
            prixUpsell = articleData.prix_upsell_2;
            niveau = 2;  // Niveau 2 car utilise prix_upsell_2
        } else if (compteur === 2 && articleData.prix_upsell_3 && articleData.prix_upsell_3 > 0) {
            prixUpsell = articleData.prix_upsell_3;
            niveau = 3;  // Niveau 3 car utilise prix_upsell_3
        } else if (compteur === 3 && articleData.prix_upsell_4 && articleData.prix_upsell_4 > 0) {
            prixUpsell = articleData.prix_upsell_4;
            niveau = 4;  // Niveau 4 car utilise prix_upsell_4
        } else if (compteur >= 4 && articleData.prix_gros && articleData.prix_gros > 0) {
            prixUpsell = articleData.prix_gros;
            niveau = 5;  // Niveau 5 pour Prix Gros
        }

        if (prixUpsell) {
            const libelle = niveau >= 5 ? 'Prix Gros' : `Prix upsell ${niveau}`;
            console.log(`⬆️ ${libelle} appliqué: ${prixUpsell} DH`);
            return {
                prix: prixUpsell,
                libelle: libelle,
                couleur: 'text-green-600',
                type: `upsell_niveau_${niveau}`
            };
        }
    }

    // PRIORITÉ 5: Prix normal par défaut
    console.log('📌 Prix normal appliqué');
    return {
        prix: articleData.prix_actuel || articleData.prix_unitaire,
        libelle: 'Prix normal',
        couleur: 'text-gray-600',
        type: 'normal'
    };
}

/**
 * Recalcule tous les prix upsells dans le panier
 * À appeler après chaque ajout/suppression/modification d'article upsell
 */
function recalculerPrixUpsells() {
    console.log('🔄 Recalcul de tous les prix upsells...');

    const articlesContainer = document.getElementById('articles-container');
    if (!articlesContainer) {
        console.warn('⚠️ Conteneur articles-container non trouvé');
        return;
    }

    // Calculer le nouveau compteur
    const compteur = calculerCompteurUpsell();
    console.log(`📊 Nouveau compteur: ${compteur}`);

    // Parcourir tous les articles du panier
    const articles = articlesContainer.querySelectorAll('[data-article-id]');

    articles.forEach(articleCard => {
        try {
            const articleDataStr = articleCard.getAttribute('data-article');
            if (!articleDataStr) return;

            const articleData = JSON.parse(articleDataStr);

            // Calculer le nouveau prix selon le compteur
            const prixInfo = getPrixSelonCompteur(articleData, compteur);

            // Récupérer la quantité actuelle
            const quantiteInput = articleCard.querySelector('input[type="number"]');
            const quantite = quantiteInput ? parseInt(quantiteInput.value) || 1 : 1;

            // Calculer le nouveau sous-total
            const nouveauSousTotal = prixInfo.prix * quantite;

            // Mettre à jour l'affichage du prix unitaire (si présent)
            const prixUnitaireElement = articleCard.querySelector('.prix-unitaire-display');
            if (prixUnitaireElement) {
                prixUnitaireElement.textContent = `${formaterMontant(prixInfo.prix)} DH`;
                prixUnitaireElement.className = `prix-unitaire-display font-medium ${prixInfo.couleur}`;
            }

            // Mettre à jour le libellé du prix (si présent)
            const libelleElement = articleCard.querySelector('.prix-libelle');
            if (libelleElement) {
                libelleElement.textContent = prixInfo.libelle;
                libelleElement.className = `prix-libelle text-xs ${prixInfo.couleur} mt-1`;
            }

            // Mettre à jour le sous-total
            const sousTotalElement = articleCard.querySelector('.text-lg.font-bold');
            if (sousTotalElement) {
                sousTotalElement.textContent = `${formaterMontant(nouveauSousTotal)} DH`;
                console.log(`✅ Mis à jour: ${articleData.nom} - ${prixInfo.libelle} - ${formaterMontant(nouveauSousTotal)} DH`);
            }

        } catch (error) {
            console.error('❌ Erreur lors du recalcul du prix pour un article:', error);
        }
    });

    // Recalculer le total de la commande
    if (typeof calculerTotal === 'function') {
        calculerTotal();
    }

    console.log('✅ Recalcul terminé');
}

// ================== FONCTIONS UTILITAIRES ==================

/**
 * Fonction pour formater un montant en DH
 */
function formaterMontant(montant) {
    return parseFloat(montant).toFixed(2);
}

/**
 * Fonction pour nettoyer et parser un montant depuis un champ de saisie
 */
function parserMontant(montantText) {
    if (!montantText) return 0;
    // Nettoyer le texte (enlever les espaces, virgules, etc.)
    const texteNettoye = montantText.toString().replace(/[^\d,.-]/g, '').replace(',', '.');
    return parseFloat(texteNettoye) || 0;
}

/**
 * Fonction pour afficher une notification (utilitaire)
 */
function showNotification(message, type = 'info', duration = 3000) {
    try {
        const notification = document.createElement('div');
        let bgColor = 'bg-blue-500';
        
        if (type === 'success') bgColor = 'bg-green-500';
        else if (type === 'error') bgColor = 'bg-red-500';
        else if (type === 'warning') bgColor = 'bg-yellow-500';
        
        notification.className = `fixed top-4 right-4 px-4 py-2 rounded-lg text-white text-sm z-50 transition-all duration-300 ${bgColor} max-w-sm`;
        notification.textContent = message;
        
        document.body.appendChild(notification);
        
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
        }, duration);
    } catch (error) {
        console.error('❌ Erreur lors de la création de la notification:', error);
        alert(message);
    }
}

// ================== INITIALISATION ==================

/**
 * Initialisation du modal au chargement de la page
 */
document.addEventListener('DOMContentLoaded', function() {
    console.log('🚀 Initialisation du modal d\'ajout d\'articles');
    
    // Empêcher la soumission de formulaire quand un modal est ouvert
    document.addEventListener('submit', function(e) {
        const modalPrincipal = document.getElementById('articleModal');
        const modalVariantes = document.getElementById('variantModal');
        
        if ((modalPrincipal && !modalPrincipal.classList.contains('hidden')) || 
            (modalVariantes && !modalVariantes.classList.contains('hidden'))) {
            console.log('🚫 Soumission de formulaire bloquée - modal ouvert');
            e.preventDefault();
            e.stopPropagation();
            return false;
        }
    });
    
    // Gestionnaire d'événements pour le modal des variantes
    const modalVariantes = document.getElementById('variantModal');
    if (modalVariantes) {
        modalVariantes.addEventListener('click', function(e) {
            if (e.target === modalVariantes) {
                fermerModalVariantes();
            }
        });
    }
    
    // Gestionnaire d'événements pour le modal principal
    const modalPrincipal = document.getElementById('articleModal');
    if (modalPrincipal) {
        modalPrincipal.addEventListener('click', function(e) {
            if (e.target === modalPrincipal) {
                fermerModalAjouterArticle();
            }
        });
    }
    
    // Event listener pour recalculer le total quand les frais de livraison changent
    const fraisLivraisonField = document.getElementById('frais_livraison');
    if (fraisLivraisonField) {
        fraisLivraisonField.addEventListener('input', function() {
            console.log('🚚 Frais de livraison modifiés, recalcul du total...');
            if (typeof calculerTotal === 'function') {
                calculerTotal();
            }
        });
    }
    
    // Initialiser le total à 0 au chargement de la page
    const totalField = document.getElementById('total_cmd');
    if (totalField) {
        totalField.value = '0.00';
        console.log('💰 Total initialisé à 0.00 DH');
    }
    
    // Ajouter un event listener pour la soumission du formulaire
    const form = document.querySelector('form');
    if (form) {
        form.addEventListener('submit', function(e) {
            console.log('📤 Soumission du formulaire détectée');
            genererChampsCachesPanier();
        });
    }
    
    console.log('✅ Modal d\'ajout d\'articles initialisé');
});
