/**
 * Gestion des modales d'impression pour les commandes confirmées
 * Fichier: impression-modals.js
 */

class ImpressionModals {
    constructor() {
        this.currentCommandeId = null;
        this.currentCommandeIdYz = null;
        this.currentClientNom = null;
        this.init();
    }

    init() {
        document.addEventListener('DOMContentLoaded', () => {
            this.setupModalListeners();
        });
    }

    setupModalListeners() {
        // Modale de choix d'impression
        const impressionChoiceModal = document.getElementById('impressionChoiceModal');
        if (impressionChoiceModal) {
            impressionChoiceModal.addEventListener('click', (e) => {
                if (e.target === impressionChoiceModal) {
                    this.hideImpressionChoiceModal();
                }
            });
        }

        // Modale de choix de format - SUPPRIMÉE car plus nécessaire

        // Fermer avec la touche Escape
        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape') {
                this.hideImpressionChoiceModal();
                // Plus de modale de choix de format à fermer
            }
        });
    }

    /**
     * Afficher la modale de choix d'impression
     * @param {number} commandeId - ID de la commande
     * @param {string} commandeIdYz - ID YZ de la commande
     * @param {string} clientNom - Nom du client
     */
    showImpressionModal(commandeId, commandeIdYz, clientNom) {
        console.log('🔍 showImpressionModal appelée avec:', { commandeId, commandeIdYz, clientNom });
        
        this.currentCommandeId = commandeId;
        this.currentCommandeIdYz = commandeIdYz;
        this.currentClientNom = clientNom;
        
        console.log('📝 Variables mises à jour:', {
            currentCommandeId: this.currentCommandeId,
            currentCommandeIdYz: this.currentCommandeIdYz,
            currentClientNom: this.currentClientNom
        });
        
        // Mettre à jour les informations dans la modale
        this.updateImpressionModalInfo();
        
        // Afficher la modale
        const modal = document.getElementById('impressionChoiceModal');
        if (modal) {
            modal.classList.remove('hidden');
            // Animation d'entrée
            modal.querySelector('.animate-fade-in-down').classList.add('animate-fade-in-down');
        }
    }

    /**
     * Fermer la modale de choix d'impression
     */
    hideImpressionChoiceModal() {
        const modal = document.getElementById('impressionChoiceModal');
        if (modal) {
            modal.classList.add('hidden');
        }
    }

    /**
     * Mettre à jour les informations de la commande dans la modale
     */
    updateImpressionModalInfo() {
        if (this.currentCommandeIdYz) {
            const commandeIdElement = document.getElementById('commandeIdImpression');
            if (commandeIdElement) {
                commandeIdElement.textContent = this.currentCommandeIdYz;
            }
        }
        if (this.currentClientNom) {
            const clientNomElement = document.getElementById('clientNomImpression');
            if (clientNomElement) {
                clientNomElement.textContent = this.currentClientNom;
            }
        }
    }


    /**
     * Afficher les étiquettes des articles dans une modale
     */
    async imprimerEtiquettesArticles() {
        this.hideImpressionChoiceModal();
        if (this.currentCommandeIdYz) {
            // Charger directement les QR codes (plus de choix de format)
            this.loadEtiquettesWithFormat('qr');
        }
    }

    /**
     * Imprimer le ticket de commande directement
     */
    imprimerTicketCommande() {
        this.hideImpressionChoiceModal();
        
        // Vérifier que l'ID de la commande est défini
        if (!this.currentCommandeIdYz) {
            console.error('❌ currentCommandeIdYz n\'est pas défini:', this.currentCommandeIdYz);
            this.showNotification('Erreur: Aucune commande sélectionnée', 'error');
            return;
        }
        
        console.log('🔍 Impression directe du ticket pour la commande:', this.currentCommandeIdYz);
        
        // Afficher une notification de chargement
        this.showNotification('Chargement du ticket de commande...', 'info');
        
        // Récupérer les données du ticket
        const url = `/Superpreparation/api/ticket-commande/?ids=${this.currentCommandeIdYz}`;
        console.log('🌐 URL de la requête:', url);
        
        fetch(url)
            .then(response => {
                console.log('📡 Réponse reçue:', response.status, response.statusText);
                if (!response.ok) {
                    throw new Error(`HTTP ${response.status}: ${response.statusText}`);
                }
                return response.json();
            })
            .then(data => {
                console.log('📦 Données reçues:', data);
                
                if (data.success && data.html) {
                    // Lancer directement l'impression
                    this.printTicketsDirect([data.html]);
                    this.showNotification('Impression lancée !', 'success');
                } else {
                    const errorMsg = data.error || 'Aucune donnée de commande disponible';
                    console.error('❌ Erreur dans les données:', errorMsg);
                    this.showNotification(`Erreur: ${errorMsg}`, 'error');
                }
            })
            .catch(error => {
                console.error('❌ Erreur lors du chargement du ticket:', error);
                this.showNotification(`Erreur lors du chargement du ticket: ${error.message}`, 'error');
            });
    }

    /**
     * Imprimer les tickets de plusieurs commandes
     */
    imprimerTicketsMultiples(commandeIds) {
        this.hideImpressionChoiceModal();
        
        // Afficher une notification de chargement
        this.showNotification('Chargement des tickets de commande...', 'info');
        
        // Récupérer les données des tickets
        fetch(`/Superpreparation/api/ticket-commande/?ids=${commandeIds.join(',')}`)
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    this.showTicketModal(data);
                } else {
                    this.showNotification(`Erreur: ${data.error}`, 'error');
                }
            })
            .catch(error => {
                console.error('Erreur lors du chargement des tickets:', error);
                this.showNotification('Erreur lors du chargement des tickets', 'error');
            });
    }

    /**
     * Imprimer le ticket de commande multiple
     */
    imprimerTicketCommandeMultiple() {
        this.hideImpressionChoiceModal();
        
        // Afficher une notification de chargement
        this.showNotification('Chargement des tickets de commande multiples...', 'info');
        
        // Récupérer les données des tickets multiples (toutes les commandes confirmées)
        fetch('/Superpreparation/api/ticket-commande-multiple/')
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    this.showTicketMultipleModal(data);
                } else {
                    this.showNotification(`Erreur: ${data.error}`, 'error');
                }
            })
            .catch(error => {
                console.error('Erreur lors du chargement des tickets multiples:', error);
                this.showNotification('Erreur lors du chargement des tickets multiples', 'error');
            });
    }

    /**
     * Afficher la modale de choix de format pour les étiquettes - SUPPRIMÉE
     * Utilise maintenant directement les QR codes
     */
    // showFormatChoiceModal() - SUPPRIMÉE

    /**
     * Créer la modale de choix de format - SUPPRIMÉE car plus nécessaire
     * Utilise maintenant directement les QR codes
     */
    // createFormatChoiceModal() - SUPPRIMÉE

    /**
     * Fermer la modale de choix de format - SUPPRIMÉE
     */
    // hideFormatChoiceModal() - SUPPRIMÉE

    /**
     * Charger les étiquettes avec un format spécifique (maintenant uniquement QR codes)
     */
    async loadEtiquettesWithFormat(format) {
        // Utilise maintenant uniquement les QR codes, le paramètre format est ignoré
        
        if (this.currentCommandeIdYz) {
            try {
                // Afficher un indicateur de chargement
                this.showNotification('Chargement des QR codes des articles...', 'info');
                
                console.log(`🔍 Chargement des QR codes pour la commande: ${this.currentCommandeIdYz}`);
                
                // Charger le contenu via AJAX avec le format QR (toujours)
                const response = await fetch(`/Superpreparation/api/etiquettes-articles/?ids=${this.currentCommandeIdYz}&format=qr`);
                console.log(`📡 Réponse du serveur: ${response.status} ${response.statusText}`);
                
                if (response.ok) {
                    const data = await response.json();
                    console.log('✅ Données reçues:', data);
                    this.showEtiquettesArticlesModal(data);
                } else {
                    const errorText = await response.text();
                    console.error('❌ Erreur serveur:', errorText);
                    throw new Error(`Erreur serveur: ${response.status} - ${errorText}`);
                }
            } catch (error) {
                console.error('Erreur:', error);
                this.showNotification(`Erreur lors du chargement des QR codes: ${error.message}`, 'error');
            }
        }
    }

    /**
     * Imprimer les tickets directement (sans modale)
     */
    printTicketsDirect(ticketsHtml) {
        const printWindow = window.open('', '_blank');
        printWindow.document.write(`
            <html>
                <head>
                    <title>Tickets de Commande</title>
                    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css">
                    <style>
                        @page { size: B5; margin: 5mm; }
                        body { 
                            margin: 0; 
                            padding: 0; 
                            font-family: Arial, sans-serif; 
                            -webkit-print-color-adjust: exact !important;
                            color-adjust: exact !important;
                            print-color-adjust: exact !important;
                        }
                        * {
                            -webkit-print-color-adjust: exact !important;
                            color-adjust: exact !important;
                            print-color-adjust: exact !important;
                        }
                        .ticket-commande-container {
                            display: grid;
                            grid-template-columns: repeat(2, 1fr);
                            gap: 2mm;
                            width: 100%;
                            max-width: 180mm;
                            margin: 0 auto;
                            padding: 2mm;
                        }
                        .ticket-commande {
                            width: 75mm;
                            height: 74mm;
                            border: 0.5px solid black;
                            font-family: Arial, sans-serif;
                            font-size: 7px;
                            background: white;
                            page-break-inside: avoid;
                            margin: 0;
                            overflow: hidden;
                        }
                        .ticket-header {
                            background-color: #000000 !important;
                            color: #ffffff !important;
                            padding: 1mm;
                            display: flex;
                            justify-content: space-between;
                            align-items: center;
                            font-weight: bold;
                            font-size: 8px;
                            height: 5mm;
                            -webkit-print-color-adjust: exact !important;
                            color-adjust: exact !important;
                            print-color-adjust: exact !important;
                            background: #000000 !important;
                            color: #ffffff !important;
                        }
                        .ticket-body {
                            padding: 2.5mm;
                        }
                        
                        .barcode-image {
                            max-width: 15mm !important;
                            max-height: 4mm !important;
                            object-fit: contain !important;
                            width: 15mm !important;
                            height: 4mm !important;
                        }
                        
                        .barcode-left .barcode-container {
                            background: white !important;
                            border: 0.3px solid #333333 !important;
                            padding: 0.3mm !important;
                            width: 15mm !important;
                            height: 4mm !important;
                        }
                        .info-line {
                            display: flex;
                            align-items: center;
                            margin-bottom: 1mm;
                            padding-bottom: 1mm;
                            border-bottom: 1px dashed #ccc;
                        }
                        .info-icon {
                            margin-right: 2mm;
                            font-size: 10px;
                            width: 12px;
                            text-align: center;
                        }
                        .info-text {
                            font-size: 7px;
                            flex: 1;
                        }
                        .ticket-footer {
                            background-color: #000000 !important;
                            color: #ffffff !important;
                            padding: 2mm;
                            display: flex;
                            justify-content: space-between;
                            align-items: center;
                            font-weight: bold;
                            font-size: 8px;
                            -webkit-print-color-adjust: exact !important;
                            color-adjust: exact !important;
                            print-color-adjust: exact !important;
                            background: #000000 !important;
                            color: #ffffff !important;
                        }
                        .ticket-contact {
                            background: #f8f8f8 !important;
                            padding: 2mm;
                            display: flex;
                            justify-content: space-between;
                            align-items: center;
                            font-size: 6px;
                            border-top: 1px solid #000000 !important;
                            -webkit-print-color-adjust: exact !important;
                            color-adjust: exact !important;
                            print-color-adjust: exact !important;
                            background-color: #f8f8f8 !important;
                            color: #000000 !important;
                        }
                        .contact-name {
                            font-weight: bold;
                            font-size: 8px;
                            color: #000000 !important;
                            -webkit-print-color-adjust: exact !important;
                            color-adjust: exact !important;
                            print-color-adjust: exact !important;
                        }
                        .contact-info {
                            text-align: right;
                            font-weight: bold;
                            font-size: 6px;
                            color: #000000 !important;
                            -webkit-print-color-adjust: exact !important;
                            color-adjust: exact !important;
                            print-color-adjust: exact !important;
                        }
                        .ticket-checkbox {
                            display: none;
                        }
                        
                        /* Assurer l'affichage des icônes Font Awesome lors de l'impression */
                        .fas, .far, .fab {
                            font-family: "Font Awesome 6 Free" !important;
                            font-weight: 900 !important;
                            -webkit-print-color-adjust: exact !important;
                            color-adjust: exact !important;
                            print-color-adjust: exact !important;
                        }
                    </style>
                </head>
                <body>
                    <div class="ticket-commande-container">
                        ${ticketsHtml.join('')}
                    </div>
                </body>
            </html>
        `);
        printWindow.document.close();
        printWindow.print();
    }

    /**
     * Imprimer les tickets (fonction générique)
     */
    printTickets(ticketsHtml) {
        const printWindow = window.open('', '_blank');
        printWindow.document.write(`
            <html>
                <head>
                    <title>Tickets de Commande</title>
                    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css">
                    <style>
                        @page { size: B5; margin: 5mm; }
                        body { 
                            margin: 0; 
                            padding: 0; 
                            font-family: Arial, sans-serif; 
                            -webkit-print-color-adjust: exact !important;
                            color-adjust: exact !important;
                            print-color-adjust: exact !important;
                        }
                        * {
                            -webkit-print-color-adjust: exact !important;
                            color-adjust: exact !important;
                            print-color-adjust: exact !important;
                        }
                        .ticket-commande-container {
                            display: grid;
                            grid-template-columns: repeat(2, 1fr);
                            gap: 2mm;
                            width: 100%;
                            max-width: 180mm;
                            margin: 0 auto;
                            padding: 2mm;
                        }
                        .ticket-commande {
                            width: 75mm;
                            height: 74mm;
                            border: 0.5px solid black;
                            font-family: Arial, sans-serif;
                            font-size: 7px;
                            background: white;
                            page-break-inside: avoid;
                            margin: 0;
                            overflow: hidden;
                        }
                        .ticket-header {
                            background-color: #000000 !important;
                            color: #ffffff !important;
                            padding: 1mm;
                            display: flex;
                            justify-content: space-between;
                            align-items: center;
                            font-weight: bold;
                            font-size: 8px;
                            height: 5mm;
                            -webkit-print-color-adjust: exact !important;
                            color-adjust: exact !important;
                            print-color-adjust: exact !important;
                            background: #000000 !important;
                            color: #ffffff !important;
                        }
                        .ticket-body {
                            padding: 2.5mm;
                        }
                        
                        .barcode-image {
                            max-width: 15mm !important;
                            max-height: 4mm !important;
                            object-fit: contain !important;
                            width: 15mm !important;
                            height: 4mm !important;
                        }
                        
                        .barcode-left .barcode-container {
                            background: white !important;
                            border: 0.3px solid #333333 !important;
                            padding: 0.3mm !important;
                            width: 15mm !important;
                            height: 4mm !important;
                        }
                        .info-line {
                            display: flex;
                            align-items: center;
                            margin-bottom: 1mm;
                            padding-bottom: 1mm;
                            border-bottom: 1px dashed #ccc;
                        }
                        .info-icon {
                            margin-right: 2mm;
                            font-size: 10px;
                            width: 12px;
                            text-align: center;
                        }
                        .info-text {
                            font-size: 7px;
                            flex: 1;
                        }
                        .ticket-footer {
                            background-color: #000000 !important;
                            color: #ffffff !important;
                            padding: 2mm;
                            display: flex;
                            justify-content: space-between;
                            align-items: center;
                            font-weight: bold;
                            font-size: 8px;
                            -webkit-print-color-adjust: exact !important;
                            color-adjust: exact !important;
                            print-color-adjust: exact !important;
                            background: #000000 !important;
                            color: #ffffff !important;
                        }
                        .ticket-contact {
                            background: #f8f8f8 !important;
                            padding: 2mm;
                            display: flex;
                            justify-content: space-between;
                            align-items: center;
                            font-size: 6px;
                            border-top: 1px solid #000000 !important;
                            -webkit-print-color-adjust: exact !important;
                            color-adjust: exact !important;
                            print-color-adjust: exact !important;
                            background-color: #f8f8f8 !important;
                            color: #000000 !important;
                        }
                        .contact-name {
                            font-weight: bold;
                            font-size: 8px;
                            color: #000000 !important;
                            -webkit-print-color-adjust: exact !important;
                            color-adjust: exact !important;
                            print-color-adjust: exact !important;
                        }
                        .contact-info {
                            text-align: right;
                            font-weight: bold;
                            font-size: 6px;
                            color: #000000 !important;
                            -webkit-print-color-adjust: exact !important;
                            color-adjust: exact !important;
                            print-color-adjust: exact !important;
                        }
                        .ticket-checkbox {
                            display: none;
                        }
                        
                        /* Assurer l'affichage des icônes Font Awesome lors de l'impression */
                        .fas, .far, .fab {
                            font-family: "Font Awesome 6 Free" !important;
                            font-weight: 900 !important;
                            -webkit-print-color-adjust: exact !important;
                            color-adjust: exact !important;
                            print-color-adjust: exact !important;
                        }
                    </style>
                </head>
                <body>
                    <div class="ticket-commande-container">
                        ${ticketsHtml.join('')}
                    </div>
                </body>
            </html>
        `);
        printWindow.document.close();
        printWindow.print();
    }

    /**
     * Imprimer le ticket de commande (fonction legacy)
     */
    printTicket() {
        const ticketContent = document.querySelector('#ticketContent .ticket-commande');
        if (ticketContent) {
            this.printTickets([ticketContent.outerHTML]);
        }
    }


    /**
     * Initialiser les fonctionnalités des codes-barres - SUPPRIMÉE
     * Plus nécessaire car nous utilisons uniquement les QR codes
     */
    // initializeCodesBarresFeatures() - SUPPRIMÉE

    /**
     * Initialiser les fonctionnalités des étiquettes
     */
    initializeEtiquettesFeatures() {
        // Charger les scripts nécessaires si pas déjà fait
        this.loadScript('/static/js/etiquettage/etiquettes-articles-modal.js');
    }

    /**
     * Charger un script dynamiquement
     */
    loadScript(src) {
        if (!document.querySelector(`script[src="${src}"]`)) {
            const script = document.createElement('script');
            script.src = src;
            document.head.appendChild(script);
        }
    }


    /**
     * Imprimer les labels sélectionnés
     */
    printLabels(labelsHtml, title, type = 'articles') {
        const printWindow = window.open('', '_blank');
        const containerClass = type === 'commandes' ? 'commande-labels-container' : 'article-labels-container';
        const timestamp = new Date().toLocaleString('fr-FR');
        
        // Déterminer le titre de la page selon le type
        let pageTitle = '';
        let pageSubtitle = '';
        
        if (type === 'commandes') {
            pageTitle = 'Codes-barres Code128 - Toutes les commandes';
            pageSubtitle = `Commande: ALL | Date: ${timestamp} | Total: ${labelsHtml.length} article(s)`;
        } else {
            pageTitle = 'QR Codes - Toutes les commandes';
            pageSubtitle = `Commande: ALL | Date: ${timestamp} | Total: ${labelsHtml.length} article(s)`;
        }
        
        printWindow.document.write(`
            <!DOCTYPE html>
            <html lang="fr">
            <head>
                <meta charset="UTF-8">
                <meta name="viewport" content="width=device-width, initial-scale=1.0">
                <title>${pageTitle}</title>
                <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css">
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
                            size: B5 portrait;
                            margin: 5mm;
                        }

                        body {
                            margin: 0;
                            padding: 0;
                            background: white !important;
                            -webkit-print-color-adjust: exact !important;
                            color-adjust: exact !important;
                            width: 210mm;
                            height: 297mm;
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
                            width: 166mm; /* 176mm - 10mm de marges */
                            height: 240mm; /* 250mm - 10mm de marges */
                            margin: 0 auto;
                            position: relative;
                            margin-top: 10mm;
                            margin-bottom: 5mm;
                            padding: 5mm;
                            min-height: calc(240mm - 10mm - 5mm);
                        }

                        .print-header {
                            position: fixed;
                            top: 5mm;
                            left: 5mm;
                            right: 5mm;
                            height: 10mm;
                            background: white;
                            z-index: 1000;
                            border-bottom: 1px solid #333;
                        }

                        .print-footer {
                            position: fixed;
                            bottom: 5mm;
                            left: 5mm;
                            right: 5mm;
                            height: 8mm;
                            background: white;
                            z-index: 1000;
                            border-top: 0.5px solid #ccc;
                        }

                        .labels-grid {
                            padding: 2mm;
                            width: 100%;
                            height: 100%;
                            margin-top: 2mm;
                        }
                    }

                    /* Styles pour l'en-tête et pied de page */
                    .print-header {
                        text-align: center;
                        padding: 2mm;
                        background: white;
                        height: 10mm;
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
                        padding: 1mm;
                        font-size: 7px;
                        color: #666;
                        background: white;
                        height: 8mm;
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
                    .labels-grid,
                    .article-labels-container,
                    .commande-labels-container {
                        display: grid;
                        grid-template-columns: repeat(2, 1fr);
                        gap: 2mm;
                        width: 100%;
                        max-width: 180mm;
                        margin: 0 auto;
                        padding: 2mm;
                        margin-top: 2mm;
                    }

                    /* Étiquette individuelle */
                    .article-label,
                    .commande-label {
                        width: 75mm;
                        height: 74mm;
                        border: 0.5px solid #000;
                        font-family: Arial, sans-serif;
                        font-size: 9px;
                        display: flex;
                        flex-direction: column;
                        justify-content: center;
                        align-items: center;
                        background: white;
                        page-break-inside: avoid;
                        break-inside: avoid;
                        margin: 0;
                        overflow: hidden;
                        position: relative;
                        padding: 2mm;
                    }

                    .article-label *,
                    .commande-label * {
                        -webkit-print-color-adjust: exact !important;
                        color-adjust: exact !important;
                    }

                    /* Code-barres */
                    .label-barcode {
                        max-width: 100%;
                        max-height: 5mm;
                        object-fit: contain;
                        margin-bottom: 1mm;
                    }

                    /* Référence */
                    .article-reference {
                        font-size: 8px;
                        text-align: center;
                        font-weight: bold;
                        color: #000;
                        word-break: break-word;
                        margin-bottom: 1mm;
                    }

                    /* Variante */
                    .article-variante {
                        font-size: 7px;
                        text-align: center;
                        color: #666;
                    }

                    /* Masquer les checkboxes lors de l'impression */
                    .label-checkbox {
                        display: none !important;
                    }
                    
                    /* Assurer l'affichage des icônes Font Awesome lors de l'impression */
                    .fas, .far, .fab {
                        font-family: "Font Awesome 6 Free" !important;
                        font-weight: 900 !important;
                        -webkit-print-color-adjust: exact !important;
                        color-adjust: exact !important;
                        print-color-adjust: exact !important;
                    }

                    /* Responsive pour l'écran */
                    @media screen {
                        body {
                            background: #f5f5f5;
                            padding: 20px;
                        }

                        .print-container {
                            background: white;
                            padding: 20px;
                            border-radius: 8px;
                            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
                        }
                    }
                </style>
            </head>
            <body>
                <div class="print-container">
                    <!-- En-tête de page -->
                    <div class="print-header">
                        <h1>${pageTitle}</h1>
                        <p>${pageSubtitle}</p>
                    </div>

                    <!-- Grille des étiquettes -->
                    <div class="${containerClass}">
                        ${labelsHtml.join('')}
                    </div>

                    <!-- Pied de page -->
                    <div class="print-footer">
                        <p>Généré le ${timestamp} - YZ-CMD</p>
                    </div>
                </div>
            </body>
            </html>
        `);
        printWindow.document.close();
        printWindow.print();
    }

    /**
     * Afficher une notification
     * @param {string} message - Message à afficher
     * @param {string} type - Type de notification ('success', 'info', 'warning', 'error')
     */
    showNotification(message, type = 'info') {
        // Supprimer les notifications existantes
        const existingNotifications = document.querySelectorAll('.impression-notification');
        existingNotifications.forEach(notification => notification.remove());

        // Créer la notification
        const notification = document.createElement('div');
        notification.className = `impression-notification fixed top-4 right-4 z-50 p-4 rounded-lg shadow-lg transition-all duration-300 transform translate-x-full`;
        
        // Couleurs selon le type
        const colors = {
            success: 'bg-green-500 text-white',
            info: 'bg-blue-500 text-white',
            warning: 'bg-yellow-500 text-black',
            error: 'bg-red-500 text-white'
        };
        
        notification.className += ` ${colors[type] || colors.info}`;
        
        // Icône selon le type
        const icons = {
            success: 'fas fa-check-circle',
            info: 'fas fa-info-circle',
            warning: 'fas fa-exclamation-triangle',
            error: 'fas fa-times-circle'
        };
        
        notification.innerHTML = `
            <div class="flex items-center space-x-3">
                <i class="${icons[type] || icons.info} text-lg"></i>
                <div>
                    <div class="font-medium">${message}</div>
                    <div class="text-sm opacity-90">Impression en cours...</div>
                </div>
                <button onclick="this.parentElement.parentElement.remove()" class="ml-2 opacity-70 hover:opacity-100">
                    <i class="fas fa-times"></i>
                </button>
            </div>
        `;
        
        // Ajouter au DOM
        document.body.appendChild(notification);
        
        // Animation d'entrée
        setTimeout(() => {
            notification.classList.remove('translate-x-full');
        }, 100);
        
        // Auto-suppression après 4 secondes
        setTimeout(() => {
            if (notification.parentNode) {
                notification.classList.add('translate-x-full');
                setTimeout(() => {
                    if (notification.parentNode) {
                        notification.parentNode.removeChild(notification);
                    }
                }, 300);
            }
        }, 4000);
    }
}

