/**
 * Dashboard KPIs Yoozak - Script principal
 * Gestion des interactions et mise à jour temps réel
 */

class YoozakKPIManager {
  constructor() {
    this.version = '1.0.0';
    this.apiEndpoint = '/kpis/api/';
    this.updateInterval = 5 * 60 * 1000; // 5 minutes
    this.charts = new Map();
    this.chartsLoaded = new Set(); // Cache des graphiques déjà chargés
    this.filters = {};
    this.activeTab = 'ventes';
    this.isLoading = false;
    this.selectedPeriodVentes = '30j'; // Persistance de la période pour les KPIs Ventes
    this.selectedPeriodPerformance = '30j'; // Persistance de la période pour Performance Commerciale

    this.init();
  }

  // Fonction utilitaire pour le formatage des nombres en français
  formatNumberFR(number, decimals = 0) {
    if (typeof number !== 'number' || isNaN(number)) {
      return '0';
    }
    return number.toLocaleString('fr-FR', {
      minimumFractionDigits: decimals,
      maximumFractionDigits: decimals
    });
  }

  // Fonction utilitaire pour obtenir le libellé d'une période
  getPeriodLabel(period) {
    const periodeLabels = {
      '7j': '7 derniers jours',
      '30j': '30 derniers jours',
      '90j': '90 derniers jours',
      'mois': 'mois en cours'
    };
    return periodeLabels[period] || period;
  }

  // Fonction pour mettre à jour les textes "vs" en fonction de la période
  updateVsPeriodTexts(period) {
    const periodLabel = this.getPeriodLabel(period);
    const elements = document.querySelectorAll('[data-kpi-vs]');

    console.log(`🔄 Mise à jour des textes "vs" pour la période: ${period} (${periodLabel})`);
    console.log(`   Nombre d'éléments trouvés: ${elements.length}`);

    elements.forEach((element, index) => {
      const kpiId = element.getAttribute('data-kpi-vs');
      element.textContent = `vs ${periodLabel}`;
      console.log(`   ✅ [${index + 1}] ${kpiId}: "${element.textContent}"`);
    });

    if (elements.length === 0) {
      console.warn(`   ⚠️ Aucun élément [data-kpi-vs] trouvé dans le DOM`);
    }
  }

  init() {
    console.log('🏭 Initialisation KPI Manager Yoozak v' + this.version);
    this.bindEvents();
    this.loadInitialData();
    this.initExportButtons();
  }

  initExportButtons() {
    // Gestion des boutons d'export
    document.querySelectorAll('.export-btn').forEach(btn => {
      btn.addEventListener('click', (e) => {
        const button = e.currentTarget;
        const btnText = button.querySelector('.btn-text');
        const loadingText = button.querySelector('.loading-text');

        // Afficher l'état de chargement
        btnText.classList.add('hidden');
        loadingText.classList.remove('hidden');

        // Réactiver le bouton après le téléchargement
        setTimeout(() => {
          btnText.classList.remove('hidden');
          loadingText.classList.add('hidden');
        }, 2000);
      });
    });
  }

  updateExportUrls(period) {
    // Mettre à jour les URLs des boutons d'export avec la nouvelle période
    document.querySelectorAll('.export-btn').forEach(btn => {
      const baseUrl = btn.href.split('?')[0];
      btn.href = `${baseUrl}?period=${period}`;
    });
  }

  bindEvents() {
    // Gestion des filtres
    document.addEventListener('change', (e) => {
      if (e.target.classList.contains('kpi-filter')) {
        this.handleFilterChange(e.target);
      }
    });

    // Gestion des onglets
    document.addEventListener('click', (e) => {
      if (e.target.classList.contains('kpi-tab-button')) {
        this.switchTab(e.target.dataset.tab);
      }
    });

    // Bouton actualiser principal
    const refreshBtn = document.querySelector('[data-action="refresh"]');
    if (refreshBtn) {
      refreshBtn.addEventListener('click', () => this.refreshCurrentTab());
    }

    // Bouton actualiser dans l'en-tête KPIs
    const refreshKpisBtn = document.getElementById('refresh-kpis');
    if (refreshKpisBtn) {
      refreshKpisBtn.addEventListener('click', () => this.refreshCurrentTab());
    }
  }

  async loadInitialData() {
    console.log('📊 Chargement des données initiales...');

    // Détecter l'onglet actif au chargement de la page
    const activeTabButton = document.querySelector('.kpi-tab-button.active');
    if (activeTabButton) {
      this.activeTab = activeTabButton.dataset.tab;
      console.log('🎯 Onglet actif détecté:', this.activeTab);
    }

    // Charger les données appropriées selon l'onglet actif
    switch (this.activeTab) {
      case 'ventes':
        // CORRECTION : Les KPIs ne sont PAS chargés côté serveur !
        // Il faut toujours appeler l'API pour charger les KPIs + graphiques
        await this.loadVentesData();
        break;
      default:
        console.log('⚠️ Onglet non implémenté, chargement des données par défaut');
      // Pas de chargement par défaut, les données seront chargées lors du changement d'onglet
    }
  }

  updateKPICard(cardId, kpiData) {
    console.log(`🔄 Mise à jour KPI: ${cardId}`, kpiData);
    const card = document.querySelector(`[data-kpi="${cardId}"]`);
    if (!card) {
      console.warn(`❌ Carte KPI introuvable: ${cardId}`);
      return;
    }

    // Mettre à jour la valeur principale
    const valueElement = card.querySelector('.kpi-value');
    if (valueElement) {
      valueElement.textContent = kpiData.valeur_formatee;
      console.log(`✅ Valeur mise à jour pour ${cardId}: ${kpiData.valeur_formatee}`);
    } else {
      console.warn(`❌ Élément .kpi-value introuvable dans ${cardId}`);
    }

    // Mettre à jour la sous-valeur si présente
    const subValueElement = card.querySelector('.kpi-sub-value');
    if (subValueElement && kpiData.sub_value) {
      subValueElement.textContent = kpiData.sub_value;
      console.log(`✅ Sous-valeur mise à jour pour ${cardId}: ${kpiData.sub_value}`);
    }

    // Mettre à jour la tendance
    const trendElement = card.querySelector('.kpi-trend');
    if (trendElement) {
      if (kpiData.tendance !== undefined && kpiData.tendance !== null) {
        const trend = kpiData.tendance;
        const isPositive = trend > 0;
        const isNegative = trend < 0;

        const existingClasses = Array.from(trendElement.classList).filter(cls =>
          !cls.includes('text-') || cls.includes('text-xs')
        );

        const iconElement = trendElement.querySelector('i');
        const textElement = trendElement.querySelector('span');

        if (iconElement && textElement) {
          iconElement.className = `fas text-xs ${isPositive ? 'fa-arrow-up' : isNegative ? 'fa-arrow-down' : 'fa-minus'}`;
          textElement.textContent = isPositive ? `+${trend}` : trend;
        } else {
          trendElement.textContent = isPositive ? `+${trend}` : trend;
        }

        trendElement.className = existingClasses.join(' ') + ` ${isPositive ? 'text-green-600 bg-green-50' : isNegative ? 'text-red-600 bg-red-50' : 'text-gray-600 bg-gray-50'}`;
        console.log(`✅ Tendance mise à jour pour ${cardId}: ${trend}`);
      }
    }

    // Mettre à jour les indicateurs de statut
    if (kpiData.status) {
      card.setAttribute('data-status', kpiData.status);
      this.updateCardStatusStyle(card, kpiData.status);
    }
  }

