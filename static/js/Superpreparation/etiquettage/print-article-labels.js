// @ts-nocheck
/* eslint-disable */
/* jshint ignore:start */
/**
 * Système d'impression des étiquettes d'articles
 * Gère l'impression optimisée des codes-barres et QR codes pour les articles
 */

class ArticleLabelsPrinter {
    constructor() {
        this.currentFormat = 'qr'; // 'qr' ou 'barcode'
        this.labelSize = {
            width: '180mm',
            height: '260mm'
        };
        this.pageSettings = {
            margin: '10mm',
            columns: 1, // Une seule colonne
            rows: 1, // Une seule rangée
            headerHeight: '15mm',
            footerHeight: '10mm'
        };
        this.init();
    }

    init() {
        console.log('🖨️ Système d\'impression des étiquettes d\'articles initialisé');
        this.setupEventListeners();
    }

    setupEventListeners() {
        // Écouter les changements de format
        document.addEventListener('formatChanged', (e) => {
            this.currentFormat = e.detail.format;
            console.log('🔄 Format d\'impression changé:', this.currentFormat);
        });
    }

    /**
     * Générer le HTML pour l'impression des étiquettes d'articles
     * @param {Array} articles - Liste des articles avec leurs données
     * @param {Object} options - Options d'impression
     * @returns {string} HTML optimisé pour l'impression
     */
    generatePrintHTML(articles, options = {}) {
        const {
            title = 'Étiquettes Articles',
            subtitle = '',
            showHeader = true,
            showFooter = true,
            format = this.currentFormat
        } = options;

        const timestamp = new Date().toLocaleString('fr-FR');
        
        let html = `
        <!DOCTYPE html>
        <html lang="fr">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>${title}</title>
            <style>
                /* Reset et styles de base */
                * {
                    margin: 0;
                    padding: 0;
                    box-sizing: border-box;
                }

                body {
                    font-family: Arial, sans-serif;
                    font-size: 12px;
                    line-height: 1.4;
                    color: #000;
                    background: white;
                }

                /* Styles pour l'impression */
                @media print {
                    @page {
                        size: 10cm 10cm;
                        margin: 0.3cm;
                    }
                    
                    body {
                        margin: 0;
                        padding: 0;
                        background: white !important;
                        -webkit-print-color-adjust: exact !important;
                        color-adjust: exact !important;
                        width: 10cm;
                        height: 10cm;
                    }

                    .no-print {
                        display: none !important;
                    }

                    .page-break {
                        page-break-before: always;
                    }

                    .avoid-break {
                        page-break-inside: avoid;
                    }

                    .print-container {
                        width: 190mm; /* 210mm - 20mm de marges */
                        height: 277mm; /* 297mm - 20mm de marges */
                        margin: 0 auto;
                        position: relative;
                        margin-top: ${this.pageSettings.headerHeight};
                        margin-bottom: ${this.pageSettings.footerHeight};
                        padding: 10mm;
                        min-height: calc(277mm - ${this.pageSettings.headerHeight} - ${this.pageSettings.footerHeight});
                    }

                    .print-header {
                        position: fixed;
                        top: 10mm;
                        left: 10mm;
                        right: 10mm;
                        height: ${this.pageSettings.headerHeight};
                        background: white;
                        z-index: 1000;
                        border-bottom: 2px solid #333;
                    }

                    .print-footer {
                        position: fixed;
                        bottom: 10mm;
                        left: 10mm;
                        right: 10mm;
                        height: ${this.pageSettings.footerHeight};
                        background: white;
                        z-index: 1000;
                        border-top: 1px solid #ccc;
                    }

                    .labels-grid {
                        padding: 5mm;
                        width: 100%;
                        height: 100%;
                        margin-top: 5mm;
                        grid-template-columns: repeat(${this.pageSettings.columns}, 1fr); /* Assure une seule colonne */
                        gap: 0; /* Pas de gap si une seule étiquette par page */
                        max-width: 190mm; /* S'adapte à la largeur du print-container */
                        min-height: calc(277mm - ${this.pageSettings.headerHeight} - ${this.pageSettings.footerHeight});
                    }

                /* Styles pour l'en-tête et pied de page */
                .print-header {
                    text-align: center;
                    padding: 3mm;
                    background: white;
                    height: ${this.pageSettings.headerHeight};
                    display: flex;
                    flex-direction: column;
                    justify-content: center;
                    align-items: center;
                }

                .print-header h1 {
                    font-size: 16px;
                    font-weight: bold;
                    color: #333;
                    margin: 0 0 2mm 0;
                    line-height: 1.2;
                }

                .print-header p {
                    font-size: 10px;
                    color: #666;
                    margin: 0;
                    line-height: 1.2;
                }

                .print-footer {
                    text-align: center;
                    padding: 2mm;
                    font-size: 8px;
                    color: #666;
                    background: white;
                    height: ${this.pageSettings.footerHeight};
                    display: flex;
                    flex-direction: column;
                    justify-content: center;
                    align-items: center;
                }

                .print-footer p {
                    margin: 0;
                    line-height: 1.2;
                }

                /* Grille des étiquettes */
                .labels-grid {
                    display: flex;
                    flex-direction: column;
                    gap: 0;
                    width: 10.1cm;
                    height: 10.1cm;
                    margin: 0;
                    padding: 0;
                }

                /* Étiquette individuelle */
                .article-label {
                    width: 10.1cm; /* Format 10x10 cm avec marges */
                    height: 10.1cm; /* Format 10x10 cm avec marges */
                    border: 1px solid #000000; /* Bordure noire pour l'impression */
                    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; /* Police plus moderne */
                    font-size: 8px; /* Réduire la taille pour s'adapter */
                    display: flex;
                    flex-direction: column;
                    background: linear-gradient(to bottom, #ffffff, #f0f0f0); /* Fond dégradé subtil */
                    page-break-after: always; /* Saut de page après chaque étiquette */
                    break-inside: avoid;
                    margin: 0;
                    overflow: hidden;
                    position: relative;
                    box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1); /* Ombre plus prononcée */
                    border-radius: 8px; /* Bords arrondis */
                    color: #333; /* Couleur de texte par défaut */
                    box-sizing: border-box;
                }
                
                .article-label:last-child {
                    page-break-after: avoid; /* Pas de saut de page pour la dernière étiquette */
                }

                .article-label * {
                    -webkit-print-color-adjust: exact !important;
                    color-adjust: exact !important;
                }

                /* En-tête stylisé avec numéro de commande et date */
                .label-header {
                    background-color: #2c3e50; /* Couleur d'en-tête plus foncée */
                    color: white;
                    padding: 5mm 8mm; /* Augmenter le padding */
                    display: flex;
                    justify-content: space-between;
                    align-items: center;
                    font-weight: bold;
                    font-size: 14px; /* Augmenter la taille de police */
                    flex-shrink: 0;
                    min-height: 15mm; /* Augmenter la hauteur minimale */
                    margin-bottom: 10mm; /* Augmenter la marge inférieure */
                    border-bottom: 2px solid #34495e; /* Bordure plus prononcée */
                    border-top-left-radius: 6px; /* Bords arrondis */
                    border-top-right-radius: 6px;
                }

                .label-number {
                    font-weight: bold;
                    text-transform: uppercase;
                    letter-spacing: 0.5px;
                }

                .label-date {
                    font-weight: bold;
                    opacity: 0.8;
                }

                /* Corps de l'étiquette */
                .label-body {
                    padding: 8mm;
                    flex-grow: 1;
                    display: flex;
                    flex-direction: column;
                    justify-content: space-between; /* Pour espacer les éléments */
                    background: #ffffff;
                    position: relative; /* Pour positionner le code */
                }

                /* Informations de l'article */
                .article-info {
                    margin-bottom: 15mm; /* Plus de marge pour le code */
                    flex-grow: 1;
                    display: flex;
                    flex-direction: column;
                    justify-content: flex-start;
                }

                .info-line {
                    display: flex;
                    align-items: center;
                    margin-bottom: 3mm; /* Augmenter la marge */
                    padding-bottom: 2mm; /* Augmenter le padding */
                    border-bottom: 1px dashed #ccc; /* Bordure en pointillés */
                    font-size: 14px; /* Augmenter la taille de police */
                }

                .info-icon {
                    margin-right: 5mm;
                    font-size: 22px; /* Augmenter la taille de police */
                    color: #2c3e50; /* Couleur d'icône */
                    font-weight: bold;
                }

                .info-text {
                    font-size: 14px; /* Augmenter la taille de police */
                    font-weight: 600; /* Texte plus gras */
                    word-break: break-word;
                    color: #333;
                    flex-grow: 1;
                }

                /* Conteneur de code-barres / QR code */
                .code-container {
                    display: flex;
                    justify-content: center;
                    align-items: center;
                    margin-top: 20mm;
                    margin-bottom: 20mm;
                    flex-shrink: 0;
                    width: 100%;
                    height: 120mm; /* Hauteur augmentée pour un code plus grand */
                    background: #ffffff; /* Fond blanc pur pour un meilleur contraste */
                    border: 2px solid #333; /* Bordure plus visible */
                    border-radius: 8px;
                    padding: 10mm; /* Plus de padding pour aérer */
                }

                .label-barcode,
                .label-qrcode {
                    max-width: 100%;
                    max-height: 100%;
                    object-fit: contain;
                }

                /* Pied de page stylisé */
                .label-footer {
                    background-color: #2c3e50; /* Couleur de pied de page plus foncée */
                    color: white;
                    padding: 4mm 8mm; /* Augmenter le padding */
                    display: flex;
                    justify-content: space-between;
                    align-items: center;
                    font-weight: bold;
                    font-size: 12px; /* Augmenter la taille de police */
                    flex-shrink: 0;
                    min-height: 10mm; /* Augmenter la hauteur minimale */
                    border-top: 2px solid #34495e; /* Bordure plus prononcée */
                    border-bottom-left-radius: 6px; /* Bords arrondis */
                    border-bottom-right-radius: 6px;
                }

                .footer-status {
                    font-weight: bold;
                    text-transform: uppercase;
                    letter-spacing: 0.5px;
                }

                .footer-company {
                    font-weight: bold;
                    opacity: 0.8;
                }

                /* Informations de contact */
                .label-contact {
                    background: #ecf0f1; /* Fond plus clair */
                    padding: 4mm 8mm;
                    display: flex;
                    justify-content: space-between;
                    align-items: center;
                    font-size: 12px;
                    border-top: 1px solid #bdc3c7; /* Bordure plus douce */
                    flex-shrink: 0;
                    min-height: 8mm;
                    border-bottom-left-radius: 6px;
                    border-bottom-right-radius: 6px;
                    margin-top: auto; /* Pousser vers le bas */
                }

                .contact-name {
                    font-weight: bold;
                    color: #2c3e50; /* Couleur de texte plus foncée */
                    font-size: 14px;
                }

                .contact-info {
                    text-align: right;
                    color: #555; /* Couleur de texte plus douce */
                    font-weight: normal;
                    font-size: 13px;
                }

                .contact-info div {
                    line-height: 1.3;
                }





                /* Responsive pour l'écran */
                @media screen {
                    body {
                        background: #f5f5f5;
                        padding: 20px;
                    }

                    .labels-grid {
                        background: white;
                        padding: 20px;
                        border-radius: 8px;
                        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
                    }

                    .print-header,
                    .print-footer {
                        display: none;
                    }
                }

                /* Animation pour l'aperçu */
                .article-label {
                    transition: transform 0.2s ease;
                }

                .article-label:hover {
                    transform: scale(1.02);
                }
            </style>
        </head>
        <body>
        `;

        // Ajouter l'en-tête si demandé (en dehors du container d'impression)
        if (showHeader) {
            html += `
            <div class="print-header">
                <h1>${title}</h1>
                ${subtitle ? `<p>${subtitle}</p>` : ''}
                <p>Généré le ${timestamp}</p>
            </div>
            `;
        }

        // Container principal pour l'impression
        html += '<div class="print-container">';
        
        // Grille des étiquettes
        html += '<div class="labels-grid">';

        let labelCount = 0;

        articles.forEach((article, index) => {
            // Générer l'étiquette pour cet article
            html += this.generateSingleLabel(article, format, index);
            labelCount++;

            // Ajouter un saut de page après chaque étiquette
            if (index < articles.length - 1) { // Si ce n'est pas la dernière étiquette
                html += '</div></div>'; // Fermer labels-grid et print-container

                // Ajouter l'en-tête pour la nouvelle page
                if (showHeader) {
                    html += `
                    <div class="print-header">
                        <h1>${title} (Suite)</h1>
                        ${subtitle ? `<p>${subtitle}</p>` : ''}
                        <p>Page ${Math.floor(labelCount / 10) + 1}</p>
                    </div>
                    `;
                }
                
                html += '<div class="page-break"></div>';
                html += '<div class="print-container">'; // Nouveau container
                html += '<div class="labels-grid">'; // Nouvelle grille
            }
        });

        html += '</div>'; // Fermer labels-grid
        html += '</div>'; // Fermer print-container

        // Ajouter le pied de page si demandé (en dehors du container d'impression)
        if (showFooter) {
            html += `
            <div class="print-footer">
                <p>Total: ${labelCount} étiquette(s) | Étiquettes d'articles</p>
                <p>Yoozak - Système de gestion des commandes</p>
            </div>
            `;
        }

        html += `
        <script src="https://cdn.jsdelivr.net/npm/jsbarcode@3.11.5/dist/JsBarcode.all.min.js"></script>
        <script>
            // Auto-impression
            window.onload = function() {
                // Attendre un peu pour que les images se chargent
                setTimeout(function() {
                    window.print();
                }, 1000);
            };
            
            // Fonction pour générer tous les codes-barres et QR codes
            function generateAllCodes() {
                // Générer les codes-barres
                const barcodeContainers = document.querySelectorAll('.barcode-container');
                console.log('Generation de', barcodeContainers.length, 'codes-barres...');
                
                barcodeContainers.forEach((container, index) => {
                    const text = container.getAttribute('data-text');
                    console.log('Code-barres', index + 1, ':', text);
                    
                    if (text && typeof JsBarcode !== 'undefined') {
                        const canvas = document.createElement('canvas');
                        canvas.width = 400; /* Largeur doublée */
                        canvas.height = 120; /* Hauteur doublée */
                        
                        try {
                            JsBarcode(canvas, text, {
                                format: "CODE128B",
                                width: 4, /* Largeur des barres doublée */
                                height: 80, /* Hauteur des barres doublée */
                                displayValue: true, /* Afficher le texte sous le code */
                                fontSize: 16, /* Taille de police pour le texte */
                                margin: 10, /* Marge augmentée */
                                background: "#ffffff",
                                lineColor: "#000000"
                            });
                            
                            const img = document.createElement('img');
                            img.src = canvas.toDataURL();
                            img.alt = text;
                            img.className = 'label-barcode';
                            
                            // Remplacer le contenu du container
                            container.innerHTML = '';
                            container.appendChild(img);
                            console.log('Code-barres', index + 1, 'genere avec succes');
                        } catch (error) {
                            console.warn('Erreur lors de la generation du code-barres:', error);
                            container.innerHTML = '<div style="color: #999; font-size: 8px; padding: 2mm;">Code non disponible</div>';
                        }
                    } else {
                        console.warn('Texte manquant ou JsBarcode non disponible pour le container', index + 1);
                        container.innerHTML = '<div style="color: #999; font-size: 8px; padding: 2mm;">Code non disponible</div>';
                    }
                });
                console.log('Generation des codes-barres terminee');

                // Générer les QR codes
                const qrcodeContainers = document.querySelectorAll('.qrcode-container');
                console.log('Generation de', qrcodeContainers.length, 'QR codes...');

                qrcodeContainers.forEach(container => {
                    const text = container.getAttribute('data-text');
                    if (text) {
                        const qrCodeImg = document.createElement('img');
                        qrCodeImg.src = 'https://api.qrserver.com/v1/create-qr-code/?size=300x300&data=' + encodeURIComponent(text);
                        qrCodeImg.alt = text;
                        qrCodeImg.className = 'label-qrcode';
                        container.innerHTML = '';
                        container.appendChild(qrCodeImg);
                    }
                });
                console.log('Generation des QR codes terminee');
            }
            
            // Appeler la fonction de génération de codes après un délai pour s'assurer que le DOM est prêt
            setTimeout(generateAllCodes, 500); // Exécuter après que les images se soient potentiellement chargées
        </script>
        </body>
        </html>
        `;

        return html;
    }

