import requests
from bs4 import BeautifulSoup
import csv
import os
import tkinter as tk
from tkinter import ttk, messagebox, Tk, Listbox, Button, Menu, Entry, IntVar, Label, X, BOTH, END
from threading import Thread
from pyperclip import copy
import re


def thread(my_func):
    def wrapper(*args, **kwargs):
        my_thread = Thread(target=my_func, args=args, kwargs=kwargs)
        my_thread.start()

    return wrapper


def parse_match_stats(url):
    """Парсит статистику матча с указанного URL."""
    try:
        response = requests.get(url)
        response.raise_for_status()
        soup = BeautifulSoup(response.content, 'html.parser')

        teams = soup.find_all('div', class_='col-12')
        if not teams:
            print("Не найдено секций команд на странице.")
            return None

        header = soup.find_all('div', 'd-flex flex-column align-items-center')
        extracted_data = []
        for info in header:
            time_element = info.find('span', class_='px-3')
            winner = info.find('h4', 'text-success')
            if not winner:
                winner = info.find('h4', 'text-danger')
            score_succes = info.find('span', 'text-success h3')
            score_danger = info.find('span', 'text-danger h3')
            extracted_data.append(winner.text.strip())
            extracted_data.append(f'{score_succes.text.strip()},{score_danger.text.strip()}')
            time_element = time_element.text.strip()
            time_match = [i.zfill(2) for i in time_element.split(" ") if i.isdigit()]
            exported_match_time = f"{time_match[0]}:{time_match[1]}"
            extracted_data.append(exported_match_time)
        team_names = []
        for info in teams:
            name = info.find_all('div', 'text-uppercase')
            for i in range(len(name)):
                if not name[i].text.strip().split('\n') in team_names:
                    team_names.append(name[i].text.strip().split('\n'))
        if len(team_names) == 2:
            team_out = f'{team_names[0][0]},{team_names[0][1]},{team_names[1][0]},{team_names[1][1]}'
        else:
            team_out = "Неизвестно"
        team_data = []
        for team_section in teams:
            players = team_section.find_all('tr')
            player_stats = []
            if len(players) == 6:
                for i in players:
                    hero_nick = ""
                    gpm_xpm2=""
                    lvl = [x for x in i][1].text.strip()
                    nick = [x for x in i][3].text.strip().upper()
                    kills = [x for x in i][5].text.strip()
                    deaths = [x for x in i][7].text.strip()
                    assists = [x for x in i][9].text.strip()
                    net = [x for x in i][13].text.strip()
                    damage = [x for x in i][17].text.strip()
                    gpm_xpm = [x for x in i][15].text.strip()
                    gpm=[x for x in gpm_xpm.split('/')]
                    if len(gpm)==2:
                        gpm_xpm2=f'{gpm[0]},{gpm[1]}'
                    hero_element = i.find('img')
                    hero_nick = ""
                    if hero_element:
                        hero_link = hero_element['src'][:-1]
                        hero_nick = hero_link[:-4].split("/")[-1]
                        if hero_nick.count('_') == 1:
                            hero_nick_words = hero_nick.split("_")
                            hero_nick = f"{hero_nick_words[0]} {hero_nick_words[1]}"
                        hero_nick = hero_nick.upper()
                        try:
                            img_data = requests.get(hero_link).content
                            os.makedirs("heroes_img", exist_ok=True)
                            with open(f'heroes_img/{hero_nick}.jpg', 'wb') as handler:
                                handler.write(img_data)
                        except Exception as e:
                            print(f"Ошибка при загрузке изображения героя: {e}")
                    if damage != "УПС":
                        damage = str(int(float(damage[:-1]) * 1000))

                    if net != "ЗМ/ОМ":
                        net = str(int(float(net[:-1]) * 1000))
                    player_stats.append({
                        'lvl': lvl,
                        'hero': hero_nick,
                        'nick': nick,
                        'kills': kills,
                        'deaths': deaths,
                        'assists': assists,
                        'net': net,
                        'damage': damage,
                        'gpm_xpm': gpm_xpm2,
                    })
                team_data.append({'team_out': team_out, 'name': extracted_data[0], 'score': extracted_data[1],
                                  'time': extracted_data[2], 'players': player_stats},)
        return team_data
    except requests.exceptions.RequestException as e:
        print(f"Ошибка запроса: {e}")
        return None
    except Exception as e:
        print(f"Ошибка при парсинге: {e}")
        return None

def replace_commas(text):
    if text is None:
        return ""
    return str(text).replace(",", ";")

def restore_commas(text):
    if text is None:
        return ""
    return str(text).replace(";", ",")

def save_stats_to_csv(stats, filename="match_stats.csv"):
    if not stats:
        print("Нет данных для сохранения.")
        return False
    try:
        with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
             writer = csv.writer(csvfile, quoting=csv.QUOTE_NONE)
             for team_data in stats:
                 writer.writerow([replace_commas(f"{team_data['team_out']},{team_data['name']},{team_data['score']},{team_data['time']}")])
                 for player in team_data['players']:
                     writer.writerow([replace_commas(f"  {player['nick']},{player['lvl']},{player['hero']},{player['kills']}/{player['deaths']}/{player['assists']},{player['net']},{player['damage']},{player['gpm_xpm']}")])
        print(f"Данные успешно сохранены в файл: {filename}")
        return True
    except Exception as e:
        print(f"Ошибка при записи в файл: {e}")
        return False


