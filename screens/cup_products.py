"""杯贴商品库（纯 Kivy）"""

from kivy.uix.screenmanager import Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.scrollview import ScrollView
from kivy.uix.popup import Popup
from core.storage import get_cup_products, add_cup_product, remove_cup_product


class CupProductsScreen(Screen):
    def on_enter(self):
        if not hasattr(self, 'list_layout'):
            self._build_ui()
        self._refresh()

    def _build_ui(self):
        from kivy.metrics import dp
        root = BoxLayout(orientation='vertical', padding=dp(12), spacing=dp(8))
        root.add_widget(Label(
            text='[b]杯贴商品库[/b]', markup=True, halign='center',
            size_hint_y=None, height=dp(44), font_size=dp(18)
        ))
        root.add_widget(Label(
            text='设置哪些商品名会被打印为杯贴标签',
            color=(0.5, 0.5, 0.5, 1), size_hint_y=None, height=dp(28), font_size=dp(12)
        ))

        self.list_container = ScrollView(size_hint_y=1)
        self.list_layout = BoxLayout(orientation='vertical', size_hint_y=None, spacing=dp(8), padding=dp(4))
        self.list_layout.bind(minimum_height=self.list_layout.setter('height'))
        self.list_container.add_widget(self.list_layout)
        root.add_widget(self.list_container)

        bottom = BoxLayout(size_hint_y=None, height=dp(46), spacing=dp(8))
        bottom.add_widget(Button(
            text='← 返回', background_color=(0.4, 0.4, 0.4, 1),
            on_release=lambda x: setattr(self.manager, 'current', 'home')
        ))
        bottom.add_widget(Button(
            text='＋ 添加商品', background_color=(0.9, 0.5, 0.2, 1),
            on_release=lambda x: self._show_add_popup()
        ))
        root.add_widget(bottom)
        self.add_widget(root)

    def _refresh(self):
        from kivy.metrics import dp
        if not hasattr(self, 'list_layout'):
            return
        self.list_layout.clear_widgets()
        products = get_cup_products()
        if not products:
            self.list_layout.add_widget(Label(
                text='暂无杯贴商品', color=(0.5, 0.5, 0.5, 1), size_hint_y=None, height=dp(60)
            ))
            return
        for p in products:
            row = BoxLayout(size_hint_y=None, height=dp(48), padding=dp(8))
            row.add_widget(Label(
                text=p.get('name', ''), halign='left', valign='middle',
                size_hint_x=0.7, font_size=dp(14)
            ))
            row.add_widget(Button(
                text='删除', size_hint_x=0.3, background_color=(0.9, 0.2, 0.2, 1),
                on_release=lambda x, pid=p['id']: self._delete(pid)
            ))
            self.list_layout.add_widget(row)

    def _show_add_popup(self):
        from kivy.metrics import dp
        content = BoxLayout(orientation='vertical', padding=dp(16), spacing=dp(12))
        self.product_input = TextInput(hint_text='商品名称关键字，如：奶茶', multiline=False, size_hint_y=None, height=dp(44))
        content.add_widget(self.product_input)
        hint_label = Label(
            text='输入商品名关键字，包含该关键字的订单\n将自动打印为杯贴标签',
            color=(0.4, 0.4, 0.4, 1), font_size=dp(12)
        )
        content.add_widget(hint_label)
        btn_row = BoxLayout(size_hint_y=None, height=dp(44), spacing=dp(8))
        btn_row.add_widget(Button(text='取消', on_release=lambda x, p=popup: p.dismiss()))
        btn_row.add_widget(Button(text='添加', background_color=(0.9, 0.5, 0.2, 1),
                                  on_release=lambda x, p=popup: self._add_product(p)))
        content.add_widget(btn_row)
        popup = Popup(title='添加杯贴商品', content=content, size_hint=(0.9, 0.5), auto_dismiss=False)
        popup.open()

    def _add_product(self, popup):
        name = self.product_input.text.strip()
        if name:
            add_cup_product(name)
        popup.dismiss()
        self._refresh()

    def _delete(self, pid):
        remove_cup_product(pid)
        self._refresh()