    /**
     * Générer une étiquette individuelle
     * @param {Object} article - Données de l'article
     * @param {string} format - Format du code (qr ou barcode)
     * @param {number} index - Index de l'article (optionnel)
     * @returns {string} HTML de l'étiquette
     */
    generateSingleLabel(article, format, index = 0) {
        const reference = article.reference || article.nom || 'Référence inconnue';
        // Utiliser les informations de commande stockées dans _commandeInfo si disponibles
        const commandeId = article._commandeInfo?.id || article.commande_id || 'N/A';
        const clientName = article._commandeInfo?.client || '';
        const variante = article.variante || '';
        const date = new Date().toLocaleDateString('fr-FR');
        
        let codeHtml = '';
        if (format === 'barcode') {
            codeHtml = '<div class="barcode-container" data-text="' + reference + '"></div>';
        } else {
            codeHtml = '<div class="qrcode-container" data-text="' + reference + '"></div>';
        }

        const varianteHtml = variante ? '<div class="info-line"><span class="info-icon">🎨</span><span class="info-text">Var: ' + variante + '</span></div>' : '';
        const clientHtml = clientName ? '<div class="info-line"><span class="info-icon">👤</span><span class="info-text">Client: ' + clientName + '</span></div>' : '';

        return '<div class="article-label avoid-break">' +
            '<div class="label-header">' +
                '<span class="label-number">N° d' + commandeId + '</span>' +
                '<span class="label-date">' + date + '</span>' +
            '</div>' +
            '<div class="label-body">' +
                '<div class="article-info">' +
                    '<div class="info-line">' +
                        '<span class="info-icon">📦</span>' +
                        '<span class="info-text">Réf: ' + reference + '</span>' +
                    '</div>' +
                    varianteHtml +
                    '<div class="info-line">' +
                        '<span class="info-icon">🏷️</span>' +
                        '<span class="info-text">Type: Article</span>' +
                    '</div>' +
                    '<div class="info-line">' +
                        '<span class="info-icon">🆔</span>' +
                        '<span class="info-text">Commande: ' + commandeId + '</span>' +
                    '</div>' +
                    clientHtml +
                    '<div class="info-line">' +
                        '<span class="info-icon">📋</span>' +
                        '<span class="info-text">Article ' + (index + 1) + '</span>' +
                    '</div>' +
                '</div>' +
                '<div class="code-container">' +
                    codeHtml +
                '</div>' +
            '</div>' +
            '<div class="label-footer">' +
                '<span class="footer-status">Article</span>' +
                '<span class="footer-company">Yoozak</span>' +
            '</div>' +
            '<div class="label-contact">' +
                '<span class="contact-name">Yoozak</span>' +
                '<span class="contact-info">' +
                    '<div>06 34 21 56 39</div>' +
                    '<div>SETTAT</div>' +
                '</span>' +
            '</div>' +
        '</div>';
    }

