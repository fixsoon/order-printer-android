"""期效标签打印界面 - 食材期效 + 食品留样"""

from datetime import datetime, timedelta
import threading

from kivy.uix.screenmanager import Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.popup import Popup
from kivy.uix.scrollview import ScrollView
from kivy.uix.spinner import Spinner
from kivy.metrics import dp

from core.storage import (
    get_ingredient_templates, get_food_sample_templates, get_default_operator,
    get_default_printer
)
from core.templates import ingredient_label_html, food_sample_label_html
from core.feie_api import print_html as feie_print
from core.config import STORAGE_TYPES, MEAL_TYPES, DEFAULT_LABEL_SN, DEFAULT_LABEL_KEY
from utils import log


# ============================================================
# 期效标签打印主界面
# ============================================================

class ExpiryLabelScreen(Screen):
    """期效标签打印主界面"""
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._build_ui()

    def on_enter(self):
        """每次进入时刷新经手人显示"""
        self._refresh_operator()

    def _build_ui(self):
        root = BoxLayout(orientation='vertical', padding=dp(12), spacing=dp(8))

        # 标题栏
        title_bar = BoxLayout(size_hint_y=None, height=dp(48))
        title_bar.add_widget(Button(
            text='← 返回', size_hint_x=None, width=dp(80),
            on_release=lambda x: setattr(self.manager, 'current', 'home')
        ))
        title_bar.add_widget(Label(
            text='[b]期效标签打印[/b]', markup=True,
            halign='center', valign='middle', font_size=dp(18)
        ))
        title_bar.add_widget(Label(size_hint_x=None, width=dp(80)))
        root.add_widget(title_bar)

        # 经手人提示
        self.op_label = Label(
            text='当前经手人: 未设置（请先添加）',
            size_hint_y=None, height=dp(28),
            color=(0.3, 0.6, 0.3, 1), font_size=dp(13)
        )
        root.add_widget(self.op_label)

        root.add_widget(Label(
            text='选择打印类型',
            size_hint_y=None, height=dp(25),
            color=(0.5, 0.5, 0.5, 1)
        ))

        root.add_widget(Button(
            text='[b]🥭 食材期效标签[/b]\n品名 / 储存温度 / 制作时间 / 有效期',
            markup=True,
            size_hint_y=None, height=dp(80),
            background_color=(0.9, 0.55, 0.2, 1),
            font_size=dp(15),
            on_release=lambda x: setattr(self.manager, 'current', 'ingredient_print')
        ))

        root.add_widget(Button(
            text='[b]🍽 食品留样标签[/b]\n食品名称 / 餐别 / 留样时间 / 重量 / 经手人',
            markup=True,
            size_hint_y=None, height=dp(80),
            background_color=(0.6, 0.3, 0.8, 1),
            font_size=dp(15),
            on_release=lambda x: setattr(self.manager, 'current', 'sample_print')
        ))

        # 标签规格说明
        root.add_widget(Label(
            text='标签规格: 40mm x 30mm | 打印机: SN 570202889',
            size_hint_y=None, height=dp(25),
            color=(0.5, 0.5, 0.5, 1), font_size=dp(11)
        ))

        self.add_widget(root)

    def _refresh_operator(self):
        default_op = get_default_operator()
        if default_op:
            self.op_label.text = f'当前经手人: {default_op["name"]}'
            self.op_label.color = (0.3, 0.6, 0.3, 1)
        else:
            self.op_label.text = '当前经手人: 未设置（请先添加）'
            self.op_label.color = (0.9, 0.3, 0.3, 1)

    def _show_toast(self, text):
        popup = Popup(
            title='提示', content=Label(text=text),
            size_hint=(0.8, None), height=dp(100),
            auto_dismiss=True
        )
        popup.open()
        from kivy.clock import Clock
        Clock.schedule_once(lambda dt: popup.dismiss(), 2)


# ============================================================
# 食材期效标签打印
# ============================================================

class IngredientPrintScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._selected_template = None
        self._build_ui()

    def on_enter(self):
        self._refresh_templates()

    def _build_ui(self):
        root = BoxLayout(orientation='vertical', padding=dp(12), spacing=dp(6))

        # 标题栏
        title_bar = BoxLayout(size_hint_y=None, height=dp(48))
        title_bar.add_widget(Button(
            text='← 返回', size_hint_x=None, width=dp(80),
            on_release=lambda x: setattr(self.manager, 'current', 'expiry_label')
        ))
        title_bar.add_widget(Label(
            text='[b]食材期效标签[/b]', markup=True,
            halign='center', valign='middle', font_size=dp(18)
        ))
        title_bar.add_widget(Label(size_hint_x=None, width=dp(80)))
        root.add_widget(title_bar)

        # 模板选择
        root.add_widget(Label(
            text='选择模板自动填充，或手动输入',
            size_hint_y=None, height=dp(22),
            color=(0.5, 0.5, 0.5, 1), font_size=dp(12)
        ))

        self.template_spinner = Spinner(
            text='-- 选择模板 --',
            values=['-- 手动输入 --'],
            size_hint_y=None, height=dp(40),
            on_text_validate=lambda: self._on_template_selected()
        )
        self.template_spinner.bind(text=lambda *x: self._on_template_selected())
        root.add_widget(self.template_spinner)

        # 表单
        form = BoxLayout(orientation='vertical', size_hint_y=None, spacing=dp(4))

        name_row = BoxLayout(size_hint_y=None, height=dp(40))
        name_row.add_widget(Label(text='品名:', size_hint_x=None, width=dp(60)))
        self.name_input = TextInput(hint_text='如: 芒果肉', multiline=False, size_hint_x=1)
        name_row.add_widget(self.name_input)
        form.add_widget(name_row)

        storage_row = BoxLayout(size_hint_y=None, height=dp(40))
        storage_row.add_widget(Label(text='储存:', size_hint_x=None, width=dp(60)))
        self.storage_spinner = Spinner(
            text='常温', values=STORAGE_TYPES,
            size_hint_x=1
        )
        storage_row.add_widget(self.storage_spinner)
        form.add_widget(storage_row)

        hours_row = BoxLayout(size_hint_y=None, height=dp(40))
        hours_row.add_widget(Label(text='有效时长:', size_hint_x=None, width=dp(60)))
        self.hours_input = TextInput(hint_text='24', multiline=False, input_filter='int', size_hint_x=0.35)
        hours_row.add_widget(self.hours_input)
        hours_row.add_widget(Label(text='小时', size_hint_x=None, width=dp(40)))
        form.add_widget(hours_row)

        copies_row = BoxLayout(size_hint_y=None, height=dp(40))
        copies_row.add_widget(Label(text='打印份数:', size_hint_x=None, width=dp(60)))
        self.copy_input = TextInput(text='1', multiline=False, input_filter='int', size_hint_x=0.35)
        copies_row.add_widget(self.copy_input)
        form.add_widget(copies_row)

        root.add_widget(form)

        # 提示
        root.add_widget(Label(
            text='制作时间以打印时间为准 | 有效期自动计算',
            size_hint_y=None, height=dp(22),
            color=(0.5, 0.5, 0.5, 1), font_size=dp(11)
        ))

        # 打印按钮
        root.add_widget(Button(
            text='🖨 打印标签',
            size_hint_y=None, height=dp(50),
            background_color=(0.2, 0.6, 0.8, 1),
            font_size=dp(16),
            on_release=lambda x: self._do_print()
        ))

        self.add_widget(root)

    def _refresh_templates(self):
        templates = get_ingredient_templates()
        values = ['-- 手动输入 --']
        if templates:
            values += [t['name'] for t in templates]
        self.template_spinner.values = values
        self.template_spinner.text = '-- 选择模板 --'

    def _on_template_selected(self):
        text = self.template_spinner.text
        if text == '-- 手动输入 --' or text == '-- 选择模板 --':
            return
        templates = get_ingredient_templates()
        for t in templates:
            if t['name'] == text:
                self.name_input.text = t['name']
                self.storage_spinner.text = t['storage_type']
                self.hours_input.text = str(t['valid_hours'])
                self._selected_template = t
                break

    def _do_print(self):
        name = self.name_input.text.strip()
        storage = self.storage_spinner.text

        try:
            hours = int(self.hours_input.text.strip()) if self.hours_input.text.strip() else 24
            copies = int(self.copy_input.text.strip()) if self.copy_input.text.strip() else 1
        except ValueError:
            self._show_toast('有效期和份数需为数字')
            return

        if not name:
            self._show_toast('请输入品名')
            return

        make_time = datetime.now()

        # 获取打印机
        printer = get_default_printer('label') or get_default_printer('cup')
        sn = DEFAULT_LABEL_SN
        key = DEFAULT_LABEL_KEY
        if printer:
            sn = printer.get('sn', sn)
            key = printer.get('key', key)

        self._run_print(name, storage, make_time, hours, copies, sn, key)

    def _run_print(self, name, storage, make_time, hours, copies, sn, key):
        self._show_toast(f'正在打印 {copies} 份...')
        log(f'食材期效标签: {name} {storage} {hours}h x{copies}')

        def do():
            ok = 0
            try:
                for i in range(copies):
                    html = ingredient_label_html(name, storage, make_time, hours)
                    feie_print(sn, html, key)
                    ok += 1
            except Exception as e:
                log(f'打印失败: {e}')

            def show_result(dt):
                if ok == copies:
                    self._show_toast(f'打印成功: {name} x{copies}')
                else:
                    self._show_toast(f'部分成功: {ok}/{copies}')

            from kivy.clock import Clock
            Clock.schedule_once(show_result)

        threading.Thread(target=do, daemon=True).start()

    def _show_toast(self, text):
        popup = Popup(
            title='提示', content=Label(text=text),
            size_hint=(0.8, None), height=dp(100),
            auto_dismiss=True
        )
        popup.open()
        from kivy.clock import Clock
        Clock.schedule_once(lambda dt: popup.dismiss(), 2)