// Initialiser l'instance globale
const impressionModals = new ImpressionModals();

// Fonctions globales pour compatibilité avec les onclick
function showImpressionModal(commandeId, commandeIdYz, clientNom) {
    impressionModals.showImpressionModal(commandeId, commandeIdYz, clientNom);
}

function hideImpressionChoiceModal() {
    impressionModals.hideImpressionChoiceModal();
}


function imprimerEtiquettesArticles() {
    impressionModals.imprimerEtiquettesArticles();
}

function imprimerTicketCommande() {
    impressionModals.imprimerTicketCommande();
}

function imprimerTicketCommandeMultiple() {
    impressionModals.imprimerTicketCommandeMultiple();
}


// Fonctions pour la modale de choix de format - SUPPRIMÉES
// function hideFormatChoiceModal() - SUPPRIMÉE

function loadEtiquettesWithFormat(format) {
    impressionModals.loadEtiquettesWithFormat(format);
}


/**
 * Impression directe des tickets multiples (sans modale)
 */
function imprimerTicketsMultipleDirect() {
    console.log('🚀 === DÉBUT IMPRESSION TICKETS MULTIPLE ===');
    
    // Afficher un indicateur de chargement
    impressionModals.showNotification('Préparation de l\'impression des tickets...', 'info');
    
    // Récupérer les IDs des commandes sélectionnées
    const selectedIds = getSelectedCommandeIds();
    console.log('📋 IDs récupérés par getSelectedCommandeIds():', selectedIds);
    
    let url = '/Superpreparation/api/ticket-commande-multiple/?direct_print=true';
    
    // Si des commandes sont sélectionnées, les passer en paramètre
    if (selectedIds && selectedIds.length > 0) {
        url += `&selected_ids=${selectedIds.join(',')}`;
        console.log(`🖨️ Impression des tickets pour ${selectedIds.length} commandes sélectionnées:`, selectedIds);
        console.log('🔗 Paramètres ajoutés à l\'URL');
    } else {
        console.log('🖨️ Impression des tickets pour toutes les commandes confirmées');
        console.log('⚠️ Aucune sélection détectée');
    }
    
    console.log('🖨️ URL finale complète:', url);
    console.log('🌐 Envoi de la requête fetch...');
    
    // Récupérer les données des tickets multiples (avec paramètre pour impression directe)
    fetch(url)
        .then(response => {
            console.log('📡 Réponse reçue du serveur');
            console.log('📊 Status:', response.status);
            console.log('📊 StatusText:', response.statusText);
            console.log('📊 Headers:', response.headers);
            return response.json();
        })
        .then(data => {
            console.log('📦 Données reçues:', data);
            console.log('✅ Success:', data.success);
            console.log('📊 Nombre de commandes dans la réponse:', data.commandes ? data.commandes.length : 'Non défini');
            
            if (data.success) {
                // Créer une nouvelle fenêtre pour l'impression
                const printWindow = window.open('', '_blank', 'width=800,height=600');
                
                // HTML pour l'impression - Utiliser exactement la même structure que la modale
                const printHTML = `
                    <!DOCTYPE html>
                    <html>
                    <head>
                        <title>Impression Tickets de Commande Multiple</title>
                        <meta charset="utf-8">
                        <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/5.15.4/css/all.min.css">
                        <style>
                            @page {
                                size: A4;
                                margin: 5mm;
                            }

                            body, html {
                                margin: 0;
                                padding: 0;
                                background: white !important;
                                -webkit-print-color-adjust: exact !important;
                                color-adjust: exact !important;
                                print-color-adjust: exact !important;
                            }
                            
                            .no-print {
                                display: none !important;
                            }
                            
                            /* Container pour les tickets */
                            .ticket-commande-container {
                                display: grid !important;
                                grid-template-columns: repeat(2, 1fr) !important;
                                gap: 3mm !important;
                                width: 100% !important;
                                max-width: 180mm !important;
                                margin: 0 auto !important;
                                padding: 3mm !important;
                            }
                            
                            /* Format compact du ticket */
                            .ticket-commande {
                                width: 85mm !important;
                                height: 85mm !important;
                                border: 1px solid black !important;
                                font-family: Arial, sans-serif !important;
                                font-size: 8px !important;
                                background: white !important;
                                page-break-inside: avoid !important;
                                margin: 0 !important;
                                overflow: hidden;
                                display: flex !important;
                                flex-direction: column !important;
                            }
                            
                            .ticket-commande * {
                                -webkit-print-color-adjust: exact !important;
                                color-adjust: exact !important;
                                print-color-adjust: exact !important;
                            }
                            
                            /* En-tête noir */
                            .ticket-header {
                                background-color: #000000 !important;
                                color: #ffffff !important;
                                padding: 2mm !important;
                                font-size: 9px !important;
                                font-weight: bold !important;
                                display: flex !important;
                                justify-content: space-between !important;
                                align-items: center !important;
                            }
                            
                            .ticket-number {
                                font-weight: bold !important;
                                display: flex !important;
                                align-items: center !important;
                            }
                            
                            .ticket-date {
                                font-weight: bold !important;
                            }
                            
                            /* Corps du ticket */
                            .ticket-body {
                                padding: 2mm !important;
                                flex-grow: 1 !important;
                                display: flex !important;
                                flex-direction: column !important;
                                justify-content: space-between !important;
                            }
                            
                            /* Informations client */
                            .client-info {
                                margin-bottom: 2mm !important;
                            }
                            
                            .info-line {
                                margin-bottom: 1mm !important;
                                padding-bottom: 1mm !important;
                                display: flex !important;
                                align-items: center !important;
                            }
                            
                            .info-icon {
                                font-size: 8px !important;
                                margin-right: 2mm !important;
                                width: 10px !important;
                                font-weight: bold !important;
                            }
                            
                            .info-text {
                                font-size: 7px !important;
                                font-weight: normal !important;
                                word-break: break-word !important;
                                flex: 1 !important;
                            }
                            
                            /* Description des articles */
                            .articles-description {
                                margin-top: 2mm !important;
                            }
                            
                            /* Pied de page noir */
                            .ticket-footer {
                                background-color: #000000 !important;
                                color: #ffffff !important;
                                padding: 2mm !important;
                                font-size: 8px !important;
                                font-weight: bold !important;
                                display: flex !important;
                                justify-content: space-between !important;
                                align-items: center !important;
                            }
                            
                            .ticket-price {
                                font-weight: bold !important;
                            }
                            
                            .ticket-city {
                                font-weight: bold !important;
                            }
                            
                            /* Informations de contact */
                            .ticket-contact {
                                background: #f8f8f8 !important;
                                padding: 2mm !important;
                                font-size: 6px !important;
                                display: flex !important;
                                justify-content: space-between !important;
                                align-items: center !important;
                                border-top: 1px solid #000000 !important;
                            }
                            
                            .contact-name {
                                font-size: 8px !important;
                                font-weight: bold !important;
                                color: #000000 !important;
                            }
                            
                            .contact-info {
                                text-align: right !important;
                                color: #000000 !important;
                                font-weight: bold !important;
                                font-size: 6px !important;
                            }
                            
                            .contact-info div {
                                line-height: 1.2 !important;
                            }
                            
                            .label-checkbox {
                                display: none !important;
                            }
                            
                            .articles-count-badge {
                                display: inline-flex !important;
                                background: white !important;
                                color: #000 !important;
                                border-radius: 50% !important;
                                width: 20px !important;
                                height: 20px !important;
                                align-items: center !important;
                                justify-content: center !important;
                                margin-left: 8px !important;
                                font-size: 10px !important;
                                font-weight: bold !important;
                                border: 1px solid #000 !important;
                                text-align: center !important;
                                line-height: 1 !important;
                            }
                            
                            .count-number {
                                font-size: 10px !important;
                                font-weight: bold !important;
                                line-height: 1 !important;
                                margin: 0 !important;
                                padding: 0 !important;
                                display: flex !important;
                                align-items: center !important;
                                justify-content: center !important;
                                width: 100% !important;
                                height: 100% !important;
                            }
                            
                            @media print {
                                body {
                                    -webkit-print-color-adjust: exact !important;
                                    color-adjust: exact !important;
                                    print-color-adjust: exact !important;
                                }
                            }
                        </style>
                    </head>
                    <body>
                        <div class="ticket-commande-container">
                            ${data.html}
                        </div>
                        <script>
                            // Lancer l'impression automatiquement
                            window.onload = function() {
                                setTimeout(function() {
                                    window.print();
                                    setTimeout(function() {
                                        window.close();
                                    }, 1000);
                                }, 500);
                            };
                        </script>
                    </body>
                    </html>
                `;
                
                // Écrire le contenu dans la nouvelle fenêtre
                printWindow.document.write(printHTML);
                printWindow.document.close();
                
                impressionModals.showNotification('Impression lancée !', 'success');
            } else {
                impressionModals.showNotification(`Erreur: ${data.error}`, 'error');
            }
        })
        .catch(error => {
            console.error('Erreur lors de l\'impression directe:', error);
            impressionModals.showNotification('Erreur lors de l\'impression', 'error');
        });
}

