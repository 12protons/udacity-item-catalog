Project 3: Item Catalog.

The Item Catalog is a site used to display items for predefined categories, and allows user to create, read, update, and delete items associated to a category.

To initially populate the database, run the following commands:

    python database_setup.py
    python lotsofitems.py

The database_setup.py script constructs an empty database used for the site. The logsofitems.py script populates the database with various items. If you want to add or modify the categories used in the site, edit the lotsofitems.py file as needed before running.

Once the database is populated, run the following command to start the site:

    python project.py

This starts the website, running on port 5000. Go to http://localhost:5000/ to view the site.

To view a category, click on a category name on the left. The list of items displayed in the category are shown to the right.

To create, edit, or delete items, you must be logged in to the site with your Google account. Click Login in the upper left to access the login page.

To logout of the page, click Logout in the upper left.