  updateCardStatusStyle(card, status) {
    card.classList.remove('border-red-300', 'border-orange-300', 'border-green-300');

    switch (status) {
      case 'critical':
        card.classList.add('border-red-300');
        break;
      case 'warning':
        card.classList.add('border-orange-300');
        break;
      case 'good':
        card.classList.add('border-green-300');
        break;
    }
  }

  showLoadingState() {
    const loadingIndicators = document.querySelectorAll('.kpi-loading');
    loadingIndicators.forEach(indicator => {
      indicator.classList.remove('hidden');
    });

    const refreshBtn = document.querySelector('[data-action="refresh"]');
    if (refreshBtn) {
      refreshBtn.disabled = true;
      refreshBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Chargement...';
    }
  }

  hideLoadingState() {
    const loadingIndicators = document.querySelectorAll('.kpi-loading');
    loadingIndicators.forEach(indicator => {
      indicator.classList.add('hidden');
    });

    const refreshBtn = document.querySelector('[data-action="refresh"]');
    if (refreshBtn) {
      refreshBtn.disabled = false;
      refreshBtn.innerHTML = '<i class="fas fa-sync-alt"></i> Actualiser';
    }
  }

  showErrorState(message) {
    const errorContainer = document.querySelector('.kpi-error-message');
    if (errorContainer) {
      errorContainer.textContent = message;
      errorContainer.classList.remove('hidden');
    }
  }

  showChartsError(message) {
    // Afficher l'erreur dans les conteneurs de graphiques
    const evolutionContainer = document.querySelector('.evolution-ca-container');
    if (evolutionContainer) {
      evolutionContainer.innerHTML = `
        <div class="flex items-center justify-center h-48 bg-gray-50 rounded-lg">
          <div class="text-center">
            <i class="fas fa-exclamation-triangle text-yellow-500 text-2xl mb-2"></i>
            <p class="text-gray-600">${message}</p>
            <button onclick="window.yoozakKPI.retryChartsLoad()" class="mt-2 px-3 py-1 bg-blue-600 text-white rounded text-sm hover:bg-blue-700">
              Réessayer
            </button>
          </div>
        </div>
      `;
    }

    const topModelesContainer = document.querySelector('.top-modeles-container');
    if (topModelesContainer) {
      topModelesContainer.innerHTML = `
        <div class="flex items-center justify-center h-48 bg-gray-50 rounded-lg">
          <div class="text-center">
            <i class="fas fa-exclamation-triangle text-yellow-500 text-2xl mb-2"></i>
            <p class="text-gray-600">Graphique temporairement indisponible</p>
          </div>
        </div>
      `;
    }
  }

  retryChartsLoad() {
    this.loadVentesData();
  }

  updateLastUpdateTime(timestamp) {
    const updateElement = document.querySelector('.last-update-time');
    if (updateElement) {
      const date = new Date(timestamp);
      const formattedTime = date.toLocaleTimeString('fr-FR', {
        hour: '2-digit',
        minute: '2-digit'
      });
      updateElement.textContent = formattedTime;
    }
  }

  async refreshData() {
    console.log('🔄 Actualisation des données...');
    switch (this.activeTab) {
      case 'ventes':
        await this.loadVentesData();
        break;
      default:
        console.log('Onglet non encore implémenté:', this.activeTab);
    }
  }

  async refreshCurrentTab() {
    console.log('🔄 Actualisation de l\'onglet actuel:', this.activeTab);

    switch (this.activeTab) {
      case 'ventes':
        await this.loadVentesData(); // Actualisation complète
        break;
      default:
        console.log('Actualisation non disponible pour cet onglet');
    }
  }
  switchTab(tabName) {
    if (tabName === this.activeTab) {
      console.log('🔄 Onglet déjà actif:', tabName);
      return;
    }

    console.log('🔄 Changement d\'onglet vers:', tabName);
    this.activeTab = tabName;

    // Mettre à jour l'interface utilisateur
    this.updateTabUI(tabName);

    // Émettre un événement pour informer les autres composants
    const tabChangeEvent = new CustomEvent('tabChanged', {
      detail: {
        tab: tabName
      }
    });
    document.dispatchEvent(tabChangeEvent);

    // Charger les données appropriées pour le nouvel onglet
    this.loadDataForTab(tabName);
  }

  updateTabUI(activeTabName) {
    document.querySelectorAll('.kpi-tab-button').forEach(button => {
      button.classList.remove('active', 'border-blue-600', 'text-blue-600');
      button.classList.add('border-transparent', 'text-gray-500');
      button.setAttribute('aria-selected', 'false');
      button.setAttribute('tabindex', '-1');
    });

    document.querySelectorAll('.kpi-tab-panel').forEach(panel => {
      panel.classList.add('hidden');
      panel.classList.remove('active');
    });

    const activeButton = document.querySelector(`[data-tab="${activeTabName}"]`);
    if (activeButton) {
      activeButton.classList.add('active', 'border-blue-600', 'text-blue-600');
      activeButton.classList.remove('border-transparent', 'text-gray-500');
      activeButton.setAttribute('aria-selected', 'true');
      activeButton.setAttribute('tabindex', '0');
    }

    const activePanel = document.getElementById(`${activeTabName}-content`);
    if (activePanel) {
      activePanel.classList.remove('hidden');
      activePanel.classList.add('active');
    }
  }

  async loadVentesData() {
    // Cette fonction charge TOUT : KPIs + graphiques
    if (this.isLoading) return;

    this.isLoading = true;

    // Afficher un loading léger seulement sur le bouton refresh (pas sur tous les KPIs)
    const refreshBtn = document.querySelector('[data-action="refresh"]');
    if (refreshBtn) {
      refreshBtn.disabled = true;
      refreshBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Chargement...';
    }

    try {
      console.log('📊 Chargement complet des données Ventes...');

      const response = await fetch(this.apiEndpoint + `ventes/?period=${this.selectedPeriodVentes}`, {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
          'X-Requested-With': 'XMLHttpRequest'
        }
      });

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }

      const data = await response.json();

