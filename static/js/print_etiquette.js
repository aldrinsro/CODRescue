/**
 * Script d'impression professionnel pour les étiquettes
 * Respecte le modèle template configuré
 */

class EtiquettePrinter {
    constructor() {
        this.init();
    }

    init() {
        // Attendre que le DOM soit chargé
        if (document.readyState === 'loading') {
            document.addEventListener('DOMContentLoaded', () => this.setupPrintButtons());
        } else {
            this.setupPrintButtons();
        }
    }

    setupPrintButtons() {
        console.log('🔍 [PRINT] Configuration des boutons d\'impression...');
        
        // Vérifier si nous sommes sur une page de prévisualisation
        const isPreviewPage = document.querySelector('.etiquette-preview') !== null;
        console.log(`🔍 [PRINT] Page de prévisualisation détectée: ${isPreviewPage}`);
        
        // Ne pas ajouter de boutons automatiques sur la page de prévisualisation
        if (isPreviewPage) {
            console.log('🔍 [PRINT] Page de prévisualisation - pas d\'ajout automatique de boutons');
        } else {
            // Ajouter des boutons d'impression aux étiquettes (seulement sur les autres pages)
            const etiquetteCards = document.querySelectorAll('.etiquette-card, .theme-card');
            
            console.log(`🔍 [PRINT] Trouvé ${etiquetteCards.length} cartes d'étiquettes`);
            
            etiquetteCards.forEach((card, index) => {
                if (!card.querySelector('.print-btn')) {
                    console.log(`🔍 [PRINT] Ajout du bouton d'impression à la carte ${index + 1}`);
                    this.addPrintButton(card);
                }
            });
        }

        // Gérer les clics sur les boutons d'impression (automatiques et manuels) - TOUJOURS configuré
        this.setupClickHandlers();
    }

    setupClickHandlers() {
        console.log('🔍 [PRINT] Configuration des gestionnaires de clic...');
        
        document.addEventListener('click', (e) => {
            console.log('🔍 [PRINT] Clic détecté sur:', e.target);
            console.log('🔍 [PRINT] Classes de l\'élément:', e.target.className);
            
            // Vérifier si c'est un bouton d'impression
            const isPrintBtn = e.target.classList.contains('print-btn') || e.target.closest('.print-btn');
            const isPrintBtnManual = e.target.classList.contains('print-btn-manual') || e.target.closest('.print-btn-manual');
            
            console.log('🔍 [PRINT] Est print-btn:', isPrintBtn);
            console.log('🔍 [PRINT] Est print-btn-manual:', isPrintBtnManual);
            
            if (isPrintBtn || isPrintBtnManual) {
                e.preventDefault();
                e.stopPropagation();
                
                const button = e.target.closest('.print-btn') || e.target.closest('.print-btn-manual');
                const etiquetteId = button.dataset.etiquetteId;
                console.log(`🔍 [PRINT] Clic sur le bouton d'impression pour l'étiquette ${etiquetteId}`);
                console.log('🔍 [PRINT] Bouton trouvé:', button);
                console.log('🔍 [PRINT] Dataset:', button.dataset);
                
                if (etiquetteId) {
                    this.printEtiquette(etiquetteId);
                } else {
                    console.error('❌ [PRINT] Aucun ID d\'étiquette trouvé');
                }
            }
        });
    }

    addPrintButton(card) {
        const printButton = document.createElement('button');
        printButton.className = 'print-btn theme-button-primary';
        printButton.innerHTML = '<i class="fas fa-print"></i> Imprimer';
        printButton.dataset.etiquetteId = this.extractEtiquetteId(card);
        
        // Ajouter le bouton à la carte
        const actionsDiv = card.querySelector('.card-actions, .actions, .btn-group, .flex.justify-center');
        if (actionsDiv) {
            actionsDiv.appendChild(printButton);
        } else {
            // Créer un conteneur d'actions si il n'existe pas
            const actionsContainer = document.createElement('div');
            actionsContainer.className = 'card-actions mt-3 flex justify-center';
            actionsContainer.appendChild(printButton);
            card.appendChild(actionsContainer);
        }
        
        console.log('✅ [PRINT] Bouton d\'impression ajouté');
    }

