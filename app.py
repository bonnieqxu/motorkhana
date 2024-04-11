from flask import Flask
from flask import render_template
from flask import request
from flask import redirect
from flask import url_for
import re
from datetime import datetime, date
import mysql.connector
from mysql.connector import FieldType
import connect

app = Flask(__name__)


dbconn = None
connection = None

def getCursor():
    global dbconn
    global connection
    connection = mysql.connector.connect(user=connect.dbuser, \
    password=connect.dbpass, host=connect.dbhost, \
    database=connect.dbname, autocommit=True)
    dbconn = connection.cursor()
    return dbconn




# --------------------THIS IS WHERE PUBLIC INTERFACE BEGINS --------------------

###################### HOME PAGE #########################
@app.route("/")
def home():
    # Render the "base.html" template when the root URL is accessed
    return render_template("base.html")
#---------------------------------------------------------




###################### LIST OF COURSES ####################
@app.route("/listcourses")
def listcourses():
    # Get a database cursor using the 'getCursor' function
    connection = getCursor()

    # Execute an SQL query to retrieve all records from the 'course' table
    connection.execute("SELECT * FROM course;")

    # Fetch the results of the SQL query and store them in the 'courseList' variable
    courseList = connection.fetchall()

    # Render the "courselist.html" template, passing the 'courseList' to it as 'course_list'
    return render_template("courselist.html", course_list = courseList)
#-------------------------------------------------------------




##################### LIST OF DRIVERS #####################
@app.route("/listdrivers")
def listdrivers():
    # Get connection, execute the query and fetch results
    connection = getCursor()

    connection.execute("""SELECT 
                        d.driver_id,
                        CONCAT(d.first_name,' ', d.surname) AS DriverName,          -- Driver's full name in first name, surname order
                        d.date_of_birth,
                        d.age,
                        CONCAT(c.first_name, ' ', c.surname) AS CaregiverName,       -- Caregiver's full name
                        ca.model,
                        ca.drive_class
                        FROM driver as d
                        INNER JOIN car as ca on d.car = ca.car_num
                        LEFT JOIN driver AS c ON d.caregiver = c.driver_id           -- Get caregiver's name
                        ORDER BY d.surname, d.first_name;""")                        # sorting by surname then first name
    
    # results stored in driverList
    driverList = connection.fetchall()

    # Render the "driverlist.html" template, passing the 'driverList' to it as 'driver_list'
    return render_template("driverlist.html", driver_list = driverList)   
#------------------------------------------------------------------------



################### DRIVER'S RUN DETAILS ####################
# Route to display a dropdown list of driver names
@app.route("/namedropdown")
def namedropdown():
    # Get a database connection， execute query, fetch data and render template
    connection = getCursor()   
    connection.execute("SELECT first_name, surname, driver_id FROM driver;")
    nameList = connection.fetchall()
    return render_template("namedropdown.html", name_list=nameList)

# Route to show the run details for the selected driver
@app.route("/namedropdown/driversrundetails", methods=['GET'])
def driversrundetails(): 
    # Get the selected driver's name from the request
    selected_driver = request.args.get('driver_name')
    connection = getCursor()

    # Prepare and execute SQL query to retrieve run details for the selected driver
    entry = selected_driver

    # sql = """SELECT * FROM(                                               -- Subquery to retrieve run details for a specific driver
    #             SELECT 
    #                 d.driver_id as DriverID, 
    #                 d.first_name as FirstName,
    #                 d.surname as Surname,
    #                 co.name as CourseName,
    #                 ca.drive_class as DriveClass,
    #                 ca.model as CarModel,
    #                 SUM(r.seconds + IFNULL(r.cones, 0) * 5 + IFNULL(r.wd, 0) * 10) AS RunTotals             -- Calculating RunTotals
    #             FROM driver as d
    #             INNER JOIN run as r on d.driver_id = r.dr_id
    #             INNER JOIN course as co on co.course_id = r.crs_id
    #             INNER JOIN car as ca on ca.car_num = d.car
    #             where d.driver_id = %s
    #             GROUP BY d.driver_id, d.first_name, d.surname, co.name, ca.drive_class, ca.model, co.course_id, r.run_num
    #             ORDER BY d.driver_id
    #             ) AS subquery;
    #             """

    sql = '''SELECT * FROM(                                               -- Subquery to retrieve run details for a specific driver
                SELECT 
                    d.driver_id as DriverID, 
                    d.first_name as FirstName,
                    d.surname as Surname,
					ca.model as CarModel,
					ca.drive_class as DriveClass,
                    co.name as CourseName,
                    r.run_num,
                    r.seconds,
                    r.cones,
                    r.wd,
                    SUM(r.seconds + IFNULL(r.cones, 0) * 5 + IFNULL(r.wd, 0) * 10) AS RunTotals             -- Calculating RunTotals
                FROM driver as d
                INNER JOIN run as r on d.driver_id = r.dr_id
                INNER JOIN course as co on co.course_id = r.crs_id
                INNER JOIN car as ca on ca.car_num = d.car
                where d.driver_id = %s
                GROUP BY d.driver_id, d.first_name, d.surname, co.name, ca.drive_class, ca.model, co.course_id, r.run_num
                ORDER BY d.driver_id
                ) AS subquery;
            '''
    
    
    parameters = (entry,)
    connection.execute(sql,parameters)   
    run_details = connection.fetchall()
   
    # limiting results to 2 decimal points
    rundetailList = []
    for item in run_details:
        driver_id, first_name, surname, car_model, drive_class, course_name, run_num, seconds, cones, wd, run_totals = item    
        if run_totals is not None:
            try:
                run_totals = round(float(run_totals), 2) 
            except ValueError:
                pass  

        driver_info = {
            "driver_id": driver_id,
            "first_name": first_name,
            "surname": surname,
            "car_model": car_model,
            "drive_class": drive_class
        }


        formatted_item = (driver_id, first_name, surname, car_model, drive_class, course_name, run_num, seconds, cones, wd, run_totals)
        rundetailList.append(formatted_item)

    # render template
    return render_template("driversrundetails.html", driver_info=driver_info, rundetail_list=rundetailList)
