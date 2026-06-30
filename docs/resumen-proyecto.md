# Resumen del proyecto

Sistema tipo CRM que conecta el **ERP** de la empresa con **WhatsApp** para automatizar el envío de
estados de cuenta y alertas de facturas por vencer a los clientes.

## Objetivo

Eliminar el proceso manual actual (extraer reportes del ERP, generar PDF e imprimir uno por uno
para cada cliente y agente) y automatizar:

1. El aviso de facturas próximas a vencer / vencidas.
2. El envío semanal del estado de cuenta completo a todos los clientes.
3. La conciliación de pagos cuando el cliente responde por WhatsApp.

## Componentes

- **ERP** (Odoo, acceso por portal web propio de la empresa): fuente de los datos de facturación
  (clientes, facturas, fechas de vencimiento, montos).
- **Integración WhatsApp**: canal de salida para alertas y estados de cuenta, y canal de entrada
  para respuestas de los clientes (confirmaciones de pago, comprobantes).
- **Motor de reglas / scheduler**: calcula a quién, qué y cuándo enviar.
- **Bot de respuestas**: interpreta respuestas de clientes y las asocia a una factura.

## Tipos de mensajes

### 1. Alerta de factura por vencer

- Se envía **solo** a clientes que tienen facturas próximas a vencer o vencidas.
- Contenido obligatorio: **fecha de vencimiento**, **número de factura** y **monto a liquidar**.
- Reglas de envío:
  - Un día antes del vencimiento.
  - El mismo día del vencimiento.
  - Si el vencimiento cae **sábado**, la alerta se envía el **viernes**.
  - Si el vencimiento cae **domingo**, la alerta se envía el **viernes** y también el **lunes**.
- Hora de envío: **9:00 am**.

### 2. Estado de cuenta semanal

- Se envía **todos los lunes** a **todos los clientes** (tengan o no facturas por vencer).
- Mismo contenido base: fecha de vencimiento, número de factura y monto a liquidar de cada factura
  pendiente.
- Hora de envío: **9:00 am**.

## Conciliación de pagos por WhatsApp

Cuando un cliente responde indicando que **ya pagó** (texto tipo "ya está pagado") o envía una
**imagen/comprobante de pago**, el sistema debe:

1. Detectar que la respuesta corresponde a un pago.
2. Preguntar al cliente a **qué factura** corresponde el pago (si tiene más de una factura
   pendiente).
3. Registrar la respuesta para que el equipo administrativo concilie el pago contra el ERP.

## Proceso actual de extracción de datos del ERP (manual, a automatizar)

> Este es el flujo que se hace hoy a mano y que el sistema debe reemplazar/automatizar.

1. Ingresar al portal web del ERP con el usuario y contraseña correspondientes.
2. Ir a **Ventas** → menú **Pedidos** → **Tableros usuarios**.
3. Entrar por **Agente**.
4. Hacer clic en **Ver Facturas Vencidas**.
5. Seleccionar cada cliente, en orden, dando clic una sola vez.
6. Para cada cliente, marcar el checkbox de **cada factura** vencida/pendiente.
7. Ir a **Imprimir** (botón superior) → seleccionar **Vainilla** → **Imprimir** → destino **PDF** →
   **Guardar**.
8. Enviar el PDF generado por WhatsApp al cliente como su estado de cuenta.
9. Usar las flechas de navegación (arriba a la derecha) para confirmar que no queden más clientes
   con facturas pendientes en ese agente.
10. Repetir el proceso completo para cada agente: **Agente 1**, **Agente 2** y **Rene Sánchez**.

El mismo flujo aplica tanto para ver las facturas **a vencer** como las **ya vencidas**.

### Nota de seguridad

Las credenciales del ERP usadas para el acceso manual **no deben quedar en el código ni en el
repositorio**: deben guardarse como variables de entorno o en un gestor de secretos, y se debe usar
un usuario con permisos mínimos (idealmente uno dedicado a la integración, distinto del de pruebas).

## Preguntas abiertas / decisiones pendientes

- ¿Qué API de WhatsApp se usará (WhatsApp Business Cloud API de Meta, Twilio, u otro BSP)?
- ¿El ERP expone alguna API/reporte exportable, o la extracción debe hacerse por scraping/RPA del
  panel web descrito arriba?
- ¿Cómo se identifica el número de WhatsApp de cada cliente en el ERP?
- ¿Qué pasa si un cliente tiene varias facturas por vencer el mismo día? (formato del mensaje:
  ¿una alerta por factura o un resumen agrupado?)
- ¿Quién concilia manualmente el pago reportado por el cliente, y dónde queda registrado
  (ERP, planilla, base de datos propia)?
- Zona horaria a usar para la regla de las 9:00 am.
