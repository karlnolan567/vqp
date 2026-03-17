from fpdf import FPDF
import datetime

class VQPReport(FPDF):
    def header(self):
        # Background Navy Bar at the very top
        self.set_fill_color(0, 51, 102) # Navy Blue
        self.rect(0, 0, 210, 15, 'F')
        
        # Brand Header (Stylized Text Logo)
        self.set_font('Arial', 'B', 20)
        self.set_y(20)
        self.set_text_color(0, 51, 102) # Navy Blue
        self.cell(10, 10, 'Virtual', 0, 0, 'L')
        self.set_text_color(0, 168, 168) # Teal Blue
        self.cell(0, 10, 'QP', 0, 1, 'L')
        
        # Sub-header
        self.set_font('Arial', 'B', 10)
        self.set_text_color(100, 100, 100)
        self.cell(0, 5, 'QMS DESIGN | QUALITY AS A SUBSCRIPTION', 0, 1, 'L')
        
        # Tagline
        self.set_font('Arial', 'I', 9)
        self.set_text_color(150, 150, 150)
        self.cell(0, 5, 'Your Quality Infrastructure Built Before You Need It', 0, 1, 'L')
        
        # Decorative Teal Line
        self.set_draw_color(0, 168, 168) # Teal
        self.set_line_width(0.8)
        self.line(10, 45, 200, 45)
        self.ln(15)

    def footer(self):
        # Teal line above footer
        self.set_draw_color(0, 168, 168)
        self.set_line_width(0.2)
        self.line(10, 280, 200, 280)
        
        self.set_y(-15)
        self.set_font('Arial', 'I', 8)
        self.set_text_color(128, 128, 128)
        self.cell(0, 10, f'VirtualQP Analysis Report | Page {self.page_no()} | Generated on {datetime.datetime.now().strftime("%Y-%m-%d %H:%M")}', 0, 0, 'C')

def generate_pdf_report(client_name, upload_id, indices, patterns, alerts):
    pdf = VQPReport()
    pdf.add_page()
    
    # 1. REPORT TITLE & METADATA
    pdf.set_font('Arial', 'B', 18)
    pdf.set_text_color(51, 51, 51)
    pdf.cell(0, 15, 'QUALITY ANALYSIS & RISK REPORT', 0, 1, 'C')
    pdf.ln(5)
    
    # Client Metadata Table-like structure
    pdf.set_fill_color(244, 247, 249) # Light Gray/Blue background
    pdf.set_font('Arial', 'B', 12)
    pdf.set_text_color(0, 51, 102) # Navy
    pdf.cell(50, 10, ' Client Site:', 1, 0, 'L', True)
    pdf.set_font('Arial', '', 12)
    pdf.set_text_color(51, 51, 51)
    pdf.cell(0, 10, f' {client_name}', 1, 1, 'L', True)
    
    pdf.set_font('Arial', 'B', 12)
    pdf.set_text_color(0, 51, 102) # Navy
    pdf.cell(50, 10, ' Batch ID:', 1, 0, 'L', True)
    pdf.set_font('Arial', '', 12)
    pdf.set_text_color(51, 51, 51)
    pdf.cell(0, 10, f' {upload_id}', 1, 1, 'L', True)
    pdf.ln(10)
    
    # 2. EXECUTIVE INDEX SUMMARY
    pdf.set_font('Arial', 'B', 14)
    pdf.set_text_color(0, 51, 102)
    pdf.cell(0, 10, '1. Executive Index Performance Summary', 0, 1, 'L')
    pdf.set_draw_color(0, 168, 168)
    pdf.set_line_width(0.3)
    pdf.line(10, pdf.get_y(), 100, pdf.get_y())
    pdf.ln(5)
    
    # Indices
    pdf.set_font('Arial', '', 11)
    pdf.set_text_color(51, 51, 51)
    
    # Column Headers for metrics
    pdf.set_font('Arial', 'B', 10)
    pdf.cell(40, 8, 'Index Metric', 1, 0, 'C', True)
    pdf.cell(30, 8, 'Score', 1, 1, 'C', True)
    
    pdf.set_font('Arial', '', 11)
    metrics = [
        ("System Safety Index (SSI)", indices.ssi),
        ("Facility Index (FI)", indices.fi),
        ("Regulatory Index (RI)", indices.ri),
        ("Quality Control Index (QCI)", indices.qci),
        ("Behavioral Index (BEI)", indices.bei)
    ]
    
    for m_name, m_val in metrics:
        pdf.cell(40, 8, m_name, 1, 0, 'L')
        # Color score based on value
        if m_val < 0.4: pdf.set_text_color(200, 0, 0) # Red
        elif m_val < 0.7: pdf.set_text_color(255, 140, 0) # Orange
        else: pdf.set_text_color(0, 128, 0) # Green
        pdf.cell(30, 8, str(round(m_val, 2)), 1, 1, 'C')
        pdf.set_text_color(51, 51, 51)

    pdf.ln(5)
    pdf.set_font('Arial', 'B', 12)
    pdf.set_text_color(0, 51, 102)
    pdf.cell(0, 10, f'Overall Quality Maturity Score (QMS): {round(indices.quality_maturity_score, 2)}', 0, 1)
    pdf.ln(10)
    
    # 3. PATTERN DETECTION
    pdf.set_font('Arial', 'B', 14)
    pdf.set_text_color(0, 51, 102)
    pdf.cell(0, 10, '2. Intelligence: Pattern Detection', 0, 1, 'L')
    pdf.line(10, pdf.get_y(), 100, pdf.get_y())
    pdf.ln(5)
    
    pdf.set_font('Arial', '', 11)
    pdf.set_text_color(51, 51, 51)
    if patterns:
        for p in patterns:
            pdf.set_font('Arial', 'B', 11)
            pdf.cell(0, 8, f"Pattern Identified: {p.pattern_id} (Strength: {round(p.strength, 2)})", 0, 1)
            pdf.set_font('Arial', 'I', 11)
            pdf.multi_cell(0, 8, f"Interpretation: {p.interpretation}")
            pdf.ln(2)
    else:
        pdf.cell(0, 10, 'No critical multi-signal patterns detected.', 0, 1)
    pdf.ln(10)
    
    # 4. CRITICAL ALERTS
    pdf.set_font('Arial', 'B', 14)
    pdf.set_text_color(0, 51, 102)
    pdf.cell(0, 10, '3. Predictive Alerts & Recommendations', 0, 1, 'L')
    pdf.line(10, pdf.get_y(), 100, pdf.get_y())
    pdf.ln(5)
    
    pdf.set_font('Arial', '', 11)
    if alerts:
        for a in alerts:
            # Severity color
            if a.severity == 'High': pdf.set_text_color(200, 0, 0)
            elif a.severity == 'Medium': pdf.set_text_color(255, 140, 0)
            else: pdf.set_text_color(0, 51, 102)
            
            pdf.set_font('Arial', 'B', 11)
            pdf.cell(0, 8, f"[{a.severity} SEVERITY] {a.alert_type}", 0, 1)
            pdf.set_font('Arial', '', 11)
            pdf.multi_cell(0, 8, a.message)
            pdf.ln(2)
    else:
        pdf.set_text_color(0, 128, 0)
        pdf.cell(0, 10, 'System status stable. No active alerts.', 0, 1)
        
    return pdf.output(dest='S').encode('latin-1')
