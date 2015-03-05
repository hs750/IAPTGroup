__author__ = 'Y8191122'

"""
This file contains several manual forms. Methods of interest are:
    getRegistrationForm     contains the contruction of a major form
    editProfile             contains the update of a record manually
    user                    contains the insertion into a database manually

"""

# This controller handles user manipulation
def index():
    redirect(URL('default', 'index'))

def profile():
    """
    A page for viewing a user profile
    :return: the user db rector, the card address record for the users card, a table of the users pledges,
            the total pledged to each bootable the user has pledged too and its completion percentage
    """
    response.subtitle = 'User Profile'
    userID = session.user
    #If user manually types url and is not logged in redirect to login
    if userID is None:
        redirect(response.loginURL)

    user = getUser(userID)
    cardAddress = getCardAddress(userID)

    pledges = db((db.Users.id == db.UserPledges.userID) &
                 (db.Bootables.id == db.UserPledges.bootID) &
                 (db.Bootables.id == db.Pledges.bootID) &
                 (db.Pledges.id == db.PledgeRewards.pledgeID) &
                 (db.Pledges.Value == db.UserPledges.Value) &
                 (db.Rewards.id == db.PledgeRewards.rewardID) &
                 (db.Users.id == userID)).select('Bootables.id',
                                                 'Bootables.Title',
                                                 'Pledges.id',
                                                 'Pledges.Name',
                                                 'Pledges.Value',
                                                 'Rewards.Description',
                                                 distinct=True)
    bootIDs = set()
    for pledge in pledges:
        bootIDs.add(pledge.Bootables.id)

    bootTotals = dict()
    bootPercentages = dict()
    for id in bootIDs:
        bootTotals[id] = getTotalPledged(id)
        bootPercentages[id] = getCompletionPercentage(id)

    return dict(user=user, cardAddress=cardAddress, pledges=pledges, totals=bootTotals, percents=bootPercentages)

def getUser(userID):
    """
    Get a user record from the db
    :param userID: the user id of the record to get
    :return: the user record
    """
    user = db((db.Users.cardID == db.CreditCards.id) &
              (db.Users.addressID == db.Addresses.id) &
              (db.Users.id == userID)).select().first()
    return user


def getCardAddress(userID):
    """
    Get the credit card address for a users credit card
    :param userID: the user to get the record for
    :return: the credit card address record
    """
    user = getUser(userID)
    cardAddress = db(db.Addresses.id == user.CreditCards.addressID).select().first()
    return cardAddress


