"""HTML 打印模板生成"""

from datetime import datetime


def receipt_html(order):
    """
    生成收银小票 HTML
    order: {
        chain, school, grade, class_name, student,
        meal, user_note, admin_note, time, items, total
    }
    """
    items_html = ""
    for i, item in enumerate(order["items"], 1):
        items_html += f"""
        <tr>
            <td style="width:50%;">{i}. {item['name']}</td>
            <td style="text-align:center;">x{item['qty']}</td>
            <td style="text-align:right;">￥{item['price']:.0f}</td>
        </tr>"""

    time_str = ""
    if order["time"]:
        if isinstance(order["time"], datetime):
            time_str = order["time"].strftime("%Y-%m-%d %H:%M")
        else:
            time_str = str(order["time"])

    html = f"""
    <html>
    <body style="font-size:14px; font-family:sans-serif; margin:0; padding:10px;">
        <!-- 接龙号 -->
        <h2 align="center" style="font-size:18px; margin:5px 0;">{order['chain']}</h2>

        <!-- 表头 -->
        <p style="font-size:10px; color:#999; text-align:center; margin:2px 0;">
            商品名称 &nbsp;&nbsp; 数量 &nbsp;&nbsp; 金额
        </p>
        <hr style="border-top:1px dashed #000; margin:5px 0;">

        <!-- 基本信息 -->
        <p style="margin:3px 0;"><b>学校：</b>{order['school']}</p>
        <p style="margin:3px 0;"><b>班级：</b>{order['grade']} {order['class_name']}</p>
        <p style="margin:3px 0;"><b>姓名：</b>{order['student']}</p>
        <p style="margin:3px 0;"><b>餐别：</b>{order['meal']}</p>"""

    if order.get("user_note"):
        html += f'\n        <p style="margin:3px 0;"><b>备注：</b>{order["user_note"]}</p>'
    if order.get("admin_note"):
        html += f'\n        <p style="margin:3px 0;"><b>发起人：</b>{order["admin_note"]}</p>'

    html += f"""
        <hr style="border-top:1px dashed #000; margin:5px 0;">

        <!-- 商品明细 -->
        <table style="width:100%; font-size:14px; border-collapse:collapse;">
            {items_html}
        </table>

        <hr style="border-top:1px dashed #000; margin:5px 0;">

        <!-- 总价 -->
        <p style="font-size:16px; font-weight:bold; text-align:right; margin:5px 0;">
            合计：￥{order['total']:.0f}
        </p>

        <!-- 时间 -->
        <p style="font-size:10px; color:#999; text-align:center; margin:2px 0;">
            {time_str}
        </p>
    </body>
    </html>"""
    return html


def cup_label_html(order, product_name, spec_text=""):
    """
    生成杯贴 HTML
    order: {chain, school, grade, class_name, student, user_note, time}
    product_name: 饮品名称
    spec_text: 规格文字（如"温/半糖/大杯"）
    """
    time_str = ""
    if order.get("time"):
        if isinstance(order["time"], datetime):
            time_str = order["time"].strftime("%m-%d %H:%M")
        else:
            time_str = str(order["time"])

    html = f"""
    <html>
    <body style="font-size:14px; font-family:sans-serif; margin:0; padding:8px; text-align:center;">
        <!-- 接龙号 -->
        <p style="font-size:16px; font-weight:bold; margin:2px 0;">{order['chain']}</p>

        <!-- 饮品名称 -->
        <h1 style="font-size:22px; font-weight:bold; margin:5px 0;">{product_name}</h1>

        <!-- 规格 -->
        <p style="font-size:14px; margin:2px 0; color:#333;">{spec_text}</p>

        <hr style="border-top:1px dashed #000; margin:5px 0;">

        <!-- 学校班级姓名 -->
        <p style="font-size:13px; margin:2px 0;">
            {order['school']} {order['grade']}{order['class_name']} {order['student']}
        </p>"""

    if order.get("user_note"):
        html += f'\n        <p style="font-size:12px; color:#666; margin:2px 0;">备注：{order["user_note"]}</p>'

    html += f"""
        <p style="font-size:10px; color:#999; margin:2px 0;">{time_str}</p>
    </body>
    </html>"""
    return html


def summary_html(title, rows, extra_lines=None):
    """
    生成汇总单 HTML
    title: 标题
    rows: [(名称, 数量, 金额)]
    extra_lines: 额外附加的文字行
    """
    rows_html = ""
    for name, qty, amount in rows:
        if amount > 0:
            rows_html += f"""
            <tr>
                <td style="width:50%;">{name}</td>
                <td style="text-align:center;">{qty}</td>
                <td style="text-align:right;">￥{amount:.0f}</td>
            </tr>"""
        else:
            rows_html += f"""
            <tr>
                <td style="width:50%;">{name}</td>
                <td style="text-align:center;">{qty}</td>
                <td style="text-align:right;"></td>
            </tr>"""

    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    extra_html = ""
    if extra_lines:
        for line in extra_lines:
            extra_html += f'<p style="font-size:12px; margin:2px 0;">{line}</p>'

    html = f"""
    <html>
    <body style="font-size:14px; font-family:sans-serif; margin:0; padding:10px;">
        <h2 align="center" style="margin:5px 0;">{title}</h2>
        <p style="font-size:10px; color:#999; text-align:center;">{now_str}</p>
        <hr style="border-top:1px dashed #000; margin:5px 0;">
        <table style="width:100%; font-size:14px; border-collapse:collapse;">
            <tr style="font-weight:bold; border-bottom:1px solid #000;">
                <td>名称</td>
                <td style="text-align:center;">数量</td>
                <td style="text-align:right;">金额</td>
            </tr>
            {rows_html}
        </table>
        {extra_html}
    </body>
    </html>"""
    return html
