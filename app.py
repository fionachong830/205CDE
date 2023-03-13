from flask import Flask, request, render_template, redirect
from flask_bootstrap import Bootstrap
import pymysql
import os
from flask_mail import Mail, Message
from distutils.log import debug
from fileinput import filename
from ShoppingCart import ShoppingCart

app = Flask(__name__)
cart=[]
app.config.update(
    DEBUG=False,
    MAIL_SERVER='smtp.gmail.com',
    MAIL_PORT=465,
    MAIL_USE_SSL=True,
    MAIL_DEFAULT_SENDER=('admin', os.environ.get('MAIL_USERNAME')),
    MAIL_MAX_EMAILS=10,
    MAIL_USERNAME=os.environ.get('MAIL_USERNAME') ,
    MAIL_PASSWORD=os.environ.get('MAIL_PASSWORD')
)
mail = Mail(app)
ALLOWED_EXTENSIONS = {'pdf', 'png', 'jpg', 'jpeg'}

bootstrap = Bootstrap(app)
connection = pymysql.connect(host = 'localhost', 
    user = 'root',
    password = 'fiona0830', 
    db = '205CDE', 
    local_infile = 1,
    cursorclass=pymysql.cursors.DictCursor)
cursor = connection.cursor()

def initial(id):
    cursor.execute("SELECT * FROM product")
    product = cursor.fetchall()
    for e in product:
        cart.append(ShoppingCart(id, e['prodID'], e['productName'], 0, e['prodPrice']))    

def checkLoginStatus(id):
    sql = 'SELECT loginStatus from userInfo WHERE userID={id}'
    cursor.execute(sql.format(id=id))
    data = cursor.fetchall()
    for e in data:
        if e['loginStatus']== 1:
            return True
        else: 
            return False

def updateStatus():
    cursor.execute('UPDATE subscription SET subStatus="Expired" WHERE subEnd < curdate()')
    connection.commit()
 
def getUserInfo(id):
    updateStatus()
    sql = 'SELECT *, SUBSTRING(name, 1, 1) AS sName from userInfo WHERE userID={id}'
    cursor.execute(sql.format(id=id))
    user = cursor.fetchall()
    return user

@app.route("/")
def home():
    return render_template('login.html')

@app.route("/login", methods=['POST', 'GET'])
def login():
    if request.method == 'POST':
        userName = request.form['userName']
        password = request.form['password']
        accType = request.form['accType']
        sql = 'SELECT userID, password from userInfo WHERE userName="{userName}" and role="{accType}"'
        cursor.execute(sql.format(userName=userName, accType=accType))
        result = cursor.fetchall()
        for i in result: 
            if i['password'] == password:
                id = i['userID']
                sql = 'UPDATE userInfo set loginStatus=1 where userID={id};'
                cursor.execute(sql.format(id=id))
                connection.commit()
                if accType=="C":
                    initial(id)
                    return redirect('/customer/{id}/dashboard'.format(id=id))
                else: 
                    return redirect('/staff/{id}/dashboard'.format(id=id))
            else: 
                return render_template('login.html', status='fail')
        return render_template('login.html', status='fail')
    else:
        return render_template('login.html')

@app.route("/signup", methods=['POST', 'GET'])
def signup():
    if request.method == 'POST':
        name = request.form['name']
        phoneNo = request.form['phoneNo']
        email = request.form['email']
        userName = request.form['userName']
        password = request.form['password']
        confirmPassword = request.form['confirmPassword']
        if confirmPassword == password:
            cursor.execute('SELECT * FROM userInfo')
            result = cursor.fetchall()
            for i in result:
                if i['userName'] == userName:
                    return render_template('signup.html', status='usernamedup')
                if i['phoneNo'] == phoneNo:
                    return render_template('signup.html', status='phoneNodup')
                if i['email'] == email:
                    return render_template('signup.html', status='emaildup')                
            insertsql='INSERT INTO userInfo(userName, password, name, phoneNo, email, role, loginStatus) VALUES ("{userName}", "{password}", "{name}", "{phoneNo}", "{email}", "C", 1)'
            cursor.execute(insertsql.format(userName=userName, password=password, name=name, phoneNo=phoneNo, email=email))
            connection.commit()
            sql = 'SELECT userID from userInfo WHERE userName="{userName}"'
            cursor.execute(sql.format(userName=userName))
            result = cursor.fetchall()
            for i in result: 
                id = i['userID']
            initial(id)
            return redirect('/customer/{id}/dashboard'.format(id=id))
        else:
            return render_template('signup.html', status='invalidConfirmPassword')
    else:
        return render_template('signup.html', status=None)

