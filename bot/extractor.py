"""Extrae, agrupados por cliente, los datos de facturas con saldo pendiente
(numero de factura, fecha de vencimiento, monto), igual que se ve en
'Ver Facturas Vencidas' dentro del ERP.
"""
from collections import defaultdict

OPEN_INVOICE_DOMAIN = [
    ["move_type", "=", "out_invoice"],
    ["state", "=", "posted"],
    ["payment_state", "not in", ["paid", "reversed"]],
    ["amount_residual", ">", 0],
]


def get_clients_with_open_invoices(client):
    move_ids = client.execute("account.move", "search", OPEN_INVOICE_DOMAIN)
    moves = client.execute(
        "account.move", "read", move_ids,
        fields=["name", "invoice_date_due", "amount_residual", "partner_id", "invoice_user_id"],
    )

    by_partner = defaultdict(list)
    for m in moves:
        partner_id = m["partner_id"][0]
        by_partner[partner_id].append(m)

    partner_ids = list(by_partner.keys())
    partners = client.execute(
        "res.partner", "read", partner_ids,
        fields=["name", "mobile", "phone"],
    )
    partner_by_id = {p["id"]: p for p in partners}

    clients = []
    for partner_id, invoices in by_partner.items():
        partner = partner_by_id.get(partner_id, {})
        phone = (partner.get("mobile") or partner.get("phone") or "").strip()
        clients.append({
            "partner_id": partner_id,
            "partner_name": partner.get("name", ""),
            "phone": phone,
            "invoices": [
                {
                    "number": inv["name"],
                    "due_date": inv["invoice_date_due"],
                    "amount": inv["amount_residual"],
                }
                for inv in invoices
            ],
            "total_due": round(sum(inv["amount_residual"] for inv in invoices), 2),
        })
    return clients
