/**
 * Script de synchronisation des statuts d'étiquettes entre les pages
 * Assure la cohérence des données entre le dashboard et la page des commandes confirmées
 */

class EtiquetteStatusSync {
    constructor() {
        this.init();
    }

    init() {
        console.log('🔄 [STATUS-SYNC] Initialisation de la synchronisation des statuts');
        
        // Écouter les événements de mise à jour de statut
        this.setupEventListeners();
        
        // Vérifier périodiquement les mises à jour
        this.startPeriodicSync();
    }

    setupEventListeners() {
        // Écouter les événements personnalisés de mise à jour de statut
        document.addEventListener('etiquetteStatusUpdated', (event) => {
            console.log('🔄 [STATUS-SYNC] Événement de mise à jour de statut reçu:', event.detail);
            this.handleStatusUpdate(event.detail);
        });

        // Écouter les événements de mise à jour des statistiques
        document.addEventListener('statisticsUpdated', (event) => {
            console.log('🔄 [STATUS-SYNC] Événement de mise à jour des statistiques reçu:', event.detail);
            this.handleStatisticsUpdate(event.detail);
        });
    }

    startPeriodicSync() {
        // Synchroniser toutes les 30 secondes
        setInterval(() => {
            this.syncStatistics();
        }, 30000);
    }

    async syncStatistics() {
        try {
            console.log('🔄 [STATUS-SYNC] Synchronisation périodique des statistiques');
            
            const response = await fetch('/etiquettes-pro/api/statistics/', {
                method: 'GET',
                headers: {
                    'X-Requested-With': 'XMLHttpRequest',
                    'Content-Type': 'application/json',
                    'X-CSRFToken': this.getCSRFToken()
                }
            });

            if (!response.ok) {
                throw new Error(`Erreur HTTP: ${response.status}`);
            }

            const data = await response.json();
            
            if (data.success) {
                // Déclencher l'événement de mise à jour des statistiques
                this.dispatchStatisticsUpdate(data.statistics);
            }
            
        } catch (error) {
            console.error('❌ [STATUS-SYNC] Erreur lors de la synchronisation:', error);
        }
    }

    handleStatusUpdate(detail) {
        const { etiquetteId, newStatus, compteurTicket, compteurQr } = detail;
        
        // Mettre à jour l'interface utilisateur
        this.updateStatusInUI(etiquetteId, newStatus, compteurTicket, compteurQr);
        
        // Mettre à jour les statistiques
        this.syncStatistics();
    }

    handleStatisticsUpdate(statistics) {
        // Mettre à jour l'interface avec les nouvelles statistiques
        this.updateStatisticsInUI(statistics);
    }

    updateStatusInUI(etiquetteId, newStatus, compteurTicket, compteurQr) {
        // Mettre à jour le statut dans le tableau du dashboard
        const statusElement = document.querySelector(`tr[data-etiquette-id="${etiquetteId}"] .etiquette-statut`);
        if (statusElement) {
            this.updateStatusElement(statusElement, newStatus);
            this.updateCountersInUI(etiquetteId, compteurTicket, compteurQr);
        }
        
        // Mettre à jour le statut dans les cartes mobiles
        const mobileStatusElement = document.querySelector(`[data-etiquette-id="${etiquetteId}"] .etiquette-statut-mobile`);
        if (mobileStatusElement) {
            this.updateStatusElement(mobileStatusElement, newStatus);
            this.updateCountersInUI(etiquetteId, compteurTicket, compteurQr);
        }
        
        // Mettre à jour le statut dans la page d'aperçu (etiquette_preview.html)
        this.updatePreviewPageStatus(etiquetteId, newStatus, compteurTicket, compteurQr);
    }

    updateStatusElement(element, newStatus) {
        // Supprimer les classes existantes
        element.className = element.className.replace(/bg-\w+-\d+|text-\w+-\d+/g, '').trim();
        
        // Ajouter la nouvelle classe selon le statut
        if (newStatus === 'printed') {
            element.classList.add('bg-blue-100', 'text-blue-800');
            element.textContent = 'Imprimée';
        } else if (newStatus === 'ready') {
            element.classList.add('bg-green-100', 'text-green-800');
            element.textContent = 'Prête';
        } else if (newStatus === 'draft') {
            element.classList.add('bg-yellow-100', 'text-yellow-800');
            element.textContent = 'Brouillon';
        }
    }

    updateCountersInUI(etiquetteId, compteurTicket, compteurQr) {
        // Mettre à jour les compteurs dans le dashboard
        const row = document.querySelector(`tr[data-etiquette-id="${etiquetteId}"]`);
        if (row) {
            this.updateCountersInRow(row, compteurTicket, compteurQr);
        }
        
        // Mettre à jour les compteurs dans les cartes
        const card = document.querySelector(`[data-etiquette-id="${etiquetteId}"]`);
        if (card) {
            this.updateCountersInCard(card, compteurTicket, compteurQr);
        }
    }