#-------------------------------------------------------------------------------------




##################### OVERALL RESULTS #####################
@app.route("/overallresults")
def overallresults():
    connection = getCursor()
    
    # This query calculates 6 course results and overall results for drivers
    connection.execute("""
                SELECT
                    subquery.*,
                    CASE
                       -- If any of the 6 course results is 'dnf', set OverallResult to 'NQ'
                        WHEN 'dnf' IN (courseA, courseB, courseC, courseD, courseE, courseF) THEN 'NQ'
                       
                       -- Otherwise, sum up the times for each course and assign the total to OverallResult
                        ELSE COALESCE(courseA, 0) + COALESCE(courseB, 0) + COALESCE(courseC, 0) + COALESCE(courseD, 0) + COALESCE(courseE, 0) + COALESCE(courseF, 0)
                    END AS OverallResult
                FROM (
                       -- subquery retrieves each driver's results in each course.
                    SELECT
                        d.driver_id AS DriverID,
                        CONCAT(d.first_name, ' ', d.surname) AS driverName,
                        d.age AS age,
                        c.model AS CarModel,
                       
                       -- For each course, calculate the best time among all runs or set to 'dnf' if no time recorded
                        COALESCE(MIN(CASE WHEN r.crs_id = 'A' THEN r.seconds + IFNULL(r.cones, 0) * 5 + IFNULL(r.wd, 0) * 10 END), MAX(CASE WHEN r.crs_id = 'A' THEN r.seconds + IFNULL(r.cones, 0) * 5 + IFNULL(r.wd, 0) * 10 END), 'dnf') AS courseA,
                        COALESCE(MIN(CASE WHEN r.crs_id = 'B' THEN r.seconds + IFNULL(r.cones, 0) * 5 + IFNULL(r.wd, 0) * 10 END), MAX(CASE WHEN r.crs_id = 'B' THEN r.seconds + IFNULL(r.cones, 0) * 5 + IFNULL(r.wd, 0) * 10 END), 'dnf') AS courseB,
                        COALESCE(MIN(CASE WHEN r.crs_id = 'C' THEN r.seconds + IFNULL(r.cones, 0) * 5 + IFNULL(r.wd, 0) * 10 END), MAX(CASE WHEN r.crs_id = 'C' THEN r.seconds + IFNULL(r.cones, 0) * 5 + IFNULL(r.wd, 0) * 10 END), 'dnf') AS courseC,
                        COALESCE(MIN(CASE WHEN r.crs_id = 'D' THEN r.seconds + IFNULL(r.cones, 0) * 5 + IFNULL(r.wd, 0) * 10 END), MAX(CASE WHEN r.crs_id = 'D' THEN r.seconds + IFNULL(r.cones, 0) * 5 + IFNULL(r.wd, 0) * 10 END), 'dnf') AS courseD,
                        COALESCE(MIN(CASE WHEN r.crs_id = 'E' THEN r.seconds + IFNULL(r.cones, 0) * 5 + IFNULL(r.wd, 0) * 10 END), MAX(CASE WHEN r.crs_id = 'E' THEN r.seconds + IFNULL(r.cones, 0) * 5 + IFNULL(r.wd, 0) * 10 END), 'dnf') AS courseE,
                        COALESCE(MIN(CASE WHEN r.crs_id = 'F' THEN r.seconds + IFNULL(r.cones, 0) * 5 + IFNULL(r.wd, 0) * 10 END), MAX(CASE WHEN r.crs_id = 'F' THEN r.seconds + IFNULL(r.cones, 0) * 5 + IFNULL(r.wd, 0) * 10 END), 'dnf') AS courseF
                    FROM driver AS d
                    INNER JOIN car AS c ON d.car = c.car_num
                    LEFT JOIN run AS r ON d.driver_id = r.dr_id
                    GROUP BY d.driver_id, driverName, age, CarModel
                    ) AS subquery
                    
                    -- Order the results by OverallResult with 'NQ' drivers at the end
                    ORDER BY CASE
                    WHEN OverallResult = 'NQ' THEN 1
                    ELSE 0
                    END, 
                    OverallResult,
                    DriverID;                
                    """)

    overall_info = connection.fetchall()

    # adding "(J)" next to juior drivers' names
    result_junior_update = []
    for result in overall_info:
        driver_name = result[1]
        age = result[2]

        if age is not None and 12 <= age <= 25:
            driver_name = driver_name + "(J)"
        result_junior_update.append((result[0], driver_name, age, result[3], result[4], result[5], result[6], result[7], result[8], result[9], result[10]))

    # limiting results to 2 decimal points
    formatted_results = []
    for item in result_junior_update:
        driver_id, driver_name, age, car_model, course_a, course_b, course_c, course_d, course_e, course_f, overall_result = item        
        try:
            course_a = round(float(course_a), 2)  
            course_b = round(float(course_b), 2)  
            course_c = round(float(course_c), 2)  
            course_d = round(float(course_d), 2)  
            course_e = round(float(course_e), 2)  
            course_f = round(float(course_f), 2)  
            overall_result = round(float(overall_result), 2)  
        except ValueError:
            pass  

        formatted_item = (
            driver_id,
            driver_name,
            age,
            car_model,
            course_a,
            course_b,
            course_c,
            course_d,
            course_e,
            course_f,
            overall_result
        )
        formatted_results.append(formatted_item)

    # adding ranking symbols
    overallList = []
    for result in formatted_results:
        driver_id, driver_name, age, car_model, course_a, course_b, course_c, course_d, course_e, course_f, overall_result = result    
        rank = ""
  
        if formatted_results.index(result) == 0:
            rank = "🏆"
        elif 1 <= formatted_results.index(result) <= 4:
            rank = "🎁"
        overallList.append((driver_id, driver_name, age, car_model, course_a, course_b, course_c, course_d, course_e, course_f, overall_result, rank))

    # Render template
    return render_template("overallresults.html", overall_list = overallList)
