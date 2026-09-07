#!/usr/bin/env python3
"""Gera resume-en.tex a partir de resume-ptbr.tex, a fonte da verdade.

Traduz apenas o corpo do documento (entre \\begin{document} e \\end{document});
o preambulo fica em preamble.tex e nunca passa pelo modelo. Antes de escrever,
valida que a sequencia de comandos LaTeX do corpo traduzido e identica a do
original -- se nao for, nada e escrito.

Uso:
    python scripts/translate.py              gera resume-en.tex
    python scripts/translate.py --selftest   roda os asserts, sem chamar a API
"""

import os
import pathlib
import re
import sys

RAIZ = pathlib.Path(__file__).resolve().parent.parent
ORIGEM = RAIZ / "resume-ptbr.tex"
DESTINO = RAIZ / "resume-en.tex"

MODELO = "claude-opus-5"
MARCA_INICIO = r"\begin{document}"
MARCA_FIM = r"\end{document}"

CABECALHO = (
    "% GERADO AUTOMATICAMENTE a partir de resume-ptbr.tex -- nao edite a mao.\n"
    "% Qualquer alteracao aqui e sobrescrita pelo workflow .github/workflows/resume.yml\n"
)

SYSTEM = r"""Voce traduz o corpo de um curriculo em LaTeX de portugues brasileiro para ingles.

REGRA DE SAIDA
Devolva APENAS o corpo LaTeX traduzido. Sem cercas markdown, sem comentario, sem
explicacao, sem \begin{document} ou \end{document}. A primeira e a ultima linha da sua
resposta devem ser as mesmas linhas do original, so que traduzidas.

ESTRUTURA -- INVIOLAVEL
Preserve cada comando LaTeX, a ordem deles, a estrutura de argumentos, a indentacao e as
quebras de linha EXATAMENTE como no original. A sequencia de comandos (\textbf, \item,
\hfill, \vspace, \begin, \end, \href, \header, ...) tem de ser identica byte a byte.
Traduza somente o texto legivel por humanos que esta dentro ou entre os comandos. Nao
adicione, remova, reordene nem reagrupe bullets, secoes ou linhas.

NAO TRADUZA
- Nomes de empresas e instituicoes: GreenLegis, Grupo Tombini, Rede Boa Supermercados,
  AirBlower Engenharia, Fly Wheel, Intellibrand, FIAP, Universidade Padre Anchieta,
  ILAC - International Language Academy of Canada, Faculdade Flamingo.
- Nomes de projetos: Pulso, Orkai.
- Nomes de pessoa, tecnologias, produtos, URLs, e-mails e telefones.
- Nomes de cidade: Sao Paulo, Jundiai, Lapa, Toronto.

GLOSSARIO
- Meses: Jan->Jan, Fev->Feb, Mar->Mar, Abr->Apr, Mai->May, Jun->Jun, Jul->Jul,
  Ago->Aug, Set->Sep, Out->Oct, Nov->Nov, Dez->Dec.
- Atual->Present | Cursando->In Progress | Completo->Completed.
- Secoes: Resumo->Summary | Experiencia->Experience | Projetos->Projects |
  Habilidades->Skills | Educacao->Education.
- Linhas da tabela de skills: "Banco de dados \& Servers"->"Databases \& Servers" |
  "Plataformas \& Outros"->"Platforms \& Others". Frontend e Backend nao mudam.
- Cargos: Engenheiro de Software->Software Engineer |
  Desenvolvedor Full-Stack->Full-Stack Developer |
  Estagiario em Suporte de TI->IT Support Intern | Estagiario em TI->IT Intern.
- Titulos academicos em caixa alta continuam em caixa alta:
  BACHARELADO EM CIENCIAS DA COMPUTACAO->BACHELOR'S DEGREE IN COMPUTER SCIENCE |
  MBA EM AI ENGINEER E MULTI-AGENTS->MBA IN AI ENGINEERING AND MULTI-AGENTS |
  TECNICO EM INFORMATICA->TECHNICAL DEGREE IN INFORMATION TECHNOLOGY |
  ENGLISH AS SECOND LANGUAGE->ENGLISH AS A SECOND LANGUAGE.
- Brasil->Brazil.
- Numeros seguem a convencao inglesa: virgula decimal vira ponto ("1,6 segundos" ->
  "1.6 seconds") e ponto de milhar vira virgula ("2.500 usuarios" -> "2,500 users").

REGISTRO
Ingles de curriculo americano, natural e idiomatico -- nao traducao literal. Bullets de
experiencia comecam com verbo de acao forte no passado (Led, Designed, Built, Optimized,
Implemented, Migrated). Prefira a formulacao que um engenheiro nativo escreveria a uma
traducao fiel ao portugues. Mantenha o comprimento de cada bullet proximo do original
para nao quebrar a paginacao."""


