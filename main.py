import os
import subprocess
import sys

try:
    import arabic_reshaper
    from bidi.algorithm import get_display
except ImportError:
    subprocess.check_call(
        [
            sys.executable,
            "-m",
            "pip",
            "install",
            "arabic-reshaper",
            "python-bidi",
            "--trusted-host",
            "pypi.org",
            "--trusted-host",
            "files.pythonhosted.org",
        ]
    )
    import arabic_reshaper
    from bidi.algorithm import get_display

import random
import pygame

pygame.init()


def ar(text):
    reshaped_text = arabic_reshaper.reshape(text)
    return get_display(reshaped_text)


# الشاشة
WIDTH, HEIGHT = 800, 600
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("لعبة المافيا الاحترافية")

# الألوان
DARK_BLUE = (20, 25, 40)
NIGHT_BLUE = (10, 15, 30)
WHITE = (255, 255, 255)
GOLD = (230, 180, 50)
RED = (200, 50, 50)
GREEN = (40, 180, 90)
GRAY = (120, 130, 150)
LIGHT_BLUE = (50, 60, 90)
INPUT_BG = (35, 45, 65)

font_title = pygame.font.SysFont("arial", 26, bold=True)
font_sub = pygame.font.SysFont("arial", 18, bold=True)

# المتغيرات
game_state = 0
num_players = 4
player_names = []
player_roles = []
players_alive = []

current_name_idx = 0
current_player_idx = 0
show_card = False
input_text = ""
winner_msg = ""

# أدوار الليل
mafia_target = None
doctor_target = None
detective_result = ""

# التصويت
voting_voter_queue = []
current_voter_idx = 0
show_vote_screen = False
votes_list = []
night_result_msg = ""
vote_result_msg = ""


def reset_night_vars():
    global mafia_target, doctor_target, detective_result
    mafia_target = None
    doctor_target = None
    detective_result = ""


def setup_game():
    global player_roles, current_player_idx, show_card, players_alive
    roles_pool = ["مافيا", "طبيب", "محقق"]
    if len(player_names) >= 7:
        roles_pool.append("مافيا")
    while len(roles_pool) < len(player_names):
        roles_pool.append("مواطن")

    player_roles = roles_pool.copy()
    random.shuffle(player_roles)

    players_alive = [True] * len(player_names)
    current_player_idx = 0
    show_card = False
    reset_night_vars()


def add_current_name():
    global input_text, current_name_idx, game_state
    name_to_add = (
        input_text.strip()
        if input_text.strip()
        else f"لاعب {current_name_idx + 1}"
    )
    player_names.append(name_to_add)
    input_text = ""
    current_name_idx += 1
    if current_name_idx >= num_players:
        setup_game()
        game_state = 2


def process_night():
    global night_result_msg
    if mafia_target is not None and mafia_target != doctor_target:
        players_alive[mafia_target] = False
        night_result_msg = (
            f"للأسف، تم اغتيال اللاعب ({player_names[mafia_target]}) البارحة!"
        )
    else:
        night_result_msg = "مرت الليلة بسلام! قامت الحماية بإنقاذ الضحية."
    check_win()


def count_votes_and_eliminate():
    global vote_result_msg
    if not votes_list:
        vote_result_msg = "لم يصوّت أحد!"
        return

    vote_counts = {}
    for target in votes_list:
        vote_counts[target] = vote_counts.get(target, 0) + 1

    max_votes = max(vote_counts.values())
    top_targets = [
        target
        for target, count in vote_counts.items()
        if count == max_votes
    ]

    if len(top_targets) > 1:
        vote_result_msg = "تعادلت الأصوات! لم يتم إقصاء أحد في هذه الجولة."
    else:
        winner_target = top_targets[0]
        if winner_target == "SKIP":
            vote_result_msg = (
                "قرر أغلبية اللاعبين التخطي (Skip)! لم يتم إقصاء أحد."
            )
        else:
            eliminated = winner_target
            players_alive[eliminated] = False
            vote_result_msg = f"بناءً على التصويت، تم إقصاء اللاعب ({player_names[eliminated]})!"

    check_win()