#----------------------------------------------------------------------------------



####################### BAR GRAPH ###################
@app.route("/graph")
def showgraph():
    # Establish a database connection
    connection = getCursor()

    # Execute SQL query to retrieve the top five drivers and their overall results
    connection.execute("""
            SELECT
                CONCAT(DriverID, ' ', driverName) AS BestDrivers,            -- Combine driver's ID and name for display
                CASE
                    WHEN OverallResult = 'NQ' THEN 'NQ'                     -- If any course was 'dnf', mark overall result as 'NQ'
                    ELSE CAST(OverallResult AS CHAR)                        -- Otherwise cast the overall result to a character
                END AS overall_result
            FROM (
                -- Subquery to calculate the overall result for each driver
                SELECT
                    subquery.DriverID,
                    subquery.driverName,
                    CASE
                       -- If any course was 'dnf' for a driver, mark their overall result as 'NQ'
                        WHEN 'dnf' IN (subquery.courseA, subquery.courseB, subquery.courseC, subquery.courseD, subquery.courseE, subquery.courseF) THEN 'NQ' 
                       
                       -- Calculate overall result by summing the best times from each course
                        ELSE CAST(subquery.courseA + subquery.courseB + subquery.courseC + subquery.courseD + subquery.courseE + subquery.courseF AS CHAR)
                      
                    END AS OverallResult
                FROM (
                    -- Subquery to retrieve each driver's runs in all 6 courses
                    SELECT
                        d.driver_id AS DriverID,
                        CONCAT(d.first_name, ' ', d.surname) AS driverName,
                        d.age AS age,
                        c.model AS CarModel,
                       
                       -- For each course, find the best time among all runs or mark 'dnf' if there's no result recorded
                       -- Course A
                        COALESCE(
                            LEAST(
                                MIN(CASE WHEN r.crs_id = 'A' THEN r.seconds + IFNULL(r.cones, 0) * 5 + IFNULL(r.wd, 0) * 10 ELSE NULL END),
                                MAX(CASE WHEN r.crs_id = 'A' THEN r.seconds + IFNULL(r.cones, 0) * 5 + IFNULL(r.wd, 0) * 10 ELSE NULL END)
                            ),
                            'dnf'
                        ) AS courseA,
                       
                       -- Course B
                        COALESCE(
                            LEAST(
                                MIN(CASE WHEN r.crs_id = 'B' THEN r.seconds + IFNULL(r.cones, 0) * 5 + IFNULL(r.wd, 0) * 10 ELSE NULL END),
                                MAX(CASE WHEN r.crs_id = 'B' THEN r.seconds + IFNULL(r.cones, 0) * 5 + IFNULL(r.wd, 0) * 10 ELSE NULL END)
                            ),
                            'dnf'
                        ) AS courseB,
                       
                       -- Course C
                        COALESCE(
                            LEAST(
                                MIN(CASE WHEN r.crs_id = 'C' THEN r.seconds + IFNULL(r.cones, 0) * 5 + IFNULL(r.wd, 0) * 10 ELSE NULL END),
                                MAX(CASE WHEN r.crs_id = 'C' THEN r.seconds + IFNULL(r.cones, 0) * 5 + IFNULL(r.wd, 0) * 10 ELSE NULL END)
                            ),
                            'dnf'
                        ) AS courseC,
                       
                       -- Course D
                        COALESCE(
                            LEAST(
                                MIN(CASE WHEN r.crs_id = 'D' THEN r.seconds + IFNULL(r.cones, 0) * 5 + IFNULL(r.wd, 0) * 10 ELSE NULL END),
                                MAX(CASE WHEN r.crs_id = 'D' THEN r.seconds + IFNULL(r.cones, 0) * 5 + IFNULL(r.wd, 0) * 10 ELSE NULL END)
                            ),
                            'dnf'
                        ) AS courseD,
                       
                       -- Course E
                        COALESCE(
                            LEAST(
                                MIN(CASE WHEN r.crs_id = 'E' THEN r.seconds + IFNULL(r.cones, 0) * 5 + IFNULL(r.wd, 0) * 10 ELSE NULL END),
                                MAX(CASE WHEN r.crs_id = 'E' THEN r.seconds + IFNULL(r.cones, 0) * 5 + IFNULL(r.wd, 0) * 10 ELSE NULL END)
                            ),
                            'dnf'
                        ) AS courseE,
                       
                       -- Course F
                        COALESCE(
                            LEAST(
                                MIN(CASE WHEN r.crs_id = 'F' THEN r.seconds + IFNULL(r.cones, 0) * 5 + IFNULL(r.wd, 0) * 10 ELSE NULL END),
                                MAX(CASE WHEN r.crs_id = 'F' THEN r.seconds + IFNULL(r.cones, 0) * 5 + IFNULL(r.wd, 0) * 10 ELSE NULL END)
                            ),
                            'dnf'
                        ) AS courseF
                    FROM driver AS d
                    INNER JOIN car AS c ON d.car = c.car_num
                    LEFT JOIN run AS r ON d.driver_id = r.dr_id
                    GROUP BY d.driver_id, driverName, age, CarModel
                ) AS subquery
            ) AS top_five_drivers
            
            -- Order the results by the overall result and limit to the top five.
            ORDER BY 
                CASE
                    WHEN OverallResult = 'NQ' THEN 1
                    ELSE 0
                END, 
                OverallResult
            LIMIT 5;""")
    
    # Fetch the results of the query
    nameList = connection.fetchall()
    
    bestDriverList = []
    rawresultsList = []

    # Extract driver names and their corresponding results
    for row in nameList:
        bestDriver, result = row
        bestDriverList.append(bestDriver)
        rawresultsList.append(result)

    # limiting results to 2 decimal places
    resultsList = []
    for item in rawresultsList:
        result = round(float(item), 2) 
        resultsList.append(result)

    # render template
    return render_template("top5graph.html", name_list = bestDriverList, value_list = resultsList)
