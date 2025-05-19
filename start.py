import tkinter as tk
import tkinter.ttk as ttk
from tkinter import simpledialog, messagebox, Menu, Toplevel, Listbox
import sqlite3
import time
import json
from datetime import datetime
import sys
import os

class Account:
    def __init__(self, canvas, x, y, account_number, from_db=False):
        self.canvas = canvas
        self.account_number = account_number
        self.x = x
        self.y = y
        self.lines = []
        self.radius = 15  # Радиус закругления углов
        
        # Получаем данные о счете из БД
        cursor.execute("SELECT balance, type FROM accounts WHERE account_number=?", (account_number,))
        result = cursor.fetchone()
        self.balance = result[0] if result else 0
        self.type = result[1] if result else 'asset'
        
        if not from_db:
            cursor.execute("UPDATE accounts SET status=?, x=?, y=? WHERE account_number=?", 
                         ("on field", x, y, account_number))
            conn.commit()
        
        # Выбор цвета прямоугольника в зависимости от типа счета
        if self.type == 'active':
            fill_color = 'lightgreen'
        elif self.type == 'passive':
            fill_color = 'lightcoral'
        elif self.type == 'activepassive':
            fill_color = 'lightblue'
        else:
            fill_color = 'gray'

        # Создание прямоугольника с закругленными углами
        width = 120
        height = 80
        self.rect = self.create_rounded_rectangle(x, y, x + width, y + height, 
                                                radius=self.radius, fill=fill_color)
        
        self.text = self.canvas.create_text(x + width/2, y + height/2, 
                                          text=f"Счет: {account_number}\nБаланс: {format_balance(self.balance, self.type)}", 
                                          font=("Arial", 12))
        
        # Привязываем обработчики для перемещения
        self.canvas.tag_bind(self.rect, '<Button3-Motion>', self.move)
        self.canvas.tag_bind(self.text, '<Button3-Motion>', self.move)
        self.canvas.tag_bind(self.rect, '<ButtonRelease-3>', self.update_position)
        self.canvas.tag_bind(self.text, '<ButtonRelease-3>', self.update_position)

    def create_rounded_rectangle(self, x1, y1, x2, y2, radius=25, **kwargs):
        """Создает прямоугольник с закругленными углами на canvas"""
        points = []
        
        # Верхний левый угол
        points.append(x1 + radius)
        points.append(y1)
        
        # Верхний правый угол
        points.append(x2 - radius)
        points.append(y1)
        points.append(x2)
        points.append(y1)
        points.append(x2)
        points.append(y1 + radius)
        
        # Нижний правый угол
        points.append(x2)
        points.append(y2 - radius)
        points.append(x2)
        points.append(y2)
        points.append(x2 - radius)
        points.append(y2)
        
        # Нижний левый угол
        points.append(x1 + radius)
        points.append(y2)
        points.append(x1)
        points.append(y2)
        points.append(x1)
        points.append(y2 - radius)
        
        # Верхний левый угол (завершение)
        points.append(x1)
        points.append(y1 + radius)
        points.append(x1)
        points.append(y1)
        points.append(x1 + radius)
        points.append(y1)
        
        return self.canvas.create_polygon(points, **kwargs, smooth=True)

    # Передвижение счетов и линий
    def move(self, event):
        # Проверяем границы Canvas
        canvas_width = self.canvas.winfo_width()
        canvas_height = self.canvas.winfo_height()
        
        # Рассчитываем новые координаты с учетом центрального захвата
        new_x = max(0, min(event.x - 60, canvas_width - 120))  # 60 - половина ширины
        new_y = max(0, min(event.y - 40, canvas_height - 80))  # 40 - половина высоты
        
        dx = new_x - self.x
        dy = new_y - self.y
        
        if dx != 0 or dy != 0:
            # Перемещаем графические элементы
            self.canvas.move(self.rect, dx, dy)
            self.canvas.move(self.text, dx, dy)
            
            # Обновляем координаты счета
            self.x = new_x
            self.y = new_y
            
            # Обновляем все связанные линии
            for line_id in self.lines:
                coords = self.canvas.coords(line_id)
                if abs(coords[0] - (self.x - dx + 60)) < 1 and abs(coords[1] - (self.y - dy + 80)) < 1:
                    self.canvas.coords(line_id, self.x + 60, self.y + 80, coords[2], coords[3])
                else:
                    self.canvas.coords(line_id, coords[0], coords[1], self.x + 60, self.y + 80)
                
                self.canvas.tag_lower(line_id)

    # Обновляем позицию в БД после перемещения
    def update_position(self, event):
        # Обновляем позицию в БД после перемещения
        cursor.execute("UPDATE accounts SET x=?, y=? WHERE account_number=?", 
                     (self.x, self.y, self.account_number))
        conn.commit()

    # Добавление средств на счет
    def add_funds(self):
        dialog = Toplevel(root)
        dialog.title("Добавить средства")
        dialog.geometry("200x120")
        dialog.resizable(False, False)
        dialog.transient(root)
        dialog.grab_set()
        
        content_frame = tk.Frame(dialog, padx=10, pady=10)
        content_frame.pack(fill='both', expand=True)
        
        tk.Label(content_frame, text="Введите сумму:").pack(pady=5)
        
        amount_entry = tk.Entry(content_frame, 
                            bd=1,
                            relief="solid",
                            highlightthickness=0)
        amount_entry.pack(pady=5)
        amount_entry.focus_set()
        
        button_frame = tk.Frame(content_frame)
        button_frame.pack(pady=(5, 0))  # Изменен отступ
        
        def process_add():
            try:
                amount = int(amount_entry.get())
                if amount <= 0:
                    messagebox.showwarning("Ошибка", "Сумма должна быть положительной!", parent=dialog)
                    return
                    
                self.balance += amount
                cursor.execute("UPDATE accounts SET balance=? WHERE account_number=?", 
                            (self.balance, self.account_number))
                conn.commit()
                
                self.canvas.itemconfig(self.text, 
                                    text=f"Счет: {self.account_number}\nБаланс: {format_balance(self.balance, self.type)}")
                log_operation(self.account_number, amount, "Добавление")
                dialog.destroy()
                
            except ValueError:
                messagebox.showwarning("Ошибка", "Введите корректную сумму!", parent=dialog)
        
        # Создаем кнопку как в окне перевода
        btn = ttk.Button(button_frame, 
                    text="Добавить",
                    width=10,
                    style='Accent.TButton' if 'Accent.TButton' in ttk.Style().theme_names() else None,
                    command=process_add)
        btn.pack(pady=5)
        
        # Центрируем окно
        dialog.update_idletasks()
        width = dialog.winfo_width()
        height = dialog.winfo_height()
        x = (dialog.winfo_screenwidth() // 2) - (width // 2)
        y = (dialog.winfo_screenheight() // 2) - (height // 2)
        dialog.geometry(f'+{x}+{y}')

    # Перевод средств между счетами
    def transfer(self):
        # Сначала проверяем наличие доступных счетов
        cursor.execute("""
            SELECT connected_account_number 
            FROM connections 
            WHERE account_number=? 
            AND connected_account_number IN (
                SELECT account_number FROM accounts WHERE status='on field'
            )
        """, (self.account_number,))
        
        available_accounts = [row[0] for row in cursor.fetchall() 
                            if row[0] != self.account_number and 
                            any(acc.account_number == row[0] for acc in account_list)]
        
        if not available_accounts:
            messagebox.showwarning("Ошибка", "Нет доступных счетов для перевода!", parent=root)
            return
        
        dialog = Toplevel(root)
        dialog.title("Перевод")
        dialog.geometry("260x120")
        dialog.resizable(False, False)
        dialog.transient(root)
        dialog.grab_set()
        
        tk.Label(dialog, text="Сумма:").grid(row=0, column=0, padx=5, pady=5)
        amount_entry = tk.Entry(dialog)
        amount_entry.grid(row=0, column=1, padx=5, pady=5)
        
        tk.Label(dialog, text="Счет:").grid(row=1, column=0, padx=5, pady=5)
        target_combobox = ttk.Combobox(dialog, values=available_accounts, state="readonly")
        target_combobox.grid(row=1, column=1, padx=5, pady=5)
        target_combobox.current(0)
        
        def process_transfer():
            try:
                amount = int(amount_entry.get())
                target_account_number = int(target_combobox.get())
                
                if amount <= 0:
                    messagebox.showwarning("Ошибка", "Сумма должна быть положительной!", parent=dialog)
                    return
                    
                # Проверяем, существует ли связь между счетами
                cursor.execute("""
                    SELECT 1 FROM connections 
                    WHERE account_number=? AND connected_account_number=?
                """, (self.account_number, target_account_number))
                
                if not cursor.fetchone():
                    messagebox.showwarning("Ошибка", "Невозможно перевести - счета не связаны!", parent=dialog)
                    return
                
                # Получаем типы обоих счетов
                cursor.execute("SELECT type, balance FROM accounts WHERE account_number=?", (self.account_number,))
                source_type, source_balance = cursor.fetchone()
                
                cursor.execute("SELECT type, balance FROM accounts WHERE account_number=?", (target_account_number,))
                target_type, target_balance = cursor.fetchone()
                
                # Находим объект целевого счета
                target_account = None
                for account in account_list:
                    if account.account_number == target_account_number:
                        target_account = account
                        break
                
                if not target_account:
                    messagebox.showwarning("Ошибка", "Счет получателя не найден!", parent=dialog)
                    return
                
                # Проверяем достаточно ли баланса на счете-источнике
                if source_type == 'active':
                    if source_balance == 0 or (source_balance - amount < 0):
                        messagebox.showwarning("Ошибка", "Недостаточно баланса на активном счете!", parent=dialog)
                        return
                    elif source_balance < 0:
                        messagebox.showwarning("Ошибка", "Баланс данного счета отрицателен, где-то произошла ошибка", parent=dialog)
                        return
                elif source_type == 'passive':
                    if source_balance < 0:
                        messagebox.showwarning("Ошибка", "Баланс данного счета отрицателен, где-то произошла ошибка", parent=dialog)
                        return
                # elif source_type == 'activepassive':
                #     if source_balance < 0:
                #         messagebox.showwarning("Ошибка", "Перевод невозможен!", parent=dialog)
                #         return
                #     elif source_balance == 0 or (source_balance - amount < 0):
                #         messagebox.showwarning("Ошибка", "Недостаточно баланса на активно-пассивном счете!", parent=dialog)
                #         return
                
                # Проверяем, чтобы у таргет счетов не было отрицательного баланса после перевода
                if target_type == 'passive' and (target_balance - amount) < 0:
                    messagebox.showwarning("Ошибка", "Нельзя сделать баланс пассивного счета отрицательным!", parent=dialog)
                    return
                    
                # Вычисляем изменения балансов в зависимости от типов счетов
                source_change = -amount  #  уменьшаем баланс
                target_change = amount   # увеличиваем баланс
                
                if source_type == 'active':
                    source_change = -amount 
                    if target_type == 'passive':
                        target_change = -amount  # Для перевода active -> passive уменьшаем целевой счет
                    else:
                        target_change = amount

                elif source_type == 'passive':
                    source_change = amount  # Для пассивного счета уменьшаем баланс (увеличиваем пассив)
                    if target_type == 'passive':
                        target_change = -amount   # Для passive -> passive уменьшаем целевой счет
                    else:  # Для перевода passive -> active и passive -> activepassive увеличиваем целевой счет
                        target_change = amount
                    
                elif source_type == 'activepassive':
                    # Действуем как active счет
                    source_change = -amount 
                    if target_type == 'passive':
                        target_change = -amount  # Для перевода active -> passive уменьшаем целевой счет
                    else:
                        target_change = amount

                # Обновляем балансы в БД
                cursor.execute("UPDATE accounts SET balance=balance+? WHERE account_number=?", 
                            (source_change, self.account_number))
                cursor.execute("UPDATE accounts SET balance=balance+? WHERE account_number=?", 
                            (target_change, target_account_number))
                conn.commit()
                
                # Обновляем балансы в интерфейсе
                self.balance += source_change
                target_account.balance += target_change
                
                self.canvas.itemconfig(self.text, 
                                    text=f"Счет: {self.account_number}\nБаланс: {format_balance(self.balance, self.type)}")
                target_account.canvas.itemconfig(target_account.text, 
                                            text=f"Счет: {target_account.account_number}\nБаланс: {format_balance(target_account.balance, target_account.type)}")
                
                log_transfer(self.account_number, target_account_number, amount)
                dialog.destroy()
                
            except ValueError:
                messagebox.showwarning("Ошибка", "Введите корректные числовые значения!", parent=dialog)
        
        tk.Button(dialog, text="Перевести", command=process_transfer).grid(row=2, columnspan=2, pady=5)
        
        dialog.update_idletasks()
        width = dialog.winfo_width()
        height = dialog.winfo_height()
        x = (dialog.winfo_screenwidth() // 2) - (width // 2)
        y = (dialog.winfo_screenheight() // 2) - (height // 2)
        dialog.geometry(f'+{x}+{y}')


    def delete_account(self):
        # Добавляем подтверждение удаления
        if not messagebox.askyesno("Подтверждение", 
                                f"Вы точно хотите удалить счет {self.account_number}?",
                                parent=root):
            return  # Если пользователь отказался, выходим из метода
        
        # Удаляем связанные операции и переводы
        cursor.execute("DELETE FROM operations WHERE account_number=?", (self.account_number,))
        cursor.execute("DELETE FROM transfers WHERE source_account_number=? OR target_account_number=?", 
                    (self.account_number, self.account_number))
        
        # Обновляем статус счета и обнуляем баланс
        cursor.execute("UPDATE accounts SET status=?, balance=0, x=NULL, y=NULL WHERE account_number=?", 
                    ("not on field", self.account_number))
        conn.commit()
        
        self.canvas.delete(self.rect)
        self.canvas.delete(self.text)
        account_list.remove(self)
        
        messagebox.showinfo("Успешно", f"Счет {self.account_number} был удален", parent=root)

    # Инфо по конкретному счету
    def show_account_info(self):
        info_window = Toplevel(root)
        info_window.title(f"Информация по счету {self.account_number}")
        info_window.geometry("580x630")  # Размер окна остался прежним
        info_window.resizable(False, False)
        info_window.transient(root)
        info_window.grab_set()
        
        # Центрируем окно
        width = 580
        height = 630
        x = (info_window.winfo_screenwidth() // 2) - (width // 2)
        y = (info_window.winfo_screenheight() // 2) - (height // 2)
        info_window.geometry(f'{width}x{height}+{x}+{y}')

        # Создаем основной контейнер с прокруткой
        main_frame = tk.Frame(info_window)
        main_frame.pack(fill='both', expand=True)
        
        canvas = tk.Canvas(main_frame, width=600)  # Фиксируем ширину Canvas
        scrollbar = ttk.Scrollbar(main_frame, orient='vertical', command=canvas.yview)
        scrollable_frame = tk.Frame(canvas, width=580)  # Фиксируем ширину внутреннего фрейма
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(
                scrollregion=canvas.bbox("all"),
                width=580  # Устанавливаем ширину Canvas при конфигурации
            )
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor='nw')
        canvas.configure(yscrollcommand=scrollbar.set)
        
        canvas.pack(side='left', fill='both', expand=True)
        scrollbar.pack(side='right', fill='y')
        
        # Функция для прокрутки колесиком мыши
        def _on_mousewheel(event):
            canvas.yview_scroll(int(-1*(event.delta/120)), "units")
        
        canvas.bind("<MouseWheel>", _on_mousewheel)
        scrollable_frame.bind("<MouseWheel>", _on_mousewheel)

        # Получаем полную информацию о счете из БД
        cursor.execute("SELECT name, description, balance, type FROM accounts WHERE account_number=?", (self.account_number,))
        name, description, balance, acc_type = cursor.fetchone()

        # Основная информация о счете
        main_info_frame = tk.Frame(scrollable_frame, width=580)  # Фиксируем ширину
        main_info_frame.pack(pady=10, fill='x', padx=10)
        
        tk.Label(main_info_frame, text=f"Номер счета: {self.account_number}", font=('Arial', 12)).pack(anchor='w')
        tk.Label(main_info_frame, text=f"Название: {name}", font=('Arial', 12)).pack(anchor='w')
        tk.Label(main_info_frame, text=f"Баланс: {format_balance(balance, acc_type)}", font=('Arial', 12)).pack(anchor='w')
        tk.Label(main_info_frame, text=f"Тип: {'Актив-Пассив' if acc_type == 'activepassive' else ('Неопределен' if acc_type == 'undefined' else ('Актив' if acc_type == 'active' else 'Пассив'))}", font=('Arial', 12)).pack(anchor='w')
        
        # Фрейм для описания с прокруткой
        desc_frame = tk.Frame(main_info_frame, width=580)
        desc_frame.pack(anchor='w', fill='x', pady=(0, 10))
        
        tk.Label(desc_frame, text="Описание:", font=('Arial', 12)).pack(anchor='w')
        
        # Text виджет для описания с переносом слов
        desc_text = tk.Text(desc_frame, 
                        width=70,  # Увеличиваем ширину текстового поля
                        height=8, 
                        wrap='word', 
                        font=('Arial', 10),
                        padx=5,
                        pady=5)
        desc_scroll = ttk.Scrollbar(desc_frame, orient='vertical', command=desc_text.yview)
        desc_text.configure(yscrollcommand=desc_scroll.set)
        
        # Вставляем текст описания
        desc_text.insert('1.0', description)
        desc_text.config(state='disabled')
        
        # Упаковываем элементы
        desc_text.pack(side='left', fill='x', expand=True)
        desc_scroll.pack(side='right', fill='y')

        # Разделительная линия
        ttk.Separator(scrollable_frame, orient='horizontal').pack(fill='x', pady=10)

        # Заголовок списка связанных счетов
        tk.Label(scrollable_frame, text="Связанные счета по кредиту:", font=('Arial', 12, 'bold')).pack()

        # Список связанных счетов
        conn_frame = tk.Frame(scrollable_frame, width=580)
        conn_frame.pack(fill='x', padx=10, pady=5)

        scrollbar_conn = ttk.Scrollbar(conn_frame)
        scrollbar_conn.pack(side='right', fill='y')

        connections_listbox = Listbox(conn_frame,
                                    width=70,  # Увеличиваем ширину списка
                                    height=5,
                                    font=('Arial', 10),
                                    yscrollcommand=scrollbar_conn.set)
        connections_listbox.pack(side='left', fill='x', expand=True)
        scrollbar_conn.config(command=connections_listbox.yview)

        # Получаем список связанных счетов с их названиями и типами
        cursor.execute("""
            SELECT c.connected_account_number, a.name, a.type 
            FROM connections c
            JOIN accounts a ON c.connected_account_number = a.account_number
            WHERE c.account_number=?
        """, (self.account_number,))

        for account_num, account_name, acc_type in cursor.fetchall():
            type_str = {'active': 'Активный', 'passive': 'Пассивный', 'activepassive': 'Активно-пассивный', 'undefined': 'Неизвестно'}.get(acc_type, '?')
            connections_listbox.insert(tk.END, f"{account_num} - {account_name} [{type_str}]")

        # Разделительная линия
        ttk.Separator(scrollable_frame, orient='horizontal').pack(fill='x', pady=10)

        # Заголовок истории переводов
        tk.Label(scrollable_frame, text="История переводов:", font=('Arial', 12, 'bold')).pack()

        # Список всех переводов
        transfers_frame = tk.Frame(scrollable_frame, width=580)
        transfers_frame.pack(fill='x', padx=10, pady=5)

        scrollbar_transfers = ttk.Scrollbar(transfers_frame)
        scrollbar_transfers.pack(side='right', fill='y')

        transfers_listbox = Listbox(transfers_frame,
                                width=70,
                                height=6,
                                font=('Arial', 10),
                                yscrollcommand=scrollbar_transfers.set)
        transfers_listbox.pack(side='left', fill='x', expand=True)
        scrollbar_transfers.config(command=transfers_listbox.yview)

        # Получаем историю переводов для этого счета
        cursor.execute("""
            SELECT source_account_number, target_account_number, amount, timestamp 
            FROM transfers 
            WHERE source_account_number=? OR target_account_number=?
            ORDER BY timestamp DESC
        """, (self.account_number, self.account_number))

        transfers = cursor.fetchall()

        if not transfers:
            transfers_listbox.insert(tk.END, "Нет истории переводов для этого счета")
        else:
            for source, target, amount, timestamp in transfers:
                transfers_listbox.insert(
                    tk.END, 
                    f"Дебет: {target} ← Кредит: {source} | Сумма: {amount} | Время: ({timestamp})"
                )


def add_account(event):
    dialog = Toplevel(root)
    dialog.title("Добавить счет")
    dialog.geometry("160x130")  # Немного увеличил размер для лучшего отображения
    
    # Убираем кнопки свернуть/развернуть
    dialog.resizable(False, False)  # Запрещаем изменение размеров
    dialog.transient(root)  # Делаем окно зависимым от главного
    dialog.grab_set()  # Захватываем фокус
    
    # Получаем список доступных счетов (не на поле)
    cursor.execute("SELECT account_number FROM accounts WHERE status='not on field' AND (type IS NULL OR type != 'undefined')")
    available_numbers = [row[0] for row in cursor.fetchall()]
    
    if not available_numbers:
        messagebox.showwarning("Ошибка", "Нет доступных счетов для добавления!", parent=dialog)
        dialog.destroy()
        return
    
    # Основной фрейм для содержимого
    content_frame = ttk.Frame(dialog, padding=10)
    content_frame.pack(fill='both', expand=True)
    
    ttk.Label(content_frame, text="Выберите номер счета:").pack(pady=5)
    account_combobox = ttk.Combobox(content_frame, values=available_numbers, state="readonly")
    account_combobox.pack(pady=5)
    account_combobox.current(0)
    
    # Фрейм для кнопки
    button_frame = ttk.Frame(content_frame)
    button_frame.pack(pady=10)
    
    def process_add():
        selected_number = int(account_combobox.get())
        new_account = Account(canvas, event.x, event.y, selected_number)
        account_list.append(new_account)
        dialog.destroy()
    
    ttk.Button(button_frame, text="Добавить", command=process_add).pack()
    
    # Центрируем окно
    dialog.update_idletasks()
    width = dialog.winfo_width()
    height = dialog.winfo_height()
    x = (dialog.winfo_screenwidth() // 2) - (width // 2)
    y = (dialog.winfo_screenheight() // 2) - (height // 2)
    dialog.geometry(f'+{x}+{y}')

# Обновление линий между счетами
def update_connection_lines():
    # Сначала удаляем все существующие линии со canvas
    for line in canvas.find_all():
        if canvas.type(line) == 'line':
            canvas.delete(line)
    
    # Очищаем списки линий у всех счетов
    for account in account_list:
        account.lines.clear()
    
    # Получаем уникальные пары счетов, между которыми были переводы
    cursor.execute("""
        SELECT DISTINCT 
            CASE WHEN source_account_number < target_account_number 
                 THEN source_account_number ELSE target_account_number END,
            CASE WHEN source_account_number < target_account_number 
                 THEN target_account_number ELSE source_account_number END
        FROM transfers
    """)
    connections = cursor.fetchall()
    
    # Создаем линии для каждой пары счетов
    for acc1, acc2 in connections:
        account1 = next((a for a in account_list if a.account_number == acc1), None)
        account2 = next((a for a in account_list if a.account_number == acc2), None)
        
        if account1 and account2:
            # Координаты для линии (под счетами)
            x1 = account1.x + 60  # Центр по X первого счета
            y1 = account1.y + 80  # Нижний край первого счета
            x2 = account2.x + 60  # Центр по X второго счета
            y2 = account2.y + 80  # Нижний край второго счета
            
            # Создаем линию (только один раз)
            line_id = canvas.create_line(
                x1, y1, x2, y2, 
                width=5, 
                fill="darkblue", 
                arrow=tk.BOTH,
                arrowshape=(15, 15, 5)  # размер стрелок (длина наконечника, ширина основания наконечника, отступ от конца линии)
            )
            
            # Делаем линию кликабельной
            canvas.tag_bind(line_id, '<Button-1>', on_click)
            
            # Помещаем линию под всеми другими элементами
            canvas.tag_lower(line_id)
            
            # Сохраняем ссылки на линии в обоих счетах
            account1.lines.append(line_id)
            account2.lines.append(line_id)


def format_balance(balance, acc_type):
    """Форматирует баланс счета в зависимости от его типа"""
    if acc_type == 'passive' or (acc_type == 'activepassive' and balance < 0):
        return f"({abs(balance)})"  # Для пассивных счетов и отрицательного баланса активно-пассивных
    return str(balance)

# Окно истории переводов между двумя счетами
def show_transfers_between_accounts(account1_num, account2_num):
    # Создаем окно
    transfer_window = Toplevel(root)
    transfer_window.title(f"История переводов между {account1_num} и {account2_num}")
    transfer_window.geometry("800x400")
    transfer_window.grab_set()
    
    # Центрируем окно
    width = 800
    height = 400
    x = (transfer_window.winfo_screenwidth() // 2) - (width // 2)
    y = (transfer_window.winfo_screenheight() // 2) - (height // 2)
    transfer_window.geometry(f'{width}x{height}+{x}+{y}')

    # Создаем основной контейнер
    main_frame = ttk.Frame(transfer_window)
    main_frame.pack(fill='both', expand=True, padx=10, pady=10)

    # Заголовок
    tk.Label(main_frame, 
            text=f"История переводов между счетами {account1_num} и {account2_num}", 
            font=('Arial', 12, 'bold')).pack(pady=10)

    # Создаем Listbox с прокруткой
    list_frame = ttk.Frame(main_frame)
    list_frame.pack(fill='both', expand=True)

    scrollbar = ttk.Scrollbar(list_frame)
    scrollbar.pack(side="right", fill="y")

    transfers_listbox = Listbox(
        list_frame,
        width=100,
        height=15,
        font=('Arial', 10),
        yscrollcommand=scrollbar.set
    )
    transfers_listbox.pack(side="left", fill="both", expand=True)
    scrollbar.config(command=transfers_listbox.yview)

    # Получаем историю переводов между этими счетами
    cursor.execute("""
        SELECT source_account_number, target_account_number, amount, timestamp 
        FROM transfers 
        WHERE (source_account_number=? AND target_account_number=?)
           OR (source_account_number=? AND target_account_number=?)
        ORDER BY timestamp DESC
    """, (account1_num, account2_num, account2_num, account1_num))
    
    transfers = cursor.fetchall()
    
    if not transfers:
        transfers_listbox.insert(tk.END, "Нет истории переводов между этими счетами")
    else:
        for source, target, amount, timestamp in transfers:
            # Форматируем вывод как "Дебет счета (source) на Кредит счета (target)"
            transfers_listbox.insert(
                tk.END, 
                f"Дебет: {target} ← Кредит: {source} | Сумма: {amount} | Время: ({timestamp})"
            )

    # Кнопка закрытия
    btn_frame = ttk.Frame(main_frame)
    btn_frame.pack(pady=10)
    
    ttk.Button(
        btn_frame,
        text="Закрыть",
        command=transfer_window.destroy
    ).pack()



# Окно отчетов
def show_reports():
    report_window = Toplevel(root)
    report_window.title("Отчёты")
    report_window.geometry("800x600")
    report_window.grab_set()  # Захватываем фокус

    width = 800
    height = 600
    x = (report_window.winfo_screenwidth() // 2) - (width // 2)
    y = (report_window.winfo_screenheight() // 2) - (height // 2)
    report_window.geometry(f'{width}x{height}+{x}+{y}')

    notebook = ttk.Notebook(report_window)
    notebook.pack(fill='both', expand=True)

    # Вкладка "Общая информация"
    tab1 = tk.Frame(notebook)
    notebook.add(tab1, text="Общая информация")

    # Вкладка "Переводы средств"
    tab2 = tk.Frame(notebook)
    notebook.add(tab2, text="Переводы средств")

    # Вкладка "Актив/Пассив"
    tab3 = tk.Frame(notebook)
    notebook.add(tab3, text="Актив/Пассив")

    # Функция для обновления вкладки "Общая информация"
    def update_general_info_tab():
        # Очищаем предыдущие данные
        for widget in tab1.winfo_children():
            widget.destroy()
        
        balance_label = tk.Label(tab1, text="Текущий баланс:", font=('Arial', 12, 'bold'))
        balance_label.pack(pady=5)

        # Получаем балансы всех счетов на поле с учетом их типа
        cursor.execute("SELECT balance, type FROM accounts WHERE status='on field'")
        accounts = cursor.fetchall()
        
        total_balance = 0
        for balance, acc_type in accounts:
            if acc_type == 'passive' or (acc_type == 'activepassive' and balance < 0):
                total_balance -= abs(balance)  # Для пассивных счетов вычитаем абсолютное значение
            else:
                total_balance += balance  # Для активных счетов добавляем значение
        
        balance_value = tk.Label(tab1, text=f"{total_balance}", font=('Arial', 14))
        balance_value.pack(pady=5)

        operations_label = tk.Label(tab1, text="Операции:", font=('Arial', 12, 'bold'))
        operations_label.pack(pady=5)

        operations_listbox = Listbox(tab1, width=100, height=15, font=('Arial', 10))
        scrollbar = tk.Scrollbar(tab1, orient="vertical", command=operations_listbox.yview)
        operations_listbox.configure(yscrollcommand=scrollbar.set)
        
        scrollbar.pack(side="right", fill="y")
        operations_listbox.pack(side="left", fill="both", expand=True)

        cursor.execute("SELECT * FROM operations ORDER BY id DESC")
        for row in cursor.fetchall():
            operations_listbox.insert(tk.END, f"Счет: {row[1]} | Сумма: {row[2]} | Тип: {row[3]} | Время: ({row[4]})")

    # Функция для обновления вкладки "Переводы средств"
    def update_transfers_tab():
        # Очищаем предыдущие данные
        for widget in tab2.winfo_children():
            widget.destroy()
            
        transfers_label = tk.Label(tab2, text="История переводов:", font=('Arial', 12, 'bold'))
        transfers_label.pack(pady=5)

        transfers_listbox = Listbox(tab2, width=100, height=20, font=('Arial', 10))
        scrollbar2 = tk.Scrollbar(tab2, orient="vertical", command=transfers_listbox.yview)
        transfers_listbox.configure(yscrollcommand=scrollbar2.set)
        
        scrollbar2.pack(side="right", fill="y")
        transfers_listbox.pack(side="left", fill="both", expand=True)

        cursor.execute("""
            SELECT source_account_number, target_account_number, amount, timestamp 
            FROM transfers 
            ORDER BY id DESC
        """)
        for row in cursor.fetchall():
            source, target, amount, timestamp = row
            transfers_listbox.insert(tk.END, f"Дебет: {target} ← Кредит: {source} | Сумма: {amount} | Время: ({timestamp})")

        # Обновляем линии соединений после загрузки данных
        update_connection_lines()

    # Функция для обновления вкладки "Актив/Пассив"
    def update_balance_tab():
        # Очищаем предыдущие данные
        for widget in tab3.winfo_children():
            widget.destroy()
                
        # Создаем фрейм для таблицы
        balance_frame = tk.Frame(tab3)
        balance_frame.pack(fill='both', expand=True, padx=10, pady=10)
        
        # Заголовки столбцов
        tk.Label(balance_frame, text="Актив", font=('Arial', 12, 'bold')).grid(row=0, column=0, padx=5, pady=5)
        tk.Label(balance_frame, text="Пассив", font=('Arial', 12, 'bold')).grid(row=0, column=1, padx=5, pady=5)
        
        # Получаем активные счета (balance > 0)
        active_accounts = []
        passive_accounts = []
        
        cursor.execute("""
            SELECT a.account_number, a.name, a.balance, a.type 
            FROM accounts a 
            WHERE a.status='on field' AND a.balance != 0
            ORDER BY a.account_number
        """)
        
        for account_number, name, balance, acc_type in cursor.fetchall():
            if (acc_type == 'active' and balance > 0) or (acc_type == 'activepassive' and balance > 0):
                active_accounts.append((account_number, name, balance))
            elif (acc_type == 'passive' and balance > 0) or (acc_type == 'activepassive' and balance < 0):
                passive_accounts.append((account_number, name, abs(balance))) 


        # Создаем Listbox для активов
        active_listbox = Listbox(balance_frame, width=50, height=25, font=('Arial', 10))
        active_scroll = tk.Scrollbar(balance_frame, orient="vertical", command=active_listbox.yview)
        active_listbox.configure(yscrollcommand=active_scroll.set)
        
        active_listbox.grid(row=1, column=0, padx=5, pady=5, sticky="nsew")
        active_scroll.grid(row=1, column=0, padx=5, pady=5, sticky="nse")
        
        # Создаем Listbox для пассивов
        passive_listbox = Listbox(balance_frame, width=50, height=25, font=('Arial', 10))
        passive_scroll = tk.Scrollbar(balance_frame, orient="vertical", command=passive_listbox.yview)
        passive_listbox.configure(yscrollcommand=passive_scroll.set)
        
        passive_listbox.grid(row=1, column=1, padx=5, pady=5, sticky="nsew")
        passive_scroll.grid(row=1, column=1, padx=5, pady=5, sticky="nse")
        
        # Заполняем списки
        for account_number, name, balance in active_accounts:
            active_listbox.insert(tk.END, f"{account_number} - {name}: {balance}")
            
        for account_number, name, balance in passive_accounts:
            passive_listbox.insert(tk.END, f"{account_number} - {name}: {balance}")
        
        # Настраиваем веса строк и столбцов для правильного растягивания
        balance_frame.grid_rowconfigure(1, weight=1)
        balance_frame.grid_columnconfigure(0, weight=1)
        balance_frame.grid_columnconfigure(1, weight=1)
        
        # Добавляем итоговые суммы
        total_active = sum(balance for _, _, balance in active_accounts)
        total_passive = sum(balance for _, _, balance in passive_accounts)
        
        tk.Label(balance_frame, text=f"Итого: {total_active}", font=('Arial', 12, 'bold')).grid(row=2, column=0, padx=5, pady=5)
        tk.Label(balance_frame, text=f"Итого: {total_passive}", font=('Arial', 12, 'bold')).grid(row=2, column=1, padx=5, pady=5)

    # Функция для обновления текущей вкладки
    def on_tab_changed(event):
        current_tab = notebook.index(notebook.select())
        if current_tab == 0:  # Общая информация
            update_general_info_tab()
        elif current_tab == 1:  # Переводы средств
            update_transfers_tab()
        elif current_tab == 2:  # Актив/Пассив
            update_balance_tab()
    
    # Привязываем обработчик изменения вкладки
    notebook.bind("<<NotebookTabChanged>>", on_tab_changed)
    
    # Инициализируем текущую вкладку
    update_general_info_tab()

# Добавляем новую функцию для показа связей счетов
def show_account_connections():
    conn_window = Toplevel(root)
    conn_window.title("Связи между счетами")
    conn_window.geometry("800x600")
    conn_window.grab_set()

    width = 800
    height = 600
    x = (conn_window.winfo_screenwidth() // 2) - (width // 2)
    y = (conn_window.winfo_screenheight() // 2) - (height // 2)
    conn_window.geometry(f'{width}x{height}+{x}+{y}')

    # Создаем основной контейнер
    main_frame = ttk.Frame(conn_window)
    main_frame.pack(fill='both', expand=True, padx=10, pady=10)

    # Заголовок
    tk.Label(main_frame, text="Связи между счетами:", font=('Arial', 14, 'bold')).pack(pady=10)

    # Создаем Listbox с прокруткой
    list_frame = ttk.Frame(main_frame)
    list_frame.pack(fill='both', expand=True)

    scrollbar = ttk.Scrollbar(list_frame)
    scrollbar.pack(side="right", fill="y")

    connections_listbox = Listbox(
        list_frame,
        width=100,
        height=25,
        font=('Arial', 10),
        yscrollcommand=scrollbar.set
    )
    connections_listbox.pack(side="left", fill="both", expand=True)
    scrollbar.config(command=connections_listbox.yview)

    # Заполняем список связей
    cursor.execute("""
        SELECT a1.account_number, a1.name, a2.account_number, a2.name 
        FROM connections c
        JOIN accounts a1 ON c.account_number = a1.account_number
        JOIN accounts a2 ON c.connected_account_number = a2.account_number
        ORDER BY a1.account_number, a2.account_number
    """)
    
    for row in cursor.fetchall():
        account1, name1, account2, name2 = row
        connections_listbox.insert(
            tk.END, 
            f"Счет {account1} ({name1}) корреспондирует со счетом {account2} ({name2}) по кредиту"
        )

    # Кнопка закрытия
    btn_frame = ttk.Frame(main_frame)
    btn_frame.pack(pady=10)
    
    ttk.Button(
        btn_frame,
        text="Закрыть",
        command=conn_window.destroy
    ).pack()

# Инфо о всех счетах
def show_all_accounts_info():
    info_window = Toplevel(root)
    info_window.title("Информация по всем счетам")
    info_window.geometry("590x600")  # Увеличил высоту для лучшего отображения
    info_window.resizable(False, False)
    info_window.transient(root)
    info_window.grab_set()

    # Центрируем окно
    width = 590
    height = 600
    x = (info_window.winfo_screenwidth() // 2) - (width // 2)
    y = (info_window.winfo_screenheight() // 2) - (height // 2)
    info_window.geometry(f'{width}x{height}+{x}+{y}')

    # Создаем Notebook для вкладок
    notebook = ttk.Notebook(info_window)
    notebook.pack(fill='both', expand=True, padx=5, pady=5)

    # Создаем две вкладки
    tab1 = ttk.Frame(notebook)
    tab2 = ttk.Frame(notebook)
    notebook.add(tab1, text="Счета 1-50")
    notebook.add(tab2, text="Счета 51-99")

    # Функция для создания содержимого вкладки
    def create_tab_content(tab, account_numbers_range):
        # Создаем фрейм для быстрого доступа к счетам
        quick_access_frame = ttk.Frame(tab, height=50)
        quick_access_frame.pack(fill="x", padx=5, pady=5)
        
        # Получаем список номеров счетов в заданном диапазоне
        cursor.execute("""
            SELECT account_number FROM accounts 
            WHERE account_number BETWEEN ? AND ?
            ORDER BY account_number
        """, account_numbers_range)
        account_numbers = [row[0] for row in cursor.fetchall()]
        
        if not account_numbers:
            ttk.Label(tab, text="Нет счетов в этом диапазоне").pack(pady=20)
            return
        
        # Создаем кнопки быстрого доступа
        quick_access_canvas = tk.Canvas(quick_access_frame, height=40)
        scroll_x = ttk.Scrollbar(quick_access_frame, orient="horizontal", command=quick_access_canvas.xview)
        quick_access_canvas.configure(xscrollcommand=scroll_x.set)
        
        scroll_x.pack(side="bottom", fill="x")
        quick_access_canvas.pack(side="top", fill="x")
        
        buttons_frame = ttk.Frame(quick_access_canvas)
        quick_access_canvas.create_window((0, 0), window=buttons_frame, anchor="nw")
        
        def update_scrollregion(event):
            quick_access_canvas.configure(scrollregion=quick_access_canvas.bbox("all"))
        
        buttons_frame.bind("<Configure>", update_scrollregion)
        
        for num in account_numbers:
            btn = ttk.Button(buttons_frame, text=str(num), width=3,
                            command=lambda n=num: scroll_to_account(n, tab))
            btn.pack(side="left", padx=2)

        # Добавляем обработчик прокрутки колесиком мыши
        def on_mousewheel(event):
            quick_access_canvas.xview_scroll(int(-1*(event.delta/120)), "units")

        quick_access_canvas.bind("<MouseWheel>", on_mousewheel)
        buttons_frame.bind("<MouseWheel>", on_mousewheel)

        # Создаем основной контейнер с прокруткой
        container = ttk.Frame(tab)
        container.pack(fill="both", expand=True)

        # Создаем Canvas и Scrollbar для основного окна
        main_canvas = tk.Canvas(container)
        main_scrollbar = ttk.Scrollbar(container, orient="vertical", command=main_canvas.yview)
        scrollable_frame = ttk.Frame(main_canvas)

        # Настраиваем прокрутку основного окна
        scrollable_frame.bind(
            "<Configure>",
            lambda e: main_canvas.configure(
                scrollregion=main_canvas.bbox("all")
            )
        )

        main_canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        main_canvas.configure(yscrollcommand=main_scrollbar.set)

        # Упаковываем элементы
        main_canvas.pack(side="left", fill="both", expand=True)
        main_scrollbar.pack(side="right", fill="y")

        # Словарь для хранения ссылок на фреймы счетов
        account_frames = {}
        
        # Получаем все счета из БД в заданном диапазоне
        cursor.execute("""
            SELECT account_number, name, description, balance, type 
            FROM accounts 
            WHERE account_number BETWEEN ? AND ?
            ORDER BY account_number
        """, account_numbers_range)
        
        accounts = cursor.fetchall()

        for i, (account_number, name, description, balance, acc_type) in enumerate(accounts):
            # Фрейм для информации о счете
            account_frame = ttk.Frame(scrollable_frame, borderwidth=2, relief="groove", padding=(10, 10))
            account_frame.pack(fill='x', padx=10, pady=5, ipadx=5, ipady=5)
            
            # Сохраняем ссылку на фрейм счета
            account_frames[account_number] = account_frame

            # Основная информация о счете
            ttk.Label(account_frame, text=f"Счет №{account_number}", font=('Arial', 12, 'bold')).pack(anchor='w')
            ttk.Label(account_frame, text=f"Название: {name}", font=('Arial', 11)).pack(anchor='w')
            ttk.Label(account_frame, text=f"Баланс: {format_balance(balance, acc_type)}", font=('Arial', 11)).pack(anchor='w')
            ttk.Label(account_frame, text=f"Тип: {'Актив-Пассив' if acc_type == 'activepassive' else ('Неопределен' if acc_type == 'undefined' else ('Актив' if acc_type == 'active' else 'Пассив'))}", font=('Arial', 12)).pack(anchor='w')

            # Фрейм для описания с прокруткой
            desc_frame = ttk.Frame(account_frame)
            desc_frame.pack(anchor='w', fill='x', pady=(0, 5))
            
            ttk.Label(desc_frame, text="Описание:", font=('Arial', 11)).pack(anchor='w')
            
            # Создаем Text виджет для описания
            desc_text = tk.Text(desc_frame, 
                              width=50, 
                              height=10, 
                              wrap='word', 
                              font=('Arial', 10),
                              padx=5,
                              pady=5)
            desc_scroll = ttk.Scrollbar(desc_frame, orient='vertical', command=desc_text.yview)
            desc_text.configure(yscrollcommand=desc_scroll.set)
            
            # Вставляем текст описания
            desc_text.insert('1.0', description)
            desc_text.config(state='disabled')
            
            # Упаковываем элементы
            desc_text.pack(side='left', fill='x', expand=True)
            desc_scroll.pack(side='right', fill='y')

            # Получаем связанные счета
            cursor.execute("""
                SELECT c.connected_account_number, a.name, a.type 
                FROM connections c
                JOIN accounts a ON c.connected_account_number = a.account_number
                WHERE c.account_number=?
            """, (account_number,))
            
            connections = cursor.fetchall()
            
            if connections:
                conn_frame = ttk.Frame(account_frame)
                conn_frame.pack(anchor='w', pady=5)
                
                ttk.Label(conn_frame, text="Связанные счета по кредиту:", font=('Arial', 11, 'underline')).pack(anchor='w')
                
                # Создаем фрейм для списка связанных счетов с прокруткой
                conn_list_frame = ttk.Frame(conn_frame)
                conn_list_frame.pack(anchor='w', padx=20)
                
                # Создаем Canvas и Scrollbar для списка связанных счетов
                conn_canvas = tk.Canvas(conn_list_frame, height=100)
                conn_scrollbar = ttk.Scrollbar(conn_list_frame, orient="vertical", command=conn_canvas.yview)
                inner_frame = ttk.Frame(conn_canvas)
                
                # Настраиваем прокрутку списка связанных счетов
                inner_frame.bind(
                    "<Configure>",
                    lambda e, canvas=conn_canvas: canvas.configure(
                        scrollregion=canvas.bbox("all")
                    )
                )
                
                conn_canvas.create_window((0, 0), window=inner_frame, anchor="nw")
                conn_canvas.configure(yscrollcommand=conn_scrollbar.set)
                
                # Заполняем список связанных счетов
                for conn_num, conn_name, acc_type in connections:
                    type_str = {'active': 'Активный', 'passive': 'Пассивный', 'activepassive': 'Активно-пассивный', 'undefined': 'Неизвестно'}.get(acc_type, '?')
                    ttk.Label(inner_frame, 
                            text=f"№{conn_num} - {conn_name} [{type_str}]", 
                            font=('Arial', 10)).pack(anchor='w')

                
                # Упаковываем элементы списка связанных счетов
                conn_canvas.pack(side="left", fill="both", expand=True)
                conn_scrollbar.pack(side="right", fill="y")
                
                # Настраиваем поведение прокрутки
                def bind_scroll(event, canvas):
                    canvas.yview_scroll(int(-1*(event.delta/120)), "units")
                    return "break"
                
                conn_canvas.bind("<MouseWheel>", lambda e, c=conn_canvas: bind_scroll(e, c))
                inner_frame.bind("<MouseWheel>", lambda e, c=conn_canvas: bind_scroll(e, c))

            # Добавляем разделительную линию между счетами (кроме последнего)
            if i < len(accounts) - 1:
                ttk.Separator(scrollable_frame, orient='horizontal').pack(fill='x', pady=10)

        # Функция для прокрутки к нужному счету в текущей вкладке
        def scroll_to_account(account_number, current_tab):
            if account_number in account_frames:
                frame = account_frames[account_number]
                main_canvas.yview_moveto(frame.winfo_y() / scrollable_frame.winfo_height())
                frame.focus_set()
                frame.configure(style='Highlight.TFrame')
                
                # Убираем подсветку через 2 секунды
                frame.after(2000, lambda: frame.configure(style='TFrame'))

        # Настраиваем стиль для подсветки
        style = ttk.Style()
        style.configure('Highlight.TFrame', background="#ccfdff")
        style.configure('TFrame', background='#f0f0f0')

        # Настраиваем прокрутку колесиком мыши для основного окна
        def _on_mousewheel(event):
            main_canvas.yview_scroll(int(-1*(event.delta/120)), "units")
        
        main_canvas.bind("<MouseWheel>", _on_mousewheel)
        scrollable_frame.bind("<MouseWheel>", _on_mousewheel)

    # Создаем содержимое для обеих вкладок
    create_tab_content(tab1, (1, 50))
    create_tab_content(tab2, (51, 99))




def log_operation(account_number, amount, operation):
    cursor.execute("INSERT INTO operations (account_number, amount, operation, timestamp) VALUES (?, ?, ?, datetime('now'))",
                   (account_number, amount, operation))
    conn.commit()

def log_transfer(source_account_number, target_account_number, amount):
    cursor.execute("INSERT INTO transfers (source_account_number, target_account_number, amount, timestamp) VALUES (?, ?, ?, datetime('now'))",
                   (source_account_number, target_account_number, amount))
    conn.commit()

    # Обновляем линии соединений
    update_connection_lines()
    
    cursor.execute("INSERT INTO operations (account_number, amount, operation, timestamp) VALUES (?, ?, ?, datetime('now'))",
                   (source_account_number, amount, "Перевод (исходящий)"))
    cursor.execute("INSERT INTO operations (account_number, amount, operation, timestamp) VALUES (?, ?, ?, datetime('now'))",
                   (target_account_number, amount, "Перевод (входящий)"))
    conn.commit()

def init_db():
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS accounts (
            id INTEGER PRIMARY KEY,
            account_number INTEGER UNIQUE,
            name TEXT,
            description TEXT,
            balance INTEGER DEFAULT 0,
            status TEXT DEFAULT 'not on field',
            x INTEGER,
            y INTEGER,
            type TEXT CHECK(type IN ('active', 'passive', 'activepassive', 'undefined')) DEFAULT 'asset'
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS connections (
            id INTEGER PRIMARY KEY,
            account_number INTEGER,
            connected_account_number INTEGER,
            FOREIGN KEY(account_number) REFERENCES accounts(account_number),
            FOREIGN KEY(connected_account_number) REFERENCES accounts(account_number)
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS operations (
            id INTEGER PRIMARY KEY,
            account_number INTEGER,
            amount INTEGER,
            operation TEXT,
            timestamp TEXT,
            FOREIGN KEY(account_number) REFERENCES accounts(account_number)
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS transfers (
            id INTEGER PRIMARY KEY,
            source_account_number INTEGER,
            target_account_number INTEGER,
            amount INTEGER,
            timestamp TEXT,
            FOREIGN KEY(source_account_number) REFERENCES accounts(account_number),
            FOREIGN KEY(target_account_number) REFERENCES accounts(account_number)
        )
    ''')
    
    # Создаем тестовые счета, если их нет
    cursor.execute("SELECT COUNT(*) FROM accounts")
    if cursor.fetchone()[0] == 0:
        accounts_data = [
            (1, "Касса", "Наличные денежные средства", 'asset'),
            (2, "Расчетный счет", "Деньги на банковском счете", 'asset'),
            (3, "Основные средства", "Оборудование, здания", 'asset'),
            (4, "Кредиторская задолженность", "Долги перед поставщиками", 'liability'),
            (5, "Займы и кредиты", "Банковские кредиты", 'liability')
        ]
        for account_number, name, description, acc_type in accounts_data:
            cursor.execute("INSERT INTO accounts (account_number, name, description, type) VALUES (?, ?, ?, ?)",
                          (account_number, name, description, acc_type))
    conn.commit()

def on_closing():
    if messagebox.askokcancel("Выход", "Вы уверены, что хотите выйти?"):
        conn.close()
        root.destroy()

def resource_path(relative_path):
    """ Получает абсолютный путь к ресурсу, работает для dev и для PyInstaller """
    try:
        # PyInstaller создает временную папку и хранит путь в _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")

    return os.path.join(base_path, relative_path)

# Подключение к базе данных
db_path = resource_path('accounts.db')
conn = sqlite3.connect(db_path)
cursor = conn.cursor()
# # Подключение к базе данных
# conn = sqlite3.connect('accounts.db')
# cursor = conn.cursor()
init_db()


# Функция для подтверждения очистки балансов
def confirm_clear_balances():
    if messagebox.askyesno("Подтверждение", "Точно ли хотите очистить все связи?", parent=root):
        if messagebox.askyesno("Последнее предупреждение", "Вы уверены? Все балансы и связи будут обнулены!", parent=root):
            clear_balances()

# Функция очистки балансов
def clear_balances():
    # Удаляем все линии с canvas
    for line in canvas.find_all():
        if canvas.type(line) == 'line':
            canvas.delete(line)
    
    # Очищаем списки линий у всех счетов
    for account in account_list:
        account.lines.clear()
    
    # Очищаем балансы и операции в БД
    cursor.execute("UPDATE accounts SET balance=0 WHERE status='on field'")
    cursor.execute("DELETE FROM operations")
    cursor.execute("DELETE FROM transfers")
    conn.commit()
    
    # Обновляем балансы в интерфейсе
    for account in account_list:
        account.balance = 0
        account.canvas.itemconfig(account.text, 
                               text=f"Счет: {account.account_number}\nБаланс: {format_balance(account.balance, account.type)}")
    
    messagebox.showinfo("Готово", "Все балансы обнулены, история операций очищена!", parent=root)


# Функция для подтверждения очистки поля
def confirm_clear_field():
    # Первое предупреждение
    if messagebox.askyesno("Подтверждение", "Точно ли хотите очистить?", parent=root):
        # Второе предупреждение
        if messagebox.askyesno("Последнее предупреждение", "Вы уверены? Все счета будут удалены!", parent=root):
            clear_field()

# Функция очистки поля
def clear_field():
    # Удаляем все линии с canvas
    for line in canvas.find_all():
        if canvas.type(line) == 'line':
            canvas.delete(line)
    
    # Очищаем списки линий у всех счетов
    for account in account_list:
        account.lines.clear()

    # Создаем копию списка, будем изменять его в цикле
    accounts_to_remove = account_list.copy()
    
    for account in accounts_to_remove:
        # Удаляем связанные операции и переводы 
        cursor.execute("DELETE FROM operations WHERE account_number=?", (account.account_number,))
        cursor.execute("DELETE FROM transfers WHERE source_account_number=? OR target_account_number=?", 
                      (account.account_number, account.account_number))
        
        # Обновляем статус счета в БД 
        cursor.execute("UPDATE accounts SET status=?, balance=0, x=NULL, y=NULL WHERE account_number=?", 
                      ("not on field", account.account_number))
        
        # Удаляем графические элементы с холста
        account.canvas.delete(account.rect)
        account.canvas.delete(account.text)
        
        # Удаляем счет из списка
        account_list.remove(account)
    
    conn.commit()
    messagebox.showinfo("Готово", "Все счета удалены с поля!", parent=root)

# Создание основного окна
root = tk.Tk()
root.title("Бухгалтерский учет")
root.state('zoomed')

canvas = tk.Canvas(root, width=800, height=600, bg="white")
canvas.pack(fill="both", expand=True)

account_list = []

# Загрузка счетов, которые уже на поле
cursor.execute("SELECT account_number, x, y FROM accounts WHERE status='on field'")
for row in cursor.fetchall():
    account_number, x, y = row
    # Если координаты не сохранены, используем значения по умолчанию
    x = x if x is not None else 100 + (account_number-1)*150
    y = y if y is not None else 100
    new_account = Account(canvas, x, y, account_number, from_db=True)
    account_list.append(new_account)




# Меню
menu_bar = Menu(root)
root.config(menu=menu_bar)

# Пункт "Отчёты"
report_menu = Menu(menu_bar, tearoff=0)
menu_bar.add_cascade(label="Отчёты", menu=report_menu)
report_menu.add_command(label="Посмотреть отчёты", command=show_reports)

# Пункт "Инфо"
file_menu = Menu(menu_bar, tearoff=0)
menu_bar.add_cascade(label="Инфо", menu=file_menu)
file_menu.add_command(label="Связи счетов", command=show_account_connections)
file_menu.add_command(label="Инфо по всем счетам", command=show_all_accounts_info)

# Пункт "Настройки"
settings_menu = Menu(menu_bar, tearoff=0)
menu_bar.add_cascade(label="Настройки", menu=settings_menu)
settings_menu.add_command(label="Сохранить текущее состояние", command=lambda: save_current_state())
settings_menu.add_command(label="Загрузить сохраненное состояние", command=lambda: load_saved_state())
settings_menu.add_separator()
settings_menu.add_command(label="Очистка связей и баланса", command=confirm_clear_balances)
settings_menu.add_command(label="Удалить все данные", command=confirm_clear_field)
settings_menu.add_command(label="Выход", command=on_closing)


# Frame для размещения времени
time_frame = tk.Frame(root)
time_frame.pack(side=tk.TOP, fill=tk.X)

# Добавляем часы в правую часть
time_label = tk.Label(time_frame, font=('Arial', 10), padx=10)
time_label.pack(side=tk.RIGHT)

def update_time():
    current_time = time.strftime('%H:%M:%S')
    time_label.config(text=current_time)
    root.after(1000, update_time)  # Обновляем каждую секунду

update_time()  # Запускаем обновление времени


def save_current_state():
    # Спрашиваем у пользователя имя файла для сохранения
    filename = simpledialog.askstring("Сохранение", "Введите имя файла для сохранения:", parent=root)
    if not filename:
        return
    
    # Добавляем расширение .json, если его нет
    if not filename.endswith('.json'):
        filename += '.json'
    
    # Собираем данные для сохранения
    data_to_save = {
        'accounts': [],
        'operations': [],
        'transfers': [],
        'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }
    
    # Сохраняем только нужные данные из accounts
    cursor.execute("SELECT account_number, balance, status, x, y FROM accounts")
    for account in cursor.fetchall():
        data_to_save['accounts'].append({
            'account_number': account[0],
            'balance': account[1],
            'status': account[2],
            'x': account[3],
            'y': account[4]
        })
    
    # Сохраняем операции
    cursor.execute("SELECT * FROM operations")
    for operation in cursor.fetchall():
        data_to_save['operations'].append({
            'account_number': operation[1],
            'amount': operation[2],
            'operation': operation[3],
            'timestamp': operation[4]
        })
    
    # Сохраняем переводы
    cursor.execute("SELECT * FROM transfers")
    for transfer in cursor.fetchall():
        data_to_save['transfers'].append({
            'source_account_number': transfer[1],
            'target_account_number': transfer[2],
            'amount': transfer[3],
            'timestamp': transfer[4]
        })
    
    try:
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(data_to_save, f, ensure_ascii=False, indent=4)
        messagebox.showinfo("Успех", f"Состояние успешно сохранено в файл {filename}", parent=root)
    except Exception as e:
        messagebox.showerror("Ошибка", f"Не удалось сохранить файл: {str(e)}", parent=root)

def load_saved_state():
    # Спрашиваем подтверждение, так как текущие данные будут перезаписаны
    if not messagebox.askyesno("Подтверждение", 
                             "Текущие данные будут перезаписаны. Продолжить?", 
                             parent=root):
        return
    
    # Выбираем файл для загрузки
    filename = simpledialog.askstring("Загрузка", "Введите имя файла для загрузки:", parent=root)
    if not filename:
        return
    
    # Добавляем расширение .json, если его нет
    if not filename.endswith('.json'):
        filename += '.json'
    
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except Exception as e:
        messagebox.showerror("Ошибка", f"Не удалось загрузить файл: {str(e)}", parent=root)
        return
    
    try:
        # Очищаем текущее состояние (только операции и переводы)
        cursor.execute("DELETE FROM operations")
        cursor.execute("DELETE FROM transfers")
        
        # Обновляем данные счетов
        for account_data in data['accounts']:
            cursor.execute("""
                UPDATE accounts 
                SET balance=?, status=?, x=?, y=?
                WHERE account_number=?
            """, (
                account_data['balance'],
                account_data['status'],
                account_data['x'],
                account_data['y'],
                account_data['account_number']
            ))
        
        # Восстанавливаем операции
        for operation in data['operations']:
            cursor.execute("""
                INSERT INTO operations (account_number, amount, operation, timestamp)
                VALUES (?, ?, ?, ?)
            """, (
                operation['account_number'],
                operation['amount'],
                operation['operation'],
                operation['timestamp']
            ))
        
        # Восстанавливаем переводы
        for transfer in data['transfers']:
            cursor.execute("""
                INSERT INTO transfers (source_account_number, target_account_number, amount, timestamp)
                VALUES (?, ?, ?, ?)
            """, (
                transfer['source_account_number'],
                transfer['target_account_number'],
                transfer['amount'],
                transfer['timestamp']
            ))
        
        conn.commit()
        
        # Обновляем графическое представление
        # Сначала удаляем все счета с холста
        for account in account_list[:]:  # Создаем копию списка для итерации
            account.canvas.delete(account.rect)
            account.canvas.delete(account.text)
            account_list.remove(account)
        
        # Затем заново создаем счета, которые должны быть на поле
        cursor.execute("SELECT account_number, x, y FROM accounts WHERE status='on field'")
        for account_number, x, y in cursor.fetchall():
            new_account = Account(canvas, x, y, account_number, from_db=True)
            account_list.append(new_account)
        
        # Обновляем линии соединений
        update_connection_lines()
        
        messagebox.showinfo("Успех", "Состояние успешно загружено!", parent=root)
    except Exception as e:
        conn.rollback()
        messagebox.showerror("Ошибка", f"Ошибка при загрузке данных: {str(e)}", parent=root)


# Добавляем глобальную переменную для отслеживания клика по линии
line_clicked = False
# Клик ЛКМ
def on_click(event):
    global line_clicked
    # Если был клик по линии, сбрасываем флаг и выходим
    if line_clicked:
        line_clicked = False
        return
        
    clicked_items = canvas.find_withtag("current")
    if not clicked_items:
        # Клик на пустом месте - меню добавления счета
        menu = Menu(canvas, tearoff=0)
        menu.add_command(label="Добавить счет", command=lambda: add_account(event))
        menu.post(event.x_root, event.y_root)
    else:
        clicked_item = clicked_items[0]
        # Проверяем, является ли кликнутый элемент линией
        if canvas.type(clicked_item) == 'line':
            # Устанавливаем флаг, что был клик по линии
            line_clicked = True
            
            # Находим счета, соединенные этой линией
            line_coords = canvas.coords(clicked_item)
            x1, y1, x2, y2 = line_coords
            
            # Ищем счета, которые соответствуют координатам линии
            account1 = None
            account2 = None
            
            for account in account_list:
                # Проверяем первый конец линии
                if abs(account.x + 60 - x1) < 5 and abs(account.y + 80 - y1) < 5:
                    account1 = account
                # Проверяем второй конец линии
                if abs(account.x + 60 - x2) < 5 and abs(account.y + 80 - y2) < 5:
                    account2 = account
            
            if account1 and account2:
                menu = Menu(canvas, tearoff=0)
                menu.add_command(label="История переводов", 
                               command=lambda: show_transfers_between_accounts(
                                   account1.account_number, 
                                   account2.account_number))
                menu.post(event.x_root, event.y_root)
        else:
            # Клик на счете - обычное меню счета
            for account in account_list:
                if account.rect == clicked_item or account.text == clicked_item:
                    menu = Menu(canvas, tearoff=0)
                    menu.add_command(label="Инфо по счету", command=account.show_account_info) 
                    menu.add_command(label="Перевод на другой счет", command=account.transfer)
                    menu.add_command(label="Внести на счет", command=account.add_funds)
                    menu.add_command(label="Удалить счет", command=account.delete_account)
                    menu.post(event.x_root, event.y_root)
                    break
                
# Клик ЛКМ
canvas.bind("<Button-1>", on_click)
# Создаем линии соединений после загрузки всех счетов
update_connection_lines()

def on_canvas_configure(event):
    # Обновляем границы при изменении размера Canvas
    for account in account_list:
        # Проверяем, чтобы счет не выходил за границы Canvas
        new_x = min(max(account.x, 0), event.width - 120)
        new_y = min(max(account.y, 0), event.height - 80)
        
        # Если координаты изменились
        if new_x != account.x or new_y != account.y:
            dx = new_x - account.x
            dy = new_y - account.y
            
            # Перемещаем графические элементы
            account.canvas.move(account.rect, dx, dy)
            account.canvas.move(account.text, dx, dy)
            
            # Обновляем координаты счета
            account.x = new_x
            account.y = new_y
            
            # Обновляем все связанные линии
            for line_id in account.lines:
                coords = account.canvas.coords(line_id)
                # Проверяем, является ли этот счет началом или концом линии
                if abs(coords[0] - (account.x - dx + 60)) < 1 and abs(coords[1] - (account.y - dy + 80)) < 1:
                    # Это начало линии
                    account.canvas.coords(line_id, account.x + 60, account.y + 80, coords[2], coords[3])
                else:
                    # Это конец линии
                    account.canvas.coords(line_id, coords[0], coords[1], account.x + 60, account.y + 80)
                
                # Помещаем линию под другими элементами
                account.canvas.tag_lower(line_id)
    
    # Обновляем линии соединений после изменения размеров
    update_connection_lines()

# Учет изменения размеров Холста (canvas)
canvas.bind("<Configure>", on_canvas_configure)


root.protocol("WM_DELETE_WINDOW", on_closing)
root.mainloop()