/**
 * Impression directe des codes QR des articles (sans modale)
 */
function imprimerCodesQRArticlesDirect() {
    // Afficher un indicateur de chargement
    impressionModals.showNotification('Préparation de l\'impression des codes QR...', 'info');
    
    // Récupérer les IDs des commandes sélectionnées
    const selectedIds = getSelectedCommandeIds();
    let url = '/Superpreparation/api/etiquettes-articles-multiple/';
    
    // Si des commandes sont sélectionnées, les passer en paramètre
    if (selectedIds && selectedIds.length > 0) {
        url += `?selected_ids=${selectedIds.join(',')}`;
        console.log(`🖨️ Impression des codes QR pour ${selectedIds.length} commandes sélectionnées:`, selectedIds);
    } else {
        console.log('🖨️ Impression des codes QR pour tous les articles des commandes confirmées');
    }
    
    // Récupérer les données des codes QR des articles (selon la sélection)
    fetch(url)
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                // Créer une nouvelle fenêtre pour l'impression
                const printWindow = window.open('', '_blank', 'width=800,height=600');
                
                // HTML pour l'impression - Utiliser exactement la même structure que la modale
                const printHTML = `
                    <!DOCTYPE html>
                    <html>
                    <head>
                        <title>Impression Codes QR Articles</title>
                        <meta charset="utf-8">
                        <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/5.15.4/css/all.min.css">
                        <style>
                            @page {
                                size: A4;
                                margin: 5mm;
                            }

                            body, html {
                                margin: 0;
                                padding: 0;
                                background: white !important;
                                -webkit-print-color-adjust: exact !important;
                                color-adjust: exact !important;
                                print-color-adjust: exact !important;
                            }
                            
                            .no-print {
                                display: none !important;
                            }
                            
                            /* Container pour les étiquettes */
                            .etiquettes-container {
                                display: grid !important;
                                grid-template-columns: repeat(2, 1fr) !important;
                                gap: 3mm !important;
                                width: 100% !important;
                                max-width: 180mm !important;
                                margin: 0 auto !important;
                                padding: 3mm !important;
                            }
                            
                            /* Format compact de l'étiquette */
                            .etiquette-article {
                                width: 85mm !important;
                                height: 85mm !important;
                                border: 1px solid black !important;
                                font-family: Arial, sans-serif !important;
                                font-size: 8px !important;
                                background: white !important;
                                page-break-inside: avoid !important;
                                margin: 0 !important;
                                overflow: hidden;
                                display: flex !important;
                                flex-direction: column !important;
                                align-items: center !important;
                                justify-content: center !important;
                                text-align: center !important;
                            }
                            
                            .etiquette-article * {
                                -webkit-print-color-adjust: exact !important;
                                color-adjust: exact !important;
                                print-color-adjust: exact !important;
                            }
                            
                            /* QR Code */
                            .qr-code {
                                margin-bottom: 2mm !important;
                            }
                            
                            .qr-code img {
                                width: 25mm !important;
                                height: 25mm !important;
                                border: 1px solid #000 !important;
                            }
                            
                            /* Informations article */
                            .article-info {
                                padding: 2mm !important;
                                font-size: 7px !important;
                                line-height: 1.2 !important;
                            }
                            
                            .article-name {
                                font-weight: bold !important;
                                margin-bottom: 1mm !important;
                                word-break: break-word !important;
                            }
                            
                            .article-variant {
                                font-size: 6px !important;
                                color: #666 !important;
                                word-break: break-word !important;
                            }
                            
                            @media print {
                                body {
                                    -webkit-print-color-adjust: exact !important;
                                    color-adjust: exact !important;
                                    print-color-adjust: exact !important;
                                }
                            }
                        </style>
                    </head>
                    <body>
                        <div class="etiquettes-container">
                            ${data.html}
                        </div>
                        <script>
                            // Lancer l'impression automatiquement
                            window.onload = function() {
                                setTimeout(function() {
                                    window.print();
                                    setTimeout(function() {
                                        window.close();
                                    }, 1000);
                                }, 500);
                            };
                        </script>
                    </body>
                    </html>
                `;
                
                // Écrire le contenu dans la nouvelle fenêtre
                printWindow.document.write(printHTML);
                printWindow.document.close();
                
                impressionModals.showNotification('Impression lancée !', 'success');
            } else {
                impressionModals.showNotification(`Erreur: ${data.error}`, 'error');
            }
        })
        .catch(error => {
            console.error('Erreur lors de l\'impression directe des codes QR:', error);
            impressionModals.showNotification('Erreur lors de l\'impression', 'error');
        });
}

