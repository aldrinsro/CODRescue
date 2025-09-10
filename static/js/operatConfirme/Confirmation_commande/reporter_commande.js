// JS de report de commande (Confirmation)
// - Expose window.reporterCommande(commandeId)
// - Optionnel: attache un listener sur les boutons [data-action="reporter-commande"]

(function () {
  'use strict';

  // Flag global pour empêcher les doubles confirmations consécutives
  let isReportingInFlight = false;

  function getCSRFToken() {
    const meta = document.querySelector('meta[name="csrf-token"]');
    if (meta && meta.content) return meta.content;
    const input = document.querySelector('input[name="csrfmiddlewaretoken"]');
    return input ? input.value : '';
  }

  function toISOFromLocal(dateStr) {
    // Attendu: 'YYYY-MM-DD HH:MM' ou 'YYYY-MM-DDTHH:MM'
    if (!dateStr) return null;
    const s = dateStr.replace('T', ' ').trim();
    const parts = s.split(' ');
    if (parts.length !== 2) return null;
    const [d, t] = parts;
    const [y, m, da] = d.split('-').map(Number);
    const [hh, mm] = t.split(':').map(Number);
    if (!y || !m || !da || hh === undefined || mm === undefined) return null;
    const dt = new Date(y, m - 1, da, hh, mm, 0, 0);
    if (isNaN(dt.getTime())) return null;
    // Retourner ISO local sans timezone (compatible backend fromisoformat)
    const pad = (n) => String(n).padStart(2, '0');
    return `${dt.getFullYear()}-${pad(dt.getMonth() + 1)}-${pad(dt.getDate())} ${pad(dt.getHours())}:${pad(dt.getMinutes())}`;
  }

  async function callReporterEndpoint(commandeId, dateReport, motif) {
    const url = `/operateur-confirme/commandes/${commandeId}/reporter-ajax/`;
    const payload = {
      date_report: dateReport,
      motif: motif || ''
    };
    const res = await fetch(url, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'X-CSRFToken': getCSRFToken(),
        'X-Requested-With': 'XMLHttpRequest'
      },
      body: JSON.stringify(payload)
    });
    return res.json();
  }

  // ===== Modal de report (date + heure + motif) =====
  function ensureReportModal() {
    if (document.getElementById('reporterCommandeModal')) return;
    const wrapper = document.createElement('div');
    wrapper.innerHTML = `
<div id="reporterCommandeModal" class="fixed inset-0 bg-gray-600 bg-opacity-50 overflow-y-auto h-full w-full hidden z-50 flex items-center justify-center">
  <div class="relative p-6 bg-white w-full max-w-md m-auto flex-col flex rounded-xl shadow-2xl" style="border: 2px solid #f7d9c4;">
    <div class="flex justify-between items-center pb-4 border-b" style="border-color: #f7d9c4;">
      <div class="flex items-center">
        <div class="w-10 h-10 rounded-full flex items-center justify-center mr-3" style="background: linear-gradient(135deg, #4B352A, #6d4b3b);">
          <i class="fas fa-clock text-white"></i>
        </div>
        <h3 class="text-xl font-bold" style="color: #4B352A;">Reporter la Commande</h3>
      </div>
      <button type="button" id="reporterCloseBtn" class="text-gray-400 hover:text-gray-600">
        <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"></path></svg>
      </button>
    </div>
    <div class="py-4 space-y-4">
      <div>
        <label class="block text-sm font-medium text-gray-700 mb-2">Date de report</label>
        <input type="date" id="reportDateInput" class="w-full p-3 border rounded-lg focus:ring-2 focus:ring-amber-300 focus:border-amber-300" style="border-color: #f7d9c4;">
      </div>
      <div>
        <label class="block text-sm font-medium text-gray-700 mb-2">Heure de report</label>
        <input type="time" id="reportTimeInput" class="w-full p-3 border rounded-lg focus:ring-2 focus:ring-amber-300 focus:border-amber-300" style="border-color: #f7d9c4;">
      </div>
      <div>
        <label class="block text-sm font-medium text-gray-700 mb-2">Motif (optionnel)</label>
        <textarea id="reportMotifInput" rows="2" class="w-full p-3 border rounded-lg focus:ring-2 focus:ring-amber-300 focus:border-amber-300" style="border-color: #f7d9c4;" placeholder="Ex: Client indisponible, replanifier..."></textarea>
      </div>
      <div class="bg-amber-50 p-3 rounded text-amber-800 text-sm"><i class="fas fa-info-circle mr-2"></i>Aucune décrémentation de stock n'est effectuée lors du report.</div>
    </div>
    <div class="flex justify-end space-x-3 pt-4 border-t" style="border-color: #f7d9c4;">
      <button type="button" id="reporterCancelBtn" class="px-5 py-2.5 rounded-lg font-medium hover:bg-gray-100" style="background-color: #f7d9c4; color: #4B352A;">Annuler</button>
      <button type="button" id="reporterConfirmBtn" class="px-5 py-2.5 text-white rounded-lg font-medium hover:shadow-lg" style="background: linear-gradient(135deg, #4B352A, #6d4b3b);">Enregistrer</button>
    </div>
  </div>
</div>`;
    document.body.appendChild(wrapper.firstElementChild);
  }

  function openReportModal(defaultDate) {
    ensureReportModal();
    const modal = document.getElementById('reporterCommandeModal');
    const dateInput = document.getElementById('reportDateInput');
    const timeInput = document.getElementById('reportTimeInput');
    const motifInput = document.getElementById('reportMotifInput');
    const now = defaultDate || (function(){ const d=new Date(); d.setHours(d.getHours()+24,0,0,0); return d; })();
    const pad = (n) => String(n).padStart(2,'0');
    dateInput.value = `${now.getFullYear()}-${pad(now.getMonth()+1)}-${pad(now.getDate())}`;
    timeInput.value = `${pad(now.getHours())}:${pad(now.getMinutes())}`;
    motifInput.value = '';
    modal.classList.remove('hidden');
    modal.classList.add('flex');
  }

  function closeReportModal() {
    const modal = document.getElementById('reporterCommandeModal');
    if (modal) { modal.classList.add('hidden'); modal.classList.remove('flex'); }
  }

  async function reporterCommande(commandeId) {
    if (!commandeId) { alert('ID commande manquant'); return; }
    openReportModal();
    const confirmBtn = document.getElementById('reporterConfirmBtn');
    const cancelBtn = document.getElementById('reporterCancelBtn');
    const closeBtn = document.getElementById('reporterCloseBtn');
    const dateInput = document.getElementById('reportDateInput');
    const timeInput = document.getElementById('reportTimeInput');
    const motifInput = document.getElementById('reportMotifInput');

    function onCancel() { closeReportModal(); cleanup(); }
    function cleanup() {
      confirmBtn.removeEventListener('click', onConfirm);
      cancelBtn.removeEventListener('click', onCancel);
      closeBtn.removeEventListener('click', onCancel);
    }
    async function onConfirm() {
      if (isReportingInFlight) { return; }
      const d = (dateInput.value || '').trim();
      const t = (timeInput.value || '').trim();
      if (!d || !t) { alert('Veuillez renseigner la date et l\'heure de report'); return; }
      const formatted = `${d} ${t}`;
      const motif = motifInput.value || '';
      try {
        isReportingInFlight = true;
        confirmBtn.disabled = true;
        const resp = await callReporterEndpoint(commandeId, formatted, motif);
        if (resp && resp.success) {
          closeReportModal();
          alert(resp.message || 'Commande reportée');
          if (resp.redirect_url) { window.location.href = resp.redirect_url; } else { window.location.reload(); }
        } else {
          alert((resp && resp.message) || 'Erreur lors du report');
        }
      } catch (e) {
        alert('Erreur réseau lors du report');
      } finally {
        isReportingInFlight = false;
        confirmBtn.disabled = false;
        cleanup();
      }
    }

    // Empêcher les doubles liaisons si la modale est ouverte plusieurs fois
    confirmBtn.addEventListener('click', onConfirm, { once: true });
    cancelBtn.addEventListener('click', onCancel, { once: true });
    
  }

  // Export global
  window.reporterCommande = reporterCommande;

  // Note: Les templates appellent déjà reporterCommande(id) avec onclick inline.
  // On évite un binding délégué supplémentaire qui provoquerait des doubles appels.
})();