@app.route("/forgotPassword")
def forgotPassword():
    return render_template('forgotPassword.html')

@app.route("/forgotPassword/email", methods=['POST'])
def password():
    phoneNo = request.form['phoneNo'].strip()
    email = request.form['email'].strip()
    sql = 'SELECT * from userInfo WHERE email="{email}"'
    cursor.execute(sql.format(email=email))
    result = cursor.fetchall()
    for i in result: 
        print(i['phoneNo'])
        if int(i['phoneNo']) == int(phoneNo):   
            subject = 'Forget password'
            message = 'Your Username: {username} <br> <br>' \
                'Your Password: {password}<br> <br>'. format(username=i['userName'] , password=i['password'] )
            msg = Message(
                subject=subject,
                recipients=[email],
                html=message
            )
            mail.send(msg)
            return render_template('forgotPassword.html', status='sent')  
        else: 
            return render_template('forgotPassword.html', status='fail')
        
@app.route("/product")
def productGuest():
    cursor.execute("SELECT * FROM product")
    product = cursor.fetchall()
    return render_template('productGuest.html', product=product)

@app.route("/<int:id>/logout", methods=['GET'])
def logout(id):
    sql = 'UPDATE userInfo set loginStatus=0 where userID={id};'
    cursor.execute(sql.format(id=id))
    connection.commit()
    cart = []
    return render_template('login.html')

"Customer app route"
@app.route("/customer/<int:id>/dashboard", methods=['POST', 'GET'])
def cusDashboard(id):
    if checkLoginStatus(id) == True:
        sql = '''    
        select *, DATEDIFF(subscription.subEnd, CURDATE()) as remaining 
        from product, subscription, userInfo
        where product.prodID=subscription.prodID and userInfo.userID=subscription.userID and userInfo.userID={id}
        '''
        cursor.execute(sql.format(id=id))
        data = cursor.fetchall()
        cursor.execute("SELECT * FROM product")
        product = cursor.fetchall()
        user = getUserInfo(id)
        if request.method == 'POST':
            prodID = request.form['prodID']
            days = request.form['days']
            for e in cart:
                if e.cid == id: 
                    if int(e.id) == int(prodID):
                        e.add(days)        
        return render_template('cusDashboard.html', product=product, data=data, user=user)
    else: 
        return render_template('404.html'), 404

@app.route("/customer/<int:id>/dashboard/<int:prodid>", methods=['GET'])
def cusDashboardDetails(id, prodid):
    if checkLoginStatus(id) == True:
        sql = '''    
        select * from subHistory, product, payment 
        where product.prodID=subHistory.prodID and subHistory.payID=payment.payID and subHistory.userID={id} and subHistory.prodID={prodid}
        '''
        cursor.execute(sql.format(id=id, prodid=prodid))
        data = cursor.fetchall()  
        cursor.execute('SELECT productName from product where prodID={prodid}'.format(prodid=prodid))
        prodName = cursor.fetchall() 
        user = getUserInfo(id)
        return render_template('cusDashboardDetails.html', data=data, user=user, prodName=prodName)
    else: 
        return render_template('404.html'), 404

@app.route("/customer/<int:id>/product", methods=['POST', 'GET'])
def cusProduct(id):
    if checkLoginStatus(id) == True:    
        cursor.execute("SELECT * FROM product")
        product = cursor.fetchall()
        user = getUserInfo(id)
        if request.method == 'POST':
            prodID = request.form['prodID']
            days = request.form['days']
            for e in cart:
                if e.cid == id:
                    if int(e.id) == int(prodID):
                        e.add(days)
        return render_template('cusProduct.html', product=product, user=user)
    else: 
        return render_template('404.html'), 404

