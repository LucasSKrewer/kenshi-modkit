"""Monta a visão EFETIVA do jogo: os valores que de fato valem, já mesclados.

Dois motivos para isto existir separado:

1. Os arquivos de `data/` se sobrepõem e cada um grava só o que altera. Ficar
   com a última versão de um registro dá campo faltando -- o `GLOBAL CONSTANTS`
   do `Newwworld.mod` não repete `max num attack slots`, e procurar lá devolve
   None. O jogo mescla campo a campo; aqui é o mesmo.
2. Com um overhaul ativo (Genesis), o valor que vale no jogo não é o vanilla.
   Gerar mod a partir do vanilla sobrescreve o rebalanceamento do overhaul.
"""
import os

import caminhos as loc
import kenshimod as km


def arquivos(excluir=()):
    """base + mods ativos na ordem do mods.cfg, menos os excluídos"""
    saida = list(loc.arquivos_base())
    import conflitos
    for c in conflitos.ordem_real():
        if os.path.basename(c) not in excluir:
            saida.append(c)
    return saida


def indexar(lista=None):
    """strid -> (registro com campos MESCLADOS, arquivo de ORIGEM do registro)

    O arquivo devolvido é onde o registro apareceu pela primeira vez, que é o
    que entra como dependência de um mod que o modifica -- não o sufixo do
    strid, que guarda a origem histórica (`__Fixes.mod`, `Mourn.mod`) e não
    corresponde a arquivo nenhum instalado.
    """
    idx = {}
    for c in (lista if lista is not None else loc.arquivos_base()):
        arq = os.path.basename(c)
        for rec in km.ler(c)["records"]:
            anterior = idx.get(rec["strid"])
            if anterior is None:
                copia = dict(rec)
                for secao, _, _ in km.SECOES:
                    copia[secao] = list(rec[secao])
                copia["extra"] = [(cat, list(it)) for cat, it in rec["extra"]]
                idx[rec["strid"]] = (copia, arq)
                continue
            alvo = anterior[0]
            for secao, _, _ in km.SECOES:
                atual = {k: v for k, v in alvo[secao]}
                atual.update({k: v for k, v in rec[secao]})
                alvo[secao] = list(atual.items())
            cats = {cat: it for cat, it in alvo["extra"]}
            cats.update({cat: list(it) for cat, it in rec["extra"]})
            alvo["extra"] = list(cats.items())
    return idx


def por_nome(idx):
    """(typecode, nome) -> (strid, registro, arquivo de origem)"""
    saida = {}
    for s, (r, arq) in idx.items():
        saida.setdefault((r["typecode"], km.t(r["name"])), (s, r, arq))
    return saida


def refs(rec, categoria):
    """a lista de referências de uma categoria, ou [] se não existe"""
    for cat, itens in rec["extra"]:
        if km.t(cat) == categoria:
            return list(itens)
    return []


def modificacao(base_rec):
    """registro que MODIFICA um existente: sem campo nenhum ainda.

    Leva só o que for adicionado depois, porque o Kenshi mescla por campo --
    alterar um campo não desfaz o que outro mod fez no resto do registro.
    """
    rec = {
        "instance_count": 0,
        "typecode": base_rec["typecode"],
        "id": 0,
        "name": base_rec["name"],
        "strid": base_rec["strid"],
        "mod_data_type": -2147483647,
        "extra": [],
        "instances": [],
    }
    for secao, _, _ in km.SECOES:
        rec[secao] = []
    return rec


def cabecalho(nome, descricao, registros, idx, autor="kenshi-modkit"):
    """monta o dicionário do mod, com as dependências saindo dos registros"""
    origens = {idx[r["strid"]][1] for r in registros if r["strid"] in idx}
    return {
        "filetype": 16,
        "mod_version": 1,
        "author": km.b(autor),
        "description": km.b(descricao),
        "dependencies": km.b(",".join(sorted(origens))),
        "references": b"",
        # sem semântica levantada (ver FORMATO.md); valor de um mod publicado
        # que o jogo aceita
        "unknown": 1535115,
        "records": registros,
        "tail": b"",
    }
