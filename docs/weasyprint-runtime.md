# Runtime do WeasyPrint no Windows

O WeasyPrint precisa do pacote Python e de bibliotecas nativas do GTK/Pango.

## Opção 1 — Dependência instalada no ambiente

Instale as dependências nativas pelo MSYS2 e reinicie o terminal/servidor Django:

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

No shell do MSYS2:

```bash
pacman -S mingw-w64-x86_64-pango
```

O Celeris tenta localizar automaticamente:

- `C:\msys64\mingw64\bin`
- `C:\msys64\ucrt64\bin`

## Opção 2 — Runtime embutido no projeto

Para distribuir sem exigir MSYS2 instalado na máquina, copie as DLLs necessárias do GTK/Pango para:

```text
runtime/weasyprint/bin/
```

Essa pasta é carregada automaticamente pelo `celeris/settings.py` usando:

- `WEASYPRINT_DLL_DIRECTORIES`
- `os.add_dll_directory(...)` no Windows

O empacotamento/instalador do Celeris deve incluir essa pasta. Antes de redistribuir DLLs, valide as licenças dos pacotes incluídos.

## Diagnóstico

Se aparecer erro como `cannot load library 'libgobject-2.0-0'`, o pacote Python está instalado, mas as DLLs nativas não estão acessíveis pelo processo do Django.
