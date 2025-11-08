/**
 * Dashboard ML - Visualización de métricas y resultados
 */

document.addEventListener('DOMContentLoaded', async () => {
    await cargarMetricas();
    await cargarGraficas();
    await cargarPatrones();
});

async function cargarMetricas() {
    try {
        const response = await fetch('/api/ml/metricas_resumen');
        const data = await response.json();
        
        // KPIs
        document.getElementById('precision-predicciones').textContent = 
            (data.r2_promedio * 100).toFixed(1) + '%';
        
        document.getElementById('mejora-contexto').textContent = 
            data.mejora_contexto + '%';
        
        document.getElementById('precision-clasificador').textContent = 
            (data.precision_clasificador * 100).toFixed(1) + '%';
        
        document.getElementById('mejora-clasificador').textContent = 
            data.mejora_clasificador.toFixed(1);
        
        document.getElementById('datos-aprendidos').textContent = 
            data.total_validaciones;
        
    } catch (error) {
        console.error('[ML] Error cargando métricas:', error);
    }
}

async function cargarGraficas() {
    // 1. Predicciones vs Realidad
    await graficarPrediccionesVsRealidad();
    
    // 2. Impacto del Contexto
    await graficarImpactoContexto();
    
    // 3. Evolución Clasificador
    await graficarEvolucionClasificador();
    
    // 4. Errores por Categoría
    await graficarErroresPorCategoria();
    
    // 5. Matriz de Confusión
    await graficarMatrizConfusion();
}

async function graficarPrediccionesVsRealidad() {
    const response = await fetch('/api/ml/predicciones_vs_realidad?dias=7');
    const data = await response.json();
    
    const ctx = document.getElementById('chartPrediccionesRealidad');
    
    new Chart(ctx, {
        type: 'line',
        data: {
            labels: data.fechas,
            datasets: [
                {
                    label: 'Predicción',
                    data: data.predicciones,
                    borderColor: '#667eea',
                    backgroundColor: 'rgba(102, 126, 234, 0.1)',
                    tension: 0.4
                },
                {
                    label: 'Real',
                    data: data.reales,
                    borderColor: '#10b981',
                    backgroundColor: 'rgba(16, 185, 129, 0.1)',
                    tension: 0.4
                }
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    position: 'top',
                },
                title: {
                    display: false
                },
                tooltip: {
                    callbacks: {
                        label: function(context) {
                            return context.dataset.label + ': ' + 
                                   context.parsed.y.toFixed(0) + ' min';
                        }
                    }
                }
            },
            scales: {
                y: {
                    beginAtZero: true,
                    title: {
                        display: true,
                        text: 'Minutos'
                    }
                }
            }
        }
    });
}

async function graficarImpactoContexto() {
    const response = await fetch('/api/ml/impacto_contexto');
    const data = await response.json();
    
    const ctx = document.getElementById('chartImpactoContexto');
    
    new Chart(ctx, {
        type: 'bar',
        data: {
            labels: data.motivos,
            datasets: [{
                label: 'Factor de Ajuste',
                data: data.factores,
                backgroundColor: [
                    'rgba(102, 126, 234, 0.8)',
                    'rgba(16, 185, 129, 0.8)',
                    'rgba(245, 158, 11, 0.8)',
                    'rgba(239, 68, 68, 0.8)'
                ]
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    display: false
                }
            },
            scales: {
                y: {
                    beginAtZero: true,
                    title: {
                        display: true,
                        text: 'Factor (1.0 = sin cambio)'
                    }
                }
            }
        }
    });
}