/**
 * Impression multiple fusionnée : tickets + codes QR des articles
 * Lance les deux impressions en séquence avec une barre de progression
 */
window.impressionMultipleFusionnee = function() {
    // Désactiver le bouton pendant l'impression
    const bulkPrintBtn = document.getElementById('bulkPrintBtn');
    const progressContainer = document.getElementById('printProgressContainer');
    const progressBar = document.getElementById('printProgressBar');
    const progressText = document.getElementById('printProgressText');
    
    if (!bulkPrintBtn || !progressContainer || !progressBar || !progressText) {
        console.error('Éléments de progression non trouvés');
        return;
    }
    
    // Afficher la barre de progression et désactiver le bouton
    bulkPrintBtn.disabled = true;
    bulkPrintBtn.classList.add('opacity-50', 'cursor-not-allowed');
    progressContainer.classList.remove('hidden');
    
    // Variables pour suivre la progression
    let currentStep = 0;
    const totalSteps = 2;
    
    // Fonction pour mettre à jour la progression
    function updateProgress(step, text) {
        currentStep = step;
        const percentage = (step / totalSteps) * 100;
        progressBar.style.width = percentage + '%';
        progressText.textContent = text;
    }
    
    // Fonction pour terminer l'impression
    function finishPrinting() {
        bulkPrintBtn.disabled = false;
        bulkPrintBtn.classList.remove('opacity-50', 'cursor-not-allowed');
        progressContainer.classList.add('hidden');
        progressBar.style.width = '0%';
        progressText.textContent = 'Préparation...';
        
        // Notification de succès
        impressionModals.showNotification('Impression multiple terminée !', 'success');
    }
    
    // Fonction pour gérer les erreurs
    function handleError(error, stepName) {
        console.error(`Erreur lors de ${stepName}:`, error);
        impressionModals.showNotification(`Erreur lors de ${stepName}`, 'error');
        finishPrinting();
    }
    
    // Étape 1 : Impression des tickets multiples
    updateProgress(1, 'Impression des tickets de commande...');
    
    fetch('/Superpreparation/api/ticket-commande-multiple/?direct_print=true')
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                // Créer une nouvelle fenêtre pour l'impression des tickets
                const printWindow = window.open('', '_blank', 'width=800,height=600');
                
                // HTML pour l'impression des tickets
                const printHTML = `
                    <!DOCTYPE html>
                    <html>
                    <head>
                        <title>Impression Tickets de Commande Multiple</title>
                        <meta charset="utf-8">
                        <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/5.15.4/css/all.min.css">
                        <style>
                            @page {
                                size: A4;
                                margin: 5mm;
                            }

                            body, html {
                                margin: 0;
                                padding: 0;
                                background: white !important;
                                -webkit-print-color-adjust: exact !important;
                                color-adjust: exact !important;
                                print-color-adjust: exact !important;
                            }
                            
                            .no-print {
                                display: none !important;
                            }
                            
                            /* Container pour les tickets */
                            .ticket-commande-container {
                                display: grid !important;
                                grid-template-columns: repeat(2, 1fr) !important;
                                gap: 3mm !important;
                                width: 100% !important;
                                max-width: 180mm !important;
                                margin: 0 auto !important;
                                padding: 3mm !important;
                            }
                            
                            /* Format compact du ticket */
                            .ticket-commande {
                                width: 85mm !important;
                                height: 85mm !important;
                                border: 1px solid black !important;
                                font-family: Arial, sans-serif !important;
                                font-size: 8px !important;
                                background: white !important;
                                page-break-inside: avoid !important;
                                margin: 0 !important;
                                overflow: hidden;
                                display: flex !important;
                                flex-direction: column !important;
                            }
                            
                            .ticket-commande * {
                                -webkit-print-color-adjust: exact !important;
                                color-adjust: exact !important;
                                print-color-adjust: exact !important;
                            }
                            
                            /* En-tête noir */
                            .ticket-header {
                                background-color: #000000 !important;
                                color: #ffffff !important;
                                padding: 2mm !important;
                                font-size: 9px !important;
                                font-weight: bold !important;
                                display: flex !important;
                                justify-content: space-between !important;
                                align-items: center !important;
                            }
                            
                            .ticket-number {
                                font-weight: bold !important;
                                display: flex !important;
                                align-items: center !important;
                            }
                            
                            .ticket-date {
                                font-size: 7px !important;
                            }
                            
                            /* Contenu du ticket */
                            .ticket-content {
                                padding: 2mm !important;
                                flex: 1 !important;
                                display: flex !important;
                                flex-direction: column !important;
                                justify-content: space-between !important;
                            }
                            
                            .client-info {
                                margin-bottom: 2mm !important;
                            }
                            
                            .client-name {
                                font-weight: bold !important;
                                font-size: 9px !important;
                                margin-bottom: 1mm !important;
                            }
                            
                            .client-details {
                                font-size: 7px !important;
                                color: #666 !important;
                                line-height: 1.2 !important;
                            }
                            
                            .articles-info {
                                margin-bottom: 2mm !important;
                            }
                            
                            .articles-title {
                                font-weight: bold !important;
                                font-size: 8px !important;
                                margin-bottom: 1mm !important;
                                color: #333 !important;
                            }
                            
                            .articles-list {
                                font-size: 7px !important;
                                color: #666 !important;
                                line-height: 1.2 !important;
                                word-break: break-word !important;
                            }
                            
                            .total-info {
                                border-top: 1px solid #ccc !important;
                                padding-top: 1mm !important;
                                text-align: right !important;
                            }
                            
                            .total-amount {
                                font-weight: bold !important;
                                font-size: 10px !important;
                                color: #000 !important;
                            }
                            
                            .articles-count {
                                font-size: 7px !important;
                                color: #666 !important;
                                margin-top: 0.5mm !important;
                            }
                            
                            @media print {
                                body {
                                    -webkit-print-color-adjust: exact !important;
                                    color-adjust: exact !important;
                                    print-color-adjust: exact !important;
                                }
                            }
                        </style>
                    </head>
                    <body>
                        <div class="ticket-commande-container">
                            ${data.html}
                        </div>
                        <script>
                            // Lancer l'impression automatiquement
                            window.onload = function() {
                                setTimeout(function() {
                                    window.print();
                                    setTimeout(function() {
                                        window.close();
                                        // Notifier la fenêtre parent que l'impression des tickets est terminée
                                        if (window.opener) {
                                            window.opener.postMessage('tickets_printed', '*');
                                        }
                                    }, 1000);
                                }, 500);
                            };
                        </script>
                    </body>
                    </html>
                `;
                
                // Écrire le contenu dans la nouvelle fenêtre
                printWindow.document.write(printHTML);
                printWindow.document.close();
                
                // Attendre que l'impression des tickets soit terminée avant de passer aux codes QR
                const checkTicketsPrinted = setInterval(() => {
                    if (printWindow.closed) {
                        clearInterval(checkTicketsPrinted);
                        
                        // Étape 2 : Impression des codes QR des articles
                        updateProgress(2, 'Impression des codes QR des articles...');
                        
                        // Petit délai pour permettre à l'utilisateur de voir la progression
                        setTimeout(() => {
                            fetch('/Superpreparation/api/etiquettes-articles-multiple/')
                                .then(response => response.json())
                                .then(data => {
                                    if (data.success) {
                                        // Créer une nouvelle fenêtre pour l'impression des codes QR
                                        const qrPrintWindow = window.open('', '_blank', 'width=800,height=600');
                                        
                                        // HTML pour l'impression des codes QR
                                        const qrPrintHTML = `
                                            <!DOCTYPE html>
                                            <html>
                                            <head>
                                                <title>Impression Codes QR Articles</title>
                                                <meta charset="utf-8">
                                                <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/5.15.4/css/all.min.css">
                                                <style>
                                                    @page {
                                                        size: A4;
                                                        margin: 5mm;
                                                    }

                                                    body, html {
                                                        margin: 0;
                                                        padding: 0;
                                                        background: white !important;
                                                        -webkit-print-color-adjust: exact !important;
                                                        color-adjust: exact !important;
                                                        print-color-adjust: exact !important;
                                                    }
                                                    
                                                    .no-print {
                                                        display: none !important;
                                                    }
                                                    
                                                    /* Container pour les étiquettes */
                                                    .etiquettes-container {
                                                        display: grid !important;
                                                        grid-template-columns: repeat(2, 1fr) !important;
                                                        gap: 3mm !important;
                                                        width: 100% !important;
                                                        max-width: 180mm !important;
                                                        margin: 0 auto !important;
                                                        padding: 3mm !important;
                                                    }
                                                    
                                                    /* Format compact de l'étiquette */
                                                    .etiquette-article {
                                                        width: 85mm !important;
                                                        height: 60mm !important;
                                                        border: 1px solid black !important;
                                                        font-family: Arial, sans-serif !important;
                                                        font-size: 8px !important;
                                                        background: white !important;
                                                        page-break-inside: avoid !important;
                                                        margin: 0 !important;
                                                        overflow: hidden;
                                                        display: flex !important;
                                                        flex-direction: column !important;
                                                        align-items: center !important;
                                                        justify-content: center !important;
                                                        text-align: center !important;
                                                    }
                                                    
                                                    .etiquette-article * {
                                                        -webkit-print-color-adjust: exact !important;
                                                        color-adjust: exact !important;
                                                        print-color-adjust: exact !important;
                                                    }
                                                    
                                                    /* QR Code */
                                                    .qr-code {
                                                        margin-bottom: 2mm !important;
                                                    }
                                                    
                                                    .qr-code img {
                                                        width: 25mm !important;
                                                        height: 25mm !important;
                                                        border: 1px solid #000 !important;
                                                    }
                                                    
                                                    /* Informations article */
                                                    .article-info {
                                                        padding: 2mm !important;
                                                        font-size: 7px !important;
                                                        line-height: 1.2 !important;
                                                    }
                                                    
                                                    .article-name {
                                                        font-weight: bold !important;
                                                        margin-bottom: 1mm !important;
                                                        word-break: break-word !important;
                                                    }
                                                    
                                                    .article-variant {
                                                        font-size: 6px !important;
                                                        color: #666 !important;
                                                        word-break: break-word !important;
                                                    }
                                                    
                                                    @media print {
                                                        body {
                                                            -webkit-print-color-adjust: exact !important;
                                                            color-adjust: exact !important;
                                                            print-color-adjust: exact !important;
                                                        }
                                                    }
                                                </style>
                                            </head>
                                            <body>
                                                <div class="etiquettes-container">
                                                    ${data.html}
                                                </div>
                                                <script>
                                                    // Lancer l'impression automatiquement
                                                    window.onload = function() {
                                                        setTimeout(function() {
                                                            window.print();
                                                            setTimeout(function() {
                                                                window.close();
                                                                // Notifier la fenêtre parent que l'impression des codes QR est terminée
                                                                if (window.opener) {
                                                                    window.opener.postMessage('qr_printed', '*');
                                                                }
                                                            }, 1000);
                                                        }, 500);
                                                    };
                                                </script>
                                            </body>
                                            </html>
                                        `;
                                        
                                        // Écrire le contenu dans la nouvelle fenêtre
                                        qrPrintWindow.document.write(qrPrintHTML);
                                        qrPrintWindow.document.close();
                                        
                                        // Attendre que l'impression des codes QR soit terminée
                                        const checkQRPrinted = setInterval(() => {
                                            if (qrPrintWindow.closed) {
                                                clearInterval(checkQRPrinted);
                                                finishPrinting();
                                            }
                                        }, 500);
                                        
                                    } else {
                                        handleError(new Error(data.error), 'l\'impression des codes QR');
                                    }
                                })
                                .catch(error => {
                                    handleError(error, 'l\'impression des codes QR');
                                });
                        }, 1000); // Délai de 1 seconde
                    }
                }, 500);
                
            } else {
                handleError(new Error(data.error), 'l\'impression des tickets');
            }
        })
        .catch(error => {
            handleError(error, 'l\'impression des tickets');
        });
};

