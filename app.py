from  flask import Flask , render_template, request , redirect , flash
from flask_sqlalchemy import SQLAlchemy
import sqlite3
from datetime import datetime
app = Flask(__name__, template_folder='template')

app.config['SQLALCHEMY_DATABASE_URI']= 'sqlite:///test.db'

db = SQLAlchemy(app)

class Product(db.Model):
    product_id = db.Column(db.Integer, primary_key=True)
    product_name = db.Column(db.String, nullable=False)
    Quantity = db.Column(db.Integer , default=0)
    unallocted = db.Column(db.Integer)
    

    def __repr__(self):
        return '<product %r>' % self.Quantity

#creating data model for product table 

class Location(db.Model):
    location_id = db.Column(db.Integer, primary_key=True)
    location = db.Column(db.String, nullable=False)

    def __repr__(self):
        return  self.location_id

# creating model for movement table
class mapping(db.Model):
    trans_id= db.Column(db.Integer, primary_key = True)
    prod_quantity = db.Column(db.Integer, nullable = False)
    product_id = db.Column(db.Integer, db.ForeignKey('product.product_id'), nullable=False)
    from_loc = db.Column(db.Integer, db.ForeignKey('location.location_id'))
    to_loc = db.Column(db.Integer, db.ForeignKey('location.location_id'))
    date_created = db.Column(db.DateTime, default=datetime.utcnow())
    product = db.relationship("Product")
    location = db.relationship("Location", foreign_keys=[to_loc])
    location_for = db.relationship("Location", foreign_keys=[from_loc])

  



###############################################################################################################
# for product 
###############################################################################################################
@app.route("/product", methods=['POST','GET'])
def index():
    msg=None
    #tasks=None
    if request.method=='POST' and request.form['productname'] not in [None , '' , ' '] and request.form['quant'] not in [None , '' , ' ']:
        name =  request.form['productname']
        qant = request.form['quant']
        new_product = Product(product_name = name, Quantity = qant,unallocted=qant )
        try:
            db.session.add(new_product)
            db.session.commit()
            return redirect('/product')
        except sqlite3.Error as e:
            print("=== ", e)
            return 'There is some issue in adding new product. '    
       
    elif request.method=='POST' and (request.form['productname'] in [None , '' , ' '] or request.form['quant'] in [None , '' , ' ']):    
        tasks = Product.query.order_by(Product.product_id).all()
        msg="Fields are required !!!"
        return render_template('index.html', tasks=tasks,msg=msg)
    else:
        tasks = Product.query.order_by(Product.product_id).all()
        return render_template('index.html', tasks=tasks)

# To delete a product  
@app.route('/product/delprod/<int:id>')
def deleteProduct(id):
    product_to_delete = Product.query.get_or_404(id)
    try:
        db.session.delete(product_to_delete)
        db.session.commit()
        return redirect('/product')
    except:
        return 'There is an problem in deleting the product. '


# To update a product with product id
@app.route('/product/updateprod/<int:id>',methods=['POST','GET'])
def updateProduct(id):
     msg= None
     tasks = Product.query.get_or_404(id)
     if request.method=='POST' and request.form['productname'] not in [None,'',' '] and request.form['quant'] not in [None,'',' ']:
         tasks.product_name= request.form['productname']
         qnt= int(request.form['quant'])
         tasks.unallocted = tasks.unallocted + qnt - tasks.Quantity
         tasks.Quantity= request.form['quant']

         try:
             db.session.commit()
             return redirect('/product')
         except:
             return 'There is an issue addinh your task. '
     elif request.method=='POST' and (request.form['productname'] not in [None,'',' '] or request.form['quant'] not in [None,'',' ']):
         msg="Fields are required !!!"
         return render_template('updateProduct.html', task=tasks,msg=msg)
     else:
         return render_template('updateProduct.html', task=tasks)



###############################################################################################################
# for location 
###############################################################################################################

@app.route("/location", methods=['POST','GET'])
def location():
    msg= None
    if request.method=='POST' and request.form['locationname'] not in [None, '', ' ']:
        name =  request.form['locationname']
        new_location= Location(location= name)
        try:
            db.session.add(new_location)
            db.session.commit()
            return redirect('/location')
        except:
            return 'There is some issue in adding new location. '    
    elif request.method=='POST' and request.form['locationname'] in [None, '', ' ']:
        msg="This field is required!!!!!"
        tasks = Location.query.order_by(Location.location_id).all()
        return render_template('location.html', tasks=tasks, msg=msg)

    else:
        tasks = Location.query.order_by(Location.location_id).all()
        return render_template('location.html', tasks=tasks)

