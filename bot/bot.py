"""Bot de extraccion de estado de cuenta (la 'sabanilla').

Cada corrida:
  1. Se conecta al ERP (Odoo) usando las credenciales del .env local.
  2. Busca todos los clientes con facturas de venta sin pagar (saldo > 0).
  3. Genera el PDF de estado de cuenta de cada cliente (el mismo reporte
     que se imprime manualmente como 'Sabanilla').
  4. Guarda los PDFs en output/pdfs/ y deja un registro en output/queue.json
     con el numero de telefono y la ruta del PDF, listo para que el bot
     de WhatsApp lo tome y lo envie.

No envia nada por si mismo: solo prepara todo para el envio.
"""
import json
import os
from datetime import date

from odoo_client import OdooClient
from extractor import get_clients_with_open_invoices

BASE_DIR = os.path.dirname(__file__)
ENV_PATH = os.path.join(BASE_DIR, ".env")
OUTPUT_DIR = os.path.join(BASE_DIR, "output")
PDF_DIR = os.path.join(OUTPUT_DIR, "pdfs")
QUEUE_PATH = os.path.join(OUTPUT_DIR, "queue.json")

STATEMENT_DATE_FROM = "2000-01-01"  # suficientemente viejo para no perder facturas antiguas sin pagar


def build_wizard_id(client, partner_id, date_to):
    return client.execute(
        "account.invoice.statement.wizard", "create",
        {
            "partner_id": partner_id,
            "is_open": True,
            "move_type": "out_invoice",
            "date_from": STATEMENT_DATE_FROM,
            "date_to": date_to,
            "show_partners": True,
        },
    )


def run():
    os.makedirs(PDF_DIR, exist_ok=True)
    today = date.today().isoformat()

    client = OdooClient(ENV_PATH)
    clients = get_clients_with_open_invoices(client)
    print(f"Clientes con saldo pendiente: {len(clients)}")

    queue = []
    for c in clients:
        if not c["phone"]:
            print(f"  [SIN TELEFONO] {c['partner_name']} (id {c['partner_id']}) - se omite")
            continue

        wizard_id = build_wizard_id(client, c["partner_id"], today)
        pdf_bytes = client.download_statement_pdf(wizard_id)

        pdf_filename = f"{c['partner_id']}_{today}.pdf"
        pdf_path = os.path.join(PDF_DIR, pdf_filename)
        with open(pdf_path, "wb") as f:
            f.write(pdf_bytes)

        queue.append({
            "partner_id": c["partner_id"],
            "partner_name": c["partner_name"],
            "phone": c["phone"],
            "pdf_path": pdf_path,
            "invoices": c["invoices"],
            "total_due": c["total_due"],
            "generated_at": today,
        })
        print(f"  OK: {c['partner_name']} -> {pdf_filename} (saldo {c['total_due']})")

    with open(QUEUE_PATH, "w", encoding="utf-8") as f:
        json.dump(queue, f, ensure_ascii=False, indent=2)

    print(f"\nListo. {len(queue)} estados de cuenta preparados en {QUEUE_PATH}")


if __name__ == "__main__":
    run()
