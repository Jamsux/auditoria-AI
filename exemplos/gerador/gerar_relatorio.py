"""Gera os relatórios de exemplo (básico e avançado) a partir dos JSON em exemplos/dados/.

Uso (em um venv com reportlab e matplotlib):
    python gerar_relatorio.py ../dados/basico.json ../exemplo-relatorio-basico.pdf
    python gerar_relatorio.py ../dados/avancado.json ../exemplo-relatorio-avancado.pdf
"""

import json
import sys
import tempfile
from collections import Counter
from html import escape
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
from reportlab.lib import colors  # noqa: E402
from reportlab.lib.enums import TA_CENTER  # noqa: E402
from reportlab.lib.pagesizes import A4  # noqa: E402
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet  # noqa: E402
from reportlab.lib.units import cm  # noqa: E402
from reportlab.lib.utils import ImageReader  # noqa: E402
from reportlab.platypus import (  # noqa: E402
    CondPageBreak,
    Image,
    KeepTogether,
    PageBreak,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

SEV_ORDER = ["CRÍTICA", "ALTA", "MÉDIA", "BAIXA", "INFORMATIVA"]
SEV_COLOR = {
    "CRÍTICA": "#B91C1C",
    "ALTA": "#EA580C",
    "MÉDIA": "#D97706",
    "BAIXA": "#2563EB",
    "INFORMATIVA": "#64748B",
}
FORTE = "#059669"
INK = colors.HexColor("#0F172A")
MUTED = colors.HexColor("#475569")
LINE = colors.HexColor("#CBD5E1")
SOFT = colors.HexColor("#F1F5F9")
STATUS_COLOR = {
    "CORRIGIDO": FORTE,
    "PERSISTENTE": "#B91C1C",
    "NÃO VERIFICÁVEL": "#64748B",
    "NOVO": "#7C3AED",
}

PAGE_W, PAGE_H = A4
MARGIN = 2 * cm
CONTENT_W = PAGE_W - 2 * MARGIN

base = getSampleStyleSheet()
S = {
    "title": ParagraphStyle("title", parent=base["Title"], fontName="Helvetica-Bold", fontSize=24,
                            leading=29, textColor=colors.white, alignment=0),
    "subtitle": ParagraphStyle("subtitle", fontName="Helvetica", fontSize=11, leading=15,
                               textColor=colors.HexColor("#CBD5E1")),
    "h1": ParagraphStyle("h1", fontName="Helvetica-Bold", fontSize=16, leading=20, textColor=INK,
                         spaceBefore=4, spaceAfter=10),
    "h2": ParagraphStyle("h2", fontName="Helvetica-Bold", fontSize=11.5, leading=15, textColor=INK,
                         spaceBefore=10, spaceAfter=5),
    "body": ParagraphStyle("body", fontName="Helvetica", fontSize=9.5, leading=13.5, textColor=INK),
    "small": ParagraphStyle("small", fontName="Helvetica", fontSize=8.3, leading=11, textColor=INK),
    "muted": ParagraphStyle("muted", fontName="Helvetica", fontSize=8.3, leading=11, textColor=MUTED),
    "cellb": ParagraphStyle("cellb", fontName="Helvetica-Bold", fontSize=8.3, leading=11, textColor=INK),
    "head": ParagraphStyle("head", fontName="Helvetica-Bold", fontSize=8.3, leading=11,
                           textColor=colors.white),
    "chip": ParagraphStyle("chip", fontName="Helvetica-Bold", fontSize=7.2, leading=9,
                           textColor=colors.white, alignment=TA_CENTER),
    "code": ParagraphStyle("code", fontName="Courier", fontSize=7.6, leading=9.8, textColor=INK),
    "kpi_n": ParagraphStyle("kpi_n", fontName="Helvetica-Bold", fontSize=20, leading=23,
                            textColor=colors.white, alignment=TA_CENTER),
    "kpi_l": ParagraphStyle("kpi_l", fontName="Helvetica-Bold", fontSize=7.5, leading=9,
                            textColor=colors.white, alignment=TA_CENTER),
}


def P(text, style="body"):
    return Paragraph(text, S[style])


def code(text):
    """Bloco monoespaçado que quebra linha (Preformatted não quebra)."""
    html = escape(text).replace(" ", "&nbsp;").replace("\n", "<br/>")
    return Paragraph(html, S["code"])


def chip(label, hex_color=None):
    color = colors.HexColor(hex_color or SEV_COLOR.get(label, "#64748B"))
    t = Table([[Paragraph(label, S["chip"])]], colWidths=[2.0 * cm])
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), color),
        ("TOPPADDING", (0, 0), (-1, -1), 2),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
        ("LEFTPADDING", (0, 0), (-1, -1), 2),
        ("RIGHTPADDING", (0, 0), (-1, -1), 2),
    ]))
    return t


