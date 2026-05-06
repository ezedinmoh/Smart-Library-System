# -*- coding: utf-8 -*-
"""
Utility functions for dashboard operations including:
- PDF report generation
- CSV exports
- Database backups
- Library card generation
- Email notifications
"""

from django.conf import settings
from django.utils import timezone
from django.core.mail import send_mail
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER
from pathlib import Path
from io import BytesIO
from PIL import Image, ImageDraw, ImageFont
import os
import csv
import shutil
from datetime import datetime, timedelta
def generate_library_card(user):
    """
    Generate a beautiful library ID card for a user (National ID style)
    Returns: PIL Image object
    """
    # Card dimensions (credit card ratio)
    width, height = 1012, 638
    
    # Create card background
    card = Image.new('RGB', (width, height), color='white')
    draw = ImageDraw.Draw(card)
    
    # Role-based colors
    role_colors = {
        'admin': '#DC2626',      # Red
        'librarian': '#2563EB',  # Blue
        'student': '#059669',    # Green
    }
    primary_color = role_colors.get(user.role, '#059669')
    
    # Load fonts
    try:
        title_font = ImageFont.truetype("arial.ttf", 48)
        name_font = ImageFont.truetype("arialbd.ttf", 38)
        info_font = ImageFont.truetype("arial.ttf", 26)
        label_font = ImageFont.truetype("arial.ttf", 22)
        small_font = ImageFont.truetype("arial.ttf", 20)
    except:
        title_font = ImageFont.load_default()
        name_font = ImageFont.load_default()
        info_font = ImageFont.load_default()
        label_font = ImageFont.load_default()
        small_font = ImageFont.load_default()
    
    # Header section with gradient-like effect
    header_height = 120
    draw.rectangle([(0, 0), (width, header_height)], fill=primary_color)
    
    # Simple book icon (SVG-like representation)
    icon_x = 80
    icon_y = 35
    icon_size = 50
    # Draw book icon
    draw.rectangle([(icon_x, icon_y), (icon_x + icon_size, icon_y + icon_size)], 
                   outline='white', width=3)
    draw.line([(icon_x + icon_size//2, icon_y), (icon_x + icon_size//2, icon_y + icon_size)], 
              fill='white', width=2)
    
    # Header text
    text_x = icon_x + icon_size + 25
    draw.text((text_x, header_height//2 - 15), "SmartLibrary", 
             fill='white', font=title_font, anchor='lm')
    draw.text((text_x, header_height//2 + 20), "Library Membership Card", 
             fill='white', font=label_font, anchor='lm')
    
    # Profile picture section (rectangular with rounded corners)
    profile_y = header_height + 40
    profile_width = 180
    profile_height = 200
    profile_x = 70
    
    # Try to load user's profile picture
    profile_img = None
    if hasattr(user, 'profile') and user.profile.profile_picture:
        try:
            storage = user.profile.profile_picture.storage
            is_cloudinary = 'cloudinary' in type(storage).__module__.lower()

            if is_cloudinary:
                # Fetch from Cloudinary URL
                import requests as req_lib
                response = req_lib.get(user.profile.profile_picture.url, timeout=10)
                if response.status_code == 200:
                    from io import BytesIO
                    profile_img = Image.open(BytesIO(response.content))
                else:
                    profile_img = None
            else:
                profile_img = Image.open(user.profile.profile_picture.path)
            # Resize to fit rectangle
            profile_img = profile_img.convert('RGB')
            profile_img = profile_img.resize((profile_width, profile_height), Image.Resampling.LANCZOS)
            
            # Create rounded rectangle mask
            mask = Image.new('L', (profile_width, profile_height), 0)
            mask_draw = ImageDraw.Draw(mask)
            mask_draw.rounded_rectangle([(0, 0), (profile_width, profile_height)], radius=15, fill=255)
            
            # Create output with rounded corners
            output = Image.new('RGB', (profile_width, profile_height), 'white')
            output.paste(profile_img, (0, 0))
            
            # Paste onto card
            card.paste(output, (profile_x, profile_y), mask)
            
            # Draw border around photo
            draw.rounded_rectangle([(profile_x-3, profile_y-3), 
                                   (profile_x + profile_width+3, profile_y + profile_height+3)], 
                                  radius=15, outline=primary_color, width=4)
        except Exception as e:
            print(f"Error loading profile picture: {e}")
            profile_img = None
    
    # If no profile picture, draw placeholder
    if profile_img is None:
        draw.rounded_rectangle([(profile_x, profile_y), 
                               (profile_x + profile_width, profile_y + profile_height)], 
                              radius=15, fill='#E5E7EB', outline=primary_color, width=4)
        # Draw initial
        initial = user.first_name[0].upper() if user.first_name else user.username[0].upper()
        draw.text((profile_x + profile_width//2, profile_y + profile_height//2), 
                 initial, fill=primary_color, font=title_font, anchor='mm')
    
    # Information section (right side)
    info_x = profile_x + profile_width + 50
    info_y = profile_y + 10
    line_height = 45
    
    # Full Name
    first_name = user.first_name or ""
    last_name = user.last_name or ""
    full_name = f"{first_name} {last_name}".strip() or user.username
    
    draw.text((info_x, info_y), "Name", fill='#6B7280', font=small_font)
    info_y += 28
    draw.text((info_x, info_y), full_name, fill='#1F2937', font=name_font)
    info_y += line_height
    
    # ID Number with LIB- prefix
    draw.text((info_x, info_y), "ID Number", fill='#6B7280', font=small_font)
    info_y += 28
    draw.text((info_x, info_y), f"LIB-{user.id:04d}", fill='#1F2937', font=info_font)
    info_y += line_height
    
    # Role
    draw.text((info_x, info_y), "Role", fill='#6B7280', font=small_font)
    info_y += 28
    role_display = user.get_role_display()
    draw.text((info_x, info_y), role_display, fill='#1F2937', font=info_font)
    info_y += line_height
    
    # Email
    if user.email:
        draw.text((info_x, info_y), "Email", fill='#6B7280', font=small_font)
        info_y += 28
        email_text = user.email if len(user.email) <= 30 else user.email[:27] + "..."
        draw.text((info_x, info_y), email_text, fill='#1F2937', font=label_font)
        info_y += line_height
    
    # Phone Number
    if hasattr(user, 'profile') and hasattr(user.profile, 'phone_number') and user.profile.phone_number:
        draw.text((info_x, info_y), "Phone", fill='#6B7280', font=small_font)
        info_y += 28
        draw.text((info_x, info_y), str(user.profile.phone_number), fill='#1F2937', font=label_font)
        info_y += line_height
    
    # Valid Until (4 years from now)
    valid_until_date = timezone.now() + timedelta(days=365*4)
    valid_until_text = valid_until_date.strftime("%B %Y")
    draw.text((info_x, info_y), "Valid Until", fill='#6B7280', font=small_font)
    info_y += 28
    draw.text((info_x, info_y), valid_until_text, fill='#1F2937', font=info_font)
    
    # Footer section with decorative barcode and QR code
    footer_y = height - 100
    
    # Draw footer background
    draw.rectangle([(0, footer_y), (width, height)], fill='#F9FAFB')
    
    # Decorative barcode (left side)
    barcode_x = 80
    barcode_y = footer_y + 20
    barcode_width = 300
    barcode_height = 50
    
    # Draw barcode lines (decorative)
    line_x = barcode_x
    for i in range(30):
        line_width = 3 if i % 3 == 0 else 2
        draw.rectangle([(line_x, barcode_y), (line_x + line_width, barcode_y + barcode_height)], 
                      fill='#1F2937')
        line_x += line_width + 2
    
    # Barcode number
    draw.text((barcode_x + barcode_width//2, barcode_y + barcode_height + 15), 
             f"LIB{user.id:04d}", fill='#6B7280', font=small_font, anchor='mm')
    
    # Decorative QR code (right side)
    qr_x = width - 150
    qr_y = footer_y + 20
    qr_size = 60
    qr_cell = 12
    
    # Draw QR code grid (decorative pattern)
    for row in range(5):
        for col in range(5):
            # Create a pseudo-random pattern based on user ID
            if (row + col + user.id) % 3 != 0:
                cell_x = qr_x + col * qr_cell
                cell_y = qr_y + row * qr_cell
                draw.rectangle([(cell_x, cell_y), (cell_x + qr_cell - 2, cell_y + qr_cell - 2)], 
                              fill='#1F2937')
    
    # QR code border
    draw.rectangle([(qr_x - 3, qr_y - 3), (qr_x + qr_size + 3, qr_y + qr_size + 3)], 
                  outline='#1F2937', width=2)
    
    # Card border
    draw.rectangle([(0, 0), (width-1, height-1)], outline=primary_color, width=5)
    
    return card

def generate_overdue_report_pdf():
    """Generate PDF report for overdue books"""
    from apps.borrow.models import BorrowRecord
    
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter)
    elements = []
    styles = getSampleStyleSheet()
    
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=24,
        textColor=colors.HexColor('#DC2626'),
        spaceAfter=30,
        alignment=TA_CENTER
    )
    elements.append(Paragraph("Overdue Books Report", title_style))
    elements.append(Paragraph(f"Generated: {timezone.now().strftime('%B %d, %Y %H:%M')}", 
                             styles['Normal']))
    elements.append(Spacer(1, 20))
    
    overdue_records = BorrowRecord.objects.filter(status='overdue').select_related('user', 'book')
    
    if overdue_records.exists():
        data = [['User', 'Book', 'Due Date', 'Days Overdue', 'Fine (ETB)']]
        
        for record in overdue_records:
            days_overdue = record.get_days_overdue()
            data.append([
                record.user.get_full_name() or record.user.username,
                record.book.title[:40],
                record.due_date.strftime('%Y-%m-%d'),
                str(days_overdue),
                f"{record.fine_amount:.2f}"
            ])
        
        table = Table(data, colWidths=[1.5*inch, 2.5*inch, 1*inch, 1*inch, 1*inch])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#DC2626')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 12),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 1), (-1, -1), 10),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.lightgrey]),
        ]))
        elements.append(table)
        
        elements.append(Spacer(1, 20))
        total_fine = sum(r.fine_amount for r in overdue_records)
        summary_text = f"<b>Total Overdue Books:</b> {overdue_records.count()}<br/>"
        summary_text += f"<b>Total Fines:</b> ETB {total_fine:.2f}"
        elements.append(Paragraph(summary_text, styles['Normal']))
    else:
        elements.append(Paragraph("No overdue books found.", styles['Normal']))
    
    doc.build(elements)
    buffer.seek(0)
    return buffer


def generate_fine_report_pdf():
    """Generate PDF report for fines"""
    from apps.borrow.models import BorrowRecord
    from django.db.models import Sum
    
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter)
    elements = []
    styles = getSampleStyleSheet()
    
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=24,
        textColor=colors.HexColor('#2563EB'),
        spaceAfter=30,
        alignment=TA_CENTER
    )
    elements.append(Paragraph("Fine Report", title_style))
    elements.append(Paragraph(f"Generated: {timezone.now().strftime('%B %d, %Y %H:%M')}", 
                             styles['Normal']))
    elements.append(Spacer(1, 20))
    
    fine_records = BorrowRecord.objects.filter(fine_amount__gt=0).select_related('user', 'book')
    
    if fine_records.exists():
        elements.append(Paragraph("<b>Unpaid Fines</b>", styles['Heading2']))
        elements.append(Spacer(1, 10))
        
        unpaid = fine_records.filter(fine_paid=False)
        if unpaid.exists():
            data = [['User', 'Book', 'Due Date', 'Fine (ETB)', 'Status']]
            for record in unpaid:
                data.append([
                    record.user.get_full_name() or record.user.username,
                    record.book.title[:40],
                    record.due_date.strftime('%Y-%m-%d'),
                    f"{record.fine_amount:.2f}",
                    record.get_status_display()
                ])
            
            table = Table(data, colWidths=[1.5*inch, 2.5*inch, 1*inch, 1*inch, 1*inch])
            table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#DC2626')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 11),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('GRID', (0, 0), (-1, -1), 1, colors.black),
                ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
                ('FONTSIZE', (0, 1), (-1, -1), 9),
                ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.lightgrey]),
            ]))
            elements.append(table)
            elements.append(Spacer(1, 20))
        else:
            elements.append(Paragraph("No unpaid fines.", styles['Normal']))
            elements.append(Spacer(1, 20))
        
        total_fines = fine_records.aggregate(Sum('fine_amount'))['fine_amount__sum'] or 0
        unpaid_total = unpaid.aggregate(Sum('fine_amount'))['fine_amount__sum'] or 0
        paid_total = total_fines - unpaid_total
        
        summary_text = f"<b>Total Fines:</b> ETB {total_fines:.2f}<br/>"
        summary_text += f"<b>Unpaid:</b> ETB {unpaid_total:.2f}<br/>"
        summary_text += f"<b>Paid:</b> ETB {paid_total:.2f}"
        elements.append(Paragraph(summary_text, styles['Normal']))
    else:
        elements.append(Paragraph("No fines recorded.", styles['Normal']))
    
    doc.build(elements)
    buffer.seek(0)
    return buffer


