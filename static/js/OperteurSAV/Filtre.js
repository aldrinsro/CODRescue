/**
 * Filtre de temps personnalisable pour les vues SAV
 * Permet de filtrer les données par période avec des options prédéfinies et personnalisées
 */

class FiltreTemps {
    constructor(containerId, options = {}) {
        this.container = document.getElementById(containerId);
        this.options = {
            // Options par défaut
            presets: [
                { label: 'Aujourd\'hui', value: 'today' },
                { label: 'Hier', value: 'yesterday' },
                { label: 'Cette semaine', value: 'this_week' },
                { label: 'Semaine dernière', value: 'last_week' },
                { label: 'Ce mois', value: 'this_month' },
                { label: 'Mois dernier', value: 'last_month' },
                { label: 'Cette année', value: 'this_year' },
                { label: 'Année dernière', value: 'last_year' },
                { label: 'Personnalisé', value: 'custom' }
            ],
            defaultPreset: 'this_month',
            showTime: false,
            format: 'DD/MM/YYYY',
            onDateChange: null,
            ...options
        };
        
        this.selectedPreset = this.options.defaultPreset;
        this.customStartDate = null;
        this.customEndDate = null;
        
        this.init();
    }
    
    init() {
        this.createHTML();
        this.bindEvents();
        this.applyDefaultFilter();
    }
    
    createHTML() {
        this.container.innerHTML = `
            <div class="filtre-temps-container">
                <div class="row align-items-center">
                    <div class="col-md-4">
                        <label class="form-label">Période :</label>
                        <select class="form-select" id="preset-select">
                            ${this.options.presets.map(preset => 
                                `<option value="${preset.value}" ${preset.value === this.selectedPreset ? 'selected' : ''}>
                                    ${preset.label}
                                </option>`
                            ).join('')}
                        </select>
                    </div>
                    
                    <div class="col-md-3" id="date-start-container" style="display: none;">
                        <label class="form-label">Date début :</label>
                        <input type="date" class="form-control" id="date-start" />
                    </div>
                    
                    <div class="col-md-3" id="date-end-container" style="display: none;">
                        <label class="form-label">Date fin :</label>
                        <input type="date" class="form-control" id="date-end" />
                    </div>
                    
                    <div class="col-md-2">
                        <button type="button" class="btn btn-primary" id="apply-filter">
                            <i class="fas fa-filter"></i> Appliquer
                        </button>
                    </div>
                </div>
                
                <div class="row mt-2">
                    <div class="col-12">
                        <div class="filtre-info" id="filtre-info">
                            <span class="badge bg-info">
                                <i class="fas fa-calendar"></i> 
                                <span id="filtre-text">Chargement...</span>
                            </span>
                        </div>
                    </div>
                </div>
            </div>
        `;
    }
    
    bindEvents() {
        const presetSelect = document.getElementById('preset-select');
        const dateStart = document.getElementById('date-start');
        const dateEnd = document.getElementById('date-end');
        const applyBtn = document.getElementById('apply-filter');
        
        // Changement de preset
        presetSelect.addEventListener('change', (e) => {
            this.selectedPreset = e.target.value;
            this.toggleCustomDates();
            this.updateFiltreInfo();
        });
        
        // Changement des dates personnalisées
        dateStart.addEventListener('change', (e) => {
            this.customStartDate = e.target.value;
            this.updateFiltreInfo();
        });
        
        dateEnd.addEventListener('change', (e) => {
            this.customEndDate = e.target.value;
            this.updateFiltreInfo();
        });
        
        // Application du filtre
        applyBtn.addEventListener('click', () => {
            this.applyFilter();
        });
        
        // Application automatique lors du changement de preset (sauf personnalisé)
        presetSelect.addEventListener('change', (e) => {
            if (e.target.value !== 'custom') {
                setTimeout(() => this.applyFilter(), 100);
            }
        });
    }
    
    toggleCustomDates() {
        const startContainer = document.getElementById('date-start-container');
        const endContainer = document.getElementById('date-end-container');
        
        if (this.selectedPreset === 'custom') {
            startContainer.style.display = 'block';
            endContainer.style.display = 'block';
            
            // Initialiser les dates si pas encore définies
            if (!this.customStartDate) {
                this.customStartDate = this.formatDate(new Date(Date.now() - 30 * 24 * 60 * 60 * 1000));
                document.getElementById('date-start').value = this.customStartDate;
            }
            if (!this.customEndDate) {
                this.customEndDate = this.formatDate(new Date());
                document.getElementById('date-end').value = this.customEndDate;
            }
        } else {
            startContainer.style.display = 'none';
            endContainer.style.display = 'none';
        }
    }
    
