import tkinter as tk
from tkinter import ttk, messagebox
import json
import psycopg2
from config import host, database, user, password
import re
from datetime import datetime, date, time
import time
import subprocess
from json import JSONEncoder
connection = psycopg2.connect(
    host=host,
    database=database,
    user=user,
    password=password
)
class DateTimeEncoder(JSONEncoder):
    def default(self, obj):
        if isinstance(obj, (datetime, date)):
            return obj.isoformat()
        elif isinstance(obj, time):
            return obj.strftime('%H:%M:%S')
        return super().default(obj)

        return super().default(obj)
with connection.cursor() as cursor:
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS loggi (
            ip VARCHAR(15),
    date DATE,
    time TIME,
    first_line_of_request TEXT,
    status INTEGER,
    size BIGINT
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id SERIAL PRIMARY KEY,
            username VARCHAR(50) NOT NULL,
            password VARCHAR(50) NOT NULL
        )
    """)
    connection.commit()

def insert_access_log(log_string):
    pattern = r'^(.*?) - - \[(.*?)\] "(.*?)" (\d+) (\d+)$'
    match = re.match(pattern, log_string)
    if match:
        ip = match.group(1)
        datetime_str = match.group(2)
        first_line = match.group(3)
        status = int(match.group(4))
        size = int(match.group(5))

        date_time = datetime.strptime(datetime_str, '%d/%b/%Y:%H:%M:%S %z')

        date = date_time.date()
        time = date_time.time()

        select_query = "SELECT COUNT(*) FROM loggi WHERE ip = %s AND date = %s AND time = %s AND first_line_of_request = %s AND status = %s AND size = %s"
        values = (ip, date, time, first_line, status, size)

        cursor = connection.cursor()
        cursor.execute(select_query, values)
        row_count = cursor.fetchone()[0]
        cursor.close()

        if row_count == 0:
            insert_query = "INSERT INTO loggi (ip, date, time, first_line_of_request,status, size) VALUES (%s, %s, %s, %s, %s, %s)"
            values = (ip, date, time,first_line, status, size)

            cursor = connection.cursor()
            cursor.execute(insert_query, values)
            connection.commit()
            cursor.close()

def read_data():
    try:
        cursor = connection.cursor()

        group_by = ""
        if group_by_ip.get():
            group_by = "ip"
        elif group_by_date.get():
            group_by = "date"

        sort_by = sort_combobox.get()

        select_query = "SELECT * FROM loggi"

        start_date = start_date_entry.get()
        end_date = end_date_entry.get()

        if start_date and end_date:
            select_query += " WHERE date BETWEEN %s AND %s"
            values = (start_date, end_date)
        else:
            values = ()

        if group_by:
            select_query += " GROUP BY " + group_by + ", ip, date, time, first_line_of_request, status, size"

        cursor.execute(select_query, values)
        data = cursor.fetchall()

        tree.delete(*tree.get_children())

        if sort_by == "IP (Asc)":
            data = sorted(data, key=lambda x: x[0])
        elif sort_by == "IP (Des)":
            data = sorted(data, key=lambda x: x[0], reverse=True)
        elif sort_by == "Date (Asc)":
            data = sorted(data, key=lambda x: x[2])
        elif sort_by == "Date (Des)":
            data = sorted(data, key=lambda x: x[2], reverse=True)

        for row in data:
            tree.insert("", tk.END, values=row)

        cursor.close()
    except (Exception, psycopg2.Error) as error:
        print("Error reading data from the database:", error)




def reset_data():
    tree.delete(*tree.get_children())

    group_by_ip.set(0)
    group_by_date.set(0)
    start_date_entry.delete(0, tk.END)
    end_date_entry.delete(0, tk.END)


def get_logs():
    try:
        cursor = connection.cursor()

        start_date = start_date_entry.get()
        end_date = end_date_entry.get()


        select_query = "SELECT ip, date, time, first_line_of_request, status, size FROM loggi"

        if start_date and end_date:
            select_query += " WHERE date BETWEEN %s AND %s"
            values = (start_date, end_date)
            cursor.execute(select_query, values)
        else:
            cursor.execute(select_query)

        data = cursor.fetchall()


        logs_json = []
        for row in data:
            log = {
                "IP": row[0],
                "Date": str(row[1]),
                "Time": str(row[2]),
                "First_Line": row[3],
                "Status": row[4],
                "Size": row[5]
            }
            logs_json.append(log)


        with open("data.json", "w") as file:
            json.dump(logs_json, file, indent=4)

        cursor.close()


        messagebox.showinfo("Успешно!", "Все логи сохранены в data.json")

    except (Exception, psycopg2.Error) as error:
        print("Error retrieving logs data:", error)

def register_user():
    username = username_entry.get()
    password = password_entry.get()

    if not username or not password:
        messagebox.showerror("Ошибка!", "Пожалуйста, заполните все поля.")
        return

    try:
        cursor = connection.cursor()

        select_query = "SELECT COUNT(*) FROM users WHERE username = %s"
        cursor.execute(select_query, (username,))
        row_count = cursor.fetchone()[0]

        if row_count > 0:
            messagebox.showerror("Ошибка!", "Пользователь с таким именем уже существует.")
            return

        insert_query = "INSERT INTO users (username, password) VALUES (%s, %s)"
        cursor.execute(insert_query, (username, password))
        connection.commit()
        cursor.close()

        messagebox.showinfo("Успешно!", "Регистрация прошла успешно.")

        username_entry.delete(0, tk.END)
        password_entry.delete(0, tk.END)
    except (Exception, psycopg2.Error) as error:
        print("Error registering user:", error)


def log_in():
    username = username_entry.get()
    password = password_entry.get()

    if not username or not password:
        messagebox.showerror("Ошибка!", "Пожалуйста, заполните все поля.")
        return

    try:
        cursor = connection.cursor()

        select_query = "SELECT COUNT(*) FROM users WHERE username = %s AND password = %s"
        cursor.execute(select_query, (username, password))
        row_count = cursor.fetchone()[0]

        if row_count == 0:
            messagebox.showerror("Ошибка!", "Неверное имя пользователя или пароль.")
            return

        messagebox.showinfo("Успешно!", "Вход выполнен успешно.")

        username_entry.delete(0, tk.END)
        password_entry.delete(0, tk.END)

        notebook.tab(1, state="normal")
        notebook.select(1)

        cursor.close()
    except (Exception, psycopg2.Error) as error:
        print("Error logging in:", error)



def run_program():

    messagebox.showinfo("Info", "Program is running!")

def schedule_program():

    schedule_time = "10:00"
    while True:
        current_time = time.strftime("%H:%M")
        if current_time == schedule_time:
            run_program()
            break
        time.sleep(60)
def log_out():
    notebook.tab(1, state="disabled")
    notebook.tab(0, state="normal")
    notebook.select(0)


def quit_application():
    connection.close()
    root.destroy()


root = tk.Tk()
root.title("Логи доступа")

notebook = ttk.Notebook(root)
notebook.pack(pady=10)

login_frame = ttk.Frame(notebook)
main_frame = ttk.Frame(notebook)

login_frame.pack(fill="both", expand=1)
main_frame.pack(fill="both", expand=1)

notebook.add(login_frame, text="Вход")
notebook.add(main_frame, text="Главная", state="disabled")

username_label = ttk.Label(login_frame, text="Имя пользователя:")
username_label.grid(row=0, column=0, sticky=tk.W, padx=10, pady=10)

username_entry = ttk.Entry(login_frame)
username_entry.grid(row=0, column=1, padx=10, pady=10)

password_label = ttk.Label(login_frame, text="Пароль:")
password_label.grid(row=1, column=0, sticky=tk.W, padx=10, pady=10)

password_entry = ttk.Entry(login_frame, show="*")
password_entry.grid(row=1, column=1, padx=10, pady=10)

login_button = ttk.Button(login_frame, text="Войти", command=log_in)
login_button.grid(row=2, column=0, columnspan=2, padx=10, pady=10)

register_button = ttk.Button(login_frame, text="Зарегистрироваться", command=register_user)
register_button.grid(row=3, column=0, columnspan=2, padx=10, pady=10)

main_menu = tk.Menu(root)
root.config(menu=main_menu)

file_menu = tk.Menu(main_menu, tearoff=False)
main_menu.add_cascade(label="Файл", menu=file_menu)
file_menu.add_command(label="Экспорт в JSON", command=get_logs)
file_menu.add_separator()
file_menu.add_command(label="Выход", command=quit_application)

options_frame = ttk.LabelFrame(main_frame, text="Фильтры")
options_frame.pack(fill="both", expand=1, padx=10, pady=10)

group_by_ip = tk.IntVar()
group_by_ip_checkbox = ttk.Checkbutton(options_frame, text="Группировать по IP", variable=group_by_ip)
group_by_ip_checkbox.grid(row=0, column=0, sticky=tk.W)

group_by_date = tk.IntVar()
group_by_date_checkbox = ttk.Checkbutton(options_frame, text="Групировать по Дате", variable=group_by_date)
group_by_date_checkbox.grid(row=1, column=0, sticky=tk.W)



start_date_label = ttk.Label(options_frame, text="Начальная дата:")
start_date_label.grid(row=2, column=0, sticky=tk.W, pady=5)

start_date_entry = ttk.Entry(options_frame)
start_date_entry.grid(row=2, column=1, pady=5)

end_date_label = ttk.Label(options_frame, text="Конечная дата:")
end_date_label.grid(row=3, column=0, sticky=tk.W, pady=5)

end_date_entry = ttk.Entry(options_frame)
end_date_entry.grid(row=3, column=1, pady=5)

reset_button = ttk.Button(options_frame, text="Сбросить", command=reset_data)
reset_button.grid(row=4, column=0, pady=10)

search_button = ttk.Button(options_frame, text="Поиск", command=read_data)
search_button.grid(row=4, column=1, pady=10)

get_logs_button = ttk.Button(main_frame, text="Получить логи", command=get_logs)
get_logs_button.pack(pady=10)


sort_label = ttk.Label(options_frame, text="Сортировать по:")
sort_label.grid(pady=10)

sort_choices = ["None", "IP (Asc)", "IP (Des)", "Date (Asc)", "Date (Des)"]
sort_combobox = ttk.Combobox(options_frame, values=sort_choices, state="readonly")
sort_combobox.current(0)
sort_combobox.grid(row=5, column=1, pady=5)

tree_frame = ttk.LabelFrame(main_frame, text="Логи доступа")
tree_frame.pack(fill="both", expand=1, padx=10, pady=10)

tree = ttk.Treeview(tree_frame, columns=("IP", "Date", "Time","FirstLine", "Status", "Size"), show="headings")

tree.column("IP", width=100, anchor=tk.CENTER)
tree.column("Date", width=100, anchor=tk.CENTER)
tree.column("Time", width=100, anchor=tk.CENTER)
tree.column("FirstLine", width=100, anchor=tk.CENTER)
tree.column("Status", width=100, anchor=tk.CENTER)
tree.column("Size", width=100, anchor=tk.CENTER)

tree.heading("IP", text="IP")
tree.heading("Date", text="Date")
tree.heading("Time", text="Time")
tree.heading("FirstLine", text="FirstLine")
tree.heading("Status", text="Status")
tree.heading("Size", text="Size")

tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=1)

scrollbar = ttk.Scrollbar(tree_frame, orient=tk.VERTICAL, command=tree.yview)
scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

tree.configure(yscrollcommand=scrollbar.set)

logout_button = ttk.Button(main_frame, text="Выйти", command=log_out)
logout_button.pack(pady=10)
# Read logs from a file and add them to the database
with open("access_log", "r") as file:
    logs = file.readlines()

    for log in logs:
        insert_access_log(log)


read_data()
root.mainloop()