def generate_top_books_report_pdf():
    """Generate PDF report for top 10 most borrowed books"""
    from apps.books.models import Book
    
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter)
    elements = []
    styles = getSampleStyleSheet()
    
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=24,
        textColor=colors.HexColor('#059669'),
        spaceAfter=30,
        alignment=TA_CENTER
    )
    elements.append(Paragraph("Top 10 Most Borrowed Books", title_style))
    elements.append(Paragraph(f"Generated: {timezone.now().strftime('%B %d, %Y %H:%M')}", 
                             styles['Normal']))
    elements.append(Spacer(1, 20))
    
    top_books = Book.objects.filter(times_borrowed__gt=0).order_by('-times_borrowed')[:10]
    
    if top_books.exists():
        data = [['Rank', 'Title', 'Author', 'Category', 'Times Borrowed', 'Rating']]
        
        for idx, book in enumerate(top_books, 1):
            data.append([
                str(idx),
                book.title[:40],
                book.author[:30],
                book.category.name if book.category else 'N/A',
                str(book.times_borrowed),
                f"{book.rating:.1f}/5.0"
            ])
        
        table = Table(data, colWidths=[0.5*inch, 2.5*inch, 1.5*inch, 1*inch, 1*inch, 0.8*inch])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#059669')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 11),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 1), (-1, -1), 9),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.lightgrey]),
        ]))
        elements.append(table)
    else:
        elements.append(Paragraph("No borrowing data available.", styles['Normal']))
    
    doc.build(elements)
    buffer.seek(0)
    return buffer


