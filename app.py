from flask import Flask, request, render_template
from flask_bootstrap import Bootstrap
app = Flask(__name__)
bootstrap = Bootstrap(app)

@app.route("/")
def home():
    return render_template('login.html')

@app.route("/login")
def login():
    return render_template('login.html')

@app.route("/signup")
def signup():
    return render_template('signup.html')
    
@app.route("/forgotPassword")
def forgotPassword():
    return render_template('forgotPassword.html')

@app.route("/product")
def productGuest():
    return render_template('productGuest.html')

@app.route("/logout")
def logout():
    return render_template('login.html')

"Customer app route"
@app.route("/customer/dashboard")
def cusDashboard():
    return render_template('cusDashboard.html')

@app.route("/customer/product")
def cusProduct():
    return render_template('cusProduct.html')

@app.route("/customer/subscriptionHistory")
def cusSubscriptionHistory():
    return render_template('cusSubscriptionHistory.html')

@app.route("/customer/uploadDocument")
def cusUploadDocument():
    return render_template('cusUploadDocument.html')

@app.route("/customer/shoppingCart")
def cusShoppingCart():
    return render_template('cusShoppingCart.html')

@app.route("/customer/personalInfo")
def cusPersonalInfo():
    return render_template('cusPersonalInfo.html')

@app.route("/customer/changePassword")
def cusChangePassword():
    return render_template('cusChangePassword.html')

@app.route("/customer/helpSupport")
def cusHelpSupport():
    return render_template('cusHelpSupport.html')

"Staff app route"
@app.route("/staff/dashboard")
def staffDashboard():
    return render_template('staffDashboard.html')

@app.route("/staff/updateProduct")
def staffUpdateProduct():
    return render_template('staffUpdateProduct.html')

@app.route("/staff/addProduct")
def staffAddProduct():
    return render_template('staffAddProduct.html')

@app.route("/staff/history")
def staffHistory():
    return render_template('staffHistory.html')

@app.route("/staff/approverCorner")
def staffApproverCorner():
    return render_template('staffApproverCorner.html')

@app.route("/staff/addAccount")
def staffAddAccount():
    return render_template('staffAddAccount.html')

@app.route("/staff/personalInfo")
def staffPersonalInfo():
    return render_template('staffPersonalInfo.html')

@app.route("/staff/changePassword")
def staffChangePassword():
    return render_template('staffChangePassword.html')

@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404

@app.errorhandler(500)
def internal_server_error(e):
    return render_template('500.html'), 500

if __name__=='__main__':
    app.run(debug=True)