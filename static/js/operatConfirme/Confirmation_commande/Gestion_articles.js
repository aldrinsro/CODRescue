

// ================== GESTION DES ARTICLES ==================

 // Variables globales pour les articles
    let articlesDisponibles = [];
    let currentArticleId = null;
    let isEditingArticle = false;
    
    let compteurCommande = commande.compteur ;
    let filtreActuel = 'all'; // Filtre actuellement actif

   
// Helpers globaux pour récupérer commandeId et urlModifier sans répétition
function getCommandeId() {
    if (typeof window !== 'undefined' && window.commandeId) return window.commandeId;
    const root = document.getElementById('mainContent');
    const id = root ? root.getAttribute('data-commande-id') : null;
    if (id) {
        window.commandeId = id;
        return id;
    }
    return '';
}

function getUrlModifier() {
    if (typeof window !== 'undefined' && window.urlModifier) return window.urlModifier;
    const id = getCommandeId();
    const url = `/operateur-confirme/commandes/${id}/modifier/`;
    window.urlModifier = url;
    return url;
}
    



// Fonction pour ajouter un nouvel article
function ajouterNouvelArticle() {
    isEditingArticle = false;
    currentArticleId = null;
    
    // Mettre à jour le titre
    document.getElementById('articleModalTitle').textContent = 'Ajouter un article';
    
    // Afficher le champ de sélection, cacher l'affichage
    document.getElementById('article-selection-field').classList.remove('hidden');
    document.getElementById('article-display-field').classList.add('hidden');
    
    // Réinitialiser le formulaire
    document.getElementById('articleSelect').value = '';
    document.getElementById('quantiteInput').value = '1';
    document.getElementById('article-info').classList.add('hidden');
    
    // Charger la liste des articles
    chargerArticlesDisponibles();
    
    // Afficher la modale
    const modal = document.getElementById('articleModal');
    if (modal) {
        modal.style.display = 'flex';
        modal.classList.remove('hidden');
        modal.classList.add('flex');
    } else {
        console.error('❌ Modale articleModal introuvable lors de l\'ajout d\'article');
    }
}

// Fonction pour modifier un article existant
function modifierArticle(panierId) {
    
    
    isEditingArticle = true;
    currentArticleId = panierId;
    
    // Mettre à jour le titre
    document.getElementById('articleModalTitle').textContent = 'Modifier l\'article';
    
    // Toujours afficher le champ de sélection pour permettre de changer l'article
    document.getElementById('article-selection-field').classList.remove('hidden');
    document.getElementById('article-display-field').classList.add('hidden');
    
    // Charger la liste des articles
    chargerArticlesDisponibles();
    
    // Récupérer les données de l'article depuis la carte
    const articleCard = document.querySelector(`[data-article-id="${panierId}"]`);
    
    if (articleCard) {
        // Récupérer la quantité avec vérification de sécurité
        const quantiteElement = articleCard.querySelector('input[type="number"]');
        if (quantiteElement && quantiteElement.value) {
            document.getElementById('quantiteInput').value = quantiteElement.value;
        } else {
            document.getElementById('quantiteInput').value = '1'; // Valeur par défaut
        }
        
        // Récupérer la référence de l'article pour le pré-sélectionner avec vérification de sécurité
        const referenceElement = articleCard.querySelector('.text-sm.text-gray-500');
        let reference = '';
        if (referenceElement && referenceElement.textContent) {
            const referenceText = referenceElement.textContent;
            reference = referenceText.replace('Réf: ', '').replace('Référence: ', '').trim();
        }
        
        // Récupérer les données complètes de l'article depuis le dataset
        try {
            const articleData = JSON.parse(articleCard.dataset.article || '{}');

            // Afficher les informations de l'article avec les données complètes
            if (articleData && articleData.id) {
                afficherInfosArticle(articleData);
            } else {
                // Fallback à l'ancienne méthode si les données ne sont pas disponibles
                afficherInfosArticleExistant(articleCard);
            }
        } catch (error) {
            console.error('❌ Erreur lors de la récupération des données article:', error);
            // Fallback à l'ancienne méthode
            afficherInfosArticleExistant(articleCard);
        }
        
        // Attendre que les articles soient chargés puis pré-sélectionner l'article actuel
        setTimeout(() => {
            preselectionnerArticle(reference);
        }, 500);
    }
    
    // Afficher la modale avec vérification de sécurité
    const modal = document.getElementById('articleModal');
    if (modal) {
        modal.style.display = 'flex';
        modal.classList.remove('hidden');
        modal.classList.add('flex');
    } else {
        console.error('❌ Modale articleModal introuvable lors de la modification d\'article');
        showNotification('❌ Erreur: Modale de modification introuvable', 'error');
        return;
    }
}

// Fonction pour pré-sélectionner un article dans la liste déroulante
function preselectionnerArticle(reference) {
    const select = document.getElementById('articleSelect');
    if (!select) {
        console.error('❌ Élément articleSelect introuvable');
        return;
    }
    
    // Chercher l'option correspondant à la référence
    for (let i = 0; i < select.options.length; i++) {
        const option = select.options[i];
        if (option.dataset.article) {
            try {
                const article = JSON.parse(option.dataset.article);
                if (article.reference === reference) {
                    select.selectedIndex = i;

                    // Déclencher l'événement de changement pour mettre à jour les informations
                    onArticleSelectionChange();
                    return;
                }
            } catch (error) {
                console.warn('⚠️ Erreur lors de l\'analyse des données article:', error);
            }
        }
    }
    
    console.warn('⚠️ Article non trouvé dans la liste pour référence:', reference);
}

// Fonction pour afficher les infos d'un article existant
function afficherInfosArticleExistant(articleCard) {
    // Chercher la référence dans la section des informations de l'article
    const referenceElement = articleCard.querySelector('.text-sm.text-gray-500');
    const reference = referenceElement ? referenceElement.textContent.replace('Réf: ', '').replace('Référence: ', '') : '';
    
    // Chercher le prix dans la section "Prix actuel"
    const prixElement = articleCard.querySelector('.text-center.min-w-0 .text-green-600, .text-center.min-w-0 .text-gray-600');
    const prixText = prixElement ? prixElement.textContent : '';
    
    // Chercher le sous-total
    const sousTotalElement = articleCard.querySelector('.text-lg.font-bold');
    const sousTotal = sousTotalElement ? sousTotalElement.textContent : '';
    
    // Informations de base (récupérées du DOM)
    const infoReference = document.getElementById('info-reference');
    const infoPrix = document.getElementById('info-prix');
    const infoSousTotal = document.getElementById('info-sous-total');
    
    if (infoReference) infoReference.textContent = reference;
    if (infoPrix) infoPrix.textContent = prixText;
    if (infoSousTotal) infoSousTotal.textContent = sousTotal;
    
    // Récupérer les caractéristiques depuis les badges
    const caracteristiques = extraireCaracteristiquesDepuisBadges(articleCard);
    
    
    const infoPointure = document.getElementById('info-pointure');
    const infoCouleur = document.getElementById('info-couleur');
    const infoCategorie = document.getElementById('info-categorie');
    
    if (infoPointure) infoPointure.textContent = caracteristiques.taille || 'Non spécifiée';
    if (infoCouleur) infoCouleur.textContent = caracteristiques.couleur || 'Non spécifiée';
    if (infoCategorie) infoCategorie.textContent = caracteristiques.categorie || 'Non spécifiée';
    
    // Mettre à jour les badges dans la modale
    mettreAJourBadgesModale(caracteristiques);
    
    // Récupérer le stock depuis le badge vert s'il existe
    const infoStock = document.getElementById('info-stock');
    const infoDescription = document.getElementById('info-description');
    
    if (caracteristiques.stock && infoStock) {
        infoStock.textContent = caracteristiques.stock;
    } else {
        // Essayer de récupérer depuis l'API
        chargerInfosCompletesArticle(reference);
    }
    
    if (infoDescription) infoDescription.textContent = caracteristiques.description || '';
    
  
    document.getElementById('article-info').classList.remove('hidden');
}

// Fonction pour extraire les caractéristiques depuis les badges de l'article
function extraireCaracteristiquesDepuisBadges(articleCard) {
    const caracteristiques = {
        taille: null,
        couleur: null,
        categorie: null,
        stock: null,
        description: ''
    };
    
    // Essayer d'abord de récupérer les données depuis le dataset de la carte
    try {
        const articleData = JSON.parse(articleCard.dataset.article || '{}');
        if (articleData && articleData.id) {

            // Récupérer les données directement depuis le dataset
            caracteristiques.taille = articleData.pointure || null;
            caracteristiques.couleur = articleData.couleur || null;
            caracteristiques.categorie = articleData.categorie || null;
            
            // Convertir le stock en nombre
            const stock = typeof articleData.qte_disponible === 'number' ? 
                          articleData.qte_disponible : 
                          (articleData.qte_disponible ? parseInt(articleData.qte_disponible) : 0);
            
            caracteristiques.stock = `Stock: ${stock}`;

            return caracteristiques;
        }
    } catch (error) {
        console.warn('⚠️ Erreur lors de la récupération des données depuis le dataset:', error);
        // Continuer avec la méthode des badges
    }
    
    // Chercher la section contenant les badges
    const badgesContainer = articleCard.querySelector('.flex.flex-wrap.gap-2');
    
    if (badgesContainer) {
        const badges = badgesContainer.querySelectorAll('span');
        
        badges.forEach(badge => {
            const badgeText = badge.textContent.trim();
            const icon = badge.querySelector('i');
            
            if (icon) {
                const iconClasses = icon.className;
                
                // Détecter le type selon l'icône
                if (iconClasses.includes('fa-ruler-vertical')) {
                    // Badge de taille - la valeur est directement dans le badge sans préfixe
                    if (!badgeText.includes('N/A')) {
                        caracteristiques.taille = badgeText.trim();
                    }
                } else if (iconClasses.includes('fa-palette')) {
                    // Badge de couleur - la valeur est directement dans le badge sans préfixe
                    if (!badgeText.includes('N/A')) {
                        caracteristiques.couleur = badgeText.trim();
                    }
                } else if (iconClasses.includes('fa-tag')) {
                    // Badge de catégorie - la valeur est directement dans le badge sans préfixe
                    if (!badgeText.includes('N/A')) {
                        caracteristiques.categorie = badgeText.trim();
                    }
                } else if (iconClasses.includes('fa-boxes')) {
                    // Badge de stock - garde le format complet "Stock: X"
                    caracteristiques.stock = badgeText.trim();
                }
            }
        });
        
  
        
        // Debug détaillé de chaque badge
        badges.forEach((badge, index) => {
            console.log(`Badge ${index + 1}:`, {
                text: badge.textContent.trim(),
                classes: badge.className,
                iconClasses: badge.querySelector('i')?.className || 'Pas d\'icône'
            });
        });
    } else {
        console.warn('⚠️ Conteneur de badges non trouvé pour cet article');
        
        // Fallback : essayer l'ancien format
        const oldInfoSection = articleCard.querySelector('.text-xs.text-gray-600');
        if (oldInfoSection) {
            const infoText = oldInfoSection.textContent;
            
            // Extraire avec regex de l'ancien format
            const tailleMatch = infoText.match(/Taille:\s*([^,\s]+)/i);
            const couleurMatch = infoText.match(/Couleur:\s*([^,\s]+)/i);
            const categorieMatch = infoText.match(/Catégorie:\s*([^,\s]+)/i);
            const stockMatch = infoText.match(/Stock:\s*(\d+)/i);
            
            if (tailleMatch) caracteristiques.taille = tailleMatch[1];
            if (couleurMatch) caracteristiques.couleur = couleurMatch[1];
            if (categorieMatch) caracteristiques.categorie = categorieMatch[1];
            if (stockMatch) caracteristiques.stock = `Stock: ${stockMatch[1]}`;
            
            console.log('🔄 Fallback vers ancien format utilisé');
        }
    }
    
    // Si aucun stock n'a été trouvé, mettre une valeur par défaut
    if (!caracteristiques.stock) {
        caracteristiques.stock = 'Stock: 0';
    }
    
    return caracteristiques;
}