def copy_file_path(filename):
    if os.path.exists(filename):
        copy(filename)
        messagebox.showinfo("Успех", f"Путь к файлу '{filename}' скопирован в буфер обмена.")
    else:
        messagebox.showerror("Ошибка", f"Файл '{filename}' не найден.")


def clear_entry(entry):
    entry.delete(0, 'end')


def paste_from_clipboard(entry, root):
    try:
        text = root.clipboard_get()
        entry.insert(tk.INSERT, text)
    except tk.TclError:
        messagebox.showerror("Ошибка", "Не удалось получить данные из буфера обмена.")


def main():
    url_stats = "https://www.vscl.ru/tournaments/868/matches/35382/stats/3"
    root = Tk()
    root.title("Парсинг статистики матчей VCL")

    original_width = 620
    original_height = 464
    new_width = int(original_width * 1.10)
    new_height = int(original_height * 1.10)
    root.geometry(f"{new_width}x{new_height}")

    root.minsize(new_width, new_height)

    l1 = ttk.LabelFrame(root, text='Введите URL страницы')
    l1.grid(row=0, column=0, padx=10, pady=10, sticky='enws')
    l1.columnconfigure(0, weight=1)

    Entry1 = Entry(l1, width=70)
    Entry1.pack(side="left", fill=X, expand=1, padx=5, pady=5)
    Entry1.insert(0, url_stats)

    Entry1.focus_set()

    b2 = Button(l1, text='Обновить статистику',
                command=lambda: update_stats(Entry1.get().strip(), listbox, save_var, status_label))
    b2.pack(side="right", padx=5, pady=5)

    popup = Menu(root, tearoff=0)
    popup.add_command(label="Пример ссылки статистики", command=lambda: clear_and_insert(Entry1, url_stats))
    popup.add_separator()
    popup.add_command(label="Очистить поле ввода", command=lambda: clear_entry(Entry1))
    popup.add_command(label="Вставить из буфера", command=lambda: paste_from_clipboard(Entry1, root))
    Entry1.bind('<Button-3>', lambda event: do_popup(event, popup))

    l2 = ttk.LabelFrame(root, text='Результат')
    l2.grid(row=1, column=0, padx=10, pady=10, sticky='enws')
    l2.columnconfigure(0, weight=1)

    listbox = Listbox(l2)
    listbox.pack(side="top", fill="both", expand=True, padx=5, pady=5)

    save_var = IntVar(value=1)

    l5 = ttk.LabelFrame(root, text='Настройка сохранения')
    l5.grid(row=2, column=0, padx=10, pady=10, sticky='enws')
    l5.columnconfigure(0, weight=1)

    check2 = ttk.Checkbutton(l5, text=u'Сохранять только если все данные получены', variable=save_var, onvalue=1,
                             offvalue=0)
    check2.grid(row=0, column=0, padx=10, pady=5, sticky='enws')

    status_label = Label(l5, text='', font="Arial 12", justify="right", anchor="e", foreground="white")
    status_label.grid(row=0, column=1, padx=10, pady=5, sticky='e')

    b_stats_copy = ttk.Button(root, text='Скопировать путь к файлу "match_stats.csv" в буфер обмена',
                             command=lambda: copy_file_path("match_stats.csv"))
    b_stats_copy.grid(row=4, column=0, padx=10, pady=10, sticky='enws')

    root.columnconfigure(0, weight=1)
    root.rowconfigure(1, weight=1)

    def clear_and_insert(entry, text):
        entry.delete(0, 'end')
        entry.insert(0, text)

    @thread
    def update_stats(url, listbox, save_var, status_label):
        stats = parse_match_stats(url)
        listbox.delete(0, END)
        if stats:
            for team_data in stats:
                listbox.insert(END, f"{team_data['team_out']},{team_data['name']},{team_data['score']},{team_data['time']}")
                for player in team_data['players']:
                    listbox.insert(END,
                                   f"  {player['nick']},{player['lvl']},{player['hero']},{player['kills']}/{player['deaths']}/{player['assists']},{player['net']},{player['damage']},{player['gpm_xpm']}")

        else:
            listbox.insert(END, "Ошибка получения данных")

        if save_var.get() == 1:
            if stats:
                if save_stats_to_csv(stats):
                    status_label.config(text="ВСЕ ХОРОШО", foreground="white", background="green")
                else:
                    status_label.config(text="ОШИБКА", foreground="white", background="red")
            else:
                status_label.config(text="ОШИБКА", foreground="white", background="red")
        else:
            save_stats_to_csv(stats)
            status_label.config(text="Сохранено", foreground="white", background="green")

    def do_popup(event, popup):
        try:
            popup.tk_popup(event.x_root, event.y_root, 0)
        finally:
            popup.grab_release()

    def on_closing():
        if messagebox.askokcancel("Закрыть", "Вы действительно хотите закрыть программу?"):
            root.destroy()
            root.quit()

    root.protocol("WM_DELETE_WINDOW", on_closing)

    root.mainloop()


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        import traceback
        traceback.print_exc()
        print(f"Главная функция завершилась с ошибкой: {e}")