@app.route("/customer/<int:id>/buy", methods=['POST', 'GET'])
def cusBuy(id):
    if checkLoginStatus(id) == True:    
        if request.method == 'POST':
            sql = 'insert into payment(payAmount,userID) values ({amount}, {id})'
            cursor.execute(sql.format(amount=ShoppingCart.total, id=id))
            connection.commit()
            cursor.execute("SELECT payID FROM payment ORDER BY payID DESC LIMIT 1")
            payInfo=cursor.fetchall()
            for e in payInfo:
                payID = e['payID']
                for e in cart:
                    if e.cid == id:
                        if e.count != 0:
                            sql = 'insert into subHistory(subHDay, payID, subAmount,userID, prodID) values({subHDay}, {payID}, {subAmount}, {userID}, {prodID});'
                            cursor.execute(sql.format(subHDay=e.count, payID=payID, subAmount=e.subtotal(), userID=id, prodID=e.id))
                            connection.commit()
            for e in cart:
                e.clear()
            sql = '''    
            select * from subHistory, product, payment
            where product.prodID=subHistory.prodID and subHistory.payID=payment.payID and payment.payID={pid}
            '''
            cursor.execute(sql.format(pid=payID))
            data = cursor.fetchall()   
            user = getUserInfo(id)
            return render_template('cusUploadDocumentDetails.html', data=data, user=user)
        else: 
            cursor.execute("SELECT * FROM product")
            product = cursor.fetchall()
            user = getUserInfo(id)
            return render_template('cusProduct.html', product=product, user=user)
    else: 
        return render_template('404.html'), 404

@app.route("/customer/<int:id>/subscriptionHistory", methods=['GET'])
def cusSubscriptionHistory(id):
    if checkLoginStatus(id) == True: 
        sql = '''    
        select * from subHistory, product, payment
        where product.prodID=subHistory.prodID and subHistory.payID=payment.payID and subHistory.userID={id}
        order by subHID
        '''
        cursor.execute(sql.format(id=id))
        data = cursor.fetchall()   
        user = getUserInfo(id)
        return render_template('cusSubscriptionHistory.html', data=data, user=user)

@app.route("/customer/<int:id>/uploadDocument", methods=['GET'])
def cusUploadDocument(id):
    if checkLoginStatus(id) == True:  
        sql = '''    
        select * from payment
        where userID={id} and payStatus != "Approved"
        '''
        cursor.execute(sql.format(id=id))
        data = cursor.fetchall() 
        user = getUserInfo(id)
        return render_template('cusUploadDocument.html', data=data, user=user, status=None)
    else: 
        return render_template('404.html'), 404

@app.route("/customer/<int:id>/uploadDocument/submit", methods=['POST','GET'])
def cusUploadDocumentSubmit(id):
    if checkLoginStatus(id) == True:  
        UPLOAD_FOLDER = '/Users/fionachong/Library/CloudStorage/OneDrive-個人/2223 Sem2/205CDE/205CDE VS/tryflask/static/uploadDoc'
        app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
        user = getUserInfo(id)
        if request.method == 'POST':
            payID = request.form['payID']  
            payDoc = request.files['payDoc']
            payDoc.save(os.path.join(app.config['UPLOAD_FOLDER'], payDoc.filename))
            sql = 'UPDATE payment SET payDoc="{doc}", payStatus="Pending for Approval" WHERE payID={payID}'
            cursor.execute(sql.format(payID=payID, doc=payDoc.filename))
            connection.commit()
            sql = 'UPDATE subHistory SET subHstatus="Pending for Approval" WHERE payID={payID}'
            cursor.execute(sql.format(payID=payID))
            connection.commit()
        sql = '''    
        select * from payment
        where userID={id}
        '''
        cursor.execute(sql.format(id=id))
        data = cursor.fetchall() 
        return render_template('cusUploadDocument.html', data=data, user=user, status='success')
    else: 
        return render_template('404.html'), 404
    