def generate_top_members_report_pdf():
    """Generate PDF report for top 10 most active members"""
    from apps.users.models import User
    from django.db.models import Count
    
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter)
    elements = []
    styles = getSampleStyleSheet()
    
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=24,
        textColor=colors.HexColor('#2563EB'),
        spaceAfter=30,
        alignment=TA_CENTER
    )
    elements.append(Paragraph("Top 10 Most Active Members", title_style))
    elements.append(Paragraph(f"Generated: {timezone.now().strftime('%B %d, %Y %H:%M')}", 
                             styles['Normal']))
    elements.append(Spacer(1, 20))
    
    top_members = User.objects.filter(role='student').annotate(
        borrow_count=Count('borrow_records')
    ).filter(borrow_count__gt=0).order_by('-borrow_count')[:10]
    
    if top_members.exists():
        data = [['Rank', 'Name', 'Email', 'Books Borrowed', 'Books Read', 'Badge']]
        
        for idx, user in enumerate(top_members, 1):
            data.append([
                str(idx),
                user.get_full_name() or user.username,
                user.email[:30] if user.email else 'N/A',
                str(user.borrow_count),
                str(user.profile.total_books_read),
                user.profile.get_badge_display_name()
            ])
        
        table = Table(data, colWidths=[0.5*inch, 1.8*inch, 2*inch, 1*inch, 1*inch, 1.2*inch])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2563EB')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 11),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 1), (-1, -1), 9),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.lightgrey]),
        ]))
        elements.append(table)
    else:
        elements.append(Paragraph("No member activity data available.", styles['Normal']))
    
    doc.build(elements)
    buffer.seek(0)
    return buffer


