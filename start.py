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
        cursor.execute("SELECT balance, type, category FROM accounts WHERE account_number=?", (account_number,))
        result = cursor.fetchone()
        self.balance = result[0] if result else 0
        self.type = result[1] if result else 'asset'
        self.category = result[2] if result else 'undefined'
        
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
                                          text=f"Счет: {account_number}\nБаланс:\n{format_balance(self.balance, self.type)}", 
                                          font=("Arial", 12, "bold"),
                                          justify="center",  # Выравнивание по центру
                                          width=width - 10,  # Ограничиваем ширину текста, чтобы не вылезал за края
                                          )
        
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
        # Размеры фрейма операций (должны быть объявлены как глобальные константы)
        FRAME_WIDTH = OPERATIONS_FRAME_WIDTH
        FRAME_HEIGHT = OPERATIONS_FRAME_HEIGHT
        
        # Проверяем границы Canvas
        canvas_width = self.canvas.winfo_width()
        canvas_height = self.canvas.winfo_height()
        
        # Рассчитываем новые координаты с учетом центра
        new_x = event.x - 60
        new_y = event.y - 40
        
        # Проверяем пересечение с областью фрейма операций
        if (new_x < FRAME_WIDTH and new_y < FRAME_HEIGHT):
            # Если курсор в зоне фрейма - корректируем координаты
            if self.x >= FRAME_WIDTH:  # Если счет был справа от фрейма
                new_x = FRAME_WIDTH  # Ставим у правой границы фрейма
            elif self.y >= FRAME_HEIGHT:  # Если счет был под фреймом
                new_y = FRAME_HEIGHT  # Ставим у нижней границы фрейма
            else:  # Если счет уже в зоне фрейма - оставляем на месте
                if abs(new_x - self.x) > abs(new_y - self.y):
                    new_x = FRAME_WIDTH
                else:
                    new_y = FRAME_HEIGHT
            
        # Ограничиваем границами canvas
        new_x = max(0, min(new_x, canvas_width - 120))
        new_y = max(0, min(new_y, canvas_height - 80))
        
        dx = new_x - self.x
        dy = new_y - self.y
        
        if dx != 0 or dy != 0:
            self.canvas.move(self.rect, dx, dy)
            self.canvas.move(self.text, dx, dy)
            self.x = new_x
            self.y = new_y
            
            # Обновляем линии соединений
            for line_id in self.lines:
                coords = self.canvas.coords(line_id)
                if abs(coords[0] - (self.x - dx + 60)) < 1 and abs(coords[1] - (self.y - dy + 80)) < 1:
                    self.canvas.coords(line_id, self.x + 60, self.y + 80, coords[2], coords[3])
                else:
                    self.canvas.coords(line_id, coords[0], coords[1], self.x + 60, self.y + 80)
                self.canvas.tag_lower(line_id)

    # Обновляем позицию в БД после перемещения
    def update_position(self, event):
        # Сохраняем позицию
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
                amount = float(amount_entry.get())
                amount = int(amount * 100) / 100  # Обрезает лишние знаки без округления

                # Внесение средств <0 нельзя, кроме актив-пассив счетов в учебных целях.
                if self.type == 'activepassive':
                    pass  # Разрешаем любые значения
                elif amount <= 0:
                    messagebox.showwarning("Ошибка", "Сумма должна быть положительной!", parent=dialog)
                    return
                    
                self.balance += amount
                cursor.execute("UPDATE accounts SET balance=? WHERE account_number=?", 
                            (self.balance, self.account_number))
                conn.commit()
                
                self.canvas.itemconfig(self.text, 
                                    text=f"Счет: {self.account_number}\nБаланс:\n{format_balance(self.balance, self.type)}")
                log_operation(self.account_number, amount, "Добавление")
                dialog.destroy()
                
            except ValueError:
                messagebox.showwarning("Ошибка", "Введите корректную сумму!", parent=dialog)

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

    # Обновление текста счета с учетом операции
    def update_text_with_operation(self, operation_amount=None, is_source=False):
        """Обновляет текст счета с информацией об операции"""
        if operation_amount is not None:
            # Получаем старый баланс (до операции)
            old_balance = self.balance + operation_amount if is_source else self.balance - operation_amount
            
            # Форматируем старый баланс
            old_balance_str = format_balance(old_balance, self.type)
            
            # Определяем знак операции
            op_sign = "-" if is_source else "+"
            
            # Форматируем сумму операции (без скобок)
            op_amount = format_balance(abs(operation_amount), self.type).strip("()")
            
            # Основной текст (черный)
            main_text = f"Счет: {self.account_number}\nБаланс:"
            
            # Устанавливаем основной текст
            self.canvas.itemconfig(self.text, 
                                text=main_text,
                                font=("Arial", 12, "bold"),
                                fill="black")
            
            # Получаем координаты основного текста
            bbox = self.canvas.bbox(self.text)
            
            # Создаем/обновляем текст старого баланса (черный)
            if not hasattr(self, 'balance_text_id'):
                self.balance_text_id = self.canvas.create_text(
                    bbox[0] + -20, bbox[3] + 5,  # Под "Баланс:", с небольшим отступом
                    text=old_balance_str,
                    font=("Arial", 12, "bold"),
                    fill="black",
                    anchor="w"
                )
            else:
                self.canvas.itemconfig(self.balance_text_id, 
                                    text=old_balance_str,
                                    fill="black")
            
            # Создаем/обновляем текст операции (красный)
            op_text = f" {op_sign} {op_amount}"
            if not hasattr(self, 'op_text_id'):
                # Позиционируем сразу после текста баланса
                op_bbox = self.canvas.bbox(self.balance_text_id)
                self.op_text_id = self.canvas.create_text(
                    op_bbox[2] + 0, op_bbox[1] + 8,  # Правее баланса, на той же высоте
                    text=op_text,
                    font=("Arial", 12, "bold"),
                    fill="red",
                    anchor="w"
                )
            else:
                self.canvas.itemconfig(self.op_text_id, 
                                    text=op_text,
                                    fill="red")
        else:
            # Обычное отображение без операции
            self.canvas.itemconfig(self.text, 
                                text=f"Счет: {self.account_number}\nБаланс: \n{format_balance(self.balance, self.type)}",
                                font=("Arial", 12, "bold"),
                                fill="black")
            
            # Удаляем дополнительные текстовые элементы, если они есть
            for attr in ['balance_text_id', 'op_text_id']:
                if hasattr(self, attr):
                    self.canvas.delete(getattr(self, attr))
                    delattr(self, attr)

    # Перевод средств между счетами
    def transfer(self):
        # Получаем доступные счета для перевода
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
        dialog.title("Перевод средств")
        dialog.geometry("300x100")  # Увеличил ширину для нового формата
        dialog.resizable(False, False)
        dialog.transient(root)
        dialog.grab_set()
        
        # Основной фрейм
        main_frame = ttk.Frame(dialog, padding=10)
        main_frame.pack(fill='both', expand=True)
        
        # Фрейм для строки "Дебет - Кредит = Сумма"
        transfer_frame = ttk.Frame(main_frame)
        transfer_frame.pack(pady=10)
        
        # Дебет (счет получатель)
        ttk.Label(transfer_frame, text="Дебет:").pack(side='left')
        debit_combobox = ttk.Combobox(transfer_frame, values=available_accounts, state="readonly", width=10)
        debit_combobox.pack(side='left', padx=5)
        debit_combobox.current(0)
        
        # Минус
        ttk.Label(transfer_frame, text=" - ").pack(side='left')
        
        # Кредит (наш текущий счет)
        ttk.Label(transfer_frame, text=f"Кредит {self.account_number}").pack(side='left')
        
        # Равно
        ttk.Label(transfer_frame, text=" = ").pack(side='left')
        
        # Сумма
        amount_entry = ttk.Entry(transfer_frame, width=10)
        amount_entry.pack(side='left')
        amount_entry.focus_set()
        
        # Кнопка перевода
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(pady=5)
        
        def process_transfer():
            try:
                amount = float(amount_entry.get())
                amount = int(amount * 100) / 100  # Обрезает лишние знаки без округления
                target_account_number = int(debit_combobox.get())
                
                if amount <= 0:
                    messagebox.showwarning("Ошибка", "Сумма должна быть положительной!", parent=dialog)
                    return
                    
                # Проверяем связь между счетами
                cursor.execute("""
                    SELECT 1 FROM connections 
                    WHERE account_number=? AND connected_account_number=?
                """, (self.account_number, target_account_number))
                
                if not cursor.fetchone():
                    messagebox.showwarning("Ошибка", "Невозможно перевести - счета не связаны!", parent=dialog)
                    return
                
                # Получаем данные счетов
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
                
                # Объединенная логика для каждого типа источника
                if source_type == 'active':
                    if source_balance < amount:
                        messagebox.showwarning("Ошибка", "Недостаточно средств на активном счете!", parent=dialog)
                        return
                    
                    if target_type == 'active':
                        source_change = -amount  # Уменьшаем актив-источник
                        target_change = amount  # Увеличиваем актив-цель
                    elif target_type == 'passive':
                        source_change = -amount  # Уменьшаем актив
                        target_change = -amount  # Уменьшаем пассив
                        
                        if target_balance + target_change < 0:
                            messagebox.showwarning("Ошибка", "Нельзя сделать пассивный счет отрицательным!", parent=dialog)
                            return
                    else:  # activepassive
                        source_change = -amount
                        target_change = amount  # Всегда увеличивается для А-П
                
                elif source_type == 'passive':
                    if target_type == 'active':
                        source_change = amount  # Пассив увеличивается
                        target_change = amount  # Актив увеличивается
                    elif target_type == 'passive':
                        source_change = amount  # Увеличиваем пассив у источника
                        target_change = -amount  # Уменьшаем пассив у цели
                        if target_balance + target_change < 0:
                            messagebox.showwarning("Ошибка", "Нельзя сделать пассивный счет отрицательным!", parent=dialog)
                            return
                    else:  # activepassive
                        source_change = amount
                        target_change = amount  # Всегда увеличивается для А-П
                
                else:  # activepassive
                    if target_type == 'active':
                        source_change = -amount
                        target_change = amount
                    elif target_type == 'passive':
                        source_change = -amount
                        target_change = -amount
                        if target_balance + target_change < 0:
                            messagebox.showwarning("Ошибка", "Нельзя сделать пассивный счет отрицательным!", parent=dialog)
                            return
                    else:  # activepassive
                        source_change = -amount
                        target_change = amount
                
                # Обновляем балансы
                cursor.execute("UPDATE accounts SET balance=balance+? WHERE account_number=?", 
                            (source_change, self.account_number))
                cursor.execute("UPDATE accounts SET balance=balance+? WHERE account_number=?", 
                            (target_change, target_account_number))
                conn.commit()
                
                # Обновляем интерфейс
                self.balance += source_change
                target_account.balance += target_change
                
                self.canvas.itemconfig(self.text, 
                                    text=f"Счет: {self.account_number}\nБаланс:\n{format_balance(self.balance, self.type)}")
                target_account.canvas.itemconfig(target_account.text, 
                                            text=f"Счет: {target_account.account_number}\nБаланс:\n{format_balance(target_account.balance, target_account.type)}")
                
                log_transfer(self.account_number, target_account_number, amount)
                update_recent_operations()  # Обновляем окно показа последних операций
                dialog.destroy()
                                
            except ValueError:
                messagebox.showwarning("Ошибка", "Введите корректные числовые значения!", parent=dialog)    
        
        ttk.Button(button_frame, text="Перевести", command=process_transfer).pack()
        
        # Центрируем окно
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
        
        # Удаляем все связанные линии с холста
        for line_id in self.lines:
            if canvas.type(line_id) == 'line':
                canvas.delete(line_id)
        
        # Удаляем связанные операции и переводы
        cursor.execute("DELETE FROM operations WHERE account_number=?", (self.account_number,))
        cursor.execute("DELETE FROM transfers WHERE source_account_number=? OR target_account_number=?", 
                    (self.account_number, self.account_number))
        
        # Обновляем статус счета и обнуляем баланс
        cursor.execute("UPDATE accounts SET status=?, balance=0, x=NULL, y=NULL WHERE account_number=?", 
                    ("not on field", self.account_number))
        conn.commit()
            
        # Удаляем графические элементы с холста
        self.canvas.delete(self.rect)
        self.canvas.delete(self.text)
        
        # Удаляем счет из списка
        account_list.remove(self)
        
        # Обновляем линии соединений
        update_connection_lines()
        
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
        cursor.execute("SELECT name, description, balance, type, category FROM accounts WHERE account_number=?", (self.account_number,))
        name, description, balance, acc_type, category = cursor.fetchone()

        # Основная информация о счете
        main_info_frame = tk.Frame(scrollable_frame, width=580)  # Фиксируем ширину
        main_info_frame.pack(pady=10, fill='x', padx=10)
        
        tk.Label(main_info_frame, text=f"Номер счета: {self.account_number}", font=('Arial', 12)).pack(anchor='w')
        tk.Label(main_info_frame, text=f"Название: {name}", font=('Arial', 12)).pack(anchor='w')
        tk.Label(main_info_frame, text=f"Баланс: {format_balance(balance, acc_type)}", font=('Arial', 12)).pack(anchor='w')
        tk.Label(main_info_frame, text=f"Тип: {'Актив-Пассив' if acc_type == 'activepassive' else ('Неопределен' if acc_type == 'undefined' else ('Актив' if acc_type == 'active' else 'Пассив'))}", font=('Arial', 12)).pack(anchor='w')
        #tk.Label(main_info_frame, text=f"Категория: {format_category(category)}", font=('Arial', 12)).pack(anchor='w')
        
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
        tk.Label(scrollable_frame, text="Движение денежных средств:", font=('Arial', 12, 'bold')).pack()

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
                    f"Дебет {target} ← Кредит {source} = {amount} | Время: ({timestamp})"
                )