      if (data.success) {
        // Vider le cache pour forcer le rechargement des graphiques
        this.chartsLoaded.clear();

        // Mettre à jour tous les KPIs avec les nouvelles données
        this.updateVentesKPIs(data);

        // Mettre à jour les graphiques
        await Promise.all([
          this.updateVentesEvolutionCAChart(),
          this.updateTopModelesChart()
        ]);

        // Remettre en cache
        this.chartsLoaded.add('ventes-graphs');

        this.updateLastUpdateTime(data.timestamp);
        console.log('✅ Données Ventes chargées avec succès');
      } else {
        throw new Error(data.message || 'Erreur lors du chargement des données Ventes');
      }

    } catch (error) {
      console.error('❌ Erreur chargement Ventes:', error);
      this.showChartsError('Erreur lors du chargement. Veuillez actualiser.');
    } finally {
      this.isLoading = false;

      // Restaurer le bouton
      if (refreshBtn) {
        refreshBtn.disabled = false;
        refreshBtn.innerHTML = '<i class="fas fa-sync-alt"></i> Actualiser';
      }
    }
  } async loadVentesGraphsOnly() {
    console.log('📈 Chargement des graphiques Ventes uniquement...');

    try {
      // Vérifier si les graphiques sont déjà chargés pour éviter les rechargements inutiles
      const cacheKey = 'ventes-graphs';

      if (this.chartsLoaded.has(cacheKey)) {
        console.log('✅ Graphiques Ventes déjà en cache');
        return;
      }

      // Les KPIs sont déjà chargés côté serveur, on charge juste les graphiques
      await Promise.all([
        this.updateVentesEvolutionCAChart(), // API call interne
        this.updateTopModelesChart()   // API call interne
      ]);

      // Marquer comme chargé
      this.chartsLoaded.add(cacheKey);

      console.log('✅ Graphiques Ventes chargés avec succès');
    } catch (error) {
      console.error('❌ Erreur chargement graphiques Ventes:', error);
      this.showChartsError('Impossible de charger les graphiques. KPIs disponibles.');
    }
  }

  async updateVentesEvolutionCAChart(data) {
    console.log('🎨 Début de updateVentesEvolutionCAChart');
    console.log('   selectedPeriodVentes:', this.selectedPeriodVentes);

    const chartId = 'ventes-evolution-ca-chart';
    const canvasElement = document.getElementById(chartId);
    const initialLoading = document.getElementById('evolution-ca-initial-loading');
    const emptyState = document.getElementById('evolution-ca-empty');

    console.log('   Elements trouvés:', {
      canvas: !!canvasElement,
      initialLoading: !!initialLoading,
      emptyState: !!emptyState
    });

    if (!canvasElement) {
      console.error('❌ Canvas element not found');
      return;
    }

    try {
      // CORRECTION: Utiliser selectedPeriodVentes (filtre global) au lieu de selectedPeriod (filtre local)
      console.log('📞 Appel fetchEvolutionCAData...');
      const evolutionData = await this.fetchEvolutionCAData(this.selectedPeriodVentes);
      console.log('✅ fetchEvolutionCAData terminé:', evolutionData);

      // Mettre à jour l'indicateur de période
      const periodeIndicator = document.getElementById('periode-indicator');
      if (periodeIndicator) {
        periodeIndicator.textContent = `Période: ${this.getPeriodLabel(this.selectedPeriodVentes)}`;
      }

      // Vérifier s'il y a des données
      console.log('🔍 Vérification des données:', {
        hasData: !!evolutionData,
        hasValues: !!evolutionData?.values,
        valuesLength: evolutionData?.values?.length,
        allZeros: evolutionData?.values?.every(val => val === 0)
      });

      // CORRECTION: Afficher le graphique même si toutes les valeurs sont à 0
      // On affiche l'état vide seulement s'il n'y a PAS de données du tout
      if (!evolutionData || !evolutionData.values || evolutionData.values.length === 0) {
        console.warn('⚠️ Aucune donnée - Affichage de l\'état vide');
        // Afficher l'état vide
        if (initialLoading) initialLoading.classList.add('hidden');
        if (canvasElement) canvasElement.classList.add('hidden');
        if (emptyState) emptyState.classList.remove('hidden');

        // Réinitialiser les statistiques
        document.getElementById('stat-ca-total').textContent = '0 DH';
        document.getElementById('stat-ca-moyen').textContent = '0 DH';
        document.getElementById('stat-tendance').textContent = '0%';
        document.getElementById('stat-tendance').className = 'font-bold text-sm text-gray-400';

        return;
      }

      // Masquer l'état initial et l'état vide, afficher le canvas
      console.log('✅ Données valides - Affichage du graphique');
      if (initialLoading) initialLoading.classList.add('hidden');
      if (emptyState) emptyState.classList.add('hidden');
      if (canvasElement) canvasElement.classList.remove('hidden');

      // Détruire l'ancien graphique si existant
      if (this.charts.has(chartId)) {
        console.log('🗑️ Destruction de l\'ancien graphique');
        this.charts.get(chartId).destroy();
      }

      // Vérifier que Chart.js est chargé
      if (typeof Chart === 'undefined') {
        throw new Error('Chart.js n\'est pas chargé');
      }

      console.log('🎨 Création du graphique Chart.js...');
      const ctx = canvasElement.getContext('2d');
      const chart = new Chart(ctx, {
        type: 'line',
        data: {
          labels: evolutionData.labels,
          datasets: [{
            label: 'CA Journalier (DH)',
            data: evolutionData.values,
            borderColor: '#3b82f6',
            backgroundColor: 'rgba(59, 130, 246, 0.1)',
            borderWidth: 2,
            fill: true,
            tension: 0.3,
            pointBackgroundColor: '#3b82f6',
            pointBorderColor: '#ffffff',
            pointBorderWidth: 2,
            pointRadius: 4,
            pointHoverRadius: 6
          }]
        },
        options: {
          responsive: true,
          maintainAspectRatio: false,
          plugins: {
            legend: {
              display: false
            },
            tooltip: {
              backgroundColor: 'rgba(0, 0, 0, 0.8)',
              titleColor: '#ffffff',
              bodyColor: '#ffffff',
              borderColor: '#3b82f6',
              borderWidth: 1,
              cornerRadius: 6,
              displayColors: false,
              callbacks: {
                label: function (context) {
                  return `CA: ${context.parsed.y.toLocaleString('fr-FR')} DH`;
                }
              }
            }
          },
          scales: {
            x: {
              grid: {
                display: false
              },
              ticks: {
                color: '#6b7280',
                font: { size: 11 },
                // CORRECTION: Pour 7 jours, afficher TOUS les jours
                // Pour 30 jours, limiter à 10 labels
                // Pour 90 jours, limiter à 12 labels
                maxTicksLimit: evolutionData.values.length <= 7 ? 7 :
                  evolutionData.values.length <= 30 ? 10 : 12,
                autoSkip: evolutionData.values.length <= 7 ? false : true,  // Ne pas sauter de labels pour 7j
                maxRotation: 45,
                minRotation: 0
              }
            },
            y: {
              beginAtZero: true,
              grid: {
                color: 'rgba(0, 0, 0, 0.05)'
              },
              ticks: {
                color: '#6b7280',
                font: { size: 11 },
                callback: function (value) {
                  return value.toLocaleString('fr-FR') + ' DH';
                }
              }
            }
          },
          interaction: {
            intersect: false,
            mode: 'index'
          },
          animation: {
            duration: 1000,
            easing: 'easeInOutQuart'
          }
        }
      });

      this.charts.set(chartId, chart);
      console.log('✅ Graphique Evolution CA mis à jour');

      // Mettre à jour les statistiques
      this.updateEvolutionStats(evolutionData.resume);

    } catch (error) {
      console.error('❌ Erreur création graphique Evolution CA:', error);
      // En cas d'erreur, afficher l'état vide
      if (initialLoading) initialLoading.classList.add('hidden');
      if (canvasElement) canvasElement.classList.add('hidden');
      if (emptyState) {
        emptyState.classList.remove('hidden');
        emptyState.querySelector('h4').textContent = 'Erreur de chargement';
        emptyState.querySelector('p').textContent = 'Impossible de charger les données. Veuillez réessayer.';
      }
    }
  }

  // Fonction pour mettre à jour les statistiques d'évolution du CA
  updateEvolutionStats(resume) {
    if (!resume) return;

    // Formater les valeurs
    const formatNumber = (num) => {
      if (!num || num === 0) return '0 DH';
      return `${Math.round(num).toLocaleString('fr-FR')} DH`;
    };

    const formatTendance = (tendance) => {
      if (!tendance || tendance === 0) return { text: '0%', color: 'text-gray-600' };
      const signe = tendance > 0 ? '+' : '';
      const color = tendance > 0 ? 'text-green-600' : 'text-red-600';
      const icon = tendance > 0 ? '↗' : '↘';
      return { text: `${signe}${tendance.toFixed(1)}% ${icon}`, color };
    };

    // Mise à jour du DOM
    const caTotal = document.getElementById('stat-ca-total');
    const caMoyen = document.getElementById('stat-ca-moyen');
    const tendance = document.getElementById('stat-tendance');

    if (caTotal) caTotal.textContent = formatNumber(resume.ca_total);
    if (caMoyen) caMoyen.textContent = formatNumber(resume.ca_moyen);

    if (tendance) {
      const tendanceFormatee = formatTendance(resume.tendance);
      tendance.textContent = tendanceFormatee.text;
      tendance.className = `font-bold text-sm ${tendanceFormatee.color}`;
    }

    console.log('✅ Statistiques d\'évolution mises à jour:', resume);
  }

  async updateTopModelesChart(modeles = null) {
    console.log('🎨 Début de updateTopModelesChart');

    const chartId = 'repartition-sources-chart';
    let canvasElement = document.getElementById(chartId);
    const container = document.querySelector('.top-modeles-container');

    if (!container) {
      console.error('❌ Container .top-modeles-container introuvable');
      return;
    }

    console.log('✅ Container trouvé');

    if (!canvasElement) {
      console.warn('⚠️ Canvas non trouvé, création du conteneur');
      container.innerHTML = `
        <div class="flex items-center justify-between mb-4">
          <h3 class="text-lg font-semibold text-gray-900">📊 Répartition par Source</h3>
          <div class="text-xs text-gray-500">Youcan, Shopify, Autres</div>
        </div>
        <div class="relative" style="height: 300px;">
          <canvas id="${chartId}"></canvas>
          <div id="top-modeles-loading" class="absolute inset-0 bg-white bg-opacity-75 flex items-center justify-center hidden">
            <i class="fas fa-spinner fa-spin text-blue-600"></i>
          </div>
        </div>
      `;
      canvasElement = document.getElementById(chartId);

      if (!canvasElement) {
        console.error('❌ Impossible de créer le canvas pour le graphique');
        return;
      }
    } else {
      console.log('✅ Canvas trouvé:', chartId);
    }

    try {
      // Charger les données depuis la nouvelle API avec la période sélectionnée
      document.getElementById('top-modeles-loading')?.classList.remove('hidden');
      const sources = await this.fetchRepartitionSourcesData(this.selectedPeriodVentes || '30j');
      document.getElementById('top-modeles-loading')?.classList.add('hidden');

      if (!sources || sources.length === 0) {
        console.warn('⚠️ Aucune donnée de sources disponible');
        container.innerHTML = `
          <div class="flex items-center justify-between mb-4">
            <h3 class="text-lg font-semibold text-gray-900">📊 Répartition par Source</h3>
            <div class="text-xs text-gray-500">Youcan, Shopify, Autres</div>
          </div>
          <div class="h-64 bg-yellow-50 border-2 border-dashed border-yellow-200 rounded-lg flex items-center justify-center">
            <div class="text-center">
              <i class="fas fa-chart-pie text-yellow-400 text-3xl mb-3"></i>
              <h4 class="text-lg font-semibold text-yellow-900 mb-2">Aucune donnée disponible</h4>
              <p class="text-yellow-700 text-sm">Aucune commande livrée pour cette période</p>
              <p class="text-yellow-600 text-xs mt-1">La répartition apparaîtra dès qu'il y aura des livraisons</p>
            </div>
          </div>
        `;
        return;
      }

      // Valider la structure des données
      if (!Array.isArray(sources)) {
        throw new Error('Format de données invalide: sources n\'est pas un tableau');
      }

      // Vérifier que chaque source a les propriétés requises
      for (const source of sources) {
        if (!source.source || source.ca === undefined || !source.couleur) {
          throw new Error(`Données source incomplètes: ${JSON.stringify(source)}`);
        }
      }

      if (this.charts.has(chartId)) {
        console.log('🗑️ Destruction de l\'ancien graphique');
        this.charts.get(chartId).destroy();
      }

      // Vérifier que Chart.js est chargé
      if (typeof Chart === 'undefined') {
        throw new Error('Chart.js n\'est pas chargé. Veuillez inclure la bibliothèque Chart.js dans votre page.');
      }

      // Préparer les données pour le Pie Chart
      const labels = sources.map(s => s.source);
      const values = sources.map(s => s.ca);
      const backgroundColors = sources.map(s => s.couleur);

      console.log('📊 Données du graphique:', {
        labels,
        values,
        backgroundColors,
        sourceCount: sources.length
      });

      const ctx = canvasElement.getContext('2d');
      console.log('🎨 Contexte canvas obtenu:', !!ctx);

      const chart = new Chart(ctx, {
        type: 'pie',
        data: {
          labels: labels,
          datasets: [{
            data: values,
            backgroundColor: backgroundColors,
            borderColor: '#ffffff',
            borderWidth: 2
          }]
        },
        options: {
          responsive: true,
          maintainAspectRatio: false,
          plugins: {
            legend: {
              display: true,
              position: 'right',
              labels: {
                color: '#374151',
                font: { size: 11 },
                padding: 10,
                usePointStyle: true,
                pointStyle: 'circle'
              }
            },
            tooltip: {
              backgroundColor: 'rgba(0, 0, 0, 0.8)',
              titleColor: '#ffffff',
              bodyColor: '#ffffff',
              borderColor: '#3b82f6',
              borderWidth: 1,
              cornerRadius: 6,
              callbacks: {
                label: function (context) {
                  const source = sources[context.dataIndex];
                  return [
                    `${source.source}`,
                    `CA: ${source.ca_formate} DH`,
                    `Commandes: ${source.nb_commandes}`,
                    `Part: ${source.pourcentage}%`
                  ];
                }
              }
            }
          },
          animation: {
            duration: 800,
            easing: 'easeOutQuart'
          }
        }
      });

      this.charts.set(chartId, chart);
      console.log('✅ Graphique Répartition Sources créé avec succès');

    } catch (error) {
      console.error('❌ Erreur création graphique Répartition Sources:', error);
      console.error('Détails de l\'erreur:', error.message, error.stack);

      // Utiliser le container au lieu de canvasElement.parentElement pour éviter les erreurs
      if (container) {
        container.innerHTML = `
          <div class="flex items-center justify-between mb-4">
            <h3 class="text-lg font-semibold text-gray-900">📊 Répartition par Source</h3>
            <div class="text-xs text-gray-500">Erreur de chargement</div>
          </div>
          <div class="h-64 bg-red-50 border-2 border-dashed border-red-200 rounded-lg flex items-center justify-center">
            <div class="text-center">
              <i class="fas fa-exclamation-triangle text-red-400 text-3xl mb-3"></i>
              <h4 class="text-lg font-semibold text-red-900 mb-2">Erreur de chargement</h4>
              <p class="text-red-700 text-sm">${error.message || 'Erreur inconnue'}</p>
              <button onclick="window.yoozakKPI.updateTopModelesChart()" class="mt-3 px-4 py-2 bg-red-600 text-white rounded hover:bg-red-700 text-sm">
                Réessayer
              </button>
            </div>
          </div>
        `;
      }
    }
  }

  async fetchRepartitionSourcesData(period = '30j') {
    console.log(`📊 Chargement répartition sources pour période: ${period}`);

    try {
      const url = `${this.apiEndpoint}repartition-sources/?period=${period}`;
      console.log(`🔗 URL API: ${url}`);

      const response = await fetch(url, {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
          'X-Requested-With': 'XMLHttpRequest'
        }
      });

      console.log(`📡 Réponse HTTP: ${response.status} ${response.statusText}`);

      if (!response.ok) {
        const errorText = await response.text();
        console.error('❌ Réponse d\'erreur du serveur:', errorText);
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }

      const data = await response.json();
      console.log('📦 Données reçues:', data);

      if (data.success) {
        console.log(`✅ ${data.sources?.length || 0} sources trouvées`);
        return data.sources || [];
      } else {
        throw new Error(data.message || 'Erreur lors du chargement de la répartition par sources');
      }

    } catch (error) {
      console.error('❌ Erreur récupération répartition sources:', error);
      console.error('Type d\'erreur:', error.name);
      console.error('Message:', error.message);

      // Re-throw l'erreur pour qu'elle soit gérée par updateTopModelesChart
      throw error;
    }
  }

  async fetchTopModelesData(limit = 5) {
    try {
      const response = await fetch(`${this.apiEndpoint}top-modeles/?limit=${limit}&days=30`, {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
          'X-Requested-With': 'XMLHttpRequest'
        }
      });

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }

      const data = await response.json();

      if (data.success) {
        return data.modeles;
      } else {
        throw new Error(data.message || 'Erreur lors du chargement du top modèles');
      }

    } catch (error) {
      console.error('❌ Erreur récupération top modèles:', error);
      return [];
    }
  }

  async fetchEvolutionCAData(period = '30j') {
    console.log(`📈 Chargement évolution CA pour période: ${period}`);

    try {
      const url = `${this.apiEndpoint}evolution-ca/?period=${period}`;
      console.log(`🔗 URL API: ${url}`);

      const response = await fetch(url, {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
          'X-Requested-With': 'XMLHttpRequest'
        }
      });

      console.log(`📡 Réponse HTTP: ${response.status} ${response.statusText}`);

      if (!response.ok) {
        const errorText = await response.text();
        console.error('❌ Réponse d\'erreur du serveur:', errorText);
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }

      const data = await response.json();
      console.log('📦 Données évolution CA reçues:', data);

      if (data.success) {
        // Vérifier que data.evolution est un tableau
        if (!Array.isArray(data.evolution)) {
          console.error('❌ data.evolution n\'est pas un tableau:', typeof data.evolution);
          throw new Error('Format de données d\'évolution invalide');
        }

        console.log(`✅ ${data.evolution.length} jours de données trouvés`);

        // Transformer les données API en format Chart.js
        const chartData = {
          labels: data.evolution.map(item => item && item.date_formatee ? item.date_formatee : 'N/A'),
          values: data.evolution.map(item => item && typeof item.ca === 'number' ? item.ca : 0),
          raw: data.evolution,
          resume: data.resume || { ca_total: 0, ca_moyen: 0, tendance: 0 }
        };

        console.log('📊 Données chart préparées:', {
          nbLabels: chartData.labels.length,
          nbValues: chartData.values.length,
          valuesSum: chartData.values.reduce((a, b) => a + b, 0),
          resume: chartData.resume
        });

        return chartData;
      } else {
        console.error('❌ API a retourné success=false:', data.message);
        throw new Error(data.message || 'Erreur lors du chargement des données d\'évolution');
      }

    } catch (error) {
      console.error('❌ Erreur récupération données évolution CA:', error);
      console.error('Type d\'erreur:', error.name);
      console.error('Message:', error.message);

      // Retourner des données vides au lieu de données aléatoires
      return {
        labels: [],
        values: [],
        raw: [],
        resume: { ca_total: 0, ca_moyen: 0, tendance: 0 }
      };
    }
  }

  // SUPPRIMÉ: changeEvolutionPeriod() - Utilise maintenant le filtre global changePeriodeVentes()

  handleFilterChange(filterElement) {
    const filterName = filterElement.name;
    const filterValue = filterElement.value;

    this.filters[filterName] = filterValue;
    console.log('🎯 Filtre modifié:', filterName, '=', filterValue);

    this.refreshData();
  }

  async changePeriodeVentes(period) {
    console.log(`🔄 Changement période Ventes: ${period}`);

    // Persister la période sélectionnée
    this.selectedPeriodVentes = period;

    // Mise à jour visuelle des boutons
    document.querySelectorAll('.periode-ventes-btn').forEach(btn => {
      btn.classList.remove('bg-blue-600', 'text-white', 'font-medium');
      btn.classList.add('bg-gray-100', 'text-gray-600');
    });

    const activeBtn = document.querySelector(`.periode-ventes-btn[data-period="${period}"]`);
    if (activeBtn) {
      activeBtn.classList.remove('bg-gray-100', 'text-gray-600');
      activeBtn.classList.add('bg-blue-600', 'text-white', 'font-medium');
    }

    // Mettre à jour les textes "vs" pour tous les KPIs
    this.updateVsPeriodTexts(period);

    // Recharger toutes les données avec la nouvelle période
    await this.loadVentesData();
  }

  updateVentesKPIs(data) {
    console.log('🔄 Mise à jour des KPIs Ventes...', data);

    try {
      // Afficher le contenu principal et masquer le loading
      document.getElementById('ventes-loading')?.classList.add('hidden');
      document.getElementById('ventes-main-content')?.classList.remove('hidden');

      // Mettre à jour les textes "vs" IMMÉDIATEMENT après l'affichage du contenu
      this.updateVsPeriodTexts(this.selectedPeriodVentes);

      // KPIs principaux
      if (data.kpis_principaux) {
        this.updateVentesKPICard('ca_periode', data.kpis_principaux.ca_periode);
        this.updateVentesKPICard('panier_moyen', data.kpis_principaux.panier_moyen);
        this.updateVentesKPICard('nb_commandes', data.kpis_principaux.nb_commandes);
      }

      // KPIs secondaires
      if (data.kpis_secondaires) {
        // Top 3 modèles avec vérification des données
        if (data.kpis_secondaires.top_modeles_kpi && data.kpis_secondaires.top_modeles_kpi.length > 0) {
          this.updateTopModelesCard(data.kpis_secondaires.top_modeles_kpi);
        } else {
          this.showTopModelesEmpty();
        }

        // Top 3 villes avec vérification des données
        if (data.kpis_secondaires.top_villes && data.kpis_secondaires.top_villes.length > 0) {
          this.updateTopVillesCard(data.kpis_secondaires.top_villes);
        } else {
          this.showTopVillesEmpty();
        }

        // TOP 3 Commandes max avec vérification des données
        if (data.kpis_secondaires.top_commandes_max && data.kpis_secondaires.top_commandes_max.length > 0) {
          this.updateTopCommandesCard(data.kpis_secondaires.top_commandes_max);
        } else {
          this.showTopCommandesEmpty();
        }
      }

      console.log('✅ KPIs Ventes mis à jour avec succès');
    } catch (error) {
      console.error('❌ Erreur lors de la mise à jour des KPIs Ventes:', error);
    }
  }

  // Nouvelle fonction pour mettre à jour le Top 3 des modèles
  updateTopModelesCard(modeles) {
    const container = document.getElementById('top-modeles-list');
    const emptyState = document.getElementById('top-modeles-empty');

    if (!container) return;

    // Masquer l'état vide
    if (emptyState) emptyState.classList.add('hidden');

    // Couleurs et icônes pour chaque rang (similaire aux villes mais thème produit)
    const rangs = [
      { couleur: 'yellow', icon: 'fa-crown', bg: 'bg-yellow-50', text: 'text-yellow-600', border: 'border-yellow-200' },
      { couleur: 'purple', icon: 'fa-star', bg: 'bg-purple-50', text: 'text-purple-600', border: 'border-purple-200' },
      { couleur: 'orange', icon: 'fa-gem', bg: 'bg-orange-50', text: 'text-orange-600', border: 'border-orange-200' }
    ];

    // Construire le HTML
    let html = '';
    modeles.forEach((modele, index) => {
      const rang = rangs[index] || rangs[2]; // Fallback sur la 3ème couleur

      html += `
        <div class="flex items-center justify-between p-3 ${rang.bg} border ${rang.border} rounded-lg hover:shadow-sm transition-shadow">
          <div class="flex items-center gap-3 flex-1">
            <div class="flex items-center justify-center w-8 h-8 ${rang.bg} ${rang.text} rounded-full border ${rang.border}">
              <i class="fas ${rang.icon} text-xs"></i>
            </div>
            <div class="flex-1">
              <p class="font-semibold text-gray-900 text-sm" title="${modele.nom}">${modele.nom.length > 25 ? modele.nom.substring(0, 25) + '...' : modele.nom}</p>
              <p class="text-xs text-gray-500">${modele.ca_formate} • ${modele.quantite} unités</p>
            </div>
          </div>
          <div class="text-right">
            <div class="inline-flex items-center gap-1 px-2 py-1 ${rang.bg} ${rang.text} rounded-full">
              <span class="text-xs font-bold">${modele.pourcentage}%</span>
            </div>
          </div>
        </div>
      `;
    });

    container.innerHTML = html;
    console.log('✅ Top 3 modèles mis à jour:', modeles);
  }

  // Fonction pour afficher l'état vide pour les modèles
  showTopModelesEmpty() {
    const container = document.getElementById('top-modeles-list');
    const emptyState = document.getElementById('top-modeles-empty');

    if (container) container.innerHTML = '';
    if (emptyState) emptyState.classList.remove('hidden');

    console.log('⚠️ Aucune donnée de modèles disponible');
  }

  // Nouvelle fonction pour mettre à jour le Top 3 des villes
  updateTopVillesCard(villes) {
    const container = document.getElementById('top-villes-list');
    const emptyState = document.getElementById('top-villes-empty');

    if (!container) return;

    // Masquer l'état vide
    if (emptyState) emptyState.classList.add('hidden');

    // Couleurs et icônes pour chaque rang
    const rangs = [
      { couleur: 'yellow', icon: 'fa-trophy', bg: 'bg-yellow-50', text: 'text-yellow-600', border: 'border-yellow-200' },
      { couleur: 'blue', icon: 'fa-medal', bg: 'bg-blue-50', text: 'text-blue-600', border: 'border-blue-200' },
      { couleur: 'green', icon: 'fa-award', bg: 'bg-green-50', text: 'text-green-600', border: 'border-green-200' }
    ];

    // Construire le HTML
    let html = '';
    villes.forEach((ville, index) => {
      const rang = rangs[index] || rangs[2]; // Fallback sur la 3ème couleur

      html += `
        <div class="flex items-center justify-between p-3 ${rang.bg} border ${rang.border} rounded-lg hover:shadow-sm transition-shadow">
          <div class="flex items-center gap-3 flex-1">
            <div class="flex items-center justify-center w-8 h-8 ${rang.bg} ${rang.text} rounded-full border ${rang.border}">
              <i class="fas ${rang.icon} text-xs"></i>
            </div>
            <div class="flex-1">
              <p class="font-semibold text-gray-900 text-sm">${ville.nom}</p>
              <p class="text-xs text-gray-500">${ville.ca_formate}</p>
            </div>
          </div>
          <div class="text-right">
            <div class="inline-flex items-center gap-1 px-2 py-1 ${rang.bg} ${rang.text} rounded-full">
              <span class="text-xs font-bold">${ville.pourcentage}%</span>
            </div>
          </div>
        </div>
      `;
    });

    container.innerHTML = html;
    console.log('✅ Top 3 villes mis à jour:', villes);
  }

  // Fonction pour afficher l'état vide pour les villes
  showTopVillesEmpty() {
    const container = document.getElementById('top-villes-list');
    const emptyState = document.getElementById('top-villes-empty');

    if (container) container.innerHTML = '';
    if (emptyState) emptyState.classList.remove('hidden');

    console.log('⚠️ Aucune donnée de villes disponible');
  }

  // Nouvelle fonction pour mettre à jour le TOP 3 des commandes
  updateTopCommandesCard(commandes) {
    const container = document.getElementById('top-commandes-list');
    const emptyState = document.getElementById('top-commandes-empty');

    if (!container) return;

    // Masquer l'état vide
    if (emptyState) emptyState.classList.add('hidden');

    // Couleurs et icônes pour chaque rang (thème trophée)
    const rangs = [
      { couleur: 'orange', icon: 'fa-trophy', bg: 'bg-orange-50', text: 'text-orange-600', border: 'border-orange-200' },
      { couleur: 'yellow', icon: 'fa-medal', bg: 'bg-yellow-50', text: 'text-yellow-600', border: 'border-yellow-200' },
      { couleur: 'gray', icon: 'fa-award', bg: 'bg-gray-50', text: 'text-gray-600', border: 'border-gray-200' }
    ];

    // Construire le HTML
    let html = '';
    commandes.forEach((commande, index) => {
      const rang = rangs[index] || rangs[2]; // Fallback sur la 3ème couleur

      html += `
        <div class="flex items-center justify-between p-3 ${rang.bg} border ${rang.border} rounded-lg hover:shadow-sm transition-shadow">
          <div class="flex items-center gap-3 flex-1">
            <div class="flex items-center justify-center w-8 h-8 ${rang.bg} ${rang.text} rounded-full border ${rang.border}">
              <i class="fas ${rang.icon} text-xs"></i>
            </div>
            <div class="flex-1">
              <p class="font-semibold text-gray-900 text-sm">Nº${commande.id_yz || 'N/A'}</p>
              <p class="text-xs text-gray-500">${commande.client} • ${commande.date}</p>
            </div>
          </div>
          <div class="text-right">
            <div class="font-bold ${rang.text} text-sm">${commande.montant_formate} DH</div>
          </div>
        </div>
      `;
    });

    container.innerHTML = html;
    console.log('✅ TOP 3 commandes mis à jour:', commandes);
  }

  // Fonction pour afficher l'état vide pour les commandes
  showTopCommandesEmpty() {
    const container = document.getElementById('top-commandes-list');
    const emptyState = document.getElementById('top-commandes-empty');

    if (container) container.innerHTML = '';
    if (emptyState) emptyState.classList.remove('hidden');

    console.log('⚠️ Aucune donnée de commandes disponible');
  }

  // Nouvelle fonction pour mettre à jour les KPIs avec la structure des cartes Ventes
  updateVentesKPICard(kpiId, kpiData) {
    console.log(`🔄 Mise à jour KPI Ventes: ${kpiId}`, kpiData);

    // Vérifier que les données KPI sont valides
    if (!kpiData) {
      console.warn(`❌ Données KPI manquantes pour ${kpiId}`);
      return;
    }

    // Mettre à jour la valeur principale
    const valueElement = document.querySelector(`[data-kpi="${kpiId}"]`);
    if (valueElement) {
      // Pour tous les KPIs, afficher la valeur formatée
      valueElement.textContent = kpiData.valeur_formatee || kpiData.valeur || '-';
      console.log(`✅ Valeur mise à jour pour ${kpiId}: ${valueElement.textContent}`);
    } else {
      console.warn(`❌ Élément [data-kpi="${kpiId}"] introuvable`);
    }

    // Mettre à jour l'unité
    const uniteElement = document.querySelector(`[data-kpi-unite="${kpiId}"]`);
    if (uniteElement && kpiData.unite) {
      uniteElement.textContent = kpiData.unite;
    }

    // Mettre à jour la sous-valeur
    const subValueElement = document.querySelector(`[data-kpi-sub="${kpiId}"]`);
    if (subValueElement && kpiData.sub_value) {
      subValueElement.textContent = kpiData.sub_value;
    }

    // Mettre à jour la tendance
    const trendElement = document.querySelector(`[data-kpi-trend="${kpiId}"]`);
    if (trendElement && kpiData.tendance !== undefined && kpiData.tendance !== null) {
      const trend = parseFloat(kpiData.tendance);
      const isPositive = trend > 0;
      const isNegative = trend < 0;

      // Mettre à jour l'icône
      const iconElement = trendElement.querySelector('i');
      if (iconElement) {
        iconElement.className = `fas ${isPositive ? 'fa-arrow-up text-green-600' : isNegative ? 'fa-arrow-down text-red-600' : 'fa-minus text-gray-600'}`;
      }

      // Mettre à jour le texte de la tendance
      const spanElement = trendElement.querySelector('span');
      if (spanElement) {
        spanElement.textContent = isPositive ? `+${trend}%` : `${trend}%`;
        spanElement.className = isPositive ? 'text-green-600' : isNegative ? 'text-red-600' : 'text-gray-600';
      }
    }
  }

  // ===== MÉTHODES CLIENTS =====
  async loadClientsData() {
    console.log('👥 Chargement des données Clients...');

    try {
      this.showClientsLoading();

      // Ajouter un timeout pour éviter les blocages
      const controller = new AbortController();
      const timeoutId = setTimeout(() => controller.abort(), 15000); // 15 secondes max

      const response = await fetch(this.apiEndpoint + 'clients/', {
        signal: controller.signal,
        headers: {
          'X-Requested-With': 'XMLHttpRequest'
        }
      });

      clearTimeout(timeoutId); // Annuler le timeout si la requête réussit

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }

      const data = await response.json();

      if (!data.success) {
        throw new Error(data.message || 'Erreur API');
      }

      // Vérifier si les données sont vides
      if (data.empty) {
        this.showClientsEmpty();
        return;
      }

      // Mettre à jour l'interface avec les données
      this.updateClientsKPIs(data);
      this.updateClientsAnalyses(data);
      this.showClientsContent();

      console.log('✅ Données Clients chargées avec succès');

    } catch (error) {
      console.error('❌ Erreur chargement Clients:', error);

      // Gestion spécifique des erreurs de timeout
      if (error.name === 'AbortError') {
        this.showErrorState('clients', 'Le chargement des données clients a pris trop de temps. Veuillez réessayer.');
      } else {
        this.showErrorState('clients', 'Erreur lors du chargement des données clients');
      }

      // Afficher l'état vide pour éviter une interface bloquée
      this.showClientsEmpty();
    }
  }

  updateClientsKPIs(data) {
    console.log('🔄 Mise à jour des KPIs Clients...', data);

    try {
      // KPIs principaux
      if (data.kpis_principaux) {
        // Nouveaux Clients
        const nouveauxClients = data.kpis_principaux.nouveaux_clients;
        this.updateElement('[data-kpi="nouveaux_clients"]', nouveauxClients.valeur_formatee);
        this.updateElement('[data-kpi-unite="nouveaux_clients"]', nouveauxClients.unite);
        this.updateElement('[data-kpi-sub="nouveaux_clients"]', nouveauxClients.sub_value);
        this.updateTrend('[data-kpi-trend="nouveaux_clients"]', nouveauxClients.tendance);

        // Clients Actifs
        const clientsActifs = data.kpis_principaux.clients_actifs;
        this.updateElement('[data-kpi="clients_actifs"]', clientsActifs.valeur_formatee);
        this.updateElement('[data-kpi-unite="clients_actifs"]', clientsActifs.unite);
        this.updateElement('[data-kpi-sub="clients_actifs"]', clientsActifs.sub_value);
        this.updateTrend('[data-kpi-trend="clients_actifs"]', clientsActifs.tendance);

        // Taux Retour
        const tauxRetour = data.kpis_principaux.taux_retour;
        this.updateElement('[data-kpi="taux_retour"]', tauxRetour.valeur_formatee);
        this.updateElement('[data-kpi-unite="taux_retour"]', tauxRetour.unite);
        this.updateElement('[data-kpi-sub="taux_retour"]', tauxRetour.sub_value);
        this.updateTrend('[data-kpi-trend="taux_retour"]', tauxRetour.tendance, true); // Inverse pour retours

        // Satisfaction
        const satisfaction = data.kpis_principaux.satisfaction;
        this.updateElement('[data-kpi="satisfaction"]', satisfaction.valeur_formatee);
        this.updateElement('[data-kpi-unite="satisfaction"]', satisfaction.unite);
        this.updateElement('[data-kpi-sub="satisfaction"]', satisfaction.sub_value);
        this.updateTrend('[data-kpi-trend="satisfaction"]', satisfaction.tendance);
      }

      console.log('✅ KPIs Clients mis à jour avec succès');
    } catch (error) {
      console.error('❌ Erreur mise à jour KPIs Clients:', error);
    }
  }

  updateClientsAnalyses(data) {
    console.log('🔄 Mise à jour analyses Clients...', data);

    try {
      // Top Clients VIP
      if (data.analyses_detaillees && data.analyses_detaillees.top_clients_vip) {
        const topClientsList = document.getElementById('top-clients-list');
        const topClientsEmpty = document.getElementById('top-clients-empty');

        if (data.analyses_detaillees.top_clients_vip.length > 0) {
          topClientsList.innerHTML = '';
          topClientsEmpty.style.display = 'none';

          data.analyses_detaillees.top_clients_vip.forEach((client, index) => {
            const colors = ['yellow', 'blue', 'green', 'purple', 'indigo'];
            const color = colors[index % colors.length];

            const clientDiv = document.createElement('div');
            clientDiv.className = 'flex items-center justify-between p-3 bg-gray-50 rounded-lg';
            clientDiv.innerHTML = `
              <div class="flex items-center gap-3">
                <div class="w-8 h-8 bg-${color}-100 text-${color}-600 rounded-full flex items-center justify-center text-sm font-bold">
                  ${index + 1}
                </div>
                <span class="font-medium">${client.nom}</span>
              </div>
              <div class="text-right">
                <div class="font-bold text-${color}-600">${client.ca_total_format}</div>
                <div class="text-xs text-gray-500">${client.nb_commandes} commandes</div>
              </div>
            `;
            topClientsList.appendChild(clientDiv);
          });
        } else {
          topClientsList.innerHTML = '';
          topClientsEmpty.style.display = 'block';
        }
      }      // Performance mensuelle
      if (data.analyses_detaillees && data.analyses_detaillees.performance_mensuelle) {
        const perf = data.analyses_detaillees.performance_mensuelle;
        this.updateElement('[data-perf="commandes_mois"]', `${perf.commandes_mois} commandes`);
        this.updateElement('[data-perf="ca_par_client"]', `${this.formatNumberFR(perf.ca_par_client, 2)} DH`);
      }

      // Statistiques globales
      if (data.stats_globales) {
        this.updateElement('[data-stats="total_clients"]', this.formatNumberFR(data.stats_globales.total_clients));
        this.updateElement('[data-stats="taux_activite"]', `${data.stats_globales.taux_activite}%`);
        this.updateElement('[data-stats="panier_moyen_clients"]', `${this.formatNumberFR(data.stats_globales.panier_moyen_clients, 2)} DH`);
      }

      console.log('✅ Analyses Clients mises à jour avec succès');
    } catch (error) {
      console.error('❌ Erreur mise à jour analyses Clients:', error);
    }
  }

  // Méthodes utilitaires pour les états d'affichage
  showLoadingState(section) {
    const loading = document.getElementById(`${section}-loading`);
    const content = document.getElementById(`${section}-content`);
    const emptyState = document.getElementById(`${section}-empty-state`);

    if (loading) loading.style.display = 'block';
    if (content) content.style.display = 'none';
    if (emptyState) emptyState.style.display = 'none';
  }

  showContentState(section) {
    const loading = document.getElementById(`${section}-loading`);
    const content = document.getElementById(`${section}-content`);
    const emptyState = document.getElementById(`${section}-empty-state`);

    if (loading) loading.style.display = 'none';
    if (content) content.style.display = 'block';
    if (emptyState) emptyState.style.display = 'none';
  }

  showEmptyState(section) {
    const loading = document.getElementById(`${section}-loading`);
    const content = document.getElementById(`${section}-content`);
    const emptyState = document.getElementById(`${section}-empty-state`);

    if (loading) loading.style.display = 'none';
    if (content) content.style.display = 'none';
    if (emptyState) emptyState.style.display = 'block';
  }

  showErrorState(section, message) {
    console.error(`Erreur section ${section}:`, message);
    // Pour le moment, on affiche l'état vide en cas d'erreur
    this.showEmptyState(section);
  }

  updateElement(selector, value) {
    const element = document.querySelector(selector);
    if (element) {
      element.textContent = value;
    }
  }

  updateTrend(selector, value, inverse = false) {
    const element = document.querySelector(selector);
    if (element) {
      const icon = element.querySelector('i');
      const span = element.querySelector('span');

      if (icon && span) {
        // Déterminer la direction (inverse pour taux de retour où baisse = bien)
        const isPositive = inverse ? value < 0 : value > 0;
        const isNegative = inverse ? value > 0 : value < 0;

        // Mettre à jour l'icône
        icon.className = isPositive ? 'fas fa-arrow-up text-green-600' :
          isNegative ? 'fas fa-arrow-down text-red-600' :
            'fas fa-minus text-gray-400';

        // Mettre à jour la valeur
        span.textContent = Math.abs(value);
        span.className = isPositive ? 'text-green-600' :
          isNegative ? 'text-red-600' :
            'text-gray-400';
      }
    }
  }

  // Fonctions spécialisées pour l'affichage des clients (évite conflit d'ID)
  showClientsLoading() {
    const loading = document.getElementById('clients-loading');
    const content = document.getElementById('clients-main-content');
    const emptyState = document.getElementById('clients-empty-state');

    if (loading) loading.style.display = 'block';
    if (content) content.style.display = 'none';
    if (emptyState) emptyState.style.display = 'none';
  }

  showClientsEmpty() {
    const loading = document.getElementById('clients-loading');
    const content = document.getElementById('clients-main-content');
    const emptyState = document.getElementById('clients-empty-state');

    if (loading) loading.style.display = 'none';
    if (content) content.style.display = 'none';
    if (emptyState) emptyState.style.display = 'block';
  }

  // Fonction spécialisée pour l'affichage des clients (évite conflit d'ID)
  showClientsContent() {
    const loading = document.getElementById('clients-loading');
    const content = document.getElementById('clients-main-content');
    const emptyState = document.getElementById('clients-empty-state');

    if (loading) loading.style.display = 'none';
    if (content) content.style.display = 'block';
    if (emptyState) emptyState.style.display = 'none';

    // Initialiser les graphiques clients une fois que le contenu est visible
    if (window.kpiCharts) {
      // Utiliser setTimeout pour s'assurer que le DOM est bien mis à jour avant de créer les graphiques
      setTimeout(() => {
        window.kpiCharts.loadClientCharts();
      }, 100);
    }
  }

  loadDataForTab(tabName) {
    switch (tabName) {
      case 'ventes':
        // Lors du changement d'onglet vers Ventes, charger TOUTES les données
        console.log('📊 Chargement de l\'onglet Ventes...');
        this.loadVentesData(); // Charge KPIs + graphiques
        break;
      case 'clients':
        this.loadClientsData();
        break;
      case 'performance-commerciale':
        this.loadPerformanceCommercialeData();
        break;
      default:
        console.log('Onglet non encore implémenté:', tabName);
    }
  }

  // ===== MÉTHODES PERFORMANCE COMMERCIALE =====
  async changePeriodePerformance(period) {
    console.log(`🔄 Changement période Performance Commerciale: ${period}`);

    // Persister la période sélectionnée
    this.selectedPeriodPerformance = period;

    // Mise à jour visuelle des boutons
    document.querySelectorAll('.periode-perf-btn').forEach(btn => {
      btn.classList.remove('bg-blue-600', 'text-white', 'font-medium');
      btn.classList.add('bg-gray-100', 'text-gray-600');
    });

    const activeBtn = document.querySelector(`.periode-perf-btn[data-period="${period}"]`);
    if (activeBtn) {
      activeBtn.classList.remove('bg-gray-100', 'text-gray-600');
      activeBtn.classList.add('bg-blue-600', 'text-white', 'font-medium');
    }

    // Mettre à jour les textes "vs" pour tous les KPIs de performance
    this.updateVsPeriodTextsPerformance(period);

    // Recharger toutes les données avec la nouvelle période
    await this.loadPerformanceCommercialeData();
  }

  updateVsPeriodTextsPerformance(period) {
    const periodLabel = this.getPeriodLabel(period);
    const elements = document.querySelectorAll('#performance-commerciale-content [data-kpi-vs]');

    console.log(`🔄 Mise à jour des textes "vs" Performance pour la période: ${period} (${periodLabel})`);
    console.log(`   Nombre d'éléments trouvés: ${elements.length}`);

    elements.forEach((element, index) => {
      const kpiId = element.getAttribute('data-kpi-vs');
      element.textContent = `vs ${periodLabel}`;
      console.log(`   ✅ [${index + 1}] ${kpiId}: "${element.textContent}"`);
    });

    if (elements.length === 0) {
      console.warn(`   ⚠️ Aucun élément [data-kpi-vs] trouvé dans Performance Commerciale`);
    }
  }

  async loadPerformanceCommercialeData() {
    console.log('📊 Chargement des données Performance Commerciale...');

    // Afficher le loading
    const loading = document.getElementById('performance-loading');
    const content = document.getElementById('performance-main-content');
    const emptyState = document.getElementById('performance-empty-state');

    if (loading) loading.classList.remove('hidden');
    if (content) content.classList.add('hidden');
    if (emptyState) emptyState.classList.add('hidden');

    try {
      // TODO: Remplacer par un vrai appel API
      // const response = await fetch(this.apiEndpoint + `performance-commerciale/?period=${this.selectedPeriodPerformance || '30j'}`);
      // const data = await response.json();

      // Pour l'instant, simuler des données
      setTimeout(() => {
        // Masquer loading, afficher contenu
        if (loading) loading.classList.add('hidden');
        if (content) content.classList.remove('hidden');

        // Mettre à jour les textes "vs"
        this.updateVsPeriodTextsPerformance(this.selectedPeriodPerformance || '30j');

        console.log('✅ Données Performance Commerciale chargées (simulation)');
      }, 500);

    } catch (error) {
      console.error('❌ Erreur chargement Performance Commerciale:', error);
      if (loading) loading.classList.add('hidden');
      if (emptyState) emptyState.classList.remove('hidden');
    }
  }
}

// Initialisation au chargement du DOM
document.addEventListener('DOMContentLoaded', () => {
  window.kpiManager = new YoozakKPIManager();
  window.yoozakKPI = window.kpiManager; // Alias pour compatibilité avec le HTML généré
  window.kpiCharts = new KPICharts();

  // Vérification de l'attachement pour debug
  console.log('🔗 window.yoozakKPI attaché:', !!window.yoozakKPI);
  console.log('🔗 changeEvolutionPeriod disponible:', typeof window.yoozakKPI.changeEvolutionPeriod);
  console.log('🔗 changePeriodeVentes disponible:', typeof window.yoozakKPI.changePeriodeVentes);
});

// Export pour utilisation dans d'autres modules
if (typeof module !== 'undefined' && module.exports) {
  module.exports = YoozakKPIManager;
}