@app.route("/customer/<int:id>/uploadDocument/<int:pid>", methods=['POST','GET'])
def cusSubscriptionDetails(id, pid):
    if checkLoginStatus(id) == True: 
        if request.method == 'POST':
            payID = request.form['payID']  
            payDoc = request.form['payDoc']
        sql = '''    
        select * from subHistory, product, payment
        where product.prodID=subHistory.prodID and subHistory.payID=payment.payID and payment.payID={pid}
        '''
        cursor.execute(sql.format(pid=pid))
        data = cursor.fetchall()   
        user = getUserInfo(id)
        return render_template('cusUploadDocumentDetails.html', data=data, user=user)
    
@app.route("/customer/<int:id>/shoppingCart", methods=['POST', 'GET'])
def cusShoppingCart(id):
    if checkLoginStatus(id) == True:
        user = getUserInfo(id)
        if request.method == 'POST':
            prodID = request.form['prodID']
            days = request.form['days']
            for e in cart:
                if e.cid == id:
                    if int(e.id) == int(prodID):
                        e.update(days)        
        list=[]
        x = 0
        for e in cart:
            if e.cid == id:
                if e.count != 0:
                    list.append(e)
                    x += 1 
        total = ShoppingCart.total
        cursor.execute("SELECT * FROM product")
        if x == 0:
            return render_template('cusShoppingCart.html', user=user, status='Empty')
        else:
            return render_template('cusShoppingCart.html', user=user, list=list, total=total)
    else: 
        return render_template('404.html'), 404

@app.route("/customer/<int:id>/personalInfo", methods=['POST','GET'])
def cusPersonalInfo(id):
    if checkLoginStatus(id) == True:
        user = getUserInfo(id)
        if request.method == 'POST':
            name = request.form['name']
            phoneNo = request.form['phoneNo']
            email = request.form['email']
            userName = request.form['userName']
            sql = 'SELECT * FROM userInfo WHERE userID!={id}'
            cursor.execute(sql.format(id=id))
            result = cursor.fetchall()
            for i in result:
                if i['userName'] == userName:
                    return render_template('cusPersonalInfo.html', user=user, status='usernamedup')
                if int(i['phoneNo']) == int(phoneNo):
                    return render_template('cusPersonalInfo.html', user=user, status='phoneNodup')
                if i['email'] == email:
                    return render_template('cusPersonalInfo.html', user=user, status='emaildup')                
            sql='UPDATE userInfo SET userName="{userName}", name="{name}", phoneNo={phoneNo}, email="{email}" WHERE userID={id}'
            cursor.execute(sql.format(userName=userName, name=name, phoneNo=phoneNo, email=email, id=id))
            connection.commit()
            user = getUserInfo(id)
            return render_template('cusPersonalInfo.html', user=user, status='success')
        else:
            return render_template('cusPersonalInfo.html', user=user, status='None')
    else: 
        return render_template('404.html'), 404

@app.route("/customer/<int:id>/changePassword", methods=['POST','GET'])
def cusChangePassword(id):
    if checkLoginStatus(id) == True:
        user = getUserInfo(id)
        if request.method == 'POST':
            password = request.form['password']
            confirmPassword = request.form['confirmPassword']
            if password == confirmPassword:
                sql='UPDATE userInfo SET password="{password}" WHERE userID={id}'
                cursor.execute(sql.format(password=password, id=id))
                connection.commit()
                return render_template('cusChangePassword.html', user=user, status='success')   
            else: 
                return render_template('cusChangePassword.html', user=user, status='fail')         
        else:
            return render_template('cusChangePassword.html', user=user, status='None')
    else: 
        return render_template('404.html'), 404
    