// Fonction pour mettre à jour les badges de caractéristiques dans la modale
function mettreAJourBadgesModale(caracteristiques) {
    const badgesContainer = document.getElementById('caracteristiques-badges');
    
    if (!badgesContainer) {
        console.warn('⚠️ Conteneur de badges de la modale non trouvé (ID: caracteristiques-badges)');
        return;
    }
    
    // Vider le conteneur
    badgesContainer.innerHTML = '';
    
    // Créer un fragment pour améliorer les performances
    const fragment = document.createDocumentFragment();

    // Fonction pour créer un badge
    const createBadge = (text, iconClass, colorClass) => {
        if (!text) return;
        const badge = document.createElement('span');
        badge.className = `inline-flex items-center px-2.5 py-1 rounded-full text-xs font-medium ${colorClass}`;
        badge.innerHTML = `<i class="fas ${iconClass} mr-1.5"></i>${text}`;
        fragment.appendChild(badge);
    };

    // Ajouter les badges pour chaque caractéristique
    createBadge(caracteristiques.taille, 'fa-ruler-vertical', 'bg-purple-100 text-purple-800');
    createBadge(caracteristiques.couleur, 'fa-palette', 'bg-orange-100 text-orange-800');
    createBadge(caracteristiques.categorie, 'fa-tag', 'bg-indigo-100 text-indigo-800');
    
    // Badge Stock avec couleur selon la quantité
    if (caracteristiques.stock) {
        let stockValue = 0;
        const stockMatch = caracteristiques.stock.match(/-?\d+/); // Gère les nombres négatifs au cas où
        if (stockMatch) {
            stockValue = parseInt(stockMatch[0], 10);
        }
        
        if (stockValue <= 0) {
            createBadge('Stock épuisé', 'fa-times-circle', 'bg-red-100 text-red-800');
        } else if (stockValue < 10) {
            createBadge(`Stock: ${stockValue} (faible)`, 'fa-exclamation-triangle', 'bg-yellow-100 text-yellow-800');
    } else {
            createBadge(`${caracteristiques.stock}`, 'fa-check-circle', 'bg-green-100 text-green-800');
        }
    } else {
        createBadge('Stock inconnu', 'fa-question-circle', 'bg-gray-100 text-gray-800');
    }
    
    // Ajouter tous les badges au DOM en une seule fois
    badgesContainer.appendChild(fragment);
}