def create_database_backup():
    """
    Create a PostgreSQL database backup using Django's dumpdata.
    Returns a BytesIO buffer containing the JSON dump — no disk writes.
    Works on both local PostgreSQL and Render/Supabase.
    """
    import subprocess
    import json
    from io import BytesIO
    from django.conf import settings

    db = settings.DATABASES['default']
    engine = db.get('ENGINE', '')

    buffer = BytesIO()

    if 'postgresql' in engine or 'postgis' in engine:
        # PostgreSQL: use pg_dump for a proper SQL backup
        import os
        env = os.environ.copy()

        # Build connection string from settings or DATABASE_URL
        database_url = db.get('OPTIONS', {}).get('DATABASE_URL') or os.environ.get('DATABASE_URL')

        if database_url:
            cmd = ['pg_dump', '--no-owner', '--no-acl', '-F', 'p', database_url]
        else:
            env['PGPASSWORD'] = db.get('PASSWORD', '')
            cmd = [
                'pg_dump',
                '--no-owner', '--no-acl',
                '-F', 'p',
                '-h', db.get('HOST', 'localhost'),
                '-p', str(db.get('PORT', '5432')),
                '-U', db.get('USER', ''),
                db.get('NAME', ''),
            ]

        try:
            result = subprocess.run(
                cmd, env=env,
                capture_output=True, timeout=120
            )
            if result.returncode == 0:
                buffer.write(result.stdout)
                buffer.seek(0)
                return buffer, 'sql'
            else:
                # pg_dump failed — fall back to Django dumpdata
                pass
        except (FileNotFoundError, subprocess.TimeoutExpired):
            # pg_dump not available — fall back to Django dumpdata
            pass

    # Fallback: Django dumpdata (works everywhere, no pg_dump needed)
    from django.core.management import call_command
    import io

    out = io.StringIO()
    call_command(
        'dumpdata',
        '--natural-foreign',
        '--natural-primary',
        '--indent', '2',
        '--exclude', 'contenttypes',
        '--exclude', 'auth.permission',
        '--exclude', 'sessions.session',
        stdout=out
    )
    buffer.write(out.getvalue().encode('utf-8'))
    buffer.seek(0)
    return buffer, 'json'