    extractEtiquetteId(card) {
        console.log('🔍 [PRINT] Extraction de l\'ID de l\'étiquette...', card);
        
        // Méthode 1: Attribut data-etiquette-id (priorité)
        const dataId = card.dataset.etiquetteId;
        if (dataId) {
            console.log('✅ [PRINT] ID trouvé via data-etiquette-id:', dataId);
            return dataId;
        }

        // Méthode 2: Chercher dans les liens de la carte
        const links = card.querySelectorAll('a[href*="/etiquette/"]');
        for (const link of links) {
            const match = link.href.match(/\/etiquette\/(\d+)/);
            if (match) {
                console.log('✅ [PRINT] ID trouvé via lien dans la carte:', match[1]);
                return match[1];
            }
        }

        // Méthode 3: Chercher dans l'URL actuelle (si on est sur une page d'étiquette)
        const currentUrl = window.location.pathname;
        const urlMatch = currentUrl.match(/\/etiquette\/(\d+)/);
        if (urlMatch) {
            console.log('✅ [PRINT] ID trouvé via URL actuelle:', urlMatch[1]);
            return urlMatch[1];
        }

        // Méthode 4: Fallback - chercher dans tous les liens de la page
        const allLinks = document.querySelectorAll('a[href*="/etiquette/"]');
        for (const link of allLinks) {
            const match = link.href.match(/\/etiquette\/(\d+)/);
            if (match) {
                console.log('✅ [PRINT] ID trouvé via lien global:', match[1]);
                return match[1];
            }
        }

        console.error('❌ [PRINT] Aucun ID d\'étiquette trouvé');
        return null;
    }

    async printEtiquette(etiquetteId) {
        if (!etiquetteId) {
            this.showError('ID d\'étiquette non trouvé');
            return;
        }

        try {
            this.showLoading('Préparation de l\'impression...');

            // Récupérer les données de l'étiquette avec le template
            const response = await fetch(`/etiquettes-pro/etiquettes/${etiquetteId}/print-data/`, {
                method: 'GET',
                headers: {
                    'X-Requested-With': 'XMLHttpRequest',
                    'Content-Type': 'application/json',
                    'X-CSRFToken': this.getCSRFToken()
                }
            });

            if (!response.ok) {
                if (response.status === 404) {
                    throw new Error('Étiquette non trouvée');
                } else if (response.status === 500) {
                    throw new Error('Erreur serveur lors de la récupération des données');
                } else {
                    throw new Error(`Erreur HTTP: ${response.status}`);
                }
            }

            const data = await response.json();
            
            // Log des données reçues pour débogage
            console.log('🔍 [PRINT] Données reçues du serveur:', data);
            console.log('🔍 [PRINT] Template reçu:', data.template);
            console.log('🔍 [PRINT] Étiquette reçue:', data.etiquette);
            
            if (data.success) {
                // Vérifier que les données essentielles sont présentes
                if (!data.template || !data.etiquette) {
                    throw new Error('Données de template ou d\'étiquette manquantes');
                }
                
                this.openPrintWindow(data);
            } else {
                throw new Error(data.error || 'Erreur lors de la récupération des données');
            }

        } catch (error) {
            console.error('Erreur d\'impression:', error);
            
            // Messages d'erreur plus spécifiques
            let errorMessage = 'Erreur d\'impression';
            if (error.message.includes('Étiquette non trouvée')) {
                errorMessage = 'Cette étiquette n\'existe plus';
            } else if (error.message.includes('Erreur serveur')) {
                errorMessage = 'Problème de connexion au serveur';
            } else if (error.message.includes('Données manquantes')) {
                errorMessage = 'Données de l\'étiquette incomplètes';
            } else {
                errorMessage = `Erreur d'impression: ${error.message}`;
            }
            
            this.showError(errorMessage);
        } finally {
            this.hideLoading();
        }
    }