def grid(rows, widths, header=True, zebra=True, extra=None):
    t = Table(rows, colWidths=widths, repeatRows=1 if header else 0)
    style = [
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("LINEBELOW", (0, 0), (-1, -1), 0.4, LINE),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ("LEFTPADDING", (0, 0), (-1, -1), 5),
        ("RIGHTPADDING", (0, 0), (-1, -1), 5),
    ]
    if header:
        style.append(("BACKGROUND", (0, 0), (-1, 0), INK))
    if zebra:
        for i in range(1 if header else 0, len(rows)):
            if i % 2 == 0:
                style.append(("BACKGROUND", (0, i), (-1, i), SOFT))
    t.setStyle(TableStyle(style + (extra or [])))
    return t


def box(flowables, border="#CBD5E1", bg="#F8FAFC", width=CONTENT_W):
    t = Table([[f] for f in flowables], colWidths=[width])
    t.setStyle(TableStyle([
        ("BOX", (0, 0), (-1, -1), 0.8, colors.HexColor(border)),
        ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor(bg)),
        ("LEFTPADDING", (0, 0), (-1, -1), 8),
        ("RIGHTPADDING", (0, 0), (-1, -1), 8),
        ("TOPPADDING", (0, 0), (-1, -1), 3),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
    ]))
    return t


# ---------- gráficos ----------

def img_w(path, width):
    """Imagem com largura fixa, mantendo a proporção do arquivo."""
    iw, ih = ImageReader(str(path)).getSize()
    return Image(str(path), width=width, height=width * ih / iw)


def donut(counts, path):
    labels = [s for s in SEV_ORDER if counts.get(s)]
    values = [counts[s] for s in labels]
    fig, ax = plt.subplots(figsize=(3.4, 3.4), dpi=200)
    ax.pie(values, colors=[SEV_COLOR[s] for s in labels], startangle=90, counterclock=False,
           wedgeprops=dict(width=0.38, edgecolor="white", linewidth=2))
    ax.text(0, 0.08, str(sum(values)), ha="center", va="center", fontsize=26, fontweight="bold",
            color="#0F172A")
    ax.text(0, -0.22, "achados", ha="center", va="center", fontsize=10, color="#475569")
    ax.legend([f"{s.capitalize()} ({counts[s]})" for s in labels], loc="upper center",
              bbox_to_anchor=(0.5, 0.02), ncol=2, frameon=False, fontsize=8.5)
    ax.set_aspect("equal")
    fig.savefig(path, bbox_inches="tight", transparent=True)
    plt.close(fig)


def barras(itens, path, titulo):
    """itens: lista de (rótulo, {severidade: n}) empilhada por severidade."""
    labels = [i[0] for i in itens][::-1]
    fig, ax = plt.subplots(figsize=(4.4, 0.42 * len(labels) + 0.9), dpi=200)
    left = [0] * len(labels)
    for sev in SEV_ORDER:
        vals = [i[1].get(sev, 0) for i in itens][::-1]
        if any(vals):
            ax.barh(labels, vals, left=left, color=SEV_COLOR[sev], height=0.6,
                    label=sev.capitalize(), edgecolor="white", linewidth=0.8)
            left = [a + b for a, b in zip(left, vals)]
    for y, total in enumerate(left):
        ax.text(total + 0.08, y, str(total), va="center", fontsize=8.5, color="#0F172A")
    ax.set_title(titulo, fontsize=10, loc="left", color="#0F172A", fontweight="bold")
    ax.spines[["top", "right"]].set_visible(False)
    ax.spines[["left", "bottom"]].set_color("#CBD5E1")
    ax.tick_params(labelsize=8.5, colors="#334155")
    ax.set_xlim(0, max(left + [1]) + 1)
    ax.xaxis.set_major_locator(matplotlib.ticker.MaxNLocator(integer=True))
    ax.legend(fontsize=7.5, frameon=False, loc="upper center", bbox_to_anchor=(0.45, -0.12), ncol=5,
              handlelength=1, columnspacing=0.8)
    fig.savefig(path, bbox_inches="tight", transparent=True)
    plt.close(fig)


