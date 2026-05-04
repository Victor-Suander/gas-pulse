import pandas as pd

from app.services.relatorio_service import gerar_corpo_email


def test_gerar_corpo_email_formata_moeda_no_padrao_brasileiro():
    vendas_df = pd.DataFrame(
        [
            {
                "filial_nome": "Posto Centro",
                "produto_canonico": "Gasolina Comum",
                "valor_total_brl": 1234.56,
            },
            {
                "filial_nome": "Posto Norte",
                "produto_canonico": "Etanol",
                "valor_total_brl": 98765.43,
            },
        ]
    )
    resumo_emails_df = pd.DataFrame(
        [
            {
                "alertas": "Sem alertas relevantes",
            }
        ]
    )

    corpo = gerar_corpo_email(
        vendas_df,
        resumo_emails_df,
        {
            "vendas": "output/vendas.csv",
            "emails": "output/emails.csv",
            "ranking": "output/ranking.csv",
        },
    )

    assert "Total geral faturado: R$ 99.999,99" in corpo
    assert "Ranking por filial:\n  - Posto Norte: R$ 98.765,43\n  - Posto Centro: R$ 1.234,56" in corpo
    assert "Ranking por produto:\n  - Etanol: R$ 98.765,43\n  - Gasolina Comum: R$ 1.234,56" in corpo