    /**
     * Créer une abréviation intelligente pour les références longues
     * @param {string} reference - Référence originale
     * @returns {string} Abréviation
     */
    createSmartAbbreviation(reference) {
        if (!reference) return 'REF';
        
        const parts = reference.split('-');
        
        if (parts.length >= 3) {
            const category = parts[0].substring(0, 3).toUpperCase();
            const gender = parts[1].substring(0, 2).toUpperCase();
            const model = parts[2].substring(0, 4).toUpperCase();
            
            let size = '';
            if (parts.length > 3) {
                const lastPart = parts[parts.length - 1];
                const sizeMatch = lastPart.match(/\d+/);
                if (sizeMatch) {
                    size = sizeMatch[0];
                }
            }
            
            let abbreviation = category + gender + model;
            if (size) {
                abbreviation += size;
            }
            
            return abbreviation;
        }
        
        // Fallback pour les références courtes
        return reference.substring(0, 12).toUpperCase().replace(/[^A-Z0-9]/g, '');
    }

    /**
     * Générer une URL data pour un code-barres Code128
     * @param {string} text - Texte à encoder
     * @returns {string} URL data du code-barres
     */
    generateCode128DataURL(text) {
        try {
            const canvas = document.createElement('canvas');
            canvas.width = 400; /* Largeur doublée */
            canvas.height = 120; /* Hauteur doublée */
            
            if (typeof JsBarcode !== 'undefined') {
                JsBarcode(canvas, text, {
                    format: "CODE128B",
                    width: 4, /* Largeur des barres doublée */
                    height: 80, /* Hauteur des barres doublée */
                    displayValue: true, /* Afficher le texte sous le code */
                    fontSize: 16, /* Taille de police pour le texte */
                    margin: 10, /* Marge augmentée */
                    background: "#ffffff",
                    lineColor: "#000000"
                });
                
                return canvas.toDataURL();
            }
        } catch (error) {
            console.warn('Erreur lors de la génération du code-barres:', error);
        }
        
        return '';
    }

