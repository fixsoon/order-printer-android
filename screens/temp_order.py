"""临时加单页面"""

from kivymd.uix.screen import MDScreen
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.button import MDRaisedButton, MDFlatButton
from kivymd.uix.label import MDLabel
from kivymd.uix.textfield import MDTextField
from kivymd.uix.dialog import MDDialog
from kivy.metrics import dp
from datetime import datetime
import re

from core.storage import get_default_printer, is_cup_product
from core.feie_api import print_html as feie_print
from core.templates import receipt_html, cup_label_html


class TempOrderScreen(MDScreen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._build_ui()

    def _build_ui(self):
        layout = MDBoxLayout(orientation="vertical", spacing=dp(8), padding=dp(15))

        # 顶部
        top = MDBoxLayout(size_hint_y=None, height=dp(48))
        top.add_widget(MDFlatButton(
            text="< 返回",
            on_release=lambda x: setattr(self.manager, "current", "home"),
        ))
        top.add_widget(MDLabel(text="临时加单", halign="center", font_style="H6"))
        top.add_widget(MDLabel(size_hint_x=0.2))
        layout.add_widget(top)

        layout.add_widget(MDLabel(
            text="填写订单信息后打印",
            theme_text_color="Secondary",
            halign="center",
            size_hint_y=None,
            height=dp(30),
        ))

        # 输入字段
        self.fields = {}
        field_defs = [
            ("chain", "接龙号"),
            ("school", "学校"),
            ("grade", "年段"),
            ("class_name", "班级"),
            ("student", "学生姓名"),
            ("meal", "餐别"),
            ("product", "商品名称"),
            ("qty", "数量"),
            ("price", "金额"),
            ("note", "备注"),
        ]

        for key, hint in field_defs:
            field = MDTextField(hint_text=hint, mode="rectangle")
            layout.add_widget(field)
            self.fields[key] = field

        self.fields["qty"].text = "1"

        # 打印按钮
        btn_box = MDBoxLayout(size_hint_y=None, height=dp(50), spacing=dp(10))
        btn_box.add_widget(MDRaisedButton(
            text="打印收银小票",
            on_release=lambda x: self._print_receipt(),
            md_bg_color=(0.2, 0.6, 0.8, 1),
            size_hint_x=0.5,
        ))
        btn_box.add_widget(MDRaisedButton(
            text="打印杯贴",
            on_release=lambda x: self._print_cup(),
            md_bg_color=(0.9, 0.5, 0.2, 1),
            size_hint_x=0.5,
        ))
        layout.add_widget(btn_box)

        self.add_widget(layout)

    def _build_order(self):
        f = self.fields
        return {
            "chain": f["chain"].text.strip() or "临时单",
            "school": f["school"].text.strip(),
            "grade": f["grade"].text.strip(),
            "class_name": f["class_name"].text.strip(),
            "student": f["student"].text.strip(),
            "meal": f["meal"].text.strip(),
            "user_note": f["note"].text.strip(),
            "admin_note": "",
            "time": datetime.now(),
            "items": [{
                "name": f["product"].text.strip(),
                "qty": int(f["qty"].text or 1),
                "price": float(f["price"].text or 0),
            }],
            "total": float(f["price"].text or 0) * int(f["qty"].text or 1),
        }

    def _print_receipt(self):
        printer = get_default_printer("receipt")
        if not printer:
            self._msg("请先设置收银小票打印机")
            return
        try:
            html = receipt_html(self._build_order())
            feie_print(printer["sn"], html, printer.get("key", ""))
            self._msg("收银小票已发送打印 ✓")
        except Exception as e:
            self._msg(f"打印失败: {e}")

    def _print_cup(self):
        product = self.fields["product"].text.strip()
        if not is_cup_product(product):
            self._msg(f"「{product}」不在杯贴商品库中，请先添加")
            return
        printer = get_default_printer("cup")
        if not printer:
            self._msg("请先设置杯贴打印机")
            return
        try:
            order = self._build_order()
            html = cup_label_html(order, product)
            feie_print(printer["sn"], html, printer.get("key", ""))
            self._msg("杯贴已发送打印 ✓")
        except Exception as e:
            self._msg(f"打印失败: {e}")

    def _msg(self, text):
        dialog = MDDialog(
            title="提示",
            text=text,
            buttons=[MDFlatButton(text="确定", on_release=lambda x: dialog.dismiss())],
        )
        dialog.open()
