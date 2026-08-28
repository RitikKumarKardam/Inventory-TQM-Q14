# User Manual - Inventory Management System

**Student:** Ritik Kumar | **Roll No.:** 2520301005 | **Q14:** Improve Navigation

## 1. Start the application
From the project folder run:

```bash
python run.py
```

The first run creates a local SQLite database and sample records.

## 2. Navigation
- **Home:** dashboard.
- **Products:** product CRUD.
- **Suppliers:** supplier list.
- **Stock:** record stock IN/OUT.
- **Reports:** inventory value and low-stock exceptions.
- **Home button:** universal return path.
- **Breadcrumbs:** current route shown above each page.

## 3. Keyboard shortcuts
| Shortcut | Action |
|---|---|
| Ctrl + H | Home |
| Ctrl + P | Products |
| Ctrl + S | Stock |
| Ctrl + R | Reports |
| F1 | Shortcut help |

## 4. Product CRUD
Use **Add Product** to create an item. Double-click a row to edit. Select a row and use **Delete Selected** to delete after confirmation. SKU must be unique; quantity, reorder level and price must be non-negative.

## 5. Stock movement
Choose a product, choose **IN** or **OUT**, enter a positive quantity and optional note. An OUT operation is rejected when it would take stock below zero.

## 6. Reports
The report page shows total inventory value and products whose quantity is at or below reorder level.

## 7. Quality evidence
The `artifacts/` directory contains CTQ, SIPOC, architecture, checksheet, Pareto and Fishbone visuals.