#---------------------------------------------------------------------------------
# 
# 
# 
# 
# 
#  
#--------------------THIS IS WHERE PUBLIC INTERFACE FINISHES --------------------
##################################################################################
##################################################################################
##################################################################################
##################################################################################
##################################################################################
##################################################################################
##################################################################################
#--------------------THIS IS WHERE ADMIN INTERFACE BEGINS ------------------------
#
#
#
#
#
#
#
################ ADMIN HOME ##################
# Route for the admin interface accessible via GET and POST requests.
@app.route("/admin", methods=['GET', 'POST'])
def admin():
    # Render the "admin.html" template when users access /admin
    return render_template("admin.html")
#----------------------------------------------







############## JUNIOR DRIVER LIST ##############
@app.route("/admin/juniorlist")
def juniorlist():
    connection = getCursor()
    
    # SQL query to select junior drivers aged 12 to 25 and their caregivers if any

    connection.execute('''
                SELECT 
                    d1.driver_id,
                    d1.first_name AS driver_first_name,
                    d1.surname AS driver_surname,
                    d1.date_of_birth AS driver_date_of_birth,
                    d1.age AS driver_age,
                    -- Combining caregiver's first name and surname
                    CONCAT(d2.first_name, ' ', d2.surname) AS caregiver_name
                FROM driver d1
                -- Left join to get caregiver's names
                LEFT JOIN driver d2 ON d1.caregiver = d2.driver_id
                -- Filtering drivers aged between 12 and 25
                WHERE d1.age >= 12 AND d1.age <= 25
                -- Sorting results by age in descending order and then by surname
                ORDER BY d1.age DESC, d1.surname;''')

    juniorList = connection.fetchall()

    # Render template
    return render_template("juniorlist.html", junior_list = juniorList)
#-----------------------------------------------------------------