@app.route("/customer/<int:id>/helpSupport",  methods=['POST','GET'])
def cusHelpSupport(id):
    if checkLoginStatus(id) == True:
        user = getUserInfo(id)
        cursor.execute("SELECT * FROM product")
        product = cursor.fetchall()
        sql = '''    
        select * from subHistory where userID={id}
        '''
        cursor.execute(sql.format(id=id))
        data = cursor.fetchall()  
        if request.method == 'POST':
            session = request.form['session']
            question = request.form['question']
            subHID = request.form['subHID']
            if subHID == "None":
                insertsql='INSERT INTO inquiry(userID, session, question) VALUES ({id}, "{session}", "{question}")'
                cursor.execute(insertsql.format(id=id, session=session, question=question))
            else:
                insertsql='INSERT INTO inquiry(userID, session, question, subHID) VALUES ({id}, "{session}", "{question}", {subHID})'
                cursor.execute(insertsql.format(id=id, session=session, question=question, subHID=subHID))
            connection.commit()
            return render_template('cusHelpSupport.html', user=user, data=data, product=product, status='success')
        else:
            return render_template('cusHelpSupport.html', user=user, data=data, product=product)
    else: 
        return render_template('404.html'), 404
    
"Staff app route"
@app.route("/staff/<int:id>/dashboard", methods=['GET'])
def staffDashboard(id):
    if checkLoginStatus(id) == True:
        sql = '''    
        select *, DATEDIFF(subscription.subEnd, CURDATE()) as remaining 
        from product, subscription, userInfo
        where product.prodID=subscription.prodID and userInfo.userID=subscription.userID
        '''
        cursor.execute(sql)
        data = cursor.fetchall()
        cursor.execute("SELECT * FROM product")
        product = cursor.fetchall()
        user = getUserInfo(id)
        return render_template('staffDashboard.html', product=product, data=data, user=user)
    else: 
        return render_template('404.html'), 404

@app.route("/staff/<int:id>/dashboard/<int:cid>/<int:prodid>", methods=['GET'])
def  staffDashboardDetails(id, prodid, cid):
    if checkLoginStatus(id) == True:
        sql = '''    
        select * from subHistory, product, payment
        where product.prodID=subHistory.prodID and subHistory.payID=payment.payID and subHistory.userID={cid} and subHistory.prodID={prodid}
        '''
        cursor.execute(sql.format(cid=cid, prodid=prodid))
        data = cursor.fetchall()  
        cursor.execute('SELECT productName from product where prodID={prodid}'.format(prodid=prodid))
        prodName = cursor.fetchall() 
        cursor.execute('SELECT name from userInfo where userID={cid}'.format(cid=cid))
        cusName = cursor.fetchall() 
        user = getUserInfo(id)
        return render_template('staffDashboardDetails.html', data=data, user=user, prodName=prodName, cusName=cusName)
    else: 
        return render_template('404.html'), 404
  
@app.route("/staff/<int:id>/updateProduct", methods=['GET'])
def staffUpdateProduct(id):
    if checkLoginStatus(id) == True:
        user = getUserInfo(id)
        cursor.execute("SELECT * FROM product")
        product = cursor.fetchall()
        return render_template('staffUpdateProduct.html', user=user, product=product, status=None)
    else: 
        return render_template('404.html'), 404
    
@app.route("/staff/<int:id>/updateProduct/submit", methods=['POST', 'GET'])
def staffUpdateProductSubmit(id):
    if checkLoginStatus(id) == True:
        user = getUserInfo(id)
        UPLOAD_FOLDER = '/Users/fionachong/Library/CloudStorage/OneDrive-個人/2223 Sem2/205CDE/205CDE VS/tryflask/static/product'
        app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
        if request.method == 'POST':
            prodID = request.form['prodID']
            productName = request.form['productName']
            prodDescr = request.form['prodDescr']
            prodLink = request.form['prodLink']
            prodPrice = request.form['prodPrice']  
            cursor.execute('SELECT * FROM product WHERE prodID != {prodID}'.format(prodID=prodID))
            existingName = cursor.fetchall()
            for e in existingName:
                if e['productName'] == productName:
                    cursor.execute("SELECT * FROM product")
                    product = cursor.fetchall()
                    return render_template('staffUpdateProduct.html', user=user, product=product, status='namedup')
            sql = 'UPDATE product SET productName="{productName}", prodDescr="{prodDescr}", prodLink="{prodLink}",prodPrice="{prodPrice}" WHERE prodID={prodID}'
            cursor.execute(sql.format(prodID=prodID, productName=productName, prodDescr=prodDescr, prodLink=prodLink, prodPrice=prodPrice))
            connection.commit()
        cursor.execute("SELECT * FROM product")
        product = cursor.fetchall()
        return render_template('staffUpdateProduct.html', user=user, product=product, status='success')
    else: 
        return render_template('404.html'), 404

