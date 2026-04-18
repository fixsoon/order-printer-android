"""打印机管理页面"""

from kivymd.uix.screen import MDScreen
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.button import MDRaisedButton, MDFlatButton
from kivymd.uix.label import MDLabel
from kivymd.uix.textfield import MDTextField
from kivymd.uix.scrollview import MDScrollView
from kivymd.uix.card import MDCard
from kivymd.uix.dialog import MDDialog
from kivymd.uix.selectioncontrol import MDCheckbox
from kivy.metrics import dp

from core.storage import add_printer, get_printers, delete_printer


class PrinterScreen(MDScreen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._build_ui()

    def _build_ui(self):
        layout = MDBoxLayout(orientation="vertical", spacing=dp(10), padding=dp(15))

        # 顶部
        top = MDBoxLayout(size_hint_y=None, height=dp(48))
        top.add_widget(MDFlatButton(
            text="< 返回",
            on_release=lambda x: setattr(self.manager, "current", "home"),
        ))
        top.add_widget(MDLabel(text="打印机管理", halign="center", font_style="H6"))
        top.add_widget(MDLabel(size_hint_x=0.2))
        layout.add_widget(top)

        # 打印机列表
        scroll = MDScrollView()
        self.printer_box = MDBoxLayout(
            orientation="vertical",
            adaptive_height=True,
            spacing=dp(8),
        )
        scroll.add_widget(self.printer_box)
        layout.add_widget(scroll)

        # 添加打印机
        layout.add_widget(MDLabel(
            text="添加打印机",
            font_style="Subtitle1",
            size_hint_y=None,
            height=dp(30),
        ))

        self.sn_field = MDTextField(hint_text="打印机 SN", mode="rectangle")
        self.key_field = MDTextField(hint_text="打印机 Key（可选）", mode="rectangle")
        self.name_field = MDTextField(hint_text="备注名称（可选）", mode="rectangle")
        layout.add_widget(self.sn_field)
        layout.add_widget(self.key_field)
        layout.add_widget(self.name_field)

        purpose_box = MDBoxLayout(size_hint_y=None, height=dp(40), spacing=dp(20))
        self.purpose_var = "receipt"
        self.receipt_radio = MDCheckbox(active=True, group="purpose", size_hint_x=None, width=dp(30))
        self.cup_radio = MDCheckbox(group="purpose", size_hint_x=None, width=dp(30))
        purpose_box.add_widget(self.receipt_radio)
        purpose_box.add_widget(MDLabel(text="收银小票", size_hint_x=0.3))
        purpose_box.add_widget(self.cup_radio)
        purpose_box.add_widget(MDLabel(text="杯贴", size_hint_x=0.3))
        layout.add_widget(purpose_box)

        self.default_check = MDCheckbox(active=True, size_hint_x=None, width=dp(30))
        default_box = MDBoxLayout(size_hint_y=None, height=dp(40))
        default_box.add_widget(self.default_check)
        default_box.add_widget(MDLabel(text="设为默认打印机"))
        layout.add_widget(default_box)

        layout.add_widget(MDRaisedButton(
            text="添加打印机",
            size_hint_x=1,
            on_release=lambda x: self._add_printer(),
        ))

        self.add_widget(layout)

    def on_enter(self):
        self._refresh_list()

    def _refresh_list(self):
        self.printer_box.clear_widgets()
        printers = get_printers()
        if not printers:
            self.printer_box.add_widget(MDLabel(
                text="暂无打印机，请添加",
                halign="center",
                theme_text_color="Hint",
                size_hint_y=None,
                height=dp(50),
            ))
            return

        for p in printers:
            card = MDCard(padding=dp(10), size_hint_y=None, height=dp(80), elevation=1)
            row = MDBoxLayout()
            info = MDBoxLayout(orientation="vertical")
            purpose_text = "收银小票" if p["purpose"] == "receipt" else "杯贴"
            default_text = " [默认]" if p["is_default"] else ""
            info.add_widget(MDLabel(
                text=f"{p['name'] or p['sn']}{default_text}",
                font_style="Subtitle1",
            ))
            info.add_widget(MDLabel(
                text=f"SN: {p['sn']}  |  {purpose_text}",
                theme_text_color="Secondary",
                font_style="Caption",
            ))
            row.add_widget(info)
            row.add_widget(MDFlatButton(
                text="删除",
                on_release=lambda x, sn=p["sn"]: self._delete(sn),
            ))
            card.add_widget(row)
            self.printer_box.add_widget(card)

    def _add_printer(self):
        sn = self.sn_field.text.strip()
        if not sn:
            return
        purpose = "receipt" if self.receipt_radio.active else "cup"
        add_printer(
            sn=sn,
            key=self.key_field.text.strip(),
            name=self.name_field.text.strip(),
            purpose=purpose,
            is_default=self.default_check.active,
        )
        self.sn_field.text = ""
        self.key_field.text = ""
        self.name_field.text = ""
        self._refresh_list()

    def _delete(self, sn):
        delete_printer(sn)
        self._refresh_list()
