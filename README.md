# Isoko Info v0.1 

IsokoInfo is a simple web application that is built using Flask. It gives buyers who want to buy agricultural products price information and help them compare different products from different sellers. Sellers can add, view, update, and delete their products and they can also get reviews from buyers using review codes. This is the first prototype for the project.

## Live Demo

This web application is deployed on Render: https://isoko-info-v0-1.onrender.com/

---

## Features

- User registration & login (for sellers)
- Add, update, and delete products
- Upload product images via Cloudinary
- Store product & market data in MySQL which is hosted on Aiven
- Admin dashboard (if implemented)
- Responsive front-end using HTML/CSS

---

## Used Technologies

- Python 3.11
- Flask
- Flask-SQLAlchemy
- Aiven, MySQL (through `mysql-connector-python`)
- Cloudinary (for image hosting)
- Gunicorn (for production WSGI server)
- Render (for deployment)

---

## Local Setup Instructions

Follow theses steps **carefully** to run this project locally

### 1. Clone the repository

Open terminal(bash, cmd, powershell)
git clone https://github.com/your-username/isoko_info_v0.1.git,
cd isoko_info_v0.1

### 2. Install Python

Make sure you have Python 3.10+ installed. If not check out https://www.python.org/ there are instructions for different operating systems.

You can check your if Python if installed with opening the terminal and typing the command:
python --version

### 3. Install Dependencies

Open your bash or command prompt terminal and type:
pip install -r requirements.txt

### 4. Configure Environmental Variables

Make a .env file in the root directory and then fill it up with this content

SECRET_KEY='your_app_secret_key'
DATABASE_URL=mysql+mysqlconnector://'avnadmin':'password'@'hostname'/'database_name'?charset=utf8mb4

CLOUDINARY_CLOUD_NAME='your_cloudinary_name'
CLOUDINARY_API_KEY='your_cloudinary_api_key'
CLOUDINARY_API_SECRET='your_app_secret_key'

You need to actually register on Aiven to get a database and it's connection information that you need to replace in the placeholding values above.

You also need to register on Cloudinary to get all the connection information you need to actually upload the images that are going to be needed when running this web application and replace them with the placeholding values.

## Deployment on Render

### 1. Pushing your code to GitHub

Make sure all your latest code is pushed to GitHub

### 2. Render Deploying

- Go to Render (www.render.com)
- Create an account
- Click on "New Web Service"
- Connect your Github repository for this project

### 3. Configuring the Render Deployment Service

- Build Command: `pip install -r requirements.txt`
- Start Command: `gunicorn app:app`
- Environment: `Python`
- Root Directory: Leave this empty if your app.py file is inside the folder
- Environmental Variables: Here you will put in your environmental variables that are in your .env file, just copy and paste. Make sure you set the values well as in your .env file.

### 4. Save & Deploy

You will have to wait for the process of building and deploying to finish. When it's finished, Render will give you a URL wher you can access your deployed web app.

---

## Testing functionality

- Make sure that the database is working with tools like MySQL Workbench
- Make sure that cloudinary is working
- Make sure that the values in environment variables on Render for the deployed app
- Don't forget to check all the depencies the requirements
- Make sure that all app routes are functional

## Author

**Credo Desparvis Gutabarwa**,
Github: https://github.com/desparvis