// Fonction pour charger les informations complètes d'un article par sa référence
function chargerInfosCompletesArticle(reference) {
    // Chercher l'article dans la liste déjà chargée
    if (articlesDisponibles && articlesDisponibles.length > 0) {
        const article = articlesDisponibles.find(a => a.reference === reference);
        if (article) {
            // Mettre à jour avec les informations complètes
            const infoPointure = document.getElementById('info-pointure');
            const infoCouleur = document.getElementById('info-couleur');
            const infoCategorie = document.getElementById('info-categorie');
            const infoStock = document.getElementById('info-stock');
            
            // Vérifier que qte_disponible est bien défini et convertir en nombre
            const stock = typeof article.qte_disponible === 'number' ? article.qte_disponible : 
                         (article.qte_disponible ? parseInt(article.qte_disponible) : 0);
            
            if (infoPointure) infoPointure.textContent = article.pointure || '-';
            if (infoCouleur) infoCouleur.textContent = article.couleur || '-';
            if (infoCategorie) infoCategorie.textContent = article.categorie || '-';
            if (infoStock) infoStock.textContent = `${stock} unité(s)`;
            
            return;
        }
    }
    
    // Si l'article n'est pas dans la liste, afficher des valeurs par défaut
    document.getElementById('info-pointure').textContent = '-';
    document.getElementById('info-couleur').textContent = '-';
    document.getElementById('info-categorie').textContent = '-';
    document.getElementById('info-stock').textContent = '0 unité(s)';
    
}
// Fonction pour charger les articles disponibles via API
function chargerArticlesDisponibles() {
    const select = document.getElementById('articleSelect');
    const tableBody = document.getElementById('articlesTableBody');
    if (!select || !tableBody) {
        console.error('❌ Élément articleSelect ou articlesTableBody introuvable');
        return;
    }
    // état de chargement
    tableBody.innerHTML = `<tr><td colspan="4" class="px-4 py-6 text-center text-gray-500">
        <i class="fas fa-spinner fa-spin mr-2"></i>Chargement des articles...
    </td></tr>`;
    select.innerHTML = '<option value="">-- Chargement des articles... --</option>';
    // Récupérer le token CSRF avec vérification
    const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]');
    if (!csrfToken) {
        console.error('❌ Token CSRF introuvable');
        select.innerHTML = '<option value="">-- Erreur: Token CSRF manquant --</option>';
        return;
    }
    
    // URL de l'API (les fichiers JS statiques ne sont pas traités par Django templates)
    // Utiliser le chemin absolu correspondant à l'URL déclarée dans operatConfirme/urls.py
    const apiUrl = '/operateur-confirme/api/articles-disponibles/';
    
    // Appel AJAX pour récupérer les articles
    fetch(apiUrl, {
        method: 'GET',
        headers: {
            'X-CSRFToken': csrfToken.value,
            'X-Requested-With': 'XMLHttpRequest',
        },
        credentials: 'same-origin',
    })
    .then(response => {
       
        
        if (!response.ok) {
            throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        }
        
        return response.json();
    })
    .then(data => {
        
        
        // Correction: La vue renvoie directement un tableau d'articles, pas un objet avec une propriété 'success'
        // Vérifier si data est un tableau ou un objet avec une propriété 'articles'
        if (Array.isArray(data)) {
            articlesDisponibles = data;
        } else if (data && data.articles) {
            articlesDisponibles = data.articles;
        } else {
            articlesDisponibles = [];
        }
        
        // Remplir le select (compatibilité) et le tableau (nouveau rendu)
        select.innerHTML = '<option value="">-- Sélectionner un article --</option>';
        tableBody.innerHTML = '';
        
        if (articlesDisponibles.length === 0) {
            select.innerHTML = '<option value="">-- Aucun article disponible --</option>';
            tableBody.innerHTML = `<tr><td colspan="4" class="px-4 py-6 text-center text-gray-500">Aucun article disponible</td></tr>`;
            console.warn('⚠️ Aucun article trouvé dans la base de données');
            showNotification('⚠️ Aucun article disponible', 'error');
            return;
        }
        
        articlesDisponibles.forEach((article, index) => {
            try {
                const option = document.createElement('option');
                option.value = article.id;
                
                // Construire un texte plus informatif avec vérifications
                let optionText = article.nom || 'Article sans nom';
                
                // Ajouter les badges de statut AVANT le prix
                const badges = [];
                
                // Vérifier les différents statuts
                if (article.has_promo_active) {
                    badges.push('🔥PROMO');
                }
                if (article.phase === 'LIQUIDATION') {
                    badges.push('🏷️LIQUIDATION');
                }
                if (article.phase === 'EN_TEST') {
                    badges.push('🧪TEST');
                }
                if (article.isUpsell) {
                    badges.push('⬆️UPSELL');
                }
                
                // Ajouter les badges au nom
                if (badges.length > 0) {
                    optionText += ` [${badges.join(' ')}]`;
                }
                
                if (article.prix_actuel) {
                    optionText += ` - ${article.prix_actuel} DH`;
                }
                
                // Ajouter taille et couleur si disponibles
                const details = [];
                if (article.pointure && article.pointure.trim()) {
                    details.push(`T:${article.pointure}`);
                }
                if (article.couleur && article.couleur.trim()) {
                    details.push(`C:${article.couleur}`);
                }
                
                if (details.length > 0) {
                    optionText += ` (${details.join(', ')})`;
                }
                
                option.textContent = optionText;
                option.dataset.article = JSON.stringify(article);
                
                // Ajouter des classes CSS pour styliser selon le type
                if (article.has_promo_active) {
                    option.style.backgroundColor = '#fef2f2';
                    option.style.color = '#dc2626';
                    option.style.fontWeight = 'bold';
                } else if (article.phase === 'LIQUIDATION') {
                    option.style.backgroundColor = '#fff7ed';
                    option.style.color = '#ea580c';
                    option.style.fontWeight = 'bold';
                } else if (article.phase === 'EN_TEST') {
                    option.style.backgroundColor = '#eff6ff';
                    option.style.color = '#2563eb';
                    option.style.fontWeight = 'bold';
                } else if (article.isUpsell) {
                    option.style.backgroundColor = '#f0fdf4';
                    option.style.color = '#16a34a';
                    option.style.fontWeight = 'bold';
                }
                
                select.appendChild(option);

                // Ligne du tableau
                const tr = document.createElement('tr');
                tr.dataset.article = JSON.stringify(article);

                // Déterminer classes de fond/texte selon type pour garder les mêmes couleurs
                let rowBg = '';
                let badgeHtml = '';
                if (article.has_promo_active) {
                    rowBg = 'bg-red-50';
                    badgeHtml += '<span class="inline-flex items-center px-2 py-0.5 bg-red-100 text-red-700 rounded-full text-xs font-semibold mr-2"><i class="fas fa-fire mr-1"></i>PROMO</span>';
                }
                if (article.phase === 'LIQUIDATION') {
                    rowBg = 'bg-orange-50';
                    badgeHtml += '<span class="inline-flex items-center px-2 py-0.5 bg-orange-100 text-orange-700 rounded-full text-xs font-semibold mr-2"><i class="fas fa-tags mr-1"></i>LIQUIDATION</span>';
                }
                if (article.phase === 'EN_TEST') {
                    rowBg = 'bg-blue-50';
                    badgeHtml += '<span class="inline-flex items-center px-2 py-0.5 bg-blue-100 text-blue-700 rounded-full text-xs font-semibold mr-2"><i class="fas fa-flask mr-1"></i>TEST</span>';
                }
                if (article.isUpsell) {
                    rowBg = 'bg-green-50';
                    badgeHtml += '<span class="inline-flex items-center px-2 py-0.5 bg-green-100 text-green-700 rounded-full text-xs font-semibold mr-2"><i class="fas fa-arrow-up mr-1"></i>UPSELL</span>';
                }
                tr.className = rowBg;

                const prixActuel = (typeof article.prix_actuel === 'number' ? article.prix_actuel : (article.prix_unitaire || 0));
                const stock = (typeof article.qte_disponible === 'number' ? article.qte_disponible : (parseInt(article.qte_disponible || '0') || 0));

                tr.innerHTML = `
                    <td class="px-4 py-3">
                        <div class="flex items-start space-x-4">
                            <!-- Image de l'article -->
                            <div class="flex-shrink-0">
                                <div class="w-16 h-16 rounded-lg overflow-hidden bg-gray-100 border-2 border-gray-200 shadow-sm hover:shadow-md transition-shadow">
                                    ${article.image_url ? 
                                        `<img src="${article.image_url}" alt="Image de ${article.nom}" class="w-full h-full object-cover hover:scale-105 transition-transform duration-200" onerror="this.style.display='none'; this.nextElementSibling.style.display='flex';">` : 
                                        ''
                                    }
                                    <div class="w-full h-full flex items-center justify-center text-gray-400 ${article.image_url ? 'hidden' : ''}">
                                        <i class="fas fa-image text-xl"></i>
                                    </div>
                                </div>
                            </div>
                            
                            <!-- Informations de l'article -->
                            <div class="flex-1 min-w-0">
                                <div class="font-medium text-gray-900">${article.nom || ''}</div>
                                <div class="text-xs text-gray-500">Réf: ${article.reference || '-'}</div>
                                <div class="mt-1">${badgeHtml}</div>
                                <div class="mt-1 flex flex-wrap gap-2 text-xs">
                                    ${typeof article.categorie === 'string' ? `<span class="px-2 py-0.5 bg-indigo-100 text-indigo-700 rounded-full"><i class=\"fas fa-tag mr-1\"></i>${article.categorie}</span>` : ''}
                                </div>
                            </div>
                        </div>
                    </td>
                    <td class="px-1 py-3 text-center">
                        <div class="text-sm font-semibold text-gray-900">${prixActuel} DH</div>
                    </td>
                    <td class="px-1 py-3 text-center">
                        <span class="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium ${stock <= 0 ? 'bg-red-100 text-red-800' : (stock < 5 ? 'bg-orange-100 text-orange-800' : 'bg-green-100 text-green-800')}">
                            ${stock <= 0 ? 'Épuisé' : stock + ' unités'}
                        </span>
                    </td>
                    <td class="px-1 py-3 text-center">
                        <button type="button" class="inline-flex items-center px-3 py-1.5 rounded-full text-xs font-medium transition-colors bg-purple-100 text-purple-700 hover:bg-purple-200" onclick="ajouterDepuisLigne(this)">
                            🎨 Ajouter
                        </button>
                    </td>
                `;
                tableBody.appendChild(tr);
                
               
                
            } catch (error) {
                console.error(`❌ Erreur lors de l'ajout de l'article ${index + 1}:`, error, article);
            }
        });
 
        // Debug des premiers articles pour vérifier les données
        if (articlesDisponibles.length > 0) {
            console.log('🔍 DEBUG: Premier article chargé:', articlesDisponibles[0]);
            console.log('🔍 DEBUG: Champs disponibles:', Object.keys(articlesDisponibles[0]));
        }
        
        // Sauvegarder dans la variable globale
        window.articlesDisponibles = articlesDisponibles;
        
        showNotification(`✅ ${articlesDisponibles.length} article(s) chargé(s)`, 'success');
        
        // Mettre à jour les compteurs des badges si la fonction est disponible
        if (typeof mettreAJourCompteursFiltre === 'function') {
            mettreAJourCompteursFiltre();
        } else {
            console.warn('⚠️ Fonction mettreAJourCompteursFiltre indisponible au moment de l\'appel');
        }
        
        // Réinitialiser la scrollbar après le chargement des articles
        //reinitScrollbarAfterArticlesLoad();
    })
    .catch(error => {
        select.innerHTML = '<option value="">-- Erreur de connexion --</option>';
        if (tableBody) {
            tableBody.innerHTML = `<tr><td colspan="4" class="px-4 py-6 text-center text-red-600 bg-red-50">Erreur de connexion</td></tr>`;
        }
        console.error('❌ Erreur AJAX complète:', error);
        
        // Messages d'erreur plus spécifiques
        let errorMessage = 'Erreur de connexion';
        if (error.message.includes('403')) {
            errorMessage = 'Accès refusé - Vérifiez vos permissions';
        } else if (error.message.includes('404')) {
            errorMessage = 'API introuvable - Vérifiez l\'URL';
        } else if (error.message.includes('500')) {
            errorMessage = 'Erreur serveur - Vérifiez les logs Django';
        }
        
        showNotification(`❌ ${errorMessage}`, 'error');
    });
}



// ===== Fonctions utilitaires pour le tableau d'articles (nouvelle UI) =====

function ajouterDepuisLigne(button) {
    try {
        const tr = button.closest('tr');
        if (!tr) return;
        const article = JSON.parse(tr.dataset.article || '{}');
        
        // Ouvrir le modal de sélection des variantes
        ouvrirModalVariantes(article);
    } catch (e) {
        showToast('Erreur lors de l\'ouverture du modal de variantes', 'error');
    }
}

function rechercherArticles(terme) {
    const value = (terme || '').toString().toLowerCase();
    const rows = document.querySelectorAll('#articlesTableBody tr');
    rows.forEach(row => {
        try {
            const article = JSON.parse(row.dataset.article || '{}');
            const cible = [article.nom, article.reference, article.couleur, article.pointure, article.categorie]
                .filter(Boolean)
                .join(' ')
                .toLowerCase();
            row.style.display = !value || cible.includes(value) ? '' : 'none';
        } catch (_) {}
    });
}

function fermerModalAjouterArticle() {
    const modal = document.getElementById('articleModal');
    if (modal) {
        modal.style.display = 'none';
        modal.classList.add('hidden');
        modal.classList.remove('flex');
    }
}

// ===== Gestion du modal des variantes =====
function ouvrirModalVariantes(article) {
    try {
        // Vérifier que l'article a un ID valide
        if (!article || !article.id) {
            showToast('❌ Erreur: Article invalide', 'error');
            return;
        }
        
        // Fermer le modal "Ajouter un article" s'il est ouvert
        fermerModalAjouterArticle();
        
        // Mettre à jour les informations de l'article
        document.getElementById('articleNom').textContent = article.nom || 'Article';
        document.getElementById('articleReference').textContent = `Réf: ${article.reference || ''}`;
        
        // Réinitialiser l'état du modal AVANT de définir l'article
        reinitialiserModalVariantes();
        
        // Stocker l'article actuel APRÈS la réinitialisation
        window.currentArticle = article;
        console.log('🔍 DEBUG ouvrirModalVariantes - window.currentArticle défini:', window.currentArticle);
        
        // Charger les variantes de l'article
        chargerVariantesArticle(article);
        
        // Afficher le modal
        const modal = document.getElementById('variantModal');
        if (modal) {
            modal.style.display = 'flex';
            modal.classList.remove('hidden');
            modal.classList.add('flex');
        }
    } catch (e) {
        console.error('❌ Erreur ouverture modal variantes:', e);
        showToast('❌ Erreur lors de l\'ouverture du modal', 'error');
    }
}

function fermerModalVariantes(event) {
    if (event) {
        event.preventDefault();
        event.stopPropagation();
    }
    console.log('🔍 DEBUG fermerModalVariantes - avant nettoyage, window.currentArticle:', window.currentArticle);
    
    const modal = document.getElementById('variantModal');
    if (modal) {
        modal.style.display = 'none';
        modal.classList.add('hidden');
        modal.classList.remove('flex');
    }
    
    // Réinitialiser les informations des variantes sélectionnées
    const selectedVariantsInfo = document.getElementById('selectedVariantsInfo');
    const addSelectedVariantsBtn = document.getElementById('addSelectedVariantsBtn');
    const clearSelectionBtn = document.getElementById('clearSelectionBtn');
    
    if (selectedVariantsInfo) selectedVariantsInfo.classList.add('hidden');
    if (addSelectedVariantsBtn) addSelectedVariantsBtn.classList.add('hidden');
    if (clearSelectionBtn) clearSelectionBtn.classList.add('hidden');
    
    // Nettoyer les variables globales
    window.selectedVariants = [];
    window.currentArticle = null;
    window.variantsData = null;
    console.log('🔍 DEBUG fermerModalVariantes - après nettoyage, window.currentArticle:', window.currentArticle);
}

function reinitialiserModalVariantes() {
    // Réinitialiser les informations des variantes sélectionnées
    const selectedVariantsInfo = document.getElementById('selectedVariantsInfo');
    const addSelectedVariantsBtn = document.getElementById('addSelectedVariantsBtn');
    const clearSelectionBtn = document.getElementById('clearSelectionBtn');
    
    if (selectedVariantsInfo) selectedVariantsInfo.classList.add('hidden');
    if (addSelectedVariantsBtn) addSelectedVariantsBtn.classList.add('hidden');
    if (clearSelectionBtn) clearSelectionBtn.classList.add('hidden');
    
    // Nettoyer les variables globales
    window.selectedVariants = [];
    window.currentArticle = null;
    window.variantsData = null;
}

function chargerVariantesArticle(article) {
    try {
        const variantsTableContainer = document.getElementById('variantsTableContainer');
        if (!variantsTableContainer) return;
        
        
        
        if (!article.id) {
            console.error('❌ ID d\'article manquant');
            variantsTableContainer.innerHTML = '<div class="text-center py-4 text-red-500">❌ ID d\'article manquant</div>';
            return;
        }
        
        variantsTableContainer.innerHTML = '<div class="text-center py-4"><i class="fas fa-spinner fa-spin mr-2"></i>Chargement des variantes...</div>';
        
        const url = `/operateur-confirme/get-article-variants/${article.id}/`;
        console.log('📡 URL de requête:', url);
        
        // Faire une requête AJAX pour récupérer les variantes
        fetch(url)
            .then(response => {
                return response.json();
            })
            .then(data => {
               
                if (data.success && data.variants) {
                    
                    afficherVariantes(data.variants, article);
                } else {
                    console.log('❌ Aucune variante ou erreur:', data.error);
                    variantsTableContainer.innerHTML = '<div class="text-center py-4 text-gray-500">Aucune variante disponible</div>';
                }
            })
            .catch(error => {
                console.error('❌ Erreur chargement variantes:', error);
                variantsTableContainer.innerHTML = '<div class="text-center py-4 text-red-500"><i class="fas fa-exclamation-triangle mr-2"></i>Erreur lors du chargement</div>';
            });
    } catch (e) {
        console.error('❌ Erreur chargerVariantesArticle:', e);
    }
}

function afficherVariantes(variants, article) {
    const variantsTableContainer = document.getElementById('variantsTableContainer');
    if (!variantsTableContainer) return;
    
    if (variants.length === 0) {
        variantsTableContainer.innerHTML = '<div class="text-center py-4 text-gray-500">Aucune variante disponible</div>';
        return;
    }
    
    // Analyser les variantes pour créer le tableau croisé
    const { tableHtml, variantMap } = creerTableauCroise(variants);
    variantsTableContainer.innerHTML = tableHtml;
    
    // Stocker les données des variantes pour la sélection
    window.variantsData = variantMap;
    // window.currentArticle est déjà défini dans ouvrirModalVariantes
    
    // Ajouter les event listeners pour les checkboxes
    ajouterEventListenersCheckboxes();
}
function creerTableauCroise(variants) {
    // Extraire les valeurs uniques pour chaque attribut
    const couleurs = [...new Set(variants.map(v => v.couleur).filter(Boolean))];
    const pointures = [...new Set(variants.map(v => v.pointure).filter(Boolean))];
    const tailles = [...new Set(variants.map(v => v.taille).filter(Boolean))];
    
    // Déterminer les dimensions du tableau
    let dimension1, dimension2, valeurs1, valeurs2;
    
    if (couleurs.length > 0 && pointures.length > 0) {
        dimension1 = 'couleur';
        dimension2 = 'pointure';
        valeurs1 = couleurs;
        valeurs2 = pointures;
    } else if (couleurs.length > 0 && tailles.length > 0) {
        dimension1 = 'couleur';
        dimension2 = 'taille';
        valeurs1 = couleurs;
        valeurs2 = tailles;
    } else if (pointures.length > 0 && tailles.length > 0) {
        dimension1 = 'pointure';
        dimension2 = 'taille';
        valeurs1 = pointures;
        valeurs2 = tailles;
    } else if (couleurs.length > 0) {
        // Seulement des couleurs
        dimension1 = 'couleur';
        dimension2 = null;
        valeurs1 = couleurs;
        valeurs2 = [];
    } else if (pointures.length > 0) {
        // Seulement des pointures
        dimension1 = 'pointure';
        dimension2 = null;
        valeurs1 = pointures;
        valeurs2 = [];
    } else if (tailles.length > 0) {
        // Seulement des tailles
        dimension1 = 'taille';
        dimension2 = null;
        valeurs1 = tailles;
        valeurs2 = [];
    } else {
        // Aucune dimension claire, afficher en liste simple
        return creerListeSimple(variants);
    }
    
    // Créer une map pour accéder rapidement aux variantes
    const variantMap = {};
    
    // Si on n'a qu'une dimension, créer un tableau simple
    if (!dimension2) {
        return creerTableauSimple(variants, dimension1, valeurs1, variantMap);
    }
    
    let tableHtml = `
        <div class="overflow-x-auto">
            <table class="min-w-full border border-gray-200 rounded-lg overflow-hidden">
                <thead>
                    <tr>
                        <th class="px-4 py-3 text-left text-sm font-semibold text-gray-700 border-b border-gray-200 bg-gray-50">
                            ${dimension1.charAt(0).toUpperCase() + dimension1.slice(1)} / ${dimension2.charAt(0).toUpperCase() + dimension2.slice(1)}
                        </th>
    `;
    
    // En-têtes de colonnes
    valeurs2.forEach(val2 => {
        tableHtml += `
            <th class="px-4 py-3 text-center text-sm font-semibold text-gray-700 border-b border-gray-200 bg-gray-50">
                ${val2 || 'N/A'}
            </th>
        `;
    });
    
    tableHtml += '</tr></thead><tbody>';
    
    // Lignes du tableau
    valeurs1.forEach(val1 => {
        tableHtml += `
            <tr class="border-b border-gray-100">
                <td class="px-4 py-3 text-sm font-medium text-gray-900 bg-gray-50">
                    ${val1 || 'N/A'}
                </td>
        `;
        
        valeurs2.forEach(val2 => {
            // Trouver la variante correspondante
            const variant = variants.find(v => {
                const v1 = dimension1 === 'couleur' ? v.couleur : (dimension1 === 'pointure' ? v.pointure : v.taille);
                const v2 = dimension2 === 'couleur' ? v.couleur : (dimension2 === 'pointure' ? v.pointure : v.taille);
                return v1 === val1 && v2 === val2;
            });
            
            if (variant) {
                const stockClass = variant.stock > 0 ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800';
                const stockText = variant.stock > 0 ? `${variant.stock} unité${variant.stock > 1 ? 's' : ''}` : 'Rupture';
                const checkboxDisabled = variant.stock <= 0 ? 'disabled' : '';
                
                // Créer une clé unique pour cette variante
                const variantKey = `${variant.id}`;
                variantMap[variantKey] = variant;
                
                tableHtml += `
                    <td class="px-4 py-3 text-center border-l border-gray-100 bg-white">
                        <div class="space-y-2">
                            <div class="text-lg font-bold text-green-600">${variant.prix_actuel} DH</div>
                            <div class="px-2 py-1 rounded-full text-xs font-semibold ${stockClass}">
                                ${stockText}
                            </div>
                            <label class="flex items-center justify-center cursor-pointer ${variant.stock > 0 ? '' : 'opacity-50 cursor-not-allowed'}">
                                <input type="checkbox" name="variantSelection" value="${variantKey}" 
                                       id="variant_${variantKey}" class="variant-checkbox w-5 h-5 text-blue-600 bg-gray-100 border-gray-300 rounded focus:ring-blue-500 focus:ring-2" ${checkboxDisabled}
                                       onchange="selectionnerVarianteFromTable('${variantKey}', this.checked)">
                            </label>
                        </div>
                    </td>
                `;
            } else {
                tableHtml += `
                    <td class="px-4 py-3 text-center border-l border-gray-100 text-gray-400 bg-white">-</td>
                `;
            }
        });
        
        tableHtml += '</tr>';
    });
    
    tableHtml += '</tbody></table></div>';
    
    return { tableHtml, variantMap };
}

function creerTableauSimple(variants, dimension, valeurs, variantMap) {
    let tableHtml = `
        <div class="overflow-x-auto">
            <table class="min-w-full border border-gray-200 rounded-lg overflow-hidden">
                <thead>
                    <tr>
                        <th class="px-4 py-3 text-left text-sm font-semibold text-gray-700 border-b border-gray-200 bg-gray-50">${dimension.charAt(0).toUpperCase() + dimension.slice(1)}</th>
                        <th class="px-4 py-3 text-center text-sm font-semibold text-gray-700 border-b border-gray-200 bg-gray-50">Prix</th>
                        <th class="px-4 py-3 text-center text-sm font-semibold text-gray-700 border-b border-gray-200 bg-gray-50">Stock</th>
                        <th class="px-4 py-3 text-center text-sm font-semibold text-gray-700 border-b border-gray-200 bg-gray-50">Sélection</th>
                    </tr>
                </thead>
                <tbody>
    `;
    
    valeurs.forEach(val => {
        const variant = variants.find(v => {
            const v1 = dimension === 'couleur' ? v.couleur : (dimension === 'pointure' ? v.pointure : v.taille);
            return v1 === val;
        });
        
        if (variant) {
            const stockClass = variant.stock > 0 ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800';
            const stockText = variant.stock > 0 ? `${variant.stock} unité${variant.stock > 1 ? 's' : ''}` : 'Rupture';
            const checkboxDisabled = variant.stock <= 0 ? 'disabled' : '';
            
            const variantKey = `${variant.id}`;
            variantMap[variantKey] = variant;
            
            tableHtml += `
                <tr class="border-b border-gray-100">
                    <td class="px-4 py-3 text-sm font-medium text-gray-900 bg-white">${val || 'N/A'}</td>
                    <td class="px-4 py-3 text-center text-lg font-bold text-green-600 bg-white">${variant.prix_unitaire} DH</td>
                    <td class="px-4 py-3 text-center ${stockClass} bg-white">${stockText}</td>
                    <td class="px-4 py-3 text-center bg-white">
                        <input type="checkbox" name="variantSelection" value="${variantKey}" 
                               id="variant_${variantKey}" class="variant-checkbox w-5 h-5 text-blue-600 bg-gray-100 border-gray-300 rounded focus:ring-blue-500 focus:ring-2" ${checkboxDisabled}
                               onchange="selectionnerVarianteFromTable('${variantKey}', this.checked)">
                    </td>
                </tr>
            `;
        }
    });
    
    tableHtml += '</tbody></table></div>';
    return { tableHtml, variantMap };
}

function creerListeSimple(variants) {
    const variantMap = {};
    
    let tableHtml = `
        <div class="overflow-x-auto">
            <table class="min-w-full border border-gray-200 rounded-lg overflow-hidden">
                <thead>
                    <tr>
                        <th class="px-4 py-3 text-left text-sm font-semibold text-gray-700 border-b border-gray-200 bg-gray-50">Variante</th>
                        <th class="px-4 py-3 text-center text-sm font-semibold text-gray-700 border-b border-gray-200 bg-gray-50">Prix</th>
                        <th class="px-4 py-3 text-center text-sm font-semibold text-gray-700 border-b border-gray-200 bg-gray-50">Stock</th>
                        <th class="px-4 py-3 text-center text-sm font-semibold text-gray-700 border-b border-gray-200 bg-gray-50">Sélection</th>
                    </tr>
                </thead>
                <tbody>
    `;
    
    variants.forEach((variant, index) => {
        const stockClass = variant.stock > 0 ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800';
        const stockText = variant.stock > 0 ? `${variant.stock} unité${variant.stock > 1 ? 's' : ''}` : 'Rupture';
        const checkboxDisabled = variant.stock <= 0 ? 'disabled' : '';
        
        const variantKey = `${variant.id}`;
        variantMap[variantKey] = variant;
        
        const variantInfo = [
            variant.couleur ? `Couleur: ${variant.couleur}` : '',
            variant.pointure ? `Pointure: ${variant.pointure}` : '',
            variant.taille ? `Taille: ${variant.taille}` : ''
        ].filter(Boolean).join(' | ');
        
        tableHtml += `
            <tr class="border-b border-gray-100">
                <td class="px-4 py-3 text-sm font-medium text-gray-900 bg-white">${variantInfo || 'Variante ' + (index + 1)}</td>
                <td class="px-4 py-3 text-center text-lg font-bold text-green-600 bg-white">${variant.prix_unitaire} DH</td>
                <td class="px-4 py-3 text-center ${stockClass} bg-white">${stockText}</td>
                <td class="px-4 py-3 text-center bg-white">
                    <input type="checkbox" name="variantSelection" value="${variantKey}" 
                           id="variant_${variantKey}" class="variant-checkbox w-5 h-5 text-blue-600 bg-gray-100 border-gray-300 rounded focus:ring-blue-500 focus:ring-2" ${checkboxDisabled}
                           onchange="selectionnerVarianteFromTable('${variantKey}', this.checked)">
                </td>
            </tr>
        `;
    });
    
    tableHtml += '</tbody></table></div>';
    return { tableHtml, variantMap };
}


function ajouterEventListenersCheckboxes() {
    const checkboxes = document.querySelectorAll('.variant-checkbox');
    checkboxes.forEach(checkbox => {
        checkbox.addEventListener('change', function() {
            // Pas besoin de décocher les autres pour les checkboxes multiples
            // La logique est gérée dans selectionnerVarianteFromTable
        });
    });
}

function selectionnerVarianteFromTable(variantKey, isChecked) {
    if (!window.variantsData || !window.variantsData[variantKey]) {
        console.error('❌ Variante non trouvée:', variantKey);
        return;
    }
    
    const variant = window.variantsData[variantKey];
    
    // Initialiser le tableau des variantes sélectionnées s'il n'existe pas
    if (!window.selectedVariants) {
        window.selectedVariants = [];
    }
    
    if (isChecked) {
        // Ajouter la variante à la sélection
        if (!window.selectedVariants.find(v => v.id === variant.id)) {
            window.selectedVariants.push(variant);
        }
    } else {
        // Retirer la variante de la sélection
        window.selectedVariants = window.selectedVariants.filter(v => v.id !== variant.id);
    }
    
    // Mettre à jour l'affichage des informations
    mettreAJourAffichageVariantesSelectionnees();
    
    // Afficher un message de confirmation
    if (isChecked) {
        showToast(`✅ Variante ajoutée à la sélection (${window.selectedVariants.length} sélectionnée(s))`, 'success');
    } else {
        showToast(`🔄 Variante retirée de la sélection (${window.selectedVariants.length} sélectionnée(s))`, 'info');
    }
}

function mettreAJourAffichageVariantesSelectionnees() {
    const selectedVariantsInfo = document.getElementById('selectedVariantsInfo');
    const selectedVariantsDetails = document.getElementById('selectedVariantsDetails');
    const addSelectedVariantsBtn = document.getElementById('addSelectedVariantsBtn');
    const clearSelectionBtn = document.getElementById('clearSelectionBtn');
    
    if (!selectedVariantsInfo || !selectedVariantsDetails || !addSelectedVariantsBtn || !clearSelectionBtn) {
        return;
    }
    
    if (window.selectedVariants && window.selectedVariants.length > 0) {
        // Afficher les informations des variantes sélectionnées
        let details = `<div class="mb-3"><strong>${window.selectedVariants.length} variante(s) sélectionnée(s):</strong></div>`;
        
        window.selectedVariants.forEach((variant, index) => {
            const stockStatus = variant.stock > 0 ? 
                `<span class="text-green-600">${variant.stock} en stock</span>` : 
                '<span class="text-red-600">Rupture</span>';
            
            details += `
                <div class="border-l-4 border-blue-200 pl-3 mb-2 ${index > 0 ? 'mt-3' : ''}">
                    <div class="font-medium">Variante ${index + 1}</div>
                    <div class="text-sm text-gray-600">
                        <strong>Prix:</strong> ${variant.prix_unitaire} DH | 
                        <strong>Stock:</strong> ${stockStatus}
                    </div>
                    <div class="text-xs text-gray-500">
                        ${variant.couleur ? `Couleur: ${variant.couleur} | ` : ''}
                        ${variant.pointure ? `Pointure: ${variant.pointure} | ` : ''}
                        ${variant.taille ? `Taille: ${variant.taille}` : ''}
                    </div>
                </div>
            `;
        });
        
        selectedVariantsDetails.innerHTML = details;
        selectedVariantsInfo.classList.remove('hidden');
        addSelectedVariantsBtn.classList.remove('hidden');
        clearSelectionBtn.classList.remove('hidden');
        
        // Mettre à jour le texte du bouton d'ajout
        addSelectedVariantsBtn.innerHTML = `<i class="fas fa-plus mr-2"></i>Ajouter ${window.selectedVariants.length} variante(s)`;
    } else {
        // Masquer les informations si aucune variante n'est sélectionnée
        selectedVariantsInfo.classList.add('hidden');
        addSelectedVariantsBtn.classList.add('hidden');
        clearSelectionBtn.classList.add('hidden');
    }
}

function effacerSelectionVariantes(event) {
    if (event) {
        event.preventDefault();
        event.stopPropagation();
    }
    // Décocher tous les checkboxes
    const checkboxes = document.querySelectorAll('.variant-checkbox');
    checkboxes.forEach(cb => cb.checked = false);
    
    // Masquer les informations des variantes sélectionnées
    const selectedVariantsInfo = document.getElementById('selectedVariantsInfo');
    const addSelectedVariantsBtn = document.getElementById('addSelectedVariantsBtn');
    const clearSelectionBtn = document.getElementById('clearSelectionBtn');
    
    if (selectedVariantsInfo) selectedVariantsInfo.classList.add('hidden');
    if (addSelectedVariantsBtn) addSelectedVariantsBtn.classList.add('hidden');
    if (clearSelectionBtn) clearSelectionBtn.classList.add('hidden');
    
    // Nettoyer la variante sélectionnée
    window.selectedVariants = [];
    
    showToast('🔄 Sélection effacée', 'info');
}

function ajouterVariantesSelectionnees(event) {
    if (event) {
        event.preventDefault();
        event.stopPropagation();
    }
    console.log('🔍 DEBUG ajouterVariantesSelectionnees - window.currentArticle:', window.currentArticle);
    console.log('🔍 DEBUG ajouterVariantesSelectionnees - window.selectedVariants:', window.selectedVariants);
    
    if (!window.selectedVariants || window.selectedVariants.length === 0) {
        showToast('❌ Aucune variante sélectionnée', 'error');
        return;
    }
    
    if (!window.currentArticle) {
        console.error('❌ Article parent non trouvé - window.currentArticle est:', window.currentArticle);
        console.error('🔍 DEBUG - Toutes les variables globales:');
        console.error('  - window.selectedVariants:', window.selectedVariants);
        console.error('  - window.variantsData:', window.variantsData);
        showToast('❌ Erreur: Article parent non trouvé', 'error');
        return;
    }
    
    try {
        // Ajouter chaque variante sélectionnée
        let ajoutees = 0;
        window.selectedVariants.forEach(variant => {
            try {
                // Créer un article combiné avec les données de la variante
                const articleAvecVariante = {
                    ...window.currentArticle,
                    ...variant,
                    id: variant.id,
                    article_id: window.currentArticle.id,  // ID de l'article parent
                    variante_id: variant.id, // ID de la variante
                    prix_actuel: variant.prix_unitaire,
                    prix_unitaire: variant.prix_unitaire,
                    stock_disponible: variant.stock
                };
                
                // Utiliser la logique existante pour ajouter l'article
                const hiddenSelect = document.getElementById('articleSelect');
                if (!hiddenSelect) return;
                
                hiddenSelect.value = variant.id;
                const qteInput = document.getElementById('quantiteInput');
                if (qteInput) qteInput.value = '1';
                
                // Créer ou mettre à jour l'option dans le select
                let opt = Array.from(hiddenSelect.options).find(o => String(o.value) === String(variant.id));
                if (!opt) {
                    opt = new Option('', variant.id);
                    hiddenSelect.appendChild(opt);
                }
                opt.dataset.article = JSON.stringify(articleAvecVariante);
                hiddenSelect.selectedIndex = opt.index;
                
                afficherInfosArticle(articleAvecVariante);
                isEditingArticle = false;
                saveArticle();
                
                ajoutees++;
                
            } catch (e) {
                console.error('❌ Erreur ajout variante individuelle:', e);
            }
        });
        
        if (ajoutees > 0) {
            showToast(`✅ ${ajoutees} variante(s) ajoutée(s) avec succès`, 'success');
        } else {
            showToast('❌ Aucune variante n\'a pu être ajoutée', 'error');
        }
        
        // Fermer le modal des variantes après le traitement
        fermerModalVariantes();
        
        // Nettoyer les variables globales
        window.selectedVariants = [];
        window.currentArticle = null;
        window.variantsData = null;
        
    } catch (e) {
        console.error('❌ Erreur ajout variantes:', e);
        showToast('❌ Erreur lors de l\'ajout des variantes', 'error');
    }
}

function selectionnerVariante(variant, article) {
    try {
        // Fermer le modal des variantes
        fermerModalVariantes();
        
        // Créer un article combiné avec les données de la variante
        const articleAvecVariante = {
            ...article,
            ...variant,
            id: variant.id,
            article_id: article.id,  // ID de l'article parent
            variante_id: variant.id, // ID de la variante
            prix_actuel: variant.prix_unitaire,
            prix_unitaire: variant.prix_unitaire,
            stock_disponible: variant.stock
        };
        
        // Utiliser la logique existante pour ajouter l'article
        const hiddenSelect = document.getElementById('articleSelect');
        if (!hiddenSelect) return;
        
        hiddenSelect.value = variant.id;
        const qteInput = document.getElementById('quantiteInput');
        if (qteInput) qteInput.value = '1';
        
        // Créer ou mettre à jour l'option dans le select
        let opt = Array.from(hiddenSelect.options).find(o => String(o.value) === String(variant.id));
        if (!opt) {
            opt = new Option('', variant.id);
            hiddenSelect.appendChild(opt);
        }
        opt.dataset.article = JSON.stringify(articleAvecVariante);
        hiddenSelect.selectedIndex = opt.index;
        
        afficherInfosArticle(articleAvecVariante);
        isEditingArticle = false;
        saveArticle();
        
        showToast('✅ Variante ajoutée avec succès', 'success');
    } catch (e) {
        console.error('❌ Erreur sélection variante:', e);
        showToast('❌ Erreur lors de la sélection de la variante', 'error');
    }
}

function rechercherArticlesPourVariantes(terme) {
    try {
        if (!terme || terme.length < 2) {
            document.getElementById('resultatsRechercheVariantes').innerHTML = '';
            return;
        }
        
        const resultatsDiv = document.getElementById('resultatsRechercheVariantes');
        resultatsDiv.innerHTML = '<div class="text-center py-4"><i class="fas fa-spinner fa-spin mr-2"></i>Recherche en cours...</div>';
        
        // Utiliser la même API que pour la recherche normale d'articles (chemin app: operateur-confirme)
        fetch(`/operateur-confirme/api/articles-disponibles/?q=${encodeURIComponent(terme)}`)
            .then(response => response.json())
            .then(data => {
                if (data.articles && data.articles.length > 0) {
                    const articlesHtml = data.articles.slice(0, 5).map(article => `
                        <div class="border rounded-lg p-4 hover:bg-gray-50 cursor-pointer mb-3" onclick="ouvrirModalVariantes(${JSON.stringify(article).replace(/"/g, '&quot;')})">
                            <div class="flex justify-between items-center">
                                <div class="flex-1">
                                    <h5 class="font-medium text-gray-900">${article.nom}</h5>
                                    <p class="text-sm text-gray-600">Réf: ${article.reference || 'N/A'}</p>
                                    <div class="flex gap-2 mt-2">
                                        ${article.couleur ? `<span class="px-2 py-1 bg-purple-100 text-purple-800 rounded text-xs">${article.couleur}</span>` : ''}
                                        ${article.pointure ? `<span class="px-2 py-1 bg-blue-100 text-blue-800 rounded text-xs">${article.pointure}</span>` : ''}
                                        ${article.categorie ? `<span class="px-2 py-1 bg-green-100 text-green-800 rounded text-xs">${article.categorie}</span>` : ''}
                                    </div>
                                </div>
                                <div class="text-right">
                                    <div class="text-lg font-semibold text-green-600">${article.prix_actuel} DH</div>
                                    <button class="mt-2 px-3 py-1 text-white rounded text-sm transition-all" style="background: linear-gradient(135deg, #2563eb, #3b82f6); hover:shadow-lg;">
                                        Voir variantes
                                    </button>
                                </div>
                            </div>
                        </div>
                    `).join('');
                    
                    resultatsDiv.innerHTML = articlesHtml;
                } else {
                    resultatsDiv.innerHTML = '<div class="text-center py-4 text-gray-500">Aucun article trouvé</div>';
                }
            })
            .catch(error => {
                console.error('❌ Erreur recherche articles:', error);
                resultatsDiv.innerHTML = '<div class="text-center py-4 text-red-500"><i class="fas fa-exclamation-triangle mr-2"></i>Erreur lors de la recherche</div>';
            });
    } catch (e) {
        console.error('❌ Erreur rechercherArticlesPourVariantes:', e);
    }
}



// ===== Gestion de la barre de navigation personnalisée =====
let scrollThumbDragging = false;

function initCustomScrollbar() {
    const container = document.getElementById('articlesScrollContainer');
    const scrollbar = document.getElementById('customScrollbar');
    const thumb = document.getElementById('scrollThumb');
    const scrollUp = document.getElementById('scrollUp');
    const scrollDown = document.getElementById('scrollDown');
    const scrollInfo = document.getElementById('scrollInfo');
    
    if (!container || !scrollbar || !thumb) {
        console.log('❌ Éléments de scrollbar manquants');
        return;
    }
    
 
    function updateScrollbar() {
        const scrollTop = container.scrollTop;
        const scrollHeight = container.scrollHeight;
        const clientHeight = container.clientHeight;
        const maxScroll = scrollHeight - clientHeight;
        
   
        if (maxScroll <= 0) {
            scrollbar.style.display = 'none';
            return;
        }
        
        scrollbar.style.display = 'block';
        const thumbHeight = Math.max(50, (clientHeight / scrollHeight) * clientHeight);
        const thumbTop = (scrollTop / maxScroll) * (clientHeight - thumbHeight);
        
        thumb.style.height = thumbHeight + 'px';
        thumb.style.top = thumbTop + 'px';
        
        // Mettre à jour l'info de scroll
        const visibleItems = Math.ceil(clientHeight / 80);
        const totalItems = document.querySelectorAll('#articlesTableBody tr:not([style*="display: none"])').length;
        const currentPosition = Math.ceil(scrollTop / 80) + 1;
        
        if (scrollInfo) {
            scrollInfo.textContent = `${currentPosition}-${Math.min(currentPosition + visibleItems - 1, totalItems)} sur ${totalItems} articles`;
        }
    }
    
    // Événements de scroll
    container.addEventListener('scroll', () => {
        if (!scrollThumbDragging) {
            updateScrollbar();
        }
    });
    
    // Drag du thumb
    thumb.addEventListener('mousedown', (e) => {
        e.preventDefault();
        scrollThumbDragging = true;
        const startY = e.clientY;
        const startTop = parseFloat(thumb.style.top) || 0;
        
        function onMouseMove(e) {
            if (!scrollThumbDragging) return;
            const deltaY = e.clientY - startY;
            const newTop = Math.max(0, Math.min(container.clientHeight - thumb.offsetHeight, startTop + deltaY));
            const scrollTop = (newTop / (container.clientHeight - thumb.offsetHeight)) * (container.scrollHeight - container.clientHeight);
            container.scrollTop = scrollTop;
        }
        
        function onMouseUp() {
            scrollThumbDragging = false;
            document.removeEventListener('mousemove', onMouseMove);
            document.removeEventListener('mouseup', onMouseUp);
        }
        
        document.addEventListener('mousemove', onMouseMove);
        document.addEventListener('mouseup', onMouseUp);
    });
    
    // Clic sur la barre de scroll
    scrollbar.addEventListener('click', (e) => {
        if (e.target === thumb) return;
        const rect = scrollbar.getBoundingClientRect();
        const clickY = e.clientY - rect.top;
        const scrollTop = (clickY / rect.height) * (container.scrollHeight - container.clientHeight);
        container.scrollTop = scrollTop;
    });
    
    // Boutons de navigation
    if (scrollUp) {
        scrollUp.addEventListener('click', () => {
            container.scrollBy({ top: -100, behavior: 'smooth' });
        });
    }
    
    if (scrollDown) {
        scrollDown.addEventListener('click', () => {
            container.scrollBy({ top: 100, behavior: 'smooth' });
        });
    }
    
    // Initialisation
    updateScrollbar();
    
    // Observer les changements dans le contenu
    const observer = new MutationObserver(() => {
        setTimeout(updateScrollbar, 50);
    });
    observer.observe(container, { childList: true, subtree: true });
    
    // Mettre à jour après le chargement des articles
    setTimeout(updateScrollbar, 200);
}
// Initialiser la barre de navigation quand le modal s'ouvre
function setupScrollbarObserver() {
    const modal = document.getElementById('articleModal');
    if (modal) {
        const observer = new MutationObserver((mutations) => {
            mutations.forEach((mutation) => {
                if (mutation.type === 'attributes' && mutation.attributeName === 'style') {
                    if (modal.style.display === 'flex') {
                        
                        setTimeout(initCustomScrollbar, 100);
                    }
                }
            });
        });
        observer.observe(modal, { attributes: true });
    }
}

// Initialiser au chargement de la page
document.addEventListener('DOMContentLoaded', setupScrollbarObserver);

// Réinitialiser après le chargement des articles
function reinitScrollbarAfterArticlesLoad() {
    setTimeout(initCustomScrollbar, 300);
}

// Fonction appelée quand un article est sélectionné
function onArticleSelectionChange() {
    const select = document.getElementById('articleSelect');
    const selectedOption = select.options[select.selectedIndex];
    
    if (selectedOption.value) {
        const article = JSON.parse(selectedOption.dataset.article);
        
        // Afficher d'abord les informations disponibles
        afficherInfosArticle(article);
        
        // Puis rafraîchir les données de stock en temps réel
        if (article.id && !article.id.toString().startsWith('fallback-')) {
            // Indiquer que le stock est en cours de rafraîchissement
            const infoStock = document.getElementById('info-stock');
            const stockProgressBar = document.getElementById('stock-progress');
            const stockPercentage = document.getElementById('stock-percentage');
            
            if (infoStock) {
                infoStock.innerHTML = '<i class="fas fa-sync fa-spin mr-1"></i> Actualisation...';
                infoStock.className = 'px-3 py-1 bg-blue-100 text-blue-700 rounded-full font-medium';
            }
            
            if (stockProgressBar) {
                stockProgressBar.className = 'h-2.5 rounded-full bg-blue-500 animate-pulse';
                stockProgressBar.style.width = '50%';
            }
            
            if (stockPercentage) {
                stockPercentage.textContent = '...';
                stockPercentage.className = 'ml-2 text-xs font-medium text-blue-700';
            }
            
            // Appeler l'API pour obtenir les données à jour
            rafraichirStockArticle(article.id)
                .then(articleMisAJour => {
                    if (articleMisAJour) {
                        // Mettre à jour les données de l'article dans le dataset de l'option
                        article.qte_disponible = articleMisAJour.qte_disponible;
                        selectedOption.dataset.article = JSON.stringify(article);
                        
                        // Réafficher les informations avec les données mises à jour
        afficherInfosArticle(article);
                    } else {
                        // Si l'API n'a pas retourné de données, utiliser les données existantes
                        afficherInfosArticle(article);
                    }
                })
                .catch(error => {
                    console.error('❌ Erreur lors du rafraîchissement du stock:', error);
                    // En cas d'erreur, utiliser les données existantes sans notification d'erreur
                    // pour ne pas perturber l'expérience utilisateur
                    afficherInfosArticle(article);
                });
        }
    } else {
        document.getElementById('article-info').classList.add('hidden');
    }
}

// Fonction pour afficher les informations d'un article
function afficherInfosArticle(article) {
    try {
        if (!article) {
            console.error('❌ Article non défini dans afficherInfosArticle');
            return;
        }
        
        // Vérifier et récupérer les valeurs avec sécurité
        const quantite = parseInt(document.getElementById('quantiteInput')?.value) || 1;
        const prixActuel = typeof article.prix_actuel === 'number' ? article.prix_actuel : 
                         (article.prix_actuel ? parseFloat(article.prix_actuel) : 
                         (article.prix_unitaire ? parseFloat(article.prix_unitaire) : 0));
        
        const sousTotal = (prixActuel * quantite).toFixed(2);
    
        // Informations de base avec vérification des éléments DOM
        const refElement = document.getElementById('info-reference');
        const prixElement = document.getElementById('info-prix');
        const sousTotalElement = document.getElementById('info-sous-total');
        const pointureElement = document.getElementById('info-pointure');
        const couleurElement = document.getElementById('info-couleur');
        const categorieElement = document.getElementById('info-categorie');
        const descriptionElement = document.getElementById('info-description');
        
        if (refElement) refElement.textContent = article.reference || '-';
        if (prixElement) prixElement.textContent = `${prixActuel} DH`;
        if (sousTotalElement) sousTotalElement.textContent = `${sousTotal} DH`;
        
        // Vérifier que qte_disponible est bien défini et convertir en nombre
        let stock = 0;
        try {
            stock = typeof article.qte_disponible === 'number' ? article.qte_disponible : 
                   (article.qte_disponible ? parseInt(article.qte_disponible) : 0);
            
            // Si la conversion a échoué, utiliser 0
            if (isNaN(stock)) {
                console.warn('⚠️ Valeur de stock non numérique:', article.qte_disponible);
                stock = 0;
            }
        } catch (e) {
            console.error('❌ Erreur lors de la conversion du stock:', e);
            stock = 0;
        }
    
    // Nouvelles informations détaillées
        if (pointureElement) pointureElement.textContent = article.pointure || 'Non spécifiée';
        if (couleurElement) couleurElement.textContent = article.couleur || 'Non spécifiée';
        if (categorieElement) categorieElement.textContent = typeof article.categorie === 'string' ? article.categorie : 'Non spécifiée';
        
        // Mettre à jour l'affichage du stock avec style conditionnel
        const stockElement = document.getElementById('info-stock');
        const stockProgressBar = document.getElementById('stock-progress');
        const stockPercentage = document.getElementById('stock-percentage');
        
        if (stockElement && stockProgressBar && stockPercentage) {
            // Définir une capacité maximale théorique pour la barre de progression (ajuster selon vos besoins)
            const capaciteMaximale = Math.max(stock, 100); // Au moins 100 ou la valeur actuelle du stock
            
            // Calculer le pourcentage du stock
            const pourcentage = Math.min(Math.round((stock / capaciteMaximale) * 100), 100);
            
            // Mettre à jour le texte et la couleur selon le niveau de stock
            if (stock <= 0) {
                stockElement.textContent = 'Épuisé';
                stockElement.className = 'px-3 py-1 bg-red-100 text-red-700 rounded-full font-medium';
                stockProgressBar.style.width = '0%';
                stockProgressBar.className = 'h-2.5 rounded-full bg-red-500';
                stockPercentage.textContent = '0%';
                stockPercentage.className = 'ml-2 text-xs font-medium text-red-700';
            } else if (stock < 5) {
                stockElement.textContent = `${stock} unité(s) - Faible`;
                stockElement.className = 'px-3 py-1 bg-orange-100 text-orange-700 rounded-full font-medium';
                stockProgressBar.style.width = `${pourcentage}%`;
                stockProgressBar.className = 'h-2.5 rounded-full bg-orange-500';
                stockPercentage.textContent = `${pourcentage}%`;
                stockPercentage.className = 'ml-2 text-xs font-medium text-orange-700';
            } else {
                stockElement.textContent = `${stock} unité(s)`;
                stockElement.className = 'px-3 py-1 bg-teal-100 text-teal-700 rounded-full font-medium';
                stockProgressBar.style.width = `${pourcentage}%`;
                stockProgressBar.className = 'h-2.5 rounded-full bg-teal-600';
                stockPercentage.textContent = `${pourcentage}%`;
                stockPercentage.className = 'ml-2 text-xs font-medium text-teal-700';
            }
        }
    
    // Mettre à jour les badges avec les informations de l'article
        try {
    const caracteristiques = {
        taille: article.pointure || null,
        couleur: article.couleur || null,
                categorie: typeof article.categorie === 'string' ? article.categorie : null,
                stock: `Stock: ${stock}`,
        description: article.description || ''
    };
    mettreAJourBadgesModale(caracteristiques);
        } catch (e) {
            console.warn('⚠️ Erreur lors de la mise à jour des badges:', e);
        }
    
    // Description
        if (descriptionElement) descriptionElement.textContent = article.description || '';
    
    // Afficher la section des informations
        const articleInfoSection = document.getElementById('article-info');
        if (articleInfoSection) articleInfoSection.classList.remove('hidden');
    
    
    } catch (error) {
        console.error('❌ Erreur lors de l\'affichage des informations de l\'article:', error);
        // Ne pas laisser l'erreur se propager pour éviter de bloquer l'interface
    }
}

// Fonction pour mettre à jour le sous-total quand la quantité change
function onQuantiteChange() {
    if (!isEditingArticle) {
        const select = document.getElementById('articleSelect');
        const selectedOption = select.options[select.selectedIndex];
        
        if (selectedOption.value) {
            const article = JSON.parse(selectedOption.dataset.article);
            afficherInfosArticle(article);
        }
    } else {
        // Pour les modifications, on recalcule avec le prix actuel
        const prixText = document.getElementById('info-prix').textContent;
        const prix = parseFloat(prixText.replace(' DH', ''));
        const quantite = parseInt(document.getElementById('quantiteInput').value) || 1;
        const sousTotal = (prix * quantite).toFixed(2);
        
        document.getElementById('info-sous-total').textContent = `${sousTotal} DH`;
    }
}

// Fonction pour sauvegarder l'article
function saveArticle() {
    const quantite = parseInt(document.getElementById('quantiteInput').value);
    
    if (!quantite || quantite < 1) {
        alert('⚠️ Veuillez saisir une quantité valide (minimum 1)');
        return;
    }
    
        const select = document.getElementById('articleSelect');
        if (!select.value) {
            alert('⚠️ Veuillez sélectionner un article');
            return;
        }
        
    const articleId = select.value;
    const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]')?.value;

    if (!csrfToken) {
        showToast('❌ Erreur: Token de sécurité manquant. Veuillez rafraîchir la page.', 'error');
        return;
    }

    let action = isEditingArticle ? 'update_article' : 'add_article';
    
    // Récupérer les données de l'article sélectionné pour voir s'il y a une variante
    const selectedOption = select.options[select.selectedIndex];
    const articleData = selectedOption ? JSON.parse(selectedOption.dataset.article || '{}') : {};
    
    let body = new URLSearchParams({
        'action': action,
        'article_id': articleId,
        'quantite': quantite,
    });
    
    // Si c'est une variante, ajouter l'ID de la variante
    if (articleData.variante_id) {
        body.append('variante_id', articleData.variante_id);
    }

    if(isEditingArticle) {
        body.append('panier_id', currentArticleId); // currentArticleId est l'ID du *panier*
    }
    // Utiliser l'URL fournie par le template dans modifier_commande.html
    // Utiliser l'URL globale (fallback via data-attribute)
    const modifierArticle = getUrlModifier();

    fetch(modifierArticle, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/x-www-form-urlencoded',
            'X-CSRFToken': csrfToken
        },
        body: body
    })
    .then(response => {
        if (!response.ok) {
            // Si le statut est une erreur (4xx, 5xx), lire en tant que texte
            return response.text().then(text => { 
                throw new Error(`Erreur ${response.status}: ${text}`);
            });
        }
        return response.json();
    })
    .then(data => {
        if (data.success) {
            // Afficher un message approprié selon l'action et le résultat
            let message = data.message || (isEditingArticle ? '✅ Article modifié' : '✅ Article ajouté');
            
            showToast(message, 'success');
            rafraichirSectionArticles();
            closeArticleModal();
        } else {
            showToast(`❌ Erreur: ${data.error}`, 'error');
        }
    })
    .catch(error => {
        console.error('❌ Erreur Fetch:', error);
        // Essayer d'extraire un message d'erreur plus clair de l'HTML
        const match = error.message.match(/<title>(.*?)<\/title>/);
        const htmlTitle = match ? match[1] : 'Erreur de communication avec le serveur.';
        showToast(`❌ Erreur: ${htmlTitle}`, 'error');
    });
}

// Nouvelle fonction pour rafraîchir la section des articles
function rafraichirSectionArticles() {
    const container = document.getElementById('articles-container');
    if (!container) {
        console.error('❌ Conteneur d\'articles introuvable');
        showToast('❌ Erreur lors du rafraîchissement: conteneur introuvable', 'error');
        return;
    }
    
    container.innerHTML = '<div class="text-center p-8"><i class="fas fa-spinner fa-spin text-2xl text-gray-500"></i><p class="mt-2">Rafraîchissement en cours...</p></div>';

    // Construire l'URL avec l'ID de commande exposé par le template dans window.commandeId
    fetch(`/operateur-confirme/api/commande/${(typeof window !== 'undefined' && window.commandeId) ? window.commandeId : ''}/rafraichir-articles/`)
        .then(response => {
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }
            return response.json();
        })
        .then(data => {
            if (data.success) {
                // Mettre à jour la liste des articles
                container.innerHTML = data.html;

                // Utiliser la fonction centralisée pour mettre à jour tous les totaux
                mettreAJourTousLesTotaux(data);

                showToast('🔄 Section des articles mise à jour.', 'info', 1500);
                
                // Déclencher des événements personnalisés pour d'autres scripts qui pourraient écouter
                window.dispatchEvent(new CustomEvent('articlesRefreshed', { 
                    detail: { 
                        articles_count: data.articles_count,
                        total_commande: data.total_commande,
                        sous_total_articles: data.sous_total_articles,
                        compteur: data.compteur
                    }
                }));
            } else {
                container.innerHTML = `<div class="text-center p-4 bg-red-100 text-red-700 rounded-lg">${data.error || 'Erreur inconnue'}</div>`;
                showToast(`❌ Erreur de rafraîchissement: ${data.error || 'Erreur inconnue'}`, 'error');
            }
        })
        .catch(error => {
            console.error('Erreur de rafraîchissement:', error);
            container.innerHTML = `<div class="text-center p-4 bg-red-100 text-red-700 rounded-lg">
                <div class="font-bold mb-2">Erreur de connexion</div>
                <div class="text-sm">${error.message || 'Impossible de contacter le serveur'}</div>
                <button onclick="rafraichirSectionArticles()" class="mt-3 px-4 py-2 text-white rounded-lg transition-all" style="background: linear-gradient(135deg, #dc2626, #ef4444); hover:shadow-lg;">
                    <i class="fas fa-sync-alt mr-1"></i>Réessayer
                </button>
            </div>`;
            showToast('❌ Erreur de connexion lors du rafraîchissement.', 'error');
        });
}

// Fonction centralisée pour mettre à jour tous les totaux et compteurs
function mettreAJourTousLesTotaux(data) {
    // Mettre à jour le sous-total global des articles
    if (data.sous_total_articles !== undefined) {
        const sousTotalGlobalElement = document.getElementById('sous-total-articles');
        if (sousTotalGlobalElement) {
            sousTotalGlobalElement.textContent = `${parseFloat(data.sous_total_articles).toFixed(2)} DH`;
        }
    }

    // Mettre à jour le total de la commande (corriger getElementById)
    if (data.total_commande !== undefined) {
        const totalElement = document.getElementById('total-commande');
        const totalElementHautPage = document.getElementById('total_commande_haut_page');
        if (totalElement) {
            totalElement.textContent = `${parseFloat(data.total_commande).toFixed(2)} DH`;
        }
        if (totalElementHautPage) {
            totalElementHautPage.textContent = `${parseFloat(data.total_commande).toFixed(2)} DH`;
        }
        
        // Également mettre à jour tous les éléments avec la classe total-commande
        const totalElements = document.querySelectorAll('.total-commande');
        totalElements.forEach(el => {
            el.textContent = `${parseFloat(data.total_commande).toFixed(2)} DH`;
        });
        // Mettre à jour le total de la commande dans la section du haut de la page 
        const totalElementHautPages = document.querySelectorAll('.total_commande_haut_page');
        totalElementHautPages.forEach(el => {
            el.textContent = `${parseFloat(data.total_commande).toFixed(2)} DH`;
        });
        
    }
    
    // Mettre à jour le compteur d'articles
    if (data.articles_count !== undefined) {
        const countElement = document.getElementById('articles-count');
        if (countElement) {
            countElement.textContent = data.articles_count;
        }
        
        const pluralElement = document.getElementById('articles-plural');
        if (pluralElement) {
            pluralElement.textContent = data.articles_count > 1 ? 's' : '';
        }
    }
    
    // Mettre à jour le compteur upsell dans tous les endroits possibles
    if (data.compteur !== undefined) {
        // Compteur principal
        const compteurSpan = document.getElementById('compteur-display');
        if (compteurSpan) {
            compteurSpan.textContent = data.compteur;
        }
        
        // Niveau upsell dashboard
        const niveauUpsellDash = document.getElementById('niveau-upsell-dashboard');
        if (niveauUpsellDash) {
            niveauUpsellDash.textContent = data.compteur;
        }
        
        // Niveau upsell articles
        const niveauUpsellArticles = document.getElementById('niveau-upsell-articles');
        if (niveauUpsellArticles) {
            niveauUpsellArticles.textContent = data.compteur;
        }
        
         // Mettre à jour les éléments avec la classe compteur-upsell
        const compteurElements = document.querySelectorAll('.compteur-upsell');
        compteurElements.forEach(el => {
            el.textContent = data.compteur;
        });
        
        // Mettre à jour le compteur dans l'en-tête de la page
        const compteurHeader = document.getElementById('compteur-upsell-header');
        if (compteurHeader) {
            compteurHeader.textContent = `Niveau ${data.compteur}`;
        }
        
        // Mettre à jour les prix unitaires si le compteur a changé
        mettreAJourPrixUnitaires(data.compteur);
        
        // Mettre à jour le badge upsell s'il existe
        const upsellBadge = document.getElementById('upsell-badge-container');
        if (upsellBadge && data.compteur > 0) {
            upsellBadge.innerHTML = `<span class="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-purple-100 text-purple-800">
                <i class="fas fa-arrow-up mr-1"></i>Niveau ${data.compteur}
            </span>`;
        } else if (upsellBadge && data.compteur === 0) {
            upsellBadge.innerHTML = '';
        }
    }
    
}

// Fonction utilitaire pour mettre à jour le compteur upsell dans tous les endroits
function mettreAJourCompteurUpsell(nouveauCompteur) {
    console.log(`🔄 Mise à jour du compteur upsell: ${nouveauCompteur}`);
    
    // Mettre à jour la variable globale
    if (typeof compteurCommande !== 'undefined') {
        compteurCommande = nouveauCompteur;
    }
    
    // Mettre à jour tous les éléments d'affichage
    const data = { compteur: nouveauCompteur };
    mettreAJourTousLesTotaux(data);
    
    // Mettre à jour les prix unitaires
    mettreAJourPrixUnitaires(nouveauCompteur);
    
}


// Fonction pour mettre à jour dynamiquement les prix unitaires
function mettreAJourPrixUnitaires(nouveauCompteur) {

    // Récupérer tous les articles
    const articleCards = document.querySelectorAll('.article-card');
    
    articleCards.forEach(articleCard => {
        const panierId = articleCard.getAttribute('data-article-id');
        
        
        
        const dataArticleAttr = articleCard.getAttribute('data-article');
        const articleData = parseArticleData(dataArticleAttr, panierId);
        
        if (articleData && !articleData.error) {
            // Calculer le nouveau prix selon le compteur
            const prixInfo = calculerPrixAvecPhaseInfo(articleData, nouveauCompteur);
            
            // Mettre à jour l'affichage du prix
            const prixElement = document.getElementById(`prix-unitaire-${panierId}`);
            const libelleElement = document.getElementById(`prix-libelle-${panierId}`);
            
            if (prixElement && libelleElement) {
                // Mettre à jour le prix
                prixElement.textContent = `${prixInfo.prix.toFixed(2)} DH`;
                
                // Mettre à jour la classe de couleur
                prixElement.className = `font-medium ${prixInfo.couleur_classe}`;
                
                // Mettre à jour le libellé
                libelleElement.textContent = prixInfo.libelle;
                libelleElement.className = `text-xs ${prixInfo.couleur_classe} mt-1`;
            
            }
            
            // Mettre à jour le sous-total
            mettreAJourSousTotalArticle(panierId, prixInfo.prix);
        } else {
            // En cas d'erreur de parsing, on peut essayer de rafraîchir la section des articles
            setTimeout(() => {
                rafraichirSectionArticles();
            }, 1000);
        }
    });
}

// Fonction utilitaire pour mettre à jour le sous-total d'un article
function mettreAJourSousTotalArticle(panierId, prixUnitaire) {
 
    
    const sousTotalElement = document.getElementById(`sous-total-${panierId}`);
    if (sousTotalElement) {
        // Récupérer la quantité depuis l'input
        const quantiteInput = document.getElementById(`quantite-${panierId}`);
        const quantite = quantiteInput ? parseInt(quantiteInput.value) || 1 : 1;
        
        // Calculer le nouveau sous-total
        const nouveauSousTotal = prixUnitaire * quantite;
        
        // Mettre à jour l'affichage
        sousTotalElement.textContent = `${nouveauSousTotal.toFixed(2)} DH`;
        
  
        return nouveauSousTotal;
    }
    return 0;
}

// Fonction pour recalculer tous les sous-totaux selon le compteur actuel
function recalculerTousLesSousTotaux() {
    const articleCards = document.querySelectorAll('.article-card');
    let totalSousTotaux = 0;
    
    articleCards.forEach(articleCard => {
        const panierId = articleCard.getAttribute('data-article-id');
        
     
        const dataArticleAttr = articleCard.getAttribute('data-article');
        const articleData = parseArticleData(dataArticleAttr, panierId);
        
        if (articleData && !articleData.error) {
            // Récupérer le compteur actuel
            const compteurActuel = parseInt(document.getElementById('compteur-upsell-header').textContent.replace('Niveau ', '')) || 0;
            
            // Calculer le prix selon le compteur
            const prixInfo = calculerPrixAvecPhaseInfo(articleData, compteurActuel);
            
            // Mettre à jour le sous-total
            const sousTotal = mettreAJourSousTotalArticle(panierId, prixInfo.prix);
            totalSousTotaux += sousTotal;
        }
    });

    return totalSousTotaux;
}

// Fonction pour calculer le prix avec les informations de phase (version JavaScript)
function calculerPrixAvecPhaseInfo(article, compteur) {
    // Déterminer le prix de base
    let prix;
    if (compteur !== null && compteur !== undefined && article.isUpsell) {
        prix = getPrixUpsellAvecCompteur(article, compteur);
    } else {
        prix = article.prix_actuel || article.prix_unitaire || 0;
    }
    
    // Déterminer le libellé selon la phase et les promotions
    let libelle, couleur_classe;
    
    if (article.has_promo_active) {
        libelle = "Prix promotion";
        couleur_classe = "text-red-600";
    } else if (article.phase === 'LIQUIDATION') {
        libelle = "Prix liquidation";
        couleur_classe = "text-orange-600";
    } else if (article.phase === 'EN_TEST') {
        libelle = "Prix test";
        couleur_classe = "text-blue-600";
    } else if (compteur !== null && compteur !== undefined && compteur > 0 && article.isUpsell) {
        libelle = `Prix upsell niveau ${compteur}`;
        couleur_classe = "text-green-600";
    } else {
        libelle = "Prix normal";
        couleur_classe = "text-gray-600";
    }
    
    return {
        prix: prix,
        libelle: libelle,
        couleur_classe: couleur_classe
    };
}
// Fonction pour calculer le prix upsell avec compteur (version JavaScript)
function getPrixUpsellAvecCompteur(article, compteur) {
    if (!article.isUpsell) {
        return article.prix_actuel || article.prix_unitaire || 0;
    }
    
    // Utiliser le compteur pour déterminer le prix upsell
    if (compteur === 0) {
        return article.prix_actuel || article.prix_unitaire || 0;
    } else if (compteur === 1 && article.prix_upsell_1) {
        return parseFloat(article.prix_upsell_1);
    } else if (compteur === 2 && article.prix_upsell_2) {
        return parseFloat(article.prix_upsell_2);
    } else if (compteur === 3 && article.prix_upsell_3) {
        return parseFloat(article.prix_upsell_3);
    } else if (compteur >= 4 && article.prix_upsell_4) {
        return parseFloat(article.prix_upsell_4);
    }
    
    // Si pas de prix upsell défini pour ce niveau, utiliser le prix unitaire
    return article.prix_actuel || article.prix_unitaire || 0;
}


// Fonction utilitaire pour valider et parser le JSON des articles
function parseArticleData(dataArticleAttr, panierId) {
    try {
        if (!dataArticleAttr || dataArticleAttr.trim() === '') {
            throw new Error('Données JSON vides ou manquantes');
        }
        
        // Nettoyer les données JSON de manière plus robuste
        let cleanedData = dataArticleAttr.trim();
        
        // Remplacer les caractères problématiques
        cleanedData = cleanedData.replace(/\n/g, '\\n')
                                .replace(/\r/g, '\\r')
                                .replace(/\t/g, '\\t');
        
        // Méthode de nettoyage complète et systématique
        // 1. D'abord gérer les séquences d'échappement
        cleanedData = cleanedData.replace(/\\u002D/g, '-');
        
        // 2. Corriger les nombres avec virgules vers points (avec ou sans guillemets)
        cleanedData = cleanedData.replace(/:\s*(\d+),(\d+)"/g, ': $1.$2');
        cleanedData = cleanedData.replace(/:\s*(\d+),(\d+)/g, ': $1.$2');
        
        // 3. Supprimer les guillemets en trop après les valeurs booléennes et numériques
        cleanedData = cleanedData.replace(/:\s*false"\s*([,}])/g, ': false$1');
        cleanedData = cleanedData.replace(/:\s*true"\s*([,}])/g, ': true$1');
        cleanedData = cleanedData.replace(/:\s*(\d+(?:\.\d+)?)\"\s*([,}])/g, ': $1$2');
        
        // 4. Nettoyer les espaces autour des séparateurs
        cleanedData = cleanedData.replace(/\s*:\s*/g, ': ');
        cleanedData = cleanedData.replace(/\s*,\s*/g, ', ');
        
        // Tentative de parsing
        const articleData = JSON.parse(cleanedData);
        
        // Valider que les données essentielles sont présentes
        if (!articleData.id || !articleData.nom) {
            throw new Error('Données d\'article incomplètes');
        }
        
        // Convertir les prix en nombres si nécessaire
        const prixFields = ['prix_actuel', 'prix_unitaire', 'prix_upsell_1', 'prix_upsell_2', 'prix_upsell_3', 'prix_upsell_4'];
        prixFields.forEach(field => {
            if (articleData[field] !== undefined && articleData[field] !== null) {
                articleData[field] = parseFloat(articleData[field]) || 0;
            }
        });
        
        return articleData;
    } catch (error) {
        console.error(`❌ Erreur de parsing JSON pour l'article ${panierId}:`, error);
        console.error('Données JSON problématiques (premiers 200 chars):', dataArticleAttr ? dataArticleAttr.substring(0, 200) : 'undefined');
        
        // Retourner un objet article minimal pour éviter les erreurs en cascade
        return {
            id: panierId,
            nom: 'Article endommagé',
            prix_actuel: 0,
            prix_unitaire: 0,
            error: true,
            errorMessage: error.message
        };
    }
}

