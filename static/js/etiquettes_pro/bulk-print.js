/**
 * Gestionnaire d'impression multiple des étiquettes
 * Chaque étiquette est imprimée sur sa propre page
 */

class BulkEtiquettePrinter {
    constructor() {
        this.selectedEtiquettes = new Set();
        this.isPrinting = false;
        this.init();
    }

    init() {
        console.log('🖨️ [BULK-PRINT] Initialisation de l\'impression multiple');
        this.attachEventListeners();
        this.updateUI();
    }

    attachEventListeners() {
        // Checkboxes individuelles
        document.addEventListener('change', (e) => {
            if (e.target.classList.contains('etiquette-checkbox')) {
                this.handleCheckboxChange(e.target);
            }
        });

        // Boutons de sélection
        const selectAllBtn = document.getElementById('select-all-btn');
        const deselectAllBtn = document.getElementById('deselect-all-btn');
        const bulkPrintBtn = document.getElementById('bulk-print-btn');

        if (selectAllBtn) {
            selectAllBtn.addEventListener('click', () => this.selectAll());
        }

        if (deselectAllBtn) {
            deselectAllBtn.addEventListener('click', () => this.deselectAll());
        }

        if (bulkPrintBtn) {
            bulkPrintBtn.addEventListener('click', () => this.printSelected());
        }


        console.log('✅ [BULK-PRINT] Event listeners attachés');
    }

    handleCheckboxChange(checkbox) {
        const etiquetteId = checkbox.dataset.etiquetteId;
        
        if (checkbox.checked) {
            this.selectedEtiquettes.add(etiquetteId);
        } else {
            this.selectedEtiquettes.delete(etiquetteId);
        }

        this.updateUI();
        console.log(`🔍 [BULK-PRINT] Étiquette ${etiquetteId} ${checkbox.checked ? 'sélectionnée' : 'désélectionnée'}`);
    }

    selectAll() {
        const checkboxes = document.querySelectorAll('.etiquette-checkbox');
        checkboxes.forEach(checkbox => {
            if (!checkbox.disabled) {
                checkbox.checked = true;
                this.selectedEtiquettes.add(checkbox.dataset.etiquetteId);
            }
        });
        this.updateUI();
        console.log('✅ [BULK-PRINT] Toutes les étiquettes sélectionnées');
    }

    deselectAll() {
        const checkboxes = document.querySelectorAll('.etiquette-checkbox');
        checkboxes.forEach(checkbox => {
            checkbox.checked = false;
        });
        this.selectedEtiquettes.clear();
        this.updateUI();
        console.log('✅ [BULK-PRINT] Toutes les étiquettes désélectionnées');
    }

    updateUI() {
        const toolbar = document.getElementById('bulk-actions-toolbar');
        const selectedCount = document.getElementById('selected-count');
        const bulkPrintBtn = document.getElementById('bulk-print-btn');

        // La barre d'outils reste toujours visible
        toolbar.classList.remove('hidden');
        selectedCount.textContent = this.selectedEtiquettes.size;
        
        // Les boutons restent toujours actifs
        bulkPrintBtn.disabled = false;
    }

    async printSelected() {
        if (this.isPrinting) {
            console.log('⚠️ [BULK-PRINT] Impression déjà en cours');
            return;
        }

        if (this.selectedEtiquettes.size === 0) {
            this.showError('Aucune étiquette sélectionnée');
            return;
        }

        this.isPrinting = true;
        const bulkPrintBtn = document.getElementById('bulk-print-btn');
        const originalText = bulkPrintBtn.innerHTML;
        
        try {
            bulkPrintBtn.disabled = true;
            bulkPrintBtn.innerHTML = '<i class="fas fa-spinner fa-spin mr-2"></i>Impression...';

            console.log(`🖨️ [BULK-PRINT] Début de l'impression de ${this.selectedEtiquettes.size} étiquettes`);

            // Récupérer les données de toutes les étiquettes sélectionnées
            const printData = await this.fetchAllPrintData();
            
            if (printData.length === 0) {
                throw new Error('Aucune donnée d\'impression récupérée');
            }

            // Créer le contenu d'impression avec saut de page entre chaque étiquette
            const printContent = this.generateBulkPrintHTML(printData);
            
            // Ouvrir la fenêtre d'impression
            this.openBulkPrintWindow(printContent);

            console.log('✅ [BULK-PRINT] Impression multiple lancée avec succès');

        } catch (error) {
            console.error('❌ [BULK-PRINT] Erreur lors de l\'impression multiple:', error);
            this.showError(`Erreur d'impression: ${error.message}`);
        } finally {
            this.isPrinting = false;
            bulkPrintBtn.disabled = false;
            bulkPrintBtn.innerHTML = originalText;
        }
    }

