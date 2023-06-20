import tkinter as tk
from tkinter import ttk, messagebox
import json
import psycopg2
from config import host, database, user, password
import re
from datetime import datetime
import time
import subprocess

connection = psycopg2.connect(
    host=host,
    database=database,
    user=user,
    password=password
)



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

            insert_query = "INSERT INTO loggi (ip, date, time, first_line_of_request, status, size) VALUES (%s, %s, %s, %s, %s, %s)"
            values = (ip, date, time, first_line, status, size)

            cursor = connection.cursor()
            cursor.execute(insert_query, values)
            connection.commit()
            cursor.close()



def read_data():
    try:
        cursor = connection.cursor()


        group_by = group_by_combobox.get()
        sort_by = sort_by_combobox.get()
        start_date = start_date_entry.get()
        end_date = end_date_entry.get()


        select_query = "SELECT * FROM loggi"

        if start_date and end_date:
            select_query += " WHERE date BETWEEN %s AND %s"
            values = (start_date, end_date)
            cursor.execute(select_query, values)
            data = cursor.fetchall()

            if group_by:
                subquery = "SELECT DISTINCT ON (" + group_by + ") * FROM (SELECT * FROM loggi WHERE date BETWEEN %s AND %s) AS sub"
                subquery += " ORDER BY " + group_by + ", " + sort_by
                cursor.execute(subquery, values)
                data = cursor.fetchall()
        else:
            if group_by:
                select_query += " GROUP BY " + group_by
                if sort_by:
                    select_query += ", " + sort_by
            elif sort_by:
                select_query += " ORDER BY " + sort_by

            cursor.execute(select_query)
            data = cursor.fetchall()


        tree.delete(*tree.get_children())


        for row in data:
            tree.insert("", tk.END, values=row)

        cursor.close()
    except (Exception, psycopg2.Error) as error:
        print("Error reading data from the database:", error)


def reset_data():

    tree.delete(*tree.get_children())


    group_by_combobox.set('')
    sort_by_combobox.set('')
    start_date_entry.delete(0, tk.END)
    end_date_entry.delete(0, tk.END)


def get_logs():
    try:
        cursor = connection.cursor()


        group_by = group_by_combobox.get()
        sort_by = sort_by_combobox.get()
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
                "first_line_of_request": row[3],
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


window = tk.Tk()
window.title("Logs Analysis")
window.geometry("1200x600")


notebook = ttk.Notebook(window)


login_frame = ttk.Frame(notebook)

username_label = ttk.Label(login_frame, text="Username:")
username_label.pack()
username_entry = ttk.Entry(login_frame)
username_entry.pack()

password_label = ttk.Label(login_frame, text="Password:")
password_label.pack()
password_entry = ttk.Entry(login_frame, show="*")
password_entry.pack()

register_button = ttk.Button(login_frame, text="Sign Up", command=register_user)
register_button.pack()

login_button = ttk.Button(login_frame, text="Log In", command=log_in)
login_button.pack()




logs_frame = ttk.Frame(notebook)
logs_frame.state(["disabled"])


start_date_label = ttk.Label(logs_frame, text="Начальная дата (YYYY-MM-DD):")
start_date_label.pack()
start_date_entry = ttk.Entry(logs_frame)
start_date_entry.pack()

end_date_label = ttk.Label(logs_frame, text="Конечная дата (YYYY-MM-DD):")
end_date_label.pack()
end_date_entry = ttk.Entry(logs_frame)
end_date_entry.pack()

group_by_label = ttk.Label(logs_frame, text="Групировать по:")
group_by_label.pack()
group_by_combobox = ttk.Combobox(logs_frame, values=["", "ip", "date", "time", "status", "size"])
group_by_combobox.pack()

sort_by_label = ttk.Label(logs_frame, text="Сортировать по:")
sort_by_label.pack()
sort_by_combobox = ttk.Combobox(logs_frame, values=["", "ip", "date", "time", "status", "size"])
sort_by_combobox.pack()

filter_button = ttk.Button(logs_frame, text="Применить фильтр", command=read_data)
filter_button.pack()

reset_button = ttk.Button(logs_frame, text="Сбросить", command=reset_data)
reset_button.pack()

get_logs_button = ttk.Button(logs_frame, text="Получить логи (JSON)", command=get_logs)
get_logs_button.pack()


schedule_button = ttk.Button(login_frame, text="Запустить по расписанию", command=schedule_program)
get_logs_button.pack()


tree = ttk.Treeview(logs_frame, columns=("IP", "Date", "Time", "First Line", "Status", "Size"), show="headings")

tree.heading("IP", text="IP")
tree.heading("Date", text="Date")
tree.heading("Time", text="Time")
tree.heading("First Line", text="First Line")
tree.heading("Status", text="Status")
tree.heading("Size", text="Size")

tree.pack()



notebook.add(login_frame, text="Sign Up / Log In")
notebook.add(logs_frame, text="Logs")


notebook.tab(1, state="disabled")

notebook.pack(expand=True, fill=tk.BOTH)




window.mainloop()