def mapa_risco(achados, path):
    fig, ax = plt.subplots(figsize=(6.2, 4.6), dpi=200)
    for x in range(1, 6):
        for y in range(1, 6):
            score = x * y
            c = "#FEE2E2" if score >= 15 else "#FFEDD5" if score >= 8 else "#FEF9C3" if score >= 4 else "#DCFCE7"
            ax.add_patch(plt.Rectangle((x - 0.5, y - 0.5), 1, 1, facecolor=c, edgecolor="white", lw=2))
    cells = {}
    for a in achados:
        cells.setdefault((a["prob_n"], a["impacto_n"]), []).append(a)
    for (x, y), grupo in cells.items():
        n = len(grupo)
        for i, a in enumerate(grupo):
            dy = (i - (n - 1) / 2) * 0.22
            ax.text(x, y + dy, a["id"].replace("SEC-", ""), ha="center", va="center", fontsize=7.5,
                    fontweight="bold", color="white",
                    bbox=dict(boxstyle="round,pad=0.25", fc=SEV_COLOR[a["severidade"]], ec="none"))
    ax.set_xlim(0.5, 5.5)
    ax.set_ylim(0.5, 5.5)
    ax.set_xticks(range(1, 6), ["Rara", "Baixa", "Possível", "Provável", "Quase certa"], fontsize=8)
    ax.set_yticks(range(1, 6), ["Mínimo", "Baixo", "Moderado", "Alto", "Severo"], fontsize=8)
    ax.set_xlabel("Probabilidade", fontsize=9)
    ax.set_ylabel("Impacto", fontsize=9)
    for s in ax.spines.values():
        s.set_visible(False)
    ax.tick_params(length=0)
    fig.savefig(path, bbox_inches="tight", transparent=True)
    plt.close(fig)


# ---------- seções ----------

def capa(d, tipo_label):
    banner = Table([
        [P(tipo_label.upper(), "kpi_l")],
        [P(escape(d["titulo"]), "title")],
        [P(f"{d['data']} &nbsp;·&nbsp; Projeto: {escape(d['projeto'])}", "subtitle")],
    ], colWidths=[CONTENT_W])
    banner.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), INK),
        ("LEFTPADDING", (0, 0), (-1, -1), 18),
        ("RIGHTPADDING", (0, 0), (-1, -1), 18),
        ("TOPPADDING", (0, 0), (-1, 0), 22),
        ("BOTTOMPADDING", (0, -1), (-1, -1), 22),
        ("ALIGN", (0, 0), (-1, 0), "LEFT"),
    ]))
    out = [banner, Spacer(1, 14)]
    out.append(box([P("<b>EXEMPLO FICTÍCIO</b>", "cellb"), P(escape(d["aviso"]), "small")],
                   border="#D97706", bg="#FFFBEB"))
    out += [Spacer(1, 14), P("Stack detectada", "h2"), P(escape(d["stack"])),
            P("Escopo auditado", "h2"), P(escape(d["escopo"])),
            P("Nota metodológica", "h2")]
    rows = [[P("Item", "head"), P("Como foi analisado", "head")]]
    rows += [[P(escape(a), "cellb"), P(escape(b), "small")] for a, b in d["metodologia"]]
    out.append(grid(rows, [4.2 * cm, CONTENT_W - 4.2 * cm]))
    if d.get("limitacoes"):
        out += [P("Limitações", "h2"), P(escape(d["limitacoes"]))]
    return out


