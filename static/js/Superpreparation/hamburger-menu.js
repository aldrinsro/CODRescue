/**
 * Gestionnaire du bouton hamburger pour l'interface Superpreparation
 * Fichier JavaScript séparé pour éviter les conflits
 * Version: 1.0.0
 */

(function() {
    'use strict';

    // Configuration
    const CONFIG = {
        DESKTOP_BREAKPOINT: 1024,
        MOBILE_BREAKPOINT: 1023,
        ANIMATION_DURATION: 300,
        DEBUG: true
    };

    // Variables globales du module
    let isInitialized = false;
    let elements = {};

    /**
     * Fonction de logging pour le debug
     */
    function log(message, data = {}) {
        if (!CONFIG.DEBUG) return;
        
        const timestamp = new Date().toISOString();
        const pageUrl = window.location.pathname;
        console.log(`🍔 [HamburgerMenu-Superpreparation] [${timestamp}] [${pageUrl}] ${message}`, data);
    }

    /**
     * Récupération des éléments DOM
     */
    function getElements() {
        return {
            body: document.body,
            menuToggle: document.getElementById('menu-toggle'),
            sidebar: document.getElementById('sidebar'),
            sidebarToggle: document.getElementById('sidebar-toggle'),
            contentOverlay: document.getElementById('content-overlay')
        };
    }

    /**
     * Vérification de la disponibilité des éléments requis
     */
    function validateElements() {
        const required = ['body', 'menuToggle', 'sidebar'];
        const missing = required.filter(key => !elements[key]);
        
        if (missing.length > 0) {
            log('❌ Éléments manquants:', missing);
            return false;
        }
        
        log('✅ Tous les éléments requis sont présents');
        return true;
    }

    /**
     * Diagnostic complet du DOM
     */
    function diagnosticDOM() {
        const diagnostic = {
            elements: {},
            window: {
                width: window.innerWidth,
                height: window.innerHeight,
                isDesktop: window.innerWidth >= CONFIG.DESKTOP_BREAKPOINT
            },
            body: {
                classes: document.body.className,
                hasOpenClass: document.body.classList.contains('sidebar-open'),
                hasCollapsedClass: document.body.classList.contains('sidebar-collapsed')
            }
        };

        // Diagnostic de chaque élément
        Object.keys(elements).forEach(key => {
            const element = elements[key];
            diagnostic.elements[key] = {
                exists: !!element,
                id: element?.id,
                classes: element?.className,
                tagName: element?.tagName
            };

            if (key === 'sidebar' && element) {
                const styles = window.getComputedStyle(element);
                diagnostic.elements[key].styles = {
                    width: styles.width,
                    transform: styles.transform,
                    position: styles.position,
                    display: styles.display,
                    visibility: styles.visibility
                };
            }
        });

        log('🔍 Diagnostic DOM complet', diagnostic);
        return diagnostic;
    }

    /**
     * Toggle de la sidebar avec logs détaillés
     */
    function toggleSidebar() {
        log('🖱️ toggleSidebar appelée');
        
        if (!elements.sidebar || !elements.body) {
            log('❌ Éléments manquants pour le toggle');
            return;
        }

        // Capture de l'état avant
        const beforeState = {
            bodyClasses: elements.body.className,
            sidebarWidth: window.getComputedStyle(elements.sidebar).width,
            sidebarTransform: window.getComputedStyle(elements.sidebar).transform,
            isOpen: elements.body.classList.contains('sidebar-open'),
            isCollapsed: elements.body.classList.contains('sidebar-collapsed')
        };

        // Toggle des classes
        elements.body.classList.toggle('sidebar-open');
        elements.body.classList.toggle('sidebar-collapsed');

        // Toggle de l'animation du hamburger
        if (elements.menuToggle) {
            elements.menuToggle.classList.toggle('hamburger-active');
        }

        // Forcer un recalcul des styles
        elements.sidebar.offsetWidth;

        // Capture de l'état après
        const afterState = {
            bodyClasses: elements.body.className,
            sidebarWidth: window.getComputedStyle(elements.sidebar).width,
            sidebarTransform: window.getComputedStyle(elements.sidebar).transform,
            isOpen: elements.body.classList.contains('sidebar-open'),
            isCollapsed: elements.body.classList.contains('sidebar-collapsed')
        };

        log('📊 Toggle sidebar effectué', {
            before: beforeState,
            after: afterState,
            windowWidth: window.innerWidth,
            isDesktop: window.innerWidth >= CONFIG.DESKTOP_BREAKPOINT
        });

        // Gestion de l'overlay sur mobile
        updateOverlay();
    }

    /**
     * Fermeture de la sidebar sur mobile
     */
    function closeSidebarMobile() {
        const shouldClose = window.innerWidth <= CONFIG.MOBILE_BREAKPOINT;
        
        log('📱 closeSidebarMobile appelée', {
            windowWidth: window.innerWidth,
            shouldClose: shouldClose
        });

        if (shouldClose && elements.body) {
            elements.body.classList.add('sidebar-collapsed');
            elements.body.classList.remove('sidebar-open');
            
            // Retirer l'animation du hamburger
            if (elements.menuToggle) {
                elements.menuToggle.classList.remove('hamburger-active');
            }
            
            updateOverlay();
            
            log('✅ Sidebar fermée sur mobile');
        }
    }

    /**
     * Mise à jour de l'overlay
     */
    function updateOverlay() {
        if (!elements.contentOverlay) return;

        const isOpen = elements.body.classList.contains('sidebar-open');
        const isMobile = window.innerWidth <= CONFIG.MOBILE_BREAKPOINT;
        
        if (isOpen && isMobile) {
            elements.contentOverlay.style.display = 'block';
            // Forcer l'opacité après un petit délai pour l'animation
            setTimeout(() => {
                elements.contentOverlay.style.opacity = '1';
            }, 10);
        } else {
            elements.contentOverlay.style.opacity = '0';
            setTimeout(() => {
                elements.contentOverlay.style.display = 'none';
            }, CONFIG.ANIMATION_DURATION);
        }
    }

    /**
     * Définition de l'état initial de la sidebar
     */
    function setInitialState() {
        if (!elements.body) return;

        const isDesktop = window.innerWidth >= CONFIG.DESKTOP_BREAKPOINT;
        
        log('📏 Définition état initial', {
            windowWidth: window.innerWidth,
            isDesktop: isDesktop
        });

        // Nettoyer les classes existantes
        elements.body.classList.remove('sidebar-open', 'sidebar-collapsed');

        if (isDesktop) {
            elements.body.classList.add('sidebar-open');
            log('💻 État initial: desktop (sidebar ouverte)');
        } else {
            elements.body.classList.add('sidebar-collapsed');
            log('📱 État initial: mobile (sidebar fermée)');
        }

        updateOverlay();
    }

    /**
     * Gestion du redimensionnement de la fenêtre
     */
    function handleResize() {
        const newWidth = window.innerWidth;
        const isDesktop = newWidth >= CONFIG.DESKTOP_BREAKPOINT;
        
        log('📏 Redimensionnement détecté', {
            newWidth: newWidth,
            isDesktop: isDesktop
        });

        if (!elements.body) return;

        if (isDesktop) {
            elements.body.classList.add('sidebar-open');
            elements.body.classList.remove('sidebar-collapsed');
            log('💻 Passage en mode desktop');
        } else {
            elements.body.classList.add('sidebar-collapsed');
            elements.body.classList.remove('sidebar-open');
            log('📱 Passage en mode mobile');
        }

        updateOverlay();
    }

    /**
     * Attachement des event listeners
     */
    function attachEventListeners() {
        log('🔗 Attachement des event listeners');

        // Listener principal du bouton hamburger
        if (elements.menuToggle) {
            // Supprimer les listeners existants en clonant l'élément
            const newMenuToggle = elements.menuToggle.cloneNode(true);
            elements.menuToggle.parentNode.replaceChild(newMenuToggle, elements.menuToggle);
            elements.menuToggle = newMenuToggle;

            elements.menuToggle.addEventListener('click', function(e) {
                log('🖱️ Clic sur menu-toggle détecté', {
                    event: {
                        type: e.type,
                        target: e.target.id,
                        timestamp: e.timeStamp
                    }
                });
                
                e.preventDefault();
                e.stopPropagation();
                toggleSidebar();
            });

            log('✅ Event listener attaché sur menuToggle');
        }

        // Listener pour fermer via le bouton X de la sidebar
        if (elements.sidebarToggle) {
            elements.sidebarToggle.addEventListener('click', closeSidebarMobile);
            log('✅ Event listener attaché sur sidebarToggle');
        }

        // Listener pour fermer via l'overlay
        if (elements.contentOverlay) {
            elements.contentOverlay.addEventListener('click', closeSidebarMobile);
            log('✅ Event listener attaché sur contentOverlay');
        }

        // Listener pour le redimensionnement
        window.addEventListener('resize', handleResize);
        log('✅ Event listener attaché sur window.resize');
    }

    /**
     * Initialisation du module
     */
    function initialize() {
        if (isInitialized) {
            log('⚠️ Module déjà initialisé, skip');
            return false;
        }

        log('🔧 Début d\'initialisation du module hamburger Superpreparation');

        try {
            // Récupération des éléments
            elements = getElements();
            
            // Validation
            if (!validateElements()) {
                log('❌ Validation échouée, abandon de l\'initialisation');
                return false;
            }

            // Diagnostic initial
            diagnosticDOM();

            // Configuration de l'état initial
            setInitialState();

            // Attachement des event listeners
            attachEventListeners();

            // Marquer comme initialisé
            isInitialized = true;

            log('✅ Initialisation terminée avec succès');
            return true;

        } catch (error) {
            log('💥 Erreur lors de l\'initialisation', {
                error: error.message,
                stack: error.stack,
                name: error.name
            });
            return false;
        }
    }

    /**
     * Fonction de réinitialisation (pour debug)
     */
    function reinitialize() {
        log('🔄 Réinitialisation forcée');
        isInitialized = false;
        elements = {};
        initialize();
    }

    /**
     * API publique du module
     */
    window.HamburgerMenuSuperpreparation = {
        // Méthodes principales
        init: initialize,
        reinit: reinitialize,
        toggle: toggleSidebar,
        close: closeSidebarMobile,
        
        // Méthodes de debug
        diagnostic: diagnosticDOM,
        getElements: () => elements,
        getConfig: () => CONFIG,
        
        // Statut
        isInitialized: () => isInitialized
    };

    /**
     * Auto-initialisation
     */
    function autoInit() {
        log('🚀 Auto-initialisation du module Superpreparation');

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
                log('⏰ Tentative fallback (100ms)');
                initialize();
            }
        }, 100);

        setTimeout(() => {
            if (!isInitialized) {
                log('⏰ Tentative fallback (500ms)');
                initialize();
            }
        }, 500);

        setTimeout(() => {
            if (!isInitialized) {
                log('💥 ÉCHEC: Module non initialisé après 1s');
                diagnosticDOM();
            }
        }, 1000);
    }

    // Démarrage automatique
    autoInit();

})();