def extrair_corpo(tex):
    """Retorna o trecho entre \\begin{document} e \\end{document}."""
    inicio = tex.index(MARCA_INICIO) + len(MARCA_INICIO)
    fim = tex.index(MARCA_FIM)
    return tex[inicio:fim]


def comandos(tex):
    """Sequencia de comandos LaTeX do trecho, na ordem em que aparecem."""
    return re.findall(r"\\[A-Za-z]+", tex)


def limpar_cerca(texto):
    """Remove cerca markdown que o modelo eventualmente adicione."""
    texto = texto.strip()
    if texto.startswith("```"):
        linhas = texto.split("\n")
        linhas = linhas[1:]
        if linhas and linhas[-1].strip() == "```":
            linhas = linhas[:-1]
        texto = "\n".join(linhas)
    return texto


def divergencia(cmd_pt, cmd_en):
    """Descreve a primeira diferenca estrutural, ou None se as sequencias baterem."""
    if cmd_pt == cmd_en:
        return None
    for i, (pt, en) in enumerate(zip(cmd_pt, cmd_en)):
        if pt != en:
            contexto = " ".join(cmd_pt[max(0, i - 3):i + 4])
            return (
                f"comando #{i}: esperado {pt!r}, veio {en!r}. "
                f"Trecho correspondente no original: {contexto}"
            )
    return f"o total de comandos difere: original={len(cmd_pt)}, traducao={len(cmd_en)}"


def traduzir(corpo_pt, feedback=None):
    import anthropic

    conteudo = corpo_pt
    if feedback:
        conteudo = (
            f"{corpo_pt}\n\n---\n"
            f"A tentativa anterior quebrou a estrutura LaTeX: {feedback}\n"
            "Refaca a traducao preservando exatamente a mesma sequencia de comandos."
        )

    resposta = anthropic.Anthropic().messages.create(
        model=MODELO,
        max_tokens=16000,
        output_config={"effort": "low"},
        system=SYSTEM,
        messages=[{"role": "user", "content": conteudo}],
    )
    texto = "".join(b.text for b in resposta.content if b.type == "text")
    return limpar_cerca(texto)


def main():
    if not os.environ.get("ANTHROPIC_API_KEY"):
        sys.exit(
            "ANTHROPIC_API_KEY nao configurado.\n"
            "  CI:    cadastre o secret em Settings > Secrets and variables > Actions\n"
            '  local: $env:ANTHROPIC_API_KEY = "sk-ant-..."'
        )

    corpo_pt = extrair_corpo(ORIGEM.read_text(encoding="utf-8"))
    cmd_pt = comandos(corpo_pt)

    feedback = None
    for tentativa in (1, 2):
        corpo_en = traduzir(corpo_pt, feedback)
        feedback = divergencia(cmd_pt, comandos(corpo_en))
        if feedback is None:
            break
        print(f"tentativa {tentativa} falhou na validacao: {feedback}", file=sys.stderr)
    else:
        sys.exit("traducao rejeitada duas vezes; resume-en.tex mantido como estava.")

    saida = (
        f"{CABECALHO}\\input{{preamble}}\n\n"
        f"% Begin document\n{MARCA_INICIO}{corpo_en}{MARCA_FIM}\n"
    )
    DESTINO.write_text(saida, encoding="utf-8", newline="\n")
    print(f"resume-en.tex gerado ({len(cmd_pt)} comandos LaTeX preservados).")


def _selftest():
    tex = "\\input{preamble}\n\\begin{document}\n\\header{Resumo}\n\\end{document}\n"
    assert extrair_corpo(tex) == "\n\\header{Resumo}\n", extrair_corpo(tex)

    assert comandos("\\textbf{Ola} \\item x") == ["\\textbf", "\\item"]
    assert comandos("sem comando algum") == []

    assert limpar_cerca("```latex\n\\item a\n```") == "\\item a"
    assert limpar_cerca("  \\item a  ") == "\\item a"

    assert divergencia(["\\item", "\\textbf"], ["\\item", "\\textbf"]) is None
    assert "esperado" in divergencia(["\\item", "\\textbf"], ["\\item", "\\emph"])
    assert "total de comandos" in divergencia(["\\item", "\\textbf"], ["\\item"])

    corpo = extrair_corpo(ORIGEM.read_text(encoding="utf-8"))
    assert comandos(corpo), "o corpo do resume-ptbr.tex nao tem comando LaTeX algum"

    print("selftest ok")


if __name__ == "__main__":
    if "--selftest" in sys.argv:
        _selftest()
    else:
        main()
