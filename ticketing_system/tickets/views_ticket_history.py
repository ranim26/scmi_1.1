from django.shortcuts import render
from .models import TicketHistory
from django.contrib.auth.decorators import login_required

@login_required
def ticket_history_list(request):
    query = request.GET.get('q', '').strip()
    histories = TicketHistory.objects.select_related('ticket', 'user').all()
    if query:
        histories = histories.filter(
            action__icontains=query
        ) | histories.filter(
            details__icontains=query
        ) | histories.filter(
            user__username__icontains=query
        ) | histories.filter(
            ticket__id__icontains=query
        )
    return render(request, 'tickets/ticket_history_list.html', {'histories': histories, 'query': query})
