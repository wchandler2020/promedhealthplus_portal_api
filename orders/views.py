from django.shortcuts import render
from rest_framework import generics, status, permissions
from django.conf import settings
from django.template.loader import render_to_string
from weasyprint import HTML
from io import BytesIO
from django.core.mail import EmailMessage
import orders.serializers as api_serializers

class CreateOrderView(generics.CreateAPIView):
    serializer_class = api_serializers.OrderSerializer
    permission_classes = [permissions.IsAuthenticated]

    def create(self, request, *args, **kwargs):
        request.data['provider'] = request.user.id
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)

        order = serializer.instance
        self.send_invoice_email(order)

        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def send_invoice_email(self, order):
        sales_rep_email = order.provider.profile.sales_rep.email
        recipient_list = [
            order.provider.email,
            sales_rep_email,
            settings.DEFAULT_FROM_EMAIL
        ]

        subject = f"Invoice for Order #{order.id}"

        # Render HTML
        html_content = render_to_string('orders/order_invoice.html', {'order': order})

        # Generate PDF
        pdf_file = BytesIO()
        HTML(string=html_content).write_pdf(pdf_file)
        pdf_file.seek(0)

        # Email with attachment
        email = EmailMessage(
            subject=subject,
            body="Please find attached the invoice for your recent order.",
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=recipient_list,
        )
        email.attach(f"invoice_order_{order.id}.pdf", pdf_file.read(), 'application/pdf')
        email.send(fail_silently=False)
