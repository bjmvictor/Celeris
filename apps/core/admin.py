from django.contrib import admin

from .models import Module, ScreenDefinition, ScreenField, UserModule


@admin.register(Module)
class ModuleAdmin(admin.ModelAdmin):
    list_display = ("code", "title", "active")
    search_fields = ("code", "title")


@admin.register(UserModule)
class UserModuleAdmin(admin.ModelAdmin):
    list_display = ("user", "module")
    autocomplete_fields = ("user", "module")


class ScreenFieldInline(admin.TabularInline):
    model = ScreenField
    extra = 1
    fields = (
        "order",
        "label",
        "table_name",
        "field_name",
        "field_type",
        "required",
        "consultable",
        "editable",
        "primary_key",
        "visible",
    )


@admin.register(ScreenDefinition)
class ScreenDefinitionAdmin(admin.ModelAdmin):
    list_display = ("title", "module", "parent_label", "screen_type", "allow_query", "allow_insert", "allow_update", "allow_delete", "active", "order")
    list_filter = ("module", "screen_type", "active")
    search_fields = ("title", "slug", "parent_label", "table_name")
    prepopulated_fields = {"slug": ("title",)}
    autocomplete_fields = ("module",)
    inlines = (ScreenFieldInline,)


@admin.register(ScreenField)
class ScreenFieldAdmin(admin.ModelAdmin):
    list_display = ("label", "screen", "field_name", "field_type", "required", "consultable", "editable", "primary_key", "visible")
    list_filter = ("field_type", "required", "consultable", "editable", "primary_key", "visible")
    search_fields = ("label", "field_name", "table_name", "screen__title")
    autocomplete_fields = ("screen",)