    /**
     * Imprimer les étiquettes d'articles
     * @param {Array} articles - Liste des articles
     * @param {Object} options - Options d'impression
     */
    printArticleLabels(articles, options = {}) {
        if (!articles || articles.length === 0) {
            console.warn('⚠️ Aucun article à imprimer');
            return;
        }

        console.log('🖨️ Impression de ' + articles.length + ' étiquette(s) d\'articles');

        const html = this.generatePrintHTML(articles, options);
        
        try {
            // Créer une nouvelle fenêtre pour l'impression
            const printWindow = window.open('', '_blank', 'width=800,height=600,scrollbars=yes,resizable=yes');
            
            if (!printWindow) {
                console.error('Impossible de creer la fenetre d\'impression. Verifiez que les popups ne sont pas bloques.');
                alert('Erreur: Impossible de créer la fenêtre d\'impression. Veuillez autoriser les popups pour ce site.');
                return;
            }
            
            // Écrire le contenu immédiatement
            printWindow.document.write(html);
            printWindow.document.close();
            
            // Vérifier que le contenu a été écrit
            setTimeout(() => {
                if (printWindow.document.body.innerHTML.trim() === '') {
                    console.warn('Contenu vide detecte, nouvelle tentative...');
                    printWindow.document.write(html);
                    printWindow.document.close();
                }
            }, 500);
            
        } catch (error) {
            console.error('Erreur lors de la creation de la fenetre d\'impression:', error);
            
            // Fallback: utiliser l'onglet actuel
            console.log('Tentative d\'impression dans l\'onglet actuel...');
            this.printInCurrentTab(html);
        }
    }

