"""排版预览（纯 Kivy）"""

from kivy.uix.screenmanager import Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.graphics import Color, Rectangle
from core.storage import get_default_printer, is_cup_product
from core.templates import receipt_html, cup_label_html


class PreviewScreen(Screen):
    def on_enter(self):
        if not hasattr(self, 'preview_label'):
            self._build_ui()
        self._refresh()

    def _build_ui(self):
        from kivy.metrics import dp
        root = BoxLayout(orientation='vertical', padding=dp(12), spacing=dp(8))

        root.add_widget(Label(
            text='[b]排版预览[/b]', markup=True, halign='center',
            size_hint_y=None, height=dp(44), font_size=dp(18)
        ))

        self.preview_label = Label(
            text='请先在主页导入 Excel 文件\n然后返回此处查看预览',
            halign='center', valign='middle', color=(0.5, 0.5, 0.5, 1)
        )
        root.add_widget(self.preview_label)

        info_box = BoxLayout(size_hint_y=None, height=dp(36), spacing=dp(8))
        info_box.add_widget(Button(
            text='← 返回主页', background_color=(0.4, 0.4, 0.4, 1),
            on_release=lambda x: setattr(self.manager, 'current', 'home')
        ))
        info_box.add_widget(Button(
            text='刷新预览', background_color=(0.3, 0.7, 0.3, 1),
            on_release=lambda x: self._refresh()
        ))
        root.add_widget(info_box)
        self.add_widget(root)

    def _refresh(self):
        from kivy.uix.screenmanager import ScreenManager
        home = None
        for screen in self.manager.screens:
            if screen.name == 'home':
                home = screen
                break
        if home and home.df is not None and len(home.df) > 0:
            df = home.df
            sample = df.iloc[0]
            printer = get_default_printer('receipt')
            if printer:
                try:
                    item = {'orders': [{'chain': sample.get('接龙号', ''), 'school': sample.get('学校', ''),
                                       'student': sample.get('学生姓名', ''),
                                       'total': sample.get('商品金额', 0),
                                       'items': [{'name': sample.get('商品名称', ''), 'qty': sample.get('数量', 1),
                                                  'price': sample.get('商品金额', 0)}]}],
                            'total': sample.get('商品金额', 0)}
                    html = receipt_html(item)
                    self.preview_label.text = f'[模拟收银小票预览]\n接龙号: {sample.get("接龙号","")}\n学生: {sample.get("学生姓名","")}\n商品: {sample.get("商品名称","")}\n\n完整 HTML 已生成，共 {len(html)} 字符'
                    self.preview_label.markup = True
                except Exception as e:
                    self.preview_label.text = f'预览生成失败: {e}'
            else:
                self.preview_label.text = '请先在打印机设置中添加打印机'
        else:
            self.preview_label.text = '请先在主页导入 Excel 文件\n然后返回此处查看预览'