# Функция обновления списка операций
def update_recent_operations():
    global account_list
    
    # Сначала сбрасываем выделение операций у всех счетов
    for account in account_list:
        account.update_text_with_operation()
    
    # Получаем последние 2 операции
    cursor.execute("""
        SELECT source_account_number, target_account_number, amount, timestamp 
        FROM transfers 
        ORDER BY timestamp DESC 
        LIMIT 2
    """)
    transfers = cursor.fetchall()
    
    # Обновляем метки операций
    for i, (source, target, amount, timestamp) in enumerate(transfers):
        text = f"Дебет {target} ← Кредит {source} = {amount} | ({timestamp.split('.')[0]})"
        operation_labels[i].config(text=text)
        
        # Для самой последней операции (i=0) обновляем отображение счетов
        if i == 0:
            # Находим счета-участники операции
            source_account = next((acc for acc in account_list if acc.account_number == source), None)
            target_account = next((acc for acc in account_list if acc.account_number == target), None)
            
            if source_account:
                source_account.update_text_with_operation(amount, is_source=True)
            if target_account:
                target_account.update_text_with_operation(amount, is_source=False)
    
    # Очистка, если операций < 2
    for i in range(len(transfers), 2):
        operation_labels[i].config(text="")
    
    # Автообновление каждые 5 сек
    root.after(5000, update_recent_operations)