// Variables globales pour la suppression
window.currentPanierIdToDelete = null;

// Fonction pour supprimer un article
function supprimerArticle(panierId) {
    currentPanierIdToDelete = panierId; // Stocke l'ID du panier à supprimer
    showDeleteArticleModal();
}



// Fonction pour afficher la modale de suppression d'article
function showDeleteArticleModal() {
    const modal = document.getElementById('deleteArticleModal');
    if (modal) {
        modal.classList.remove('hidden');
        modal.classList.add('flex');
        // Mettre à jour l'ID sur le bouton de confirmation
        const confirmBtn = document.getElementById('confirmDeleteArticleBtn');
        if (confirmBtn) {
            confirmBtn.onclick = function() { proceedWithArticleDeletion(); };
        }
    }
}

// Fonction pour masquer la modale de suppression d'article
function hideDeleteArticleModal() {
    const modal = document.getElementById('deleteArticleModal');
    if (modal) {
        modal.classList.add('hidden');
        modal.classList.remove('flex');
    }
    currentPanierIdToDelete = null; // Réinitialise l'ID
}

// Fonction pour procéder à la suppression après confirmation
function proceedWithArticleDeletion() {
    if (currentPanierIdToDelete) {
        const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]').value;
        const modifierArticle = getUrlModifier();
       
        fetch(modifierArticle, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/x-www-form-urlencoded',
                'X-CSRFToken': csrfToken
            },
            body: new URLSearchParams({
                'action': 'delete_panier',
                'panier_id': currentPanierIdToDelete
            })
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                showToast('✅ Article supprimé avec succès', 'success');
                rafraichirSectionArticles();
                hideDeleteArticleModal(); // Masquer la modale après succès
            } else {
                showToast('❌ Erreur: ' + data.error, 'error');
                hideDeleteArticleModal(); // Masquer la modale même en cas d'erreur
            }
        })
        .catch(error => {
            console.error('❌ Erreur:', error);
            showToast('❌ Erreur de réseau', 'error');
            hideDeleteArticleModal(); // Masquer la modale en cas d'erreur réseau
        });
    }
}

