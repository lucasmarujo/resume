# Currículo / Resume — Lucas Marujo

Currículo em LaTeX com versão em inglês gerada automaticamente.

## Download

| | |
|---|---|
| 🇧🇷 Português | [resume-ptbr.pdf](https://github.com/lucasmarujo/resume/releases/latest/download/resume-ptbr.pdf) |
| 🇺🇸 English | [resume-en.pdf](https://github.com/lucasmarujo/resume/releases/latest/download/resume-en.pdf) |

Os links acima apontam sempre para a versão mais recente.

## Como funciona

**`resume-ptbr.tex` é a única fonte da verdade.** Edite apenas ele.

**No commit**, o hook [`pre-commit`](.githooks/pre-commit) detecta que o PT-BR mudou,
regenera o `resume-en.tex` e o inclui no mesmo commit. A tradução usa o CLI do Claude
Code com a **assinatura já autenticada na máquina** — nenhuma chave de API envolvida.

Antes de escrever, o script confere que a sequência de comandos LaTeX do EN é idêntica
à do PT-BR. Se divergir, tenta de novo; falhando, aborta o commit sem escrever nada.

**No push**, o workflow [`resume.yml`](.github/workflows/resume.yml) compila os dois
PDFs e publica na release `latest` e como artifact da execução.

> ⚠️ `resume-en.tex` é **gerado**. Qualquer edição manual nele é sobrescrita no próximo commit que toque o PT-BR.

## Setup (uma vez por clone)

```powershell
git config core.hooksPath .githooks
claude auth login          # se ainda não estiver logado
```

Confira com `claude auth status` — precisa mostrar `"loggedIn": true`.

## Estrutura

```
preamble.tex           macros e pacotes, compartilhados pelos dois documentos
resume-ptbr.tex        fonte da verdade — editar aqui
resume-en.tex          gerado a partir do PT-BR
scripts/translate.py   tradução + validação estrutural
.githooks/pre-commit   dispara a tradução no commit
build.ps1              build local dos PDFs
```

## Build local

Requer MiKTeX (ou TeX Live) com `latexmk` no PATH.

```powershell
.\build.ps1              # compila os dois PDFs
.\build.ps1 -Translate   # regenera o EN antes de compilar
```

Para checar o tradutor sem chamar o modelo:

```powershell
python scripts/translate.py --selftest
```

## Limitação conhecida

A tradução roda no hook local. Um commit feito com `--no-verify`, ou de uma máquina sem
o hook instalado e sem `claude` autenticado, deixa o `resume-en.tex` defasado sem avisar.
Nesse caso, rode `python scripts/translate.py` e commite o resultado.