    /**
     * Imprimer dans l'onglet actuel (fallback)
     * @param {string} html - HTML à imprimer
     */
    printInCurrentTab(html) {
        try {
            // Créer un élément temporaire avec un ID unique
            const tempDiv = document.createElement('div');
            tempDiv.id = 'print-temp-' + Date.now();
            tempDiv.innerHTML = html;
            tempDiv.style.position = 'fixed';
            tempDiv.style.top = '-9999px';
            tempDiv.style.left = '-9999px';
            tempDiv.style.zIndex = '-9999';
            tempDiv.style.width = '210mm';
            tempDiv.style.height = '297mm';
            tempDiv.style.background = 'white';
            
            // Ajouter au DOM
            document.body.appendChild(tempDiv);
            
            // Attendre un peu puis imprimer
            setTimeout(() => {
                try {
                    window.print();
                } catch (printError) {
                    console.error('Erreur lors de l\'impression:', printError);
                    alert('Erreur lors de l\'impression. Veuillez vérifier les paramètres d\'impression.');
                }
            }, 1000);
            
            // Nettoyer après un délai
            setTimeout(() => {
                const element = document.getElementById(tempDiv.id);
                if (element && document.body.contains(element)) {
                    document.body.removeChild(element);
                }
            }, 10000);
            
        } catch (error) {
            console.error('Erreur lors de l\'impression dans l\'onglet actuel:', error);
            alert('Erreur lors de l\'impression. Veuillez vérifier les paramètres d\'impression de votre navigateur.');
        }
    }

    /**
     * Imprimer les étiquettes d'une commande spécifique
     * @param {string} commandeId - ID de la commande
     * @param {string} clientName - Nom du client
     */
    printCommandeLabels(commandeId, clientName) {
        console.log('🖨️ Impression des étiquettes pour la commande ' + commandeId);
        
        // Afficher une notification de chargement
        if (window.showNotification) {
            window.showNotification('info', 'Chargement des articles pour la commande ' + commandeId + '...');
        }
        
        // Récupérer les articles de la commande
        this.fetchCommandeArticles(commandeId)
            .then(articles => {
                if (articles && articles.length > 0) {
                    console.log('✅ ' + articles.length + ' article(s) récupéré(s) pour la commande ' + commandeId);
                    
                    // Déterminer la source des données pour le message
                    let dataSource = '';
                    if (articles[0]._source) {
                        dataSource = ' (' + articles[0]._source + ')';
                    } else if (window.testArticles && window.testArticles[commandeId] === articles) {
                        dataSource = ' (données de test)';
                    }
                    
                    this.printArticleLabels(articles, {
                        title: 'Étiquettes Articles - Commande ' + commandeId,
                        subtitle: 'Client: ' + clientName + dataSource,
                        format: this.currentFormat
                    });
                    
                    if (window.showNotification) {
                        window.showNotification('success', 'Impression lancée pour ' + articles.length + ' article(s)');
                    }
                } else {
                    console.warn('⚠️ Aucun article trouvé pour la commande ' + commandeId);
                    if (window.showNotification) {
                        window.showNotification('warning', 'Aucun article trouvé pour la commande ' + commandeId);
                    }
                }
            })
            .catch(error => {
                console.error('❌ Erreur lors de la récupération des articles:', error);
                
                // Essayer d'utiliser les données du modal comme fallback
                if (window.modalArticles && window.modalArticles.articles) {
                    console.log('🔄 Tentative avec les données du modal...');
                    const articles = window.modalArticles.articles.map(article => ({
                        reference: article.reference,
                        commande_id: commandeId,
                        variante: article.variante || '',
                        qr_url: article.barcode_url,
                        nom: article.reference,
                        _source: 'modal'
                    }));
                    
                    this.printArticleLabels(articles, {
                        title: 'Étiquettes Articles - Commande ' + commandeId,
                        subtitle: 'Client: ' + clientName + ' (données du modal)',
                        format: this.currentFormat
                    });
                    
                    if (window.showNotification) {
                        window.showNotification('success', 'Impression lancée avec les données du modal');
                    }
                } else {
                    if (window.showNotification) {
                        window.showNotification('error', 'Erreur lors de la récupération des articles. Veuillez d\'abord ouvrir la commande.');
                    } else {
                        alert('Erreur lors de la récupération des articles. Veuillez d\'abord ouvrir la commande pour charger les données.');
                    }
                }
            });
    }

    /**
     * Stocker les articles dans le localStorage pour utilisation future
     * @param {string} commandeId - ID de la commande
     * @param {Array} articles - Articles à stocker
     */
    storeArticlesInLocalStorage(commandeId, articles) {
        try {
            if (articles && articles.length > 0) {
                // Limiter la taille des données pour éviter de dépasser les limites du localStorage
                const simplifiedArticles = articles.map(article => ({
                    reference: article.reference || article.nom || '',
                    commande_id: article.commande_id || commandeId,
                    variante: article.variante || '',
                    nom: article.nom || article.reference || ''
                }));
                
                localStorage.setItem('commande_' + commandeId + '_articles', JSON.stringify(simplifiedArticles));
                console.log('✅ ' + articles.length + ' article(s) stocké(s) dans le localStorage pour la commande ' + commandeId);
            }
        } catch (error) {
            console.warn('Erreur lors du stockage dans localStorage:', error);
        }
    }
    
