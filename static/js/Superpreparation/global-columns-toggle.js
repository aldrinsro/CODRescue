// Global column visibility controller for tables (expects a table with id "cmdTable")
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
    return Array.from(ths).map((th, idx) => ({ index: idx + 1, label: th.textContent.trim() || `Colonne ${idx + 1}` }));
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

    // thead
    theadRows.forEach(tr => {
      const cells = tr.children;
      hiddenIndices.forEach(i => {
        const cell = cells[i - 1];
        if (cell) setCell(cell, true);
      });
      // show the rest
      Array.from(cells).forEach((cell, idx) => {
        if (!hiddenIndices.includes(idx + 1)) setCell(cell, false);
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

    // Après application, ajuster la mise en page pour éviter les espaces blancs
    adjustTableAfterVisibility(table, hiddenIndices);
  }

  function adjustTableAfterVisibility(table, hiddenIndices) {
    try {
      // Libérer certaines contraintes puis recalculer
      table.style.tableLayout = 'auto';
      // Étendre le tableau pour occuper toute la largeur du conteneur
      table.style.width = '100%';
      table.style.minWidth = '0px';
      // Nettoyer les largeurs forcées éventuelles
      table.querySelectorAll('th, td').forEach(el => { el.style.width = ''; });

      // Si le tableau reste plus petit que le conteneur, répartir l'espace
      const ths = Array.from(table.querySelectorAll('thead th'));
      const hidden = new Set(hiddenIndices || []);
      const visibleIndices = ths.map((_th, idx) => idx + 1).filter(i => !hidden.has(i));
      if (visibleIndices.length > 0) {
        // Retirer toute largeur fixe pour laisser le navigateur répartir
        visibleIndices.forEach(i => {
          const head = ths[i - 1];
          if (head) { head.style.width = ''; }
        });
      }

      // Forcer le conteneur à rafraîchir son scroll et les ombres directionnelles
      const container = table.closest('.table-responsive, .overflow-x-auto, .rounded-lg') || table.parentElement;
      if (container) {
        // Déclencher un reflow léger
        container.scrollLeft = container.scrollLeft;
        // Relancer le calcul d'ombres directionnelles si implémenté ailleurs
        window.dispatchEvent(new Event('resize'));
        container.dispatchEvent(new Event('scroll'));
      }
    } catch (e) {
      // silencieux
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

  function ensurePanel() {
    let panel = document.getElementById('yzColumnsPanel');
    if (panel) return panel;
    panel = document.createElement('div');
    panel.id = 'yzColumnsPanel';
    panel.style.position = 'fixed';
    panel.style.top = '64px';
    panel.style.right = '24px';
    panel.style.zIndex = '9999';
    panel.style.background = '#fff';
    panel.style.border = '1px solid #e5e7eb';
    panel.style.borderRadius = '12px';
    panel.style.boxShadow = '0 10px 25px rgba(0,0,0,0.12)';
    panel.style.width = '320px';
    panel.style.maxHeight = '60vh';
    panel.style.overflow = 'hidden';
    panel.style.display = 'none';

    panel.innerHTML = `
      <div style="padding:12px 16px; border-bottom:1px solid #e5e7eb; display:flex; align-items:center; justify-content:space-between;">
        <div style="font-weight:700; color:#111827;">Colonnes du tableau</div>
        <button id="yzColumnsClose" style="color:#6b7280;">✕</button>
      </div>
      <div id="yzColumnsBody" style="padding:12px; overflow:auto; max-height:48vh;"></div>
      <div style="padding:12px; border-top:1px solid #e5e7eb; display:flex; gap:8px; justify-content:flex-end;">
        <button id="yzColumnsReset" style="padding:8px 12px; border:1px solid #d1d5db; border-radius:8px; color:#374151; background:#fff;">Réinitialiser</button>
        <button id="yzColumnsApply" style="padding:8px 12px; border-radius:8px; color:#fff; background: var(--preparation-primary);">Appliquer</button>
      </div>
    `;
    document.body.appendChild(panel);

    panel.querySelector('#yzColumnsClose').addEventListener('click', () => { panel.style.display = 'none'; });
    panel.querySelector('#yzColumnsReset').addEventListener('click', () => {
      const table = getTable();
      const headings = readHeadings(table);
      const body = panel.querySelector('#yzColumnsBody');
      body.querySelectorAll('input[type="checkbox"]').forEach((cb, idx) => {
        // By default, all shown
        cb.checked = true;
      });
    });
    panel.querySelector('#yzColumnsApply').addEventListener('click', () => {
      const table = getTable();
      const body = panel.querySelector('#yzColumnsBody');
      const checkboxes = Array.from(body.querySelectorAll('input[type="checkbox"]'));
      const hidden = checkboxes.filter(cb => !cb.checked).map(cb => parseInt(cb.dataset.index, 10));
      saveHidden(hidden);
      applyVisibility(table, hidden);
      panel.style.display = 'none';
    });

    return panel;
  }

  function openPanel() {
    const table = getTable();
    if (!table) return alert('Tableau introuvable.');
    const headings = readHeadings(table);
    const hidden = loadHidden();
    const panel = ensurePanel();
    const body = panel.querySelector('#yzColumnsBody');
    body.innerHTML = '';

    headings.forEach(({ index, label }) => {
      // Option: ne pas proposer la 1ère colonne (select) si détectée
      // Ici on laisse tout visible/configurable
      const row = document.createElement('label');
      row.style.display = 'flex';
      row.style.alignItems = 'center';
      row.style.gap = '8px';
      row.style.padding = '6px 4px';

      const cb = document.createElement('input');
      cb.type = 'checkbox';
      cb.dataset.index = String(index);
      cb.checked = !hidden.includes(index);

      const span = document.createElement('span');
      span.textContent = label;
      span.style.fontSize = '14px';
      span.style.color = '#111827';

      row.appendChild(cb);
      row.appendChild(span);
      body.appendChild(row);
    });

    panel.style.display = 'block';
  }

  // Public API
  window.toggleColumnVisibility = function() {
    const panel = document.getElementById('yzColumnsPanel');
    if (panel && panel.style.display === 'block') {
      panel.style.display = 'none';
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
      // S'assurer que la table occupe 100% au chargement
      adjustTableAfterVisibility(table, []);
    }
  });
})();