    // Fonction de génération PDF supprimée

    // Fonction de génération PDF multiple supprimée

    async fetchAllPrintData() {
        const printData = [];
        const etiquetteIds = Array.from(this.selectedEtiquettes);

        for (const etiquetteId of etiquetteIds) {
            try {
                console.log(`📡 [BULK-PRINT] Récupération des données pour l'étiquette ${etiquetteId}`);
                
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
                        console.warn(`⚠️ [BULK-PRINT] Étiquette ${etiquetteId} non trouvée`);
                        continue;
                    } else {
                        throw new Error(`Erreur HTTP ${response.status} pour l'étiquette ${etiquetteId}`);
                    }
                }

                const data = await response.json();
                
                if (data.success && data.template && data.etiquette) {
                    printData.push({
                        etiquetteId: etiquetteId,
                        template: data.template,
                        etiquette: data.etiquette,
                        commande: data.commande,
                        total_articles: data.total_articles || 0
                    });
                    console.log(`✅ [BULK-PRINT] Données récupérées pour l'étiquette ${etiquetteId} (${data.total_articles || 0} articles)`);
                } else {
                    console.warn(`⚠️ [BULK-PRINT] Données incomplètes pour l'étiquette ${etiquetteId}`);
                }

            } catch (error) {
                console.error(`❌ [BULK-PRINT] Erreur pour l'étiquette ${etiquetteId}:`, error);
                // Continuer avec les autres étiquettes
            }
        }

        return printData;
    }

    generateBulkPrintHTML(printData) {
        // Utiliser la même fonction que l'impression individuelle
        const individualPrinter = new EtiquettePrinter();
        
        let html = `
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <title>Impression Multiple - ${printData.length} Étiquettes</title>
            <style>
                @page {
                    size: A4;
                    margin: 0.5in;
                }
                
                .etiquette-page {
                    page-break-after: always;
                    min-height: 100vh;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                }
                
                .etiquette-page:last-child {
                    page-break-after: avoid;
                }
                
                @media print {
                    body { margin: 0; }
                    .etiquette-page { 
                        page-break-after: always;
                        margin: 0;
                    }
                    .etiquette-page:last-child { 
                        page-break-after: avoid; 
                    }
                }
            </style>
        </head>
        <body>
        `;

        // Générer le contenu pour chaque étiquette en utilisant la même fonction
        printData.forEach((data, index) => {
            html += `<div class="etiquette-page">`;
            html += individualPrinter.generatePrintHTML(data);
            html += `</div>`;
        });

        html += `
        </body>
        </html>
        `;

        return html;
    }


    openBulkPrintWindow(printContent) {
        const printWindow = window.open('', '_blank', 'width=800,height=600');
        
        if (!printWindow) {
            throw new Error('Impossible d\'ouvrir la fenêtre d\'impression. Vérifiez les bloqueurs de popup.');
        }

        printWindow.document.write(printContent);
        printWindow.document.close();

        // Attendre que le contenu soit chargé puis lancer l'impression
        printWindow.onload = () => {
            setTimeout(() => {
                printWindow.print();
                printWindow.close();
            }, 500);
        };
    }

    getCSRFToken() {
        const token = document.querySelector('[name=csrfmiddlewaretoken]')?.value;
        if (!token) {
            console.warn('⚠️ [BULK-PRINT] Token CSRF non trouvé');
        }
        return token || '';
    }

    showError(message) {
        console.error('❌ [BULK-PRINT]', message);
        alert(`Erreur: ${message}`);
    }
}

// Initialiser l'impression multiple quand le DOM est prêt
document.addEventListener('DOMContentLoaded', () => {
    if (document.querySelector('.etiquette-checkbox')) {
        window.bulkEtiquettePrinter = new BulkEtiquettePrinter();
        console.log('✅ [BULK-PRINT] Gestionnaire d\'impression multiple initialisé');
    }
});

// API publique
window.BulkEtiquettePrinter = BulkEtiquettePrinter;
