"""经手人管理界面"""

from kivy.uix.screenmanager import Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.popup import Popup
from kivy.uix.scrollview import ScrollView
from kivy.metrics import dp
from kivy.uix.checkbox import CheckBox

from core.storage import (
    get_operators, add_operator, remove_operator,
    set_default_operator, get_default_operator
)
from utils import log


class OperatorManageScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._build_ui()

    def _build_ui(self):
        root = BoxLayout(orientation='vertical', padding=dp(12), spacing=dp(8))

        # 标题栏
        title_bar = BoxLayout(size_hint_y=None, height=dp(48))
        title_bar.add_widget(Button(
            text='← 返回', size_hint_x=None, width=dp(80),
            on_release=lambda x: setattr(self.manager, 'current', 'home')
        ))
        title_bar.add_widget(Label(
            text='[b]经手人管理[/b]', markup=True,
            halign='center', valign='middle', font_size=dp(18)
        ))
        title_bar.add_widget(Label(size_hint_x=None, width=dp(80)))
        root.add_widget(title_bar)

        # 当前默认经手人提示
        default_op = get_default_operator()
        default_name = default_op['name'] if default_op else '未设置'
        self.default_label = Label(
            text=f'当前默认: {default_name}',
            size_hint_y=None, height=dp(30),
            color=(0.3, 0.6, 0.3, 1), font_size=dp(14)
        )
        root.add_widget(self.default_label)

        # 添加经手人
        add_box = BoxLayout(size_hint_y=None, height=dp(44), spacing=dp(8))
        self.name_input = TextInput(
            hint_text='输入经手人姓名', multiline=False,
            size_hint_x=1, padding=[dp(8), dp(8), 0, 0]
        )
        add_box.add_widget(self.name_input)
        add_box.add_widget(Button(
            text='添加', size_hint_x=None, width=dp(70),
            background_color=(0.2, 0.6, 0.3, 1),
            on_release=lambda x: self._add_operator()
        ))
        root.add_widget(add_box)

        # 列表标题
        root.add_widget(Label(
            text='经手人列表（点击行设为默认）',
            size_hint_y=None, height=dp(25),
            halign='left', font_size=dp(13), color=(0.5, 0.5, 0.5, 1)
        ))

        # 经手人列表
        self.list_container = BoxLayout(orientation='vertical', size_hint_y=None)
        self.list_container.bind(minimum_height=self.list_container.setter('height'))
        scroll = ScrollView(size_hint_y=1)
        scroll.add_widget(self.list_container)
        root.add_widget(scroll)

        # 空状态提示
        self.empty_label = Label(
            text='暂无经手人，请添加',
            size_hint_y=None, height=dp(60),
            color=(0.6, 0.6, 0.6, 1)
        )
        root.add_widget(self.empty_label)

        self.add_widget(root)
        self._refresh_list()

    def _refresh_list(self):
        self.list_container.clear_children()
        operators = get_operators()
        default_op = get_default_operator()
        default_name = default_op['name'] if default_op else ''

        if not operators:
            self.empty_label.height = dp(60)
        else:
            self.empty_label.height = 0
            for op in operators:
                row = OperatorRow(
                    name=op['name'],
                    is_default=(op['name'] == default_name),
                    on_set_default=lambda n: self._set_default(n),
                    on_delete=lambda n: self._delete_operator(n)
                )
                self.list_container.add_widget(row)

    def _add_operator(self):
        name = self.name_input.text.strip()
        if not name:
            self._show_toast('请输入经手人姓名')
            return
        try:
            add_operator(name)
            self.name_input.text = ''
            self._refresh_list()
            self._show_toast(f'已添加: {name}')
        except Exception as e:
            log(f"添加经手人失败: {e}")
            self._show_toast('添加失败')

    def _set_default(self, name):
        set_default_operator(name)
        self._refresh_list()
        self.default_label.text = f'当前默认: {name}'
        self._show_toast(f'已设为默认: {name}')

    def _delete_operator(self, name):
        remove_operator(name)
        self._refresh_list()
        default_op = get_default_operator()
        self.default_label.text = f'当前默认: {default_op["name"] if default_op else "未设置"}'

    def _show_toast(self, text):
        popup = Popup(
            title='提示', content=Label(text=text),
            size_hint=(0.8, None), height=dp(100),
            auto_dismiss=True
        )
        popup.open()
        from kivy.clock import Clock
        Clock.schedule_once(lambda dt: popup.dismiss(), 2)


class OperatorRow(BoxLayout):
    """经手人列表行"""
    def __init__(self, name, is_default, on_set_default, on_delete, **kwargs):
        super().__init__(
            orientation='horizontal', size_hint_y=None, height=dp(46),
            spacing=dp(6), **kwargs
        )
        self._name = name
        self._on_set_default = on_set_default
        self._on_delete = on_delete

        # 默认标记
        if is_default:
            badge = Button(
                text='默认', size_hint_x=None, width=dp(40),
                background_color=(0.2, 0.7, 0.3, 1),
                on_release=lambda x: self._on_set_default(name)
            )
        else:
            badge = Button(
                text='设为默认', size_hint_x=None, width=dp(60),
                background_color=(0.4, 0.4, 0.4, 1),
                on_release=lambda x: self._on_set_default(name)
            )
        self.add_widget(badge)

        # 姓名
        name_label = Button(
            text=name, valign='middle',
            background_color=(0.95, 0.95, 0.95, 1),
            color=(0.2, 0.2, 0.2, 1),
            on_release=lambda x: self._on_set_default(name)
        )
        self.add_widget(name_label)

        # 删除按钮
        del_btn = Button(
            text='删除', size_hint_x=None, width=dp(60),
            background_color=(0.9, 0.3, 0.3, 1),
            on_release=lambda x: self._on_delete(name)
        )
        self.add_widget(del_btn)
