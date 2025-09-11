/**
 * Système d'étiquettes professionnelles avec ReportLab
 * Remplace l'ancien système JavaScript par une intégration Django moderne
 */

class EtiquettesProfessionnelles {
    constructor() {
        this.apiBaseUrl = '/commande/';
        this.selectedCommandes = new Set();
        this.selectedTemplate = null;
        this.selectedFormat = 'barcode';
        this.init();
    }

    init() {
        console.log('🚀 Initialisation du système d\'étiquettes professionnelles');
        this.setupEventListeners();
        this.loadTemplates();
    }

    setupEventListeners() {
        // Gestion de la sélection des templates
        document.addEventListener('click', (e) => {
            if (e.target.closest('.template-card')) {
                this.selectTemplate(e.target.closest('.template-card'));
            }
            
            if (e.target.closest('.format-option')) {
                this.selectFormat(e.target.closest('.format-option'));
            }
            
            if (e.target.closest('.commande-item')) {
                this.toggleCommande(e.target.closest('.commande-item'));
            }
        });

        // Boutons d'action
        const generateBtn = document.getElementById('btn-generate');
        const previewBtn = document.getElementById('btn-preview');
        
        if (generateBtn) {
            generateBtn.addEventListener('click', () => this.generateEtiquettes());
        }
        
        if (previewBtn) {
            previewBtn.addEventListener('click', () => this.previewEtiquette());
        }
    }

    async loadTemplates() {
        try {
            const response = await fetch(`${this.apiBaseUrl}api/templates/`);
            if (response.ok) {
                const templates = await response.json();
                this.renderTemplates(templates);
            }
        } catch (error) {
            console.warn('Impossible de charger les templates via API, utilisation des templates statiques');
        }
    }

    renderTemplates(templates) {
        const container = document.querySelector('.template-selector');
        if (!container) return;

        container.innerHTML = templates.map(template => `
            <div class="template-card" data-template-id="${template.id}">
                <div class="template-info">
                    <div class="template-name">${template.name}</div>
                    <div class="template-dimensions">${template.width}×${template.height}mm</div>
                </div>
                <div class="template-options">
                    ${template.show_header ? '<span class="option-badge">En-tête</span>' : ''}
                    ${template.show_footer ? '<span class="option-badge">Pied</span>' : ''}
                    ${template.show_barcode ? '<span class="option-badge">Code-barres</span>' : ''}
                    ${template.show_qr ? '<span class="option-badge">QR Code</span>' : ''}
                </div>
            </div>
        `).join('');
    }

    selectTemplate(templateCard) {
        // Désélectionner tous les autres
        document.querySelectorAll('.template-card').forEach(card => {
            card.classList.remove('selected');
        });
        
        // Sélectionner celui-ci
        templateCard.classList.add('selected');
        this.selectedTemplate = templateCard.dataset.templateId;
        
        this.updateButtons();
        this.showNotification('success', `Template sélectionné: ${templateCard.querySelector('.template-name').textContent}`);
    }

    selectFormat(formatOption) {
        document.querySelectorAll('.format-option').forEach(option => {
            option.classList.remove('selected');
        });
        
        formatOption.classList.add('selected');
        this.selectedFormat = formatOption.dataset.format;
        
        this.showNotification('info', `Format sélectionné: ${formatOption.querySelector('.format-text').textContent}`);
    }

    toggleCommande(commandeItem) {
        const checkbox = commandeItem.querySelector('.commande-checkbox');
        const commandeId = commandeItem.dataset.commandeId;
        
        checkbox.checked = !checkbox.checked;
        
        if (checkbox.checked) {
            this.selectedCommandes.add(commandeId);
            commandeItem.classList.add('selected');
        } else {
            this.selectedCommandes.delete(commandeId);
            commandeItem.classList.remove('selected');
        }
        
        this.updateStats();
        this.updateButtons();
    }

    updateStats() {
        const selectedCount = this.selectedCommandes.size;
        const totalArticles = selectedCount * 2; // Estimation: 2 articles par commande
        const estimatedPages = totalArticles; // 1 page par article
        
        document.getElementById('selected-commandes').textContent = selectedCount;
        document.getElementById('total-articles').textContent = totalArticles;
        document.getElementById('estimated-pages').textContent = estimatedPages;
    }

    updateButtons() {
        const canGenerate = this.selectedTemplate && this.selectedCommandes.size > 0;
        const generateBtn = document.getElementById('btn-generate');
        const previewBtn = document.getElementById('btn-preview');
        
        if (generateBtn) generateBtn.disabled = !canGenerate;
        if (previewBtn) previewBtn.disabled = !canGenerate;
    }

