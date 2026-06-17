from django.contrib import admin

from .models import AgentEvent, AgentMachine


@admin.register(AgentMachine)
class AgentMachineAdmin(admin.ModelAdmin):
    list_display = ("machine_name", "status", "ip", "username", "last_seen_at")
    list_filter = ("status", "display_enabled")
    search_fields = ("machine_name", "ip", "username", "operating_system")


@admin.register(AgentEvent)
class AgentEventAdmin(admin.ModelAdmin):
    list_display = ("event_type", "machine", "title", "created_at")
    list_filter = ("event_type",)
    search_fields = ("title", "message", "machine__machine_name")
