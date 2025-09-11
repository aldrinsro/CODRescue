// Colonnes (global) – conforme README_RESPONSIVE_COLUMNS.md avec logs de diagnostic
(function(){
  try {
    console.log('[columns-toggle] Initialisation du module...');
    const STORAGE_KEY = 'hiddenColumns_confirmees';
    const COLUMNS = ['column-select','column-idyz','column-numext','column-client','column-phone','column-ville','column-total','column-dateconf','column-operateur','column-etat','column-actions'];

    function getHidden(){
      try { const v = JSON.parse(localStorage.getItem(STORAGE_KEY) || '[]'); console.log('[columns-toggle] hiddenColumns chargés:', v); return v; } catch(e){ console.warn('[columns-toggle] JSON parse error storage:', e); return []; }
    }
    function setHidden(list){
      try { localStorage.setItem(STORAGE_KEY, JSON.stringify(list||[])); console.log('[columns-toggle] hiddenColumns sauvegardés:', list); } catch(e){ console.warn('[columns-toggle] localStorage set error:', e); }
    }

    function applyVisibility(hidden){
      try {
        console.log('[columns-toggle] applyVisibility → hidden:', hidden);
        COLUMNS.forEach(col => {
          const nodes = document.querySelectorAll('.'+col);
          if (nodes && nodes.length) {
            nodes.forEach(el => { el.style.display = (hidden.includes(col) ? 'none' : ''); });
          }
        });
      } catch(err) {
        console.error('[columns-toggle] applyVisibility error:', err);
      }
    }

    // Expose global API (avec logs)
    window.updateColumnVisibility = function(hidden){ console.log('[columns-toggle] updateColumnVisibility called'); applyVisibility(hidden || []); };

    window.toggleColumnVisibility = function(){
      try {
        console.log('[columns-toggle] toggleColumnVisibility() appelé');
        const hidden = new Set(getHidden());
        const modal = document.createElement('div');
        modal.className = 'fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50';
        const items = [
          ['column-idyz','ID YZ'],['column-numext','N° Externe'],['column-client','Client'],['column-phone','Téléphone'],
          ['column-ville','Ville & Région'],['column-total','Total'],['column-dateconf','Date Confirmation'],['column-operateur','Opérateur'],
          ['column-etat','État Préparation'],['column-actions','Actions']
        ];
        const checks = items.map(([c,l]) => `<label class="flex items-center"><input type="checkbox" class="column-checkbox" data-column="${c}" ${hidden.has(c)?'':'checked'}><span class="ml-2 text-sm text-gray-700">${l}</span></label>`).join('');
        modal.innerHTML = `
          <div class="bg-white rounded-lg p-6 max-w-md w-full mx-4">
            <div class="flex items-center justify-between mb-4">
              <h3 class="text-lg font-semibold text-gray-900">Sélectionner les colonnes</h3>
              <button class="text-gray-400 hover:text-gray-600" onclick="this.closest('.fixed').remove()"><i class="fas fa-times"></i></button>
            </div>
            <div class="space-y-3">${checks}</div>
            <div class="flex justify-end space-x-3 mt-6">
              <button class="px-4 py-2 text-sm font-medium text-gray-700 bg-gray-100 hover:bg-gray-200 rounded-md" onclick="this.closest('.fixed').remove()">Annuler</button>
              <button class="px-4 py-2 text-sm font-medium text-white bg-blue-600 hover:bg-blue-700 rounded-md" onclick="window.applyColumnVisibility(this.closest('.fixed'))">Appliquer</button>
            </div>
          </div>`;
        document.body.appendChild(modal);
        console.log('[columns-toggle] Modale injectée dans le DOM');
      } catch(err) {
        console.error('[columns-toggle] Erreur dans toggleColumnVisibility:', err);
      }
    };

    window.applyColumnVisibility = function(modal){
      try {
        console.log('[columns-toggle] applyColumnVisibility() appelé');
        const hidden = [];
        modal.querySelectorAll('.column-checkbox').forEach(cb => { if(!cb.checked) hidden.push(cb.dataset.column); });
        setHidden(hidden);
        applyVisibility(hidden);
        modal.remove();
      } catch(err) {
        console.error('[columns-toggle] Erreur dans applyColumnVisibility:', err);
      }
    };

    document.addEventListener('DOMContentLoaded', function(){
      console.log('[columns-toggle] DOMContentLoaded');
      // Appliquer état sauvegardé
      applyVisibility(getHidden());
      // Fallback: attacher un listener si l’onclick inline échoue
      const btn = document.getElementById('columnToggle');
      if (btn) {
        console.log('[columns-toggle] Bouton détecté, ajout listener de secours');
        btn.addEventListener('click', function(e){
          if (typeof window.toggleColumnVisibility !== 'function') {
            console.warn('[columns-toggle] toggleColumnVisibility non dispo au clic, réattachement forcé');
          }
          window.toggleColumnVisibility();
        });
      } else {
        console.warn('[columns-toggle] Bouton #columnToggle introuvable au DOM');
      }
      console.log('[columns-toggle] window.toggleColumnVisibility type =', typeof window.toggleColumnVisibility);
    });

    console.log('[columns-toggle] Module chargé');
  } catch (fatal) {
    console.error('[columns-toggle] Erreur fatale d’initialisation:', fatal);
  }
})();
