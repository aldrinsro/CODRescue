/**
 * Gestionnaire des dropdowns pour la sidebar operatConfirme
 * Fichier JavaScript séparé pour éviter les conflits
 * Version: 1.0.0
 */

(function() {
    'use strict';

    // Configuration
    const CONFIG = {
        DEBUG: true,
        ANIMATION_DURATION: 200
    };

    // Variables globales du module
    let isInitialized = false;

    /**
     * Fonction de logging pour le debug
     */
    function log(message, data = {}) {
        if (!CONFIG.DEBUG) return;
        
        const timestamp = new Date().toISOString();
        const pageUrl = window.location.pathname;
        console.log(`📋 [SidebarDropdowns] [${timestamp}] [${pageUrl}] ${message}`, data);
    }

    /**
     * Toggle d'un dropdown par ID (pour compatibilité avec fonction existante)
     */
    function toggleDropdown(id) {
        log(`🔽 toggleDropdown appelée pour: ${id}`);
        
        const dropdown = document.getElementById(id);
        const icon = document.getElementById(id + '-icon');
        
        if (!dropdown) {
            log(`❌ Dropdown non trouvé: ${id}`);
            return;
        }
        
        const wasHidden = dropdown.classList.contains('hidden');
        dropdown.classList.toggle('hidden');
        
        if (icon) {
            icon.classList.toggle('rotate-180');
        }
        
        log(`📊 Dropdown ${id} ${wasHidden ? 'ouvert' : 'fermé'}`, {
            wasHidden: wasHidden,
            nowHidden: dropdown.classList.contains('hidden'),
            hasIcon: !!icon
        });
    }

    /**
     * Gestion des dropdowns avec data-target
     */
    function handleDataTargetDropdowns() {
        log('🔗 Configuration des dropdowns avec data-target');
        
        const toggleButtons = document.querySelectorAll('.toggle-dropdown');
        
        log(`📋 Trouvé ${toggleButtons.length} boutons toggle-dropdown`);
        
        toggleButtons.forEach((button, index) => {
            const target = button.getAttribute('data-target');
            const targetElement = target ? document.querySelector(target) : null;
            const chevronIcon = button.querySelector('.fa-chevron-down');
            
            log(`🔘 Bouton ${index + 1}:`, {
                target: target,
                targetExists: !!targetElement,
                hasChevron: !!chevronIcon,
                buttonClasses: button.className
            });
            
            if (!targetElement) {
                log(`❌ Élément cible non trouvé pour: ${target}`);
                return;
            }
            
            // Supprimer les listeners existants en clonant l'élément
            const newButton = button.cloneNode(true);
            button.parentNode.replaceChild(newButton, button);
            
            // Récupérer la nouvelle référence des éléments
            const newTargetElement = document.querySelector(target);
            const newChevronIcon = newButton.querySelector('.fa-chevron-down');
            
            newButton.addEventListener('click', function(e) {
                e.preventDefault();
                e.stopPropagation();
                
                log(`🖱️ Clic sur dropdown button`, {
                    target: target,
                    currentlyHidden: newTargetElement.classList.contains('hidden')
                });
                
                const wasHidden = newTargetElement.classList.contains('hidden');
                
                // Toggle du dropdown
                newTargetElement.classList.toggle('hidden');
                
                // Animation de l'icône chevron
                if (newChevronIcon) {
                    if (wasHidden) {
                        newChevronIcon.style.transform = 'rotate(180deg)';
                    } else {
                        newChevronIcon.style.transform = 'rotate(0deg)';
                    }
                }
                
                log(`📊 Dropdown toggle effectué`, {
                    target: target,
                    wasHidden: wasHidden,
                    nowHidden: newTargetElement.classList.contains('hidden'),
                    chevronRotated: newChevronIcon ? newChevronIcon.style.transform : 'no-chevron'
                });
            });
            
            log(`✅ Event listener attaché pour: ${target}`);
        });
    }

    /**
     * Fermeture des dropdowns en cliquant ailleurs
     */
    function setupOutsideClickClose() {
        log('👆 Configuration fermeture au clic extérieur');
        
        document.addEventListener('click', function(event) {
            const dropdowns = document.querySelectorAll('#sidebar .toggle-dropdown');
            
            dropdowns.forEach(button => {
                const target = button.getAttribute('data-target');
                const dropdown = target ? document.querySelector(target) : null;
                
                if (!dropdown || dropdown.classList.contains('hidden')) {
                    return; // Déjà fermé
                }
                
                // Vérifier si le clic est à l'extérieur du bouton et du dropdown
                if (!button.contains(event.target) && !dropdown.contains(event.target)) {
                    dropdown.classList.add('hidden');
                    
                    const chevronIcon = button.querySelector('.fa-chevron-down');
                    if (chevronIcon) {
                        chevronIcon.style.transform = 'rotate(0deg)';
                    }
                    
                    log(`👆 Dropdown fermé par clic extérieur: ${target}`);
                }
            });
        });
    }

    /**
     * Diagnostic des dropdowns
     */
    function diagnosticDropdowns() {
        const diagnostic = {
            toggleButtons: [],
            dropdowns: [],
            existingFunction: typeof window.toggleDropdown === 'function'
        };
        
        // Analyse des boutons toggle
        const toggleButtons = document.querySelectorAll('.toggle-dropdown');
        toggleButtons.forEach((button, index) => {
            const target = button.getAttribute('data-target');
            const targetElement = target ? document.querySelector(target) : null;
            
            diagnostic.toggleButtons.push({
                index: index,
                target: target,
                targetExists: !!targetElement,
                buttonId: button.id,
                buttonClasses: button.className
            });
        });
        
        // Analyse des dropdowns
        const dropdowns = document.querySelectorAll('#sidebar [id*="menu"], #sidebar [id*="dropdown"]');
        dropdowns.forEach((dropdown, index) => {
            diagnostic.dropdowns.push({
                index: index,
                id: dropdown.id,
                classes: dropdown.className,
                isHidden: dropdown.classList.contains('hidden')
            });
        });
        
        log('🔍 Diagnostic des dropdowns', diagnostic);
        return diagnostic;
    }

    /**
     * Initialisation du module
     */
    function initialize() {
        if (isInitialized) {
            log('⚠️ Module déjà initialisé, skip');
            return false;
        }
        
        log('🔧 Début d\'initialisation des dropdowns sidebar');
        
        try {
            // Diagnostic initial
            diagnosticDropdowns();
            
            // Configuration des dropdowns avec data-target
            handleDataTargetDropdowns();
            
            // Configuration de la fermeture au clic extérieur
            setupOutsideClickClose();
            
            // Exposer la fonction toggleDropdown globalement (compatibilité)
            if (typeof window.toggleDropdown !== 'function') {
                window.toggleDropdown = toggleDropdown;
                log('✅ Fonction toggleDropdown exposée globalement');
            }
            
            isInitialized = true;
            log('✅ Initialisation des dropdowns terminée avec succès');
            return true;
            
        } catch (error) {
            log('💥 Erreur lors de l\'initialisation des dropdowns', {
                error: error.message,
                stack: error.stack
            });
            return false;
        }
    }

    /**
     * API publique du module
     */
    window.SidebarDropdowns = {
        // Méthodes principales
        init: initialize,
        toggle: toggleDropdown,
        
        // Méthodes de debug
        diagnostic: diagnosticDropdowns,
        
        // Statut
        isInitialized: () => isInitialized
    };

    /**
     * Auto-initialisation
     */
    function autoInit() {
        log('🚀 Auto-initialisation des dropdowns sidebar');
        
        // Tentative 1: DOMContentLoaded
        if (document.readyState === 'loading') {
            log('📄 DOM en cours de chargement, attente DOMContentLoaded');
            document.addEventListener('DOMContentLoaded', initialize);
        } else {
            log('📄 DOM déjà chargé, initialisation immédiate');
            initialize();
        }
        
        // Tentatives de fallback
        setTimeout(() => {
            if (!isInitialized) {
                log('⏰ Tentative fallback (300ms)');
                initialize();
            }
        }, 300);
        
        setTimeout(() => {
            if (!isInitialized) {
                log('⏰ Tentative fallback (800ms)');
                initialize();
            }
        }, 800);
    }
    
    // Démarrage automatique
    autoInit();

})();
