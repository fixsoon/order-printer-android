"""杯贴商品库管理页面"""

from kivymd.uix.screen import MDScreen
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.button import MDRaisedButton, MDFlatButton
from kivymd.uix.label import MDLabel
from kivymd.uix.textfield import MDTextField
from kivymd.uix.scrollview import MDScrollView
from kivymd.uix.card import MDCard
from kivy.metrics import dp

from core.storage import add_cup_product, remove_cup_product, get_cup_products


class CupProductsScreen(MDScreen):
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
        top.add_widget(MDLabel(text="杯贴商品库", halign="center", font_style="H6"))
        top.add_widget(MDLabel(size_hint_x=0.2))
        layout.add_widget(top)

        layout.add_widget(MDLabel(
            text="只有以下列表中的商品才会打印杯贴标签",
            theme_text_color="Secondary",
            font_style="Caption",
            halign="center",
            size_hint_y=None,
            height=dp(30),
        ))

        # 商品列表
        scroll = MDScrollView()
        self.product_box = MDBoxLayout(
            orientation="vertical",
            adaptive_height=True,
            spacing=dp(5),
        )
        scroll.add_widget(self.product_box)
        layout.add_widget(scroll)

        # 添加区域
        add_box = MDBoxLayout(size_hint_y=None, height=dp(50), spacing=dp(10))
        self.name_field = MDTextField(hint_text="输入商品名称", mode="rectangle", size_hint_x=0.7)
        add_box.add_widget(self.name_field)
        add_box.add_widget(MDRaisedButton(
            text="添加",
            on_release=lambda x: self._add(),
            size_hint_x=0.3,
        ))
        layout.add_widget(add_box)

        self.add_widget(layout)

    def on_enter(self):
        self._refresh_list()

    def _refresh_list(self):
        self.product_box.clear_widgets()
        products = get_cup_products(enabled_only=False)
        if not products:
            self.product_box.add_widget(MDLabel(
                text="暂无商品，请添加需要打印杯贴的饮品名称",
                halign="center",
                theme_text_color="Hint",
                size_hint_y=None,
                height=dp(50),
            ))
            return

        for p in products:
            card = MDCard(padding=dp(10), size_hint_y=None, height=dp(55), elevation=1)
            row = MDBoxLayout()
            status = "✓" if p["enabled"] else "✗"
            row.add_widget(MDLabel(text=f"{status} {p['name']}"))
            row.add_widget(MDFlatButton(
                text="删除",
                on_release=lambda x, n=p["name"]: self._remove(n),
            ))
            card.add_widget(row)
            self.product_box.add_widget(card)

    def _add(self):
        name = self.name_field.text.strip()
        if name:
            add_cup_product(name)
            self.name_field.text = ""
            self._refresh_list()

    def _remove(self, name):
        remove_cup_product(name)
        self._refresh_list()