def editProfile():
    """
    A page for a user to edit their profile on
    :return: profile editing form
    """
    response.subtitle = 'Edit Profile'
    userID = session.user
    #If user manually types url and is not loged in redirect to login
    if userID is None:
        redirect(response.loginURL)

    user = getUser(userID)
    cardAddress = getCardAddress(userID)


    cardAddressSame = (user.CreditCards.addressID == user.Users.addressID)
    cardAddressSameOriginal = cardAddressSame
    #Use the new value of using the same address if the user has changed thr form
    if (session.useSameAddress is not None) and (request.post_vars.fName is not None):
        cardAddressSame = session.useSameAddress

    #For pre population of the form
    values = dict()
    values['fName'] = user.Users.FirstName
    values['lName'] = user.Users.LastName
    values['email'] = user.Users.Email
    values['dob'] = user.Users.DateOfBirth

    values['sAddress'] = user.Addresses.StreetAddress
    values['city'] = user.Addresses.City
    values['country'] = user.Addresses.Country
    values['postCode'] = user.Addresses.PostCode

    values['cardNumber'] = user.CreditCards.CardNumber
    month = str(user.CreditCards.ExpiryDate.month)
    if len(month) == 1:
        month = '0' + month
    values['expDate'] =  month + '/' + str(user.CreditCards.ExpiryDate.year)[2:]
    values['cardID'] = user.CreditCards.IDCode

    values['ccAddress'] = cardAddress.StreetAddress
    values['ccCity'] = cardAddress.City
    values['ccCountry'] = cardAddress.Country
    values['ccPostCode'] = cardAddress.PostCode

    #Overide DB with user entry
    for item in request.post_vars:
        values[item] = request.post_vars[item]

    #Display the registration form with or without a separate billing address depending on users preferences
    formChanged = False
    if (request.post_vars.ccUseAddress is not None) & (request.post_vars.ccUserAddress != ''):
        form = getRegistrationForm(True, values, False)
        formChanged = True
        session.useSameAddress = False
    elif (request.post_vars.ccCancel is not None) & (request.post_vars.ccCancel != ''):
        formChanged = True
        form = getRegistrationForm(False, values, False)
        session.useSameAddress = True
    else:
        form = getRegistrationForm(not cardAddressSame, values, False)

    if (not formChanged) and form.accepts(request.post_vars, session, formname='regForm'):
        session.useSameAddress = None

        user.Users.FirstName = request.post_vars.fName
        user.Users.LastName = request.post_vars.lName
        user.Users.Email = request.post_vars.email
        user.Users.DateOfBirth = request.post_vars.dob

        user.Addresses.StreetAddress = request.post_vars.sAddress
        user.Addresses.City = request.post_vars.city
        user.Addresses.Country = request.post_vars.country
        user.Addresses.PostCode = request.post_vars.postCode

        user.CreditCards.CardNumber = request.post_vars.cardNumber
        user.CreditCards.ExpiryDate = formatExpDate(request.post_vars.expDate)
        user.CreditCards.IDCode = request.post_vars.cardID
        user.Users.update_record()
        user.Addresses.update_record()
        user.CreditCards.update_record()

        useSameCCAddress = (request.post_vars.ccAddress is None)

        if cardAddressSameOriginal and useSameCCAddress:
            #Still using the same - Do Nothing
            pass
        elif cardAddressSameOriginal and (not useSameCCAddress):
            #Gone from using same to not
            ccAddressID = db.Addresses.insert(StreetAddress=request.post_vars.ccAddress,
                                              City=request.post_vars.ccCity,
                                              Country=request.post_vars.ccCountry,
                                              PostCode=request.post_vars.ccPostCode)
            user.CreditCards.addressID = ccAddressID
            user.CreditCards.update_record()
        elif (not cardAddressSameOriginal) and useSameCCAddress:
            #Gone from using different to same addresses
            oldCCAddressID = user.CreditCards.addressID
            user.CreditCards.addressID = user.Users.addressID
            user.CreditCards.update_record()
            db(db.Addresses.id == oldCCAddressID).delete()
        else:
            #Still using different
            cardAddress.StreetAddress = request.post_vars.ccAddress
            cardAddress.City = request.post_vars.ccCity
            cardAddress.Country = request.post_vars.ccCountry
            cardAddress.PostCode = request.post_vars.ccPostCode
            cardAddress.update_record()
        redirect(URL('profile'))
    elif form.errors:
        response.flash = 'There was something wrong with what you entered'
    else:
        response.flash = 'Change your details below'

    return dict(form=form)

