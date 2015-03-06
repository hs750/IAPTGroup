# -*- coding: utf-8 -*-
## Exam Number: Y8185795

# Login cookies
validateUser(request)


def register():
    # User must not be logged in
    userOnly(request, False)
    return dict()

# First part of multi-part form
def registerPartOne():
    # Create form
    form = SQLFORM.factory(db.Users,submit_button='Next')
    if form.validate(keepvalues=True):
        # Store input for later
        session.storeDetails = form.vars
        # Process second part of form
        response.js = "jQuery('.signupone').hide(); jQuery('.signuptwo').show()"

    return dict(form=form)

def registerPartTwo():
    buttons = [TAG.button('Back',_type="button",_onClick = "jQuery('.signuptwo').hide(); jQuery('.signupone').show()"),
            TAG.button('Next',_type="submit")]

    # Create form
    form2 = SQLFORM.factory(db.Addresses, buttons=buttons)
    # Add a checkbox to iss if they need another address
    checkbox = TR(LABEL('Use this as my billing address'),
        INPUT(_name='combine',value=True,_type='checkbox'))
    form2[0].insert(4, checkbox)
    if form2.validate(keepvalues=True):
        # Store input for later
        session.storeAddress = form2.vars
        # Process second part of form
        print 'this should reload'
        response.js = "jQuery('.signuptwo').hide(); jQuery('.signupthree').show(); jQuery('#thirdform').get(0).reload();"

    return dict(form2=form2)

def registerPartThree():
    buttons = [TAG.button('Back',_type="button",_onClick = "jQuery('.signupthree').hide(); jQuery('.signuptwo').show()"),
        TAG.button('Create',_type="submit")]

    print 'here2'
    if session.storeAddress and session.storeAddress.combine:
        # No need for billing address
        # Create form
        form3 = SQLFORM.factory(db.CreditCards, buttons=buttons)
    else:
        form3 = SQLFORM.factory(db.CreditCards,db.Addresses, buttons=buttons)
        blabel = TR(H4('Billing Address:'))
        form3[0].insert(3, blabel)


    if form3.validate(keepvalues=True):
        # Add Shipping Address table first
        id = db.Addresses.insert(**db.Addresses._filter_fields(session.storeAddress))
        # Use address reference in hidden fields in other two parts of form
        session.storeDetails.shippingaddress = id

        # If separate addresses, add billing to db
        if session.storeAddress.combine:
            form3.vars.billingaddress = id
        else:
            id = db.Addresses.insert(**db.Addresses._filter_fields(form3.vars))
            form3.vars.billingaddress = id

        # Add Credit Card table next
        id = db.CreditCards.insert(**db.CreditCards._filter_fields(form3.vars))
        # Use credit card reference in user table
        session.storeDetails.creditcard = id
        # Add User table last
        id = db.Users.insert(**db.Users._filter_fields(session.storeDetails))


        ## Log in and construct cookies as appropriate
        response.cookies['logincookie'] = response.session_id
        response.cookies['logincookie']['expires'] = 24 * 3600
        response.cookies['logincookie']['path'] = '/'

        row = db(db.Users.username == session.storeDetails.username).select().first()
        db(db.UserSessions.user_id==row.id).delete()

        newSession = dict(user_id = row.id, cookie_id = response.session_id)
        db.UserSessions.insert(**newSession)
        # Redirect to Home
        redirect(URL('default','index', extension='html'),client_side=True)

    return dict(form3=form3)