@app.route("/staff/<int:id>/updateProduct/submitpic", methods=['POST', 'GET'])
def staffUpdateProductSubmitPic(id):
    if checkLoginStatus(id) == True:
        user = getUserInfo(id)
        UPLOAD_FOLDER = '/Users/fionachong/Library/CloudStorage/OneDrive-個人/2223 Sem2/205CDE/205CDE VS/tryflask/static/product'
        app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
        if request.method == 'POST':
            prodID = request.form['prodID']
            prodImg = request.files['prodImg']
            prodImg.save(os.path.join(app.config['UPLOAD_FOLDER'], prodImg.filename))
            sql = 'UPDATE product SET prodImg="{prodImg}" WHERE prodID={prodID}'
            cursor.execute(sql.format(prodID=prodID, prodImg=prodImg.filename))
            connection.commit()
        cursor.execute("SELECT * FROM product")
        product = cursor.fetchall()
        return render_template('staffUpdateProduct.html', user=user, product=product, status='success')
    else: 
        return render_template('404.html'), 404
    
@app.route("/staff/<int:id>/addProduct", methods=['GET'])
def staffAddProduct(id):
    if checkLoginStatus(id) == True:
        user = getUserInfo(id)
        return render_template('staffAddProduct.html', user=user)
    else: 
        return render_template('404.html'), 404

@app.route("/staff/<int:id>/addProduct/submit", methods=['POST', 'GET'])
def staffAddProductSubmit(id):
    if checkLoginStatus(id) == True:
        user = getUserInfo(id)
        UPLOAD_FOLDER = '/Users/fionachong/Library/CloudStorage/OneDrive-個人/2223 Sem2/205CDE/205CDE VS/tryflask/static/product'
        app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
        if request.method == 'POST':
            productName = request.form['productName']
            prodDescr = request.form['prodDescr']
            prodLink = request.form['prodLink']
            prodPrice = request.form['prodPrice']  
            prodImg = request.files['prodImg']
            cursor.execute('SELECT productName FROM product')
            existingName = cursor.fetchall()
            for e in existingName:
                if e['productName'] == productName:
                    return render_template('staffAddProduct.html', user=user, status='namedup')
            prodImg.save(os.path.join(app.config['UPLOAD_FOLDER'], prodImg.filename))
            sql = 'INSERT INTO product(productName,prodDescr, prodLink, prodPrice, prodImg) VALUES ("{productName}", "{prodDescr}", "{prodLink}", {prodPrice}, "{prodImg}")'
            cursor.execute(sql.format(productName=productName, prodDescr=prodDescr, prodLink=prodLink, prodPrice=prodPrice, prodImg=prodImg.filename))
            connection.commit()
        cursor.execute("SELECT * FROM product")
        product = cursor.fetchall()
        return render_template('staffAddProduct.html', user=user, status='success')
    else: 
        return render_template('404.html'), 404

@app.route("/staff/<int:id>/history", methods=['GET'])
def staffHistory(id):
    if checkLoginStatus(id) == True: 
        sql = '''    
        select * from subHistory, product, payment
        where product.prodID=subHistory.prodID and subHistory.payID=payment.payID
        '''
        cursor.execute(sql)
        data = cursor.fetchall()   
        user = getUserInfo(id)
        return render_template('staffHistory.html', data=data, user=user)
    else: 
        return render_template('404.html'), 404
    
@app.route("/staff/<int:id>/approverCorner", methods=['GET'])
def staffApproverCorner(id):
    if checkLoginStatus(id) == True:
        user = getUserInfo(id)
        cursor.execute('select * from payment where payDoc is not null and payStatus != "Approved"')
        data = cursor.fetchall() 
        return render_template('staffApproverCorner.html', user=user, data=data)
    else: 
        return render_template('404.html'), 404

