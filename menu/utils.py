import logging
from django.conf import settings
from django.utils import timezone

logger = logging.getLogger(__name__)

RESTAURANT_NAME = "The Grand"
RESTAURANT_ADDRESS = "123, Main Street, City"
RESTAURANT_GSTIN = ""

def generate_invoice_text(order):
    items_lines = []
    for i, item in enumerate(order.items.all(), 1):
        amount = item.unit_price * item.quantity
        items_lines.append(
            f"{i:2}. {item.item_name:<30} {item.quantity:2} x ₹{item.unit_price:<7} ₹{amount:>8}"
        )

    items_str = "\n".join(items_lines)

    subtotal = order.total - order.gst_amount
    cgst = order.gst_amount / 2
    sgst = order.gst_amount / 2

    now = timezone.localtime(order.created_at)
    date_str = now.strftime("%d-%b-%Y %I:%M %p")

    invoice = f"""
{'='*48}
          {RESTAURANT_NAME}
          TAX INVOICE
{'='*48}
Order No   : {order.order_id}
Table      : {order.table.number}
Date       : {date_str}
Phone      : {order.phone}
{'='*48}

{'─'*48}
 ITEMS
{'─'*48}
{items_str}

{'─'*48}
Subtotal     : ₹{subtotal:>8.2f}
CGST (2.5%)  : ₹{cgst:>8.2f}
SGST (2.5%)  : ₹{sgst:>8.2f}
{'─'*48}
TOTAL        : ₹{order.total:>8.2f}
{'─'*48}
"""

    if order.utrn:
        invoice += f"UTR No      : {order.utrn}\n"
    if order.payment_method:
        invoice += f"Payment     : {order.payment_method.name}\n"

    invoice += f"""
{RESTAURANT_ADDRESS}
"""
    if RESTAURANT_GSTIN:
        invoice += f"GSTIN: {RESTAURANT_GSTIN}\n"

    invoice += """
      Thank you! Visit Again :)
"""
    return invoice


def generate_whatsapp_invoice(order):
    items_lines = []
    for i, item in enumerate(order.items.all(), 1):
        amount = item.unit_price * item.quantity
        items_lines.append(
            f"{i}. {item.item_name} x{item.quantity} = ₹{amount:.2f}"
        )

    items_str = "\n".join(items_lines)

    subtotal = order.total - order.gst_amount
    cgst = order.gst_amount / 2
    sgst = order.gst_amount / 2

    now = timezone.localtime(order.created_at)
    date_str = now.strftime("%d-%b-%Y %I:%M %p")

    payment_line = ""
    if order.payment_method:
        payment_line = f"Payment: {order.payment_method.name}"
        if order.utrn:
            payment_line += f" (UTR: {order.utrn})"

    msg = f"🧾 *{RESTAURANT_NAME}* 🧾\n"
    msg += f"━━━━━━━━━━━━━━━━━━\n"
    msg += f"*Order:* {order.order_id}\n"
    msg += f"*Table:* {order.table.number}\n"
    msg += f"*Date:* {date_str}\n"
    msg += f"━━━━━━━━━━━━━━━━━━\n\n"
    msg += f"*ITEMS*\n{items_str}\n\n"
    msg += f"Subtotal: ₹{subtotal:.2f}\n"
    msg += f"CGST (2.5%): ₹{cgst:.2f}\n"
    msg += f"SGST (2.5%): ₹{sgst:.2f}\n"
    msg += f"━━━━━━━━━━━━━━━━━━\n"
    msg += f"*TOTAL: ₹{order.total:.2f}*\n"
    msg += f"━━━━━━━━━━━━━━━━━━\n"
    msg += f"{payment_line}\n\n"
    msg += f"{RESTAURANT_ADDRESS}\n"
    msg += f"_Thank you! Visit Again :)_"

    return msg


def send_sms(to_phone, message):
    if not all([settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN, settings.TWILIO_PHONE_NUMBER]):
        logger.warning("Twilio not configured — SMS not sent")
        return False

    try:
        from twilio.rest import Client
        client = Client(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)
        client.messages.create(
            body=message,
            from_=settings.TWILIO_PHONE_NUMBER,
            to=to_phone,
        )
        logger.info(f"SMS sent to {to_phone}")
        return True
    except Exception as e:
        logger.error(f"Failed to send SMS to {to_phone}: {e}")
        return False


def send_whatsapp(to_phone, message):
    if not all([settings.WHATSAPP_ACCESS_TOKEN, settings.WHATSAPP_PHONE_NUMBER_ID]):
        logger.warning("WhatsApp Cloud API not configured — message not sent")
        return False

    import requests

    phone = to_phone.lstrip("+")
    url = f"https://graph.facebook.com/v21.0/{settings.WHATSAPP_PHONE_NUMBER_ID}/messages"
    headers = {
        "Authorization": f"Bearer {settings.WHATSAPP_ACCESS_TOKEN}",
        "Content-Type": "application/json",
    }
    payload = {
        "messaging_product": "whatsapp",
        "recipient_type": "individual",
        "to": phone,
        "type": "text",
        "text": {"preview_url": False, "body": message},
    }

    try:
        resp = requests.post(url, json=payload, headers=headers, timeout=15)
        resp.raise_for_status()
        logger.info(f"WhatsApp message sent to {phone}")
        return True
    except Exception as e:
        logger.error(f"Failed to send WhatsApp to {phone}: {e}")
        return False


def notify_invoice(order):
    invoice_text = generate_invoice_text(order)
    whatsapp_msg = generate_whatsapp_invoice(order)

    results = {}

    if order.phone:
        results["sms"] = send_sms(order.phone, invoice_text)
        results["whatsapp"] = send_whatsapp(order.phone, whatsapp_msg)

    return results