############### DRIVER SEARCH #################
@app.route("/admin/driversearch", methods=['GET', 'POST'])
def driversearch():
    # Get a database connection
    connection = getCursor()
    
    if request.method == 'POST':
        # If a POST request is received, retrieve the 'search_term' from the submitted form
        search_term = request.form['search_term']

        # Split the search term into 'first_name' and 'surname' if a space is present
        if ' ' in search_term:
            first_name, surname = search_term.split(' ', 1)
        else:
            first_name = search_term
            surname = search_term

        # Define the SQL query to search for drivers       
        sql = '''
            SELECT
            -- Select columns for the driver search results
                subquery.DriverID,
                d.first_name,
                d.surname,
                d.date_of_birth,
                subquery.age,
                CONCAT(caregiver.first_name, ' ', caregiver.surname) as caregiver,
                d.car AS car_num,
                subquery.CarModel as model,
                c.drive_class,
                IF(subquery.courseA = 'dnf', 'dnf', ROUND(subquery.courseA, 2)) AS courseA,
                IF(subquery.courseB = 'dnf', 'dnf', ROUND(subquery.courseB, 2)) AS courseB,
                IF(subquery.courseC = 'dnf', 'dnf', ROUND(subquery.courseC, 2)) AS courseC,
                IF(subquery.courseD = 'dnf', 'dnf', ROUND(subquery.courseD, 2)) AS courseD,
                IF(subquery.courseE = 'dnf', 'dnf', ROUND(subquery.courseE, 2)) AS courseE,
                IF(subquery.courseF = 'dnf', 'dnf', ROUND(subquery.courseF, 2)) AS courseF,

                -- Calculate the OverallResult, show 'NQ' if any 'dnf'
                CASE
                    WHEN 'dnf' IN (courseA, courseB, courseC, courseD, courseE, courseF) THEN 'NQ'
                    ELSE   ROUND(COALESCE(courseA, 0) + COALESCE(courseB, 0) + COALESCE(courseC, 0) + COALESCE(courseD, 0) + COALESCE(courseE, 0) + COALESCE(courseF, 0), 2)
                END AS OverallResult
            FROM (
                -- Subquery to calculate driver course time, and retrieve other info
                SELECT
                    d.driver_id AS DriverID,
                    CONCAT(d.first_name, ' ', d.surname) AS driverName,
                    d.age AS age,
                    c.model AS CarModel,

                    -- Calculate the best time for each course, or 'dnf' if not completed
                    COALESCE(MIN(CASE WHEN r.crs_id = 'A' THEN r.seconds + IFNULL(r.cones, 0) * 5 + IFNULL(r.wd, 0) * 10 END), MAX(CASE WHEN r.crs_id = 'A' THEN r.seconds + IFNULL(r.cones, 0) * 5 + IFNULL(r.wd, 0) * 10 END), 'dnf') AS courseA,
                    COALESCE(MIN(CASE WHEN r.crs_id = 'B' THEN r.seconds + IFNULL(r.cones, 0) * 5 + IFNULL(r.wd, 0) * 10 END), MAX(CASE WHEN r.crs_id = 'B' THEN r.seconds + IFNULL(r.cones, 0) * 5 + IFNULL(r.wd, 0) * 10 END), 'dnf') AS courseB,
                    COALESCE(MIN(CASE WHEN r.crs_id = 'C' THEN r.seconds + IFNULL(r.cones, 0) * 5 + IFNULL(r.wd, 0) * 10 END), MAX(CASE WHEN r.crs_id = 'C' THEN r.seconds + IFNULL(r.cones, 0) * 5 + IFNULL(r.wd, 0) * 10 END), 'dnf') AS courseC,
                    COALESCE(MIN(CASE WHEN r.crs_id = 'D' THEN r.seconds + IFNULL(r.cones, 0) * 5 + IFNULL(r.wd, 0) * 10 END), MAX(CASE WHEN r.crs_id = 'D' THEN r.seconds + IFNULL(r.cones, 0) * 5 + IFNULL(r.wd, 0) * 10 END), 'dnf') AS courseD,
                    COALESCE(MIN(CASE WHEN r.crs_id = 'E' THEN r.seconds + IFNULL(r.cones, 0) * 5 + IFNULL(r.wd, 0) * 10 END), MAX(CASE WHEN r.crs_id = 'E' THEN r.seconds + IFNULL(r.cones, 0) * 5 + IFNULL(r.wd, 0) * 10 END), 'dnf') AS courseE,
                    COALESCE(MIN(CASE WHEN r.crs_id = 'F' THEN r.seconds + IFNULL(r.cones, 0) * 5 + IFNULL(r.wd, 0) * 10 END), MAX(CASE WHEN r.crs_id = 'F' THEN r.seconds + IFNULL(r.cones, 0) * 5 + IFNULL(r.wd, 0) * 10 END), 'dnf') AS courseF
                FROM driver AS d
                INNER JOIN car AS c ON d.car = c.car_num
                LEFT JOIN run AS r ON d.driver_id = r.dr_id
                GROUP BY d.driver_id, driverName, age, CarModel
                ) AS subquery

            -- Join with driver and caregiver tables
            LEFT JOIN driver AS d ON subquery.DriverID = d.driver_id
            LEFT JOIN driver as caregiver on d.caregiver = caregiver.driver_id
            INNER JOIN car as c on d.car = c.car_num

            -- Filter by first name or surname matches
            WHERE d.first_name LIKE %s OR d.surname LIKE %s
                OR (d.first_name LIKE %s OR d.surname LIKE %s)

            -- Order the results by OverallResult, handling 'NQ' cases
            ORDER BY CASE
            WHEN OverallResult = 'NQ' THEN 1
            ELSE 0
            END, OverallResult,
            DriverID;'''

        # Execute the SQL query with search terms as parameters
        connection.execute(sql, (f"%{first_name}%", f"%{surname}%", f"%{surname}%", f"%{first_name}%"))
        
        # Fetch the query results
        results = connection.fetchall()

        # Render the 'driversearchresult.html' template with the search results
        return render_template('driversearchresult.html', results=results)
    
    # If it's a GET request, render the 'driversearch.html' template to display the search form
    return render_template("driversearch.html")
#----------------------------------------------------------------------------