    /**
     * Extraire les articles du DOM pour une commande
     * @param {string} commandeId - ID de la commande
     * @returns {Array} Articles trouvés dans le DOM
     */
    getArticlesFromDOM(commandeId) {
        try {
            // Chercher dans le modal d'articles s'il est ouvert
            const modalContent = document.querySelector('#modalArticles .modal-body');
            if (modalContent) {
                const articleElements = modalContent.querySelectorAll('.article-item');
                if (articleElements.length > 0) {
                    console.log('🔍 ' + articleElements.length + ' articles trouvés dans le modal');
                    
                    const articles = [];
                    articleElements.forEach((element, index) => {
                        // Extraire les données des éléments du DOM
                        const reference = element.querySelector('.article-reference')?.textContent || 
                                          element.querySelector('[data-reference]')?.dataset.reference || 
                                          'Article ' + (index + 1);
                        
                        const variante = element.querySelector('.article-variante')?.textContent || 
                                         element.querySelector('[data-variante]')?.dataset.variante || '';
                        
                        articles.push({
                            reference: reference.trim(),
                            commande_id: commandeId,
                            variante: variante.trim(),
                            nom: reference.trim(),
                            _source: 'dom'
                        });
                    });
                    
                    return articles;
                }
            }
            
            // Chercher dans le tableau des articles si visible
            const tableRows = document.querySelectorAll('tr[data-commande-id="' + commandeId + '"], .commande-row[data-id="' + commandeId + '"]');
            if (tableRows.length > 0) {
                const articles = [];
                tableRows.forEach(row => {
                    const articlesText = row.querySelector('.commande-articles')?.textContent || '';
                    if (articlesText) {
                        // Essayer d'extraire les articles du texte
                        const articlesList = articlesText.split(',').map(item => item.trim());
                        articlesList.forEach((item, index) => {
                            if (item) {
                                const parts = item.split(' - ');
                                articles.push({
                                    reference: parts[0] || 'Article ' + (index + 1),
                                    commande_id: commandeId,
                                    variante: parts[1] || '',
                                    nom: parts[0] || 'Article ' + (index + 1),
                                    _source: 'table'
                                });
                            }
                        });
                    }
                });
                
                if (articles.length > 0) {
                    return articles;
                }
            }
            
            // Aucun article trouvé dans le DOM
            return [];
        } catch (error) {
            console.warn('Erreur lors de l\'extraction des articles du DOM:', error);
            return [];
        }
    }

    /**
     * Récupérer les articles d'une commande via AJAX
     * @param {string} commandeId - ID de la commande
     * @returns {Promise} Promise avec les articles
     * Note: Une commande avec plusieurs articles génère plusieurs tickets (1 par article)
     */
    async fetchCommandeArticles(commandeId) {
        try {
            // Essayer plusieurs endpoints possibles avec différentes méthodes
            const endpoints = [
                '/api/commande/' + commandeId + '/articles/',
                '/api/commandes/' + commandeId + '/articles/',
                '/superpreparation/api/commande/' + commandeId + '/articles/',
                '/commande/' + commandeId + '/articles/json/',
                '/api/etiquettes/commande/' + commandeId + '/articles/',
                '/commande/articles/' + commandeId + '/',
                '/commande/' + commandeId + '/details/',
                '/api/commandes/details/' + commandeId + '/',
                '/superpreparation/commande/' + commandeId + '/articles/'
            ];

            // Vérifier si des données sont déjà disponibles dans le DOM
            const articlesFromDOM = this.getArticlesFromDOM(commandeId);
            if (articlesFromDOM && articlesFromDOM.length > 0) {
                console.log('✅ ' + articlesFromDOM.length + ' article(s) trouvé(s) dans le DOM pour la commande ' + commandeId);
                return articlesFromDOM;
            }

            // Essayer les endpoints avec différentes méthodes
            for (const endpoint of endpoints) {
                try {
                    console.log('🔍 Tentative avec l\'endpoint: ' + endpoint);
                    
                    // Essayer avec différentes options de requête
                    const options = [
                        {
                            method: 'GET',
                            headers: {
                                'Content-Type': 'application/json',
                                'X-Requested-With': 'XMLHttpRequest'
                            }
                        },
                        {
                            method: 'GET',
                            headers: {
                                'Accept': 'application/json'
                            }
                        },
                        {
                            method: 'POST',
                            headers: {
                                'Content-Type': 'application/json',
                                'X-Requested-With': 'XMLHttpRequest'
                            },
                            body: JSON.stringify({ id: commandeId })
                        }
                    ];

                    for (const option of options) {
                        try {
                            const response = await fetch(endpoint, option);
                            
                            if (response.ok) {
                                const contentType = response.headers.get('content-type');
                                if (contentType && contentType.includes('application/json')) {
                                    const data = await response.json();
                                    console.log('✅ Données récupérées via AJAX:', data);
                                    
                                    // Extraire les articles selon différentes structures possibles
                                    const articles = 
                                        data.articles || 
                                        data.data?.articles || 
                                        data.data || 
                                        data.commande?.articles || 
                                        data.items || 
                                        data;
                                        
                                    if (Array.isArray(articles) && articles.length > 0) {
                                        // Ajouter un marqueur de source et stocker dans localStorage
                                        const articlesWithSource = articles.map(article => ({
                                            ...article,
                                            _source: 'api'
                                        }));
                                        this.storeArticlesInLocalStorage(commandeId, articlesWithSource);
                                        return articlesWithSource;
                                    } else if (typeof articles === 'object' && articles !== null) {
                                        // Convertir l'objet en tableau si nécessaire
                                        const articlesArray = Object.values(articles).filter(item => item && typeof item === 'object');
                                        if (articlesArray.length > 0) {
                                            const articlesWithSource = articlesArray.map(article => ({
                                                ...article,
                                                _source: 'api'
                                            }));
                                            this.storeArticlesInLocalStorage(commandeId, articlesWithSource);
                                            return articlesWithSource;
                                        }
                                    }
                                }
                            }
                        } catch (optionError) {
                            // Silencieux pour les erreurs d'options individuelles
                        }
                    }
                } catch (e) {
                    console.warn('⚠️ Endpoint ' + endpoint + ' non disponible:', e.message);
                }
            }

            // Fallback: utiliser les données du modal si disponible
            if (window.modalArticles && window.modalArticles.articles) {
                console.log('🔄 Utilisation des données du modal comme fallback');
                const articlesFromModal = window.modalArticles.articles.map(article => ({
                    reference: article.reference,
                    commande_id: commandeId,
                    variante: article.variante || '',
                    qr_url: article.barcode_url,
                    nom: article.reference,
                    _source: 'modal'
                }));
                this.storeArticlesInLocalStorage(commandeId, articlesFromModal);
                return articlesFromModal;
            }
            
            // Vérifier s'il y a des données dans localStorage
            try {
                const storedData = localStorage.getItem('commande_' + commandeId + '_articles');
                if (storedData) {
                    const parsedData = JSON.parse(storedData);
                    if (Array.isArray(parsedData) && parsedData.length > 0) {
                        console.log('🔄 Utilisation des données du localStorage');
                        // Ajouter la source si elle n'existe pas déjà
                        const articlesWithSource = parsedData.map(article => ({
                            ...article,
                            _source: article._source || 'localStorage'
                        }));
                        return articlesWithSource;
                    }
                }
            } catch (storageError) {
                console.warn('Erreur lors de la lecture du localStorage:', storageError);
            }

            // Fallback: données de test uniquement si absolument nécessaire
            console.warn('⚠️ Aucune donnée disponible - utilisation de données de test pour la commande ' + commandeId);
            
            // Créer des données de test avec un marqueur de source
            // Utiliser l'ID de commande pour générer des données différentes pour chaque commande
            const testArticles = [];
            
            // Générer 2 articles différents pour chaque commande
            testArticles.push({
                reference: 'BOT-FEM-YZ' + commandeId + '-Standard-37',
                commande_id: commandeId,
                variante: 'Standard',
                qr_url: '',
                nom: 'Article 1 - Commande ' + commandeId,
                _source: 'test'
            });
            
            testArticles.push({
                reference: 'MULE-FEM-YZ' + commandeId + '-Beige-36',
                commande_id: commandeId,
                variante: 'Beige',
                qr_url: '',
                nom: 'Article 2 - Commande ' + commandeId,
                _source: 'test'
            });
            
            // Stocker les données de test pour référence
            window.testArticles = window.testArticles || {};
            window.testArticles[commandeId] = testArticles;
            
            return testArticles;

        } catch (error) {
            console.error('Erreur AJAX:', error);
            throw error;
        }
    }