// Fonction pour fermer la modale d'article
function closeArticleModal() {
    const modal = document.getElementById('articleModal');
    if (modal) {
        modal.style.display = 'none';
        modal.classList.add('hidden');
        modal.classList.remove('flex');
    } else {
        console.error('❌ Modale articleModal introuvable lors de la fermeture');
    }
}

// Fonction pour mettre à jour le compteur d'articles
function mettreAJourCompteurArticles() {
    const articles = document.querySelectorAll('.article-card');
    const count = articles.length;
    
    document.getElementById('articles-count').textContent = count;
    document.getElementById('articles-plural').textContent = count > 1 ? 's' : '';
}

function getPrixUpsell(article, compteur) {
    // Utiliser le compteur de la commande pour déterminer le prix
    const prixUnitaire = article.prix_actuel || article.prix_unitaire;
    
    if (compteur === 0) {
        // Pas d'upsell actif
        return prixUnitaire;
    } else if (compteur === 1 && article.prix_upsell_1) {
        // Niveau 1 d'upsell
        return parseFloat(article.prix_upsell_1);
    } else if (compteur === 2 && article.prix_upsell_2) {
        // Niveau 2 d'upsell
        return parseFloat(article.prix_upsell_2);
    } else if (compteur === 3 && article.prix_upsell_3) {
        // Niveau 3 d'upsell
        return parseFloat(article.prix_upsell_3);
    } else if (compteur >= 4 && article.prix_upsell_4) {
        // Niveau 4 d'upsell (pour compteur >= 4)
        return parseFloat(article.prix_upsell_4);
    }
    
    // Si pas de prix upsell défini pour ce niveau, utiliser le prix unitaire
    return prixUnitaire;
}

