// Fermer la modal avec Escape (uniquement si elle est ouverte)
document.addEventListener('keydown', function(event) {
    if (event.key === 'Escape') {
        const modal = document.getElementById('modalExplicationTotal');
        if (modal && modal.style.display === 'flex') {
            fermerModalExplicationTotal();
        }
    }
});