    getDateRange() {
        const now = new Date();
        let startDate, endDate;
        
        switch (this.selectedPreset) {
            case 'today':
                startDate = new Date(now.getFullYear(), now.getMonth(), now.getDate());
                endDate = new Date(now.getFullYear(), now.getMonth(), now.getDate(), 23, 59, 59);
                break;
                
            case 'yesterday':
                const yesterday = new Date(now);
                yesterday.setDate(yesterday.getDate() - 1);
                startDate = new Date(yesterday.getFullYear(), yesterday.getMonth(), yesterday.getDate());
                endDate = new Date(yesterday.getFullYear(), yesterday.getMonth(), yesterday.getDate(), 23, 59, 59);
                break;
                
            case 'this_week':
                const startOfWeek = new Date(now);
                startOfWeek.setDate(now.getDate() - now.getDay() + 1); // Lundi
                startDate = new Date(startOfWeek.getFullYear(), startOfWeek.getMonth(), startOfWeek.getDate());
                endDate = new Date(now.getFullYear(), now.getMonth(), now.getDate(), 23, 59, 59);
                break;
                
            case 'last_week':
                const lastWeekStart = new Date(now);
                lastWeekStart.setDate(now.getDate() - now.getDay() - 6); // Lundi de la semaine dernière
                const lastWeekEnd = new Date(lastWeekStart);
                lastWeekEnd.setDate(lastWeekStart.getDate() + 6);
                startDate = new Date(lastWeekStart.getFullYear(), lastWeekStart.getMonth(), lastWeekStart.getDate());
                endDate = new Date(lastWeekEnd.getFullYear(), lastWeekEnd.getMonth(), lastWeekEnd.getDate(), 23, 59, 59);
                break;
                
            case 'this_month':
                startDate = new Date(now.getFullYear(), now.getMonth(), 1);
                endDate = new Date(now.getFullYear(), now.getMonth(), now.getDate(), 23, 59, 59);
                break;
                
            case 'last_month':
                startDate = new Date(now.getFullYear(), now.getMonth() - 1, 1);
                endDate = new Date(now.getFullYear(), now.getMonth(), 0, 23, 59, 59);
                break;
                
            case 'this_year':
                startDate = new Date(now.getFullYear(), 0, 1);
                endDate = new Date(now.getFullYear(), now.getMonth(), now.getDate(), 23, 59, 59);
                break;
                
            case 'last_year':
                startDate = new Date(now.getFullYear() - 1, 0, 1);
                endDate = new Date(now.getFullYear() - 1, 11, 31, 23, 59, 59);
                break;
                
            case 'custom':
                if (this.customStartDate && this.customEndDate) {
                    startDate = new Date(this.customStartDate);
                    endDate = new Date(this.customEndDate);
                    endDate.setHours(23, 59, 59, 999);
                } else {
                    return null;
                }
                break;
                
            default:
                return null;
        }
        
        return { startDate, endDate };
    }
    
    formatDate(date) {
        if (!date) return '';
        const d = new Date(date);
        const year = d.getFullYear();
        const month = String(d.getMonth() + 1).padStart(2, '0');
        const day = String(d.getDate()).padStart(2, '0');
        return `${year}-${month}-${day}`;
    }
    
    formatDateDisplay(date) {
        if (!date) return '';
        const d = new Date(date);
        return d.toLocaleDateString('fr-FR');
    }
    
    updateFiltreInfo() {
        const infoElement = document.getElementById('filtre-text');
        const dateRange = this.getDateRange();
        
        if (!dateRange) {
            infoElement.textContent = 'Aucune période sélectionnée';
            return;
        }
        
        const { startDate, endDate } = dateRange;
        const startStr = this.formatDateDisplay(startDate);
        const endStr = this.formatDateDisplay(endDate);
        
        if (startStr === endStr) {
            infoElement.textContent = `${startStr}`;
        } else {
            infoElement.textContent = `${startStr} - ${endStr}`;
        }
    }
    
    applyDefaultFilter() {
        this.updateFiltreInfo();
        this.applyFilter();
    }
    
    applyFilter() {
        const dateRange = this.getDateRange();
        
        if (!dateRange) {
            console.warn('Aucune période valide sélectionnée');
            return;
        }
        
        const { startDate, endDate } = dateRange;
        
        // Données du filtre
        const filterData = {
            preset: this.selectedPreset,
            startDate: startDate.toISOString(),
            endDate: endDate.toISOString(),
            startDateFormatted: this.formatDateDisplay(startDate),
            endDateFormatted: this.formatDateDisplay(endDate)
        };
        
        console.log('🔍 Filtre appliqué:', filterData);
        
        // Appeler le callback si défini
        if (this.options.onDateChange && typeof this.options.onDateChange === 'function') {
            this.options.onDateChange(filterData);
        }
        
        // Déclencher un événement personnalisé
        const event = new CustomEvent('filtreTempsChanged', {
            detail: filterData
        });
        document.dispatchEvent(event);
    }
    
    // Méthodes publiques
    setPreset(preset) {
        this.selectedPreset = preset;
        document.getElementById('preset-select').value = preset;
        this.toggleCustomDates();
        this.updateFiltreInfo();
        this.applyFilter();
    }
    
    setCustomDates(startDate, endDate) {
        this.customStartDate = this.formatDate(startDate);
        this.customEndDate = this.formatDate(endDate);
        document.getElementById('date-start').value = this.customStartDate;
        document.getElementById('date-end').value = this.customEndDate;
        this.selectedPreset = 'custom';
        document.getElementById('preset-select').value = 'custom';
        this.toggleCustomDates();
        this.updateFiltreInfo();
    }
    
    getCurrentFilter() {
        const dateRange = this.getDateRange();
        if (!dateRange) return null;
        
        return {
            preset: this.selectedPreset,
            startDate: dateRange.startDate,
            endDate: dateRange.endDate,
            startDateFormatted: this.formatDateDisplay(dateRange.startDate),
            endDateFormatted: this.formatDateDisplay(dateRange.endDate)
        };
    }
    
    reset() {
        this.selectedPreset = this.options.defaultPreset;
        document.getElementById('preset-select').value = this.selectedPreset;
        this.customStartDate = null;
        this.customEndDate = null;
        this.toggleCustomDates();
        this.updateFiltreInfo();
        this.applyFilter();
    }
}

// Fonction utilitaire pour initialiser le filtre
function initFiltreTemps(containerId, options = {}) {
    return new FiltreTemps(containerId, options);
}

// Export pour utilisation dans d'autres modules
if (typeof module !== 'undefined' && module.exports) {
    module.exports = { FiltreTemps, initFiltreTemps };
}
