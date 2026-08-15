from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.textinput import TextInput
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.core.window import Window
import random

Window.softinput_mode = 'below_target'

class GameData:
    players = []
    mafia_count = 1
    doctor_count = 1
    detective_count = 1
    roles = {}

class SetupScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        layout = BoxLayout(orientation='vertical', padding=20, spacing=10)
        
        layout.add_widget(Label(text="لعبة المافيا (Mafia Game)", font_size='24sp', size_hint_y=0.2))
        
        self.input = TextInput(hint_text="أدخل أسماء اللاعبين مفصولة بفاصلة (,)", multiline=False, size_hint_y=0.2)
        layout.add_widget(self.input)
        
        btn = Button(text="بدء توزيع الأدوار", size_hint_y=0.2, background_color=(0.2, 0.8, 0.2, 1))
        btn.bind(on_press=self.start_game)
        layout.add_widget(btn)
        
        self.msg = Label(text="", size_hint_y=0.2, color=(1, 0, 0, 1))
        layout.add_widget(self.msg)
        
        self.add_widget(layout)

    def start_game(self, instance):
        names = [n.strip() for n in self.input.text.split(',') if n.strip()]
        if len(names) < 4:
            self.msg.text = "يجب إدخال 4 لاعبين على الأقل!"
            return
        
        GameData.players = names
        roles_pool = ['مافيا'] * GameData.mafia_count + ['طبيب'] * GameData.doctor_count + ['محقق'] * GameData.detective_count
        while len(roles_pool) < len(names):
            roles_pool.append('مواطن')
        
        random.shuffle(roles_pool)
        GameData.roles = {player: role for player, role in zip(names, roles_pool)}
        
        self.manager.current = 'reveal'

class RevealScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.index = 0
        self.layout = BoxLayout(orientation='vertical', padding=20, spacing=10)
        
        self.lbl = Label(text="", font_size='20sp', size_hint_y=0.6)
        self.layout.add_widget(self.lbl)
        
        self.btn = Button(text="كشف الدور", size_hint_y=0.2)
        self.btn.bind(on_press=self.toggle_role)
        self.layout.add_widget(self.btn)
        
        self.add_widget(self.layout)
        self.showing = False

    def on_enter(self):
        self.update_screen()

    def update_screen(self):
        if self.index < len(GameData.players):
            player = GameData.players[self.index]
            self.lbl.text = f"اعطِ الهاتف لـ: {player}"
            self.btn.text = "كشف الدور"
            self.showing = False
        else:
            self.lbl.text = "تم توزيع جميع الأدوار بنجاح!\nالآن تبدأ اللعبة."
            self.btn.text = "إنهاء"
            self.btn.bind(on_press=self.finish)

    def toggle_role(self, instance):
        if self.index >= len(GameData.players):
            return
        player = GameData.players[self.index]
        if not self.showing:
            self.lbl.text = f"دورك يا {player} هو:\n[ {GameData.roles[player]} ]"
            self.btn.text = "إخفاء وانسخ التلفون للبعده"
            self.showing = True
        else:
            self.index += 1
            self.update_screen()

    def finish(self, instance):
        App.get_running_app().stop()

class MafiaApp(App):
    def build(self):
        sm = ScreenManager()
        sm.add_widget(SetupScreen(name='setup'))
        sm.add_widget(RevealScreen(name='reveal'))
        return sm

if __name__ == '__main__':
    MafiaApp().run()