    openPrintWindow(data) {
        // Créer une nouvelle fenêtre pour l'impression
        const printWindow = window.open('', '_blank', 'width=800,height=600');
        
        if (!printWindow) {
            this.showError('Impossible d\'ouvrir la fenêtre d\'impression. Vérifiez les bloqueurs de popup.');
            return;
        }

        // Générer le HTML d'impression avec le template
        const printHTML = this.generatePrintHTML(data);
        
        printWindow.document.write(printHTML);
        printWindow.document.close();

        // Attendre que le contenu soit chargé puis imprimer
        printWindow.onload = () => {
            // Forcer les styles d'impression
            printWindow.document.body.style.webkitPrintColorAdjust = 'exact';
            printWindow.document.body.style.printColorAdjust = 'exact';
            printWindow.document.body.style.colorAdjust = 'exact';
            
            // Optimiser les images pour l'impression
            const images = printWindow.document.querySelectorAll('img');
            let loadedImages = 0;
            let totalImages = images.length;
            
            console.log(`🔍 [PRINT] ${totalImages} images à charger pour l'impression`);
            
            if (totalImages === 0) {
                // Pas d'images, imprimer directement
                setTimeout(() => {
                    printWindow.print();
                    printWindow.close();
                }, 500);
                return;
            }
            
            // Précharger et optimiser chaque image
            images.forEach((img, index) => {
                // Forcer le rechargement pour éviter le cache
                const originalSrc = img.src;
                img.src = originalSrc + '?t=' + Date.now();
                
                img.onload = () => {
                    loadedImages++;
                    console.log(`🔍 [PRINT] Image ${index + 1}/${totalImages} chargée`);
                    
                    // Optimiser l'image pour l'impression
                    img.style.imageRendering = 'crisp-edges';
                    img.style.filter = 'contrast(1.3) brightness(1.15)';
                    
                    if (loadedImages === totalImages) {
                        // Toutes les images sont chargées
                        console.log('🔍 [PRINT] Toutes les images chargées, lancement de l\'impression');
                        setTimeout(() => {
                            printWindow.print();
                            printWindow.close();
                        }, 800); // Délai plus long pour s'assurer que tout est prêt
                    }
                };
                
                img.onerror = () => {
                    loadedImages++;
                    console.warn(`⚠️ [PRINT] Erreur de chargement de l'image ${index + 1}`);
                    
                    if (loadedImages === totalImages) {
                        // Même en cas d'erreur, imprimer
                        setTimeout(() => {
                            printWindow.print();
                            printWindow.close();
                        }, 500);
                    }
                };
            });
            
            // Timeout de sécurité plus long
            setTimeout(() => {
                console.log('🔍 [PRINT] Timeout de sécurité atteint, impression forcée');
                printWindow.print();
                printWindow.close();
            }, 5000);
        };
    }

