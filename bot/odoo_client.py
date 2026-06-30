"""Cliente minimo para hablar con Odoo: login XML-RPC (para leer/crear datos)
y login por sesion web (necesario para descargar el PDF del reporte, porque
el endpoint /report/pdf/ requiere cookie de sesion, no funciona por XML-RPC).
"""
import json
import re
import urllib.parse
import xmlrpc.client

import requests

REPORT_TECHNICAL_NAME = "pos_8a_standard.report_invoice_statement_wizard"  # "Sabanilla" / Estado de Cuenta


def load_env(path):
    data = {}
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            k, v = line.split("=", 1)
            data[k.strip()] = v.strip()
    return data


class OdooClient:
    def __init__(self, env_path):
        env = load_env(env_path)
        self.url = env["ODOO_URL"]
        self.db = env["ODOO_DB"]
        self.user = env["ODOO_USER"]
        self.password = env["ODOO_PASSWORD"]

        common = xmlrpc.client.ServerProxy(f"{self.url}/xmlrpc/2/common")
        self.uid = common.login(self.db, self.user, self.password)
        if not self.uid:
            raise RuntimeError("Login XML-RPC fallo: revisa ODOO_DB/ODOO_USER/ODOO_PASSWORD en .env")
        self.models = xmlrpc.client.ServerProxy(f"{self.url}/xmlrpc/2/object")

        self.session = requests.Session()
        self._web_login()

    def execute(self, model, method, *args, **kwargs):
        return self.models.execute_kw(self.db, self.uid, self.password, model, method, list(args), kwargs)

    def _web_login(self):
        r = self.session.get(f"{self.url}/web/login")
        csrf = re.search(r'name="csrf_token" value="([^"]+)"', r.text).group(1)
        self.session.post(f"{self.url}/web/login", data={
            "csrf_token": csrf,
            "login": self.user,
            "password": self.password,
            "redirect": "",
        })

    def download_statement_pdf(self, wizard_id):
        """Crea el PDF de estado de cuenta (la 'sabanilla') para un wizard ya creado."""
        wform = self.execute("account.invoice.statement.wizard", "read", [wizard_id])[0]
        options = json.dumps({"form": wform})
        pdf_url = f"{self.url}/report/pdf/{REPORT_TECHNICAL_NAME}/{wizard_id}?options={urllib.parse.quote(options)}"
        r = self.session.get(pdf_url)
        if r.content[:4] != b"%PDF":
            raise RuntimeError(f"El servidor no devolvio un PDF valido para wizard_id={wizard_id} (status {r.status_code})")
        return r.content
