from django.contrib import admin

from .models import BoardingAutoConfig, BoardingStatus


@admin.register(BoardingStatus)
class BoardingStatusAdmin(admin.ModelAdmin):
    list_display = ("quantity", "status", "level", "changed_by", "created_at")
    list_filter = ("status", "level")


@admin.register(BoardingAutoConfig)
class BoardingAutoConfigAdmin(admin.ModelAdmin):
    list_display = ("enabled", "database", "refresh_seconds", "updated_at")
