import pymysql

class ShoppingCart:
    connection = None
    total = 0

    def __init__(self, cid, id, name, count, price):
        self.cid = cid
        self.id = id
        self.name = name 
        self.count = int(count)
        self.price = float(price) 
        ShoppingCart.total = ShoppingCart.total + count*self.price

    def add(self, num):
        self.count += int(num)
        ShoppingCart.total +=int(num)*self.price
    
    def deduct(self, num):
        self.count -= int(num) 
        ShoppingCart.total -= int(num)*self.price

    def update(self, num):
        ShoppingCart.total = ShoppingCart.total - self.count*self.price + int(num)*self.price
        self.count = int(num)
    
    def clear(self):
        self.count = 0
        ShoppingCart.total = 0

    def subtotal(self):
        return int(self.count*self.price)
    
    def display(self):
        x = ("<td>"+self.name+"</td><td>"+str(self.count)+"</td><td>"+str(self.price)+"</td><td>"+str(self.count*self.price)+"</td><td>"+ "<p><label class='btn' for='"+self.name+"'>Edit</label></p>"+"</td>")
        return x
'''
item1 = ShoppingCart("Route System", 1, 5)
item2 = ShoppingCart("Route System", 1, 5)
item1.add(3)
del item1
item2.display()
connection = pymysql.connect(host = 'localhost', 
    user = 'root',
    password = 'fiona0830', 
    db = '205CDE', 
    local_infile = 1,
    cursorclass=pymysql.cursors.DictCursor)
cursor = connection.cursor()
cart = []

cursor.execute("SELECT * FROM product")
product = cursor.fetchall()
for e in product:
    cart.append(ShoppingCart(e['productName'], 0, e['prodPrice']))
    cart.append(ShoppingCart(e['productName'], 1, e['prodPrice']))

list=[]
for e in cart:
    if int(e.count) != 0:
        list.append(e.display())

for e in list:
    print(e)
'''