// Fonction utilitaire pour vérifier si les frais de livraison sont activés
function sontFraisLivraisonActives() {
    const fraisStatusText = document.getElementById('frais-status-text');
    return fraisStatusText && fraisStatusText.textContent.trim() === 'Activés';
}

// Fonction pour mettre à jour l'affichage des frais de livraison dans le résumé
function mettreAJourAffichageFraisResume() {
    const fraisResumeElement = document.querySelector('#frais-display.font-medium.text-gray-800');
    const fraisResumeContainer = fraisResumeElement ? fraisResumeElement.closest('.flex.justify-between.items-center') : null;
    
    if (sontFraisLivraisonActives()) {
        // Afficher la section des frais de livraison
        if (fraisResumeContainer) {
            fraisResumeContainer.style.display = 'flex';
        }
        
        // Mettre à jour le montant
        const fraisElement = document.getElementById('frais-display');
        if (fraisElement && fraisResumeElement) {
            const fraisText = fraisElement.value.replace(' DH', '').replace(',', '.');
            const fraisMontant = parseFloat(fraisText) || 0;
            fraisResumeElement.textContent = `${fraisMontant.toFixed(2)} DH`;
        }
    } else {
        // Masquer la section des frais de livraison
        if (fraisResumeContainer) {
            fraisResumeContainer.style.display = 'none';
        }
    }
}

