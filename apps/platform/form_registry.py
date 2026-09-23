"""Neutral registry for configurable forms exposed by installed applications."""
from dataclasses import dataclass, field

from django.utils.module_loading import import_string


@dataclass(frozen=True)
class ConfigurableForm:
    code: str
    name: str
    form_class: str
    field_labels: dict[str, str] = field(default_factory=dict)
    uses_company: bool = True


class FormRegistry:
    def __init__(self):
        self._forms: dict[str, ConfigurableForm] = {}

    def register(self, definition: ConfigurableForm) -> None:
        existing = self._forms.get(definition.code)
        if existing and existing != definition:
            raise RuntimeError(f"Configurable form code duplicated: {definition.code}")
        self._forms[definition.code] = definition

    def get(self, code: str) -> ConfigurableForm | None:
        return self._forms.get(code)

    def definitions(self) -> tuple[ConfigurableForm, ...]:
        return tuple(sorted(self._forms.values(), key=lambda item: item.name))

    def build(self, code: str, company):
        definition = self.get(code)
        if definition is None:
            return None
        kwargs = {"empresa": company} if definition.uses_company else {}
        return import_string(definition.form_class)(**kwargs)


form_registry = FormRegistry()
