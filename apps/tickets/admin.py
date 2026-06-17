from django.contrib import admin

from .models import Ticket


@admin.register(Ticket)
class TicketAdmin(admin.ModelAdmin):
    list_display = ("id", "module", "title", "sector", "status", "created_at")
    list_filter = ("module", "status", "priority")
    search_fields = ("title", "description", "sector")
