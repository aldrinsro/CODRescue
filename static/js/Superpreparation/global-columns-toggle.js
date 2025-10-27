// Global column visibility controller for tables (expects a table with id "cmdTable")
// Version améliorée avec recherche, animations et meilleure UX
(function() {
  const STORAGE_KEY_PREFIX = 'yz.columns.visibility';

  function getStorageKey() {
    const tableId = 'cmdTable';
    return `${STORAGE_KEY_PREFIX}:${location.pathname}:${tableId}`;
  }

  function getTable() {
    return document.getElementById('cmdTable') || document.querySelector('table');
  }

  function readHeadings(table) {
    const ths = table?.querySelectorAll('thead th');
    if (!ths || ths.length === 0) return [];
    return Array.from(ths).map((th, idx) => ({ 
      index: idx + 1, 
      label: th.textContent.trim() || `Colonne ${idx + 1}`,
      isEssential: idx === 0 // La première colonne (N° Commande) est essentielle
    }));
  }

  function applyVisibility(table, hiddenIndices) {
    if (!table) return;
    const theadRows = table.querySelectorAll('thead tr');
    const bodyRows = table.querySelectorAll('tbody tr');

    function setCell(cell, hide) {
      if (hide) {
        cell.style.display = 'none';
      } else {
        cell.style.display = '';
      }
    }

    // thead avec animation
    theadRows.forEach(tr => {
      const cells = tr.children;
      hiddenIndices.forEach(i => {
        const cell = cells[i - 1];
        if (cell) {
          cell.style.transition = 'opacity 0.2s ease-out';
          cell.style.opacity = '0';
          setTimeout(() => setCell(cell, true), 200);
        }
      });
      // show the rest avec animation
      Array.from(cells).forEach((cell, idx) => {
        if (!hiddenIndices.includes(idx + 1)) {
          cell.style.opacity = '0';
          setCell(cell, false);
          setTimeout(() => {
            cell.style.transition = 'opacity 0.2s ease-in';
            cell.style.opacity = '1';
          }, 50);
        }
      });
    });

    // tbody
    bodyRows.forEach(tr => {
      const cells = tr.children;
      hiddenIndices.forEach(i => {
        const cell = cells[i - 1];
        if (cell) setCell(cell, true);
      });
      Array.from(cells).forEach((cell, idx) => {
        if (!hiddenIndices.includes(idx + 1)) setCell(cell, false);
      });
    });

    // Après application, ajuster la mise en page
    adjustTableAfterVisibility(table, hiddenIndices);
    
    // Afficher un message de succès
    showSuccessToast(`${hiddenIndices.length} colonne(s) masquée(s)`);
  }

  function adjustTableAfterVisibility(table, hiddenIndices) {
    try {
      table.style.tableLayout = 'auto';
      table.style.width = '100%';
      table.style.minWidth = '0px';
      table.querySelectorAll('th, td').forEach(el => { el.style.width = ''; });

      const ths = Array.from(table.querySelectorAll('thead th'));
      const hidden = new Set(hiddenIndices || []);
      const visibleIndices = ths.map((_th, idx) => idx + 1).filter(i => !hidden.has(i));
      if (visibleIndices.length > 0) {
        visibleIndices.forEach(i => {
          const head = ths[i - 1];
          if (head) { head.style.width = ''; }
        });
      }

      const container = table.closest('.table-responsive, .overflow-x-auto, .rounded-lg') || table.parentElement;
      if (container) {
        container.scrollLeft = container.scrollLeft;
        window.dispatchEvent(new Event('resize'));
        container.dispatchEvent(new Event('scroll'));
      }
    } catch (e) {
      console.warn('Erreur lors de l\'ajustement du tableau:', e);
    }
  }

  function loadHidden() {
    try {
      const raw = localStorage.getItem(getStorageKey());
      if (!raw) return [];
      const parsed = JSON.parse(raw);
      if (Array.isArray(parsed)) return parsed;
      return [];
    } catch {
      return [];
    }
  }

  function saveHidden(indices) {
    try { localStorage.setItem(getStorageKey(), JSON.stringify(indices || [])); } catch {}
  }

  function showSuccessToast(message) {
    const toast = document.createElement('div');
    toast.style.cssText = `
      position: fixed;
      top: 20px;
      right: 20px;
      background: linear-gradient(135deg, #10b981, #059669);
      color: white;
      padding: 12px 20px;
      border-radius: 8px;
      box-shadow: 0 4px 12px rgba(0,0,0,0.15);
      z-index: 10000;
      display: flex;
      align-items: center;
      gap: 8px;
      font-size: 14px;
      animation: slideInRight 0.3s ease-out;
    `;
    toast.innerHTML = `<i class="fas fa-check-circle"></i><span>${message}</span>`;
    document.body.appendChild(toast);
    
    setTimeout(() => {
      toast.style.animation = 'slideOutRight 0.3s ease-in';
      setTimeout(() => toast.remove(), 300);
    }, 2000);
  }

  function ensurePanel() {
    let panel = document.getElementById('yzColumnsPanel');
    if (panel) return panel;
    
    panel = document.createElement('div');
    panel.id = 'yzColumnsPanel';
    panel.style.cssText = `
      position: fixed;
      top: 50%;
      right: 24px;
      transform: translateY(-50%);
      z-index: 9999;
      background: #fff;
      border: 1px solid #e5e7eb;
      border-radius: 16px;
      box-shadow: 0 20px 40px rgba(0,0,0,0.15);
      width: 380px;
      max-height: 70vh;
      overflow: hidden;
      display: none;
      animation: slideInPanel 0.3s ease-out;
    `;

    panel.innerHTML = `
      <div style="padding:16px 20px; border-bottom:2px solid #e5e7eb; display:flex; align-items:center; justify-content:space-between; background: linear-gradient(135deg, #070F2B 0%, #0b183a 100%);">
        <div style="display:flex; align-items:center; gap:10px;">
          <i class="fas fa-columns" style="color:#fff; font-size:20px;"></i>
          <span style="font-weight:700; color:#fff; font-size:16px;">Gérer les colonnes</span>
        </div>
        <button id="yzColumnsClose" style="color:#fff; background:rgba(255,255,255,0.1); border:none; width:32px; height:32px; border-radius:50%; cursor:pointer; display:flex; align-items:center; justify-content:center; transition:all 0.2s;" onmouseover="this.style.background='rgba(255,255,255,0.2)'" onmouseout="this.style.background='rgba(255,255,255,0.1)'">
          <i class="fas fa-times"></i>
        </button>
      </div>
      
      <div style="padding:16px 20px; border-bottom:1px solid #e5e7eb;">
        <div style="position:relative;">
          <i class="fas fa-search" style="position:absolute; left:12px; top:50%; transform:translateY(-50%); color:#9ca3af; font-size:14px;"></i>
          <input 
            type="text" 
            id="yzColumnsSearch" 
            placeholder="Rechercher une colonne..." 
            style="width:100%; padding:10px 12px 10px 36px; border:1px solid #d1d5db; border-radius:8px; font-size:14px; transition:all 0.2s;"
            onfocus="this.style.borderColor='#070F2B'; this.style.boxShadow='0 0 0 3px rgba(7,15,43,0.1)'"
            onblur="this.style.borderColor='#d1d5db'; this.style.boxShadow='none'"
          />
        </div>
        <div style="margin-top:12px; display:flex; gap:8px; justify-content:space-between;">
          <button id="yzColumnsSelectAll" style="flex:1; padding:8px 12px; border:1px solid #070F2B; border-radius:8px; color:#070F2B; background:#fff; font-size:13px; font-weight:500; cursor:pointer; transition:all 0.2s;" onmouseover="this.style.background='#f9fafb'" onmouseout="this.style.background='#fff'">
            <i class="fas fa-check-double mr-1"></i>Tout sélectionner
          </button>
          <button id="yzColumnsDeselectAll" style="flex:1; padding:8px 12px; border:1px solid #d1d5db; border-radius:8px; color:#6b7280; background:#fff; font-size:13px; font-weight:500; cursor:pointer; transition:all 0.2s;" onmouseover="this.style.background='#f9fafb'" onmouseout="this.style.background='#fff'">
            <i class="fas fa-times-circle mr-1"></i>Tout désélectionner
          </button>
        </div>
      </div>
      
      <div id="yzColumnsBody" style="padding:12px 16px; overflow:auto; max-height:40vh;"></div>
      
      <div style="padding:16px 20px; border-top:2px solid #e5e7eb; display:flex; gap:10px; justify-content:flex-end; background:#f9fafb;">
        <button id="yzColumnsReset" style="padding:10px 16px; border:1px solid #d1d5db; border-radius:8px; color:#374151; background:#fff; font-weight:500; cursor:pointer; transition:all 0.2s;" onmouseover="this.style.background='#f3f4f6'" onmouseout="this.style.background='#fff'">
          <i class="fas fa-undo mr-2"></i>Réinitialiser
        </button>
        <button id="yzColumnsApply" style="padding:10px 20px; border:none; border-radius:8px; color:#fff; background:linear-gradient(135deg, #070F2B 0%, #0b183a 100%); font-weight:600; cursor:pointer; box-shadow:0 2px 8px rgba(7,15,43,0.2); transition:all 0.2s;" onmouseover="this.style.transform='translateY(-1px)'; this.style.boxShadow='0 4px 12px rgba(7,15,43,0.3)'" onmouseout="this.style.transform='translateY(0)'; this.style.boxShadow='0 2px 8px rgba(7,15,43,0.2)'">
          <i class="fas fa-check mr-2"></i>Appliquer
        </button>
      </div>
    `;
    
    // Ajouter les styles d'animation
    const style = document.createElement('style');
    style.textContent = `
      @keyframes slideInPanel {
        from {
          opacity: 0;
          transform: translateY(-50%) translateX(20px);
        }
        to {
          opacity: 1;
          transform: translateY(-50%) translateX(0);
        }
      }
      @keyframes slideInRight {
        from {
          opacity: 0;
          transform: translateX(100%);
        }
        to {
          opacity: 1;
          transform: translateX(0);
        }
      }
      @keyframes slideOutRight {
        from {
          opacity: 1;
          transform: translateX(0);
        }
        to {
          opacity: 0;
          transform: translateX(100%);
        }
      }
    `;
    document.head.appendChild(style);
    
    document.body.appendChild(panel);

    // Event listeners
    panel.querySelector('#yzColumnsClose').addEventListener('click', () => { 
      panel.style.animation = 'slideOutRight 0.3s ease-in';
      setTimeout(() => {
        panel.style.display = 'none';
        panel.style.animation = 'slideInPanel 0.3s ease-out';
      }, 300);
    });
    
    // Recherche en temps réel
    panel.querySelector('#yzColumnsSearch').addEventListener('input', function() {
      const searchTerm = this.value.toLowerCase();
      const items = panel.querySelectorAll('#yzColumnsBody > label');
      let visibleCount = 0;
      
      items.forEach(item => {
        const text = item.textContent.toLowerCase();
        if (text.includes(searchTerm)) {
          item.style.display = 'flex';
          visibleCount++;
        } else {
          item.style.display = 'none';
        }
      });
      
      // Afficher un message si aucun résultat
      let noResults = panel.querySelector('#noResults');
      if (visibleCount === 0) {
        if (!noResults) {
          noResults = document.createElement('div');
          noResults.id = 'noResults';
          noResults.style.cssText = 'text-align:center; padding:20px; color:#9ca3af;';
          noResults.innerHTML = '<i class="fas fa-search" style="font-size:32px; margin-bottom:8px;"></i><p>Aucune colonne trouvée</p>';
          panel.querySelector('#yzColumnsBody').appendChild(noResults);
        }
      } else if (noResults) {
        noResults.remove();
      }
    });
    
    // Tout sélectionner
    panel.querySelector('#yzColumnsSelectAll').addEventListener('click', () => {
      panel.querySelectorAll('#yzColumnsBody input[type="checkbox"]').forEach(cb => {
        if (!cb.disabled) cb.checked = true;
      });
    });
    
    // Tout désélectionner
    panel.querySelector('#yzColumnsDeselectAll').addEventListener('click', () => {
      panel.querySelectorAll('#yzColumnsBody input[type="checkbox"]').forEach(cb => {
        if (!cb.disabled && !cb.dataset.essential) cb.checked = false;
      });
    });
    
    panel.querySelector('#yzColumnsReset').addEventListener('click', () => {
      panel.querySelectorAll('input[type="checkbox"]').forEach(cb => {
        cb.checked = true;
      });
      saveHidden([]);
      const table = getTable();
      applyVisibility(table, []);
      showSuccessToast('Colonnes réinitialisées');
    });
    
    panel.querySelector('#yzColumnsApply').addEventListener('click', () => {
      const table = getTable();
      const body = panel.querySelector('#yzColumnsBody');
      const checkboxes = Array.from(body.querySelectorAll('input[type="checkbox"]'));
      const hidden = checkboxes.filter(cb => !cb.checked).map(cb => parseInt(cb.dataset.index, 10));
      saveHidden(hidden);
      applyVisibility(table, hidden);
      
      panel.style.animation = 'slideOutRight 0.3s ease-in';
      setTimeout(() => {
        panel.style.display = 'none';
        panel.style.animation = 'slideInPanel 0.3s ease-out';
      }, 300);
    });

    return panel;
  }

  function openPanel() {
    const table = getTable();
    if (!table) {
      alert('Tableau introuvable.');
      return;
    }
    
    const headings = readHeadings(table);
    const hidden = loadHidden();
    const panel = ensurePanel();
    const body = panel.querySelector('#yzColumnsBody');
    body.innerHTML = '';

    headings.forEach(({ index, label, isEssential }) => {
      const row = document.createElement('label');
      row.style.cssText = `
        display: flex;
        align-items: center;
        gap: 12px;
        padding: 10px 12px;
        border-radius: 8px;
        cursor: pointer;
        transition: all 0.2s;
        margin-bottom: 4px;
      `;
      row.onmouseover = function() {
        if (!this.querySelector('input').disabled) {
          this.style.background = '#f3f4f6';
        }
      };
      row.onmouseout = function() {
        this.style.background = '';
      };

      const cb = document.createElement('input');
      cb.type = 'checkbox';
      cb.dataset.index = String(index);
      cb.checked = !hidden.includes(index);
      cb.style.cssText = `
        width: 18px;
        height: 18px;
        cursor: pointer;
        accent-color: #070F2B;
      `;
      
      // Désactiver la première colonne (essentielle)
      if (isEssential) {
        cb.checked = true;
        cb.disabled = true;
        cb.dataset.essential = 'true';
        row.style.opacity = '0.6';
        row.style.cursor = 'not-allowed';
      }

      const span = document.createElement('span');
      span.textContent = label;
      span.style.cssText = `
        font-size: 14px;
        color: #111827;
        font-weight: 500;
        flex: 1;
      `;
      
      if (isEssential) {
        const badge = document.createElement('span');
        badge.textContent = 'Essentielle';
        badge.style.cssText = `
          font-size: 11px;
          padding: 2px 8px;
          background: #dbeafe;
          color: #1d4ed8;
          border-radius: 4px;
          font-weight: 600;
          margin-left: 8px;
        `;
        span.appendChild(badge);
      }

      row.appendChild(cb);
      row.appendChild(span);
      body.appendChild(row);
    });

    // Afficher le compteur
    const counter = document.createElement('div');
    counter.style.cssText = `
      margin-top: 12px;
      padding: 10px;
      background: #f0f9ff;
      border-radius: 8px;
      text-align: center;
      font-size: 13px;
      color: #0369a1;
      font-weight: 500;
    `;
    counter.innerHTML = `<i class="fas fa-info-circle mr-2"></i>${headings.length} colonnes au total`;
    body.appendChild(counter);

    panel.style.display = 'block';
  }

  // Public API
  window.toggleColumnVisibility = function() {
    const panel = document.getElementById('yzColumnsPanel');
    if (panel && panel.style.display === 'block') {
      panel.style.animation = 'slideOutRight 0.3s ease-in';
      setTimeout(() => {
        panel.style.display = 'none';
        panel.style.animation = 'slideInPanel 0.3s ease-out';
      }, 300);
      return;
    }
    openPanel();
  };

  // Auto-apply saved visibility on load
  document.addEventListener('DOMContentLoaded', function() {
    const table = getTable();
    if (!table) return;
    const hidden = loadHidden();
    if (hidden.length) {
      applyVisibility(table, hidden);
    } else {
      adjustTableAfterVisibility(table, []);
    }
  });
})();