################### EDIT RUNS #####################
# DISPLAYING WAYS(BY DRIVER OR BY COURSE) OF UPDATING RUNS
@app.route("/admin/editruns", methods=['GET', 'POST'])
def editruns():
    # Get a database connection
    connection = getCursor()

    if request.method == 'POST':
        # Retrieve 'dr_id' and 'crs_id' from the submitted form
        dr_id = request.form.get('dr_id')
        crs_id = request.form.get('crs_id')

        if dr_id:
            # If 'dr_id' is selected, fetch and display runs for the selected driver

            # Define SQL query to fetch driver's runs
            sql ='''SELECT 
                        r.dr_id,
                        d.first_name, 
                        d.surname, 
                        c.course_id, 
                        c.name as course_name,
                        r.run_num as run_number,
                        r.seconds as time,
                        r.cones, 
                        CASE 
                            WHEN r.wd = 1 THEN 'wd'             -- display 'wd' if r.wd = 1
                            ELSE ''                             -- Otherwise empty string
                        END as wd
                    FROM run as r
                    INNER JOIN driver as d on d.driver_id = r.dr_id         -- Joining the 'driver' table aliased as 'd'
                    INNER JOIN course as c on c.course_id = r.crs_id        -- Joining the 'course' table aliased as 'c'
                    WHERE r.dr_id = %s                                      -- Filter by dr_id
                    ORDER BY r.dr_id, d.first_name, d.surname, c.course_id, r.run_num;
            '''
            parameters = (dr_id,)
            connection.execute(sql, parameters)
            runList = connection.fetchall()
            
            # Render the 'runeditting_driver.html' template with the driver's run list
            return render_template('runeditting_driver.html', run_list=runList)

        elif crs_id:
            # If 'crs_id' is selected, fetch and display runs for the selected course

            # Define SQL query to fetch course runs
            sql = '''SELECT 
                        c.course_id, 
                        c.name as course_name,
                        r.run_num as run_number,
                        r.dr_id,
                        d.first_name, 
                        d.surname, 
                        r.seconds as time,
                        r.cones, 
                        CASE 
                            WHEN r.wd = 1 THEN 'wd'                 -- display 'wd' if r.wd = 1
                            ELSE ''                                 -- Otherwise empty string
                        END as wd
                    FROM run as r
                    INNER JOIN driver as d on d.driver_id = r.dr_id             -- Joining the 'driver' table aliased as 'd'
                    INNER JOIN course as c on c.course_id = r.crs_id            -- Joining the 'course' table aliased as 'c'
                    WHERE r.crs_id = %s                                         -- Filter by crs_id
                    ORDER BY c.course_id, r.run_num, r.dr_id;
            '''
            parameters = (crs_id,)
            connection.execute(sql, parameters)      
            runList = connection.fetchall()
            
            # Render the 'runeditting_course.html' template with the course run list
            return render_template('runeditting_course.html', run_list = runList)
    
    # If it's a GET request, retrieve the list of drivers and courses
    connection.execute('SELECT driver_id, first_name, surname FROM driver;')
    drivers = connection.fetchall()
    connection.execute('SELECT course_id, name FROM course;')
    courses = connection.fetchall()

    # Render the 'editruns.html' template with the list of drivers and courses
    return render_template("editruns.html", drivers = drivers, courses = courses)




# UPDATING DATABASE WITH NEW VALUES
@app.route("/update_run", methods=['POST'])
def update_run():   
    if request.method == 'POST':
        connection = getCursor()

        # Retrieve run data from the submitted form
        driver_id = request.form.get('driver_id')  
        course_id = request.form.get('course_id')  
        run_number = request.form.get('run_number')  
        time = request.form.get('time')         
        cones = request.form.get('cones') 
        wd = request.form.get('wd')  

        # Define an SQL query to update run data in the database
        sql = '''
                UPDATE run
                -- If value is an empty string, set 'seconds' and 'cones' to NULL; otherwise use existing value
                SET seconds = CASE WHEN %s = '' THEN NULL ELSE COALESCE(%s, seconds) END,
                    cones = CASE WHEN %s = '' THEN NULL ELSE COALESCE(%s, cones) END,
                    wd = COALESCE(%s, wd)
                
                -- Update rows in 'run' table where the driver ID, course ID, and run number match the provided values
                WHERE dr_id = %s AND crs_id = %s AND run_num = %s;
            '''
 
        # Define parameters for the SQL query
        parameters = (time, time, cones, cones, wd, driver_id, course_id, run_number)
        connection.execute(sql, parameters)

        # Retrieve additional data from the form
        first_name = request.form.get('first_name')  
        surname = request.form.get('surname')  
        course_name = request.form.get('course_name')  

        # Store updated run information in a dictionary
        updated_run_info = {
            "driver_id": driver_id,
            "first_name": first_name,
            "surname": surname,
            "course_id": course_id,
            "course_name": course_name,
            "run_number": run_number,
            "time": time,
            "cones": cones,
            "wd": wd
        }

        # render template
        return render_template("success_edit.html", updated_run=updated_run_info)
    
    
#--------------------------------------------------------------------------------


################# DISPLAYING MESSAGES ################


# success in editting run message #
@app.route("/admin/success_edit")
def success_edit():
    # Get the updated run information
    updated_run = request.args.get('updated_run')
    # Render template
    return render_template("success_edit.html", updated_run = updated_run)


# success in adding driver message #
@app.route("/admin/success_add")
def success_add():
    # Get the added driver information 
    added_driver = request.args.get('added_driver')
    # Render template
    return render_template("success_add.html", added_driver = added_driver)






################## ADD A DRIVER ####################

# CALCULATE AGE WITH GIVEN DOB
def calculate_age(date_of_birth):
    if date_of_birth:
        try:   
            # Attempt to process the date_of_birth using 'day-month-year' format
            birth_date = datetime.strptime(date_of_birth, '%d-%m-%Y').date()
        except ValueError:
            try:   
                # If processing with 'day-month-year' format fails, try 'year-month-day' format
                birth_date = datetime.strptime(date_of_birth, '%Y-%m-%d').date()
            except ValueError as e:
                print("Error:", str(e))
                return None

        # Get the current date
        today = datetime.now().date()  

        # Calculate age based on birth date and current date
        if (today.month, today.day) >= (birth_date.month, birth_date.day):
            age = today.year - birth_date.year
        else:
            age = today.year - birth_date.year - 1
        return age
    else:
        # Return None if date_of_birth is not provided
        return None




