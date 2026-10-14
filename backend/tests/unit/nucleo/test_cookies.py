"""Cookies apagados (DTEC 023; CS-003): a resposta não pode variar com o relógio."""

from __future__ import annotations

import time

import pytest
from starlette.responses import Response

from app.nucleo.configuracao import Configuracao
from app.nucleo.cookies import apagar_cookies

pytestmark = pytest.mark.unit


def _set_cookie_apos_apagar(configuracao: Configuracao) -> list[str]:
    resposta = Response()
    apagar_cookies(resposta, configuracao)
    return resposta.headers.getlist("set-cookie")


def test_cookies_apagados_nao_dependem_do_instante_da_resposta(
    configuracao: Configuracao, monkeypatch: pytest.MonkeyPatch
) -> None:
    # Duas respostas em segundos diferentes: um `Expires` calculado a partir de "agora" faria o
    # cabeçalho mudar e o teste de respostas idênticas da entrada oscilaria na virada do segundo.
    monkeypatch.setattr(time, "time", lambda: 1_800_000_000.0)
    antes = _set_cookie_apos_apagar(configuracao)
    monkeypatch.setattr(time, "time", lambda: 1_800_000_001.0)
    depois = _set_cookie_apos_apagar(configuracao)
    assert antes == depois


def test_cookies_apagados_expiram_no_passado_e_com_max_age_zero(
    configuracao: Configuracao,
) -> None:
    cookies = _set_cookie_apos_apagar(configuracao)
    assert len(cookies) == 2
    for bruto in cookies:
        minusculo = bruto.lower()
        assert "max-age=0" in minusculo
        assert "expires=thu, 01 jan 1970 00:00:00 gmt" in minusculo