# To delete a location
@app.route('/dellocation/<int:id>')
def deleteLocation(id):
    location_to_del =  Location.query.get_or_404(id)
    try:
        db.session.delete(location_to_del)
        db.session.commit()
        return redirect('/location')
    except:
        return 'Unable to delete location. '

# To update a location with location id
@app.route('/updatelocation/<int:id>', methods=['GET','POST'])
def updateLocation(id):
    msg=None
    location_to_update =Location.query.get_or_404(id) 
    if request.method == 'POST' and (request.form['location'] not in  [None, '', ' ']):
        location_to_update.location=request.form['location']
        try:
            db.session.commit()
            return redirect('/location')
        except:
            return 'Unable to update .'
    elif request.method == 'POST' and request.form['location'] in  [None, '', ' ']:
        msg="This field is required"
        return render_template('updateLocation.html', task=location_to_update,msg=msg)

    else:
        return render_template('updateLocation.html', task=location_to_update)

###############################################################################################################
# for movement of product
###############################################################################################################
@app.route("/management", methods=["GET","POST"])
def managementInventory():
    msg = None
    mapping_summary = None
    conn = sqlite3.connect('test.db',detect_types=sqlite3.PARSE_DECLTYPES)
    cur = conn.cursor()
    cur.execute('SELECT product_id,product_name, Quantity FROM product ORDER BY product_id')
    product = cur.fetchall()
    cur.execute('SELECT location_id , location FROM location ORDER BY location')
    locations = cur.fetchall()
    if request.method=='GET':

        cur.execute('SELECT * FROM mapping') 
        mapping_summary = cur.fetchall()        
        log_summary = []
        for p_id in [x[0] for x in product]:
            cur.execute("SELECT product_name FROM product WHERE product_id = ?", (p_id, ))
            temp_prod_name = cur.fetchone()
            
            for l_id in [x[0] for x in locations]:
                cur.execute("SELECT location FROM location WHERE location_id = ?", (l_id,))
                temp_loc_name = cur.fetchone()
               
                cur.execute("""
                SELECT SUM(log.prod_quantity)
                FROM mapping log
                WHERE log.product_id = ? AND log.to_loc = ?
                """, (p_id, l_id))
                sum_to_loc = cur.fetchone()
                
                cur.execute("""
                SELECT SUM(log.prod_quantity)
                FROM mapping log
                WHERE log.product_id = ? AND log.from_loc = ?
                """, (p_id, l_id))
                sum_from_loc = cur.fetchone()
              
                cur.execute("""
                SELECT *
                FROM mapping  """)
               

                if sum_from_loc[0] is None:
                    sum_from_loc = (0,)
                if sum_to_loc[0] is None:
                    sum_to_loc = (0,)
                # print("individual values==")
                # print([(temp_prod_name + temp_loc_name + (sum_to_loc[0],))])
                # print([(temp_prod_name + temp_loc_name + (sum_from_loc[0],))])
                log_summary += [(temp_prod_name + temp_loc_name + (sum_to_loc[0] - sum_from_loc[0],))]
        #print(" log_summary == ",log_summary)

    elif request.method == 'POST'  and request.form['product'] not in [None,'',' '] and request.form['quantity'] not in [None,'',' '] :
        product_selected= request.form['product']
        from_loc = request.form['from_loc']
        to_loc = request.form['to_loc']
        quant_selected = int(request.form['quantity'])

        if from_loc in [None, '',' ']:

            try:
                cur.execute("""
                            select unallocted from product where product_name = ? """,(product_selected,))
                prod_unallocation_count = cur.fetchone()
                if prod_unallocation_count[0] >= quant_selected:

                    cur.execute("""Insert into mapping(product_id , to_loc, prod_quantity,date_created)
                            SELECT product.product_id, location.location_id, ? ,?
                            FROM product, location 
                            WHERE product.product_name == ? AND location.location == ?""",(quant_selected, datetime.utcnow(),product_selected, to_loc))
                    
                    cur.execute(""" update product
                            set unallocted = unallocted - ? where product_name == ? """,(quant_selected,product_selected ))    
                else:
                    msg=" No enough products are left to allocate."

                
            except sqlite3.Error as e:
                msg= f"An error occurred: {e.args[0]}"
                print("msg from  ==", msg)
            

        elif to_loc in [None, '',' ']:
            cur.execute("select location_id from location where location =?",(from_loc,))
            from_loc_selected= ''.join([str(x[0]) for x in cur.fetchall()])
            cur.execute("select product_id from product where product_name =?",(product_selected,))
            product_id_select = ''.join([str(x[0]) for x in cur.fetchall()])
            cur.execute("select prod_quantity from mapping where product_id == ? AND to_loc == ? ",(product_id_select,from_loc_selected))
            product_allocated_mapping_amount  = cur.fetchone()
            try:
                if product_allocated_mapping_amount[0] not in [None,'',' '] and product_allocated_mapping_amount[0] >= quant_selected:  
                    print("inside the condiotion")                      
                    cur.execute("""Insert into mapping(product_id , from_loc, prod_quantity,date_created )
                            SELECT product.product_id, location.location_id, ? ,?
                            FROM product, location 
                            WHERE product.product_name == ? AND location.location == ?""",(quant_selected,datetime.utcnow(), product_selected, from_loc))

                    # cur.execute(""" update mapping set prod_quantity = prod_quantity - ? where product_id = ? AND to_loc = ?""",(quant_selected ,product_id_select,from_loc_selected))
                    cur.execute(""" update product set unallocted = unallocted + ? where product_name == ? """,(quant_selected,product_selected ))
                else:
                    msg="No enough quantity is present at this location."
                    print(msg)
            except sqlite3.Error as e:
                msg= f"An error occurred: {e.args[0]}"
                print("msg from to ==", msg)
           
        elif from_loc not in [None, '',' '] and to_loc not in [None, '',' ']:
            cur.execute("select location_id from location where location =?",(to_loc,))
            to_loc= ''.join([str(x[0]) for x in cur.fetchall()])
            cur.execute("select location_id from location where location =?",(from_loc,))
            from_loc= ''.join([str(x[0]) for x in cur.fetchall()])
            cur.execute("select product_id from product where product_name =?",(product_selected,))
            product_selected_id = ''.join([str(x[0]) for x in cur.fetchall()])
            cur.execute(""" select prod_quantity from mapping where product_id =?  and to_loc= ? """,[product_selected_id,from_loc])
            total_amount =  cur.fetchone()

            try:
                if total_amount[0] >= quant_selected:
                    cur.execute(""" Insert into mapping(product_id, to_loc,from_loc, prod_quantity,date_created)values(?,?,?,?,?) """, 
                    ( product_selected_id,to_loc,from_loc,quant_selected, datetime.utcnow()))

                    cur.execute(""" update mapping set prod_quantity = prod_quantity-? where product_id = ? and to_loc =?  """,(quant_selected,product_selected,from_loc))
                else:
                    msg=" Movement can't be possible from warehouse to warehouse."    
            except sqlite3.Error as e:
                msg= f"An error occurred: {e.args[0]}"
                print("msg from both ==", msg)

        elif from_loc  in [None, '',' '] and to_loc  in [None, '',' ']:
            msg="This fields required!!!!!!!!!!!"
    elif request.method == 'POST'  and (request.form['product']  in [None,'',' '] or request.form['quantity']  in [None,'',' '] ):    
             msg="This fields required!!!!!!!!!!!"

    if msg:
        print("====",msg)
        return redirect('/management')
    conn.commit()    
    return render_template('movement.html', logSummary=log_summary,product=product,locations=locations, mapping_summary=mapping_summary, msg=msg)

@app.route("/")
def Summary():
    msg=None
    conn = sqlite3.connect('test.db')
    cur = conn.cursor()
    try:

        cur.execute('Select * from location')
        location_info = cur.fetchall()
        print("location--------", location_info)
        cur.execute('select product_id , product_name, Quantity from product')
        product_info = cur.fetchall()
        cur.execute('Select product_name , Quantity, unallocted from product')
        unallocation_info = cur.fetchall()


    except sqlite3.Error as e:
        msg = f"An error occurred: {e.args[0]}"
    if msg:
        print(msg)
    #print(location_info)
    return render_template("summary.html", loc=location_info, prod= product_info, unallocate= unallocation_info)

            
if __name__=="__main__":
    app.run(debug=True)