def send_due_reminder_emails():
    """Send reminder emails for books due soon"""
    from apps.borrow.models import BorrowRecord
    from django.core.mail import send_mass_mail
    
    today = timezone.now().date()
    due_soon = today + timedelta(days=3)
    
    records = BorrowRecord.objects.filter(
        status='borrowed',
        due_date__lte=due_soon,
        due_date__gte=today
    ).select_related('user', 'book')
    
    messages = []
    sent_count = 0
    
    for record in records:
        if record.user.email:
            days_remaining = (record.due_date - today).days
            
            subject = f'Reminder: "{record.book.title}" due in {days_remaining} day(s)'
            
            message = f"""Dear {record.user.get_full_name() or record.user.username},

This is a friendly reminder that the following book is due soon:

Book: {record.book.title}
Author: {record.book.author}
Due Date: {record.due_date.strftime('%B %d, %Y')}
Days Remaining: {days_remaining}

Please return the book on or before the due date to avoid late fees of ETB 2 per day.

Thank you for using Smart Library Management System!

Best regards,
Library Administration
"""
            
            messages.append((
                subject,
                message,
                settings.DEFAULT_FROM_EMAIL,
                [record.user.email]
            ))
            sent_count += 1
    
    if messages:
        import threading
        def _send():
            try:
                from django.db import connections
                for conn in connections.all():
                    conn.close()
                send_mass_mail(messages, fail_silently=True)
            except Exception as e:
                import logging
                logging.getLogger(__name__).error(f"send_due_reminder_emails failed: {e}")
        threading.Thread(target=_send, daemon=True).start()
    
    return sent_count


