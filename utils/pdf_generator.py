# utils/pdf_generator.py

from reportlab.lib.pagesizes import A4, letter
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from reportlab.lib.units import inch, cm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.graphics.shapes import Drawing, Rect, String
from reportlab.graphics.charts.linecharts import HorizontalLineChart
from reportlab.graphics.charts.barcharts import VerticalBarChart
from reportlab.graphics.charts.legends import Legend
from reportlab.graphics import renderPDF
from io import BytesIO
import os
from datetime import datetime
import json

class LuxuryPDFGenerator:
    """Luxury PDF report generator with professional styling"""
    
    # Color scheme matching hotel luxury theme
    COLORS = {
        'primary': colors.HexColor('#D4AF37'),  # Gold
        'secondary': colors.HexColor('#2C3E50'),  # Dark Blue
        'accent': colors.HexColor('#E74C3C'),  # Red
        'light_bg': colors.HexColor('#F8F9FA'),
        'dark_text': colors.HexColor('#2C3E50'),
        'success': colors.HexColor('#27AE60'),
        'warning': colors.HexColor('#F39C12'),
        'table_header': colors.HexColor('#34495E'),
        'table_row_even': colors.HexColor('#FFFFFF'),
        'table_row_odd': colors.HexColor('#F8F9FA')
    }
    
    @staticmethod
    def generate_revenue_report(report_data):
        """Generate luxury revenue report PDF"""
        buffer = BytesIO()
        doc = SimpleDocTemplate(
            buffer, 
            pagesize=A4,
            topMargin=0.5*inch,
            bottomMargin=0.5*inch,
            leftMargin=0.5*inch,
            rightMargin=0.5*inch
        )
        
        story = []
        styles = LuxuryPDFGenerator._create_styles()
        
        # Cover Page
        story.extend(LuxuryPDFGenerator._create_cover_page(styles, report_data))
        story.append(PageBreak())
        
        # Executive Summary
        story.extend(LuxuryPDFGenerator._create_executive_summary(styles, report_data))
        story.append(Spacer(1, 0.3*inch))
        
        # Key Metrics
        story.extend(LuxuryPDFGenerator._create_key_metrics(styles, report_data))
        story.append(Spacer(1, 0.3*inch))
        
        # Room Performance
        story.extend(LuxuryPDFGenerator._create_room_performance(styles, report_data))
        story.append(PageBreak())
        
        # Revenue Analysis
        story.extend(LuxuryPDFGenerator._create_revenue_analysis(styles, report_data))
        
        # Footer on every page
        doc.build(story, onFirstPage=LuxuryPDFGenerator._add_header_footer, 
                 onLaterPages=LuxuryPDFGenerator._add_header_footer)
        
        buffer.seek(0)
        return buffer
    
    @staticmethod
    def _create_styles():
        """Create custom styles for the PDF"""
        styles = getSampleStyleSheet()
        
        # Title Style
        styles.add(ParagraphStyle(
            name='LuxuryTitle',
            parent=styles['Heading1'],
            fontSize=24,
            textColor=LuxuryPDFGenerator.COLORS['primary'],
            spaceAfter=30,
            alignment=1,  # Center
            fontName='Helvetica-Bold'
        ))
        
        # Subtitle Style
        styles.add(ParagraphStyle(
            name='LuxurySubtitle',
            parent=styles['Heading2'],
            fontSize=16,
            textColor=LuxuryPDFGenerator.COLORS['secondary'],
            spaceAfter=20,
            alignment=1,
            fontName='Helvetica-Bold'
        ))
        
        # Heading Style
        styles.add(ParagraphStyle(
            name='LuxuryHeading',
            parent=styles['Heading2'],
            fontSize=14,
            textColor=LuxuryPDFGenerator.COLORS['secondary'],
            spaceAfter=12,
            fontName='Helvetica-Bold',
            borderColor=LuxuryPDFGenerator.COLORS['primary'],
            borderWidth=1,
            borderPadding=5,
            backColor=LuxuryPDFGenerator.COLORS['light_bg']
        ))
        
        # Normal Style
        styles.add(ParagraphStyle(
            name='LuxuryNormal',
            parent=styles['Normal'],
            fontSize=10,
            textColor=LuxuryPDFGenerator.COLORS['dark_text'],
            spaceAfter=6,
            fontName='Helvetica'
        ))
        
        return styles
    
    @staticmethod
    def _create_cover_page(styles, report_data):
        """Create luxury cover page"""
        elements = []
        
        # Hotel Logo/Title
        title = Paragraph("HOTEL ROYAL ORCHID", styles['LuxuryTitle'])
        elements.append(title)
        elements.append(Spacer(1, 0.5*inch))
        
        # Report Title
        subtitle = Paragraph("BUSINESS INTELLIGENCE REPORT", styles['LuxurySubtitle'])
        elements.append(subtitle)
        elements.append(Spacer(1, 0.3*inch))
        
        # Period
        period = report_data['period']
        period_text = f"{period['start_date'].strftime('%B %d, %Y')} - {period['end_date'].strftime('%B %d, %Y')}"
        period_para = Paragraph(period_text, styles['LuxuryNormal'])
        elements.append(period_para)
        elements.append(Spacer(1, 1*inch))
        
        # Summary Box
        summary_data = [
            ['TOTAL REVENUE', f"₹{report_data['summary']['total_revenue']:,.2f}"],
            ['TOTAL BOOKINGS', str(report_data['summary']['total_bookings'])],
            ['AVG BOOKING VALUE', f"₹{report_data['summary']['avg_booking_value']:,.2f}"]
        ]
        
        summary_table = Table(summary_data, colWidths=[3*inch, 2*inch])
        summary_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), LuxuryPDFGenerator.COLORS['primary']),
            ('TEXTCOLOR', (0, 0), (-1, -1), colors.white),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 12),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
            ('TOPPADDING', (0, 0), (-1, -1), 12),
            ('GRID', (0, 0), (-1, -1), 1, colors.white),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE')
        ]))
        elements.append(summary_table)
        elements.append(Spacer(1, 2*inch))
        
        # Footer on cover
        generated_date = Paragraph(f"Generated on: {datetime.now().strftime('%B %d, %Y at %H:%M')}", styles['LuxuryNormal'])
        elements.append(generated_date)
        
        confidential = Paragraph("CONFIDENTIAL - FOR MANAGEMENT USE ONLY", styles['LuxuryNormal'])
        elements.append(confidential)
        
        return elements
    
    @staticmethod
    def _create_executive_summary(styles, report_data):
        """Create executive summary section"""
        elements = []
        
        title = Paragraph("EXECUTIVE SUMMARY", styles['LuxuryHeading'])
        elements.append(title)
        
        summary = report_data['summary']
        text = f"""
        This report provides a comprehensive analysis of Hotel Royal Orchid's performance 
        during the specified period. The hotel achieved a total revenue of <b>₹{summary['total_revenue']:,.2f}</b> 
        from <b>{summary['total_bookings']}</b> bookings, with an average booking value of 
        <b>₹{summary['avg_booking_value']:,.2f}</b>. The property maintained strong performance 
        across all room categories, demonstrating consistent guest satisfaction and revenue growth.
        """
        
        summary_para = Paragraph(text, styles['LuxuryNormal'])
        elements.append(summary_para)
        
        return elements
    
    @staticmethod
    def _create_key_metrics(styles, report_data):
        """Create key metrics section with styled table"""
        elements = []
        
        title = Paragraph("KEY PERFORMANCE INDICATORS", styles['LuxuryHeading'])
        elements.append(title)
        
        summary = report_data['summary']
        metrics_data = [
            ['Performance Metric', 'Value', 'Status'],
            ['Total Revenue', f"₹{summary['total_revenue']:,.2f}", 'Primary'],
            ['Total Bookings', str(summary['total_bookings']), 'Secondary'],
            ['Confirmed Bookings', str(summary['confirmed_bookings']), 'Success'],
            ['Completed Bookings', str(summary['completed_bookings']), 'Success'],
            ['Average Booking Value', f"₹{summary['avg_booking_value']:,.2f}", 'Primary']
        ]
        
        metrics_table = Table(metrics_data, colWidths=[2.5*inch, 1.5*inch, 1*inch])
        metrics_table.setStyle(TableStyle([
            # Header
            ('BACKGROUND', (0, 0), (-1, 0), LuxuryPDFGenerator.COLORS['table_header']),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 11),
            ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
            
            # Data rows
            ('BACKGROUND', (0, 1), (-1, -1), LuxuryPDFGenerator.COLORS['table_row_even']),
            ('TEXTCOLOR', (0, 1), (-1, -1), LuxuryPDFGenerator.COLORS['dark_text']),
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 1), (-1, -1), 10),
            ('ALIGN', (0, 1), (1, -1), 'CENTER'),
            ('ALIGN', (0, 1), (0, -1), 'LEFT'),
            
            # Grid
            ('GRID', (0, 0), (-1, -1), 1, colors.grey),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
            ('TOPPADDING', (0, 0), (-1, -1), 8)
        ]))
        
        elements.append(metrics_table)
        return elements
    
    @staticmethod
    def _create_room_performance(styles, report_data):
        """Create room performance section"""
        elements = []
        
        title = Paragraph("ROOM PERFORMANCE ANALYSIS", styles['LuxuryHeading'])
        elements.append(title)
        
        if not report_data['room_performance']:
            no_data = Paragraph("No room performance data available for this period.", styles['LuxuryNormal'])
            elements.append(no_data)
            return elements
        
        # Header
        room_data = [['Room Type', 'Bookings', 'Revenue', 'Avg Revenue', 'Performance']]
        
        # Data rows
        for room in report_data['room_performance']:
            performance = "Excellent" if room['avg_revenue'] > 5000 else "Good" if room['avg_revenue'] > 3000 else "Average"
            room_data.append([
                room['room_type'].replace('_', ' ').title(),
                str(room['bookings']),
                f"₹{room['revenue']:,.2f}",
                f"₹{room['avg_revenue']:,.2f}",
                performance
            ])
        
        room_table = Table(room_data, colWidths=[1.5*inch, 0.8*inch, 1.2*inch, 1.2*inch, 1*inch])
        room_table.setStyle(TableStyle([
            # Header
            ('BACKGROUND', (0, 0), (-1, 0), LuxuryPDFGenerator.COLORS['primary']),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            
            # Data rows with alternating colors
            ('BACKGROUND', (0, 1), (-1, -1), LuxuryPDFGenerator.COLORS['table_row_even']),
            ('BACKGROUND', (0, 2), (-1, 2), LuxuryPDFGenerator.COLORS['table_row_odd']),
            ('BACKGROUND', (0, 4), (-1, 4), LuxuryPDFGenerator.COLORS['table_row_odd']),
            
            ('TEXTCOLOR', (0, 1), (-1, -1), LuxuryPDFGenerator.COLORS['dark_text']),
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 1), (-1, -1), 9),
            ('ALIGN', (0, 1), (-1, -1), 'CENTER'),
            ('ALIGN', (0, 1), (0, -1), 'LEFT'),
            
            # Grid
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
            ('TOPPADDING', (0, 0), (-1, -1), 6)
        ]))
        
        elements.append(room_table)
        return elements
    
    @staticmethod
    def _create_revenue_analysis(styles, report_data):
        """Create revenue analysis section"""
        elements = []
        
        title = Paragraph("REVENUE BREAKDOWN & INSIGHTS", styles['LuxuryHeading'])
        elements.append(title)
        
        text = """
        <b>Revenue Distribution:</b> The revenue distribution across room types shows healthy 
        diversification. Premium suites contribute significantly to overall revenue despite 
        lower booking volumes, indicating successful upselling strategies.
        
        <b>Seasonal Trends:</b> Revenue patterns demonstrate consistent performance with 
        expected seasonal variations. Weekend bookings show higher average values compared 
        to weekdays.
        
        <b>Opportunities:</b> There is potential to increase revenue through targeted 
        marketing campaigns during low-occupancy periods and introducing premium packages 
        for high-value guests.
        """
        
        analysis_para = Paragraph(text, styles['LuxuryNormal'])
        elements.append(analysis_para)
        
        return elements
    
    @staticmethod
    def _add_header_footer(canvas, doc):
        """Add luxury header and footer to every page"""
        canvas.saveState()
        
        # Header
        canvas.setFont('Helvetica-Bold', 12)
        canvas.setFillColor(LuxuryPDFGenerator.COLORS['primary'])
        canvas.drawString(0.5*inch, doc.pagesize[1] - 0.7*inch, "HOTEL ROYAL ORCHID")
        
        canvas.setFont('Helvetica', 8)
        canvas.setFillColor(LuxuryPDFGenerator.COLORS['secondary'])
        canvas.drawString(0.5*inch, doc.pagesize[1] - 0.9*inch, "Business Intelligence Report")
        
        # Footer
        canvas.setFont('Helvetica', 8)
        canvas.setFillColor(LuxuryPDFGenerator.COLORS['secondary'])
        canvas.drawString(0.5*inch, 0.5*inch, f"Page {doc.page}")
        canvas.drawRightString(doc.pagesize[0] - 0.5*inch, 0.5*inch, 
                             f"Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
        
        # Decorative line
        canvas.setStrokeColor(LuxuryPDFGenerator.COLORS['primary'])
        canvas.setLineWidth(1)
        canvas.line(0.5*inch, 0.7*inch, doc.pagesize[0] - 0.5*inch, 0.7*inch)
        
        canvas.restoreState()

class PDFGenerator:
    """Main PDF generator class with fallback"""
    
    @staticmethod
    def generate_revenue_report(report_data):
        """Generate luxury revenue report with fallback"""
        try:
            return LuxuryPDFGenerator.generate_revenue_report(report_data)
        except Exception as e:
            print(f"Luxury PDF generation failed, using fallback: {e}")
            return PDFGenerator._generate_fallback_pdf(report_data)
    
    @staticmethod
    def _generate_fallback_pdf(report_data):
        """Fallback PDF generator"""
        buffer = BytesIO()
        buffer.write(b"%PDF-1.4\n")
        buffer.write(b"1 0 obj\n<< /Type /Catalog /Pages 2 0 R >>\nendobj\n")
        buffer.write(b"2 0 obj\n<< /Type /Pages /Kids [3 0 R] /Count 1 >>\nendobj\n")
        buffer.write(b"3 0 obj\n<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Contents 4 0 R >>\nendobj\n")
        buffer.write(b"4 0 obj\n<< /Length 200 >>\nstream\nBT /F1 12 Tf 50 750 Td (Hotel Royal Orchid - Revenue Report) Tj ET\n")
        
        y_pos = 700
        if 'summary' in report_data:
            for key, value in report_data['summary'].items():
                buffer.write(f"BT /F1 10 Tf 50 {y_pos} Td ({key}: {value}) Tj ET\n".encode('utf-8'))
                y_pos -= 20
        
        buffer.write(b"endstream\nendobj\n")
        buffer.write(b"xref\n0 5\n0000000000 65535 f \n0000000009 00000 n \n0000000058 00000 n \n0000000115 00000 n \n0000000220 00000 n \n")
        buffer.write(b"trailer\n<< /Size 5 /Root 1 0 R >>\n")
        buffer.write(b"startxref\n300\n%%EOF\n")
        buffer.seek(0)
        return buffer