def resumo(d, tmp, por_owasp):
    counts = Counter(a["severidade"] for a in d["achados"])
    out = [PageBreak(), P("Resumo executivo", "h1")]
    tiles = [[P(str(counts.get(s, 0)), "kpi_n") for s in SEV_ORDER] + [P(str(len(d["pontos_fortes"])), "kpi_n")],
             [P(s, "kpi_l") for s in SEV_ORDER] + [P("PONTOS FORTES", "kpi_l")]]
    w = CONTENT_W / 6
    t = Table(tiles, colWidths=[w] * 6)
    st = [("TOPPADDING", (0, 0), (-1, 0), 8), ("BOTTOMPADDING", (0, 1), (-1, 1), 8),
          ("LINEAFTER", (0, 0), (-2, -1), 3, colors.white)]
    for i, s in enumerate(SEV_ORDER + ["F"]):
        st.append(("BACKGROUND", (i, 0), (i, -1), colors.HexColor(SEV_COLOR.get(s, FORTE))))
    t.setStyle(TableStyle(st))
    out += [t, Spacer(1, 10)]

    donut(counts, tmp / "donut.png")
    if por_owasp:
        cats = [(f"{r[0]}", {}) for r in d["owasp_matriz"]]
        idx = {c[0]: c[1] for c in cats}
        for a in d["achados"]:
            idx[a["owasp"]][a["severidade"]] = idx[a["owasp"]].get(a["severidade"], 0) + 1
        barras(cats, tmp / "barras.png", "Achados por categoria OWASP Top 10:2025")
    else:
        cats = [(c, {}) for c in d["categorias"]]
        idx = {c[0]: c[1] for c in cats}
        for a in d["achados"]:
            idx[a["categoria"]][a["severidade"]] = idx[a["categoria"]].get(a["severidade"], 0) + 1
        barras(cats, tmp / "barras.png", "Achados por categoria")
    charts = Table([[img_w(tmp / "donut.png", 6.4 * cm),
                     img_w(tmp / "barras.png", 10.2 * cm)]],
                   colWidths=[6.8 * cm, CONTENT_W - 6.8 * cm])
    charts.setStyle(TableStyle([("VALIGN", (0, 0), (-1, -1), "MIDDLE")]))
    out.append(charts)
    return out


def fortes_fracos(d):
    out = [CondPageBreak(9 * cm), P("Pontos fortes", "h1"),
           P("Controles encontrados e verificados no código, com evidência.", "muted"), Spacer(1, 4)]
    rows = [[P("Controle", "head"), P("Evidência", "head")]]
    rows += [[P(escape(a), "cellb"), P(escape(b), "small")] for a, b in d["pontos_fortes"]]
    out.append(grid(rows, [5.5 * cm, CONTENT_W - 5.5 * cm],
                    extra=[("LINEBEFORE", (0, 1), (0, -1), 3, colors.HexColor(FORTE))]))
    out += [P("Pontos fracos", "h1")]
    for f in d["pontos_fracos"]:
        out.append(box([P("&#9679;&nbsp; " + escape(f), "small")], border="#FECACA", bg="#FEF2F2"))
        out.append(Spacer(1, 3))
    return out


def evolucao(d):
    out = [PageBreak(), P("Evolução desde a auditoria básica", "h1")]
    st = Counter(e[2] for e in d["evolucao"])
    novos = sum(1 for a in d["achados"] if a["status"] == "NOVO")
    out.append(P(f"<b>{st.get('CORRIGIDO', 0)}</b> corrigidos &nbsp;·&nbsp; "
                 f"<b>{st.get('PERSISTENTE', 0)}</b> persistentes &nbsp;·&nbsp; "
                 f"<b>{novos}</b> achados novos nesta auditoria"))
    out.append(Spacer(1, 6))
    rows = [[P("ID", "head"), P("Achado da básica", "head"), P("Status", "head"), P("Evidência", "head")]]
    for i, s, status, ev in d["evolucao"]:
        rows.append([P(i, "cellb"), P(escape(s), "small"), chip(status, STATUS_COLOR[status]),
                     P(escape(ev), "small")])
    out.append(grid(rows, [1.4 * cm, 5 * cm, 2.4 * cm, CONTENT_W - 8.8 * cm]))
    return out


def risco(d, tmp):
    mapa_risco(d["achados"], tmp / "risco.png")
    return [CondPageBreak(12 * cm), P("Mapa de risco", "h1"),
            P("Impacto × probabilidade. Cada marcador é um achado (número do SEC), colorido pela severidade.",
              "muted"),
            img_w(tmp / "risco.png", 14 * cm)]