# ADDING DIFFERENT TYPES OF DRIVERS

@app.route("/admin/addadriver", methods=['GET', 'POST'])
def addadriver():
    connection = getCursor()

    # Getting car info from database
    connection.execute("SELECT * FROM car;")
    cars = connection.fetchall()

    if request.method == 'POST':
        # COLLECTING INFO FROM FORM
        first_name = request.form.get("first_name")
        surname = request.form.get("surname")
        car_num = request.form.get("car_num")
        
        # DECIDING IF DRIVER IS JUNIOR
        is_junior = request.form.get("junior_driver")



        # FOR JUNIOR DRIVERS
        if is_junior == 'on':

            # ASKING FOR DOB AND CALCULATING AGE
            date_of_birth = request.form.get("date_of_birth")
            age = calculate_age(date_of_birth)

            if age is None:
                # if date_of_birth not entered, prompt the user to re-try
                return render_template('agenone.html')
            
            # DRIVERS WHO NEED A CARE-GIVER
            if age and age <= 16 and age >= 12:
                connection = getCursor()
    
                # retrieve caregiver info to be passed to template
                connection.execute("SELECT driver_id, first_name, surname FROM driver WHERE age is null;")
                caregivers = connection.fetchall()

                # Render template for user to add a caregiver
                return render_template('addcaregiver.html', caregivers=caregivers, first_name=first_name, surname=surname, car_num=car_num, date_of_birth=date_of_birth, age=age)

            # DRIVERS YOUNGER THAN 12
            elif age and age < 12:
                # if the new driver's age is less than 12, they are not qualified
                # render template to prompt user
                return render_template("tooyoung.html")

            # JUNIOR DRIVERS WHO DO NOT NEED A CARE-GIVER
            elif age and age > 16 and age <= 25:
                # connect to database to insert new driver
                connection_junior = getCursor()

                # SQL statement to insert a new junior driver into the database
                sql_driver = "INSERT INTO driver (first_name, surname, date_of_birth, age, caregiver, car) \
                    VALUES (%s, %s, %s, %s, %s, %s);"
                
                # Parameters for the SQL query, where caregiver is Null
                parameters_driver = (first_name, surname, date_of_birth, age, None, car_num)
                connection_junior.execute(sql_driver, parameters_driver)
        

                # get the new driver's driver_id
                driver_id = connection_junior.lastrowid         

                # ADDING 12 RUNS

                # Create a new database connection
                connection_run1 = getCursor()

                # retrieve distinct course IDs and store them in the 'courses' list
                connection_run1.execute("SELECT DISTINCT crs_id FROM run;")
                courses = [row[0] for row in connection_run1.fetchall()]

                # retrieve distinct run numbers and store them in the 'run_numbers' list
                connection_run1.execute("SELECT DISTINCT run_num FROM run;")
                run_numbers = [row[0] for row in connection_run1.fetchall()]

                # insert 12 blank runs
                # loop through each distinct course and run number
                for course in courses:
                    for run_num in run_numbers:
                        
                        # insert a new run record into the database
                        sql_run = "INSERT INTO run (dr_id, crs_id, run_num, seconds, cones, wd) VALUES (%s, %s, %s, %s, %s, %s);"
                        
                        # Define the parameters with default values
                        parameters_run = (driver_id, course, run_num, None, None, 0)

                        # Execute the query to insert the new run record with default values
                        connection_run1.execute(sql_run, parameters_run)

                # store new driver's info in a dictionary to be passed to template
                added_driver_info = {
                        "driver_id": driver_id,
                        "first_name": first_name,
                        "surname": surname,
                        "date_of_birth": date_of_birth,
                        "age": age,
                        "caregiver": None,
                        "car_number": car_num
                    }

                # render template
                return render_template('success_add.html', added_driver = added_driver_info)
          
            # FOR DRIVERS OVER 25 BUT MISTAKENLY ENTERED AS JUNIOR 
            else:
                # connect to database to insert new driver
                connection_no_junior = getCursor()

                # Define query for inserting a new driver into the database
                sql_driver = "INSERT INTO driver (first_name, surname, date_of_birth, age, caregiver, car) \
                        VALUES (%s, %s, %s, %s, %s, %s);"
                # Prepare parameters, setting date_of_birth, age, and caregiver to None
                parameters_driver = (first_name, surname, None, None, None, car_num)
                # Execute the SQL query 
                connection_no_junior.execute(sql_driver, parameters_driver)
            
                # Get the newly assigned driver ID
                driver_id = connection_no_junior.lastrowid         

                # insert 12 blank runs for the new driver
                # get a new connection
                connection_run2 = getCursor()

                # Retrieve distinct course IDs and run numbers from the 'run' table
                connection_run2.execute("SELECT DISTINCT crs_id FROM run;")
                courses = [row[0] for row in connection_run2.fetchall()]
                connection_run2.execute("SELECT DISTINCT run_num FROM run;")
                run_numbers = [row[0] for row in connection_run2.fetchall()]
                
                 # loop through courses and run numbers to insert blank run records for the new driver
                for course in courses:
                    for run_num in run_numbers:    
                        sql_run = "INSERT INTO run (dr_id, crs_id, run_num, seconds, cones, wd) VALUES (%s, %s, %s, %s, %s, %s);"
                        parameters_run = (driver_id, course, run_num, None, None, 0)
                        connection_run2.execute(sql_run, parameters_run)

                # store new driver's info into a new dictionary to be passed to template
                added_driver_info = {
                        "driver_id": driver_id,
                        "first_name": first_name,
                        "surname": surname,
                        "date_of_birth": None,
                        "age": None,
                        "caregiver": None,
                        "car_number": car_num
                    }

                # render template
                return render_template('success_add.html', added_driver = added_driver_info)
                
            

        # FOR DRIVERS WHO ARE NOT JUNIOR
        else:
            # connect to database to insert new driver
            connection_no_junior = getCursor()
            # Define query for inserting a new driver into the database
            sql_driver = "INSERT INTO driver (first_name, surname, date_of_birth, age, caregiver, car) \
                    VALUES (%s, %s, %s, %s, %s, %s);"
            # Prepare the parameters, setting date_of_birth, age, and caregiver to None
            parameters_driver = (first_name, surname, None, None, None, car_num)
            # Execute query to insert the new driver
            connection_no_junior.execute(sql_driver, parameters_driver)
        
            # Get the newly assigned driver ID
            driver_id = connection_no_junior.lastrowid         

            # insert 12 blank runs

            # get a new connection
            connection_run3 = getCursor()
            # Retrieve distinct course IDs and run numbers from the 'run' table
            connection_run3.execute("SELECT DISTINCT crs_id FROM run;")
            courses = [row[0] for row in connection_run3.fetchall()]
            connection_run3.execute("SELECT DISTINCT run_num FROM run;")
            run_numbers = [row[0] for row in connection_run3.fetchall()]

            # Iterate over courses and run numbers to insert blank run records for the new driver
            for course in courses:
                for run_num in run_numbers:
                    sql_run = "INSERT INTO run (dr_id, crs_id, run_num, seconds, cones, wd) VALUES (%s, %s, %s, %s, %s, %s);"
                    parameters_run = (driver_id, course, run_num, None, None, 0)
                    connection_run3.execute(sql_run, parameters_run)

            # Create a dictionary with information about the newly added driver
            added_driver_info = {
                        "driver_id": driver_id,
                        "first_name": first_name,
                        "surname": surname,
                        "date_of_birth": None,
                        "age": None,
                        "caregiver": None,
                        "car_number": car_num
                    }

            # render template and pass the added driver info through to display
            return render_template('success_add.html', added_driver = added_driver_info)
            
    # If it's not a POST request, render the 'addadriver.html' template with the list of cars
    return render_template('addadriver.html', cars=cars)    

            