    async generateEtiquettes() {
        if (!this.selectedTemplate || this.selectedCommandes.size === 0) {
            this.showNotification('warning', 'Veuillez sélectionner un template et au moins une commande.');
            return;
        }

        this.showLoading(true);
        
        try {
            const data = {
                commande_ids: Array.from(this.selectedCommandes),
                template_id: parseInt(this.selectedTemplate),
                format: this.selectedFormat
            };

            const response = await fetch(`${this.apiBaseUrl}etiquettes/generate/`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': this.getCSRFToken()
                },
                body: JSON.stringify(data)
            });

            if (response.ok) {
                const blob = await response.blob();
                this.downloadFile(blob, `etiquettes_${new Date().toISOString().slice(0,10)}.pdf`);
                
                this.showNotification('success', 
                    `Étiquettes générées avec succès ! ${this.selectedCommandes.size} commande(s) traitée(s).`);
            } else {
                const error = await response.json();
                throw new Error(error.error || 'Erreur lors de la génération');
            }
        } catch (error) {
            console.error('Erreur génération étiquettes:', error);
            this.showNotification('error', `Erreur: ${error.message}`);
        } finally {
            this.showLoading(false);
        }
    }

    async previewEtiquette() {
        if (!this.selectedTemplate || this.selectedCommandes.size === 0) {
            this.showNotification('warning', 'Veuillez sélectionner un template et au moins une commande.');
            return;
        }

        const firstCommandeId = Array.from(this.selectedCommandes)[0];
        const previewUrl = `${this.apiBaseUrl}etiquettes/preview/${firstCommandeId}/${this.selectedTemplate}/`;
        
        window.open(previewUrl, '_blank');
        this.showNotification('info', 'Aperçu ouvert dans un nouvel onglet');
    }

    downloadFile(blob, filename) {
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = filename;
        document.body.appendChild(a);
        a.click();
        window.URL.revokeObjectURL(url);
        document.body.removeChild(a);
    }

    showLoading(show) {
        const overlay = document.getElementById('loading-overlay');
        if (overlay) {
            overlay.style.display = show ? 'flex' : 'none';
        }
    }

    showNotification(type, message) {
        // Créer une notification temporaire
        const notification = document.createElement('div');
        notification.className = `alert alert-${type} alert-dismissible fade show position-fixed`;
        notification.style.cssText = 'top: 20px; right: 20px; z-index: 9999; min-width: 300px;';
        
        notification.innerHTML = `
            ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        `;
        
        document.body.appendChild(notification);
        
        // Auto-suppression après 5 secondes
        setTimeout(() => {
            if (notification.parentNode) {
                notification.parentNode.removeChild(notification);
            }
        }, 5000);
    }

    getCSRFToken() {
        const token = document.querySelector('[name=csrfmiddlewaretoken]');
        return token ? token.value : '';
    }

    // Méthodes utilitaires pour l'intégration avec l'ancien système
    static migrateFromOldSystem() {
        console.log('🔄 Migration depuis l\'ancien système d\'étiquettes...');
        
        // Désactiver l'ancien système
        if (window.articleLabelsPrinter) {
            window.articleLabelsPrinter = null;
        }
        
        // Rediriger les appels vers le nouveau système
        window.printArticleLabels = function(articles, options) {
            console.log('⚠️ Utilisation de l\'ancienne API. Veuillez utiliser le nouveau générateur d\'étiquettes.');
            window.location.href = '/commande/etiquettes/';
        };
        
        window.printCommandeLabels = function(commandeId, clientName) {
            console.log('⚠️ Utilisation de l\'ancienne API. Veuillez utiliser le nouveau générateur d\'étiquettes.');
            window.location.href = '/commande/etiquettes/';
        };
        
        console.log('✅ Migration terminée. Redirection vers le nouveau système.');
    }
}

// Initialisation automatique
document.addEventListener('DOMContentLoaded', function() {
    // Vérifier si nous sommes sur la page du générateur d'étiquettes
    if (document.querySelector('.etiquette-generator')) {
        window.etiquettesProfessionnelles = new EtiquettesProfessionnelles();
        console.log('✅ Système d\'étiquettes professionnelles initialisé');
    }
    
    // Migration depuis l'ancien système si nécessaire
    if (window.articleLabelsPrinter) {
        EtiquettesProfessionnelles.migrateFromOldSystem();
    }
});

// Export pour utilisation externe
window.EtiquettesProfessionnelles = EtiquettesProfessionnelles;