def matrizes(d):
    out = [PageBreak(), P("Matriz OWASP Top 10:2025", "h1")]
    rows = [[P("OWASP", "head"), P("Categoria", "head"), P("Status", "head"), P("Achados", "head"),
             P("Observação", "head")]]
    for c, nome, status, n, obs in d["owasp_matriz"]:
        rows.append([P(c, "cellb"), P(escape(nome), "small"), P(status, "small"), P(n, "cellb"),
                     P(escape(obs), "small")])
    out.append(grid(rows, [1.5 * cm, 5.2 * cm, 2.4 * cm, 1.6 * cm, CONTENT_W - 10.7 * cm]))
    out += [P("Matriz de TTPs", "h1")]
    rows = [[P("TTP", "head"), P("Aplicável", "head"), P("Verificado", "head"), P("Achados", "head")]]
    for t, ap, ver, n in d["ttp_matriz"]:
        rows.append([P(escape(t), "cellb"), P(ap, "small"), P(ver, "small"), P(n, "cellb")])
    out.append(grid(rows, [6.5 * cm, 3 * cm, 4 * cm, CONTENT_W - 13.5 * cm]))
    out += [CondPageBreak(5 * cm), P("Cobertura", "h1")]
    rows = [[P(h, "head") for h in ["Item", "Total", "Analisados", "Não aplicáveis", "Não confirmados"]]]
    rows += [[P(r[0], "cellb")] + [P(x, "small") for x in r[1:]] for r in d["cobertura"]]
    out.append(grid(rows, [5.5 * cm] + [(CONTENT_W - 5.5 * cm) / 4] * 4))
    return out


def tabela_achados(d, avancado):
    out = [CondPageBreak(10 * cm), P("Achados detalhados", "h1")]
    if avancado:
        rows = [[P(h, "head") for h in ["ID", "Severidade", "OWASP", "TTP", "Arquivo:linha", "Descrição"]]]
        for a in d["achados"]:
            rows.append([P(a["id"], "cellb"), chip(a["severidade"]), P(a["owasp"], "small"),
                         P(escape(a["ttp"]), "small"), P(escape(a["arquivo"]), "code"),
                         P(escape(a["titulo"]), "small")])
        out.append(grid(rows, [1.6 * cm, 2.3 * cm, 1.6 * cm, 2.6 * cm, 4.3 * cm, CONTENT_W - 12.4 * cm]))
        return out
    for cat in d["categorias"]:
        itens = [a for a in d["achados"] if a["categoria"] == cat]
        out.append(P(escape(cat), "h2"))
        rows = [[P(h, "head") for h in ["Severidade", "Arquivo:linha", "Descrição"]]]
        for a in itens:
            rows.append([chip(a["severidade"]), P(escape(a["arquivo"]), "code"),
                         P(f"<b>{a['id']} · {escape(a['titulo'])}.</b> {escape(a['descricao'])}", "small")])
        out.append(grid(rows, [2.4 * cm, 5 * cm, CONTENT_W - 7.4 * cm]))
    return out


def detalhe(a, avancado):
    head = Table([[chip(a["severidade"]), P(f"<b>{a['id']}</b> &nbsp; {escape(a['titulo'])}", "cellb")]],
                 colWidths=[2.3 * cm, CONTENT_W - 2.3 * cm])
    head.setStyle(TableStyle([("VALIGN", (0, 0), (-1, -1), "MIDDLE"), ("LEFTPADDING", (0, 0), (-1, -1), 0)]))
    if avancado:
        meta = (f"<b>Status:</b> {a['status']} &nbsp;·&nbsp; <b>Prioridade:</b> {a['prioridade']} &nbsp;·&nbsp; "
                f"<b>Confiança:</b> {a['confianca']} &nbsp;·&nbsp; <b>OWASP:</b> {a['owasp']}:2025 &nbsp;·&nbsp; "
                f"<b>{a['cwe']}</b> &nbsp;·&nbsp; <b>TTP:</b> {escape(a['ttp'])}")
        campos = [("Source", a["source"]), ("Sink", a["sink"]), ("Exploração", a["exploracao"]),
                  ("Pré-condições", a["precondicoes"]), ("Impacto", a["impacto"]), ("Correção", a["correcao"])]
    else:
        meta = f"<b>Categoria:</b> {escape(a['categoria'])}"
        campos = [("Por que é explorável", a["descricao"]), ("Impacto", a["impacto"]),
                  ("Correção", a["correcao"])]
    rows = [[P("Arquivo", "cellb"), P(escape(a["arquivo"]), "code")],
            [P("Evidência", "cellb"), box([code(a["trecho"])], bg="#F1F5F9", width=CONTENT_W - 3.3 * cm)]]
    rows += [[P(k, "cellb"), P(escape(v), "small")] for k, v in campos]
    body = grid(rows, [3 * cm, CONTENT_W - 3 * cm], header=False, zebra=False,
                extra=[("VALIGN", (0, 0), (-1, -1), "TOP")])
    return KeepTogether([head, P(meta, "muted"), Spacer(1, 3), body, Spacer(1, 12)])