// Fonction pour récupérer les IDs des commandes sélectionnées
function getSelectedCommandeIds() {
    try {
        // Récupérer tous les checkboxes de commandes cochés
        const selectedCheckboxes = document.querySelectorAll('.commande-checkbox:checked');
        
        console.log('🔍 Checkboxes trouvés:', selectedCheckboxes.length);
        console.log('🔍 Checkboxes:', selectedCheckboxes);
        
        if (selectedCheckboxes.length === 0) {
            console.log('📋 Aucune commande sélectionnée');
            return [];
        }
        
        // Extraire les IDs des commandes sélectionnées
        const selectedIds = Array.from(selectedCheckboxes).map(checkbox => {
            const commandeId = checkbox.getAttribute('data-commande-id');
            console.log('🔍 Checkbox:', checkbox, 'data-commande-id:', commandeId);
            if (commandeId) {
                return commandeId;
            } else {
                console.warn('⚠️ Checkbox sans data-commande-id:', checkbox);
                return null;
            }
        }).filter(id => id !== null);
        
        console.log(`📋 ${selectedIds.length} commandes sélectionnées:`, selectedIds);
        return selectedIds;
        
    } catch (error) {
        console.error('❌ Erreur lors de la récupération des IDs sélectionnés:', error);
        return [];
    }
}

// S'assurer que la fonction est disponible globalement
if (typeof window !== 'undefined') {
    window.impressionMultipleFusionnee = window.impressionMultipleFusionnee || function() {
        console.error('La fonction impressionMultipleFusionnee n\'est pas encore chargée');
        if (window.impressionModals && window.impressionModals.showNotification) {
            window.impressionModals.showNotification('Erreur', 'La fonction d\'impression multiple n\'est pas encore disponible', 'error');
        }
    };
    
    // Rendre la fonction getSelectedCommandeIds disponible globalement
    window.getSelectedCommandeIds = getSelectedCommandeIds;
}
