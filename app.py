from flask import Flask, request, render_template_string, send_from_directory
from homeharvest import scrape_property
from datetime import datetime
import pandas as pd

app = Flask(__name__)

# HTML form template including all parameters and added CSS for styling
HTML_FORM = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>Property Details</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            margin: 0;
            padding: 0;
            background-color: #f4f4f4;
        }
        .container {
            max-width: 600px;
            margin: 20px auto;
            padding: 20px;
            background-color: #fff;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }
        h2 {
            color: #333;
        }
        form {
            display: flex;
            flex-direction: column;
        }
        .form-group {
            margin-bottom: 15px;
        }
        label {
            margin-bottom: 5px;
            font-weight: bold;
        }
        input[type=text], input[type=number], select {
            padding: 10px;
            margin-bottom: 10px;
            border-radius: 4px;
            border: 1px solid #ddd;
            width: 100%;
        }
        input[type=checkbox] {
            margin-right: 10px;
        }
        input[type=submit] {
            background-color: #04AA6D;
            color: white;
            padding: 10px;
            border: none;
            border-radius: 4px;
            cursor: pointer;
            font-size: 16px;
        }
        input[type=submit]:hover {
            background-color: #037f58;
        }
    </style>
</head>
<body>
    <div class="container">
        <h2>Enter Property Details</h2>
        <form action="/results" method="post">
            <div class="form-group">
                <label for="location">Location</label>
                <input type="text" id="location" name="location" placeholder="Enter location" required>
            </div>
            <div class="form-group">
                <label for="listing_type">Listing Type</label>
                <select id="listing_type" name="listing_type">
                    <option value="for_sale">For Sale</option>
                    <option value="for_rent">For Rent</option>
                    <option value="sold">Sold</option>
                </select>
            </div>
            <div class="form-group">
                <label for="radius">Radius (miles)</label>
                <input type="number" id="radius" name="radius" placeholder="Enter radius (miles)" step="0.01">
            </div>
            <div class="form-group">
                <label>
                    <input type="checkbox" name="mls_only" value="true"> MLS Only
                </label>
            </div>
            <div class="form-group">
                <label for="past_days">Past Days</label>
                <input type="number" id="past_days" name="past_days" placeholder="Enter number of past days">
            </div>
            <div class="form-group">
                <label for="date_from">Date From (YYYY-MM-DD)</label>
                <input type="text" id="date_from" name="date_from" placeholder="Enter start date (YYYY-MM-DD)">
            </div>
            <div class="form-group">
                <label for="date_to">Date To (YYYY-MM-DD)</label>
                <input type="text" id="date_to" name="date_to" placeholder="Enter end date (YYYY-MM-DD)">
            </div>
            <div class="form-group">
                <label>
                    <input type="checkbox" name="foreclosure" value="true"> Foreclosure
                </label>
            </div>
            <div class="form-group">
                <input type="submit" value="Show Results">
            </div>
        </form>
    </div>
</body>
</html>

"""

# Route for displaying results
@app.route('/results', methods=['POST'])
def results():
    data = request.form
    location = data.get('location', '')
    listing_type = data.get('listing_type', 'for_sale')
    radius = float(data.get('radius', 0)) if data.get('radius') else None
    mls_only = 'mls_only' in data
    past_days = int(data.get('past_days')) if data.get('past_days') else None
    date_from = data.get('date_from', None)
    date_to = data.get('date_to', None)
    foreclosure = 'foreclosure' in data
    proxy = data.get('proxy', None)

    properties = scrape_property(
        location=location,
        listing_type=listing_type,
        radius=radius,
        mls_only=mls_only,
        past_days=past_days,
        date_from=date_from,
        date_to=date_to,
        foreclosure=foreclosure,
        proxy=proxy,
    )

    properties = properties.iloc[:, :-1]  # Select all rows, and all columns except the last

    properties_html = properties.to_html(classes='data', header="true")

    # Generate a unique filename for the CSV
    timestamp = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
    filename = f"property_results_{timestamp}.csv"
    properties.to_csv(f"static/{filename}", index=False)  # Save the CSV in the 'static' folder

    # Include a download link in the rendered HTML
    download_link = f'<a href="/download/{filename}">Download CSV</a>'

    return render_template_string("""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <title>Results</title>
        <style>
            .data {
                border-collapse: collapse;
                width: 100%;
            }
            .data td, .data th {
                border: 1px solid #ddd;
                padding: 8px;
            }
            .data tr:nth-child(even){background-color: #f2f2f2;}
            .data tr:hover {background-color: #ddd;}
            .data th {
                padding-top: 12px;
                padding-bottom: 12px;
                text-align: left;
                background-color: #04AA6D;
                color: white;
            }
        </style>
    </head>
    <body>
        <h2>Property Results</h2>
        {{ download_link|safe }}
        {{ properties_html|safe }}
    </body>
    </html>
    """, properties_html=properties_html, download_link=download_link)

@app.route('/download/<filename>')
def download(filename):
    directory = "./static"
    return send_from_directory(directory, filename, as_attachment=True)

@app.route('/')
def index():
    return render_template_string(HTML_FORM)