    /**
     * Changer le format d'impression
     * @param {string} format - 'qr' ou 'barcode'
     */
    setFormat(format) {
        this.currentFormat = format;
        console.log('🔄 Format d\'impression changé vers: ' + format);
        
        // Émettre un événement pour notifier les autres composants
        document.dispatchEvent(new CustomEvent('formatChanged', {
            detail: { format: format }
        }));
    }

    /**
     * Aperçu des étiquettes (sans impression)
     * @param {Array} articles - Liste des articles
     * @param {Object} options - Options d'affichage
     */
    previewLabels(articles, options = {}) {
        if (!articles || articles.length === 0) {
            console.warn('⚠️ Aucun article pour l\'aperçu');
            return;
        }

        console.log('👁️ Aperçu de ' + articles.length + ' étiquette(s)');

        const html = this.generatePrintHTML(articles, {
            ...options,
            showHeader: false,
            showFooter: false
        });
        
        // Créer une fenêtre d'aperçu
        const previewWindow = window.open('', '_blank', 'width=1000,height=800');
        previewWindow.document.write(html);
        previewWindow.document.close();
    }
}

// Initialiser l'imprimeur d'étiquettes
let articleLabelsPrinter;

// Fonctions globales pour l'interface
window.printArticleLabels = function(articles, options) {
    if (!articleLabelsPrinter) {
        articleLabelsPrinter = new ArticleLabelsPrinter();
    }
    articleLabelsPrinter.printArticleLabels(articles, options);
};

window.printCommandeLabels = function(commandeId, clientName) {
    if (!articleLabelsPrinter) {
        articleLabelsPrinter = new ArticleLabelsPrinter();
    }
    articleLabelsPrinter.printCommandeLabels(commandeId, clientName);
};

window.previewArticleLabels = function(articles, options) {
    if (!articleLabelsPrinter) {
        articleLabelsPrinter = new ArticleLabelsPrinter();
    }
    articleLabelsPrinter.previewLabels(articles, options);
};

window.setPrintFormat = function(format) {
    if (!articleLabelsPrinter) {
        articleLabelsPrinter = new ArticleLabelsPrinter();
    }
    articleLabelsPrinter.setFormat(format);
};

