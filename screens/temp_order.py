"""临时加单（纯 Kivy）"""

from kivy.uix.screenmanager import Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.popup import Popup
import threading


class TempOrderScreen(Screen):
    def on_enter(self):
        if not hasattr(self, 'chain_input'):
            self._build_ui()

    def _build_ui(self):
        from kivy.metrics import dp
        root = BoxLayout(orientation='vertical', padding=dp(12), spacing=dp(8))

        root.add_widget(Label(
            text='[b]临时加单[/b]', markup=True, halign='center',
            size_hint_y=None, height=dp(44), font_size=dp(18)
        ))
        root.add_widget(Label(
            text='手动输入临时订单信息',
            color=(0.5, 0.5, 0.5, 1), size_hint_y=None, height=dp(28), font_size=dp(12)
        ))

        form = BoxLayout(orientation='vertical', spacing=dp(10), size_hint_y=1)
        fields = [
            ('接龙号', 'chain_input'),
            ('学校', 'school_input'),
            ('学生姓名', 'student_input'),
            ('商品名称', 'product_input'),
            ('数量', 'qty_input'),
        ]
        for label_text, attr_name in fields:
            row = BoxLayout(size_hint_y=None, height=dp(44))
            row.add_widget(Label(text=label_text + ':', size_hint_x=0.35, halign='left'))
            inp = TextInput(size_hint_x=0.65, multiline=False)
            if attr_name == 'qty_input':
                inp.input_filter = 'int'
                inp.text = '1'
            setattr(self, attr_name, inp)
            row.add_widget(inp)
            form.add_widget(row)

        self.temp_info = Label(text='', color=(0.4, 0.4, 0.4, 1), size_hint_y=None, height=dp(30))
        form.add_widget(self.temp_info)
        root.add_widget(form)

        bottom = BoxLayout(size_hint_y=None, height=dp(46), spacing=dp(8))
        bottom.add_widget(Button(
            text='← 返回', background_color=(0.4, 0.4, 0.4, 1),
            on_release=lambda x: setattr(self.manager, 'current', 'home')
        ))
        bottom.add_widget(Button(
            text='打印杯贴', background_color=(0.9, 0.5, 0.2, 1),
            on_release=lambda x: self._print_cup()
        ))
        bottom.add_widget(Button(
            text='打印小票', background_color=(0.2, 0.6, 0.8, 1),
            on_release=lambda x: self._print_receipt()
        ))
        root.add_widget(bottom)
        self.add_widget(root)

    def _show_toast(self, text):
        from kivy.clock import Clock
        popup = Popup(
            title='提示', content=Label(text=text),
            size_hint=(0.8, None), height=dp(120),
            auto_dismiss=True
        )
        popup.open()
        Clock.schedule_once(lambda dt: popup.dismiss(), 3)

    def _get_fields(self):
        return {
            'chain': self.chain_input.text.strip(),
            'school': self.school_input.text.strip(),
            'student': self.student_input.text.strip(),
            'product_name': self.product_input.text.strip(),
            'qty': int(self.qty_input.text.strip() or '1'),
        }

    def _print_cup(self):
        from core.storage import get_default_printer
        from core.feie_api import print_html as feie_print
        from core.templates import cup_label_html
        printer = get_default_printer('cup')
        if not printer:
            self._show_toast('请先设置杯贴打印机')
            return
        fields = self._get_fields()
        if not fields['product_name']:
            self._show_toast('请输入商品名称')
            return
        self.temp_info.text = '正在打印...'

        def do():
            try:
                html = cup_label_html(fields, fields['product_name'])
                feie_print(printer['sn'], html, printer.get('key', ''))
                from kivy.clock import Clock
                Clock.schedule_once(lambda dt: self._show_toast('杯贴打印成功'))
            except Exception as e:
                from kivy.clock import Clock
                Clock.schedule_once(lambda dt: self._show_toast(f'打印失败: {e}'))

        threading.Thread(target=do, daemon=True).start()

    def _print_receipt(self):
        from core.storage import get_default_printer
        from core.feie_api import print_html as feie_print
        from core.templates import receipt_html
        printer = get_default_printer('receipt')
        if not printer:
            self._show_toast('请先设置收银小票打印机')
            return
        fields = self._get_fields()
        if not fields['student'] or not fields['product_name']:
            self._show_toast('请输入姓名和商品')
            return
        self.temp_info.text = '正在打印...'

        def do():
            try:
                item = {'orders': [{'chain': fields['chain'], 'school': fields['school'],
                                   'student': fields['student'],
                                   'total': 0,
                                   'items': [{'name': fields['product_name'],
                                              'qty': fields['qty'], 'price': 0}]}],
                        'total': 0}
                html = receipt_html(item)
                feie_print(printer['sn'], html, printer.get('key', ''))
                from kivy.clock import Clock
                Clock.schedule_once(lambda dt: self._show_toast('小票打印成功'))
            except Exception as e:
                from kivy.clock import Clock
                Clock.schedule_once(lambda dt: self._show_toast(f'打印失败: {e}'))

        threading.Thread(target=do, daemon=True).start()