@app.route("/staff/<int:id>/approverCorner/submit", methods=['POST', 'GET'])
def staffApproverCornerSubmit(id):
    if checkLoginStatus(id) == True:
        user = getUserInfo(id)
        if request.method == 'POST':
            payID = request.form['payID']
            status = request.form['status']
            sql = 'UPDATE payment SET payStatus="{status}", confirmBy={id}, confirmDate=curdate() WHERE payID={payID}'
            cursor.execute(sql.format(payID=payID, status=status, id=id))
            connection.commit()
            sql = 'UPDATE subHistory SET subHstatus="{status}" WHERE payID={payID}'
            cursor.execute(sql.format(payID=payID, status=status))
            connection.commit()
            sql = 'SELECT * FROM subHistory WHERE payID={payID}'
            cursor.execute(sql.format(payID=payID))
            sub = cursor.fetchall()
            for e in sub:
                sql = 'SELECT * FROM subscription WHERE userID={id} AND prodID={prodID}'
                cursor.execute(sql.format(prodID=e['prodID'], id=e['userID']))
                current = cursor.fetchall()
                if current == ():
                    sql = 'UPDATE subHistory SET subHStart=curdate(), subHEnd=DATE_ADD(curdate(), INTERVAL subHDay DAY) WHERE subHID={subHID}'
                    cursor.execute(sql.format(subHID=e['subHID']))
                    connection.commit()
                    sql = "INSERT INTO subscription(subStart, subEnd, subStatus, userID, prodID) VALUES (curdate(), DATE_ADD(curdate(), INTERVAL {days} DAY), 'Ongoing', {id}, {prodID})"
                    cursor.execute(sql.format(days=e['subHDay'], id=e['userID'], prodID=e['prodID']))
                    connection.commit()
                else:
                    for x in current:
                        if x['subStatus'] == 'Expired':
                            sql = 'UPDATE subHistory SET subHStart=curdate(), subHEnd=DATE_ADD(curdate(), INTERVAL subHDay DAY) WHERE subHID={subHID}'
                            cursor.execute(sql.format(subHID=e['subHID']))
                            connection.commit()
                            sql = 'UPDATE subscription SET subStart=curdate(), subEnd=DATE_ADD(curdate(), INTERVAL {days} DAY), subStatus="Ongoing" WHERE subID={subID}'
                            cursor.execute(sql.format(days=e['subHDay'] , subID=x['subID']))
                            connection.commit()
                        elif x['subStatus'] == 'Ongoing':
                            sql = 'UPDATE subHistory SET subHStart=DATE_ADD("{subEnd}", INTERVAL 1 DAY), subHEnd=DATE_ADD("{subEnd}", INTERVAL {days}+1 DAY) WHERE subHID={subHID}'
                            cursor.execute(sql.format(days=e['subHDay'], subHID=e['subHID'], subEnd=x['subEnd']))
                            connection.commit()
                            sql = 'UPDATE subscription SET subEnd=DATE_ADD("{subEnd}", INTERVAL {days}+1 DAY), subStatus="Ongoing" WHERE subID={subID}'
                            cursor.execute(sql.format(days=e['subHDay'] , subID=x['subID'], subEnd=x['subEnd']))
                            connection.commit()
        cursor.execute('select * from payment where payDoc is not null and payStatus != "Approved"')
        data = cursor.fetchall() 
        return render_template('staffApproverCorner.html', user=user, data=data)
    else: 
        return render_template('404.html'), 404