function mettreAJourTotalCommande() {
    const articlesContainer = document.getElementById('articles-container');
    if (!articlesContainer) {
        console.error("L'élément 'articles-container' est introuvable.");
        return;
    }

    const articles = articlesContainer.querySelectorAll('.article-card');
    let sousTotal = 0;
    

    articles.forEach((article, index) => {
        const sousTotalElement = article.querySelector('.text-lg.font-bold');
        
        if (sousTotalElement) {
            // Simplement additionner les sous-totaux déjà affichés
            const sousTotalText = sousTotalElement.textContent;
            const sousTotal_article = parseFloat(sousTotalText.replace(' DH', '').replace(',', '.'));
            
            if (!isNaN(sousTotal_article)) {
                sousTotal += sousTotal_article;
            } else {
                console.warn(`   ⚠️ Sous-total ${index + 1} non valide: "${sousTotalText}"`);
            }
        }
    });
    
    // Vérifier si les frais de livraison sont activés et récupérer le montant
    let fraisLivraison = 0;
    if (sontFraisLivraisonActives()) {
        const fraisElement = document.getElementById('frais-display');
        if (fraisElement) {
            const fraisText = fraisElement.value.replace(' DH', '').replace(',', '.');
            fraisLivraison = parseFloat(fraisText) || 0;
        }
    }
    
    const totalFinal = sousTotal + fraisLivraison;
    

    // Mettre à jour l'affichage des frais dans le résumé
    mettreAJourAffichageFraisResume();
    
    const totalElement = document.getElementById('total-commande');
    if (totalElement) {
        const ancienTotal = totalElement.textContent;
        totalElement.textContent = `${totalFinal.toFixed(2)} DH`;
     
    }
    const totalElementHautPage = document.getElementById('total_commande_haut_page');
    if (totalElementHautPage) {
        const ancienTotal = totalElementHautPage.textContent;
        totalElementHautPage.textContent = `${totalFinal.toFixed(2)} DH`;
       
    }
    
    // Mettre à jour le sous-total des articles dans le détail si l'élément existe
    const sousTotalElement = document.getElementById('sous-total-articles');
    if (sousTotalElement) {
        const ancienSousTotal = sousTotalElement.textContent;
        sousTotalElement.textContent = `${sousTotal.toFixed(2)} DH`;
       
    }
    
}