# ============================================================
# 食品留样标签打印
# ============================================================

class SamplePrintScreen(Screen):
    """食品留样标签打印"""
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._selected_template = None
        self._build_ui()

    def on_enter(self):
        self._refresh_templates()
        self._refresh_operator()

    def _build_ui(self):
        root = BoxLayout(orientation='vertical', padding=dp(12), spacing=dp(6))

        # 标题栏
        title_bar = BoxLayout(size_hint_y=None, height=dp(48))
        title_bar.add_widget(Button(
            text='← 返回', size_hint_x=None, width=dp(80),
            on_release=lambda x: setattr(self.manager, 'current', 'expiry_label')
        ))
        title_bar.add_widget(Label(
            text='[b]食品留样标签[/b]', markup=True,
            halign='center', valign='middle', font_size=dp(18)
        ))
        title_bar.add_widget(Label(size_hint_x=None, width=dp(80)))
        root.add_widget(title_bar)

        # 经手人
        self.op_label = Label(
            text='经手人: 未设置',
            size_hint_y=None, height=dp(25),
            color=(0.9, 0.3, 0.3, 1), font_size=dp(13)
        )
        root.add_widget(self.op_label)

        # 模板选择
        root.add_widget(Label(
            text='选择模板自动填充，或手动输入',
            size_hint_y=None, height=dp(22),
            color=(0.5, 0.5, 0.5, 1), font_size=dp(12)
        ))

        self.template_spinner = Spinner(
            text='-- 选择模板 --',
            values=['-- 手动输入 --'],
            size_hint_y=None, height=dp(40),
        )
        self.template_spinner.bind(text=lambda *x: self._on_template_selected())
        root.add_widget(self.template_spinner)

        # 表单
        form = BoxLayout(orientation='vertical', size_hint_y=None, spacing=dp(4))

        name_row = BoxLayout(size_hint_y=None, height=dp(40))
        name_row.add_widget(Label(text='食品名称:', size_hint_x=None, width=dp(70)))
        self.name_input = TextInput(hint_text='食品名称', multiline=False, size_hint_x=1)
        name_row.add_widget(self.name_input)
        form.add_widget(name_row)

        meal_row = BoxLayout(size_hint_y=None, height=dp(40))
        meal_row.add_widget(Label(text='餐别:', size_hint_x=None, width=dp(70)))
        self.meal_spinner = Spinner(
            text='午餐', values=MEAL_TYPES,
            size_hint_x=1
        )
        meal_row.add_widget(self.meal_spinner)
        form.add_widget(meal_row)

        weight_row = BoxLayout(size_hint_y=None, height=dp(40))
        weight_row.add_widget(Label(text='留样重量:', size_hint_x=None, width=dp(70)))
        self.weight_input = TextInput(hint_text='150g', multiline=False, size_hint_x=0.5)
        weight_row.add_widget(self.weight_input)
        form.add_widget(weight_row)

        copies_row = BoxLayout(size_hint_y=None, height=dp(40))
        copies_row.add_widget(Label(text='打印份数:', size_hint_x=None, width=dp(70)))
        self.copy_input = TextInput(text='1', multiline=False, input_filter='int', size_hint_x=0.35)
        copies_row.add_widget(self.copy_input)
        form.add_widget(copies_row)

        root.add_widget(form)

        root.add_widget(Label(
            text='留样时间以打印时间为准',
            size_hint_y=None, height=dp(22),
            color=(0.5, 0.5, 0.5, 1), font_size=dp(11)
        ))

        root.add_widget(Button(
            text='🖨 打印标签',
            size_hint_y=None, height=dp(50),
            background_color=(0.6, 0.3, 0.8, 1),
            font_size=dp(16),
            on_release=lambda x: self._do_print()
        ))

        self.add_widget(root)

    def _refresh_templates(self):
        templates = get_food_sample_templates()
        values = ['-- 手动输入 --']
        if templates:
            values += [t['name'] for t in templates]
        self.template_spinner.values = values
        self.template_spinner.text = '-- 选择模板 --'

    def _refresh_operator(self):
        default_op = get_default_operator()
        if default_op:
            self.op_label.text = f'经手人: {default_op["name"]}'
            self.op_label.color = (0.3, 0.6, 0.3, 1)
        else:
            self.op_label.text = '经手人: 未设置'
            self.op_label.color = (0.9, 0.3, 0.3, 1)

    def _on_template_selected(self):
        text = self.template_spinner.text
        if text == '-- 手动输入 --' or text == '-- 选择模板 --':
            return
        templates = get_food_sample_templates()
        for t in templates:
            if t['name'] == text:
                self.name_input.text = t['name']
                self.weight_input.text = t['default_weight']
                self._selected_template = t
                break

    def _do_print(self):
        name = self.name_input.text.strip()
        meal = self.meal_spinner.text
        weight = self.weight_input.text.strip() or '150g'

        try:
            copies = int(self.copy_input.text.strip()) if self.copy_input.text.strip() else 1
        except ValueError:
            self._show_toast('份数需为数字')
            return

        if not name:
            self._show_toast('请输入食品名称')
            return

        default_op = get_default_operator()
        operator = default_op['name'] if default_op else ''

        sample_time = datetime.now()

        printer = get_default_printer('label') or get_default_printer('cup')
        sn = DEFAULT_LABEL_SN
        key = DEFAULT_LABEL_KEY
        if printer:
            sn = printer.get('sn', sn)
            key = printer.get('key', key)

        self._run_print(name, meal, sample_time, weight, operator, copies, sn, key)

    def _run_print(self, name, meal, sample_time, weight, operator, copies, sn, key):
        self._show_toast(f'正在打印 {copies} 份...')
        log(f'食品留样标签: {name} {meal} {weight} {operator} x{copies}')

        def do():
            ok = 0
            try:
                for i in range(copies):
                    html = food_sample_label_html(name, meal, sample_time, weight, operator)
                    feie_print(sn, html, key)
                    ok += 1
            except Exception as e:
                log(f'打印失败: {e}')

            def show_result(dt):
                if ok == copies:
                    self._show_toast(f'打印成功: {name} x{copies}')
                else:
                    self._show_toast(f'部分成功: {ok}/{copies}')

            from kivy.clock import Clock
            Clock.schedule_once(show_result)

        threading.Thread(target=do, daemon=True).start()

    def _show_toast(self, text):
        popup = Popup(
            title='提示', content=Label(text=text),
            size_hint=(0.8, None), height=dp(100),
            auto_dismiss=True
        )
        popup.open()
        from kivy.clock import Clock
        Clock.schedule_once(lambda dt: popup.dismiss(), 2)
