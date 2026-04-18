"""排版预览页面"""

from kivymd.uix.screen import MDScreen
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.button import MDRaisedButton, MDFlatButton
from kivymd.uix.label import MDLabel
from kivymd.uix.scrollview import MDScrollView
from kivymd.uix.card import MDCard
from kivy.metrics import dp
from datetime import datetime

from core.templates import receipt_html, cup_label_html


class PreviewScreen(MDScreen):
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
        top.add_widget(MDLabel(text="排版预览", halign="center", font_style="H6"))
        top.add_widget(MDLabel(size_hint_x=0.2))
        layout.add_widget(top)

        # 切换按钮
        tab_box = MDBoxLayout(size_hint_y=None, height=dp(48), spacing=dp(10))
        tab_box.add_widget(MDRaisedButton(
            text="收银小票",
            on_release=lambda x: self._show_receipt(),
        ))
        tab_box.add_widget(MDRaisedButton(
            text="杯贴",
            on_release=lambda x: self._show_cup(),
        ))
        layout.add_widget(tab_box)

        # 预览内容
        scroll = MDScrollView()
        self.preview_label = MDLabel(
            text="",
            halign="left",
            font_style="Body2",
            size_hint_y=None,
        )
        self.preview_label.bind(texture_height=self.preview_label.setter("height"))
        scroll.add_widget(self.preview_label)
        layout.add_widget(scroll)

        layout.add_widget(MDLabel(
            text="提示：修改 core/templates.py 中的模板函数可自定义排版",
            theme_text_color="Secondary",
            font_style="Caption",
            halign="center",
            size_hint_y=None,
            height=dp(30),
        ))

        self.add_widget(layout)
        self._show_receipt()

    def _show_receipt(self):
        sample = {
            "chain": "接龙号 #001",
            "school": "音西一中",
            "grade": "七年级",
            "class_name": "3班",
            "student": "张三",
            "meal": "午餐",
            "user_note": "不要辣",
            "admin_note": "请于12点前送到",
            "time": datetime.now(),
            "items": [
                {"name": "红烧排骨饭", "qty": 1, "price": 18},
                {"name": "珍珠奶茶", "qty": 2, "price": 12},
            ],
            "total": 42,
        }
        self.preview_label.text = receipt_html(sample)

    def _show_cup(self):
        sample = {
            "chain": "接龙号 #001",
            "school": "音西一中",
            "grade": "七年级",
            "class_name": "3班",
            "student": "张三",
            "user_note": "少冰",
            "time": datetime.now(),
        }
        self.preview_label.text = cup_label_html(sample, "珍珠奶茶", "温/半糖/大杯")
