"""Testes simples da amostra sintética; não substituem testes de integração do LLM."""
from pathlib import Path
import csv
import unittest

CAMINHO = Path(__file__).resolve().parents[1] / "data" / "amostra_leituras.csv"

class TestAmostra(unittest.TestCase):
    def test_amostra_presente_e_nao_vazia(self):
        self.assertTrue(CAMINHO.is_file())
        with CAMINHO.open(encoding="utf-8-sig", newline="") as arquivo:
            registros = list(csv.DictReader(arquivo))
        self.assertGreater(len(registros), 0)

    def test_delta_t_consistente(self):
        with CAMINHO.open(encoding="utf-8-sig", newline="") as arquivo:
            for leitura in csv.DictReader(arquivo):
                esperado = float(leitura["temperatura_saida"]) - float(leitura["temperatura_entrada"])
                observado = float(leitura["delta_t"])
                self.assertAlmostEqual(observado, esperado, places=2)

    def test_fluxo_zero_quando_aquecendo_ou_maturando(self):
        with CAMINHO.open(encoding="utf-8-sig", newline="") as arquivo:
            for leitura in csv.DictReader(arquivo):
                if leitura["estado_processo"] in {"AQUECENDO", "MATURANDO"}:
                    self.assertEqual(float(leitura["vazao_l_min"]), 0.0)

if __name__ == "__main__":
    unittest.main()