def send_overdue_notification_emails():
    """Send notification emails for overdue books"""
    from apps.borrow.models import BorrowRecord
    from django.core.mail import send_mass_mail
    
    records = BorrowRecord.objects.filter(status='overdue').select_related('user', 'book')
    
    messages = []
    sent_count = 0
    
    for record in records:
        if record.user.email:
            days_overdue = record.get_days_overdue()
            
            subject = f'OVERDUE: "{record.book.title}" - Fine: ETB {record.fine_amount}'
            
            message = f"""Dear {record.user.get_full_name() or record.user.username},

The following book is OVERDUE:

Book: {record.book.title}
Author: {record.book.author}
Due Date: {record.due_date.strftime('%B %d, %Y')}
Days Overdue: {days_overdue}
Current Fine: ETB {record.fine_amount:.2f}

Please return the book immediately to avoid additional charges.
Fine Rate: ETB 2 per day

You can return the book at the library during operating hours.

Best regards,
Library Administration
"""
            
            messages.append((
                subject,
                message,
                settings.DEFAULT_FROM_EMAIL,
                [record.user.email]
            ))
            sent_count += 1
    
    if messages:
        import threading
        def _send():
            try:
                from django.db import connections
                for conn in connections.all():
                    conn.close()
                send_mass_mail(messages, fail_silently=True)
            except Exception as e:
                import logging
                logging.getLogger(__name__).error(f"send_overdue_notification_emails failed: {e}")
        threading.Thread(target=_send, daemon=True).start()
    
    return sent_count


def log_activity(user, action, description, request=None):
    """Log system activity"""
    from apps.users.models import ActivityLog
    
    ip_address = None
    user_agent = ''
    
    if request:
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip_address = x_forwarded_for.split(',')[0]
        else:
            ip_address = request.META.get('REMOTE_ADDR')
        
        user_agent = request.META.get('HTTP_USER_AGENT', '')[:500]
    
    ActivityLog.objects.create(
        user=user,
        action=action,
        description=description,
        ip_address=ip_address,
        user_agent=user_agent
    )
