import tkinter as tk
from tkinter import ttk, messagebox
from .db import get_conn, init_db, seed_demo

APP_TITLE = 'Inventory Management System - TQM Q14'

class InventoryApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title(APP_TITLE)
        self.geometry('1180x760')
        self.minsize(1000, 650)
        self.configure(bg='#eef2f7')
        init_db()
        self.current_user = 'admin'
        self.current_page = 'Home'
        self.breadcrumb = tk.StringVar(value='Home')
        self.page_title = tk.StringVar(value='Inventory Dashboard')
        self.status = tk.StringVar(value='Ready')
        self._build_shell()
        self.show_home()

    def _build_shell(self):
        top = tk.Frame(self, bg='#143d59', height=70)
        top.pack(fill='x')
        tk.Label(top, text='INVENTORY MANAGEMENT SYSTEM', bg='#143d59', fg='white', font=('Segoe UI', 18, 'bold')).pack(side='left', padx=22)
        self.user_lbl = tk.Label(top, text='Admin | Q14 Navigation', bg='#143d59', fg='#dbeafe', font=('Segoe UI', 10))
        self.user_lbl.pack(side='right', padx=22)

        nav = tk.Frame(self, bg='white', height=48, bd=1, relief='solid')
        nav.pack(fill='x')
        for text, cmd in [('Home', self.show_home), ('Products', self.show_products), ('Suppliers', self.show_suppliers), ('Stock', self.show_stock), ('Reports', self.show_reports)]:
            ttk.Button(nav, text=text, command=cmd).pack(side='left', padx=5, pady=7)
        ttk.Button(nav, text='⌨ Shortcuts', command=self.show_shortcuts).pack(side='right', padx=5, pady=7)
        ttk.Button(nav, text='Logout', command=self.destroy).pack(side='right', padx=5, pady=7)

        crumb = tk.Frame(self, bg='#f7fafc')
        crumb.pack(fill='x', padx=18, pady=(12, 4))
        tk.Label(crumb, text='Navigation:', bg='#f7fafc', fg='#64748b', font=('Segoe UI', 9, 'bold')).pack(side='left')
        tk.Label(crumb, textvariable=self.breadcrumb, bg='#f7fafc', fg='#1e3a8a', font=('Segoe UI', 9)).pack(side='left', padx=8)

        titlebar = tk.Frame(self, bg='#eef2f7')
        titlebar.pack(fill='x', padx=18, pady=(3, 5))
        tk.Label(titlebar, textvariable=self.page_title, bg='#eef2f7', fg='#0f172a', font=('Segoe UI', 22, 'bold')).pack(side='left')
        ttk.Button(titlebar, text='← Home', command=self.show_home).pack(side='right')

        self.content = tk.Frame(self, bg='#eef2f7')
        self.content.pack(fill='both', expand=True, padx=18, pady=10)
        self.bind_all('<Control-h>', lambda e: self.show_home())
        self.bind_all('<Control-p>', lambda e: self.show_products())
        self.bind_all('<Control-s>', lambda e: self.show_stock())
        self.bind_all('<Control-r>', lambda e: self.show_reports())
        self.bind('<F1>', lambda e: self.show_shortcuts())

    def _clear(self):
        for w in self.content.winfo_children(): w.destroy()

    def _set_page(self, name, title):
        self.current_page = name
        self.breadcrumb.set(f'Home  ›  {name}')
        self.page_title.set(title)
        self.status.set(f'Viewing {name}')
        self._clear()

    def _tile(self, parent, title, value, column, row=0, command=None):
        card = tk.Frame(parent, bg='white', bd=1, relief='solid')
        card.grid(row=row, column=column, padx=7, pady=7, sticky='nsew')
        tk.Label(card, text=title, bg='white', fg='#64748b', font=('Segoe UI', 10, 'bold')).pack(anchor='w', padx=16, pady=(15,5))
        tk.Label(card, text=value, bg='white', fg='#0f172a', font=('Segoe UI', 23, 'bold')).pack(anchor='w', padx=16, pady=(0,15))
        if command:
            ttk.Button(card, text='Open', command=command).pack(anchor='e', padx=12, pady=(0,12))
        return card

    def show_home(self):
        self._set_page('Home', 'Inventory Dashboard')
        conn = get_conn(); cur = conn.cursor()
        total = cur.execute('SELECT COUNT(*) c FROM products').fetchone()['c']
        low = cur.execute('SELECT COUNT(*) c FROM products WHERE quantity <= reorder_level').fetchone()['c']
        suppliers = cur.execute('SELECT COUNT(*) c FROM suppliers').fetchone()['c']
        stock_units = cur.execute('SELECT COALESCE(SUM(quantity),0) q FROM products').fetchone()['q']
        conn.close()
        grid = tk.Frame(self.content, bg='#eef2f7'); grid.pack(fill='x');
        for i in range(4): grid.grid_columnconfigure(i, weight=1)
        self._tile(grid, 'Total Products', total, 0, command=self.show_products)
        self._tile(grid, 'Low Stock Alerts', low, 1, command=self.show_products)
        self._tile(grid, 'Total Suppliers', suppliers, 2, command=self.show_suppliers)
        self._tile(grid, 'Units in Stock', stock_units, 3, command=self.show_stock)

        quick = tk.Frame(self.content, bg='white', bd=1, relief='solid'); quick.pack(fill='both', expand=True, pady=12)
        tk.Label(quick, text='Quick Navigation', bg='white', font=('Segoe UI', 14, 'bold')).pack(anchor='w', padx=18, pady=(16,10))
        actions=[('Manage Products', self.show_products),('Manage Suppliers', self.show_suppliers),('Record Stock Movement', self.show_stock),('View Quality Reports', self.show_reports),('Keyboard Shortcuts', self.show_shortcuts)]
        for label, cmd in actions:
            ttk.Button(quick, text=f'  {label}', command=cmd).pack(fill='x', padx=18, pady=5, ipady=6)

    def show_shortcuts(self):
        self._set_page('Help', 'Navigation Shortcuts')
        data=[('Ctrl + H','Home Dashboard'),('Ctrl + P','Products'),('Ctrl + S','Stock Movements'),('Ctrl + R','Reports'),('F1','Shortcut Help'),('Home button','Return to dashboard'),('Top navigation','Jump between major modules'),('Breadcrumb trail','Show current navigation path')]
        tree=ttk.Treeview(self.content, columns=('shortcut','purpose'), show='headings', height=12); tree.pack(fill='x', padx=10, pady=10)
        tree.heading('shortcut', text='Shortcut / Navigation'); tree.heading('purpose', text='Purpose')
        tree.column('shortcut', width=220); tree.column('purpose', width=700)
        for a,b in data: tree.insert('', 'end', values=(a,b))

    def show_products(self):
        self._set_page('Products', 'Product Management')
        bar=tk.Frame(self.content,bg='#eef2f7');bar.pack(fill='x',pady=(0,8))
        ttk.Button(bar,text='Add Product',command=self.product_dialog).pack(side='left')
        ttk.Button(bar,text='Refresh',command=self.show_products).pack(side='left',padx=7)
        ttk.Button(bar,text='Delete Selected',command=lambda: self.delete_product(tree)).pack(side='left',padx=7)
        cols=('id','sku','name','category','supplier','quantity','reorder','price','status')
        tree=ttk.Treeview(self.content,columns=cols,show='headings');tree.pack(fill='both',expand=True)
        heads={'id':'ID','sku':'SKU','name':'Product','category':'Category','supplier':'Supplier','quantity':'Qty','reorder':'Reorder','price':'Price','status':'Status'}
        widths={'id':55,'sku':110,'name':220,'category':130,'supplier':160,'quantity':70,'reorder':75,'price':90,'status':90}
        for c in cols: tree.heading(c,text=heads[c]);tree.column(c,width=widths[c])
        conn=get_conn(); rows=conn.execute('''SELECT p.id,p.sku,p.name,COALESCE(c.name,'-') category,COALESCE(s.name,'-') supplier,
            p.quantity,p.reorder_level,p.price,p.status FROM products p LEFT JOIN categories c ON c.id=p.category_id LEFT JOIN suppliers s ON s.id=p.supplier_id ORDER BY p.name''').fetchall();conn.close()
        for r in rows: tree.insert('', 'end', values=tuple(r))
        tree.bind('<Double-1>', lambda e: self.product_dialog(tree.item(tree.focus(),'values')[0]) if tree.focus() else None)
        self.product_tree = tree

    def delete_product(self, tree):
        item = tree.focus()
        if not item:
            messagebox.showwarning('Selection', 'Select a product first.')
            return
        vals = tree.item(item, 'values')
        if not messagebox.askyesno('Confirm Delete', f'Delete product {vals[1]}?'):
            return
        conn=get_conn(); conn.execute('DELETE FROM products WHERE id=?',(vals[0],)); conn.commit(); conn.close()
        self.show_products()

    def product_dialog(self, product_id=None):
        win=tk.Toplevel(self);win.title('Product');win.geometry('520x470');win.transient(self);win.grab_set()
        fields=[('SKU','sku'),('Product Name','name'),('Quantity','quantity'),('Reorder Level','reorder'),('Unit Price','price')]
        entries={}
        for i,(lbl,key) in enumerate(fields):
            tk.Label(win,text=lbl,font=('Segoe UI',10,'bold')).grid(row=i,column=0,sticky='w',padx=20,pady=10); e=tk.Entry(win,width=40);e.grid(row=i,column=1,padx=20,pady=10);entries[key]=e
        conn=get_conn(); cats=conn.execute('SELECT id,name FROM categories ORDER BY name').fetchall(); sups=conn.execute('SELECT id,name FROM suppliers ORDER BY name').fetchall(); conn.close()
        tk.Label(win,text='Category',font=('Segoe UI',10,'bold')).grid(row=5,column=0,sticky='w',padx=20,pady=10)
        cat=ttk.Combobox(win,values=[f'{r[0]} - {r[1]}' for r in cats],state='readonly',width=37);cat.grid(row=5,column=1,padx=20,pady=10)
        tk.Label(win,text='Supplier',font=('Segoe UI',10,'bold')).grid(row=6,column=0,sticky='w',padx=20,pady=10)
        sup=ttk.Combobox(win,values=[f'{r[0]} - {r[1]}' for r in sups],state='readonly',width=37);sup.grid(row=6,column=1,padx=20,pady=10)
        if product_id:
            conn=get_conn();r=conn.execute('SELECT * FROM products WHERE id=?',(product_id,)).fetchone();conn.close()
            if r:
                for k in entries: entries[k].insert(0, r['reorder_level'] if k=='reorder' else r[k])
                if r['category_id']:
                    cat.set(next((f'{x[0]} - {x[1]}' for x in cats if x[0]==r['category_id']),''))
                if r['supplier_id']:
                    sup.set(next((f'{x[0]} - {x[1]}' for x in sups if x[0]==r['supplier_id']),''))
        def save():
            try:
                sku=entries['sku'].get().strip(); name=entries['name'].get().strip(); qty=int(entries['quantity'].get()); reorder=int(entries['reorder'].get()); price=float(entries['price'].get())
                if not sku or not name or qty<0 or reorder<0 or price<0: raise ValueError
                cat_id=int(cat.get().split(' - ')[0]) if cat.get() else None; sup_id=int(sup.get().split(' - ')[0]) if sup.get() else None
                conn=get_conn();cur=conn.cursor()
                if product_id: cur.execute('UPDATE products SET sku=?,name=?,category_id=?,supplier_id=?,quantity=?,reorder_level=?,price=?,updated_at=CURRENT_TIMESTAMP WHERE id=?',(sku,name,cat_id,sup_id,qty,reorder,price,product_id));action='Updated'
                else: cur.execute('INSERT INTO products(sku,name,category_id,supplier_id,quantity,reorder_level,price) VALUES(?,?,?,?,?,?,?)',(sku,name,cat_id,sup_id,qty,reorder,price));action='Created'
                cur.execute('INSERT INTO audit_log(username,action,entity,details) VALUES(?,?,?,?)', (self.current_user,action,'Product',sku))
                conn.commit();conn.close();win.destroy();self.show_products()
            except Exception: messagebox.showerror('Validation Error','Please enter valid product details.')
        ttk.Button(win,text='Save',command=save).grid(row=8,column=1,sticky='e',padx=20,pady=20)

    def show_suppliers(self):
        self._set_page('Suppliers','Supplier Management')
        ttk.Button(self.content,text='Refresh',command=self.show_suppliers).pack(anchor='w',pady=(0,8))
        tree=ttk.Treeview(self.content,columns=('id','name','phone','email','address'),show='headings');tree.pack(fill='both',expand=True)
        for c,t,w in [('id','ID',60),('name','Supplier',250),('phone','Phone',150),('email','Email',260),('address','Address',250)]:tree.heading(c,text=t);tree.column(c,width=w)
        conn=get_conn();rows=conn.execute('SELECT id,name,phone,email,address FROM suppliers ORDER BY name').fetchall();conn.close()
        for r in rows:tree.insert('', 'end', values=tuple(r))

    def show_stock(self):
        self._set_page('Stock','Stock Movement')
        bar=tk.Frame(self.content,bg='#eef2f7');bar.pack(fill='x',pady=(0,8));ttk.Button(bar,text='Record Movement',command=self.stock_dialog).pack(side='left');ttk.Button(bar,text='Refresh',command=self.show_stock).pack(side='left',padx=7)
        tree=ttk.Treeview(self.content,columns=('id','sku','name','type','qty','note','date'),show='headings');tree.pack(fill='both',expand=True)
        for c,t,w in [('id','ID',55),('sku','SKU',110),('name','Product',230),('type','Type',75),('qty','Qty',70),('note','Note',300),('date','Date',170)]:tree.heading(c,text=t);tree.column(c,width=w)
        conn=get_conn();rows=conn.execute('''SELECT m.id,p.sku,p.name,m.movement_type,m.quantity,COALESCE(m.note,''),m.created_at FROM stock_movements m JOIN products p ON p.id=m.product_id ORDER BY m.id DESC''').fetchall();conn.close()
        for r in rows:tree.insert('', 'end', values=tuple(r))

    def stock_dialog(self):
        win=tk.Toplevel(self);win.title('Stock Movement');win.geometry('460x280');win.grab_set()
        conn=get_conn();products=conn.execute('SELECT id,sku,name FROM products ORDER BY name').fetchall();conn.close()
        tk.Label(win,text='Product').grid(row=0,column=0,padx=20,pady=15,sticky='w'); product=ttk.Combobox(win,values=[f'{r[0]} - {r[1]} - {r[2]}' for r in products],state='readonly',width=30);product.grid(row=0,column=1)
        tk.Label(win,text='Type').grid(row=1,column=0,padx=20,pady=10,sticky='w'); typ=ttk.Combobox(win,values=['IN','OUT'],state='readonly',width=30);typ.grid(row=1,column=1);typ.current(0)
        tk.Label(win,text='Quantity').grid(row=2,column=0,padx=20,pady=10,sticky='w'); qty=tk.Entry(win,width=33);qty.grid(row=2,column=1)
        tk.Label(win,text='Note').grid(row=3,column=0,padx=20,pady=10,sticky='w'); note=tk.Entry(win,width=33);note.grid(row=3,column=1)
        def save():
            try:
                pid=int(product.get().split(' - ')[0]);q=int(qty.get());mt=typ.get();
                if q<=0: raise ValueError
                conn=get_conn();cur=conn.cursor();row=cur.execute('SELECT quantity FROM products WHERE id=?',(pid,)).fetchone()
                if mt=='OUT' and row['quantity']<q: raise ValueError
                newq=row['quantity']+q if mt=='IN' else row['quantity']-q
                cur.execute('UPDATE products SET quantity=?,updated_at=CURRENT_TIMESTAMP WHERE id=?',(newq,pid))
                cur.execute('INSERT INTO stock_movements(product_id,movement_type,quantity,note) VALUES(?,?,?,?)',(pid,mt,q,note.get().strip()))
                conn.commit();conn.close();win.destroy();self.show_stock()
            except Exception: messagebox.showerror('Error','Select a product and enter a valid quantity. OUT cannot exceed stock.')
        ttk.Button(win,text='Save Movement',command=save).grid(row=4,column=1,sticky='e',padx=20,pady=15)

    def show_reports(self):
        self._set_page('Reports','Quality & Inventory Reports')
        conn=get_conn();low=conn.execute('SELECT sku,name,quantity,reorder_level FROM products WHERE quantity<=reorder_level ORDER BY quantity').fetchall(); total=conn.execute('SELECT COALESCE(SUM(quantity*price),0) v FROM products').fetchone()['v'];conn.close()
        tk.Label(self.content,text=f'Inventory Value: ₹{total:,.2f}',bg='white',font=('Segoe UI',14,'bold')).pack(fill='x',pady=(0,8),ipady=10)
        box=tk.Frame(self.content,bg='white',bd=1,relief='solid');box.pack(fill='both',expand=True)
        tk.Label(box,text='Low Stock Exceptions',bg='white',font=('Segoe UI',13,'bold')).pack(anchor='w',padx=16,pady=14)
        tree=ttk.Treeview(box,columns=('sku','name','qty','reorder'),show='headings',height=10);tree.pack(fill='x',padx=16)
        for c,t,w in [('sku','SKU',120),('name','Product',320),('qty','Qty',100),('reorder','Reorder Level',150)]:tree.heading(c,text=t);tree.column(c,width=w)
        for r in low:tree.insert('', 'end', values=tuple(r))

if __name__ == '__main__':
    seed_demo()
    app=InventoryApp();app.mainloop()
