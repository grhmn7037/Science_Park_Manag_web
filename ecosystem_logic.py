# ecosystem_logic.py
# هذا الملف مسؤول عن العمليات الحسابية والتصنيف دون لمس المسارات الرئيسية

def calculate_readiness(stage):
    """حساب مدى جاهزية المشروع بناءً على المرحلة"""
    readiness_map = {
        'فكرة': 20,
        'نموذج': 60,
        'جاهز': 100
    }
    return readiness_map.get(stage, 0)

def get_color_by_status(status):
    """إرجاع لون التاغ بناءً على الحالة"""
    colors = {
        'pending': '#f1c40f',    # أصفر
        'approved': '#2ecc71',   # أخضر
        'rejected': '#e74c3c',   # أحمر
        'incubated': '#9b59b6'   # بنفسجي للحاضنة
    }
    return colors.get(status, '#7f8c8d')