// JS for demande_dashboard.html view switching
function changeView(view) {
    document.getElementById('btn-cards').classList.remove('active');
    document.getElementById('btn-list').classList.remove('active');
    document.getElementById('btn-kanban').classList.remove('active');
    document.getElementById('btn-' + view).classList.add('active');

    const cardsGrid = document.querySelector('.ticket-grid');
    const listView = document.getElementById('ticket-list-view');
    const kanbanView = document.getElementById('ticket-kanban-view');
    if (cardsGrid) cardsGrid.style.display = (view === 'cards') ? 'grid' : 'none';
    if (listView) listView.style.display = (view === 'list') ? 'block' : 'none';
    if (kanbanView) kanbanView.style.display = (view === 'kanban') ? 'block' : 'none';
}