def user():
    """
    The user page, depending on the request.args it will display different forms relating to users
    :return: a dict containing: the form for the required operation
    """
    if request.args(0) == 'register':
        response.subtitle = 'Register with BootUP'
        #Display the registration form with or without a separate billing address depending on users preferences
        formChanged = False
        if (request.post_vars.ccUseAddress is not None) & (request.post_vars.ccUserAddress != ''):
            form = getRegistrationForm(True, request.post_vars)
            formChanged = True
        elif (request.post_vars.ccCancel is not None) & (request.post_vars.ccCancel != ''):
            formChanged = True
            form = getRegistrationForm(False, request.post_vars)
        else:
            form = getRegistrationForm(False, request.post_vars)

        if (not formChanged) and form.accepts(request.post_vars, session, formname='regForm'):
            #Check if username is already taken (IS_NOT_IN_DB doesnt seem to work)
            if db(db.Users.Username == request.post_vars.username).select().first() is not None:
                form.errors.username = 'Username already taken'
                response.flash = 'Username already taken!'
            else:
                #Insert data if username is not taken
                adrsID = db.Addresses.insert(StreetAddress=request.post_vars.sAddress,
                                                City=request.post_vars.city,
                                                Country=request.post_vars.country,
                                                PostCode=request.post_vars.postCode)
                ccAddressID = adrsID
                if (request.post_vars.ccAddress is not None) & (request.post_vars.ccAddress != ''):
                    ccAddressID = db.Addresses.insert(StreetAddress=request.post_vars.ccAddress,
                                                      City=request.post_vars.ccCity,
                                                      Country=request.post_vars.ccCountry,
                                                      PostCode=request.post_vars.ccPostCode)

                expDate = formatExpDate(request.post_vars.expDate)
                ccID = db.CreditCards.insert(CardNumber=request.post_vars.cardNumber,
                                             ExpiryDate=expDate,
                                             IDCode=request.post_vars.cardID,
                                             addressID=ccAddressID)
                userid = db.Users.insert(FirstName=request.post_vars.fName,
                                LastName=request.post_vars.lName,
                                Email=request.post_vars.email,
                                Username=request.post_vars.username,
                                Password=request.post_vars.password,
                                DateOfBirth=request.post_vars.dob,
                                addressID=adrsID,
                                cardID=ccID)
                response.flash = 'Successfully Registered'

                #Log user in and redirect to home
                session.user = userid
                session.flash = 'Logged in as ' + request.post_vars.username
                redirect(URL('default', 'index'))
        elif form.errors:
            response.flash = 'There was a problem with something you entered'
        else:
            response.flash = 'Please enter your details bellow:'
    elif request.args(0) == 'login':
        response.subtitle = 'Login to BootUP'
        #Display the login form
        form = getLoginForm()
        if form.accepts(request.post_vars, session, formname='login'):
            #Find user
            userLogin = db(db.Users.Username == request.post_vars.username).select(db.Users.id,
                                                                                   db.Users.Password,
                                                                                   db.Users.Username).first()
            if userLogin is not None:
                #if user found check password
                if userLogin.Password == request.post_vars.password:
                    #password check passed, login
                    #When logged in store user ID and redirect to home page
                    session.user = userLogin.id
                    session.flash = 'Logged in as ' + userLogin.Username
                    redirect(URL('default', 'index'))
                else:
                    response.flash = 'Incorrect Password'
            else:
                response.flash = 'User Not Found!'
        elif form.errors:
            response.flash = 'Username or Password incorrectly entered'
        else:
            response.flash = 'Please enter your username and password'
    elif request.args(0) == 'logout':
        #Log the user out and redirect home
        session.user = None
        session.flash = 'Successfully logged out'
        redirect(URL('default', 'index'))
    return dict(form=form)