    generatePrintHTML(data) {
        console.log('🔍 [PRINT DEBUG] Début generatePrintHTML');
        console.log('  - data:', data);
        
        const template = data.template;
        const etiquette = data.etiquette;
        const commande = data.commande;
        
        console.log('🔍 [PRINT DEBUG] Variables extraites:');
        console.log('  - template:', template);
        console.log('  - etiquette:', etiquette);
        console.log('  - commande:', commande);
        console.log('  - commande.ville_init:', commande ? commande.ville_init : 'commande null');
        const totalArticles = data.total_articles || 0;

        return `
<!DOCTYPE html>
<html lang="fr">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Étiquette ${etiquette.reference}</title>
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css">
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: Arial, sans-serif;
            background: white;
            padding: 20px;
        }
        
        .etiquette-preview {
            max-width: 800px;
            margin: 0 auto;
            background: white;
            border: 2px solid #e5e7eb;
            border-radius: 8px;
            box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
        }
        
        .bg-gray-100 {
            background-color: #f3f4f6;
            padding: 24px;
            border-radius: 8px;
        }
        
        .bg-white {
            background-color: white;
        }
        
        .etiquette-container {
            overflow: hidden;
            max-width: 400px;
            margin: ${template.print_margin_top || 10}px ${template.print_margin_right || 10}px ${template.print_margin_bottom || 10}px ${template.print_margin_left || 10}px;
            padding: ${template.print_padding || 15}px;
            ${template.border_enabled ? `border: ${template.border_width}px solid ${template.border_color} !important; border-radius: ${template.border_radius}px !important;` : ''}
        }
        
        .flex {
            display: flex;
        }
        
        .flex-1 {
            flex: 1;
        }
        
        .flex-2 {
            flex: 2;
        }
        
        .items-center {
            align-items: center;
        }
        
        .justify-center {
            justify-content: center;
        }
        
        .justify-between {
            justify-content: space-between;
        }
        
        .p-3 {
            padding: 12px;
        }
        
        .p-2 {
            padding: 8px;
        }
        
        .px-2 {
            padding-left: 8px;
            padding-right: 8px;
        }
        
        .py-2 {
            padding-top: 8px;
            padding-bottom: 8px;
        }
        
        .text-center {
            text-align: center;
        }
        
        .text-white {
            color: white;
        }
        
        .text-sm {
            font-size: 14px;
        }
        
        .text-xs {
            font-size: 12px;
        }
        
        .font-bold {
            font-weight: bold;
        }
        
        .font-semibold {
            font-weight: 600;
        }
        
        .mr-1 {
            margin-right: 4px;
        }
        
        .mr-2 {
            margin-right: 8px;
        }
        
        .ml-1 {
            margin-left: 4px;
        }
        
        .ml-3 {
            margin-left: 12px;
        }
        
        .mb-1 {
            margin-bottom: 4px;
        }
        
        .mb-2 {
            margin-bottom: 8px;
        }
        
        .mt-1 {
            margin-top: 4px;
        }
        
        .w-3 {
            width: 12px;
        }
        
        .w-4 {
            width: 16px;
        }
        
        .w-5 {
            width: 20px;
        }
        
        .w-8 {
            width: 32px;
        }
        
        .w-24 {
            width: 96px;
        }
        
        .h-3 {
            height: 12px;
        }
        
        .h-4 {
            height: 16px;
        }
        
        .h-5 {
            height: 20px;
        }
        
        .h-8 {
            height: 32px;
        }
        
        .rounded-full {
            border-radius: 50%;
        }
        
        .rounded {
            border-radius: 4px;
        }
        
        .bg-blue-100 {
            background-color: #dbeafe;
        }
        
        .bg-green-100 {
            background-color: #dcfce7;
        }
        
        .bg-orange-100 {
            background-color: #fed7aa;
        }
        
        .bg-purple-100 {
            background-color: #e9d5ff;
        }
        
        .bg-indigo-100 {
            background-color: #e0e7ff;
        }
        
        .bg-yellow-100 {
            background-color: #fef3c7;
        }
        
        .bg-red-100 {
            background-color: #fee2e2;
        }
        
        .text-blue-600 {
            color: #2563eb;
        }
        
        .text-green-600 {
            color: #16a34a;
        }
        
        .text-orange-600 {
            color: #ea580c;
        }
        
        .text-purple-600 {
            color: #9333ea;
        }
        
        .text-indigo-600 {
            color: #4f46e5;
        }
        
        .text-yellow-600 {
            color: #ca8a04;
        }
        
        .text-red-600 {
            color: #dc2626;
        }
        
        .bg-gray-50 {
            background-color: #f9fafb;
        }
        
        .border-b {
            border-bottom: 1px solid #d1d5db;
        }
        
        .border-t {
            border-top: 1px solid #d1d5db;
        }
        
        .border-gray-300 {
            border-color: #d1d5db;
        }
        
        .section-with-border {
            ${template.border_enabled ? `border: ${template.border_width}px solid ${template.border_color}; border-radius: ${template.border_radius}px;` : ''}
        }
        
        .dynamic-text {
            font-family: ${template.police_texte || 'Arial, sans-serif'} !important;
            font-size: ${template.print_font_size_text || (template.taille_texte || 12) + 2}px !important;
            color: ${template.couleur_texte || '#000'} !important;
            line-height: 1.4;
        }
        
        .dynamic-title {
            font-family: ${template.police_titre || 'Arial, sans-serif'} !important;
            font-size: ${template.print_font_size_title || (template.taille_titre || 16) + 4}px !important;
            color: ${template.couleur_texte || '#000'} !important;
            font-weight: bold !important;
            line-height: 1.2;
        }
        
        .small-text {
            font-family: ${template.police_texte || 'Arial, sans-serif'} !important;
            font-size: ${template.print_font_size_small || 10}px !important;
            color: ${template.couleur_texte || '#000'} !important;
        }
        
        .code-image {
            image-rendering: -webkit-optimize-contrast;
            image-rendering: crisp-edges;
            image-rendering: pixelated;
            border: 1px solid #e5e7eb;
            border-radius: 4px;
            transition: none !important;
            animation: none !important;
            transform: none !important;
        }
        
        /* Optimisation pour l'impression haute qualité */
        @media print {
            .code-image {
                image-rendering: -webkit-optimize-contrast !important;
                image-rendering: crisp-edges !important;
                border: 1px solid #000 !important;
                width: 150px !important; /* Agrandir la largeur pour l'impression */
                height: auto !important; /* Garder la proportion */
                transition: none !important;
                animation: none !important;
                transform: none !important;
            }
        }
        
        @media print {
            @page {
                size: ${template.format_page === '10x10' ? '10cm 10cm' : 'A4'} !important;
                margin: ${template.format_page === '10x10' ? '0.3cm' : '1cm'} !important;
            }
            
            * {
                -webkit-print-color-adjust: exact !important;
                color-adjust: exact !important;
                print-color-adjust: exact !important;
            }
            
            body {
                padding: 0 !important;
                margin: 0 !important;
                background: white !important;
                font-family: Arial, sans-serif !important;
                width: ${template.format_page === '10x10' ? '10cm' : '21cm'};
                height: ${template.format_page === '10x10' ? '10cm' : '29.7cm'};
            }
            
            .etiquette-preview {
                box-shadow: none !important;
                border: none !important;
                margin: 0 !important;
                padding: 0 !important;
                width: ${template.format_page === '10x10' ? '9.4cm' : '19cm'};
                height: ${template.format_page === '10x10' ? '9.4cm' : '27.7cm'};
            }
            
            .etiquette-container {
                box-shadow: none !important;
                border: ${template.border_enabled ? template.border_width + 'px solid ' + template.border_color + ' !important' : '1px solid #000 !important'};
                page-break-inside: avoid !important;
                width: 9.4cm;
                height: 9.4cm;
                padding: 0.2cm !important;
                margin: 0 !important;
                box-sizing: border-box;
            }
            
            /* Forcer les couleurs de fond pour l'impression */
            .bg-gray-100 {
                background-color: #f3f4f6 !important;
                -webkit-print-color-adjust: exact !important;
            }
            
            .bg-white {
                background-color: white !important;
                -webkit-print-color-adjust: exact !important;
            }
            
            .bg-gray-50 {
                background-color: #f9fafb !important;
                -webkit-print-color-adjust: exact !important;
            }
            
            .text-white {
                color: white !important;
                -webkit-print-color-adjust: exact !important;
            }
            
            /* Couleurs spécifiques du template */
            .template-primary-bg {
                background-color: ${template.couleur_principale} !important;
                -webkit-print-color-adjust: exact !important;
            }
            
            .template-secondary-bg {
                background-color: ${template.couleur_secondaire} !important;
                -webkit-print-color-adjust: exact !important;
            }
            
            .template-text-color {
                color: ${template.couleur_texte} !important;
                -webkit-print-color-adjust: exact !important;
            }
            
            /* Optimisations pour l'impression */
            .flex {
                display: flex !important;
            }
            
            .items-center {
                align-items: center !important;
            }
            
            .justify-center {
                justify-content: center !important;
            }
            
            .text-center {
                text-align: center !important;
            }
            
            /* Éviter les coupures de page */
            .etiquette-container,
            .flex {
                page-break-inside: avoid !important;
            }
            
            /* Optimisation des tailles pour format 10x10 cm */
            .code-image {
                max-width: 3cm !important;
                max-height: 3cm !important;
                width: auto !important;
                height: auto !important;
            }
            
            .text-sm {
                font-size: 8px !important;
            }
            
            .text-xs {
                font-size: 6px !important;
            }
            
            .p-3 {
                padding: 0.1cm !important;
            }
            
            .p-2 {
                padding: 0.05cm !important;
            }
            
            .px-2 {
                padding-left: 0.1cm !important;
                padding-right: 0.1cm !important;
            }
            
            .py-2 {
                padding-top: 0.05cm !important;
                padding-bottom: 0.05cm !important;
            }
        }
    </style>
</head>
<body>
    <div class="etiquette-preview">
        <div class="bg-gray-100 p-6 rounded-lg">
            <div class="bg-white etiquette-container overflow-hidden max-w-md mx-auto">
                <!-- Ligne 1: Code-barres et date -->
                <div class="flex">
                    <div class="flex-1 p-3 flex items-center section-with-border template-secondary-bg" style="background-color: ${template.couleur_secondaire} !important;">
                        <!-- Code visuel (Code-barres ou QR Code) -->
                        ${template.code_type === 'barcode' || template.code_type === 'both' ? `
                            <img src="${window.location.origin}/etiquettes-pro/barcode/${etiquette.code_data}/" 
                                 alt="Barcode" 
                                 class="mr-2 code-image"
                                 style="height: ${template.print_code_height || 80}px; width: ${template.print_code_width || 250}px;"/>
                         ` : template.code_type === 'qr' ? `
                             <img src="${window.location.origin}/etiquettes-pro/qrcode/${etiquette.code_data}/" 
                                  alt="QR Code" 
                                  class="mr-2 code-image"
                                 style="height: ${template.print_code_height || 80}px; width: ${template.print_code_width || 250}px;"/>
                        ` : ''}
                        <div class="dynamic-title font-bold">${etiquette.reference}</div>
                    </div>
                    
                    <!-- Cercle avec le total d'articles au milieu entre ID YZ et date -->
                    ${totalArticles > 0 && template.print_show_total_circle !== false ? `
                    <div class="flex items-center justify-center px-2">
                        <div class="flex items-center justify-center w-8 h-8 rounded-full text-white font-bold text-sm" 
                             style="background-color: ${template.couleur_principale}; border: ${template.border_width}px solid ${template.border_color};">
                            ${totalArticles}
                        </div>
                    </div>
                    ` : ''}
                    
                    ${template.print_show_date !== false ? `
                    <div class="w-24 text-white p-3 flex items-center justify-center section-with-border template-primary-bg" style="background-color: ${template.couleur_principale} !important;">
                        <div class="text-sm font-bold text-center">${this.formatDate(new Date())}</div>
                    </div>
                    ` : ''}
                </div>
                
                <!-- Ligne 2: Informations client avec icônes professionnelles -->
                ${(() => {
                    console.log('🔍 [PRINT DEBUG] Vérification section client:');
                    console.log('  - template.print_show_client_info:', template.print_show_client_info);
                    console.log('  - Condition (template.print_show_client_info !== false):', template.print_show_client_info !== false);
                    return template.print_show_client_info !== false;
                })() ? `
                <div class="bg-gray-50 p-3">
                    ${commande && commande.client ? `
                        <div class="dynamic-text flex items-center">
                            <div class="w-4 h-4 bg-blue-100 rounded-full flex items-center justify-center mr-2">
                                <i class="${template.icone_client} text-blue-600 text-xs"></i>
                            </div>
                            <span>Client: ${commande.client.nom} ${commande.client.prenom}</span>
                        </div>
                        ${commande.client.numero_tel ? `
                        <div class="dynamic-text flex items-center">
                            <div class="w-4 h-4 bg-green-100 rounded-full flex items-center justify-center mr-2">
                                <i class="${template.icone_telephone} text-green-600 text-xs"></i>
                            </div>
                            <span>Tél: ${commande.client.numero_tel}</span>
                        </div>
                        ` : ''}
                        ${commande.client.adresse ? `
                        <div class="dynamic-text flex items-center">
                            <div class="w-4 h-4 bg-orange-100 rounded-full flex items-center justify-center mr-2">
                                <i class="${template.icone_adresse} text-orange-600 text-xs"></i>
                            </div>
                            <span>Adresse: ${commande.client.adresse}</span>
                        </div>
                        ` : ''}
                    ` : etiquette.client_nom ? `
                        <div class="dynamic-text flex items-center">
                            <div class="w-4 h-4 bg-blue-100 rounded-full flex items-center justify-center mr-2">
                                <i class="fas fa-user text-blue-600 text-xs"></i>
                            </div>
                            <span>Client: ${etiquette.client_nom}</span>
                        </div>
                    ` : `
                        <div class="dynamic-text flex items-center">
                            <div class="w-4 h-4 bg-gray-100 rounded-full flex items-center justify-center mr-2">
                                <i class="fas fa-exclamation-triangle text-gray-600 text-xs"></i>
                            </div>
                            <span>Informations client non disponibles</span>
                        </div>
                    `}
                    
                    <!-- Ville du client - affichée indépendamment de commande.client -->
                    ${(() => {
                        console.log('🔍 [PRINT DEBUG] Vérification ville_init:');
                        console.log('  - commande:', commande);
                        console.log('  - commande.ville_init:', commande ? commande.ville_init : 'commande null');
                        console.log('  - Condition (commande && commande.ville_init):', commande && commande.ville_init);
                        return commande && commande.ville_init ? `
                        <div class="dynamic-text flex items-center">
                            <div class="w-4 h-4 bg-purple-100 rounded-full flex items-center justify-center mr-2">
                                <i class="${template.icone_ville} text-purple-600 text-xs"></i>
                            </div>
                            <span>Ville: ${commande.ville_init}</span>
                        </div>
                        ` : '';
                    })()}
                </div>
                ` : ''}
                
                <!-- Ligne 2.5: Articles du panier avec icônes professionnelles -->
                ${etiquette.cart_items && etiquette.cart_items.length > 0 && template.print_show_articles !== false ? `
                <div class="bg-gray-50 p-3">
                    <div class="dynamic-text font-bold mb-2 flex items-center">
                        <div class="w-4 h-4 bg-indigo-100 rounded-full flex items-center justify-center mr-2">
                            <i class="${template.icone_panier} text-indigo-600 text-xs"></i>
                        </div>
                        <span>Articles du panier:</span>
                    </div>
                    ${etiquette.cart_items.map(item => `
                        <div class="dynamic-text text-sm ml-3 flex items-center mb-1">
                            <div class="w-3 h-3 bg-yellow-100 rounded-full flex items-center justify-center mr-2">
                                <i class="${template.icone_article} text-yellow-600 text-xs"></i>
                            </div>
                            <span>${item.nom} ${item.variante} x${item.quantite}</span>
                            <!-- Prix individuels masqués lors de l'impression -->
                        </div>
                    `).join('')}
                </div>
                ` : ''}

                <!-- Ligne de séparation -->
                <div class="border-b mx-3" style="border-width: ${template.border_width}px; border-color: ${template.border_color};"></div>
                
                <!-- Ligne 3: Article -->
                <div class="bg-gray-50 p-3 text-center">
                    <div class="font-bold flex items-center justify-center gap-3">
                        ${etiquette.nom_article || (commande && commande.num_cmd) || (commande && commande.id_yz) || etiquette.commande_id}
                        
                        <!-- Cercle avec le total d'articles -->
                        ${totalArticles > 0 ? `
                        <div class="flex items-center justify-center w-8 h-8 rounded-full text-white font-bold text-sm" 
                             style="background-color: ${template.couleur_principale}; border: ${template.border_width}px solid ${template.border_color};">
                            ${totalArticles}
                        </div>
                        ` : ''}
                    </div>
                </div>
                
                <!-- Séparateur -->
                <div class="border-t border-gray-300"></div>
                
                <!-- Ligne 4: Prix et contact avec icônes professionnelles -->
                <div class="flex">
                    <div class="flex-1 bg-gray-50 p-3 contact-info-section">
                        ${template.print_show_prices !== false ? `
                        <div class="font-bold flex items-center mb-1">
                            <div class="w-5 h-5 bg-green-100 rounded-full flex items-center justify-center mr-2">
                                <i class="${template.icone_prix} text-green-600 text-sm"></i>
                            </div>
                            <span>
                                ${commande && commande.total_cmd ? `${commande.total_cmd} DH` : 'Prix non disponible'}
                            </span>
                        </div>
                        ` : ''}
                        ${template.print_show_brand !== false ? `
                        <div class="text-sm flex items-center">
                            <div class="w-4 h-4 bg-red-100 rounded-full flex items-center justify-center mr-2">
                                <i class="${template.icone_marque} text-red-600 text-xs"></i>
                            </div>
                            <span>YOZAK</span>
                        </div>
                        ` : ''}
                    </div>
                    ${template.print_show_contact_info !== false ? `
                    <div class="text-white p-3 text-center section-with-border contact-info-section" style="background-color: ${template.couleur_principale}; width: ${template.print_contact_width || 250}px;">
                        <div class="text-sm font-bold flex items-center justify-center">
                            <i class="${template.icone_ville} mr-1"></i>
                            <span>${commande && commande.ville ? commande.ville.nom : 'VILLE NON DÉFINIE'}</span>
                        </div>
                        <div class="text-xs flex items-center justify-center">
                            <i class="${template.icone_website} mr-1"></i>
                            <span>www.yoozak.com</span>
                        </div>
                        <div class="text-xs flex items-center justify-center">
                            <i class="${template.icone_telephone} mr-1"></i>
                            <span>06 34 21 56 39 / 47</span>
                        </div>
                    </div>
                    ` : ''}
                </div>
            </div>
        </div>
    </div>
</body>
</html>`;
    }

