# Bot de Estado de Cuenta (extraccion + preparacion para WhatsApp)

## Resumen del proceso original (manual)

El proceso que se automatiza era, hasta ahora, completamente manual dentro del ERP
(Odoo):

1. Entrar a Ventas > Pedidos > Tableros Usuario.
2. Por cada Agente (vendedor) de la empresa, entrar a "Ver Facturas Vencidas".
3. Dentro de cada agente, ir cliente por cliente (en el orden en que aparecen).
4. Para cada cliente, marcar todas sus facturas vencidas o por vencer.
5. Imprimir esas facturas con la opcion "Sabanilla" (el estado de cuenta del
   cliente), exportar a PDF y guardarlo.
6. Enviar ese PDF por WhatsApp al cliente, junto con un aviso.
7. Repetir cliente por cliente, agente por agente (Agente 1, Agente 2, Rene Sanchez, etc.).

Reglas de negocio identificadas:
- El estado de cuenta siempre debe incluir: numero de factura, fecha de
  vencimiento y monto a liquidar.
- Alertas de facturas por vencer: un dia antes del vencimiento y el dia
  exacto del vencimiento, a las 9:00 am.
- Si el vencimiento cae en sabado o domingo, la alerta se manda viernes y
  lunes (no en fin de semana).
- Todos los lunes se manda, ademas, el estado de cuenta completo a TODOS
  los clientes (no solo a los que tienen facturas por vencer).
- Si el cliente responde "ya pague" o envia una ficha de pago, el sistema
  debe preguntar a que factura corresponde (logica conversacional - hoy
  vive en el servicio de WhatsApp, no en este bot).

## Alcance de este bot (lo que se construyo)

Por decision del usuario, el alcance actual es el siguiente (mas simple que
el listado de reglas completo arriba, pensado para arrancar ya):

- Cada lunes a las 9:00 am, el bot se conecta al ERP y busca **todos los
  clientes que tengan facturas de venta sin pagar** (saldo > 0).
- Por cada cliente, genera el mismo PDF de "Estado de Cuenta" (la
  "Sabanilla") que antes se generaba a mano.
- Guarda el PDF y un registro con el numero de telefono del cliente,
  listo para que el servicio de WhatsApp que ya existe lo tome y lo envie.
- El bot **no envia nada por WhatsApp**: solo deja todo preparado.

Las reglas de "un dia antes / el dia del vencimiento / viernes-lunes en fin
de semana" y la logica de "a que factura corresponde tu pago" quedaron
fuera de este bot por ahora; viven en el servicio de mensajeria o se pueden
agregar despues si se necesitan.

## Como funciona tecnicamente

El sitio es Odoo 14. En vez de simular clics en pantalla, el bot habla
directo con la base de datos via la API de Odoo (XML-RPC), que es mas
rapido y no se rompe si cambia el diseno de una pantalla:

1. `odoo_client.py` - se conecta dos veces: por XML-RPC (para leer datos y
   crear el "wizard" del reporte) y por sesion web normal (necesario porque
   el PDF del reporte solo se puede descargar con una sesion de navegador,
   no por XML-RPC).
2. `extractor.py` - busca todas las facturas de venta (`account.move`)
   posteadas, no pagadas, con saldo mayor a cero, y las agrupa por cliente.
   Para cada cliente obtiene su telefono (`mobile` o `phone`).
3. `bot.py` - por cada cliente con telefono, crea el wizard de
   "Estado de Cuenta" (`account.invoice.statement.wizard`, el mismo que usa
   el boton "Sabanilla"), descarga el PDF, lo guarda en `output/pdfs/`, y
   escribe `output/queue.json` con el numero, la ruta del PDF y el detalle
   de facturas de cada cliente.

## Conectar con el servicio de WhatsApp

El bot deja todo listo en `output/queue.json`, con esta forma:

```json
[
  {
    "partner_id": 134931,
    "partner_name": "MOSTRADOR BUGARIN",
    "phone": "...",
    "pdf_path": "C:\\...\\output\\pdfs\\134931_2026-06-30.pdf",
    "invoices": [
      {"number": "FAGBG/1011204", "due_date": "2026-04-01", "amount": 1440.06}
    ],
    "total_due": 1440.06,
    "generated_at": "2026-06-30"
  }
]
```

El servicio de mensajeria solo necesita leer ese archivo (o que se le
indique como conectarse a el: leerlo de esa carpeta, o si se prefiere se
puede cambiar `bot.py` para que en vez de escribir un archivo, haga una
llamada HTTP a un endpoint del bot de WhatsApp - el lugar exacto a cambiar
es la funcion `run()` en `bot.py`.

## Configuracion (.env)

Copiar `.env.example` a `.env` y llenarlo con los datos reales del ERP
(no se incluyen en el repositorio por seguridad):

```
ODOO_URL=
ODOO_DB=
ODOO_USER=
ODOO_PASSWORD=
```

El archivo `.env` con los datos reales **nunca debe subirse al repositorio**
(ya esta en `.gitignore`). Usar una cuenta dedicada al bot, no la de pruebas.

## Como correrlo manualmente

```
py "C:\Users\8A\Documents\Bot estado de cuenta\bot.py"
```

## Programacion automatica

Ya se creo una Tarea Programada de Windows llamada **"BotEstadoDeCuenta"**
que corre automaticamente todos los lunes a las 9:00 am en esta PC.

Para verla o cambiarla: Programador de Tareas de Windows > Biblioteca del
Programador de Tareas > BotEstadoDeCuenta.

Cuando se mude a un servidor (como se planeo: "primero local, luego a un
servidor"), el mismo `bot.py` se puede programar igual con `cron`:

```
0 9 * * 1 /usr/bin/python3 /ruta/al/bot.py
```

## Pendiente / siguientes pasos sugeridos

- Confirmar con un cliente real que el PDF generado coincide exactamente
  con lo que se manda hoy a mano (ya se valido el formato, falta validar
  un cliente con saldo real en una corrida completa).
- Decidir el mecanismo final de entrega al bot de WhatsApp (carpeta,
  base de datos o llamada API) cuando se tenga esa informacion.
- Si se quiere recuperar las reglas completas (alertas un dia antes/el
  dia del vencimiento, ajuste de fin de semana, pregunta de "a que
  factura corresponde tu pago"), se pueden agregar como una segunda fase.