def getRegistrationForm(ccAddress, values, incUsernameAndPassword=True):
    """Returns a form for user registration

    :param ccAddress: Include a seperate address as billing address
    :param values: input values taken from form (for re-population)
    :param incUsernameAndPassword: include the username and password entry fields (for user profile editing)
    :return: The form to be displayed
    """

    #The requirements of the inputs are taken from the requirements of the database fields as
    #as they should be the same in most cases and there is no need for duplication.

    #A registration form consists of 4 parts 3 manditory and 1 optional
    #   General details (name, email, username, password)
    #   Address
    #   Credit Card
    #   Then optionally the address of the credit card (if different from the main address)
    generalDiv = DIV(DIV(LEGEND('General Details:')),
                     DIV(LABEL('First Name:', _for='fName')),
                     DIV(INPUT(_name='fName', requires=db.Users.FirstName.requires,
                               _value=getFieldValue(values, 'fName'))),
                     DIV(LABEL('Last Name:', _for='lName')),
                     DIV(INPUT(_name='lName', reqires=db.Users.LastName.requires,
                               _value=getFieldValue(values, 'lName'))),
                     DIV(LABEL('Email:', _for='email')),
                     DIV(INPUT(_name='email', _type='email', reqires=db.Users.Email.requires,
                               _value=getFieldValue(values, 'email'))),
                     DIV(LABEL('Date of Birth:', _for='dob')),
                     DIV(INPUT(_name='dob', _type='date', reqires=db.Users.DateOfBirth.requires,
                               _value=getFieldValue(values, 'dob'),
                               _placeholder='YYYY-MM-DD',
                               _class='date')),
                     _class='regForm',
                     _id='regForm1')
    #optionally include password and username fields
    if incUsernameAndPassword:
        generalDiv.append(DIV(DIV(LABEL('Username:', _for='username')),
                              DIV(INPUT(_name='username', reqires=db.Users.Username.requires,
                                        _value=getFieldValue(values, 'username'))),
                              DIV(LABEL('Password:', _for='password')),
                              DIV(INPUT(_name='password', _type='password', reqires=db.Users.Password.requires,
                                        _value=getFieldValue(values, 'password'))),
                              DIV(LABEL('Confirm Password:', _for='password_two')),
                              DIV(INPUT(_name="password_two", _type="password",
                                        requires=IS_EXPR('value==%s' % repr(request.vars.password),
                                                         error_message='Passwords do not match'),
                                        _value=getFieldValue(values, 'password_two')))))
    form = FORM(generalDiv,
                DIV(DIV(LEGEND('Address:')),
                    DIV(LABEL('Street Address:', _for='sAddress')),
                    DIV(TEXTAREA(_name='sAddress', requires=db.Addresses.StreetAddress.requires,
                                 value=getFieldValue(values, 'sAddress'))),
                    DIV(LABEL('City:', _for='city')),
                    DIV(INPUT(_name='city', requires=db.Addresses.City.requires,
                              _value=getFieldValue(values, 'city'))),
                    DIV(LABEL('Country:', _for='country')),
                    DIV(INPUT(_name='country', requires=db.Addresses.Country.requires,
                              _value=getFieldValue(values, 'country'))),
                    DIV(LABEL('Post Code:', _for='postCode')),
                    DIV(INPUT(_name='postCode', requires=db.Addresses.PostCode.requires,
                              _value=getFieldValue(values, 'postCode'),
                              _placeholder='AB01 2CD')),
                    _class='regForm',
                    _id='regForm2'),

                DIV(DIV(LEGEND('Credit Card Details:')),
                    DIV(LABEL('Card Number:', _for='cardNumber')),
                    DIV(INPUT(_name='cardNumber', requires=db.CreditCards.CardNumber.requires,
                              _value=getFieldValue(values, 'cardNumber'),
                              _placeholder='012345678901', _maxlength=12)),
                    DIV(LABEL('Expiry Date:', _for='expDate')),
                    DIV(INPUT(_name='expDate', requires=db.CreditCards.ExpiryDate.requires,
                              _value=getFieldValue(values, 'expDate'),
                              _placeholder='MM/YY')),
                    DIV(LABEL('Card ID Code:', _for='cardID')),
                    DIV(INPUT(_name='cardID', requires=db.CreditCards.IDCode.requires,
                              _value=getFieldValue(values, 'cardID'),
                              _placeholder='012', _maxlength=3)),
                    _class='regForm',
                    _id='regForm3'),
                formname='regForm'
                )

    #optionally inclide card address fields
    if not ccAddress:
        form.append(INPUT(_name='ccUseAddress', _type='submit', _value='Use Separate Billing Address'))
    else:
        form.append(DIV(DIV(LEGEND('Billing Address')),
                        DIV(LABEL('Street Address:', _for='ccAddress')),
                        DIV(TEXTAREA(_name='ccAddress', requires=db.Addresses.StreetAddress.requires,
                                     value=getFieldValue(values, 'ccAddress'))),
                        DIV(LABEL('City:', _for='ccCity')),
                        DIV(INPUT(_name='ccCity', requires=db.Addresses.City.requires,
                                  _value=getFieldValue(values, 'ccCity'))),
                        DIV(LABEL('Country:', _for='ccCountry')),
                        DIV(INPUT(_name='ccCountry', requires=db.Addresses.Country.requires,
                                  _value=getFieldValue(values, 'ccCountry'))),
                        DIV(LABEL('Post Code:', _for='ccPostCode')),
                        DIV(INPUT(_name='ccPostCode', requires=db.Addresses.PostCode.requires,
                                  _value=getFieldValue(values, 'ccPostCode'),
                                  _placeholder='AB01 2CD')),
                        _class='regForm',
                        _id='regForm4'
                        ))
        form.append(INPUT(_name='ccCancel', _type='submit', _value='Cancel billing address'))

    form.append(INPUT(_name='submit', _type='submit'))

    #Must preform accepts do that in all paths formkey in form and session get set to tbe the same
    form.accepts(dict(), session, 'regForm')
    return form


def getLoginForm():
    """
    Create the login form
    :return: the login form
    """
    form = FORM(DIV(LEGEND('Login:')),
                DIV(LABEL('Username:', _for='username')),
                DIV(INPUT(_name='username', requires=IS_NOT_EMPTY())),
                DIV(LABEL('Password:', _for='password')),
                DIV(INPUT(_name='password', _type='password', requires=IS_NOT_EMPTY())),
                DIV(INPUT(_name='login', _type='submit')),
                name='loginForm'
                )
    return form

def formatExpDate(expDate):
    """
    Expiry Date of credit card has the form MM/YY but the database wants the form YYYY-MM-DD
    Sor format appropriately
    :param expDate: date with format MM/YY
    :return: date with format 20YY-MM-01
    """
    expDateParts = expDate.split('/')
    expDate = '20' + expDateParts[1] + '-' + expDateParts[0] + '-01'
    return expDate