    updateCountersInRow(row, compteurTicket, compteurQr) {
        // Trouver ou créer le conteneur des compteurs
        let countersContainer = row.querySelector('.counters-container');
        if (!countersContainer) {
            const statusCell = row.querySelector('.column-statut');
            if (statusCell) {
                const statusDiv = statusCell.querySelector('div');
                if (statusDiv) {
                    countersContainer = document.createElement('div');
                    countersContainer.className = 'flex items-center gap-1 text-xs text-gray-500';
                    statusDiv.appendChild(countersContainer);
                }
            }
        }
        
        if (countersContainer) {
            this.updateCountersContainer(countersContainer, compteurTicket, compteurQr);
        }
    }

    updateCountersInCard(card, compteurTicket, compteurQr) {
        // Trouver ou créer le conteneur des compteurs dans la carte
        let countersContainer = card.querySelector('.counters-container');
        if (!countersContainer) {
            const statusContainer = card.querySelector('.flex.items-center.gap-2');
            if (statusContainer) {
                countersContainer = document.createElement('div');
                countersContainer.className = 'flex items-center gap-1';
                statusContainer.appendChild(countersContainer);
            }
        }
        
        if (countersContainer) {
            this.updateCountersContainer(countersContainer, compteurTicket, compteurQr);
        }
    }

    updateCountersContainer(container, compteurTicket, compteurQr) {
        // Vider le conteneur
        container.innerHTML = '';
        
        // Ajouter le compteur de tickets si > 0
        if (compteurTicket > 0) {
            const ticketCounter = document.createElement('span');
            ticketCounter.className = 'inline-flex items-center px-1.5 py-0.5 rounded-full text-xs font-medium bg-blue-100 text-blue-800';
            ticketCounter.title = 'Tickets imprimés';
            ticketCounter.innerHTML = `<i class="fas fa-ticket-alt mr-1"></i>${compteurTicket}`;
            container.appendChild(ticketCounter);
        }
        
        // Ajouter le compteur de QR si > 0
        if (compteurQr > 0) {
            const qrCounter = document.createElement('span');
            qrCounter.className = 'inline-flex items-center px-1.5 py-0.5 rounded-full text-xs font-medium bg-purple-100 text-purple-800';
            qrCounter.title = 'Codes QR imprimés';
            qrCounter.innerHTML = `<i class="fas fa-qrcode mr-1"></i>${compteurQr}`;
            container.appendChild(qrCounter);
        }
    }

    updatePreviewPageStatus(etiquetteId, newStatus, compteurTicket, compteurQr) {
        // Vérifier si nous sommes sur la page d'aperçu
        const isPreviewPage = document.querySelector('.etiquette-preview') !== null;
        if (!isPreviewPage) {
            return;
        }

        console.log(`🔄 [STATUS-SYNC] Mise à jour du statut sur la page d'aperçu: ${etiquetteId} -> ${newStatus}`);

        // Mettre à jour le badge de statut dans les détails de l'étiquette
        const statusBadge = document.querySelector('.info-group .status-badge');
        if (statusBadge) {
            this.updatePreviewStatusBadge(statusBadge, newStatus);
        }

        // Mettre à jour les compteurs dans la page d'aperçu
        this.updatePreviewCounters(compteurTicket, compteurQr);

        // Mettre à jour le bouton d'impression si nécessaire
        const printButton = document.querySelector('.print-btn-manual');
        if (printButton) {
            this.updatePreviewPrintButton(printButton, newStatus);
        }
    }

    updatePreviewCounters(compteurTicket, compteurQr) {
        // Trouver ou créer le conteneur des compteurs dans la page d'aperçu
        let countersContainer = document.querySelector('.info-group .flex.items-center.gap-2');
        if (countersContainer) {
            // Vider le conteneur des compteurs existants
            const existingCounters = countersContainer.querySelectorAll('.inline-flex.items-center.px-2.py-1.rounded-full');
            existingCounters.forEach(counter => counter.remove());
            
            // Ajouter le compteur de tickets si > 0
            if (compteurTicket > 0) {
                const ticketCounter = document.createElement('span');
                ticketCounter.className = 'inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-blue-100 text-blue-800';
                ticketCounter.title = 'Nombre de fois que le ticket a été imprimé';
                ticketCounter.innerHTML = `<i class="fas fa-ticket-alt mr-1"></i>${compteurTicket}`;
                countersContainer.appendChild(ticketCounter);
            }
            
            // Ajouter le compteur de QR si > 0
            if (compteurQr > 0) {
                const qrCounter = document.createElement('span');
                qrCounter.className = 'inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-purple-100 text-purple-800';
                qrCounter.title = 'Nombre de fois que les codes QR ont été imprimés';
                qrCounter.innerHTML = `<i class="fas fa-qrcode mr-1"></i>${compteurQr}`;
                countersContainer.appendChild(qrCounter);
            }
        }
    }

