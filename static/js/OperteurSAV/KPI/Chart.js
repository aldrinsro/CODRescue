/**
 * Chart.js - Graphiques pour l'interface opérateur logistique
 * Histogramme des 10 villes avec le plus de livraisons
 */

document.addEventListener('DOMContentLoaded', function() {
    console.log('🚀 Chart.js initialisé');

    // Vérifier si les données des villes sont disponibles
    if (typeof villesLabels === 'undefined' || typeof villesData === 'undefined') {
        console.error('❌ Données manquantes: villesLabels ou villesData non définis');
        return;
    }

    if (!villesLabels || villesLabels.length === 0) {
        console.warn('⚠️ Aucune donnée de ville disponible');
        showNoDataMessage();
        return;
    }

    console.log('✅ Création du graphique avec', villesLabels.length, 'villes');
    createVillesChart();
});

/**
 * Affiche un message quand il n'y a pas de données
 */
function showNoDataMessage() {
    const container = document.querySelector('.chart-container');
    if (container) {
        container.innerHTML = `
            <div class="text-center py-12">
                <div class="mb-6">
                    <i class="fas fa-chart-bar text-6xl text-gray-300"></i>
                </div>
                <h4 class="text-lg font-semibold text-gray-600 mb-2">Aucune donnée disponible</h4>
                <p class="text-gray-500 text-sm">Les statistiques de livraison par ville apparaîtront ici</p>
            </div>
        `;
    }
}

/**
 * Crée l'histogramme des 10 villes avec le plus de livraisons
 */
function createVillesChart() {
    const ctx = document.getElementById('villesChart');

    if (!ctx) {
        console.error('❌ Canvas #villesChart non trouvé dans le DOM');
        return;
    }

    console.log('🎨 Création du graphique Chart.js...');

    try {
        new Chart(ctx.getContext('2d'), {
            type: 'bar',
            data: {
                labels: villesLabels,
                datasets: [{
                    label: 'Nombre de livraisons',
                    data: villesData,
                    backgroundColor: [
                        'rgba(54, 162, 235, 0.7)',
                        'rgba(75, 192, 192, 0.7)',
                        'rgba(255, 206, 86, 0.7)',
                        'rgba(153, 102, 255, 0.7)',
                        'rgba(255, 159, 64, 0.7)',
                        'rgba(255, 99, 132, 0.7)',
                        'rgba(201, 203, 207, 0.7)',
                        'rgba(83, 102, 255, 0.7)',
                        'rgba(255, 102, 178, 0.7)',
                        'rgba(102, 255, 178, 0.7)'
                    ],
                    borderColor: [
                        'rgba(54, 162, 235, 1)',
                        'rgba(75, 192, 192, 1)',
                        'rgba(255, 206, 86, 1)',
                        'rgba(153, 102, 255, 1)',
                        'rgba(255, 159, 64, 1)',
                        'rgba(255, 99, 132, 1)',
                        'rgba(201, 203, 207, 1)',
                        'rgba(83, 102, 255, 1)',
                        'rgba(255, 102, 178, 1)',
                        'rgba(102, 255, 178, 1)'
                    ],
                    borderWidth: 2,
                    borderRadius: 8,
                    borderSkipped: false,
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        display: true,
                        position: 'top',
                        labels: {
                            font: {
                                size: 13,
                                family: "'Inter', 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif",
                                weight: '500'
                            },
                            padding: 15,
                            color: '#374151'
                        }
                    },
                    title: {
                        display: false
                    },
                    tooltip: {
                        backgroundColor: 'rgba(31, 41, 55, 0.95)',
                        titleFont: {
                            size: 14,
                            weight: 'bold',
                            family: "'Inter', 'Segoe UI', sans-serif"
                        },
                        bodyFont: {
                            size: 13,
                            family: "'Inter', 'Segoe UI', sans-serif"
                        },
                        padding: 12,
                        borderColor: 'rgba(59, 130, 246, 0.5)',
                        borderWidth: 2,
                        cornerRadius: 8,
                        displayColors: true,
                        callbacks: {
                            label: function(context) {
                                const value = context.parsed.y;
                                return ' Livraisons: ' + value + (value > 1 ? ' commandes' : ' commande');
                            },
                            title: function(context) {
                                return '📍 ' + context[0].label;
                            }
                        }
                    }
                },
                scales: {
                    y: {
                        beginAtZero: true,
                        ticks: {
                            stepSize: 1,
                            font: {
                                size: 11,
                                family: "'Inter', 'Segoe UI', sans-serif"
                            },
                            color: '#6B7280',
                            callback: function(value) {
                                return Number.isInteger(value) ? value : '';
                            }
                        },
                        grid: {
                            color: 'rgba(156, 163, 175, 0.1)',
                            drawBorder: false,
                            lineWidth: 1
                        },
                        title: {
                            display: true,
                            text: 'Nombre de livraisons',
                            font: {
                                size: 12,
                                weight: '600',
                                family: "'Inter', 'Segoe UI', sans-serif"
                            },
                            color: '#374151',
                            padding: {
                                top: 10,
                                bottom: 10
                            }
                        }
                    },
                    x: {
                        ticks: {
                            font: {
                                size: 10,
                                family: "'Inter', 'Segoe UI', sans-serif"
                            },
                            color: '#6B7280',
                            maxRotation: 45,
                            minRotation: 45,
                            autoSkip: false
                        },
                        grid: {
                            display: false
                        },
                        title: {
                            display: true,
                            text: 'Villes',
                            font: {
                                size: 12,
                                weight: '600',
                                family: "'Inter', 'Segoe UI', sans-serif"
                            },
                            color: '#374151',
                            padding: {
                                top: 10,
                                bottom: 5
                            }
                        }
                    }
                },
                animation: {
                    duration: 1200,
                    easing: 'easeInOutQuart',
                    onComplete: function() {
                        console.log('✨ Graphique affiché avec succès');
                    }
                },
                interaction: {
                    intersect: false,
                    mode: 'index'
                }
            }
        });

        console.log('✅ Graphique créé avec succès');
    } catch (error) {
        console.error('❌ Erreur lors de la création du graphique:', error);
    }
}