########### adding a caregiver ############

@app.route("/admin/addcaregiver", methods=['GET', 'POST'])
def addcaregiver():
    # establish conncetion
    connection = getCursor()
    
    # retrieve caregiver info from database
    connection.execute("SELECT driver_id, first_name, surname FROM driver WHERE age is null;")
    caregivers = connection.fetchall()

    if request.method == 'POST':
        # RETRIEVE VALUES FROM PREVIOUS TEMPLATE
        first_name = request.form.get("first_name")
        surname = request.form.get("surname")
        car_num = request.form.get("car_num")
        date_of_birth = request.form.get("date_of_birth")

        # Calculate the age of the driver based on the provided date of birth
        age = calculate_age(date_of_birth)
            
        # collecting caregiver value from form
        caregiver = request.form.get("caregiver")

        # insert into database
        sql_driver = "INSERT INTO driver (first_name, surname, date_of_birth, age, caregiver, car) \
                    VALUES (%s, %s, %s, %s, %s, %s);"
        parameters_driver = (first_name, surname, date_of_birth, age, caregiver, car_num)
        connection.execute(sql_driver, parameters_driver)
        
        # Get the newly assigned driver ID
        driver_id = connection.lastrowid         

        # add 12 blank runs for the new driver
        connection = getCursor()
        connection.execute("SELECT DISTINCT crs_id FROM run;")
        courses = [row[0] for row in connection.fetchall()]
        connection.execute("SELECT DISTINCT run_num FROM run;")
        run_numbers = [row[0] for row in connection.fetchall()]

        # Iterate over courses and run numbers to insert blank run records
        for course in courses:
            for run_num in run_numbers:       
                sql_run = "INSERT INTO run (dr_id, crs_id, run_num, seconds, cones, wd) VALUES (%s, %s, %s, %s, %s, %s);"
                parameters_run = (driver_id, course, run_num, None, None, 0)
                connection.execute(sql_run, parameters_run)

        # Retrieve the name of the caregiver for display
        sql = "SELECT first_name, surname FROM driver WHERE driver_id = %s;"
        parameters = (caregiver,)
        connection.execute(sql,parameters)
        caregiver_name = connection.fetchone()
        caregiver_full_name = ' '.join(caregiver_name)

        # Create a dictionary with information about the newly added driver
        added_driver_info = {
                        "driver_id": driver_id,
                        "first_name": first_name,
                        "surname": surname,
                        "date_of_birth": date_of_birth,
                        "age": age,
                        "caregiver": caregiver_full_name,
                        "car_number": car_num
                    }

        # render template, passing the added driver info for display
        return render_template('success_add.html', added_driver = added_driver_info)

    # If it's not a POST request, render the 'addcaregiver.html' template, passing caregiver information
    return render_template("addcaregiver.html",caregiver=caregiver, caregivers=caregivers)

#---------------------------------------------------------------------------------------------------


