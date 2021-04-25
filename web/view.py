# This code is wrote by Prasanna.N on apr 24...
# importing flask framework
from flask import Blueprint, render_template, request, flash,redirect,url_for,session,send_file
from werkzeug.utils import secure_filename # for files uploading
import os # to delete files after the user left
import pandas as pd # to open uploaded xlsx or csv files
import glob # to delete files after the user left
from sklearn.ensemble import RandomForestClassifier # For machine learning
from sklearn.preprocessing import LabelEncoder # For converting text to numbers
from sklearn.model_selection import train_test_split
import math
import json # for interaction between js and flask
import time


date_former = [] # date array for uploading files(Select file)
meal_column_data = [] # meal array for uploading files(Select file)
food_column_data = [] # food array for uploading files(Select file)

view = Blueprint('view',__name__) # adding blueprint

# home root
@view.route('/')
def home():    
    files = glob.glob('web/temp/*')# deleting files in temp folder
    for f in files:
        os.remove(f)
    return render_template('home.html')

# more html for help
@view.route('/more')
def more():
    return render_template('more.html')

# file selector for selecting files
@view.route('/file_selector', methods=['POST','GET'])
def file_selector():
    try:
        if request.method == 'POST':
            
            date_former = [] # date array for uploading files(Select file)
            meal_column_data = [] # meal array for uploading files(Select file)
            food_column_data = [] # food array for uploading files(Select file)

            session['date_former'] = date_former # sending blank array data to javascript
            session['meal_column_data'] = meal_column_data # sending data blank array to javascript
            session['food_column_data'] = food_column_data # sending data blank array to javascript

            training_file = request.files["training_data"]# loading file from html
            trainingpath = os.path.dirname(__file__)
            training_file_path = os.path.join(trainingpath, "temp", secure_filename(training_file.filename))
            training_file.save(training_file_path)

            name, extension = os.path.splitext(training_file_path)# checking extenstion and name
            if extension == '.csv':# for csv extension
                df = pd.read_csv(training_file_path)# reading csv

                meal_column_data = df.loc[:,'Time'].values.tolist()# Transferring data from csv to array
                day_column_data = df.loc[:,'Day'].values
                year_column_data = df.loc[:,'Year'].values
                food_column_data = df.loc[:,'Food'].values.tolist()
                month_column_data = df.loc[:,'Month'].values

                for no,i in enumerate(day_column_data):# transferring day,month,year to date
                    form = str(i) + '-' + str(month_column_data[no]) +'-'+ str(year_column_data[no])
                    date_former.append(form)
                date_former = date_former

                # Sending this data to render in html page
                session['date_former'] = date_former# sending loaded array data to javascript
                session['meal_column_data'] = meal_column_data# sending loaded blank array to javascript
                session['food_column_data'] = food_column_data# sending loaded blank array to javascript
                
                return redirect(url_for('view.home'))
                # sending all datas to html for fun
                
            elif extension == '.xlsx':# for xlsx extension
                df = pd.read_excel(training_file_path) # reading csv
                meal_column_data = df.loc[:,'Time'].values.tolist()# Transferring data from csv to array
                day_column_data = df.loc[:,'Day'].values
                year_column_data = df.loc[:,'Year'].values
                food_column_data = df.loc[:,'Food'].values.tolist()
                month_column_data = df.loc[:,'Month'].values
                for no,i in enumerate(day_column_data):# transferring day,month,year to date
                    form = str(i) + '-' + str(month_column_data[no]) +'-'+ str(year_column_data[no])
                    date_former.append(form)
                date_former = date_former.tolist()
                # Sending this data to render in html page
                session['date_former'] = date_former# sending loaded array data to javascript
                session['meal_column_data'] = meal_column_data# sending loaded blank array to javascript
                session['food_column_data'] = food_column_data# sending loaded blank array to javascript
                
                return redirect(url_for('view.home'))
        else:   # sending all datas to html for fun
            
            return redirect(url_for('view.home'))
    except:
        
        flash('Check your file there are some errors click more for reference!!!', category='error')# showing errors if any error happens
        return redirect(url_for('view.home'))

