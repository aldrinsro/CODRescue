/**
 * Script pour gérer l'ouverture/fermeture des sections dans la page de détail commande
 */

document.addEventListener('DOMContentLoaded', function() {
    // Fonction pour toggle une section
    function toggleSection(sectionId) {
        const content = document.getElementById(sectionId);
        const button = document.querySelector(`[data-toggle="${sectionId}"]`);
        const icon = button?.querySelector('i');
        const textSpan = button?.querySelector('span');

        if (content && button) {
            content.classList.toggle('hidden');

            // Changer l'icône et le texte
            if (content.classList.contains('hidden')) {
                icon?.classList.remove('fa-chevron-up');
                icon?.classList.add('fa-chevron-down');
                if (textSpan) textSpan.textContent = 'Agrandir';
                button.setAttribute('aria-expanded', 'false');
            } else {
                icon?.classList.remove('fa-chevron-down');
                icon?.classList.add('fa-chevron-up');
                if (textSpan) textSpan.textContent = 'Réduire';
                button.setAttribute('aria-expanded', 'true');
            }
        }
    }

    // Attacher les événements aux boutons toggle
    document.querySelectorAll('[data-toggle]').forEach(button => {
        button.addEventListener('click', function() {
            const targetId = this.getAttribute('data-toggle');
            toggleSection(targetId);
        });
    });
});
