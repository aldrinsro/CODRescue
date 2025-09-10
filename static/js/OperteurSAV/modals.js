/**
 * Gestion des modales pour l'opérateur SAV
 * Ce fichier contient toutes les fonctions d'ouverture et fermeture des modales
 */

// Variables globales pour les modales
let currentCommandeId = null;
let currentCommandeIdYz = null;
let currentCommandePayement = null;

/**
 * Ouvre la modale SAV avec l'état spécifié
 * @param {string} etat - L'état de la commande (Livrée, Retournée, etc.)
 */
function openSavModal(etat) {
    console.log('🔧 DEBUG: openSavModal appelée avec etat:', etat);
    
    // Stocker les informations de la commande
    currentCommandeId = document.querySelector('[data-commande-id]')?.dataset.commandeId;
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
 */
function ouvrirModalLivraisonPartielle() {
    console.log('🔧 DEBUG: ouvrirModalLivraisonPartielle appelée');
    
    const modal = document.getElementById('livraisonPartielleModal');
    if (modal) {
        modal.classList.remove('hidden');
        console.log('✅ Modale de livraison partielle ouverte');
        
        // Initialiser la modale
        initialiserModalLivraisonPartielle();
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
    mettreAJourSectionArticlesRenvoyes();
    mettreAJourResumeLivraisonPartielle();
    
    console.log('✅ Modale de livraison partielle initialisée');
}

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
});