    updatePreviewStatusBadge(badge, newStatus) {
        // Supprimer les classes existantes
        badge.className = badge.className.replace(/confirmee|terminee|en-preparation/g, '').trim();
        
        // Ajouter la nouvelle classe selon le statut
        if (newStatus === 'printed') {
            badge.classList.add('terminee');
            badge.textContent = 'Imprimée';
        } else if (newStatus === 'ready') {
            badge.classList.add('confirmee');
            badge.textContent = 'Prête';
        } else if (newStatus === 'draft') {
            badge.classList.add('en-preparation');
            badge.textContent = 'Brouillon';
        }

        console.log(`✅ [STATUS-SYNC] Badge de statut mis à jour: ${newStatus}`);
    }

    updatePreviewPrintButton(button, newStatus) {
        if (newStatus === 'printed') {
            // Désactiver le bouton d'impression si l'étiquette est déjà imprimée
            button.disabled = true;
            button.classList.add('opacity-50', 'cursor-not-allowed');
            button.innerHTML = '<i class="fas fa-check"></i> Déjà imprimée';
            
            // Ajouter un tooltip
            button.title = 'Cette étiquette a déjà été imprimée';
            
            console.log('✅ [STATUS-SYNC] Bouton d\'impression désactivé (étiquette déjà imprimée)');
        } else {
            // Réactiver le bouton d'impression
            button.disabled = false;
            button.classList.remove('opacity-50', 'cursor-not-allowed');
            button.innerHTML = '<i class="fas fa-print"></i> Imprimer';
            button.title = '';
            
            console.log('✅ [STATUS-SYNC] Bouton d\'impression réactivé');
        }
    }

    updateStatisticsInUI(statistics) {
        // Mettre à jour les statistiques des commandes confirmées
        if (statistics.confirmed_orders) {
            const stats = statistics.confirmed_orders;
            
            // Mettre à jour le compteur total
            const totalElement = document.querySelector('#etiquettes-count');
            if (totalElement) {
                totalElement.textContent = stats.total || 0;
            }
            
            // Mettre à jour les cartes de statistiques dans le dashboard
            this.updateDashboardStats(stats);
            
            // Mettre à jour les statistiques dans la page des commandes confirmées
            this.updateCommandesConfirmesStats(stats);
        }
    }

    updateDashboardStats(stats) {
        // Mettre à jour les cartes de statistiques
        const statsCards = document.querySelectorAll('#stats-cards .group');
        statsCards.forEach(card => {
            const textElement = card.querySelector('.text-xl.sm\\:text-2xl.font-bold');
            if (textElement) {
                const cardText = card.textContent;
                if (cardText.includes('Prêtes')) {
                    textElement.textContent = stats.ready || 0;
                } else if (cardText.includes('Imprimées')) {
                    textElement.textContent = stats.printed || 0;
                } else if (cardText.includes('Total étiquettes')) {
                    textElement.textContent = stats.total || 0;
                }
            }
        });
    }

    updateCommandesConfirmesStats(stats) {
        // Mettre à jour le compteur total dans l'en-tête
        const totalElement = document.querySelector('.text-3xl.font-bold.text-white');
        if (totalElement && totalElement.textContent.includes('Total confirmées')) {
            const parentDiv = totalElement.closest('.text-center');
            if (parentDiv) {
                const numberElement = parentDiv.querySelector('.text-3xl.font-bold');
                if (numberElement) {
                    numberElement.textContent = stats.total || 0;
                }
            }
        }
        
        // Mettre à jour les cartes de statistiques
        const statsCards = document.querySelectorAll('#stats-cards .group');
        statsCards.forEach(card => {
            const textElement = card.querySelector('.text-xl.sm\\:text-2xl.font-bold');
            if (textElement) {
                const cardText = card.textContent;
                if (cardText.includes('Total Confirmées')) {
                    textElement.textContent = stats.total || 0;
                }
            }
        });
    }

    dispatchStatusUpdate(etiquetteId, newStatus) {
        const event = new CustomEvent('etiquetteStatusUpdated', {
            detail: { etiquetteId, newStatus }
        });
        document.dispatchEvent(event);
    }

    dispatchStatisticsUpdate(statistics) {
        const event = new CustomEvent('statisticsUpdated', {
            detail: statistics
        });
        document.dispatchEvent(event);
    }

    getCSRFToken() {
        const token = document.querySelector('[name=csrfmiddlewaretoken]');
        return token ? token.value : '';
    }
}

// Initialiser la synchronisation au chargement de la page
document.addEventListener('DOMContentLoaded', function() {
    window.etiquetteStatusSync = new EtiquetteStatusSync();
});

console.log('✅ [STATUS-SYNC] Module de synchronisation des statuts chargé');
