"""打印机设置（纯 Kivy）"""

from kivy.uix.screenmanager import Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.scrollview import ScrollView
from kivy.uix.popup import Popup
from kivy.metrics import dp
from core.storage import get_all_printers, save_printer, delete_printer_by_id


class PrinterScreen(Screen):
    def on_enter(self):
        if not hasattr(self, 'list_layout'):
            self._build_ui()
        self._refresh()

    def _build_ui(self):
        from kivy.metrics import dp
        root = BoxLayout(orientation='vertical', padding=dp(12), spacing=dp(8))

        root.add_widget(Label(
            text='[b]打印机设置[/b]', markup=True, halign='center',
            size_hint_y=None, height=dp(44), font_size=dp(18)
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
            text='＋ 添加打印机', background_color=(0.2, 0.6, 0.8, 1),
            on_release=lambda x: self._show_add_popup()
        ))
        root.add_widget(bottom)

        self.add_widget(root)

    def _refresh(self):
        if not hasattr(self, 'list_layout'):
            return
        self.list_layout.clear_widgets()
        printers = get_all_printers()
        if not printers:
            self.list_layout.add_widget(Label(
                text='暂无打印机，请点击添加', color=(0.5, 0.5, 0.5, 1), size_hint_y=None, height=dp(60)
            ))
            return
        for p in printers:
            ptype = p.get('purpose', 'receipt')
            row = BoxLayout(size_hint_y=None, height=dp(60), padding=dp(8))
            info = BoxLayout(orientation='vertical', size_hint_x=0.6)
            info.add_widget(Label(
                text=f"[b]{'收银小票' if ptype == 'receipt' else '杯贴'}[/b] {p.get('name','')}",
                markup=True, halign='left', font_size=dp(14)
            ))
            info.add_widget(Label(
                text=f"SN: {p.get('sn','')[:12]}...", color=(0.4, 0.4, 0.4, 1),
                halign='left', font_size=dp(11)
            ))
            info.add_widget(Label(
                text='\u2714 默认' if p.get('is_default') else '', color=(0, 0.7, 0, 1),
                font_size=dp(11)
            ))
            row.add_widget(info)
            btns = BoxLayout(size_hint_x=0.4, spacing=dp(4))
            btns.add_widget(Button(
                text='默认', size_hint_x=0.5,
                background_color=(0, 0.6, 0.2, 1) if not p.get('is_default') else (0.3, 0.3, 0.3, 1),
                on_release=lambda x, pid=p['id']: self._set_default(pid)
            ))
            btns.add_widget(Button(
                text='删除', size_hint_x=0.5,
                background_color=(0.9, 0.2, 0.2, 1),
                on_release=lambda x, pid=p['id']: self._delete(pid)
            ))
            row.add_widget(btns)
            self.list_layout.add_widget(row)

    def _show_add_popup(self):
        from kivy.metrics import dp
        content = BoxLayout(orientation='vertical', padding=dp(16), spacing=dp(12))

        ptype_label = Label(text='类型:', size_hint_x=0.3)
        self.ptype_dropdown = TextInput(text='receipt', hint_text='receipt / cup', size_hint_x=0.7)
        content.add_widget(ptype_label)
        content.add_widget(self.ptype_dropdown)

        self.name_input = TextInput(hint_text='打印机名称', multiline=False, size_hint_y=None, height=dp(40))
        self.sn_input = TextInput(hint_text='打印机 SN', multiline=False, size_hint_y=None, height=dp(40))
        self.key_input = TextInput(hint_text='Printer Key (可选)', multiline=False, size_hint_y=None, height=dp(40))

        content.add_widget(Label(text='名称:', size_hint_y=None, height=dp(25)))
        content.add_widget(self.name_input)
        content.add_widget(Label(text='SN:', size_hint_y=None, height=dp(25)))
        content.add_widget(self.sn_input)
        content.add_widget(Label(text='Key:', size_hint_y=None, height=dp(25)))
        content.add_widget(self.key_input)

        btn_row = BoxLayout(size_hint_y=None, height=dp(44), spacing=dp(8))
        btn_row.add_widget(Button(text='取消', on_release=lambda x, p=popup: p.dismiss()))
        save_btn = Button(text='保存', background_color=(0.2, 0.6, 0.8, 1),
                          on_release=lambda x, p=popup: self._save_printer(p))
        btn_row.add_widget(save_btn)
        content.add_widget(btn_row)

        popup = Popup(title='添加打印机', content=content, size_hint=(0.9, 0.8), auto_dismiss=False)
        popup.open()

    def _save_printer(self, popup):
        name = self.name_input.text.strip()
        sn = self.sn_input.text.strip()
        ptype = self.ptype_dropdown.text.strip() or 'receipt'
        key = self.key_input.text.strip()
        if not sn:
            return
        save_printer({'name': name, 'sn': sn, 'key': key, 'type': ptype})
        popup.dismiss()
        self._refresh()

    def _set_default(self, pid):
        printers = get_all_printers()
        for p in printers:
            save_printer({**p, 'is_default': (p['id'] == pid)})
        self._refresh()

    def _delete(self, pid):
        delete_printer_by_id(pid)
        self._refresh()