    showLoading(message) {
        // Créer ou mettre à jour l'indicateur de chargement
        let loading = document.getElementById('print-loading');
        if (!loading) {
            loading = document.createElement('div');
            loading.id = 'print-loading';
            loading.className = 'print-loading-overlay';
            loading.innerHTML = `
                <div class="print-loading-content">
                    <div class="spinner"></div>
                    <p>${message}</p>
                </div>
            `;
            document.body.appendChild(loading);
        } else {
            loading.querySelector('p').textContent = message;
        }
        
        // Ajouter les styles si nécessaire
        if (!document.getElementById('print-loading-styles')) {
            const styles = document.createElement('style');
            styles.id = 'print-loading-styles';
            styles.textContent = `
                .print-loading-overlay {
                    position: fixed;
                    top: 0;
                    left: 0;
                    width: 100%;
                    height: 100%;
                    background: rgba(0, 0, 0, 0.5);
                    display: flex;
                    justify-content: center;
                    align-items: center;
                    z-index: 9999;
                }
                
                .print-loading-content {
                    background: white;
                    padding: 30px;
                    border-radius: 10px;
                    text-align: center;
                    box-shadow: 0 4px 20px rgba(0, 0, 0, 0.3);
                }
                
                .spinner {
                    width: 40px;
                    height: 40px;
                    border: 4px solid #f3f3f3;
                    border-top: 4px solid #3498db;
                    border-radius: 50%;
                    animation: spin 1s linear infinite;
                    margin: 0 auto 15px;
                }
                
                @keyframes spin {
                    0% { transform: rotate(0deg); }
                    100% { transform: rotate(360deg); }
                }
            `;
            document.head.appendChild(styles);
        }
    }