def _send_notification_email(action, rec, custom_to=None, custom_subject=None, custom_body=None):
    """
    Send a real email via Brevo API.
    action: 'send_due_soon' | 'send_overdue' | 'send_unpaid' | 'send_custom'
    rec: BorrowRecord instance (None for send_custom)
    """
    import os
    import logging
    import threading
    from django.conf import settings as django_settings
    from django.template.loader import render_to_string

    logger = logging.getLogger(__name__)

    brevo_api_key = os.environ.get('BREVO_API_KEY', '')
    if not brevo_api_key:
        logger.error('BREVO_API_KEY not set — cannot send notification center email.')
        raise RuntimeError('BREVO_API_KEY not configured.')

    from_email = django_settings.DEFAULT_FROM_EMAIL
    site_name  = getattr(django_settings, 'SITE_NAME', 'SmartLibrary')
    site_url   = getattr(django_settings, 'SITE_URL', '')

    if action == 'send_custom':
        to_email  = custom_to
        subject   = custom_subject
        html_body = (
            '<div style="font-family:Arial,sans-serif;max-width:600px;'
            'margin:0 auto;padding:24px;">'
            + custom_body.replace('\n', '<br>')
            + '</div>'
        )
        text_body = custom_body

    else:
        user     = rec.user
        book     = rec.book
        to_email = user.email
        if not to_email:
            return

        if action == 'send_due_soon':
            days_remaining = (rec.due_date - timezone.now().date()).days
            from apps.dashboard.models import SystemSettings
            sys_settings = SystemSettings.get_settings()
            ctx = {
                'user': user,
                'book': book,
                'due_date': rec.due_date,
                'days_remaining': days_remaining,
                'fine_per_day': sys_settings.fine_per_day,
                'site_name': site_name,
                'site_url': site_url,
            }
            subject   = f'[{site_name}] Reminder: "{book.title}" is due in {days_remaining} day(s)'
            html_body = render_to_string('emails/book_due_soon.html', ctx)
            text_body = render_to_string('emails/book_due_soon.txt',  ctx)

        elif action == 'send_overdue':
            days_overdue = (timezone.now().date() - rec.due_date).days
            from apps.dashboard.models import SystemSettings
            sys_settings = SystemSettings.get_settings()
            ctx = {
                'user': user,
                'book': book,
                'due_date': rec.due_date,
                'days_overdue': days_overdue,
                'fine_amount': rec.fine_amount,
                'fine_per_day': sys_settings.fine_per_day,
                'site_name': site_name,
                'site_url': site_url,
            }
            subject   = f'[{site_name}] Overdue: "{book.title}" — {days_overdue} day(s) overdue'
            html_body = render_to_string('emails/book_overdue.html', ctx)
            text_body = render_to_string('emails/book_overdue.txt',  ctx)

        elif action == 'send_unpaid':
            days_overdue = max((timezone.now().date() - rec.due_date).days, 0)
            from apps.dashboard.models import SystemSettings
            sys_settings = SystemSettings.get_settings()
            ctx = {
                'user': user,
                'book': book,
                'due_date': rec.due_date,
                'days_overdue': days_overdue,
                'fine_amount': rec.fine_amount,
                'fine_paid': rec.fine_paid,
                'fine_per_day': sys_settings.fine_per_day,
                'site_name': site_name,
                'site_url': site_url,
            }
            subject   = f'[{site_name}] Unpaid Fine: ETB {rec.fine_amount} for "{book.title}"'
            html_body = render_to_string('emails/fine_applied.html', ctx)
            text_body = render_to_string('emails/fine_applied.txt',  ctx)

        else:
            raise ValueError(f'Unknown action: {action}')

    _subject = subject
    _html    = html_body
    _text    = text_body
    _from    = from_email
    _to      = to_email
    _key     = brevo_api_key

    def _send():
        try:
            from django.db import connections
            for conn in connections.all():
                conn.close()

            from django.conf import settings as s
            if not hasattr(s, 'ANYMAIL'):
                s.ANYMAIL = {}
            s.ANYMAIL['BREVO_API_KEY'] = _key

            from anymail.backends.brevo import EmailBackend as BrevoBackend
            from django.core.mail import EmailMultiAlternatives

            backend = BrevoBackend(fail_silently=False)
            msg = EmailMultiAlternatives(
                subject=_subject,
                body=_text,
                from_email=_from,
                to=[_to],
                connection=backend,
            )
            msg.attach_alternative(_html, 'text/html')
            msg.send(fail_silently=False)
            logger.info(f'Notification email sent to {_to}: {_subject!r}')
        except Exception as e:
            logger.error(f'Notification email FAILED to {_to}: {type(e).__name__}: {e}')
            raise

    threading.Thread(target=_send, daemon=True).start()