async function graficarEvolucionClasificador() {
    const response = await fetch('/api/ml/evolucion_clasificador');
    const data = await response.json();
    
    const ctx = document.getElementById('chartEvolucionClasificador');
    
    new Chart(ctx, {
        type: 'line',
        data: {
            labels: data.fechas,
            datasets: [
                {
                    label: 'Precisión',
                    data: data.precisiones,
                    borderColor: '#667eea',
                    backgroundColor: 'rgba(102, 126, 234, 0.1)',
                    tension: 0.4,
                    yAxisID: 'y'
                },
                {
                    label: 'Ejemplos de Entrenamiento',
                    data: data.ejemplos,
                    borderColor: '#10b981',
                    backgroundColor: 'rgba(16, 185, 129, 0.1)',
                    tension: 0.4,
                    yAxisID: 'y1'
                }
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            interaction: {
                mode: 'index',
                intersect: false,
            },
            scales: {
                y: {
                    type: 'linear',
                    display: true,
                    position: 'left',
                    title: {
                        display: true,
                        text: 'Precisión (%)'
                    }
                },
                y1: {
                    type: 'linear',
                    display: true,
                    position: 'right',
                    title: {
                        display: true,
                        text: 'Ejemplos'
                    },
                    grid: {
                        drawOnChartArea: false
                    }
                }
            }
        }
    });
}

async function graficarErroresPorCategoria() {
    const response = await fetch('/api/ml/errores_por_categoria');
    const data = await response.json();
    
    const ctx = document.getElementById('chartErroresPorCategoria');
    
    new Chart(ctx, {
        type: 'bar',
        data: {
            labels: data.categorias,
            datasets: [
                {
                    label: 'MAE (min)',
                    data: data.mae,
                    backgroundColor: 'rgba(239, 68, 68, 0.8)'
                },
                {
                    label: 'RMSE (min)',
                    data: data.rmse,
                    backgroundColor: 'rgba(245, 158, 11, 0.8)'
                }
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            scales: {
                y: {
                    beginAtZero: true,
                    title: {
                        display: true,
                        text: 'Error (minutos)'
                    }
                }
            }
        }
    });
}

async function graficarMatrizConfusion() {
    const response = await fetch('/api/ml/matriz_confusion_clasificador');
    const data = await response.json();
    
    const ctx = document.getElementById('chartMatrizConfusion');
    
    // Convertir matriz a formato de chart.js
    const datasets = [];
    data.matriz.forEach((fila, i) => {
        fila.forEach((valor, j) => {
            datasets.push({
                x: data.categorias[j],
                y: data.categorias[i],
                v: valor
            });
        });
    });
    
    new Chart(ctx, {
        type: 'scatter',
        data: {
            datasets: [{
                label: 'Clasificaciones',
                data: datasets.map(d => ({x: d.x, y: d.y})),
                backgroundColor: datasets.map(d => 
                    `rgba(102, 126, 234, ${d.v / Math.max(...data.matriz.flat())})`
                ),
                pointRadius: 15
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                tooltip: {
                    callbacks: {
                        label: function(context) {
                            const d = datasets[context.dataIndex];
                            return `Predicho: ${d.x}, Real: ${d.y}, Count: ${d.v}`;
                        }
                    }
                }
            }
        }
    });
}

async function cargarPatrones() {
    try {
        const response = await fetch('/api/ml/patrones_aprendidos');
        const data = await response.json();
        
        const tbody = document.getElementById('tablaPatrones');
        
        if (!data.patrones || data.patrones.length === 0) {
            tbody.innerHTML = '<tr><td colspan="5" class="text-center">No hay patrones aprendidos aún</td></tr>';
            return;
        }
        
        tbody.innerHTML = data.patrones.map(p => `
            <tr>
                <td><strong>${p.motivo}</strong></td>
                <td><span class="badge bg-primary">${p.ocurrencias}</span></td>
                <td><span class="badge bg-${p.factor > 1 ? 'danger' : 'success'}">${p.factor.toFixed(2)}x</span></td>
                <td>
                    <div class="progress" style="height: 20px;">
                        <div class="progress-bar" role="progressbar" 
                             style="width: ${p.confianza * 100}%"
                             aria-valuenow="${p.confianza * 100}" 
                             aria-valuemin="0" aria-valuemax="100">
                            ${(p.confianza * 100).toFixed(0)}%
                        </div>
                    </div>
                </td>
                <td>${p.categoria}</td>
            </tr>
        `).join('');
        
    } catch (error) {
        console.error('[ML] Error cargando patrones:', error);
    }
}
