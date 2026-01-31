"""
PDF Generator Service - توليد ملفات PDF لطلبات عروض الأسعار
"""
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm, mm
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.enums import TA_RIGHT, TA_CENTER, TA_LEFT
from io import BytesIO
from datetime import datetime, timezone
from typing import Dict, Any, Optional, List
import os

# Import Arabic text processing libraries
try:
    import arabic_reshaper
    from bidi.algorithm import get_display
    ARABIC_SUPPORT = True
except ImportError:
    ARABIC_SUPPORT = False

# Try to register Arabic font
try:
    # Check for common Arabic font paths
    arabic_font_paths = [
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/usr/share/fonts/truetype/freefont/FreeSans.ttf",
        "/app/backend/fonts/NotoSansArabic-Regular.ttf",
        "fonts/NotoSansArabic-Regular.ttf"
    ]
    
    font_registered = False
    for font_path in arabic_font_paths:
        if os.path.exists(font_path):
            pdfmetrics.registerFont(TTFont('Arabic', font_path))
            font_registered = True
            break
    
    if not font_registered:
        # Use default font
        ARABIC_FONT = 'Helvetica'
    else:
        ARABIC_FONT = 'Arabic'
except:
    ARABIC_FONT = 'Helvetica'


class RFQPDFGenerator:
    """Generate PDF for RFQ"""
    
    def __init__(self):
        self.styles = getSampleStyleSheet()
        self._setup_styles()
    
    def _setup_styles(self):
        """Setup custom styles for Arabic text"""
        # Title style
        self.title_style = ParagraphStyle(
            'ArabicTitle',
            parent=self.styles['Heading1'],
            fontName=ARABIC_FONT,
            fontSize=18,
            alignment=TA_CENTER,
            spaceAfter=20,
            textColor=colors.HexColor('#1a365d')
        )
        
        # Subtitle style
        self.subtitle_style = ParagraphStyle(
            'ArabicSubtitle',
            parent=self.styles['Heading2'],
            fontName=ARABIC_FONT,
            fontSize=14,
            alignment=TA_RIGHT,
            spaceAfter=10,
            textColor=colors.HexColor('#2d3748')
        )
        
        # Normal text style
        self.normal_style = ParagraphStyle(
            'ArabicNormal',
            parent=self.styles['Normal'],
            fontName=ARABIC_FONT,
            fontSize=11,
            alignment=TA_RIGHT,
            spaceAfter=5
        )
        
        # Table header style
        self.header_style = ParagraphStyle(
            'TableHeader',
            parent=self.styles['Normal'],
            fontName=ARABIC_FONT,
            fontSize=10,
            alignment=TA_CENTER,
            textColor=colors.white
        )
    
    def _process_arabic(self, text: str) -> str:
        """Process Arabic text for proper RTL display in PDF"""
        if not text:
            return ""
        
        text = str(text)
        
        # Check if text contains Arabic characters
        has_arabic = any('\u0600' <= c <= '\u06FF' or '\u0750' <= c <= '\u077F' for c in text)
        
        if not has_arabic:
            return text
        
        if ARABIC_SUPPORT:
            try:
                # Reshape Arabic characters to connect properly
                reshaped_text = arabic_reshaper.reshape(text)
                # Apply BiDi algorithm for proper RTL display
                bidi_text = get_display(reshaped_text)
                return bidi_text
            except Exception as e:
                # Fallback to simple reverse if reshaping fails
                return text[::-1]
        else:
            # Fallback to simple reverse if libraries not available
            return text[::-1]
    
    def _get_logo_image(self, company_settings: Optional[Dict[str, Any]], max_width: float = 4*cm) -> Optional[Image]:
        """Get logo image from base64 or file path"""
        if not company_settings:
            return None
        
        logo_data = company_settings.get('company_logo_base64') or company_settings.get('company_logo')
        if not logo_data:
            return None
        
        try:
            # Check if it's base64 data
            if logo_data.startswith('data:'):
                # Extract base64 content
                import re
                match = re.match(r'data:image/\w+;base64,(.+)', logo_data)
                if match:
                    image_data = base64.b64decode(match.group(1))
                    logo_buffer = BytesIO(image_data)
                    img = Image(logo_buffer)
                    
                    # Scale image to fit
                    aspect = img.imageHeight / img.imageWidth if img.imageWidth > 0 else 1
                    img.drawWidth = min(max_width, img.imageWidth)
                    img.drawHeight = img.drawWidth * aspect
                    
                    return img
            else:
                # Try to load from file path
                import os
                file_path = logo_data.replace('/api/v2/sysadmin/uploads/', '')
                file_path = logo_data.replace('/uploads/', '')
                
                upload_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'uploads')
                full_path = os.path.join(upload_dir, os.path.basename(file_path))
                
                if os.path.exists(full_path):
                    img = Image(full_path)
                    aspect = img.imageHeight / img.imageWidth if img.imageWidth > 0 else 1
                    img.drawWidth = min(max_width, img.imageWidth)
                    img.drawHeight = img.drawWidth * aspect
                    return img
        except Exception as e:
            print(f"Error loading logo: {e}")
        
        return None
    
    def generate_rfq_pdf(
        self,
        rfq_data: Dict[str, Any],
        company_settings: Optional[Dict[str, Any]] = None
    ) -> BytesIO:
        """Generate PDF for RFQ"""
        buffer = BytesIO()
        
        # Create document
        doc = SimpleDocTemplate(
            buffer,
            pagesize=A4,
            rightMargin=1.5*cm,
            leftMargin=1.5*cm,
            topMargin=2*cm,
            bottomMargin=2*cm
        )
        
        elements = []
        
        # Company Header
        if company_settings:
            company_name = company_settings.get('company_name', 'شركة المشتريات')
            elements.append(Paragraph(self._process_arabic(company_name), self.title_style))
            
            company_address = company_settings.get('company_address', '')
            if company_address:
                elements.append(Paragraph(self._process_arabic(company_address), self.normal_style))
            
            company_phone = company_settings.get('company_phone', '')
            company_email = company_settings.get('company_email', '')
            if company_phone or company_email:
                contact_info = f"{company_phone} | {company_email}".strip(' | ')
                elements.append(Paragraph(contact_info, self.normal_style))
        else:
            elements.append(Paragraph(self._process_arabic("طلب عرض سعر"), self.title_style))
        
        elements.append(Spacer(1, 20))
        
        # RFQ Header
        elements.append(Paragraph(
            self._process_arabic("طلب عرض سعر"),
            ParagraphStyle(
                'RFQTitle',
                parent=self.title_style,
                fontSize=16,
                textColor=colors.HexColor('#2b6cb0')
            )
        ))
        
        elements.append(Spacer(1, 10))
        
        # RFQ Info Table
        rfq_info = [
            [self._process_arabic(rfq_data.get('rfq_number', '')), self._process_arabic('رقم الطلب:')],
            [self._process_arabic(rfq_data.get('title', '')), self._process_arabic('الموضوع:')],
            [rfq_data.get('created_at', '')[:10] if rfq_data.get('created_at') else '', self._process_arabic('التاريخ:')],
            [rfq_data.get('submission_deadline', '')[:10] if rfq_data.get('submission_deadline') else self._process_arabic('غير محدد'), self._process_arabic('آخر موعد للتقديم:')],
            [self._process_arabic(rfq_data.get('project_name', '') or 'غير محدد'), self._process_arabic('المشروع:')],
        ]
        
        info_table = Table(rfq_info, colWidths=[10*cm, 5*cm])
        info_table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (-1, -1), ARABIC_FONT),
            ('FONTSIZE', (0, 0), (-1, -1), 11),
            ('ALIGN', (0, 0), (0, -1), 'LEFT'),
            ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
            ('TEXTCOLOR', (1, 0), (1, -1), colors.HexColor('#4a5568')),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ]))
        
        elements.append(info_table)
        elements.append(Spacer(1, 20))
        
        # Items Table
        elements.append(Paragraph(
            self._process_arabic("الأصناف المطلوبة"),
            self.subtitle_style
        ))
        
        # Table header - بدون السعر التقديري (لا يُرسل للموردين)
        items_header = [
            self._process_arabic('الوحدة'),
            self._process_arabic('الكمية'),
            self._process_arabic('الوصف'),
            self._process_arabic('اسم الصنف'),
            '#'
        ]
        
        items_data = [items_header]
        
        for idx, item in enumerate(rfq_data.get('items', []), 1):
            row = [
                self._process_arabic(item.get('unit', 'قطعة')),
                f"{item.get('quantity', 0):,.0f}",
                self._process_arabic(item.get('description', '') or '-'),
                self._process_arabic(item.get('item_name', '')),
                str(idx)
            ]
            items_data.append(row)
        
        items_table = Table(items_data, colWidths=[2.5*cm, 2*cm, 5*cm, 5.5*cm, 1*cm])
        items_table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (-1, -1), ARABIC_FONT),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2b6cb0')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#e2e8f0')),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
            ('TOPPADDING', (0, 0), (-1, -1), 8),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f7fafc')]),
        ]))
        
        elements.append(items_table)
        elements.append(Spacer(1, 20))
        
        # Terms Section
        if rfq_data.get('payment_terms') or rfq_data.get('delivery_terms') or rfq_data.get('delivery_location'):
            elements.append(Paragraph(
                self._process_arabic("الشروط والأحكام"),
                self.subtitle_style
            ))
            
            if rfq_data.get('delivery_location'):
                elements.append(Paragraph(
                    self._process_arabic(f"مكان التسليم: {rfq_data['delivery_location']}"),
                    self.normal_style
                ))
            
            if rfq_data.get('payment_terms'):
                elements.append(Paragraph(
                    self._process_arabic(f"شروط الدفع: {rfq_data['payment_terms']}"),
                    self.normal_style
                ))
            
            if rfq_data.get('delivery_terms'):
                elements.append(Paragraph(
                    self._process_arabic(f"شروط التسليم: {rfq_data['delivery_terms']}"),
                    self.normal_style
                ))
            
            elements.append(Spacer(1, 10))
        
        # Notes
        if rfq_data.get('notes'):
            elements.append(Paragraph(
                self._process_arabic("ملاحظات:"),
                self.subtitle_style
            ))
            elements.append(Paragraph(
                self._process_arabic(rfq_data['notes']),
                self.normal_style
            ))
            elements.append(Spacer(1, 10))
        
        # Validity
        elements.append(Spacer(1, 20))
        elements.append(Paragraph(
            self._process_arabic(f"مدة صلاحية العرض المطلوبة: {rfq_data.get('validity_period', 30)} يوم"),
            self.normal_style
        ))
        
        # Footer
        elements.append(Spacer(1, 30))
        footer_text = self._process_arabic("نأمل منكم التكرم بإرسال عرض السعر في أقرب وقت ممكن")
        elements.append(Paragraph(footer_text, self.normal_style))
        
        elements.append(Spacer(1, 10))
        elements.append(Paragraph(
            self._process_arabic("مع أطيب التحيات"),
            self.normal_style
        ))
        
        if rfq_data.get('created_by_name'):
            elements.append(Paragraph(
                self._process_arabic(rfq_data['created_by_name']),
                self.normal_style
            ))
        
        # Build PDF
        doc.build(elements)
        buffer.seek(0)
        return buffer
    
    def generate_comparison_pdf(
        self,
        comparison_data: Dict[str, Any],
        company_settings: Optional[Dict[str, Any]] = None
    ) -> BytesIO:
        """Generate PDF for quotation comparison"""
        buffer = BytesIO()
        
        # Create document
        doc = SimpleDocTemplate(
            buffer,
            pagesize=A4,
            rightMargin=1.5*cm,
            leftMargin=1.5*cm,
            topMargin=2*cm,
            bottomMargin=2*cm
        )
        
        elements = []
        
        # Title
        elements.append(Paragraph(
            self._process_arabic("مقارنة عروض الأسعار"),
            self.title_style
        ))
        
        elements.append(Spacer(1, 10))
        
        # RFQ Info
        rfq_number = comparison_data.get('rfq_number', '')
        rfq_title = comparison_data.get('rfq_title', '')
        
        elements.append(Paragraph(
            self._process_arabic(f"رقم طلب عرض السعر: {rfq_number}"),
            self.normal_style
        ))
        
        if rfq_title:
            elements.append(Paragraph(
                self._process_arabic(f"الموضوع: {rfq_title}"),
                self.normal_style
            ))
        
        elements.append(Paragraph(
            self._process_arabic(f"تاريخ التقرير: {datetime.now(timezone.utc).strftime('%Y-%m-%d')}"),
            self.normal_style
        ))
        
        elements.append(Spacer(1, 20))
        
        # Summary section
        summary = comparison_data.get('summary', {})
        if summary:
            elements.append(Paragraph(
                self._process_arabic("ملخص المقارنة"),
                self.subtitle_style
            ))
            
            summary_info = [
                [f"{summary.get('total_quotations', 0)}", self._process_arabic('عدد العروض:')],
                [f"{summary.get('lowest_total', 0):,.2f} ريال", self._process_arabic('أقل إجمالي:')],
                [f"{summary.get('highest_total', 0):,.2f} ريال", self._process_arabic('أعلى إجمالي:')],
            ]
            
            if summary.get('best_supplier'):
                summary_info.append([
                    self._process_arabic(summary.get('best_supplier', '')),
                    self._process_arabic('أفضل مورد:')
                ])
            
            summary_table = Table(summary_info, colWidths=[8*cm, 5*cm])
            summary_table.setStyle(TableStyle([
                ('FONTNAME', (0, 0), (-1, -1), ARABIC_FONT),
                ('FONTSIZE', (0, 0), (-1, -1), 11),
                ('ALIGN', (0, 0), (0, -1), 'LEFT'),
                ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
                ('TEXTCOLOR', (1, 0), (1, -1), colors.HexColor('#4a5568')),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
                ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#f7fafc')),
            ]))
            
            elements.append(summary_table)
            elements.append(Spacer(1, 20))
        
        # Quotations comparison table
        quotations = comparison_data.get('quotations', [])
        if quotations:
            elements.append(Paragraph(
                self._process_arabic("مقارنة العروض"),
                self.subtitle_style
            ))
            
            # Table header
            quote_header = [
                self._process_arabic('الملاحظات'),
                self._process_arabic('الحالة'),
                self._process_arabic('الإجمالي النهائي'),
                self._process_arabic('الضريبة'),
                self._process_arabic('الخصم'),
                self._process_arabic('المورد'),
                '#'
            ]
            
            quote_data = [quote_header]
            
            for idx, q in enumerate(quotations, 1):
                status_text = "الأفضل ✓" if q.get('is_winner') else (
                    "مقبول" if q.get('status') == 'accepted' else 
                    "مرفوض" if q.get('status') == 'rejected' else "قيد المراجعة"
                )
                
                row = [
                    self._process_arabic(q.get('notes', '-') or '-'),
                    self._process_arabic(status_text),
                    f"{q.get('final_amount', 0):,.2f}",
                    f"{q.get('vat_percentage', 15)}%",
                    f"{q.get('discount_percentage', 0)}%",
                    self._process_arabic(q.get('supplier_name', '')),
                    str(idx)
                ]
                quote_data.append(row)
            
            quote_table = Table(quote_data, colWidths=[3*cm, 2*cm, 2.5*cm, 1.5*cm, 1.5*cm, 4*cm, 0.8*cm])
            quote_table.setStyle(TableStyle([
                ('FONTNAME', (0, 0), (-1, -1), ARABIC_FONT),
                ('FONTSIZE', (0, 0), (-1, -1), 9),
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2b6cb0')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#e2e8f0')),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
                ('TOPPADDING', (0, 0), (-1, -1), 6),
                ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f7fafc')]),
            ]))
            
            elements.append(quote_table)
            elements.append(Spacer(1, 20))
        
        # Items comparison
        items = comparison_data.get('items', [])
        if items:
            elements.append(Paragraph(
                self._process_arabic("مقارنة أسعار الأصناف"),
                self.subtitle_style
            ))
            
            for item in items:
                item_name = item.get('item_name', '')
                quantity = item.get('quantity', 0)
                unit = item.get('unit', 'قطعة')
                
                elements.append(Paragraph(
                    self._process_arabic(f"• {item_name} - {quantity} {unit}"),
                    ParagraphStyle(
                        'ItemName',
                        parent=self.normal_style,
                        fontName=ARABIC_FONT,
                        fontSize=11,
                        textColor=colors.HexColor('#2d3748'),
                        spaceBefore=10
                    )
                ))
                
                # Prices from different suppliers
                prices = item.get('prices', [])
                if prices:
                    price_header = [
                        self._process_arabic('الإجمالي'),
                        self._process_arabic('سعر الوحدة'),
                        self._process_arabic('المورد')
                    ]
                    
                    price_data = [price_header]
                    
                    for p in prices:
                        row = [
                            f"{p.get('total_price', 0):,.2f}",
                            f"{p.get('unit_price', 0):,.2f}",
                            self._process_arabic(p.get('supplier_name', ''))
                        ]
                        price_data.append(row)
                    
                    price_table = Table(price_data, colWidths=[3*cm, 3*cm, 6*cm])
                    price_table.setStyle(TableStyle([
                        ('FONTNAME', (0, 0), (-1, -1), ARABIC_FONT),
                        ('FONTSIZE', (0, 0), (-1, -1), 9),
                        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#4a5568')),
                        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#e2e8f0')),
                        ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
                        ('TOPPADDING', (0, 0), (-1, -1), 5),
                    ]))
                    
                    elements.append(price_table)
        
        # Footer
        elements.append(Spacer(1, 30))
        elements.append(Paragraph(
            self._process_arabic("تم إنشاء هذا التقرير آلياً من نظام إدارة المشتريات"),
            ParagraphStyle(
                'Footer',
                parent=self.normal_style,
                fontSize=9,
                textColor=colors.HexColor('#718096'),
                alignment=TA_CENTER
            )
        ))
        
        # Build PDF
        doc.build(elements)
        buffer.seek(0)
        return buffer


# Singleton instance
pdf_generator = RFQPDFGenerator()


def generate_rfq_pdf(rfq_data: Dict[str, Any], company_settings: Optional[Dict[str, Any]] = None) -> BytesIO:
    """Generate RFQ PDF - convenience function"""
    return pdf_generator.generate_rfq_pdf(rfq_data, company_settings)


def generate_comparison_pdf(comparison_data: Dict[str, Any], company_settings: Optional[Dict[str, Any]] = None) -> BytesIO:
    """Generate comparison PDF - convenience function"""
    return pdf_generator.generate_comparison_pdf(comparison_data, company_settings)