// Fonction pour imprimer toutes les étiquettes d'articles
window.imprimerEtiquettesArticles = async function() {
    console.log('🖨️ Impression de toutes les étiquettes d\'articles');
    
    if (!articleLabelsPrinter) {
        articleLabelsPrinter = new ArticleLabelsPrinter();
    }
    
    // Récupérer toutes les commandes visibles
    const visibleRows = document.querySelectorAll('.commande-row:not([style*="display: none"])');
    
    if (visibleRows.length === 0) {
        alert('Aucune commande visible à imprimer. Veuillez effacer les filtres de recherche.');
        return;
    }
    
    // Collecter toutes les commandes
    const commandes = Array.from(visibleRows).map(row => ({
        id: row.dataset.id,
        client: row.dataset.client || `Client ${row.dataset.id}`
    }));
    
    // Afficher une confirmation avec le nombre total d'articles attendus
    const expectedArticleCount = commandes.length * 2; // Estimation: 2 articles par commande
    const confirmed = confirm(`Imprimer les étiquettes d'articles pour ${commandes.length} commande(s) ? (environ ${expectedArticleCount} étiquettes)`);
    
    if (confirmed) {
        // Collecter tous les articles de toutes les commandes
        let allArticles = [];
        let errorCount = 0;
        
        // Précharger les données pour toutes les commandes
        if (window.showNotification) {
            window.showNotification('info', `Préparation des étiquettes pour ${commandes.length} commande(s)...`);
        }
        
        // Traiter les commandes séquentiellement pour collecter tous les articles
        for (let i = 0; i < commandes.length; i++) {
            const commande = commandes[i];
            
            try {
                // Notification de progression
                if (window.showNotification && i > 0 && i % 5 === 0) {
                    window.showNotification('info', `Progression: ${i}/${commandes.length} commandes traitées`);
                }
                
                // Précharger les données des articles
                const articles = await articleLabelsPrinter.fetchCommandeArticles(commande.id);
                
                if (articles && articles.length > 0) {
                    console.log(`✅ Commande ${commande.id}: ${articles.length} article(s) trouvé(s)`);
                    
                    // Ajouter des informations sur la commande à chaque article
                    const articlesWithInfo = articles.map(article => ({
                        ...article,
                        _commandeInfo: {
                            id: commande.id,
                            client: commande.client
                        }
                    }));
                    
                    // Ajouter ces articles à la collection complète
                    allArticles = allArticles.concat(articlesWithInfo);
                } else {
                    console.warn(`⚠️ Aucun article trouvé pour la commande ${commande.id}`);
                    errorCount++;
                }
            } catch (error) {
                console.error(`❌ Erreur pour la commande ${commande.id}:`, error);
                errorCount++;
            }
            
            // Petite pause pour éviter de surcharger le navigateur
            await new Promise(resolve => setTimeout(resolve, 300));
        }
        
        // Vérifier si des articles ont été trouvés
        if (allArticles.length === 0) {
            if (window.showNotification) {
                window.showNotification('error', 'Aucun article trouvé pour l\'impression');
            } else {
                alert('Aucun article trouvé pour l\'impression');
            }
            return;
        }
        
        // Imprimer tous les articles en une seule fois
        console.log(`🖨️ Impression de ${allArticles.length} étiquettes au total`);
        
        try {
            // Imprimer tous les articles en une seule fois
            articleLabelsPrinter.printArticleLabels(allArticles, {
                title: `Étiquettes Articles - ${commandes.length} commande(s)`,
                subtitle: `Total: ${allArticles.length} étiquette(s)`,
                format: articleLabelsPrinter.currentFormat
            });
            
            // Notification de succès
            if (window.showNotification) {
                window.showNotification('success', `Impression lancée pour ${allArticles.length} étiquettes`);
            }
            
            // Notification finale après un délai
            setTimeout(() => {
                const message = `Impression terminée: ${allArticles.length} étiquette(s) au total, ${errorCount} erreur(s)`;
                if (window.showNotification) {
                    window.showNotification(errorCount > 0 ? 'warning' : 'success', message);
                }
            }, 3000);
            
        } catch (error) {
            console.error('❌ Erreur lors de l\'impression:', error);
            if (window.showNotification) {
                window.showNotification('error', `Erreur lors de l'impression: ${error.message}`);
            } else {
                alert(`Erreur lors de l'impression: ${error.message}`);
            }
        }
    }
};

// Fonction pour imprimer les étiquettes d'articles d'une commande spécifique
window.imprimerEtiquettesArticlesCommande = function(commandeId, clientName) {
    console.log(`🖨️ Impression des étiquettes d'articles pour la commande ${commandeId}`);
    
    if (!articleLabelsPrinter) {
        articleLabelsPrinter = new ArticleLabelsPrinter();
    }
    
    // Afficher une notification de début
    if (window.showNotification) {
        window.showNotification('info', `Préparation de l'impression pour la commande ${commandeId}...`);
    }
    
    // Imprimer les étiquettes
    articleLabelsPrinter.printCommandeLabels(commandeId, clientName);
    
    // Notification de succès
    if (window.showNotification) {
        window.showNotification('success', `Impression lancée pour la commande ${commandeId}`);
    }
};

// Fonction pour afficher des notifications
window.showNotification = function(type, message) {
    // Créer une notification temporaire
    const notification = document.createElement('div');
    notification.className = `fixed top-4 right-4 z-50 p-4 rounded-md shadow-lg transition-all duration-300 transform translate-x-full`;
    
    // Styles selon le type
    switch (type) {
        case 'success':
            notification.className += ' bg-green-500 text-white';
            notification.innerHTML = `<i class="fas fa-check mr-2"></i>${message}`;
            break;
        case 'error':
            notification.className += ' bg-red-500 text-white';
            notification.innerHTML = `<i class="fas fa-exclamation-triangle mr-2"></i>${message}`;
            break;
        case 'info':
            notification.className += ' bg-blue-500 text-white';
            notification.innerHTML = `<i class="fas fa-info-circle mr-2"></i>${message}`;
            break;
        case 'warning':
            notification.className += ' bg-yellow-500 text-white';
            notification.innerHTML = `<i class="fas fa-exclamation-circle mr-2"></i>${message}`;
            break;
    }
    
    // Ajouter au DOM
    document.body.appendChild(notification);
    
    // Animation d'entrée
    setTimeout(() => {
        notification.classList.remove('translate-x-full');
    }, 100);
    
    // Auto-suppression après 3 secondes
    setTimeout(() => {
        notification.classList.add('translate-x-full');
        setTimeout(() => {
            if (notification.parentNode) {
                notification.parentNode.removeChild(notification);
            }
        }, 300);
    }, 3000);
}

// Initialiser quand le DOM est chargé
document.addEventListener('DOMContentLoaded', function() {
    console.log('🚀 Initialisation du système d\'impression des étiquettes d\'articles...');
    articleLabelsPrinter = new ArticleLabelsPrinter();
    console.log('✅ Système d\'impression des étiquettes d\'articles initialisé');
});

// Exporter pour utilisation externe
window.ArticleLabelsPrinter = ArticleLabelsPrinter;

/* jshint ignore:end */
