# Sport-Catalog-Application
A sport Catalog application for my Udacity Nanodegree! I have really delayed on this one!

# Catalog

### Description
Basic Python app framework with database, CRUD operations, JSON API, Google and Facebook login.

### Requirements
* Python
* Vagrant
* Flask
* SQLAlchemy
* Sqlite3

### How to Run

```sh
$ python lotofcategory.py
```

```sh
$ python application.py
```

### API

1. View all categories and items
* http://localhost:8000/sport/category/JSON

2. View individual category with category_id
* http://localhost:8000/sport/<int:category_id>/items/JSON'

3. View individual item with item_id
* http://localhost:8000/sport/<int:category_id>/<int:item_id>/JSON'