@app.route("/staff/<int:id>/addAccount", methods=['POST', 'GET'])
def staffAddAccount(id):
    if checkLoginStatus(id) == True:
        user = getUserInfo(id)
        if request.method == 'POST':
            accType = request.form['accType']
            name = request.form['name']
            phoneNo = request.form['phoneNo']
            email = request.form['email']
            userName = request.form['userName']
            password = request.form['password']
            confirmPassword = request.form['confirmPassword']
            if confirmPassword == password:
                cursor.execute('SELECT * FROM userInfo')
                result = cursor.fetchall()
                for i in result:
                    if i['userName'] == userName:
                        return render_template('staffAddAccount.html',user=user, status='usernamedup')
                    if int(i['phoneNo']) == int(phoneNo):
                        return render_template('staffAddAccount.html', user=user, status='phoneNodup')
                    if i['email'] == email:
                        return render_template('staffAddAccount.html', user=user, status='emaildup')   
                if accType == "C":             
                    insertsql='INSERT INTO userInfo(userName, password, name, phoneNo, email, role, loginStatus) VALUES ("{userName}", "{password}", "{name}", "{phoneNo}", "{email}", "C", 0)'
                    cursor.execute(insertsql.format(userName=userName, password=password, name=name, phoneNo=phoneNo, email=email))
                    connection.commit()
                elif accType == "S":             
                    insertsql='INSERT INTO userInfo(userName, password, name, phoneNo, email, role, loginStatus) VALUES ("{userName}", "{password}", "{name}", "{phoneNo}", "{email}", "S", 0)'
                    cursor.execute(insertsql.format(userName=userName, password=password, name=name, phoneNo=phoneNo, email=email))
                    connection.commit()
                sql = 'SELECT userID from userInfo WHERE userName="{userName}"'
                cursor.execute(sql.format(userName=userName))
                result = cursor.fetchall()
                for i in result: 
                    id = i['userID']
                return render_template('staffAddAccount.html', user=user, status='success')
            else:
                return render_template('staffAddAccount.html', user=user, status='invalidConfirmPassword')
        else: 
            return render_template('staffAddAccount.html', user=user, status=None)
    else: 
        return render_template('staffAddAccount.html', user=user, status=None)

@app.route("/staff/<int:id>/personalInfo", methods=['POST','GET'])
def staffPersonalInfo(id):
    if checkLoginStatus(id) == True:
        user = getUserInfo(id)
        if request.method == 'POST':
            name = request.form['name']
            phoneNo = request.form['phoneNo']
            email = request.form['email']
            userName = request.form['userName']
            sql = 'SELECT * FROM userInfo WHERE userID!={id}'
            cursor.execute(sql.format(id=id))
            result = cursor.fetchall()
            for i in result:
                if i['userName'] == userName:
                    return render_template('staffPersonalInfo.html', user=user, status='usernamedup')
                if i['phoneNo'] == phoneNo:
                    return render_template('staffPersonalInfo.html', user=user, status='phoneNodup')
                if i['email'] == email:
                    return render_template('staffPersonalInfo.html', user=user, status='emaildup')                
            sql='UPDATE userInfo SET userName="{userName}", name="{name}", phoneNo={phoneNo}, email="{email}" WHERE userID={id}'
            cursor.execute(sql.format(userName=userName, name=name, phoneNo=phoneNo, email=email, id=id))
            connection.commit()
            user = getUserInfo(id)
            return render_template('staffPersonalInfo.html', user=user, status='success')
        else:
            return render_template('staffPersonalInfo.html', user=user, status='None')
    else: 
        return render_template('404.html'), 404
    
@app.route("/staff/<int:id>/changePassword", methods=['POST','GET'])
def staffChangePassword(id):
    if checkLoginStatus(id) == True:
        user = getUserInfo(id)
        if request.method == 'POST':
            password = request.form['password']
            confirmPassword = request.form['confirmPassword']
            if password == confirmPassword:
                sql='UPDATE userInfo SET password="{password}" WHERE userID={id}'
                cursor.execute(sql.format(password=password, id=id))
                connection.commit()
                return render_template('staffChangePassword.html', user=user, status='success')   
            else: 
                return render_template('staffChangePassword.html', user=user, status='fail')         
        else:
            return render_template('staffChangePassword.html', user=user, status='None')
    else: 
        return render_template('404.html'), 404

@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404

@app.errorhandler(500)
def internal_server_error(e):
    return render_template('500.html'), 500

if __name__=='__main__':
    app.run(debug=True)