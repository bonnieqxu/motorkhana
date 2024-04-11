# Motorkhana

## Web Application Development Report

> This report presents a detailed analysis of my web application designed for the management of monthly Motorkhana events, as well as the drivers and their performance within the BRMM car club. The application utilizes technologies such as Python, Flask, HTML, Jinja, Bootstrap, MySQL Workbench, and GitHub, and it has been successfully deployed on PythonAnywhere.

***

### Web Application Structure
***

[Click here to access a hand-drawn diagram illustrating the web application's structure.](https://github.com/bonniexu8/motorkhana/blob/main/Web%20App%20Structure%20-%20hand%20drawn%20diagram%20EDITED.jpg)


•	 **Home Page ("/", function: home()):**    
The home page serves as the user entry point and displays the "base.html" template.

•	**List Courses ("/listcourses", function: listcourses()):**   
Designed for viewing all available courses and their images in a table. It passes the “course_list” and renders the "courselist.html" template.

•	**List Drivers ("/listdrivers", function: listdrivers()):**   
This route allows users to explore all drivers, displaying the "driverlist.html" template. Data is passed to the template in the form of "driver_list." It presents driver names as clickable links, leading to the “driver's run detail” page.

•	**Name Dropdown ("/namedropdown", function: namedropdown()):**   
This route passes the “name_list” to the "namedropdown.html" template and provides a dropdown list of driver names. Users make selections, leading to the "driversrundetails.html" template, where they access detailed run information.

•	**Drivers Run Details ("/namedropdown/driversrundetails", function:driversrundetails()):**    
Users select a driver from a dropdown list and are directed to the "driversrundetails.html" template, which offers a detailed breakdown of the selected driver's run information. Both “driver_info” and “rundetail_list” are passed to the template.

•	**Overall Results ("/overallresults", function: overallresults()):**   
This route allows users to access overall results via the "overallresults.html" template. The relevant data is passed to the template as "overall_list."

•	**Graph ("/graph", function: showgraph()):**   
This route generates a horizontal bar graph of the top five drivers' results using the "top5graph.html" template. It passes data to the template as "name_list" and "value_list" for display.

•	**Admin ("/admin", function: admin()):**   
Reserved for admin users, this route leads to the "admin.html" template, serving as the central administrative dashboard for various functions.

•	**Junior List ("/admin/juniorlist", function: juniorlist()):**   
Reserved for admin users, this route provides a view of all junior drivers through the "juniorlist.html" template. The data is passed to the template as "junior_list".

•	**Driver Search ("/admin/driversearch", function: driversearch()):**   
Admin users can search for driver information. It renders the “driversearch.html” template for user input, presenting results in the "driversearchresult.html" template. The data is passed to the template as “results”.

•	**Edit Runs ("/admin/editruns", function: editruns()):**   
Admins can update run records either by driver or course. It offers two templates, "runeditting_driver.html"(data is passed in the form of “run_list”) and "runeditting_course.html”, (data is passed in the form of “run_list”), along with the "editruns.html" template for user selection (data is passed in the form of “drivers” and “courses”). 

•	**Update Run ("/update_run", function: update_run()):**   
This crucial route is responsible for updating run data in the database and redirects users to the "success_edit.html" template. Data is passed to the template in the form of “updated_run”. This is a subsequent step after rendering the 'runeditting_driver.html' or 'runeditting_course.html' template.

•	**Success Edit ("/admin/success_edit", function: success_edit()):**   
Displays a success message after successfully editing a run. “updated_run” is passed to the "success_edit.html" template.

•	**Success Add ("/admin/success_add", function: success_add()):**   
Displays a success message after successfully adding a new driver. “added_driver” is passed to the “success_add.html” template.

•	**Age Calculation (function: calculate_age(date_of_birth)):**   
Calculates the age of the new driver by processing the user-entered value of "date_of_birth" and returns the value to the “addadriver” function.

•	**Add a Driver ("/admin/addadriver", function: addadriver()):**   
Admins can add new drivers to the database, distinguishing between junior and non-junior drivers. It passes “cars” to 'addadriver.html' template for car selection and driver names input, offering users the option to identify a junior driver. Then it routes users to the appropriate template based on their input and handles scenarios as follows:

    - Drivers aged 25 or older:   
    Driver’s information and 12 blank runs inserted into the database. Passes ‘added_driver’ to 'success_add.html' template and displays a message.
    
    - Junior drivers aged 16 to 25:   
    Driver’s information, including the value of date_of_birth and age, plus 12 blank runs inserted into the database. Passes “added_driver” to 'success_add.html' template and displays a message.
    
    - Junior drivers aged 12 to 16, requiring a caregiver:   
    "addcaregiver.html" template is displayed. All of the following data is passed to the template: caregivers, first_name, surname, car_num, date_of_birth and age.
    
    - Junior drivers under 12:   
    Deemed unqualified, and "tooyoung.html" template is shown, displaying a message.
    
    - Junior drivers with no date_of_birth entered:   
    Users are prompted with the "agenone.html" template and asked to try again.
    
    - Drivers aged over 25 mistakenly added as junior:   
    Database updated without date_of_birth and age values, 12 blank runs inserted. Passes “added_driver” to 'success_add.html' template and displays a message.

•	**Add a Caregiver ("/admin/addcaregiver", function: addcaregiver()):**   
This route is displayed only if the junior driver falls within the age range of 12 to 16. It handles the addition of caregiver details for junior drivers. Passes both “caregiver” and “caregivers” to the "addcaregiver.html" template and updates the database by adding the new driver’s full information and inserting 12 blank runs. It passes “added_driver” to the “success_add.html” template and displays a success message.

***

### Assumptions and Design Decisions

***

> During the development of the Motorkhana club web application, several assumptions and design decisions played a pivotal role in shaping the application's functionality and user experience:

***

#### Drivers’ Run Details Function:
**Decision**: After selecting a driver, users should be directed to a separate web page for detailed run information.  

**Rationale**: This approach was chosen to maintain a clear and organized user interface while offering comprehensive driver-specific run details. To implement this, the application utilizes a GET request to retrieve driver details when a specific driver is selected from a list. Furthermore, for efficient template value passing, it is more effective to use driver_id as the key value, a unique identifier.

***

#### List of Drivers Function: 
**Decision**: Initially, the interpretation of the directive to "show them in surname then first name order" was limited to the visual display of drivers’ names. However, it was later realized that it also referred to sorting the results.  

**Rationale**: This listing of drivers primarily involves a GET request to retrieve and display the driver information in the specified order, ensuring that the user experience aligns with the specified sorting criteria.

***

#### Bar Graph Presentation:
**Decision**: A decision was made to display the bar graph in ascending order, with the best results at the top.  

**Rationale**: This arrangement provides an intuitive and visually appealing representation of the data, allowing users to quickly identify the top-performing drivers and enhancing data visualization.

 ***
 
#### Driver Search Function: 
**Decision**: To provide users with comprehensive results, the decision was made to generate a substantial table displaying various driver details.  

**Rationale**: This approach includes various driver details such as driver_id, first_name, surname, date_of_birth, age, caregiver, car_num, model, drive_class, and all of the 6 course results, as well as the overall results. The search function typically involves a GET request with query parameters to retrieve filtered driver data, ensuring users have access to a rich set of driver information.

***

#### Edit Runs Function: 
**Decision**: Offering flexibility in locating runs for editing was a key design consideration, achieved by providing users with two options – selecting runs by a specific driver or course. 

**Rationale**: This approach streamlines the process of finding the relevant run for updates, enhancing user-friendliness. A GET request is used for displaying the initial form with a selection of drivers and courses. When a user submits the form to edit runs, a POST request is utilized to process and save the edits.   

An **obstacle** encountered during the testing phase highlighted the significance of the application's structure. The issue of only updating the first row's values was traced back to the placement of the Jinja "for" loop. To address this, the decision was made to add a submit button to each run (row) for easy updates, enhancing the user experience and the efficiency of data editing.

***

#### Add a Driver Function: 
**Decision**: Initially, the plan was to use a single template for adding drivers, with a checkbox to determine junior status. However, the challenge of achieving dynamic form changes through checkboxes led to the creation of a separate template for caregiver-related fields.  

**Rationale**: This decision ensures that user inputs align with the driver's age group, enhancing data accuracy and user experience. Due to limitations in dynamically altering the form using checkboxes (without JavaScript), a separate caregiver template was introduced. The "Add a Driver" function primarily utilizes a POST request to submit new driver information to the server and database.

***

#### Database Approach: 
**Decision**: A critical discovery was made regarding the database structure and queries. Initially, views were created in the database to facilitate server-side queries and maintain clean code. However, with the addition of admin features and the need to update/insert data, it became evident that views could not handle these functions effectively.  

**Rationale**: Additionally, synchronization issues between the local database and the PythonAnywhere database led to the decision to redo all previous MySQL queries. This decision ensured data integrity and consistency across platforms, maintaining the quality of data throughout the application.

***

#### Data Handling: 
**Decision**: The experience of working with data highlighted the importance of proper planning and logic.  

**Rationale**: Initially, there was an attempt to use Python logic to manipulate raw data. However, this approach proved to be complex, emphasizing the necessity of employing MySQL queries to refine data before integrating it into Python. This decision underscores the significance of meticulous planning and logical structure during the development process, leading to improved data handling and application efficiency.

***

> **These assumptions and design decisions collectively guided the development process, resulting in an application that meets the club's requirements and provides an efficient and user-friendly experience.**



***

### Database Questions

***

**1. SQL Statement for Creating "car" Table:**
 
The SQL statement for creating the "car" table is as follows:

    CREATE TABLE IF NOT EXISTS car  
    (  
    car_num INT PRIMARY KEY NOT NULL,  
    model VARCHAR(20) NOT NULL,  
    drive_class VARCHAR(3) NOT NULL  
    );

***

**2. Establishing Relationship Between "car" and "driver" Tables:**
   
The relationship between the "car" and "driver" tables is established through the "car_num" field in the "car" table, which also serves as the primary key, and the "car" field in the "driver" table. This setup forms a foreign key relationship.

This following line of SQL code sets up the relationship between the car and the driver table:

    FOREIGN KEY (car) REFERENCES car(car_num)  
    ON UPDATE CASCADE  
    ON DELETE CASCADE

***

**3. SQL Statements to Insert "Mini" and "GR Yaris" Details:**
   
The SQL statements to insert "Mini" and "GR Yaris" details into the "car" table are as follows:

    INSERT INTO car VALUES  
    (11,'Mini','FWD'),  
    (17,'GR Yaris','4WD');

***

**4. Setting Default Value for "driver_class" Field in the "driver" Table:**

To set a default value of 'RWD' for the "driver_class" field in the "driver" table, the SQL statement involves:

    CREATE TABLE IF NOT EXISTS car  
    (  
    car_num INT PRIMARY KEY NOT NULL,  
    model VARCHAR(20) NOT NULL,  
    drive_class VARCHAR(3) DEFAULT ‘RWD’  
    );

***

**5. Importance of Distinguishing Public and Admin Routes:**

Distinguishing between public and admin routes is critical to maintaining data integrity and security. Here are two specific issues that may arise if all web app facilities were available to everyone:

**- Data Manipulation:** Unrestricted access to admin routes could result in unauthorized data manipulation, including the ability for public users to edit runs, insert drivers, or alter results. This poses substantial security risks, potentially compromising the accuracy and fairness of competitions. By separating these routes, data integrity is safeguarded, ensuring that only authorized admin users can perform actions that may affect data accuracy, such as updating run records or adding drivers.

**- Privacy Concerns:** Admin features often involve access to sensitive data, such as drivers’ private information or detailed run results. Granting public users access to these data can lead to privacy breaches and misuse of personal information. To address this, admin routes should be protected from unauthorized access, ensuring that sensitive data and functions are restricted to authorized personnel. 

**By implementing role-based access control with separate routes for drivers and admins, the application ensures that users only access the features and information relevant to their roles. This approach effectively safeguards data and privacy, providing a secure and efficient user experience.**

