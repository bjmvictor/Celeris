"""Small extension point for demo-data providers owned by applications."""
from dataclasses import dataclass, field
from typing import Protocol


@dataclass
class DemoSeedContext:
    company_code: int
    password: str
    allow_non_debug: bool
    stdout: object
    style: object
    state: dict[str, object] = field(default_factory=dict)


class DemoSeedProvider(Protocol):
    code: str
    dependencies: tuple[str, ...]

    def run(self, context: DemoSeedContext) -> None: ...


class DemoSeedRegistry:
    def __init__(self):
        self._providers: dict[str, DemoSeedProvider] = {}

    def register(self, provider: DemoSeedProvider) -> None:
        existing = self._providers.get(provider.code)
        if existing is provider:
            return
        if existing and type(existing) is type(provider) and existing.dependencies == provider.dependencies:
            # Django can rebuild its app registry in tests; the application
            # module remains imported, so accept the equivalent provider.
            return
        if existing:
            raise RuntimeError(f"Demo seed provider code duplicated: {provider.code}")
        self._providers[provider.code] = provider

    def providers(self) -> tuple[DemoSeedProvider, ...]:
        resolved: list[DemoSeedProvider] = []
        remaining = dict(self._providers)
        while remaining:
            ready = [
                provider
                for code, provider in remaining.items()
                if set(provider.dependencies).issubset({item.code for item in resolved})
            ]
            if not ready:
                unresolved = ", ".join(sorted(remaining))
                raise RuntimeError(f"Demo seed provider dependencies cannot be resolved: {unresolved}")
            for provider in sorted(ready, key=lambda item: item.code):
                resolved.append(provider)
                remaining.pop(provider.code)
        return tuple(resolved)

    def run(self, context: DemoSeedContext) -> None:
        for provider in self.providers():
            provider.run(context)


seed_registry = DemoSeedRegistry()