# this is the main core which predicts using machine learning to output the data
@view.route('/dataprocessor', methods= ['POST','GET'])
def dataprocessor():
    try:
        if request.method == 'POST':

            meal_arr1 = []
            arr = []
            arr1 = []
            day_arr = []# for getting days from step1.
            month_arr = []# for getting month from step1.
            year_arr = []# for getting year from step1.

            meal = request.form['meals']# from step2 meals
            dates = request.form['date']# from step2 date picker

            day = dates.split('-')# date --> day, month, year splitter
            month = day[1]
            year = day[2]
            day = day[0]
            meal = meal.lower()
            if meal == 'lunch':
                    meal = 1
            elif meal == 'breakfast':
                    meal = 0
            elif meal == 'dinner':
                    meal = 2
            
            # Loading all data from js
            date_arr = session['date_c']
            date_arr = json.loads(date_arr)   
            meal_arr = session['meal_c']
            meal_arr = json.loads(meal_arr)        
            food_arr = session['food_c']
            food_arr = json.loads(food_arr)
            

            for i in date_arr:# date_arr --> day_arr, month_arr, year_arr splitter
                i = i.split('-')
                day_arr.append(i[0])
                month_arr.append(i[1])
                year_arr.append(i[2]) 
            for r in meal_arr:# text to number for meal_arr
                if r == 'lunch':
                    r = 1
                elif r == 'breakfast':
                    r = 0
                elif r == 'dinner':
                    r = 2
                meal_arr1.append(r)
            meal_arr = meal_arr1
           
            df_arr = {# making a  dataframe with all arrays 
                'Day':day_arr,
                'Month':month_arr,
                'Year':year_arr,
                'Time':meal_arr,
                'Food':food_arr
            }
            
            df = pd.DataFrame(data=df_arr)
            encode = LabelEncoder()# encoder for food
            encode.fit(df['Food'])
            df['food'] = encode.fit_transform(df['Food'])
            df1 = df.drop(['Food', 'food'], axis=1)
            target = df['food']  
            model = RandomForestClassifier()# model
            model.fit(df1[['Day', 'Month', 'Year', 'Time']], target)# training
            value = model.predict([[day,month,year,meal]])
            score = model.score(df1[['Day', 'Month', 'Year', 'Time']], target)
            files = glob.glob('web/temp/*')
            for f in files:
                os.remove(f)
            for ele in df['Food']:
                arr.append(ele)# appending names
            for e in df['food']:
                arr1.append(e)# appending encoded integers
            for items in arr1:
                if value[0] == items:   
                    pos = arr1.index(items)
                    session['result'] = arr[pos]# sending to js
            return redirect(url_for('view.home')) 
        else:
            return redirect(url_for('view.home'))
    except Exception as e:
        flash(f'Some error occured{e}!!!', category='error')
        return redirect(url_for('view.home'))  

# sending result
@view.route('/result')
def res():
    try:
        resul = session['result']
        return json.dumps(resul)
    except:
        pass

# sending dates after file selection
@view.route('/dates')
def date():
    try:
        date_former = session['date_former']
        return json.dumps(date_former)
    except:
        pass

# sending food after file selection
@view.route('/food')
def food():
    try:
        food_column_data = session['food_column_data']
        return json.dumps(food_column_data)
    except:
        pass

# sending meal after file selection
@view.route('/meal')
def meal():
    try:
        meal_column_data = session['meal_column_data']
        return json.dumps(meal_column_data)
    except:
        pass

# getting data from js
@view.route('/datas', methods = ['POST'])
def datas():
    date_c = request.form['date_c']
    food_c = request.form['food_c']
    meal_c = request.form['meal_c']
    session['date_c'] =date_c
    session['food_c'] =food_c
    session['meal_c'] =meal_c
    return date_c,food_c,meal_c