    hideLoading() {
        const loading = document.getElementById('print-loading');
        if (loading) {
            loading.remove();
        }
    }

    showError(message) {
        // Créer une notification d'erreur
        const errorDiv = document.createElement('div');
        errorDiv.className = 'print-error-notification';
        errorDiv.innerHTML = `
            <div class="error-content">
                <i class="fas fa-exclamation-triangle"></i>
                <span>${message}</span>
                <button onclick="this.parentElement.parentElement.remove()">×</button>
            </div>
        `;
        
        // Ajouter les styles si nécessaire
        if (!document.getElementById('print-error-styles')) {
            const styles = document.createElement('style');
            styles.id = 'print-error-styles';
            styles.textContent = `
                .print-error-notification {
                    position: fixed;
                    top: 20px;
                    right: 20px;
                    background: #ff4444;
                    color: white;
                    padding: 15px 20px;
                    border-radius: 5px;
                    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.3);
                    z-index: 10000;
                    animation: slideIn 0.3s ease-out;
                }
                
                .error-content {
                    display: flex;
                    align-items: center;
                    gap: 10px;
                }
                
                .error-content button {
                    background: none;
                    border: none;
                    color: white;
                    font-size: 18px;
                    cursor: pointer;
                    padding: 0;
                    width: 20px;
                    height: 20px;
                }
                
                @keyframes slideIn {
                    from { transform: translateX(100%); opacity: 0; }
                    to { transform: translateX(0); opacity: 1; }
                }
            `;
            document.head.appendChild(styles);
        }
        
        document.body.appendChild(errorDiv);
        
        // Supprimer automatiquement après 5 secondes
        setTimeout(() => {
            if (errorDiv.parentElement) {
                errorDiv.remove();
            }
        }, 5000);
    }

    getCSRFToken() {
        // Récupérer le token CSRF depuis les cookies ou le DOM
        const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]')?.value ||
                         document.cookie.match(/csrftoken=([^;]+)/)?.[1] ||
                         '';
        console.log('🔍 [PRINT] Token CSRF récupéré:', csrfToken ? 'Oui' : 'Non');
        return csrfToken;
    }

    formatDate(date) {
        // Formater la date au format m/d/Y (ex: 7/9/2025)
        const month = date.getMonth() + 1;
        const day = date.getDate();
        const year = date.getFullYear();
        return `${month}/${day}/${year}`;
    }
}

// Exposer la classe globalement
window.EtiquettePrinter = EtiquettePrinter;

// Initialiser l'imprimeur d'étiquettes
console.log('🔍 [PRINT] Initialisation du système d\'impression...');
window.etiquettePrinter = new EtiquettePrinter();