def detalhes(d, avancado):
    out = [PageBreak(), P("Detalhamento dos achados", "h1")]
    ordem = sorted(d["achados"], key=lambda a: (SEV_ORDER.index(a["severidade"]), a["id"]))
    out += [detalhe(a, avancado) for a in ordem]
    return out


def nao_confirmados(d):
    out = [CondPageBreak(6 * cm), P("Não confirmados", "h1"),
           P("Itens investigados sem evidência suficiente. Não contam como achados.", "muted"), Spacer(1, 4)]
    rows = [[P("Item", "head"), P("O que falta para confirmar", "head")]]
    rows += [[P(escape(a), "cellb"), P(escape(b), "small")] for a, b in d["nao_confirmados"]]
    out.append(grid(rows, [6 * cm, CONTENT_W - 6 * cm]))
    return out


def recomendacoes(d):
    out = [CondPageBreak(8 * cm), P("Recomendações priorizadas", "h1")]
    cor = {"P1": "#B91C1C", "P2": "#EA580C", "P3": "#2563EB"}
    rows = [[P("Prioridade", "head"), P("Ação", "head")]]
    rows += [[chip(p, cor[p]), P(escape(t), "small")] for p, t in d["recomendacoes"]]
    out.append(grid(rows, [2.4 * cm, CONTENT_W - 2.4 * cm]))
    return out


def issue_md(n, it):
    linhas = [f"--- ISSUE {n} ---", "", f"# {it['titulo']}", "", f"Labels: {it['labels']}",
              f"Achados: {', '.join(it['achados'])}", "", "## Descrição", it["descricao"], "",
              "## Evidência", it["evidencia"], "", "## Impacto", it["impacto"], "",
              "## Correção sugerida", it["correcao"], "", "## Critérios de aceite"]
    linhas += [f"- [ ] {c}" for c in it["aceite"]]
    linhas += ["", f"--- FIM ISSUE {n} ---"]
    return "\n".join(linhas)


def issues(d):
    out = [CondPageBreak(12 * cm), P("Issues para o GitHub", "h1"),
           P("Texto pronto para copiar e colar. Nenhuma issue foi aberta automaticamente. "
             "Em repositório público, prefira um GitHub Security Advisory privado.", "muted"),
           Spacer(1, 8)]
    for n, it in enumerate(d["issues"], 1):
        out += [box([code(issue_md(n, it))]), Spacer(1, 10)]
    return out


# ---------- montagem ----------

def build(dados_path, saida):
    d = json.loads(Path(dados_path).read_text(encoding="utf-8"))
    avancado = d["tipo"] == "avancado"

    def decor(canvas, doc):
        canvas.saveState()
        canvas.setFont("Helvetica", 7.5)
        canvas.setFillColor(MUTED)
        canvas.drawString(MARGIN, PAGE_H - 1.25 * cm, d["cabecalho"])
        canvas.drawRightString(PAGE_W - MARGIN, PAGE_H - 1.25 * cm, d["data"])
        canvas.setStrokeColor(LINE)
        canvas.line(MARGIN, PAGE_H - 1.4 * cm, PAGE_W - MARGIN, PAGE_H - 1.4 * cm)
        canvas.line(MARGIN, 1.4 * cm, PAGE_W - MARGIN, 1.4 * cm)
        canvas.drawString(MARGIN, 1.0 * cm, "Exemplo gerado para fins educacionais — dados fictícios")
        canvas.drawRightString(PAGE_W - MARGIN, 1.0 * cm, f"Página {doc.page}")
        canvas.restoreState()

    with tempfile.TemporaryDirectory() as t:
        tmp = Path(t)
        story = capa(d, "Auditoria avançada" if avancado else "Auditoria básica")
        story += resumo(d, tmp, por_owasp=avancado)
        if avancado:
            story += evolucao(d) + risco(d, tmp)
        story += fortes_fracos(d)
        if avancado:
            story += matrizes(d)
        story += tabela_achados(d, avancado) + detalhes(d, avancado)
        if avancado:
            story += nao_confirmados(d)
        story += recomendacoes(d) + issues(d)

        doc = SimpleDocTemplate(str(saida), pagesize=A4, leftMargin=MARGIN, rightMargin=MARGIN,
                                topMargin=MARGIN, bottomMargin=MARGIN, title=d["titulo"],
                                author="Auditoria de Segurança com IA (exemplo)")
        doc.build(story, onFirstPage=decor, onLaterPages=decor)
    print(f"gerado: {saida}")


if __name__ == "__main__":
    build(sys.argv[1], sys.argv[2])
