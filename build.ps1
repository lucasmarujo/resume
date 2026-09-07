<#
.SYNOPSIS
    Gera os PDFs do curriculo localmente.
.DESCRIPTION
    .\build.ps1              compila resume-ptbr.tex e resume-en.tex
    .\build.ps1 -Translate   regenera resume-en.tex a partir do PT-BR antes de compilar
                             (usa a assinatura autenticada via claude auth login)
#>
param([switch]$Translate)

$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot

if ($Translate) {
    python scripts/translate.py
    if ($LASTEXITCODE -ne 0) { throw "falha na traducao; nada foi compilado" }
}

foreach ($doc in "resume-ptbr", "resume-en") {
    latexmk -pdf -interaction=nonstopmode -halt-on-error "$doc.tex"
    if ($LASTEXITCODE -ne 0) { throw "falha ao compilar $doc.tex" }
}

latexmk -c | Out-Null
Get-ChildItem resume-*.pdf | Select-Object Name, Length, LastWriteTime