# Добавить счет на поле
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
    # Сначала удаляем все существующие линии с canvas
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
    if (acc_type == 'passive' and balance > 0) or \
       (acc_type == 'active' and balance < 0) or \
       (acc_type == 'activepassive' and balance < 0):
        return f"({abs(balance):.2f})"  # Отрицательное сальдо в скобках
    return str(f"{balance:.2f}")  # Положительное сальдо без скобок

def format_category(category):
    """Форматирует категорию счета для отображения"""
    category_names = {
        'non_current_assets': 'Внеоборотные активы',
        'current_assets': 'Оборотные активы',
        'capital': 'Капитал и резервы',
        'long_term_liabilities': 'Долгосрочные обязательства',
        'short_term_liabilities': 'Краткосрочные обязательства',
        'undefined': 'Неопределено'
    }
    return category_names.get(category, 'Неизвестно')

# Окно истории переводов между двумя счетами
def show_transfers_between_accounts(account1_num, account2_num):
    # Создаем окно
    transfer_window = Toplevel(root)
    transfer_window.title(f"Движение денежных средств между {account1_num} и {account2_num}")
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
            text=f"Движение денежных средств между счетами {account1_num} и {account2_num}", 
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
                f"Дебет {target} ← Кредит {source} = {amount} | Время: ({timestamp})"
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
    report_window.geometry("900x630")
    report_window.grab_set()  # Захватываем фокус

    width = 950
    height = 630
    x = (report_window.winfo_screenwidth() // 2) - (width // 2)
    y = (report_window.winfo_screenheight() // 2) - (height // 2)
    report_window.geometry(f'{width}x{height}+{x}+{y}')

    notebook = ttk.Notebook(report_window)
    notebook.pack(fill='both', expand=True)

    # Вкладка "Общая информация"
    tab1 = tk.Frame(notebook)
    notebook.add(tab1, text="Общая информация")

    # Вкладка "Актив/Пассив"
    tab2 = tk.Frame(notebook)
    notebook.add(tab2, text="Актив/Пассив")

    # Вкладка "Финансовые результаты"
    tab3 = tk.Frame(notebook)
    notebook.add(tab3, text="Финансовые результаты")


    # Функция для обновления вкладки "Общая информация"
    def update_general_info_tab():
        # Очищаем предыдущие данные
        for widget in tab1.winfo_children():
            widget.destroy()
        
        # Основной контейнер с прокруткой
        container = ttk.Frame(tab1)
        container.pack(fill='both', expand=True)
        
        canvas = tk.Canvas(container)
        scrollbar = ttk.Scrollbar(container, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(
                scrollregion=canvas.bbox("all")
            )
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # Фрейм для операций
        operations_frame = ttk.Frame(scrollable_frame)
        operations_frame.pack(fill='x', padx=10, pady=10)
        
        # Заголовок операций
        ttk.Label(operations_frame, text="Операции:", font=('Arial', 12, 'bold')).pack(anchor='w')
        
        # Список операций с фиксированной высотой
        operations_listbox = Listbox(operations_frame, 
                                width=100, 
                                height=12,
                                font=('Arial', 10))
        scrollbar_ops = ttk.Scrollbar(operations_frame, orient="vertical", command=operations_listbox.yview)
        operations_listbox.configure(yscrollcommand=scrollbar_ops.set)
        
        scrollbar_ops.pack(side="right", fill="y")
        operations_listbox.pack(side="left", fill="both", expand=True)
        
        # Заполняем список операций
        cursor.execute("SELECT * FROM operations ORDER BY id DESC")
        for row in cursor.fetchall():
            operations_listbox.insert(tk.END, f"Счет: {row[1]} | Сумма: {row[2]} | Тип: {row[3]} | Время: ({row[4]})")
        
        # Разделитель
        ttk.Separator(scrollable_frame, orient='horizontal').pack(fill='x', pady=10)
        
        # Фрейм для движения средств
        transfers_frame = ttk.Frame(scrollable_frame)
        transfers_frame.pack(fill='x', padx=10, pady=10)
        
        # Заголовок движения средств
        ttk.Label(transfers_frame, text="Движение денежных средств:", font=('Arial', 12, 'bold')).pack(anchor='w')
        
        # Список переводов с фиксированной высотой
        transfers_listbox = Listbox(transfers_frame, 
                                width=100, 
                                height=12,
                                font=('Arial', 10))
        scrollbar_trans = ttk.Scrollbar(transfers_frame, orient="vertical", command=transfers_listbox.yview)
        transfers_listbox.configure(yscrollcommand=scrollbar_trans.set)
        
        scrollbar_trans.pack(side="right", fill="y")
        transfers_listbox.pack(side="left", fill="both", expand=True)
        
        # Заполняем список переводов
        cursor.execute("""
            SELECT source_account_number, target_account_number, amount, timestamp 
            FROM transfers 
            ORDER BY id DESC
        """)
        for row in cursor.fetchall():
            source, target, amount, timestamp = row
            transfers_listbox.insert(tk.END, f"Дебет {target} ← Кредит {source} = {amount} | Время: ({timestamp})")
        
        # Обновляем линии соединений после загрузки данных
        update_connection_lines()
        
        # Прокрутка колесиком мыши
        def _on_mousewheel(event):
            canvas.yview_scroll(int(-1*(event.delta/120)), "units")
        
        canvas.bind("<MouseWheel>", _on_mousewheel)
        scrollable_frame.bind("<MouseWheel>", _on_mousewheel)

    # Вкладка Актив/Пассив
    def update_balance_tab():
        global balance_results_previous_values
        
        # Создаем локальный словарь для хранения изменений в текущей сессии
        current_changes = {}
        
        # Очищаем предыдущие данные
        for widget in tab2.winfo_children():
            widget.destroy()

        # Создаем основной контейнер с прокруткой
        container = ttk.Frame(tab2)
        container.pack(fill='both', expand=True)
        
        canvas = tk.Canvas(container)
        scrollbar = ttk.Scrollbar(container, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(
                scrollregion=canvas.bbox("all")
            )
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # Функция для форматирования валюты
        def format_currency(value):
            """Форматирует: отрицательные значения в скобках"""
            try:
                num = float(value) if isinstance(value, str) else value
                if num < 0:
                    return f"({abs(num):,.2f})"
                return f"{num:,.2f}"
            except (ValueError, TypeError):
                return str(value)
        
        # Создаем главный фрейм для двух колонок
        main_frame = ttk.Frame(scrollable_frame)
        main_frame.pack(fill='both', expand=True, padx=10, pady=10)
        
        # Стиль для элементов
        style = ttk.Style()
        style.configure("Bold.TLabel", font=('Arial', 10, 'bold'))
        style.configure("Subheader.TLabel", font=('Arial', 10, 'bold'), background="#f0f0f0")
        style.configure("Total.TLabel", font=('Arial', 10, 'bold'), background="#e0e0e0")
        style.configure("Changed.TLabel", foreground='red')
        
        # Колонка активов
        active_frame = ttk.Frame(main_frame)
        active_frame.grid(row=0, column=0, sticky="nsew", padx=(0, 20))
        
        # Колонка пассивов
        passive_frame = ttk.Frame(main_frame)
        passive_frame.grid(row=0, column=1, sticky="nsew")
        
        # Фрейм для итоговых строк
        totals_frame = ttk.Frame(main_frame)
        totals_frame.grid(row=1, column=0, columnspan=2, sticky="ew", pady=(10, 0))
        
        # Настраиваем пропорции
        main_frame.grid_columnconfigure(0, weight=1)
        main_frame.grid_columnconfigure(1, weight=1)
        main_frame.grid_rowconfigure(0, weight=1)
        
        # Заголовки колонок
        ttk.Label(active_frame, text="АКТИВЫ", style="Bold.TLabel").pack(fill="x", pady=(0, 10))
        ttk.Label(passive_frame, text="ПАССИВЫ", style="Bold.TLabel").pack(fill="x", pady=(0, 10))
        
        # Получаем текущие значения всех статей
        cursor.execute("""
            SELECT category, item_name, line_number, related_accounts 
            FROM balance_items 
            ORDER BY category, line_number
        """)
        balance_items = cursor.fetchall()
        
        cursor.execute("SELECT account_number, balance, type FROM accounts WHERE status='on field'")
        account_balances = {row[0]: (row[1], row[2]) for row in cursor.fetchall()}

        # Получаем последние операции для определения изменений
        cursor.execute("""
            SELECT account_number, amount, operation, timestamp 
            FROM operations 
            ORDER BY timestamp DESC 
            LIMIT 2
        """)
        recent_operations = cursor.fetchall()
        
        # Определяем, какие счета были изменены в последних операциях
        changed_accounts = set()
        if len(recent_operations) == 2 and recent_operations[0][2] == "Добавление":
            # Если вторая операция - "Добавление", берем только ее
            changed_accounts.add(recent_operations[0][0])
        else:
            # Иначе берем все операции
            for account_number, amount, operation, timestamp in recent_operations:
                changed_accounts.add(account_number)
        
        # Группируем статьи баланса и вычисляем текущие значения
        active_data = {'non_current_assets': [], 'current_assets': []}
        passive_data = {'capital': [], 'long_term_liabilities': [], 'short_term_liabilities': []}
        
        for category, item_name, line_number, accounts_str in balance_items:
            accounts = [int(acc.strip()) for acc in accounts_str.split(',') if acc.strip().isdigit()]
            item_sum = 0.0
            
            for account_num in accounts:
                if account_num in account_balances:
                    balance, acc_type = account_balances[account_num]
                    
                    if category in ['non_current_assets', 'current_assets']:
                        if acc_type == 'active':
                            item_sum += balance
                        elif acc_type == 'passive':
                            item_sum -= balance
                        elif acc_type == 'activepassive':
                            item_sum += balance
                    else:
                        if acc_type == 'passive':
                            item_sum += balance
                        elif acc_type == 'active':
                            item_sum -= balance
                        elif acc_type == 'activepassive':
                            item_sum -= balance
            
            # Проверяем, была ли статья изменена (если связанные счета в changed_accounts)
            is_changed = any(acc_num in changed_accounts for acc_num in accounts)
            if is_changed:
                current_changes[line_number] = item_sum
            
            # Добавляем данные для отображения только если хотя бы одно значение не нулевое
            prev_value = balance_results_previous_values.get(str(line_number), 0.0)
            if abs(item_sum) >= 0.01 or abs(prev_value) >= 0.01:
                item_data = (line_number, item_name, item_sum, is_changed)
                if category in active_data:
                    active_data[category].append(item_data)
                elif category in passive_data:
                    passive_data[category].append(item_data)
        
        # Если это первый запуск, инициализируем предыдущие значения текущими
        if not balance_results_previous_values:
            balance_results_previous_values = {
                str(line_number): sum_val 
                for category in active_data.values() 
                for (line_number, _, sum_val, _) in category
            }
            balance_results_previous_values.update({
                str(line_number): sum_val 
                for category in passive_data.values() 
                for (line_number, _, sum_val, _) in category
            })
        
        # Функция для создания подтаблицы
        def create_subtable(parent, title, items):
            # Пропускаем подтаблицу, если нет элементов для отображения
            if not items:
                return
                
            # Заголовок подтаблицы
            ttk.Label(parent, text=title, style="Subheader.TLabel").pack(fill="x", pady=(10, 5))
            
            # Фрейм для таблицы
            table_frame = ttk.Frame(parent)
            table_frame.pack(fill="x")
            
            # Заголовки столбцов
            headers_frame = ttk.Frame(table_frame)
            headers_frame.pack(fill="x")
            
            ttk.Label(headers_frame, text="№", width=4, style="Bold.TLabel").pack(side="left")
            ttk.Label(headers_frame, text="Наименование", style="Bold.TLabel").pack(side="left", fill="x", expand=True)
            ttk.Label(headers_frame, text="До", width=9, style="Bold.TLabel").pack(side="left")
            ttk.Label(headers_frame, text="После", width=9, style="Bold.TLabel").pack(side="left")
            
            # Добавляем статьи
            for line_num, name, amount, is_changed in items:
                row_frame = ttk.Frame(table_frame)
                row_frame.pack(fill="x", pady=1)
                
                # Определяем стиль в зависимости от наличия изменений
                style_used = "Changed.TLabel" if is_changed else "TLabel"
                
                # Номер статьи
                ttk.Label(row_frame, text=str(line_num), width=4, anchor="e", 
                        style=style_used, borderwidth=1, relief="solid", padding=2).pack(side="left")
                
                # Название статьи
                ttk.Label(row_frame, text=name, anchor="w", 
                        style=style_used, borderwidth=1, relief="solid", padding=2).pack(side="left", fill="x", expand=True)
                
                # Столбец "До" (предыдущее значение)
                prev_value = balance_results_previous_values.get(str(line_num), 0.0)
                ttk.Label(row_frame, text=format_currency(prev_value), width=9, anchor="e", 
                        style=style_used, borderwidth=1, relief="solid", padding=2).pack(side="left")
                
                # Столбец "После" (текущее значение)
                ttk.Label(row_frame, text=format_currency(amount), width=9, anchor="e", 
                        style=style_used, borderwidth=1, relief="solid", padding=2).pack(side="left")
        
        # Создаем подтаблицы для активов (только если есть данные)
        if active_data['non_current_assets']:
            create_subtable(active_frame, "ВНЕОБОРОТНЫЕ АКТИВЫ", active_data['non_current_assets'])
        if active_data['current_assets']:
            create_subtable(active_frame, "ОБОРОТНЫЕ АКТИВЫ", active_data['current_assets'])
        
        # Создаем подтаблицы для пассивов (только если есть данные)
        if passive_data['capital']:
            create_subtable(passive_frame, "КАПИТАЛ И РЕЗЕРВЫ", passive_data['capital'])
        if passive_data['long_term_liabilities']:
            create_subtable(passive_frame, "ДОЛГОСРОЧНЫЕ ОБЯЗАТЕЛЬСТВА", passive_data['long_term_liabilities'])
        if passive_data['short_term_liabilities']:
            create_subtable(passive_frame, "КРАТКОСРОЧНЫЕ ОБЯЗАТЕЛЬСТВА", passive_data['short_term_liabilities'])
        
        # Считаем итоги только по отображаемым статьям
        total_active_before = sum(
            balance_results_previous_values.get(str(line_number), 0.0) 
            for category in active_data.values() 
            for (line_number, _, _, _) in category
        )
        
        total_active_after = sum(
            amount 
            for category in active_data.values() 
            for (_, _, amount, _) in category
        )
        
        total_passive_before = sum(
            balance_results_previous_values.get(str(line_number), 0.0) 
            for category in passive_data.values() 
            for (line_number, _, _, _) in category
        )
        
        total_passive_after = sum(
            amount 
            for category in passive_data.values() 
            for (_, _, amount, _) in category
        )
        
        # Добавляем итоговые строки только если есть что отображать
        if active_data['non_current_assets'] or active_data['current_assets'] or \
        passive_data['capital'] or passive_data['long_term_liabilities'] or passive_data['short_term_liabilities']:
            
            totals_after_frame = ttk.Frame(totals_frame)
            totals_after_frame.pack(fill="x")
            
            ttk.Label(totals_after_frame, text=f"Итого активы: {format_currency(total_active_after)}", 
                    style="Total.TLabel").pack(side="left", fill="x", expand=True)
            
            ttk.Label(totals_after_frame, text=f"Итого пассивы: {format_currency(total_passive_after)}", 
                    style="Total.TLabel").pack(side="left", fill="x", expand=True)
            
            # Проверка баланса
            if abs(total_active_after - total_passive_after) >= 0.01:
                error_frame = ttk.Frame(scrollable_frame)
                error_frame.pack(fill='x', padx=10, pady=10)
                
                ttk.Label(error_frame, 
                        text=f"ОШИБКА: Активы {format_currency(total_active_after)} и Пассивы {format_currency(total_passive_after)} не сходятся!",
                        foreground='red', 
                        font=('Arial', 12, 'bold')).pack()
        
        # Обновляем предыдущие значения только если произошли реальные изменения
        has_changes = any(
            abs(current_changes.get(line_number, 0.0) - 
            balance_results_previous_values.get(str(line_number), 0.0)) >= 0.01
            for category in active_data.values() 
            for (line_number, _, _, is_changed) in category if is_changed
        ) or any(
            abs(current_changes.get(line_number, 0.0) - 
            balance_results_previous_values.get(str(line_number), 0.0)) >= 0.01
            for category in passive_data.values() 
            for (line_number, _, _, is_changed) in category if is_changed
        )
        
        if has_changes:
            # Сохраняем текущие значения как предыдущие для следующего обновления
            balance_results_previous_values = {
                str(line_number): amount 
                for category in active_data.values() 
                for (line_number, _, amount, _) in category
            }
            balance_results_previous_values.update({
                str(line_number): amount 
                for category in passive_data.values() 
                for (line_number, _, amount, _) in category
            })

    # Функция для обновления вкладки "Финансовые результаты"
    def update_financial_results_tab():
        global financial_results_previous_values
        
        # Очищаем предыдущие данные
        for widget in tab3.winfo_children():
            widget.destroy()
            
        # Создаем основной контейнер с прокруткой
        container = ttk.Frame(tab3)
        container.pack(fill='both', expand=True)
        
        canvas = tk.Canvas(container)
        scrollbar = ttk.Scrollbar(container, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(
                scrollregion=canvas.bbox("all")
            )
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # Функция для форматирования валюты
        def format_currency(value):
            """Форматирует: отрицательные значения в скобках"""
            try:
                num = float(value) if isinstance(value, str) else value
                if num < 0:
                    return f"({abs(num):,.2f})"
                return f"{num:,.2f}"
            except (ValueError, TypeError):
                return str(value)
        
        # Стили для элементов
        style = ttk.Style()
        style.configure("Bold.TLabel", font=('Arial', 10, 'bold'))
        style.configure("Subheader.TLabel", font=('Arial', 10, 'bold'), background="#f0f0f0")
        style.configure("Total.TLabel", font=('Arial', 10, 'bold'), background="#e0e0e0")
        style.configure("Changed.TLabel", foreground='red')
        
        # Заголовок
        ttk.Label(scrollable_frame, text="ФИНАНСОВЫЕ РЕЗУЛЬТАТЫ", 
                font=('Arial', 14, 'bold')).pack(pady=10)
        
        # Получаем данные из таблицы financial_results_items
        cursor.execute("""
            SELECT line_number, item_name, transactions, line_formula 
            FROM financial_results_items 
            ORDER BY 
                CAST(line_number/100 AS INTEGER),
                CASE WHEN line_number % 100 = 0 THEN 1 ELSE 0 END,
                line_number
        """)
        financial_items = cursor.fetchall()
        
        if not financial_items:
            ttk.Label(scrollable_frame, text="Нет данных о финансовых результатах",
                    font=('Arial', 12)).pack(pady=20)
            return
        
        # Создаем таблицу
        table_frame = ttk.Frame(scrollable_frame)
        table_frame.pack(fill='x', padx=10, pady=5)
        
        # Заголовки столбцов
        headers = ["Номер", "Наименование", "До", "После"]
        for col, header in enumerate(headers):
            ttk.Label(table_frame, text=header, font=('Arial', 10, 'bold'), 
                    borderwidth=1, relief="solid", padding=5).grid(row=0, column=col, sticky="nsew")
        
        # Настраиваем ширину столбцов
        table_frame.grid_columnconfigure(0, weight=1, minsize=80)
        table_frame.grid_columnconfigure(1, weight=3, minsize=300)
        table_frame.grid_columnconfigure(2, weight=1, minsize=100)
        table_frame.grid_columnconfigure(3, weight=1, minsize=100)
        
        # Функция для расчета суммы по проводкам
        def calculate_transactions_sum(transactions_str):
            if not transactions_str:
                return 0.0
            
            total = 0.0
            transactions = [t.strip() for t in transactions_str.split(',') if t.strip()]
            
            for transaction in transactions:
                try:
                    source, target = transaction.split('-')
                    source = source.strip()
                    target = target.strip()
                    
                    cursor.execute("""
                        SELECT SUM(amount) 
                        FROM transfers 
                        WHERE source_account_number=? AND target_account_number=?
                    """, (source, target))
                    sum_amount = cursor.fetchone()[0] or 0.0
                    total += sum_amount
                except ValueError:
                    continue
            
            return total
        
        # Функция для расчета суммы по формуле
        def calculate_formula_sum(formula_str, results_dict):
            if not formula_str:
                return 0.0
            
            try:
                components = [c.strip() for c in formula_str.split(',') if c.strip()]
                total = 0.0
                
                for comp in components:
                    sign = 1
                    line_num = comp
                    
                    if comp.startswith('-'):
                        sign = -1
                        line_num = comp[1:]
                    
                    if line_num in results_dict:
                        total += sign * results_dict[line_num]
                
                return total
            except:
                return 0.0
        
        # Словарь для хранения текущих значений
        current_values = {}
        
        # Сначала вычисляем все текущие суммы
        results_dict = {}
        for line_number, item_name, transactions, line_formula in financial_items:
            transactions_sum = calculate_transactions_sum(transactions)
            
            if line_formula:
                formula_sum = calculate_formula_sum(line_formula, results_dict)
                amount = formula_sum
            else:
                amount = transactions_sum
            
            results_dict[str(line_number)] = amount
            current_values[str(line_number)] = amount
        
        # Если это первый запуск, инициализируем предыдущие значения текущими
        if not financial_results_previous_values:
            financial_results_previous_values = current_values.copy()
        
        # Заполняем таблицу
        row = 1
        for line_number, item_name, transactions, line_formula in financial_items:
            current_amount = current_values.get(str(line_number), 0.0)
            previous_amount = financial_results_previous_values.get(str(line_number), 0.0)
            
            # Определяем, изменилось ли значение (учитываем погрешность округления)
            is_changed = abs(current_amount - previous_amount) >= 0.01
            
            # Определяем стиль в зависимости от изменения
            style_used = "Changed.TLabel" if is_changed else "TLabel"
            
            # Номер строки
            ttk.Label(table_frame, text=str(line_number), 
                    style=style_used, borderwidth=1, relief="solid", padding=2).grid(row=row, column=0, sticky="nsew")
            
            # Название статьи
            ttk.Label(table_frame, text=item_name, 
                    style=style_used, borderwidth=1, relief="solid", padding=2).grid(row=row, column=1, sticky="nsew")
            
            # Столбец "До" (предыдущее значение)
            ttk.Label(table_frame, text=format_currency(previous_amount), 
                    style=style_used, borderwidth=1, relief="solid", padding=2).grid(row=row, column=2, sticky="nsew")
            
            # Столбец "После" (текущее значение)
            ttk.Label(table_frame, text=format_currency(current_amount), 
                    style=style_used, borderwidth=1, relief="solid", padding=2).grid(row=row, column=3, sticky="nsew")
            
            row += 1
        
        # Обновляем предыдущие значения только если произошли реальные изменения
        # Проверяем, есть ли хотя бы одно изменение
        has_changes = any(
            abs(current_values.get(str(line_number), 0.0) - 
                financial_results_previous_values.get(str(line_number), 0.0)) >= 0.01
            for line_number, _, _, _ in financial_items
        )
        
        if has_changes:
            # Сохраняем текущие значения как предыдущие для следующего обновления
            financial_results_previous_values = current_values.copy()
        
        # Прокрутка колесиком мыши
        def _on_mousewheel(event):
            canvas.yview_scroll(int(-1*(event.delta/120)), "units")
        
        canvas.bind("<MouseWheel>", _on_mousewheel)
        scrollable_frame.bind("<MouseWheel>", _on_mousewheel)

    # Функция для обновления текущей вкладки
    def on_tab_changed(event):
        current_tab = notebook.index(notebook.select())
        if current_tab == 0:  # Общая информация
            update_general_info_tab()
        elif current_tab == 1:  # Актив/Пассив
            update_balance_tab()
        elif current_tab == 2:  # Финансовые результаты
            update_financial_results_tab()
    
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
            SELECT account_number, name, description, balance, type, category 
            FROM accounts 
            WHERE account_number BETWEEN ? AND ?
            ORDER BY account_number
        """, account_numbers_range)
        
        accounts = cursor.fetchall()

        for i, (account_number, name, description, balance, acc_type, category) in enumerate(accounts):
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

# Окно Расшифровка активов баланса
def show_balance_items_info():
    info_window = Toplevel(root)
    info_window.title("Расшифровка активов баланса")
    info_window.geometry("800x600")
    info_window.resizable(False, False)
    info_window.transient(root)
    info_window.grab_set()

    # Центрируем окно
    width = 800
    height = 600
    x = (info_window.winfo_screenwidth() // 2) - (width // 2)
    y = (info_window.winfo_screenheight() // 2) - (height // 2)
    info_window.geometry(f'{width}x{height}+{x}+{y}')

    # Создаем основной контейнер с прокруткой
    main_frame = tk.Frame(info_window)
    main_frame.pack(fill='both', expand=True)

    canvas = tk.Canvas(main_frame, width=800)
    scrollbar = ttk.Scrollbar(main_frame, orient='vertical', command=canvas.yview)
    scrollable_frame = tk.Frame(canvas, width=780)  # Фиксируем ширину внутреннего фрейма

    scrollable_frame.bind(
        "<Configure>",
        lambda e: canvas.configure(
            scrollregion=canvas.bbox("all"),
            width=780  # Устанавливаем ширину Canvas при конфигурации
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

    # Получаем данные из БД, группируя по категориям
    cursor.execute("""
        SELECT category, item_name, line_number, description, related_accounts 
        FROM balance_items 
        ORDER BY category, line_number
    """)
    balance_items = cursor.fetchall()

    # Словарь для группировки по категориям с правильным порядком
    categories = {
        'Актив': {
            'non_current_assets': [],
            'current_assets': []
        },
        'Пассив': {
            'capital': [],
            'long_term_liabilities': [],
            'short_term_liabilities': []
        }
    }

    for item in balance_items:
        category = item[0]
        # Распределяем по категориям в зависимости от типа
        if category in ['non_current_assets', 'current_assets']:
            categories['Актив'][category].append(item[1:])  # (item_name, line_number, description, related_accounts)
        elif category in ['capital', 'long_term_liabilities', 'short_term_liabilities']:
            categories['Пассив'][category].append(item[1:])

    # Выводим данные по категориям
    for section, section_categories in categories.items():
        # Заголовок раздела (Актив или Пассив)
        section_label = tk.Label(
            scrollable_frame, 
            text=section,
            font=('Arial', 16, 'bold'),
            bg='lightgray',
            anchor='w'
        )
        section_label.pack(fill='x', padx=10, pady=(15, 5), ipady=5)

        # Выводим подкатегории в правильном порядке
        if section == 'Актив':
            subcategories_order = ['non_current_assets', 'current_assets']
        else:  # Пассив
            subcategories_order = ['capital', 'long_term_liabilities', 'short_term_liabilities']

        for subcategory in subcategories_order:
            items = section_categories[subcategory]
            if not items:
                continue

            # Заголовок подкатегории
            subcategory_label = tk.Label(
                scrollable_frame, 
                text=format_category(subcategory),
                font=('Arial', 14, 'bold'),
                anchor='w'
            )
            subcategory_label.pack(fill='x', padx=20, pady=(15, 5), anchor='w')

            # Выводим все элементы подкатегории
            for item in items:
                item_name, line_number, description, related_accounts = item

                # Фрейм для элемента
                item_frame = tk.Frame(scrollable_frame, bd=1, relief='groove', padx=10, pady=10)
                item_frame.pack(fill='x', padx=20, pady=5)

                # Название и номер строки
                name_number_frame = tk.Frame(item_frame)
                name_number_frame.pack(fill='x', pady=(0, 5))

                tk.Label(
                    name_number_frame, 
                    text=f"{item_name} (строка {line_number})",
                    font=('Arial', 12, 'bold'),
                    anchor='w'
                ).pack(side='left')

                # Связанные счета
                accounts_label = tk.Label(
                    name_number_frame,
                    text=f"Счета: {related_accounts}",
                    font=('Arial', 10),
                    fg='gray',
                    anchor='w'
                )
                accounts_label.pack(side='right')

                # Описание (с прокруткой)
                desc_frame = tk.Frame(item_frame)
                desc_frame.pack(fill='x')

                tk.Label(desc_frame, text="Описание:", font=('Arial', 10)).pack(anchor='w')

                desc_text = tk.Text(
                    desc_frame,
                    width=70,
                    height=4,
                    wrap='word',
                    font=('Arial', 10),
                    padx=5,
                    pady=5,
                    bd=1,
                    relief='solid'
                )
                desc_scroll = ttk.Scrollbar(desc_frame, orient='vertical', command=desc_text.yview)
                desc_text.configure(yscrollcommand=desc_scroll.set)

                desc_text.insert('1.0', description)
                desc_text.config(state='disabled')

                desc_text.pack(side='left', fill='x', expand=True)
                desc_scroll.pack(side='right', fill='y')

        # Разделитель между разделами
        ttk.Separator(scrollable_frame, orient='horizontal').pack(fill='x', pady=10)

    # Если нет данных
    if not balance_items:
        tk.Label(
            scrollable_frame,
            text="Нет данных о расшифровке баланса",
            font=('Arial', 12),
            fg='gray'
        ).pack(pady=20)

# Функция для показа информации о финансовых результатах
def show_financial_results_info():
    info_window = Toplevel(root)
    info_window.title("Финансовые результаты - Справочник")
    info_window.geometry("900x600")
    info_window.resizable(False, False)
    info_window.transient(root)
    info_window.grab_set()

    # Центрируем окно
    width = 900
    height = 600
    x = (info_window.winfo_screenwidth() // 2) - (width // 2)
    y = (info_window.winfo_screenheight() // 2) - (height // 2)
    info_window.geometry(f'{width}x{height}+{x}+{y}')

    # Стили
    style = ttk.Style()
    style.configure('Header.TLabel', font=('Arial', 10, 'bold'), padding=3)
    style.configure('Data.TLabel', font=('Arial', 9), padding=2)

    # Главный контейнер
    main_frame = ttk.Frame(info_window)
    main_frame.pack(fill='both', expand=True, padx=5, pady=5)

    # Canvas и Scrollbar
    canvas = tk.Canvas(main_frame, highlightthickness=0, width=880)
    scrollbar = ttk.Scrollbar(main_frame, orient='vertical', command=canvas.yview)
    table_frame = ttk.Frame(canvas)

    # Настройка прокрутки
    table_frame.bind(
        "<Configure>",
        lambda e: canvas.configure(
            scrollregion=canvas.bbox("all")
        )
    )

    canvas.create_window((0, 0), window=table_frame, anchor='nw')
    canvas.configure(yscrollcommand=scrollbar.set)

    # Упаковка
    canvas.pack(side='left', fill='both', expand=True)
    scrollbar.pack(side='right', fill='y')

    # Получение и сортировка данных
    cursor.execute("""
        SELECT line_number, item_name, description, transactions, line_formula 
        FROM financial_results_items 
        ORDER BY 
            CAST(line_number/100 AS INTEGER),  -- Группируем по первым двум цифрам
            CASE WHEN line_number % 100 = 0 THEN 1 ELSE 0 END,  -- Сначала обычные строки
            line_number  -- Затем итоговые (оканчивающиеся на 00)
    """)
    items = cursor.fetchall()

    if not items:
        ttk.Label(table_frame, text="Нет данных").pack(pady=20)
        return

    # Заголовок таблицы
    ttk.Label(table_frame, text="Справочник строк финансовых результатов", 
             font=('Arial', 12, 'bold')).grid(row=0, column=0, columnspan=5, pady=5)

    # Ширины столбцов (сумма = 880)
    col_widths = [50, 150, 400, 200, 80]
    wrap_lengths = [45, 140, 390, 190, 70]

    # Заголовки столбцов
    headers = ["Номер", "Наименование", "Описание", "Проводки", "Строки"]
    for col, (header, width) in enumerate(zip(headers, col_widths)):
        header_cell = ttk.Frame(table_frame, width=width, height=25)
        header_cell.grid(row=1, column=col, sticky='nsew')
        ttk.Label(header_cell, text=header, style='Header.TLabel', 
                wraplength=wrap_lengths[col]).pack(fill='both', expand=True)

    # Данные таблицы
    row_idx = 2  # Начинаем с 2, так как 0-заголовок, 1-заголовки столбцов

    for line_number, item_name, description, transactions, line_formula in items:
        # Высота строки (5 строк для описания)
        row_height = 85
        
        # Код строки
        cell = ttk.Frame(table_frame, width=col_widths[0], height=row_height)
        cell.grid(row=row_idx, column=0, sticky='nsew')
        ttk.Label(cell, text=str(line_number), style='Data.TLabel', 
                wraplength=wrap_lengths[0]).place(relx=0.5, rely=0.5, anchor='center')
        
        # Наименование
        cell = ttk.Frame(table_frame, width=col_widths[1], height=row_height)
        cell.grid(row=row_idx, column=1, sticky='nsew')
        ttk.Label(cell, text=item_name, style='Data.TLabel', 
                wraplength=wrap_lengths[1]).place(relx=0.5, rely=0.5, anchor='center')
        
        # Описание (с прокруткой)
        cell = ttk.Frame(table_frame, width=col_widths[2], height=row_height)
        cell.grid(row=row_idx, column=2, sticky='nsew')
        
        text_frame = ttk.Frame(cell)
        text_frame.pack(fill='both', expand=True, padx=2, pady=2)
        
        text = tk.Text(text_frame, wrap='word', font=('Arial', 9), 
                     height=5, width=col_widths[2]//8,
                     borderwidth=0, highlightthickness=0)
        text.insert('1.0', description or '')
        text.config(state='disabled')
        
        text_scroll = ttk.Scrollbar(text_frame, orient='vertical', command=text.yview)
        text.configure(yscrollcommand=text_scroll.set)
        
        text.pack(side='left', fill='both', expand=True)
        text_scroll.pack(side='right', fill='y')
        
        # Проводки
        cell = ttk.Frame(table_frame, width=col_widths[3], height=row_height)
        cell.grid(row=row_idx, column=3, sticky='nsew')
        
        # Отображаем проводки как есть
        ttk.Label(cell, text=transactions or '', style='Data.TLabel', 
                wraplength=wrap_lengths[3]).place(relx=0.5, rely=0.5, anchor='center')
        
        # Формула
        cell = ttk.Frame(table_frame, width=col_widths[4], height=row_height)
        cell.grid(row=row_idx, column=4, sticky='nsew')
        ttk.Label(cell, text=line_formula or '', style='Data.TLabel', 
                wraplength=wrap_lengths[4]).place(relx=0.5, rely=0.5, anchor='center')
        
        row_idx += 1

    # Настройка столбцов
    for i in range(5):
        table_frame.grid_columnconfigure(i, weight=1 if i == 2 else 0)

    # Прокрутка колесиком
    def _on_mousewheel(event):
        canvas.yview_scroll(int(-1*(event.delta/120)), "units")

    canvas.bind("<MouseWheel>", _on_mousewheel)
    table_frame.bind("<MouseWheel>", _on_mousewheel)



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
            balance REAL DEFAULT 0,
            status TEXT DEFAULT 'not on field',
            x INTEGER,
            y INTEGER,
            type TEXT CHECK(type IN ('active', 'passive', 'activepassive', 'undefined')) DEFAULT 'asset',
            category TEXT CHECK(category IN (
                'non_current_assets', 
                'current_assets', 
                'capital', 
                'long_term_liabilities', 
                'short_term_liabilities',
                'undefined'
            )) DEFAULT 'undefined'
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

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS balance_items (
            id INTEGER PRIMARY KEY,
            category TEXT NOT NULL CHECK(category IN (
                'non_current_assets', 
                'current_assets', 
                'capital', 
                'long_term_liabilities', 
                'short_term_liabilities',
                'undefined'
            )) DEFAULT 'undefined',               -- Категория статьи баланса
            item_name TEXT NOT NULL,              -- Название строки в балансе
            line_number INTEGER NOT NULL,         -- Номер строки в балансе
            description TEXT,                     -- Описание текст
            related_accounts TEXT                 -- Связанные счета в виде текста, по типу "4, -5"
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS financial_results_items (
            id INTEGER PRIMARY KEY,
            line_number INTEGER NOT NULL UNIQUE,  -- Код строки (2110, 2120)
            item_name TEXT NOT NULL,             -- Название строки
            description TEXT,                    -- Описание
            transactions TEXT,        -- Проводки в формате "23-90, 21-90, 66-91"
            line_formula TEXT DEFAULT ''         -- Формула из других строк ("2110,-2120")
        )
    ''')
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


# Глобальный словарь для хранения измененных статей баланса
changed_balance_items = {}
# Глобальный словарь для хранения измененных статей финансовых результатов
changed_financial_items = {}

# Глобальная переменная для хранения предыдущих значений баланса
balance_results_previous_values = {}
# Глобальная переменная для хранения предыдущих значений
financial_results_previous_values = {}

# Подключение к базе данных
db_path = resource_path('accounts.db')
conn = sqlite3.connect(db_path)
cursor = conn.cursor()
init_db()


# Функция для подтверждения очистки балансов
def confirm_clear_balances():
    if messagebox.askyesno("Подтверждение", "Точно ли хотите очистить все связи?", parent=root):
        if messagebox.askyesno("Последнее предупреждение", "Вы уверены? Все балансы и связи будут обнулены!", parent=root):
            # Очистка баланса
            clear_balances()

# Функция очистки балансов
def clear_balances():
    global changed_balance_items
    # Очищаем список измененных статей
    changed_balance_items.clear()

    # Глобальная переменная для хранения предыдущих значений баланса
    balance_results_previous_values.clear()
    # Глобальная переменная для хранения предыдущих значений
    financial_results_previous_values.clear()

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
                               text=f"Счет: {account.account_number}\nБаланс:\n{format_balance(account.balance, account.type)}")
    
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
    global changed_balance_items
    # Очищаем список измененных статей
    changed_balance_items.clear()

    # Глобальная переменная для хранения предыдущих значений баланса
    balance_results_previous_values.clear()
    # Глобальная переменная для хранения предыдущих значений
    financial_results_previous_values.clear()

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

# Создаем холст (на всё окно)
canvas = tk.Canvas(root, bg="white")
canvas.pack(fill="both", expand=True)

# Фрейм для операций (будет внутри холста)
operations_frame = ttk.Frame(canvas, borderwidth=1, relief="groove", padding=5)
operations_frame.pack_propagate(False)  # Фиксируем размер
operations_frame.config(width=320, height=100)  # Фиксированные размеры

# Создаем окно на холсте для фрейма операций
canvas.create_window(
    0, 0,  # Позиция (x,y) - левый верхний угол с отступом 10 пикселей
    window=operations_frame,
    anchor="nw"
)

# Заголовок и метки операций (как было)
ttk.Label(operations_frame, text="Последние 2 корреспонденции:", font=('Arial', 10, 'bold')).pack(side=tk.TOP, anchor='w')
operation_labels = []
for i in range(2):
    lbl = ttk.Label(
        operations_frame, 
        text="", 
        font=('Arial', 9), 
        borderwidth=1, 
        relief="solid", 
        padding=5,
        background='white'
    )
    lbl.pack(side=tk.TOP, fill=tk.X, pady=2)
    operation_labels.append(lbl)

OPERATIONS_FRAME_WIDTH = 320
OPERATIONS_FRAME_HEIGHT = 100


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
file_menu.add_command(label="Расшифровка активов баланса", command=show_balance_items_info)
file_menu.add_command(label="Финансовые результаты", command=show_financial_results_info)
file_menu.add_command(label="Инфо по всем счетам", command=show_all_accounts_info)
file_menu.add_command(label="Инфо по связям счетов", command=show_account_connections)

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

# Сохраняем текущее состояние
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
        'changed_balance_items': changed_balance_items,
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

# Загружаем текущее состояние
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
        
        # Загружаем изменения статей
        changed_balance_items = data.get('changed_balance_items', {})
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
                menu.add_command(label="Движение средств", 
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
                    menu.post(event.x_root, event.y_root)
                    break
                
# Клик ЛКМ
canvas.bind("<Button-1>", on_click)
# Создаем линии соединений после загрузки всех счетов
update_connection_lines()

# Запускаем автообновление операций
update_recent_operations()

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