def check_win():
    global game_state, winner_msg
    mafia_count = sum(
        1
        for i in range(len(player_names))
        if players_alive[i] and player_roles[i] == "مافيا"
    )
    others_count = sum(
        1
        for i in range(len(player_names))
        if players_alive[i] and player_roles[i] != "مافيا"
    )

    if mafia_count == 0:
        winner_msg = "فاز المواطنون! تم القضاء على جميع أفراد المافيا 🎉"
        game_state = 9
    elif mafia_count >= others_count:
        winner_msg = "فازت المافيا! تمت السيطرة على المدينة 🕵️‍♂️"
        game_state = 9


def get_next_night_state():
    reset_night_vars()

    has_mafia = any(
        players_alive[i] and player_roles[i] == "مافيا"
        for i in range(len(player_names))
    )
    if has_mafia:
        return 3

    has_doc = any(
        players_alive[i] and player_roles[i] == "طبيب"
        for i in range(len(player_names))
    )
    if has_doc:
        return 4

    has_det = any(
        players_alive[i] and player_roles[i] == "محقق"
        for i in range(len(player_names))
    )
    if has_det:
        return 5

    process_night()
    return 6 if game_state != 9 else 9


running = True
while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

        if game_state == 1 and event.type == pygame.KEYDOWN:
            if event.key == pygame.K_RETURN:
                add_current_name()
            elif event.key == pygame.K_BACKSPACE:
                input_text = input_text[:-1]
            else:
                if len(input_text) < 15:
                    input_text += event.unicode

        if event.type == pygame.MOUSEBUTTONDOWN:
            mouse_pos = event.pos

            # 0️⃣ اختيار عدد اللاعبين
            if game_state == 0:
                plus_btn = pygame.Rect(WIDTH // 2 + 70, 230, 50, 50)
                minus_btn = pygame.Rect(WIDTH // 2 - 120, 230, 50, 50)
                start_btn = pygame.Rect(WIDTH // 2 - 100, 340, 200, 50)

                if plus_btn.collidepoint(mouse_pos) and num_players < 10:
                    num_players += 1
                elif minus_btn.collidepoint(mouse_pos) and num_players > 4:
                    num_players -= 1
                elif start_btn.collidepoint(mouse_pos):
                    player_names = []
                    current_name_idx = 0
                    input_text = ""
                    game_state = 1

            # 1️⃣ إضافة الأسماء
            elif game_state == 1:
                confirm_btn = pygame.Rect(WIDTH // 2 - 100, 280, 200, 50)
                del_btn = pygame.Rect(WIDTH // 2 + 110, 200, 60, 50)
                if confirm_btn.collidepoint(mouse_pos):
                    add_current_name()
                elif del_btn.collidepoint(mouse_pos):
                    input_text = input_text[:-1]

            # 2️⃣ كشف الكروت
            elif game_state == 2:
                action_btn = pygame.Rect(WIDTH // 2 - 120, 380, 240, 50)
                if action_btn.collidepoint(mouse_pos):
                    if not show_card:
                        show_card = True
                    else:
                        show_card = False
                        current_player_idx += 1
                        if current_player_idx >= len(player_roles):
                            game_state = get_next_night_state()

            # 3️⃣ المافيا (اصلاح تحديد الهدف الدقيق)
            elif game_state == 3:
                y_offset = 180
                for i in range(len(player_names)):
                    if players_alive[i] and player_roles[i] != "مافيا":
                        btn = pygame.Rect(WIDTH // 2 - 100, y_offset, 200, 35)
                        if btn.collidepoint(mouse_pos):
                            mafia_target = i
                            has_doc = any(
                                players_alive[j] and player_roles[j] == "طبيب"
                                for j in range(len(player_names))
                            )
                            has_det = any(
                                players_alive[j] and player_roles[j] == "محقق"
                                for j in range(len(player_names))
                            )
                            if has_doc:
                                game_state = 4
                            elif has_det:
                                game_state = 5
                            else:
                                process_night()
                                if game_state != 9:
                                    game_state = 6
                            break
                        y_offset += 45

            # 4️⃣ الطبيب
            elif game_state == 4:
                y_offset = 180
                for i in range(len(player_names)):
                    if players_alive[i]:
                        btn = pygame.Rect(WIDTH // 2 - 100, y_offset, 200, 35)
                        if btn.collidepoint(mouse_pos):
                            doctor_target = i
                            has_det = any(
                                players_alive[j] and player_roles[j] == "محقق"
                                for j in range(len(player_names))
                            )
                            if has_det:
                                game_state = 5
                            else:
                                process_night()
                                if game_state != 9:
                                    game_state = 6
                            break
                        y_offset += 45

            # 5️⃣ المحقق
            elif game_state == 5:
                if not detective_result:
                    y_offset = 180
                    for i in range(len(player_names)):
                        if players_alive[i] and player_roles[i] != "محقق":
                            btn = pygame.Rect(
                                WIDTH // 2 - 100, y_offset, 200, 35
                            )
                            if btn.collidepoint(mouse_pos):
                                is_m = player_roles[i] == "مافيا"
                                detective_result = f"اللاعب {player_names[i]} : {'مافيا 🔴' if is_m else 'بريء 🟢'}"
                                break
                        y_offset += 45
                else:
                    next_btn = pygame.Rect(WIDTH // 2 - 100, 420, 200, 45)
                    if next_btn.collidepoint(mouse_pos):
                        process_night()
                        if game_state != 9:
                            game_state = 6

            # 6️⃣ نتائج الليل
            elif game_state == 6:
                start_vote_btn = pygame.Rect(
                    WIDTH // 2 - 120, HEIGHT - 90, 240, 45
                )
                if start_vote_btn.collidepoint(mouse_pos):
                    voting_voter_queue = [
                        i
                        for i in range(len(player_names))
                        if players_alive[i]
                    ]
                    current_voter_idx = 0
                    show_vote_screen = False
                    votes_list = []
                    game_state = 7

            # 7️⃣ التصويت الفردي (مُعالج بشكل مباشر ودقيق)
            elif game_state == 7:
                if current_voter_idx < len(voting_voter_queue):
                    voter_id = voting_voter_queue[current_voter_idx]
                    if not show_vote_screen:
                        open_btn = pygame.Rect(WIDTH // 2 - 120, 320, 240, 50)
                        if open_btn.collidepoint(mouse_pos):
                            show_vote_screen = True
                    else:
                        y_offset = 110
                        voted_in_this_click = False

                        # فحص خيارات الضغط على اللاعبين
                        for target_id in range(len(player_names)):
                            if players_alive[target_id] and target_id != voter_id:
                                btn = pygame.Rect(
                                    WIDTH // 2 - 100, y_offset, 200, 32
                                )
                                if btn.collidepoint(mouse_pos):
                                    votes_list.append(target_id)
                                    show_vote_screen = False
                                    current_voter_idx += 1
                                    voted_in_this_click = True
                                    break
                                y_offset += 38

                        # زر Skip التخطي
                        if not voted_in_this_click:
                            skip_btn = pygame.Rect(
                                WIDTH // 2 - 100, HEIGHT - 75, 200, 40
                            )
                            if skip_btn.collidepoint(mouse_pos):
                                votes_list.append("SKIP")
                                show_vote_screen = False
                                current_voter_idx += 1

                        # التحقق هل انتهى التصويت للجميع
                        if current_voter_idx >= len(voting_voter_queue):
                            count_votes_and_eliminate()
                            if game_state != 9:
                                game_state = 8

            # 8️⃣ نتيجة التصويت والانتقال
            elif game_state == 8:
                next_night_btn = pygame.Rect(
                    WIDTH // 2 - 110, HEIGHT - 90, 220, 45
                )
                if next_night_btn.collidepoint(mouse_pos):
                    game_state = get_next_night_state()

            # 9️⃣ النهاية
            elif game_state == 9:
                restart_btn = pygame.Rect(WIDTH // 2 - 100, 400, 200, 50)
                if restart_btn.collidepoint(mouse_pos):
                    game_state = 0

    # ----- الرسم -----
    screen.fill(NIGHT_BLUE if game_state in [3, 4, 5] else DARK_BLUE)

    if game_state == 0:
        title = font_title.render(ar("لعبة المافيا الاحترافية"), True, GOLD)
        screen.blit(title, (WIDTH // 2 - title.get_width() // 2, 80))
        subtitle = font_sub.render(ar("حدد عدد اللاعبين:"), True, WHITE)
        screen.blit(subtitle, (WIDTH // 2 - subtitle.get_width() // 2, 170))

        minus_btn = pygame.Rect(WIDTH // 2 - 120, 230, 50, 50)
        plus_btn = pygame.Rect(WIDTH // 2 + 70, 230, 50, 50)
        pygame.draw.rect(screen, LIGHT_BLUE, minus_btn, border_radius=10)
        pygame.draw.rect(screen, LIGHT_BLUE, plus_btn, border_radius=10)
        screen.blit(
            font_title.render("-", True, WHITE),
            (minus_btn.x + 18, minus_btn.y + 2),
        )
        screen.blit(
            font_title.render("+", True, WHITE),
            (plus_btn.x + 15, plus_btn.y + 2),
        )

        num_txt = font_title.render(str(num_players), True, GOLD)
        screen.blit(num_txt, (WIDTH // 2 - num_txt.get_width() // 2, 235))

        start_btn = pygame.Rect(WIDTH // 2 - 100, 340, 200, 50)
        pygame.draw.rect(screen, RED, start_btn, border_radius=10)
        btn_txt = font_sub.render(ar("التالي: كتابة الأسماء"), True, WHITE)
        screen.blit(
            btn_txt,
            (start_btn.x + (200 - btn_txt.get_width()) // 2, start_btn.y + 12),
        )

    elif game_state == 1:
        title = font_title.render(
            ar(f"اسم اللاعب ({current_name_idx + 1} من {num_players}):"),
            True,
            GOLD,
        )
        screen.blit(title, (WIDTH // 2 - title.get_width() // 2, 110))

        input_box = pygame.Rect(WIDTH // 2 - 160, 200, 260, 50)
        pygame.draw.rect(screen, INPUT_BG, input_box, border_radius=10)
        pygame.draw.rect(screen, GOLD, input_box, 2, border_radius=10)

        del_btn = pygame.Rect(WIDTH // 2 + 110, 200, 60, 50)
        pygame.draw.rect(screen, RED, del_btn, border_radius=10)
        del_txt = font_sub.render(ar("مسح"), True, WHITE)
        screen.blit(
            del_txt,
            (del_btn.x + (60 - del_txt.get_width()) // 2, del_btn.y + 12),
        )

        display_str = input_text if input_text else "اكتب الاسم..."
        txt_surface = font_sub.render(
            ar(display_str), True, WHITE if input_text else GRAY
        )
        screen.blit(
            txt_surface,
            (input_box.x + (260 - txt_surface.get_width()) // 2, input_box.y + 12),
        )

        confirm_btn = pygame.Rect(WIDTH // 2 - 100, 280, 200, 50)
        pygame.draw.rect(screen, GREEN, confirm_btn, border_radius=10)
        conf_txt = font_sub.render(ar("حفظ والتالي ->"), True, WHITE)
        screen.blit(
            conf_txt,
            (
                confirm_btn.x + (200 - conf_txt.get_width()) // 2,
                confirm_btn.y + 12,
            ),
        )

    elif game_state == 2:
        p_name = player_names[current_player_idx]
        title = font_title.render(ar(f"دور اللاعب: {p_name}"), True, GOLD)
        screen.blit(title, (WIDTH // 2 - title.get_width() // 2, 80))

        card_rect = pygame.Rect(WIDTH // 2 - 150, 150, 300, 180)
        pygame.draw.rect(
            screen, GRAY if not show_card else GOLD, card_rect, border_radius=15
        )

        if show_card:
            role_str = player_roles[current_player_idx]
            role_txt = font_title.render(ar(role_str), True, DARK_BLUE)
            screen.blit(
                role_txt,
                (
                    card_rect.x + (300 - role_txt.get_width()) // 2,
                    card_rect.y + 65,
                ),
            )
        else:
            hide_txt = font_sub.render(
                ar(f"يا {p_name} اضغط للكشف عن دورك"), True, WHITE
            )
            screen.blit(
                hide_txt,
                (
                    card_rect.x + (300 - hide_txt.get_width()) // 2,
                    card_rect.y + 75,
                ),
            )

        action_btn = pygame.Rect(WIDTH // 2 - 120, 380, 240, 50)
        pygame.draw.rect(screen, GREEN, action_btn, border_radius=10)
        btn_str = "اكشف الكرت" if not show_card else "إخفاء والتالي"
        action_txt = font_sub.render(ar(btn_str), True, WHITE)
        screen.blit(
            action_txt,
            (
                action_btn.x + (240 - action_txt.get_width()) // 2,
                action_btn.y + 12,
            ),
        )

    elif game_state == 3:
        title = font_title.render(ar("الليل: دور المافيا 🕵️‍♂️"), True, RED)
        sub = font_sub.render(
            ar("اختر اللاعب المراد قتله بالسر:"), True, WHITE
        )
        screen.blit(title, (WIDTH // 2 - title.get_width() // 2, 60))
        screen.blit(sub, (WIDTH // 2 - sub.get_width() // 2, 120))

        y_offset = 180
        for i, name in enumerate(player_names):
            if players_alive[i] and player_roles[i] != "مافيا":
                btn = pygame.Rect(WIDTH // 2 - 100, y_offset, 200, 35)
                pygame.draw.rect(screen, RED, btn, border_radius=8)
                txt = font_sub.render(ar(f"اغتيال {name}"), True, WHITE)
                screen.blit(txt, (btn.x + (200 - txt.get_width()) // 2, btn.y + 7))
                y_offset += 45

    elif game_state == 4:
        title = font_title.render(ar("الليل: دور الطبيب 🩺"), True, GREEN)
        sub = font_sub.render(
            ar("اختر اللاعب المراد حمايته:"), True, WHITE
        )
        screen.blit(title, (WIDTH // 2 - title.get_width() // 2, 60))
        screen.blit(sub, (WIDTH // 2 - sub.get_width() // 2, 120))

        y_offset = 180
        for i, name in enumerate(player_names):
            if players_alive[i]:
                btn = pygame.Rect(WIDTH // 2 - 100, y_offset, 200, 35)
                pygame.draw.rect(screen, GREEN, btn, border_radius=8)
                txt = font_sub.render(ar(f"حماية {name}"), True, WHITE)
                screen.blit(txt, (btn.x + (200 - txt.get_width()) // 2, btn.y + 7))
                y_offset += 45

    elif game_state == 5:
        title = font_title.render(ar("الليل: دور المحقق 🔍"), True, GOLD)
        screen.blit(title, (WIDTH // 2 - title.get_width() // 2, 60))

        if not detective_result:
            sub = font_sub.render(
                ar("اختر لاعباً للتحقيق عن هويته:"), True, WHITE
            )
            screen.blit(sub, (WIDTH // 2 - sub.get_width() // 2, 120))
            y_offset = 180
            for i, name in enumerate(player_names):
                if players_alive[i] and player_roles[i] != "محقق":
                    btn = pygame.Rect(WIDTH // 2 - 100, y_offset, 200, 35)
                    pygame.draw.rect(screen, GOLD, btn, border_radius=8)
                    txt = font_sub.render(
                        ar(f"التحقيق مع {name}"), True, DARK_BLUE
                    )
                    screen.blit(
                        txt, (btn.x + (200 - txt.get_width()) // 2, btn.y + 7)
                    )
                    y_offset += 45
        else:
            res_txt = font_title.render(ar(detective_result), True, WHITE)
            screen.blit(res_txt, (WIDTH // 2 - res_txt.get_width() // 2, 220))

            next_btn = pygame.Rect(WIDTH // 2 - 100, 420, 200, 45)
            pygame.draw.rect(screen, GREEN, next_btn, border_radius=10)
            n_txt = font_sub.render(ar("متابعة ->"), True, WHITE)
            screen.blit(
                n_txt, (next_btn.x + (200 - n_txt.get_width()) // 2, next_btn.y + 10)
            )

    elif game_state == 6:
        title = font_title.render(ar("أشرقت الشمس ☀️"), True, GOLD)
        screen.blit(title, (WIDTH // 2 - title.get_width() // 2, 80))

        res_txt = font_sub.render(ar(night_result_msg), True, WHITE)
        screen.blit(res_txt, (WIDTH // 2 - res_txt.get_width() // 2, 180))

        start_vote_btn = pygame.Rect(WIDTH // 2 - 120, HEIGHT - 90, 240, 45)
        pygame.draw.rect(screen, RED, start_vote_btn, border_radius=10)
        v_txt = font_sub.render(ar("الانتقال للتصويت السري 🗳️"), True, WHITE)
        screen.blit(v_txt, (start_vote_btn.x + 15, start_vote_btn.y + 10))

    elif game_state == 7:
        if current_voter_idx < len(voting_voter_queue):
            voter_id = voting_voter_queue[current_voter_idx]
            voter_name = player_names[voter_id]

            if not show_vote_screen:
                title = font_title.render(
                    ar(f"دور اللاعب: {voter_name}"), True, GOLD
                )
                sub = font_sub.render(
                    ar("سلم الجهاز لهذا اللاعب للتصويت بالسر!"), True, WHITE
                )
                screen.blit(title, (WIDTH // 2 - title.get_width() // 2, 140))
                screen.blit(sub, (WIDTH // 2 - sub.get_width() // 2, 220))

                open_btn = pygame.Rect(WIDTH // 2 - 120, 320, 240, 50)
                pygame.draw.rect(screen, GREEN, open_btn, border_radius=10)
                o_txt = font_sub.render(ar("أنا جاهز، فتح التصويت"), True, WHITE)
                screen.blit(
                    o_txt,
                    (
                        open_btn.x + (240 - o_txt.get_width()) // 2,
                        open_btn.y + 12,
                    ),
                )
            else:
                title = font_title.render(
                    ar(f"تصويت {voter_name}: اختر المشتبه به"), True, GOLD
                )
                screen.blit(title, (WIDTH // 2 - title.get_width() // 2, 40))

                y_offset = 110
                for target_id, name in enumerate(player_names):
                    if players_alive[target_id] and target_id != voter_id:
                        btn = pygame.Rect(WIDTH // 2 - 100, y_offset, 200, 32)
                        pygame.draw.rect(screen, RED, btn, border_radius=8)
                        txt = font_sub.render(ar(f"تصويت ضد {name}"), True, WHITE)
                        screen.blit(
                            txt,
                            (btn.x + (200 - txt.get_width()) // 2, btn.y + 5),
                        )
                        y_offset += 38

                skip_btn = pygame.Rect(WIDTH // 2 - 100, HEIGHT - 75, 200, 40)
                pygame.draw.rect(screen, GRAY, skip_btn, border_radius=8)
                s_txt = font_sub.render(ar("تخطي (Skip) ⏭️"), True, WHITE)
                screen.blit(
                    s_txt,
                    (
                        skip_btn.x + (200 - s_txt.get_width()) // 2,
                        skip_btn.y + 10,
                    ),
                )

    elif game_state == 8:
        title = font_title.render(ar("نتيجة التصويت الجماعي 📊"), True, GOLD)
        screen.blit(title, (WIDTH // 2 - title.get_width() // 2, 100))

        res_txt = font_sub.render(ar(vote_result_msg), True, WHITE)
        screen.blit(res_txt, (WIDTH // 2 - res_txt.get_width() // 2, 200))

        next_night_btn = pygame.Rect(
            WIDTH // 2 - 110, HEIGHT - 90, 220, 45
        )
        pygame.draw.rect(screen, LIGHT_BLUE, next_night_btn, border_radius=10)
        nn_txt = font_sub.render(ar("الانتقال لـ الليل 🌙"), True, WHITE)
        screen.blit(nn_txt, (next_night_btn.x + 30, next_night_btn.y + 10))

    elif game_state == 9:
        title = font_title.render(ar("نهاية اللعبة!"), True, GOLD)
        screen.blit(title, (WIDTH // 2 - title.get_width() // 2, 120))

        win_txt = font_title.render(ar(winner_msg), True, WHITE)
        screen.blit(win_txt, (WIDTH // 2 - win_txt.get_width() // 2, 220))

        restart_btn = pygame.Rect(WIDTH // 2 - 100, 400, 200, 50)
        pygame.draw.rect(screen, GREEN, restart_btn, border_radius=10)
        r_txt = font_sub.render(ar("جيم جديد"), True, WHITE)
        screen.blit(
            r_txt,
            (
                restart_btn.x + (200 - r_txt.get_width()) // 2,
                restart_btn.y + 12,
            ),
        )

    pygame.display.flip()

pygame.quit()
sys.exit()