// Fonction alternative qui additionne directement les sous-totaux affichés
function recalculerTotalDepuisSousTotaux() {
    const sousTotalElements = document.querySelectorAll('.text-lg.font-bold');
    let total = 0;
    
    sousTotalElements.forEach((element, index) => {
        const texte = element.textContent;
        const valeur = parseFloat(texte.replace(' DH', '').replace(',', '.'));
        
        if (!isNaN(valeur)) {
         
            total += valeur;
        } else {
            console.warn(`   ⚠️ Sous-total ${index + 1} non valide: "${texte}"`);
        }
    });
    const totalElement = document.getElementById('total-commande');
    if (totalElement) {
        const ancienTotal = totalElement.textContent;
        totalElement.textContent = `${total.toFixed(2)} DH`;
    }
    
    return total;
}

// Fonction pour sauvegarder un nouvel article immédiatement
function sauvegarderNouvelArticle(article, quantite) {

    const formData = new FormData();
    
    // Ajouter le token CSRF
    const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]');
    if (csrfToken) {
        formData.append('csrfmiddlewaretoken', csrfToken.value);
        }
        
    // Ajouter les données de l'article
    formData.append('action', 'add_article');
    formData.append('article_id', article.id);
    formData.append('quantite', quantite);
    formData.append('commande_id', '{{ commande.id }}');

    const modifierArticle = getUrlModifier();
        
    // Envoyer via AJAX
    fetch(modifierArticle, {
            method: 'POST',
            body: formData,
            headers: {
            'X-Requested-With': 'XMLHttpRequest',
            }
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
      
            // Mettre à jour l'ID de l'article dans le DOM avec l'ID réel de la base
            if (data.article_id) {
                const articleCard = document.querySelector(`[data-article-id^="new-"]`);
                if (articleCard) {
                    articleCard.setAttribute('data-article-id', data.article_id);
                    articleCard.removeAttribute('data-is-new');
                }
            }
            
            // Utiliser la fonction centralisée pour mettre à jour tous les totaux et compteurs
            const updateData = {
                total_commande: data.total_commande,
                articles_count: data.nb_articles,
                compteur: data.compteur,
                sous_total_articles: data.sous_total_articles
            };
            mettreAJourTousLesTotaux(updateData);
                
        } else {
            console.error('❌ Erreur lors de la sauvegarde:', data.error);
            showNotification('❌ Erreur lors de la sauvegarde: ' + data.error, 'error');
        }
    })
    .catch(error => {
        console.error('❌ Erreur de connexion:', error);
        showNotification('❌ Erreur de connexion lors de la sauvegarde', 'error');
    });
}


// Ajouter les événements pour la modale d'articles et les raccourcis clavier
document.addEventListener('DOMContentLoaded', function() {
    // Événement pour la sélection d'article
    const articleSelect = document.getElementById('articleSelect');
    if (articleSelect) {
        articleSelect.addEventListener('change', onArticleSelectionChange);
    }
    
    // Événement pour le changement de quantité
    const quantiteInput = document.getElementById('quantiteInput');
    if (quantiteInput) {
        quantiteInput.addEventListener('input', onQuantiteChange);
    }
    
    // Fermer la modale en cliquant à l'extérieur
    const articleModal = document.getElementById('articleModal');
    if (articleModal) {
        articleModal.addEventListener('click', function(event) {
            if (event.target === this) {
                closeArticleModal();
            }
        });
    }
    
    // Raccourcis clavier pour l'interface
    document.addEventListener('keydown', function(event) {
        // Ctrl+S désactivé - sauvegarde automatique avec les boutons "Enregistrer"
        if (event.ctrlKey && event.key === 's') {
            event.preventDefault();
            showNotification('ℹ️ Sauvegarde automatique active - utilisez les boutons "Enregistrer"', 'success');
        }
        
        // Ctrl+Enter pour confirmer la commande
        if (event.ctrlKey && event.key === 'Enter') {
            event.preventDefault();
            confirmerCommande();
        }
        
        // Escape pour fermer les modales
        if (event.key === 'Escape') {
            const commentModal = document.getElementById('commentModal');
            const articleModal = document.getElementById('articleModal');
            
            if (commentModal && commentModal.style.display === 'flex') {
                closeCommentModal();
            }
            if (articleModal && articleModal.style.display === 'flex') {
                closeArticleModal();
            }
        }
    });
    
    // Charger les commentaires depuis l'API Django
    chargerCommentairesDisponibles();
    
    // Charger les articles disponibles au chargement de la page
    chargerArticlesDisponibles();
    
    // Charger les opérations existantes depuis la base de données
    chargerOperationsExistantes();
    
    // Recalculer le total de la commande au chargement de la page
    // pour s'assurer que l'affichage correspond à la nouvelle logique de calcul

    mettreAJourTotalCommande();
    
    // Fonction alternative pour tester
    window.recalculerTotal = recalculerTotalDepuisSousTotaux;
    
    // Fonction de debug pour tester le calcul des totaux
    window.debugTotalCommande = function() {
        console.log('🔍 Debug du calcul du total de la commande:');
        
        const articlesContainer = document.getElementById('articles-container');
        if (!articlesContainer) {
            console.error('❌ Conteneur des articles introuvable');
            return;
        }
        
        const articles = articlesContainer.querySelectorAll('.article-card');
        
        let totalCalcule = 0;
        articles.forEach((article, index) => {
            const quantiteElement = article.querySelector('.text-blue-600');
            const sousTotalElement = article.querySelector('.text-lg.font-bold');
            const articleData = JSON.parse(article.dataset.article || '{}');
            
            if (quantiteElement && articleData) {
                const quantite = parseInt(quantiteElement.textContent);
                const prix = getPrixUpsell(articleData, quantite);
                const sousTotal = articleData.isUpsell ? prix : prix * quantite;
    
                totalCalcule += sousTotal;
            }
        });
        
        const totalElement = document.getElementById('total-commande');
        if (totalElement) {
            console.log(`📊 Total affiché avant recalcul: ${totalElement.textContent}`);
        }
        
        // Forcer le recalcul avec la méthode principale
        mettreAJourTotalCommande();
        if (totalElement) {
            console.log(`📊 Total affiché après recalcul principal: ${totalElement.textContent}`);
        }
        // Essayer aussi la méthode alternative
        const totalAlternatif = recalculerTotalDepuisSousTotaux();   
    };
    
    console.log('💡 Fonction de debug disponible: debugTotalCommande()');

});


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

// Fonction pour modifier la quantité d'un article (avec boutons +/-)
function modifierQuantite(panierId, delta) {
    const input = document.getElementById(`quantite-${panierId}`);
    if (input) {
        const currentValue = parseInt(input.value) || 0;
        const newValue = Math.max(1, currentValue + delta);
        input.value = newValue;
        modifierQuantiteDirecte(panierId, newValue);
    }
}

// Fonction pour modifier directement la quantité d'un article
function modifierQuantiteDirecte(panierId, nouvelleQuantite) {
    const quantite = parseInt(nouvelleQuantite);
    
    // Validation
    if (isNaN(quantite) || quantite < 1) {
        // Restaurer la valeur précédente
        const input = document.getElementById(`quantite-${panierId}`);
        if (input) {
            input.value = input.getAttribute('data-previous-value') || 1;
        }
        showToast('⚠️ La quantité doit être au moins de 1.', 'warning');
        return;
    }

    // Sauvegarder la valeur précédente
    const input = document.getElementById(`quantite-${panierId}`);
    if (input) {
        input.setAttribute('data-previous-value', input.value);
    }

    // Envoyer la modification au serveur
    const formData = new FormData();
    formData.append('action', 'update_quantity');
    formData.append('panier_id', panierId);
    formData.append('nouvelle_quantite', quantite);
    const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]');
    if (csrfToken) formData.append('csrfmiddlewaretoken', csrfToken.value);

    const modifierArticle = getUrlModifier();
    
    fetch(modifierArticle, { 
        method: 'POST', 
        body: formData 
    })
    .then(res => res.json())
    .then(data => {
        if (data.success) {
            // Mettre à jour l'affichage du sous-total et du total
            mettreAJourTotauxConfirmation(panierId, data);
            showToast('✅ Quantité mise à jour', 'success');
        } else {
            // Restaurer la valeur précédente en cas d'erreur
            if (input) {
                input.value = input.getAttribute('data-previous-value') || 1;
            }
            showToast('❌ ' + (data.error || 'Impossible de modifier la quantité.'), 'error');
        }
    })
    .catch(error => {
        console.error('❌ Erreur:', error);
        // Restaurer la valeur précédente en cas d'erreur
        if (input) {
            input.value = input.getAttribute('data-previous-value') || 1;
        }
        showToast('❌ Erreur de communication', 'error');
    });
}

// Fonction pour mettre à jour les totaux en temps réel (utilisée lors des changements de quantité)
function mettreAJourTotauxConfirmation(panierId, data) {
    // Mettre à jour le sous-total de la ligne spécifique (seulement pour les changements de quantité)
    if (data.sous_total !== undefined && panierId) {
        const sousTotalElement = document.getElementById(`sous-total-${panierId}`);
        if (sousTotalElement) {
            sousTotalElement.textContent = `${parseFloat(data.sous_total).toFixed(2)} DH`;
            console.log(`✅ Sous-total mis à jour pour article ${panierId}: ${parseFloat(data.sous_total).toFixed(2)} DH`);
        }
    }
    
    // Utiliser la fonction centralisée pour tous les autres totaux
    mettreAJourTousLesTotaux(data);
    
    // Déclencher un événement personnalisé pour signaler la mise à jour
    window.dispatchEvent(new CustomEvent('totauxMisAJour', { 
        detail: { 
            panierId: panierId,
            data: data
        }
    }));
}