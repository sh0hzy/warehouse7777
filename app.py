from flask import Flask, render_template, request, redirect, url_for, send_from_directory
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
import pandas as pd
import os

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///tools.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['UPLOAD_FOLDER'] = 'uploads'  # Папка для хранения файлов
db = SQLAlchemy(app)
migrate = Migrate(app, db)

class Tool(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    number = db.Column(db.Integer, nullable=False)
    name = db.Column(db.String(100), nullable=False)
    abbreviation = db.Column(db.String(50), nullable=True)
    unit = db.Column(db.String(20), nullable=True)
    quantity = db.Column(db.Integer, nullable=False)
    information = db.Column(db.String(200), nullable=True)
    image = db.Column(db.String(100), nullable=True)
    category = db.Column(db.String(100), nullable=False, default='Uncategorized')

class Category(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False, unique=True)

@app.route('/')
def index():
    categories = Category.query.all()

    # Загрузите данные из Excel
    excel_file = 'Warehouse.xlsx'
    df = pd.read_excel(excel_file)

    # Создайте пустую таблицу
    empty_table = pd.DataFrame(columns=df.columns)
    empty_table_html = empty_table.to_html(index=False, escape=False)

    # Разделите таблицу по категориям
    tables_by_category = {}
    for category in categories:
        # Фильтрация данных по категории
        df_filtered = df[df['category'] == category.name]

        # Добавление чекбоксов
        df_filtered['Select'] = df_filtered.index.to_series().apply(
            lambda x: f'<input type="checkbox" name="selected_tool" value="{x}">'
        )

        # Преобразование в HTML
        tables_by_category[category.name] = df_filtered.to_html(index=False, escape=False)

    # Создание общей таблицы без фильтрации по категории
    df['Select'] = df.index.to_series().apply(lambda x: f'<input type="checkbox" name="selected_tool" value="{x}">')
    all_tools_table = df.to_html(index=False, escape=False)

    return render_template('index.html', tables_by_category=tables_by_category, empty_table_html=empty_table_html, all_tools_table=all_tools_table, categories=categories)

@app.route('/move_tools', methods=['POST'])
def move_tools():
    selected_tool_ids = request.form.getlist('selected_tool')
    target_category = request.form.get('target_category')
    
    if selected_tool_ids and target_category:
        # Преобразуйте идентификаторы в числа, если это строки
        selected_tool_ids = [int(x) for x in selected_tool_ids]

        # Загрузите данные из Excel
        df = pd.read_excel('Warehouse.xlsx')

        df.loc[selected_tool_ids, 'category'] = target_category

        # Сохраните измененный файл Excel
        df.to_excel('Warehouse.xlsx', index=False)
    
    return redirect(url_for('index'))

@app.route('/add_category', methods=['POST'])
def add_category():
    new_category_name = request.form['new_category']
    if new_category_name:
        existing_category = Category.query.filter_by(name=new_category_name).first()
        if not existing_category:
            new_category = Category(name=new_category_name)
            db.session.add(new_category)
            db.session.commit()

            df = pd.DataFrame(columns=['Number', 'Name', 'Abbreviation', 'Unit', 'Quantity', 'Information', 'Image', 'Warehouse'])
            df.to_excel(f'uploads/{new_category_name}.xlsx', index=False)

            return redirect(url_for('index'))

    return redirect(url_for('index'))

@app.route('/uploads/<filename>')
def download_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

if __name__ == "__main__":
    if not os.path.exists(app.config['UPLOAD_FOLDER']):
        os.makedirs(app.config['UPLOAD_FOLDER'])
    app.run(debug=True)